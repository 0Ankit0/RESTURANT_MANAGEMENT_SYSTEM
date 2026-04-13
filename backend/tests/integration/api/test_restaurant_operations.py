import pytest
from sqlmodel import select

from src.apps.restaurant.models import (
    Ingredient,
    OperationalSeverity,
    OpsEventOutbox,
    OpsEventOutboxStatus,
    PurchaseOrderLine,
    StockLedgerEntry,
)
from src.apps.restaurant.services.ops_event_outbox import ops_event_outbox_dispatcher


@pytest.mark.asyncio
async def test_restaurant_flow(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "Downtown", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "T1", "seats": 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Burger", "price": 10})).json()
    category = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/menu-categories",
            json={"name": "Mains", "display_order": 1},
        )
    ).json()
    modifier_group = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/modifier-groups",
            json={"name": "Cheese options", "min_select": 0, "max_select": 2, "is_required": False},
        )
    ).json()
    modifier_option = (
        await client.post(
            f"/api/v1/modifier-groups/{modifier_group['id']}/options",
            json={"name": "Extra cheese", "extra_price": 1.25},
        )
    ).json()
    tax_rule = (
        await client.post(
            "/api/v1/tax-rules",
            json={"branch_id": branch["id"], "name": "VAT", "rate": 0.1},
        )
    ).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Tomato", "unit": "kg", "quantity_on_hand": 5, "reorder_threshold": 2},
        )
    ).json()
    branch_two = (await client.post("/api/v1/branches", json={"name": "Uptown", "tax_rate": 0.08, "service_charge_rate": 0.03})).json()
    ingredient_two = (
        await client.post(
            f"/api/v1/branches/{branch_two['id']}/ingredients",
            json={"name": "Tomato", "unit": "kg", "quantity_on_hand": 1, "reorder_threshold": 1},
        )
    ).json()
    recipe = (
        await client.post(
            "/api/v1/recipes",
            json={
                "branch_id": branch["id"],
                "name": "Burger Base",
                "items": [{"ingredient_id": ingredient["id"], "quantity": 0.2}],
            },
        )
    ).json()
    vendor = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/vendors",
            json={"name": "Fresh Farms", "contact_name": "Alice", "phone": "+15550001"},
        )
    ).json()
    drawer = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/drawer-sessions",
            json={"cashier_id": 7, "opening_balance": 100},
        )
    ).json()
    policy = (await client.post(f"/api/v1/branches/{branch['id']}/policies", json={"key": "max_discount_pct", "value": "10"})).json()

    res = await client.get(f"/api/v1/branches/{branch['id']}/tables")
    assert res.status_code == 200
    assert any(row["id"] == table["id"] for row in res.json())
    assert category["id"] is not None
    assert modifier_option["id"] is not None
    assert tax_rule["version"] >= 1
    assert recipe["version"] >= 1

    res = await client.post(f"/api/v1/branches/{branch['id']}/service-zones", json={"name": "Patio"})
    assert res.status_code == 201
    zone_id = res.json()["id"]
    assert zone_id is not None

    res = await client.get(f"/api/v1/branches/{branch['id']}/service-zones")
    assert res.status_code == 200
    assert any(row["id"] == zone_id for row in res.json())

    res = await client.post(
        f"/api/v1/branches/{branch['id']}/table-groups",
        json={"name": "T1+T2", "table_ids": [table["id"]]},
    )
    assert res.status_code == 201

    res = await client.post(
        "/api/v1/reservations",
        json={
            "branch_id": branch["id"],
            "guest_name": "Jane Doe",
            "guest_phone": "+1000000000",
            "party_size": 2,
            "reservation_time": "2026-03-25T18:30:00Z",
        },
    )
    assert res.status_code == 201
    reservation_id = res.json()["id"]

    res = await client.get(f"/api/v1/reservations/{reservation_id}")
    assert res.status_code == 200

    res = await client.patch(f"/api/v1/reservations/{reservation_id}", json={"notes": "arriving in 5"})
    assert res.status_code == 200

    res = await client.post(
        f"/api/v1/tables/{table['id']}/seat",
        json={"reservation_id": reservation_id, "party_size": 2},
    )
    assert res.status_code == 200

    res = await client.post(f"/api/v1/reservations/{reservation_id}/cancel")
    assert res.status_code == 200


    res = await client.post(
        "/api/v1/waitlist",
        json={
            "branch_id": branch["id"],
            "guest_name": "Walk In",
            "guest_phone": "+12223334444",
            "party_size": 2,
            "notes": "window side",
        },
    )
    assert res.status_code == 201
    waitlist_id = res.json()["id"]

    res = await client.post(f"/api/v1/tables/{table['id']}/release")
    assert res.status_code == 200

    res = await client.patch(f"/api/v1/waitlist/{waitlist_id}/promote?table_id={table['id']}")
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/orders",
        json={
            "branch_id": branch["id"],
            "order_source": "dine_in",
            "table_id": table["id"],
            "waiter_id": 2,
            "items": [{"menu_item_id": menu["id"], "quantity": 2, "course_no": 1}],
        },
    )
    assert res.status_code == 201
    order_id = res.json()["order"]["id"]
    bill_id = res.json()["bill"]["id"]

    res = await client.get(f"/api/v1/orders?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(item["id"] == order_id for item in res.json()["items"])

    res = await client.get(f"/api/v1/bills/{bill_id}")
    assert res.status_code == 200

    res = await client.get(f"/api/v1/bills?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(row["id"] == bill_id for row in res.json())

    res = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={"status": "ready", "items": [{"menu_item_id": menu['id'], "quantity": 3, "course_no": 1}]},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    res = await client.get("/api/v1/kitchen/tickets")
    assert res.status_code == 200
    ticket_id = res.json()["items"][0]["id"]

    res = await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "in_preparation"})
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/inventory/adjustments",
        json={"ingredient_id": ingredient["id"], "change_qty": -1, "reason": "prep_usage", "approved_by": 1},
    )
    assert res.status_code == 201

    res = await client.post(
        "/api/v1/purchase-orders",
        json={
            "branch_id": branch["id"],
            "created_by": 5,
            "lines": [{"ingredient_id": ingredient["id"], "ordered_qty": 3, "unit_cost": 2.5}],
        },
    )
    assert res.status_code == 201
    po_id = res.json()["id"]

    po_line = (
        await db_session.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po_id))
    ).scalars().first()
    assert po_line is not None

    res = await client.get(f"/api/v1/branches/{branch['id']}/vendors")
    assert res.status_code == 200
    assert any(item["id"] == vendor["id"] for item in res.json())

    res = await client.post(
        f"/api/v1/purchase-orders/{po_id}/receipts",
        json={"lines": [{"line_id": po_line.id, "received_qty": 3}]},
    )
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/goods-receipts",
        json={"branch_id": branch["id"], "purchase_order_id": po_id, "vendor_id": vendor["id"], "notes": "delivered"},
    )
    assert res.status_code == 201
    goods_receipt_id = res.json()["id"]

    res = await client.get(f"/api/v1/goods-receipts?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(item["id"] == goods_receipt_id for item in res.json()["items"])

    res = await client.post(
        "/api/v1/stock-transfers",
        json={
            "from_branch_id": branch["id"],
            "to_branch_id": branch_two["id"],
            "from_ingredient_id": ingredient["id"],
            "to_ingredient_id": ingredient_two["id"],
            "quantity": 1.0,
        },
    )
    assert res.status_code == 201
    transfer_id = res.json()["id"]

    res = await client.patch(
        f"/api/v1/stock-transfers/{transfer_id}",
        json={
            "approved_by": 1,
            "acknowledged_by": 1,
            "acknowledgement_note": "picked and sealed",
            "action": "mark_in_transit",
            "shipped_qty": 1.0,
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_transit"

    res = await client.patch(
        f"/api/v1/stock-transfers/{transfer_id}",
        json={
            "approved_by": 1,
            "acknowledged_by": 2,
            "acknowledgement_note": "received in full",
            "action": "mark_received",
            "received_qty": 1.0,
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "received"

    res = await client.get(f"/api/v1/stock-transfers?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(item["id"] == transfer_id for item in res.json()["items"])

    res = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 7, "settlements": [{"payment_method": "cash", "amount": 34.5}]},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "paid"

    res = await client.post(
        "/api/v1/discount-approvals",
        json={
            "branch_id": branch["id"],
            "bill_id": bill_id,
            "requested_by": 2,
            "discount_amount": 2.0,
            "reason": "service recovery",
        },
    )
    assert res.status_code == 201
    approval_id = res.json()["id"]

    res = await client.patch(
        f"/api/v1/discount-approvals/{approval_id}",
        json={"approved_by": 1, "status": "approved"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    res = await client.post(
        "/api/v1/refunds",
        json={"branch_id": branch["id"], "bill_id": bill_id, "amount": 1.5, "reason": "item issue", "approved_by": 1},
    )
    assert res.status_code == 201

    res = await client.get(f"/api/v1/refunds?branch_id={branch['id']}")
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1

    res = await client.post(
        f"/api/v1/drawer-sessions/{drawer['id']}/close",
        json={"closing_balance": 134.5},
    )
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/shifts",
        json={
            "branch_id": branch["id"],
            "staff_user_id": 9,
            "role": "waiter",
            "starts_at": "2026-03-25T09:00:00Z",
            "ends_at": "2026-03-25T17:00:00Z",
            "status": "scheduled",
        },
    )
    assert res.status_code == 201
    shift_id = res.json()["id"]

    res = await client.patch(f"/api/v1/shifts/{shift_id}", json={"status": "started"})
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/attendance",
        json={"branch_id": branch["id"], "staff_user_id": 9, "shift_id": shift_id, "notes": "on time"},
    )
    assert res.status_code == 201
    attendance_id = res.json()["id"]

    res = await client.get(f"/api/v1/attendance?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(row["id"] == attendance_id for row in res.json())

    res = await client.patch(f"/api/v1/attendance/{attendance_id}/checkout", json={"notes": "completed"})
    assert res.status_code == 200

    res = await client.post(
        "/api/v1/accounting-exports",
        json={"branch_id": branch["id"], "business_date": "2026-03-25T00:00:00Z"},
        headers={"Idempotency-Key": "exp-1"},
    )
    assert res.status_code == 201
    export_id = res.json()["id"]

    replay = await client.post(
        "/api/v1/accounting-exports",
        json={"branch_id": branch["id"], "business_date": "2026-03-25T00:00:00Z"},
        headers={"Idempotency-Key": "exp-1"},
    )
    assert replay.status_code == 201
    assert replay.headers.get("X-Idempotent-Replay") == "true"

    res = await client.get(f"/api/v1/accounting-exports?branch_id={branch['id']}")
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1

    res = await client.post(
        f"/api/v1/accounting-exports/{export_id}/retry",
        json={"requested_by": 1, "reason": "network timeout"},
    )
    assert res.status_code == 201

    res = await client.get(f"/api/v1/accounting-exports/retries?export_id={export_id}")
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1

    res = await client.post(
        "/api/v1/day-close",
        json={"branch_id": branch["id"], "business_date": "2026-03-25T00:00:00Z", "notes": "closing"},
    )
    assert res.status_code == 201
    day_close_id = res.json()["id"]

    res = await client.post(
        f"/api/v1/day-close/{day_close_id}/checklist-items",
        json={"item_key": "drawer_reconciled", "is_required": True},
    )
    assert res.status_code == 201
    checklist_item_id = res.json()["id"]

    res = await client.patch(
        f"/api/v1/day-close/checklist-items/{checklist_item_id}",
        json={"checked_by": 1, "is_checked": True},
    )
    assert res.status_code == 200

    res = await client.patch(f"/api/v1/day-close/{day_close_id}/finalize", json={"closed_by": 1, "notes": "all clear"})
    assert res.status_code == 200
    assert res.json()["status"] == "closed"

    res = await client.get(f"/api/v1/day-close?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(row["id"] == day_close_id for row in res.json()["items"])

    res = await client.get(f"/api/v1/reports/branch-operations?branch_id={branch['id']}")
    assert res.status_code == 200
    assert res.json()["orders_count"] >= 1
    assert res.json()["collected_sales"] >= 34.5
    assert "settlement_health" in res.json()
    assert "staffing" in res.json()

    res = await client.get(f"/api/v1/drawer-reconciliation?branch_id={branch['id']}")
    assert res.status_code == 200
    assert len(res.json()["rows"]) >= 1

    res = await client.get(f"/api/v1/operations/notifications?branch_id={branch['id']}&limit=10")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = await client.patch(f"/api/v1/admin/branch-policies/{policy['id']}", json={"value": "15"})
    assert res.status_code == 200
    assert res.json()["value"] == "15"


@pytest.mark.asyncio
async def test_branch_bootstrap_and_privileged_audit(client):
    bootstrap = await client.post(
        "/api/v1/branches/bootstrap",
        json={
            "branch_name": "Harbor",
            "tax_rate": 0.07,
            "service_charge_rate": 0.05,
            "zones": ["Dining", "Patio"],
            "tables": [{"code": "D1", "seats": 4}, {"code": "P1", "seats": 2}],
            "taxes": [{"name": "City VAT", "rate": 0.07}],
            "payment_methods": [{"code": "cash", "display_name": "Cash"}, {"code": "card", "display_name": "Card"}],
            "kitchen_stations": [{"name": "Grill", "code": "grill"}, {"name": "Expo", "code": "expo", "is_expo": True}],
        },
    )
    assert bootstrap.status_code == 201
    payload = bootstrap.json()
    branch_id = payload["branch"]["id"]
    assert len(payload["zones"]) == 2
    assert len(payload["tables"]) == 2
    assert len(payload["payment_methods"]) == 2
    assert len(payload["kitchen_stations"]) == 2

    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch_id}/ingredients",
            json={"name": "Cheese", "unit": "kg", "quantity_on_hand": 10, "reorder_threshold": 1},
        )
    ).json()

    adjustment = await client.post(
        "/api/v1/inventory/adjustments",
        json={"ingredient_id": ingredient["id"], "change_qty": -0.5, "reason": "manual_count", "approved_by": 55},
    )
    assert adjustment.status_code == 201

    audits = await client.get(f"/api/v1/audit/privileged-actions?branch_id={branch_id}")
    assert audits.status_code == 200
    assert any(row["action"] == "inventory.adjustment.manual" for row in audits.json())


@pytest.mark.asyncio
async def test_edge_case_controls_and_audit_trace(client):
    branch = (await client.post("/api/v1/branches", json={"name": "EdgeCase", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "E1", "seats": 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Steak", "price": 20})).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Beef", "unit": "kg", "quantity_on_hand": 10, "reorder_threshold": 2},
        )
    ).json()
    await client.post(
        "/api/v1/recipes",
        json={
            "branch_id": branch["id"],
            "name": "Steak",
            "items": [{"ingredient_id": ingredient["id"], "quantity": 0.4}],
        },
    )
    drawer = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/drawer-sessions",
            json={"cashier_id": 8, "opening_balance": 200},
        )
    ).json()

    reservation = (
        await client.post(
            "/api/v1/reservations",
            json={
                "branch_id": branch["id"],
                "guest_name": "Reservation Guest",
                "guest_phone": "+1999888777",
                "party_size": 2,
                "reservation_time": "2026-04-09T18:00:00Z",
            },
        )
    ).json()
    seated = await client.post(
        f"/api/v1/tables/{table['id']}/seat",
        json={"reservation_id": reservation["id"], "party_size": 2},
    )
    assert seated.status_code == 200

    delivery_order = await client.post(
        "/api/v1/orders",
        json={
            "branch_id": branch["id"],
            "order_source": "delivery",
            "waiter_id": 5,
            "items": [{"menu_item_id": menu["id"], "quantity": 1, "course_no": 2, "notes": "channel #abc"}],
        },
    )
    assert delivery_order.status_code == 201
    order_id = delivery_order.json()["order"]["id"]
    bill_id = delivery_order.json()["bill"]["id"]
    assert delivery_order.json()["order"]["order_source"] == "delivery"

    kitchen = await client.get("/api/v1/kitchen/tickets")
    assert kitchen.status_code == 200
    ticket_id = kitchen.json()["items"][0]["id"]
    assert (await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "in_preparation"})).status_code == 200

    cancel_without_approval = await client.patch(f"/api/v1/orders/{order_id}", json={"status": "cancelled"})
    assert cancel_without_approval.status_code == 409

    approval = (
        await client.post(
            "/api/v1/orders/edit-approvals",
            json={"order_id": order_id, "requested_by": 5, "reason": "customer requested cancellation"},
        )
    ).json()
    await client.patch(f"/api/v1/orders/edit-approvals/{approval['id']}", json={"status": "approved", "approved_by": 1})
    cancel_with_approval = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={"status": "cancelled", "edit_approval_id": approval["id"]},
    )
    assert cancel_with_approval.status_code == 200

    settle = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 8, "settlements": [{"payment_method": "cash", "amount": 5}]},
    )
    assert settle.status_code == 200

    assert (
        await client.post(
            "/api/v1/refunds",
            json={"branch_id": branch["id"], "bill_id": bill_id, "amount": 1, "approved_by": 1},
        )
    ).status_code == 400

    assert (
        await client.post(
            f"/api/v1/drawer-sessions/{drawer['id']}/close",
            json={"closing_balance": 203, "override_reason": "cash mismatch"},
        )
    ).status_code == 400

    assert (
        await client.post(
            f"/api/v1/drawer-sessions/{drawer['id']}/close",
            json={"closing_balance": 203, "override_reason": "cash mismatch", "approved_by": 1},
        )
    ).status_code == 200

    refund = await client.post(
        "/api/v1/refunds",
        json={
            "branch_id": branch["id"],
            "bill_id": bill_id,
            "amount": 1,
            "reason": "post-close supervised adjustment",
            "approved_by": 1,
        },
    )
    assert refund.status_code == 201
    refund_id = refund.json()["id"]

    rerun = await client.post(
        f"/api/v1/refunds/{refund_id}/rerun",
        json={"requested_by": 1, "reason": "gateway timeout replay"},
        headers={"Idempotency-Key": "refund-rerun-1"},
    )
    assert rerun.status_code == 200
    assert rerun.json()["status"] == "completed"

    rerun_replay = await client.post(
        f"/api/v1/refunds/{refund_id}/rerun",
        json={"requested_by": 1, "reason": "gateway timeout replay"},
        headers={"Idempotency-Key": "refund-rerun-1"},
    )
    assert rerun_replay.status_code == 200
    assert rerun_replay.headers.get("X-Idempotent-Replay") == "true"

    audits = await client.get(f"/api/v1/audit/privileged-actions?branch_id={branch['id']}")
    assert audits.status_code == 200
    actions = [row["action"] for row in audits.json()]
    assert "billing.refund.created" in actions
    assert "reconciliation.override" in actions

    day_close = await client.post(
        "/api/v1/day-close",
        json={"branch_id": branch["id"], "business_date": "2026-04-09T00:00:00Z", "notes": "blocker verification"},
    )
    assert day_close.status_code == 201
    blockers = await client.get(f"/api/v1/day-close/{day_close.json()['id']}/blockers")
    assert blockers.status_code == 200
    assert isinstance(blockers.json()["blockers"], list)


@pytest.mark.asyncio
async def test_purchase_order_to_stock_workflow(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "PO Branch", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Rice", "unit": "kg", "quantity_on_hand": 2, "reorder_threshold": 1},
        )
    ).json()

    po = (
        await client.post(
            "/api/v1/purchase-orders",
            json={
                "branch_id": branch["id"],
                "created_by": 9,
                "lines": [{"ingredient_id": ingredient["id"], "ordered_qty": 5, "unit_cost": 1.2}],
            },
        )
    ).json()
    assert po["status"] == "requested"

    mark_in_transit = await client.patch(f"/api/v1/purchase-orders/{po['id']}", json={"action": "mark_in_transit", "approved_by": 1})
    assert mark_in_transit.status_code == 200
    assert mark_in_transit.json()["status"] == "in_transit"

    po_line = (
        await db_session.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po["id"]))
    ).scalars().first()
    assert po_line is not None

    partial_receipt = await client.post(
        f"/api/v1/purchase-orders/{po['id']}/receipts",
        json={"lines": [{"line_id": po_line.id, "received_qty": 3}], "discrepancy_notes": "supplier short ship"},
    )
    assert partial_receipt.status_code == 200
    assert partial_receipt.json()["status"] == "discrepancy"

    final_receipt = await client.post(
        f"/api/v1/purchase-orders/{po['id']}/receipts",
        json={"lines": [{"line_id": po_line.id, "received_qty": 2}]},
    )
    assert final_receipt.status_code == 200
    assert final_receipt.json()["status"] == "received"

    ingredient_row = await db_session.get(Ingredient, ingredient["id"])
    assert ingredient_row is not None
    assert ingredient_row.quantity_on_hand == 7

    ledger_rows = (
        await db_session.execute(
            select(StockLedgerEntry).where(
                StockLedgerEntry.reference_type == "purchase_order",
                StockLedgerEntry.reference_id == po["id"],
                StockLedgerEntry.reason == "goods_receipt",
            )
        )
    ).scalars().all()
    assert len(ledger_rows) == 2


@pytest.mark.asyncio
async def test_stock_count_variance_workflow(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "Count Branch", "tax_rate": 0.05, "service_charge_rate": 0.02})).json()
    ingredient = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/ingredients",
            json={"name": "Milk", "unit": "ltr", "quantity_on_hand": 10, "reorder_threshold": 2},
        )
    ).json()

    session = (
        await client.post(
            "/api/v1/inventory/stock-count-sessions",
            json={"branch_id": branch["id"], "opened_by": 3},
        )
    ).json()

    line = await client.post(
        f"/api/v1/inventory/stock-count-sessions/{session['id']}/lines",
        json={"ingredient_id": ingredient["id"], "counted_qty": 8, "notes": "breakage"},
    )
    assert line.status_code == 201
    assert line.json()["variance_qty"] == -2

    submitted = await client.patch(f"/api/v1/inventory/stock-count-sessions/{session['id']}/submit?submitted_by=3")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"

    reviewed = await client.patch(
        f"/api/v1/inventory/stock-count-sessions/{session['id']}/review",
        json={"action": "approve", "reviewer_id": 1},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "approved"

    ingredient_row = await db_session.get(Ingredient, ingredient["id"])
    assert ingredient_row is not None
    assert ingredient_row.quantity_on_hand == 8

    ledger_rows = (
        await db_session.execute(
            select(StockLedgerEntry).where(
                StockLedgerEntry.reference_type == "stock_count_session",
                StockLedgerEntry.reference_id == session["id"],
                StockLedgerEntry.reason == "stock_count_variance",
            )
        )
    ).scalars().all()
    assert len(ledger_rows) == 1
    assert ledger_rows[0].change_qty == -2
async def test_lifecycle_idempotency_and_operational_events(client):
    branch = (await client.post('/api/v1/branches', json={'name': 'Lifecycle', 'tax_rate': 0.1, 'service_charge_rate': 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={'code': 'L1', 'seats': 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={'name': 'Pasta', 'price': 12})).json()
    drawer = (await client.post(f"/api/v1/branches/{branch['id']}/drawer-sessions", json={'cashier_id': 22, 'opening_balance': 50})).json()

    reservation_payload = {
        'branch_id': branch['id'],
        'guest_name': 'Replay Guest',
        'guest_phone': '+14445556666',
        'party_size': 2,
        'reservation_time': '2026-04-10T19:00:00Z',
    }
    reservation = await client.post('/api/v1/reservations', json=reservation_payload, headers={'Idempotency-Key': 'life-rsv-create'})
    assert reservation.status_code == 201
    reservation_id = reservation.json()['id']

    reservation_replay = await client.post('/api/v1/reservations', json=reservation_payload, headers={'Idempotency-Key': 'life-rsv-create'})
    assert reservation_replay.status_code == 201
    assert reservation_replay.headers.get('X-Idempotent-Replay') == 'true'

    seated = await client.post(
        f"/api/v1/tables/{table['id']}/seat",
        json={'reservation_id': reservation_id, 'party_size': 2},
        headers={'Idempotency-Key': 'life-seat'},
    )
    assert seated.status_code == 200
    seated_replay = await client.post(
        f"/api/v1/tables/{table['id']}/seat",
        json={'reservation_id': reservation_id, 'party_size': 2},
        headers={'Idempotency-Key': 'life-seat'},
    )
    assert seated_replay.status_code == 200
    assert seated_replay.headers.get('X-Idempotent-Replay') == 'true'

    order = await client.post(
        '/api/v1/orders',
        json={
            'branch_id': branch['id'],
            'order_source': 'dine_in',
            'table_id': table['id'],
            'waiter_id': 4,
            'items': [{'menu_item_id': menu['id'], 'quantity': 2, 'course_no': 1}],
        },
        headers={'Idempotency-Key': 'life-order'},
    )
    assert order.status_code == 201
    order_id = order.json()['order']['id']
    bill_id = order.json()['bill']['id']

    order_patch = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={'status': 'in_progress'},
        headers={'Idempotency-Key': 'life-order-patch'},
    )
    assert order_patch.status_code == 200
    patch_replay = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={'status': 'in_progress'},
        headers={'Idempotency-Key': 'life-order-patch'},
    )
    assert patch_replay.status_code == 200
    assert patch_replay.headers.get('X-Idempotent-Replay') == 'true'

    tickets = await client.get('/api/v1/kitchen/tickets')
    ticket_id = tickets.json()['items'][0]['id']
    kitchen = await client.patch(
        f"/api/v1/kitchen/tickets/{ticket_id}",
        json={'status': 'in_preparation', 'updated_by': 9},
        headers={'Idempotency-Key': 'life-kitchen'},
    )
    assert kitchen.status_code == 200

    settlement = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={'cashier_id': 22, 'settlements': [{'payment_method': 'cash', 'amount': 27.6}]},
        headers={'Idempotency-Key': 'life-settlement'},
    )
    assert settlement.status_code == 200
    settlement_replay = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={'cashier_id': 22, 'settlements': [{'payment_method': 'cash', 'amount': 27.6}]},
        headers={'Idempotency-Key': 'life-settlement'},
    )
    assert settlement_replay.status_code == 200
    assert settlement_replay.headers.get('X-Idempotent-Replay') == 'true'

    close_drawer = await client.post(f"/api/v1/drawer-sessions/{drawer['id']}/close", json={'closing_balance': 77.6})
    assert close_drawer.status_code == 200

    day_close = await client.post(
        '/api/v1/day-close',
        json={'branch_id': branch['id'], 'business_date': '2026-04-10T00:00:00Z', 'notes': 'lifecycle close'},
        headers={'Idempotency-Key': 'life-day-close-open'},
    )
    assert day_close.status_code == 201
    day_close_id = day_close.json()['id']

    checklist = await client.post(f"/api/v1/day-close/{day_close_id}/checklist-items", json={'item_key': 'ops_review', 'is_required': True})
    assert checklist.status_code == 201
    checked = await client.patch(
        f"/api/v1/day-close/checklist-items/{checklist.json()['id']}",
        json={'checked_by': 22, 'is_checked': True},
    )
    assert checked.status_code == 200

    finalize = await client.patch(
        f"/api/v1/day-close/{day_close_id}/finalize",
        json={'closed_by': 22, 'notes': 'done'},
        headers={'Idempotency-Key': 'life-day-close-finalize'},
    )
    assert finalize.status_code == 200
    finalize_replay = await client.patch(
        f"/api/v1/day-close/{day_close_id}/finalize",
        json={'closed_by': 22, 'notes': 'done'},
        headers={'Idempotency-Key': 'life-day-close-finalize'},
    )
    assert finalize_replay.status_code == 200
    assert finalize_replay.headers.get('X-Idempotent-Replay') == 'true'

    ops_events = await client.get(f"/api/v1/operations/notifications?branch_id={branch['id']}&limit=200")
    assert ops_events.status_code == 200
    event_names = {row['event_name'] for row in ops_events.json()}
    assert 'reservation.created' in event_names
    assert 'table.seated' in event_names
    assert 'order.opened' in event_names
    assert 'settlement.completed' in event_names
    assert 'branch.day_closed' in event_names


@pytest.mark.asyncio
async def test_release_workflow_gate_scenarios(client):
    branch = (await client.post('/api/v1/branches', json={'name': 'GateFlow', 'tax_rate': 0.1, 'service_charge_rate': 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={'code': 'G1', 'seats': 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={'name': 'Ramen', 'price': 15})).json()

    reservation = (
        await client.post(
            '/api/v1/reservations',
            json={
                'branch_id': branch['id'],
                'guest_name': 'Gate Guest',
                'guest_phone': '+1555444000',
                'party_size': 2,
                'reservation_time': '2026-04-10T18:30:00Z',
            },
        )
    ).json()
    seated = await client.post(f"/api/v1/tables/{table['id']}/seat", json={'reservation_id': reservation['id'], 'party_size': 2})
    assert seated.status_code == 200

    order = (
        await client.post(
            '/api/v1/orders',
            json={
                'branch_id': branch['id'],
                'order_source': 'dine_in',
                'table_id': table['id'],
                'waiter_id': 12,
                'items': [{'menu_item_id': menu['id'], 'quantity': 1, 'course_no': 1}],
            },
        )
    ).json()

    kitchen = await client.get('/api/v1/kitchen/tickets')
    assert kitchen.status_code == 200
    ticket_id = kitchen.json()['items'][0]['id']
    assert (await client.patch(f'/api/v1/kitchen/tickets/{ticket_id}', json={'status': 'in_preparation'})).status_code == 200

    bill_id = order['bill']['id']
    settlement = await client.post(
        f'/api/v1/bills/{bill_id}/settlements',
        json={'cashier_id': 7, 'settlements': [{'payment_method': 'cash', 'amount': order['bill']['total_amount']}]},
    )
    assert settlement.status_code == 200
    assert settlement.json()['status'] == 'paid'

    export = (
        await client.post(
            '/api/v1/accounting-exports',
            json={'branch_id': branch['id'], 'business_date': '2026-04-10T00:00:00Z'},
            headers={'Idempotency-Key': 'gate-export-1'},
        )
    ).json()
    retry = await client.post(
        f"/api/v1/accounting-exports/{export['id']}/retry",
        json={'requested_by': 1, 'reason': 'network recovery run'},
    )
    assert retry.status_code == 201

    drawer = (
        await client.post(
            f"/api/v1/branches/{branch['id']}/drawer-sessions",
            json={'cashier_id': 7, 'opening_balance': 100},
        )
    ).json()
    day_close = (
        await client.post(
            '/api/v1/day-close',
            json={'branch_id': branch['id'], 'business_date': '2026-04-10T00:00:00Z', 'notes': 'gate validation'},
        )
    ).json()

    blocked_finalize = await client.patch(f"/api/v1/day-close/{day_close['id']}/finalize", json={'closed_by': 1})
    assert blocked_finalize.status_code == 409

    blockers = await client.get(f"/api/v1/day-close/{day_close['id']}/blockers")
    assert blockers.status_code == 200
    assert any(item["blocker_code"] == 'open_drawers' for item in blockers.json()['blockers'])

    closed = await client.post(
        f"/api/v1/drawer-sessions/{drawer['id']}/close",
        json={'closing_balance': 100},
    )
    assert closed.status_code == 200


@pytest.mark.asyncio
async def test_day_close_blocker_remediation_and_override_audit(client):
    branch = (await client.post('/api/v1/branches', json={'name': 'BlockerFlow', 'tax_rate': 0.1, 'service_charge_rate': 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={'code': 'B1', 'seats': 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={'name': 'Stew', 'price': 10})).json()
    drawer = (await client.post(f"/api/v1/branches/{branch['id']}/drawer-sessions", json={'cashier_id': 3, 'opening_balance': 50})).json()
    shift = await client.post(
        '/api/v1/shifts',
        json={'branch_id': branch['id'], 'staff_user_id': 22, 'role': 'cashier', 'starts_at': '2026-04-10T10:00:00Z', 'ends_at': '2026-04-10T18:00:00Z'},
    )
    assert shift.status_code == 201

    order = (
        await client.post(
            '/api/v1/orders',
            json={
                'branch_id': branch['id'],
                'order_source': 'dine_in',
                'table_id': table['id'],
                'waiter_id': 12,
                'items': [{'menu_item_id': menu['id'], 'quantity': 1, 'course_no': 1}],
            },
        )
    ).json()
    bill_id = order['bill']['id']
    settlement = await client.post(
        f'/api/v1/bills/{bill_id}/settlements',
        json={'cashier_id': 7, 'settlements': [{'payment_method': 'cash', 'amount': order['bill']['total_amount']}]},
    )
    assert settlement.status_code == 200
    refund = await client.post(
        '/api/v1/refunds',
        json={'branch_id': branch['id'], 'bill_id': bill_id, 'amount': 2, 'reason': 'test', 'approved_by': 1},
    )
    assert refund.status_code == 201
    export = await client.post('/api/v1/accounting-exports', json={'branch_id': branch['id'], 'business_date': '2026-04-10T00:00:00Z'})
    assert export.status_code == 201
    day_close = (await client.post('/api/v1/day-close', json={'branch_id': branch['id'], 'business_date': '2026-04-10T00:00:00Z'})).json()

    blocked = await client.patch(f"/api/v1/day-close/{day_close['id']}/finalize", json={'closed_by': 1})
    assert blocked.status_code == 409

    blockers = (await client.get(f"/api/v1/day-close/{day_close['id']}/blockers")).json()['blockers']
    codes = {row['blocker_code'] for row in blockers}
    assert {'open_drawers', 'unresolved_refunds', 'pending_exports', 'staffing_gaps'} <= codes

    assert (await client.post(f"/api/v1/day-close/{day_close['id']}/remediation/close-drawer/{drawer['id']}", json={'closed_by': 1})).status_code == 200
    assert (await client.post(f"/api/v1/day-close/{day_close['id']}/remediation/rerun-export/{export.json()['id']}", json={'requested_by': 1})).status_code == 201
    assert (await client.post(f"/api/v1/day-close/{day_close['id']}/remediation/resolve-refund/{refund.json()['id']}", json={'resolved_by': 1})).status_code == 200
    assert (await client.post(f"/api/v1/day-close/{day_close['id']}/remediation/acknowledge-staffing-gap", json={'acknowledged_by': 1})).status_code == 200

    finalize_override = await client.patch(
        f"/api/v1/day-close/{day_close['id']}/finalize",
        json={'closed_by': 1, 'privileged_override': True, 'override_reason': 'manager override after staffing acknowledgment'},
    )
    assert finalize_override.status_code == 200

    audits = await client.get(f"/api/v1/audit/privileged-actions?branch_id={branch['id']}")
    assert audits.status_code == 200
    actions = {row['action'] for row in audits.json()}
    assert 'day_close.override' in actions
    assert 'staffing.gap_override' in actions


@pytest.mark.asyncio
async def test_ops_outbox_retry_dispatch_success(client, monkeypatch):
    branch = (await client.post("/api/v1/branches", json={"name": "Outbox Branch", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    reservation = await client.post(
        "/api/v1/reservations",
        json={
            "branch_id": branch["id"],
            "guest_name": "Retry Guest",
            "guest_phone": "+1555111000",
            "party_size": 2,
            "reservation_time": "2026-04-12T18:30:00Z",
        },
    )
    assert reservation.status_code == 201

    attempts = {"count": 0}

    async def flaky_push_event_to_room(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("simulated disconnect")
        return None

    monkeypatch.setattr("src.apps.restaurant.services.ops_event_outbox.ws_manager.push_event_to_room", flaky_push_event_to_room)

    processed_first = await ops_event_outbox_dispatcher.dispatch_once()
    assert processed_first >= 1
    processed_second = await ops_event_outbox_dispatcher.dispatch_once()
    assert processed_second >= 1

    outbox_rows = (await client.get(f"/api/v1/operations/outbox?branch_id={branch['id']}")).json()
    assert outbox_rows
    assert outbox_rows[0]["status"] == OpsEventOutboxStatus.SENT.value
    assert outbox_rows[0]["attempt_count"] >= 2


@pytest.mark.asyncio
async def test_ops_outbox_dead_letter_requeue_and_replay(client, db_session, monkeypatch):
    branch = (await client.post("/api/v1/branches", json={"name": "DeadLetter Branch", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    row = OpsEventOutbox(
        branch_id=branch["id"],
        room=f"branch:{branch['id']}:ops",
        event_name="restaurant.synthetic.test",
        severity=OperationalSeverity.INFO,
        payload_json='{\"ok\": true}',
        status=OpsEventOutboxStatus.PENDING,
        max_attempts=1,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)

    async def always_fail(*args, **kwargs):
        raise RuntimeError("always fail")

    monkeypatch.setattr("src.apps.restaurant.services.ops_event_outbox.ws_manager.push_event_to_room", always_fail)
    processed = await ops_event_outbox_dispatcher.dispatch_once()
    assert processed >= 1

    failed_row = await db_session.get(OpsEventOutbox, row.id)
    assert failed_row is not None
    assert failed_row.status == OpsEventOutboxStatus.DEAD_LETTER

    requeue = await client.post(f"/api/v1/operations/outbox/{row.id}/requeue")
    assert requeue.status_code == 200
    assert requeue.json()["status"] == OpsEventOutboxStatus.RETRY.value

    async def always_ok(*args, **kwargs):
        return None

    monkeypatch.setattr("src.apps.restaurant.services.ops_event_outbox.ws_manager.push_event_to_room", always_ok)
    processed_replay = await ops_event_outbox_dispatcher.dispatch_once()
    assert processed_replay >= 1

    replayed_row = await db_session.get(OpsEventOutbox, row.id)
    assert replayed_row is not None
    assert replayed_row.status == OpsEventOutboxStatus.SENT


@pytest.mark.asyncio
async def test_ops_outbox_status_endpoint_lists_dead_letters(client):
    branch = (await client.post("/api/v1/branches", json={"name": "Inspect Branch", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    reservation = await client.post(
        "/api/v1/reservations",
        json={
            "branch_id": branch["id"],
            "guest_name": "Inspect Guest",
            "guest_phone": "+1555222000",
            "party_size": 2,
            "reservation_time": "2026-04-12T19:30:00Z",
        },
    )
    assert reservation.status_code == 201

    status_all = await client.get(f"/api/v1/operations/outbox?branch_id={branch['id']}")
    assert status_all.status_code == 200
    assert len(status_all.json()) >= 1


@pytest.mark.asyncio
async def test_transition_validation_matrix_and_settlement_rollback(client):
    branch = (await client.post("/api/v1/branches", json={"name": "Matrix", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "M1", "seats": 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Pasta", "price": 10})).json()

    reservation = (
        await client.post(
            "/api/v1/reservations",
            json={
                "branch_id": branch["id"],
                "guest_name": "Matrix Guest",
                "guest_phone": "+1001001000",
                "party_size": 2,
                "reservation_time": "2026-04-12T18:00:00Z",
            },
        )
    ).json()
    invalid_reservation = await client.patch(f"/api/v1/reservations/{reservation['id']}", json={"status": "seated"})
    assert invalid_reservation.status_code == 409
    assert invalid_reservation.json()["detail"]["code"] == "reservation.invalid_transition"

    order_payload = (
        await client.post(
            "/api/v1/orders",
            json={
                "branch_id": branch["id"],
                "order_source": "dine_in",
                "table_id": table["id"],
                "waiter_id": 12,
                "items": [{"menu_item_id": menu["id"], "quantity": 1, "course_no": 1}],
            },
        )
    ).json()
    order_id = order_payload["order"]["id"]
    bill_id = order_payload["bill"]["id"]

    invalid_order = await client.patch(f"/api/v1/orders/{order_id}", json={"status": "draft"})
    assert invalid_order.status_code == 409
    assert invalid_order.json()["detail"]["code"] == "order.invalid_transition"

    ticket_id = (await client.get("/api/v1/kitchen/tickets")).json()["items"][0]["id"]
    invalid_ticket = await client.patch(f"/api/v1/kitchen/tickets/{ticket_id}", json={"status": "served"})
    assert invalid_ticket.status_code == 409
    assert invalid_ticket.json()["detail"]["code"] == "kitchen_ticket.invalid_transition"

    settlement = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 300, "settlements": [{"payment_method": "cash", "amount": 11.5}]},
    )
    assert settlement.status_code == 409
    assert settlement.json()["detail"]["code"] == "settlement.drawer_session_required"

    no_change_bill = await client.get(f"/api/v1/bills/{bill_id}")
    assert no_change_bill.status_code == 200
    assert no_change_bill.json()["status"] == "open"
    assert no_change_bill.json()["paid_amount"] == 0

    drawer = await client.post(
        f"/api/v1/branches/{branch['id']}/drawer-sessions",
        json={"cashier_id": 300, "opening_balance": 50},
    )
    assert drawer.status_code == 201

    valid_settlement = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 300, "settlements": [{"payment_method": "cash", "amount": 11.5}]},
    )
    assert valid_settlement.status_code == 200
    assert valid_settlement.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_stock_transfer_partial_and_over_receipt_variance(client):
    source = (await client.post("/api/v1/branches", json={"name": "Transfer Src", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    dest = (await client.post("/api/v1/branches", json={"name": "Transfer Dest", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    src_ing = (await client.post(f"/api/v1/branches/{source['id']}/ingredients", json={"name": "Flour", "unit": "kg", "quantity_on_hand": 30, "reorder_threshold": 5})).json()
    dst_ing = (await client.post(f"/api/v1/branches/{dest['id']}/ingredients", json={"name": "Flour", "unit": "kg", "quantity_on_hand": 0, "reorder_threshold": 1})).json()

    transfer = (await client.post("/api/v1/stock-transfers", json={
        "from_branch_id": source["id"],
        "to_branch_id": dest["id"],
        "from_ingredient_id": src_ing["id"],
        "to_ingredient_id": dst_ing["id"],
        "quantity": 10,
    })).json()

    in_transit = await client.patch(f"/api/v1/stock-transfers/{transfer['id']}", json={
        "action": "mark_in_transit",
        "acknowledged_by": 11,
        "acknowledgement_note": "truck dispatched",
        "shipped_qty": 10,
    })
    assert in_transit.status_code == 200
    assert in_transit.json()["status"] == "in_transit"

    partial = await client.patch(f"/api/v1/stock-transfers/{transfer['id']}", json={
        "action": "mark_received",
        "acknowledged_by": 22,
        "acknowledgement_note": "short landed",
        "received_qty": 7,
        "discrepancy_notes": "3kg missing",
    })
    assert partial.status_code == 200
    assert partial.json()["status"] == "discrepancy"

    transfer_over = (await client.post("/api/v1/stock-transfers", json={
        "from_branch_id": source["id"],
        "to_branch_id": dest["id"],
        "from_ingredient_id": src_ing["id"],
        "to_ingredient_id": dst_ing["id"],
        "quantity": 5,
    })).json()
    await client.patch(f"/api/v1/stock-transfers/{transfer_over['id']}", json={
        "action": "mark_in_transit",
        "acknowledged_by": 11,
        "acknowledgement_note": "truck dispatched",
        "shipped_qty": 5,
    })
    over = await client.patch(f"/api/v1/stock-transfers/{transfer_over['id']}", json={
        "action": "mark_received",
        "acknowledged_by": 22,
        "acknowledgement_note": "received extra",
        "received_qty": 6,
        "discrepancy_notes": "supplier over-shipped",
    })
    assert over.status_code == 200
    assert over.json()["status"] == "discrepancy"


@pytest.mark.asyncio
async def test_stock_count_mismatch_requires_review_outcome(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "Count Review", "tax_rate": 0.05, "service_charge_rate": 0.02})).json()
    ing = (await client.post(f"/api/v1/branches/{branch['id']}/ingredients", json={"name": "Oil", "unit": "ltr", "quantity_on_hand": 25, "reorder_threshold": 5})).json()
    session = (await client.post("/api/v1/inventory/stock-count-sessions", json={"branch_id": branch["id"], "opened_by": 9})).json()
    await client.post(f"/api/v1/inventory/stock-count-sessions/{session['id']}/lines", json={"ingredient_id": ing["id"], "counted_qty": 18, "notes": "major leak"})
    await client.patch(f"/api/v1/inventory/stock-count-sessions/{session['id']}/submit?submitted_by=9")

    reject = await client.patch(
        f"/api/v1/inventory/stock-count-sessions/{session['id']}/review",
        json={"action": "reject", "reviewer_id": 2, "rejection_reason": "recount required"},
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

    session2 = (await client.post("/api/v1/inventory/stock-count-sessions", json={"branch_id": branch["id"], "opened_by": 9})).json()
    await client.post(f"/api/v1/inventory/stock-count-sessions/{session2['id']}/lines", json={"ingredient_id": ing["id"], "counted_qty": 18, "notes": "major leak"})
    await client.patch(f"/api/v1/inventory/stock-count-sessions/{session2['id']}/submit?submitted_by=9")
    approve = await client.patch(
        f"/api/v1/inventory/stock-count-sessions/{session2['id']}/review",
        json={"action": "approve", "reviewer_id": 1},
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    ledger_rows = (await db_session.execute(select(StockLedgerEntry).where(
        StockLedgerEntry.reference_type == "stock_count_session",
        StockLedgerEntry.reference_id == session2["id"],
    ))).scalars().all()
    assert len(ledger_rows) == 1


@pytest.mark.asyncio
async def test_recipe_reversal_after_order_void_and_refund(client, db_session):
    branch = (await client.post("/api/v1/branches", json={"name": "Lifecycle Stock", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "S1", "seats": 2})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Soup", "price": 8})).json()
    ingredient = (await client.post(f"/api/v1/branches/{branch['id']}/ingredients", json={"name": "Stock", "unit": "ltr", "quantity_on_hand": 20, "reorder_threshold": 4})).json()
    await client.post("/api/v1/recipes", json={"branch_id": branch["id"], "name": menu["name"], "items": [{"ingredient_id": ingredient["id"], "quantity": 1}]})

    order_payload = (await client.post("/api/v1/orders", json={
        "branch_id": branch["id"],
        "order_source": "dine_in",
        "table_id": table["id"],
        "waiter_id": 10,
        "items": [{"menu_item_id": menu["id"], "quantity": 2, "course_no": 1}],
    })).json()
    order_id = order_payload["order"]["id"]
    bill_id = order_payload["bill"]["id"]
    ing_row = await db_session.get(Ingredient, ingredient["id"])
    assert ing_row.quantity_on_hand == 18

    approval = (await client.post("/api/v1/orders/edit-approvals", json={"order_id": order_id, "requested_by": 10, "reason": "void"})).json()
    await client.patch(f"/api/v1/orders/edit-approvals/{approval['id']}", json={"approved_by": 1, "status": "approved"})
    cancel = await client.patch(f"/api/v1/orders/{order_id}", json={"status": "cancelled", "edit_approval_id": approval["id"]})
    assert cancel.status_code == 200
    ing_after_cancel = await db_session.get(Ingredient, ingredient["id"])
    assert ing_after_cancel.quantity_on_hand == 20

    drawer = await client.post(f"/api/v1/branches/{branch['id']}/drawer-sessions", json={"cashier_id": 10, "opening_balance": 100})
    assert drawer.status_code == 201
    await client.post(f"/api/v1/bills/{bill_id}/settlements", json={"cashier_id": 10, "settlements": [{"payment_method": "cash", "amount": 17.2}]})
    refund = await client.post("/api/v1/refunds", json={"branch_id": branch["id"], "bill_id": bill_id, "amount": 17.2, "reason": "voided ticket", "approved_by": 1})
    assert refund.status_code == 201
    ing_after_refund = await db_session.get(Ingredient, ingredient["id"])
    assert ing_after_refund.quantity_on_hand == 20
