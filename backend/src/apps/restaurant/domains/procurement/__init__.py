"""Procurement domain utilities."""


TERMINAL_PO_STATES = {"received", "discrepancy"}


def outstanding_quantity(*, ordered_qty: float, received_qty: float) -> float:
    if ordered_qty < 0 or received_qty < 0:
        raise ValueError("Quantities cannot be negative")
    if received_qty > ordered_qty:
        raise ValueError("Received quantity cannot exceed ordered quantity")
    return round(ordered_qty - received_qty, 3)


def po_status(*, lines_fully_received: int, total_lines: int, has_discrepancy: bool = False) -> str:
    if total_lines <= 0:
        raise ValueError("Purchase order must include lines")
    if lines_fully_received < 0:
        raise ValueError("Received line count cannot be negative")
    if lines_fully_received > total_lines:
        raise ValueError("Received line count cannot exceed total lines")
    if lines_fully_received == total_lines:
        return "received"
    if has_discrepancy:
        return "discrepancy"
    if lines_fully_received > 0:
        return "partial"
    return "in_transit"


def enforce_po_transition(*, current_status: str, action: str) -> str:
    transitions = {
        "requested": {"mark_in_transit": "in_transit"},
        "in_transit": {"mark_received": "partial", "mark_discrepancy": "discrepancy"},
        "partial": {"mark_received": "partial", "mark_discrepancy": "discrepancy"},
        "discrepancy": {"mark_received": "partial"},
    }
    if current_status in TERMINAL_PO_STATES:
        raise ValueError("Purchase order already resolved")
    target = transitions.get(current_status, {}).get(action)
    if not target:
        raise ValueError(f"Invalid purchase order transition from {current_status} via {action}")
    return target
