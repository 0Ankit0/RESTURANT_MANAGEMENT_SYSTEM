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


def recipe_component_delta(component_qty: float, item_qty: int, *, reverse: bool = False) -> float:
    if component_qty <= 0 or item_qty <= 0:
        raise ValueError("Recipe component and item quantities must be positive")
    change = round(component_qty * item_qty, 3)
    return change if reverse else -change


def reconcile_inventory_target(current_net: float, target_net: float) -> float:
    """Return delta needed to move current net movement to target net movement."""
    return round(target_net - current_net, 3)
