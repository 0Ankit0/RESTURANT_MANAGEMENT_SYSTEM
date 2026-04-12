"""Reporting domain utilities."""

from datetime import UTC, datetime

DAY_CLOSE_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"closed"},
    "closed": set(),
}


def build_branch_snapshot(*, branch_id: int, orders_count: int, gross_sales: float, collected_sales: float) -> dict:
    return {
        "branch_id": branch_id,
        "orders_count": max(0, orders_count),
        "gross_sales": round(max(0.0, gross_sales), 2),
        "collected_sales": round(max(0.0, collected_sales), 2),
        "generated_at": datetime.now(UTC),
    }


def validate_day_close_transition(*, current_status: str, next_status: str) -> tuple[bool, str]:
    allowed = DAY_CLOSE_ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None:
        return False, "Unknown day-close status"
    if next_status not in allowed:
        return False, "Day-close status transition is not allowed"
    return True, ""
