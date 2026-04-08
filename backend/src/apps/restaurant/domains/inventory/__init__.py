"""Inventory domain utilities."""


def apply_inventory_delta(current_qty: float, delta: float) -> float:
    next_qty = round(current_qty + delta, 3)
    if next_qty < 0:
        raise ValueError("Inventory cannot go negative")
    return next_qty


def variance(expected_qty: float, counted_qty: float) -> float:
    if expected_qty < 0 or counted_qty < 0:
        raise ValueError("Quantities cannot be negative")
    return round(counted_qty - expected_qty, 3)
