import pytest

from src.apps.restaurant.domains.access import RestaurantRole, resolve_action, role_can_access_action
from src.apps.restaurant.domains.billing import apply_settlement, bill_totals
from src.apps.restaurant.domains.inventory import apply_inventory_delta
from src.apps.restaurant.domains.kitchen import can_transition_ticket
from src.apps.restaurant.domains.procurement import po_status


def test_tax_and_settlement_rounding_and_guards():
    totals = bill_totals(subtotal=19.995, tax_rate=0.13, service_charge_rate=0.1)
    assert totals == {
        "subtotal": 20.0,
        "tax_amount": 2.6,
        "service_charge": 2.0,
        "total_amount": 24.6,
    }

    paid, status = apply_settlement(paid_amount=10.0, incoming_amount=5.25, total_amount=24.6)
    assert paid == 15.25
    assert status == "partially_paid"

    with pytest.raises(ValueError, match="Settlement exceeds bill amount"):
        apply_settlement(paid_amount=24.0, incoming_amount=1.0, total_amount=24.6)


def test_routing_logic_transition_rules():
    assert can_transition_ticket(current_status="queued", next_status="in_preparation")
    assert can_transition_ticket(current_status="in_preparation", next_status="ready")
    assert not can_transition_ticket(current_status="ready", next_status="in_preparation")
    assert not can_transition_ticket(current_status="unknown", next_status="ready")


def test_recipe_depletion_guard_via_inventory_delta():
    assert apply_inventory_delta(4.5, -2.0) == 2.5
    with pytest.raises(ValueError, match="Inventory cannot go negative"):
        apply_inventory_delta(0.25, -0.5)


def test_procurement_reconciliation_statuses():
    assert po_status(lines_fully_received=0, total_lines=3) == "open"
    assert po_status(lines_fully_received=2, total_lines=3) == "partial"
    assert po_status(lines_fully_received=3, total_lines=3) == "received"


def test_security_branch_scoping_and_approval_restrictions():
    approval_action = resolve_action("/api/v1/discount-approvals")
    assert approval_action == "approval.discount"

    assert role_can_access_action(role=RestaurantRole.BRANCH_MANAGER, action=approval_action)
    assert not role_can_access_action(role=RestaurantRole.CASHIER, action=approval_action)
    assert role_can_access_action(role=RestaurantRole.ACCOUNTANT, action="billing.refund")
