import unittest
from datetime import UTC, datetime, timedelta

from src.apps.restaurant.domains.billing import apply_settlement, bill_totals
from src.apps.restaurant.domains.inventory import apply_inventory_delta, variance
from src.apps.restaurant.domains.kitchen import can_transition_ticket
from src.apps.restaurant.domains.menu import line_total, validate_modifier_selection
from src.apps.restaurant.domains.orders import can_patch_order, order_subtotal
from src.apps.restaurant.domains.procurement import enforce_po_transition, outstanding_quantity, po_status
from src.apps.restaurant.domains.reporting import build_branch_snapshot
from src.apps.restaurant.domains.seating import evaluate_table_assignment
from src.apps.restaurant.domains.workforce import attendance_state, validate_shift_window


class DomainUtilitiesTests(unittest.TestCase):
    def test_seating_decision(self):
        self.assertTrue(evaluate_table_assignment(table_seats=4, party_size=2, is_occupied=False).can_seat)
        self.assertFalse(evaluate_table_assignment(table_seats=4, party_size=6, is_occupied=False).can_seat)

    def test_menu_helpers(self):
        self.assertEqual(line_total(10.0, 3), 30.0)
        self.assertTrue(validate_modifier_selection(min_select=0, max_select=2, selected=1))

    def test_orders_helpers(self):
        self.assertEqual(order_subtotal([10.0, 2.5]), 12.5)
        self.assertFalse(can_patch_order(is_cancelled=False, has_fired_tickets=True, has_approval=False))

    def test_kitchen_transitions(self):
        self.assertTrue(can_transition_ticket(current_status="queued", next_status="in_preparation"))
        self.assertFalse(can_transition_ticket(current_status="served", next_status="ready"))

    def test_inventory_helpers(self):
        self.assertEqual(apply_inventory_delta(2.0, -1.0), 1.0)
        self.assertEqual(variance(10.0, 8.5), -1.5)

    def test_procurement_helpers(self):
        self.assertEqual(outstanding_quantity(ordered_qty=10, received_qty=4), 6)
        self.assertEqual(po_status(lines_fully_received=0, total_lines=2), "in_transit")
        self.assertEqual(po_status(lines_fully_received=1, total_lines=2), "partial")
        self.assertEqual(po_status(lines_fully_received=1, total_lines=2, has_discrepancy=True), "discrepancy")
        self.assertEqual(enforce_po_transition(current_status="requested", action="mark_in_transit"), "in_transit")

    def test_billing_helpers(self):
        totals = bill_totals(subtotal=100, tax_rate=0.1, service_charge_rate=0.05)
        self.assertEqual(totals["total_amount"], 115.0)
        paid, status = apply_settlement(paid_amount=50, incoming_amount=65, total_amount=115)
        self.assertEqual((paid, status), (115.0, "paid"))

    def test_workforce_and_reporting_helpers(self):
        now = datetime.now(UTC)
        self.assertTrue(validate_shift_window(starts_at=now, ends_at=now + timedelta(hours=1)))
        self.assertEqual(attendance_state(check_in_at=now, check_out_at=None), "present")
        snapshot = build_branch_snapshot(branch_id=1, orders_count=5, gross_sales=100, collected_sales=90)
        self.assertEqual(snapshot["branch_id"], 1)


if __name__ == "__main__":
    unittest.main()
