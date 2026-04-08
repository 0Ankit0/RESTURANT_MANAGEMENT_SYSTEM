"""Procurement domain utilities."""


def outstanding_quantity(*, ordered_qty: float, received_qty: float) -> float:
    if ordered_qty < 0 or received_qty < 0:
        raise ValueError("Quantities cannot be negative")
    if received_qty > ordered_qty:
        raise ValueError("Received quantity cannot exceed ordered quantity")
    return round(ordered_qty - received_qty, 3)


def po_status(*, lines_fully_received: int, total_lines: int) -> str:
    if total_lines <= 0:
        raise ValueError("Purchase order must include lines")
    if lines_fully_received <= 0:
        return "open"
    if lines_fully_received < total_lines:
        return "partial"
    return "received"
