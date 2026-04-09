from __future__ import annotations

import time

import pytest
from sqlmodel import select

from src.apps.restaurant.models import Ingredient, OperationalEvent, PurchaseOrderLine


@pytest.mark.asyncio
async def test_e2e_seat_to_settlement_and_security_audits(client, db_session):
    branch = (
        await client.post(
            "/api/v1/branches",
            json={"name": "ReleaseBranch", "tax_rate": 0.1, "service_charge_rate": 0.05},
        )
    ).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "R1", "seats": 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Pasta", "price": 12.0})).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Flour", "unit": "kg", "quantity_on_hand": 5, "reorder_threshold": 1},
        )
    ).json()

    await client.post(
        "/api/v1/recipes",
        json={
            "branch_id": branch["id"],
            "name": "Pasta Base",
            "items": [{"ingredient_id": ingredient["id"], "quantity": 0.4}],
        },
    )

    reservation = (
        await client.post(
            "/api/v1/reservations",
            json={
                "branch_id": branch["id"],
                "guest_name": "Readiness Guest",
                "guest_phone": "+15550100",
                "party_size": 2,
                "reservation_time": "2026-04-09T19:00:00Z",
            },
        )
    ).json()
    seated = await client.post(f"/api/v1/tables/{table['id']}/seat", json={"reservation_id": reservation["id"], "party_size": 2})
    assert seated.status_code == 200

    order = (
        await client.post(
            "/api/v1/orders",
            json={
                "branch_id": branch["id"],
                "order_source": "dine_in",
                "table_id": table["id"],
                "waiter_id": 10,
                "items": [{"menu_item_id": menu["id"], "quantity": 2, "course_no": 1}],
            },
        )
    ).json()

    bill_id = order["bill"]["id"]
    tickets = (await client.get("/api/v1/kitchen/tickets")).json()["items"]
    ticket_id = tickets[0]["id"]
    assert (await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "in_preparation"})).status_code == 200
    assert (await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "ready"})).status_code == 200
    assert (await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "served"})).status_code == 200

    settled = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 99, "settlements": [{"payment_method": "cash", "amount": order["bill"]["total_amount"]}]},
    )
    assert settled.status_code == 200
    assert settled.json()["status"] == "paid"

    approval = (
        await client.post(
            "/api/v1/discount-approvals",
            json={
                "branch_id": branch["id"],
                "bill_id": bill_id,
                "requested_by": 10,
                "discount_amount": 1.0,
                "reason": "service recovery",
            },
        )
    ).json()
    approved = await client.patch(
        f"/api/v1/discount-approvals/{approval['id']}",
        json={"approved_by": 1, "status": "approved"},
    )
    assert approved.status_code == 200

    refund = await client.post(
        "/api/v1/refunds",
        json={"branch_id": branch["id"], "bill_id": bill_id, "amount": 1.0, "reason": "late service", "approved_by": 1},
    )
    assert refund.status_code == 201

    audits = await client.get(f"/api/v1/audit/privileged-actions?branch_id={branch['id']}")
    assert audits.status_code == 200
    actions = {row["action"] for row in audits.json()}
    assert {"billing.discount.approved", "billing.refund.created"}.issubset(actions)


@pytest.mark.asyncio
async def test_po_to_stock_traceability_and_reconciliation_readiness(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "Supply", "tax_rate": 0.08, "service_charge_rate": 0.05})).json()
    vendor = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/vendors",
            json={"name": "Vendor A", "contact_name": "Bob", "phone": "+15551234"},
        )
    ).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Rice", "unit": "kg", "quantity_on_hand": 10, "reorder_threshold": 2},
        )
    ).json()

    po = (
        await client.post(
            "/api/v1/purchase-orders",
            json={
                "branch_id": branch["id"],
                "created_by": 5,
                "lines": [{"ingredient_id": ingredient["id"], "ordered_qty": 6, "unit_cost": 1.5}],
            },
        )
    ).json()

    po_line = (
        await db_session.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po["id"]))
    ).scalars().first()
    assert po_line is not None

    receipt = await client.post(
        f"/api/v1/purchase-orders/{po['id']}/receipts",
        json={"lines": [{"line_id": po_line.id, "received_qty": 6}]},
    )
    assert receipt.status_code == 200

    goods = (
        await client.post(
            "/api/v1/goods-receipts",
            json={"branch_id": branch["id"], "purchase_order_id": po["id"], "vendor_id": vendor["id"], "notes": "full receipt"},
        )
    ).json()
    assert goods["purchase_order_id"] == po["id"]

    refreshed_ingredient = await db_session.get(Ingredient, ingredient["id"])
    assert refreshed_ingredient is not None
    assert refreshed_ingredient.quantity_on_hand == pytest.approx(16.0)


@pytest.mark.asyncio
async def test_nfr_latency_availability_audit_and_degraded_mode(client, db_session):
    # Availability posture checks
    health = await client.get("/health")
    ready = await client.get("/ready")
    assert health.status_code == 200
    assert ready.status_code == 200

    # Latency checks: p95 POS action target (<300ms) and order->kitchen/bill targets (<2s)
    samples: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        response = await client.get("/health")
        samples.append(time.perf_counter() - t0)
        assert response.status_code == 200
    samples.sort()
    p95 = samples[max(0, int(len(samples) * 0.95) - 1)]
    assert p95 < 0.3

    branch = (
        await client.post(
            "/api/v1/branches",
            json={"name": "NFR", "tax_rate": 0.1, "service_charge_rate": 0.05},
        )
    ).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "N1", "seats": 2})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Soup", "price": 8.0})).json()
    drawer = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/drawer-sessions",
            json={"cashier_id": 1, "opening_balance": 100.0},
        )
    ).json()

    t_order = time.perf_counter()
    order_resp = await client.post(
        "/api/v1/orders",
        json={
            "branch_id": branch["id"],
            "order_source": "dine_in",
            "table_id": table["id"],
            "waiter_id": 5,
            "items": [{"menu_item_id": menu["id"], "quantity": 1, "course_no": 1}],
        },
    )
    order_elapsed = time.perf_counter() - t_order
    assert order_resp.status_code == 201
    assert order_elapsed < 2.0

    bill_id = order_resp.json()["bill"]["id"]
    t_settle = time.perf_counter()
    settle = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 1, "settlements": [{"payment_method": "cash", "amount": order_resp.json()["bill"]["total_amount"]}]},
    )
    settle_elapsed = time.perf_counter() - t_settle
    assert settle.status_code == 200
    assert settle_elapsed < 2.0

    # Degraded-mode behavior proxy: blocked day-close emits warning operational event and exposes blockers.
    day_close = (
        await client.post(
            "/api/v1/day-close",
            json={"branch_id": branch["id"], "business_date": "2026-04-09T00:00:00Z", "notes": "degraded test"},
        )
    ).json()
    finalize = await client.patch(f"/api/v1/day-close/{day_close['id']}/finalize", json={"closed_by": 1})
    assert finalize.status_code == 409

    blockers = await client.get(f"/api/v1/day-close/{day_close['id']}/blockers")
    assert blockers.status_code == 200
    assert any(item.startswith("open_drawers=") for item in blockers.json()["blockers"])

    events = (
        await db_session.execute(
            select(OperationalEvent).where(
                OperationalEvent.branch_id == branch["id"],
                OperationalEvent.event_name == "branch.day_close_blocked",
            )
        )
    ).scalars().all()
    assert len(events) >= 1

    # Reconciliation override required approval and complete audit trail.
    failed_close = await client.post(
        f"/api/v1/drawer-sessions/{drawer['id']}/close",
        json={"closing_balance": 95.0, "override_reason": "cash mismatch"},
    )
    assert failed_close.status_code == 400

    ok_close = await client.post(
        f"/api/v1/drawer-sessions/{drawer['id']}/close",
        json={"closing_balance": 95.0, "override_reason": "cash mismatch", "approved_by": 1},
    )
    assert ok_close.status_code == 200

    audits = await client.get(f"/api/v1/audit/privileged-actions?branch_id={branch['id']}&action=reconciliation.override")
    assert audits.status_code == 200
    assert len(audits.json()) >= 1
