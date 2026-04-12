import pytest

from src.apps.restaurant.domains.access import RestaurantRole, resolve_action, role_can_access_action
from src.apps.restaurant.domains.billing import apply_settlement, bill_totals
from src.apps.restaurant.domains.inventory import apply_inventory_delta, recipe_component_delta
from src.apps.restaurant.domains.procurement import enforce_po_transition, outstanding_quantity, po_status


@pytest.mark.parametrize(
    ("subtotal", "tax_rate", "service_charge_rate", "expected_total"),
    [
        (135.555, 0.13, 0.1, 166.07),
        (0.0, 0.1, 0.05, 0.0),
        (59.99, 0.0, 0.1, 65.99),
    ],
)
def test_billing_totals_rounding_matrix(subtotal: float, tax_rate: float, service_charge_rate: float, expected_total: float):
    totals = bill_totals(subtotal=subtotal, tax_rate=tax_rate, service_charge_rate=service_charge_rate)
    assert totals["total_amount"] == expected_total


def test_billing_settlement_multi_step_lifecycle():
    total_amount = 47.35

    paid_amount, status = apply_settlement(paid_amount=0.0, incoming_amount=20.0, total_amount=total_amount)
    assert (paid_amount, status) == (20.0, "partially_paid")

    paid_amount, status = apply_settlement(paid_amount=paid_amount, incoming_amount=27.35, total_amount=total_amount)
    assert (paid_amount, status) == (47.35, "paid")

    with pytest.raises(ValueError, match="Settlement exceeds bill amount"):
        apply_settlement(paid_amount=47.35, incoming_amount=0.01, total_amount=total_amount)


@pytest.mark.parametrize(
    ("ordered_qty", "received_qty", "expected"),
    [
        (20.0, 0.0, 20.0),
        (20.0, 7.125, 12.875),
        (20.0, 20.0, 0.0),
    ],
)
def test_procurement_outstanding_quantity_precision(ordered_qty: float, received_qty: float, expected: float):
    assert outstanding_quantity(ordered_qty=ordered_qty, received_qty=received_qty) == expected


@pytest.mark.parametrize(
    ("lines_fully_received", "total_lines", "has_discrepancy", "expected"),
    [
        (0, 4, False, "in_transit"),
        (2, 4, False, "partial"),
        (2, 4, True, "discrepancy"),
        (4, 4, False, "received"),
    ],
)
def test_procurement_status_resolution(lines_fully_received: int, total_lines: int, has_discrepancy: bool, expected: str):
    assert po_status(lines_fully_received=lines_fully_received, total_lines=total_lines, has_discrepancy=has_discrepancy) == expected


def test_procurement_transition_guards_terminal_states():
    assert enforce_po_transition(current_status="requested", action="mark_in_transit") == "in_transit"
    assert enforce_po_transition(current_status="in_transit", action="mark_received") == "partial"

    with pytest.raises(ValueError, match="Purchase order already resolved"):
        enforce_po_transition(current_status="received", action="mark_discrepancy")


@pytest.mark.parametrize(
    ("component_qty", "item_qty", "reverse", "expected"),
    [
        (0.35, 4, False, -1.4),
        (0.35, 4, True, 1.4),
    ],
)
def test_inventory_depletion_and_reversal(component_qty: float, item_qty: int, reverse: bool, expected: float):
    delta = recipe_component_delta(component_qty=component_qty, item_qty=item_qty, reverse=reverse)
    assert delta == expected


def test_inventory_stock_cannot_drop_below_zero_when_reversing_sequences():
    qty = 3.0
    qty = apply_inventory_delta(qty, recipe_component_delta(component_qty=0.5, item_qty=2))
    assert qty == 2.0
    qty = apply_inventory_delta(qty, recipe_component_delta(component_qty=0.5, item_qty=1, reverse=True))
    assert qty == 2.5

    with pytest.raises(ValueError, match="Inventory cannot go negative"):
        apply_inventory_delta(qty, -3.0)


def test_access_control_mapping_for_branch_sensitive_operations():
    assert resolve_action("/api/v1/orders/123") == "orders.manage"
    assert resolve_action("/api/v1/kitchen/tickets") == "kitchen.manage"
    assert resolve_action("/api/v1/accounting-exports/5/retry") == "reporting.view"

    assert role_can_access_action(role=RestaurantRole.BRANCH_MANAGER, action="orders.manage")
    assert not role_can_access_action(role=RestaurantRole.CHEF, action="billing.refund")
    assert role_can_access_action(role=RestaurantRole.ACCOUNTANT, action="billing.settle")
