"""Orders domain utilities."""

from collections.abc import Iterable

ORDER_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"in_progress", "ready", "served", "cancelled"},
    "in_progress": {"ready", "served", "cancelled"},
    "ready": {"served", "cancelled"},
    "served": set(),
    "cancelled": set(),
}


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


def validate_order_transition(*, current_status: str, next_status: str) -> tuple[bool, str]:
    allowed = ORDER_ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None:
        return False, "Unknown order status"
    if next_status not in allowed:
        return False, "Order status transition is not allowed"
    return True, ""
