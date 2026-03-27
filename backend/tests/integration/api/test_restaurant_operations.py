import pytest
from sqlmodel import select

from src.apps.restaurant.models import PurchaseOrderLine


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
        json={"ingredient_id": ingredient["id"], "change_qty": -1, "reason": "prep_usage"},
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
    assert any(item["id"] == goods_receipt_id for item in res.json())

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

    res = await client.patch(f"/api/v1/stock-transfers/{transfer_id}", json={"approved_by": 1, "status": "approved"})
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    res = await client.get(f"/api/v1/stock-transfers?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(item["id"] == transfer_id for item in res.json())

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
    assert len(res.json()) >= 1

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

    replay = await client.post(
        "/api/v1/accounting-exports",
        json={"branch_id": branch["id"], "business_date": "2026-03-25T00:00:00Z"},
        headers={"Idempotency-Key": "exp-1"},
    )
    assert replay.status_code == 201
    assert replay.headers.get("X-Idempotent-Replay") == "true"

    res = await client.get(f"/api/v1/accounting-exports?branch_id={branch['id']}")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = await client.post(
        "/api/v1/day-close",
        json={"branch_id": branch["id"], "business_date": "2026-03-25T00:00:00Z", "notes": "closing"},
    )
    assert res.status_code == 201
    day_close_id = res.json()["id"]

    res = await client.patch(f"/api/v1/day-close/{day_close_id}/finalize", json={"closed_by": 1, "notes": "all clear"})
    assert res.status_code == 200
    assert res.json()["status"] == "closed"

    res = await client.get(f"/api/v1/day-close?branch_id={branch['id']}")
    assert res.status_code == 200
    assert any(row["id"] == day_close_id for row in res.json())

    res = await client.get(f"/api/v1/reports/branch-operations?branch_id={branch['id']}")
    assert res.status_code == 200
    assert res.json()["orders_count"] >= 1
    assert res.json()["collected_sales"] >= 34.5

    res = await client.patch(f"/api/v1/admin/branch-policies/{policy['id']}", json={"value": "15"})
    assert res.status_code == 200
    assert res.json()["value"] == "15"
