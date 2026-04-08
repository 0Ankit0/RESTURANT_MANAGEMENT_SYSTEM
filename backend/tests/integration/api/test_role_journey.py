import pytest


@pytest.mark.asyncio
async def test_role_journey_guest_to_manager(client):
    branch = (await client.post("/api/v1/branches", json={"name": "Journey", "tax_rate": 0.1, "service_charge_rate": 0.05})).json()
    table = (await client.post(f"/api/v1/branches/{branch['id']}/tables", json={"code": "J1", "seats": 4})).json()
    menu = (await client.post(f"/api/v1/branches/{branch['id']}/menu-items", json={"name": "Journey Meal", "price": 12})).json()

    # guest -> reservation
    reservation = (
        await client.post(
            "/api/v1/reservations",
            json={
                "branch_id": branch["id"],
                "guest_name": "Guest",
                "guest_phone": "+10000000000",
                "party_size": 2,
                "reservation_time": "2026-03-26T18:00:00Z",
            },
        )
    ).json()

    # host -> seat reservation
    seat = await client.post(f"/api/v1/tables/{table['id']}/seat", json={"reservation_id": reservation["id"], "party_size": 2})
    assert seat.status_code == 200

    # waiter -> order
    order = (
        await client.post(
            "/api/v1/orders",
            json={
                "branch_id": branch["id"],
                "order_source": "dine_in",
                "table_id": table["id"],
                "waiter_id": 101,
                "items": [{"menu_item_id": menu["id"], "quantity": 1, "course_no": 1}],
            },
        )
    ).json()

    # chef -> transition ticket
    tickets = (await client.get("/api/v1/kitchen/tickets")).json()["items"]
    patch = await client.patch(
        f"/api/v1/kitchen/tickets/{tickets[0]['id']}",
        json={"status": "in_preparation", "updated_by": 202},
    )
    assert patch.status_code == 200

    # cashier -> settle bill
    bill_id = order["bill"]["id"]
    settle = await client.post(
        f"/api/v1/bills/{bill_id}/settlements",
        json={"cashier_id": 303, "settlements": [{"payment_method": "cash", "amount": order["bill"]["total_amount"]}]},
    )
    assert settle.status_code == 200

    # manager -> day close + manifests
    day_close = (
        await client.post(
            "/api/v1/day-close",
            json={"branch_id": branch["id"], "business_date": "2026-03-26T00:00:00Z", "notes": "journey"},
        )
    ).json()
    checklist = (
        await client.post(
            f"/api/v1/day-close/{day_close['id']}/checklist-items",
            json={"item_key": "ops_done", "is_required": True},
        )
    ).json()
    done = await client.patch(f"/api/v1/day-close/checklist-items/{checklist['id']}", json={"checked_by": 404, "is_checked": True})
    assert done.status_code == 200

    finalize = await client.patch(f"/api/v1/day-close/{day_close['id']}/finalize", json={"closed_by": 404})
    assert finalize.status_code == 200

    shells = await client.get("/api/v1/client/role-shells")
    flows = await client.get("/api/v1/client/mobile-role-flows")
    assert shells.status_code == 200
    assert flows.status_code == 200
