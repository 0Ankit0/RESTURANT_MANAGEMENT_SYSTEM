"""Menu domain utilities."""


def line_total(unit_price: float, quantity: int) -> float:
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    return round(unit_price * quantity, 2)


def validate_modifier_selection(*, min_select: int, max_select: int, selected: int) -> bool:
    if min_select < 0 or max_select < 1 or min_select > max_select:
        raise ValueError("Invalid modifier constraints")
    return min_select <= selected <= max_select
