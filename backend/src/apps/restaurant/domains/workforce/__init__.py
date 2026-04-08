"""Workforce domain utilities."""

from datetime import datetime


def validate_shift_window(*, starts_at: datetime, ends_at: datetime) -> bool:
    return ends_at > starts_at


def attendance_state(*, check_in_at: datetime, check_out_at: datetime | None) -> str:
    if check_out_at is None:
        return "present"
    if check_out_at < check_in_at:
        return "invalid"
    return "checked_out"
