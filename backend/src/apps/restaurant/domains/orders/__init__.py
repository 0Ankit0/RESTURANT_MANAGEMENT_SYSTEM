"""Orders domain utilities."""

from collections.abc import Iterable


def order_subtotal(line_totals: Iterable[float]) -> float:
    total = 0.0
    for amount in line_totals:
        if amount < 0:
            raise ValueError("Line totals cannot be negative")
        total += amount
    return round(total, 2)


def can_patch_order(*, is_cancelled: bool, has_fired_tickets: bool, has_approval: bool) -> bool:
    if is_cancelled:
        return False
    if has_fired_tickets and not has_approval:
        return False
    return True
