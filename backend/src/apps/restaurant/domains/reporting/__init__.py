"""Reporting domain utilities."""

from datetime import UTC, datetime


def build_branch_snapshot(*, branch_id: int, orders_count: int, gross_sales: float, collected_sales: float) -> dict:
    return {
        "branch_id": branch_id,
        "orders_count": max(0, orders_count),
        "gross_sales": round(max(0.0, gross_sales), 2),
        "collected_sales": round(max(0.0, collected_sales), 2),
        "generated_at": datetime.now(UTC),
    }
