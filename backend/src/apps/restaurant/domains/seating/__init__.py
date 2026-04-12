"""Seating domain utilities."""

from dataclasses import dataclass

RESERVATION_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"seated", "cancelled"},
    "seated": set(),
    "cancelled": set(),
}


@dataclass(frozen=True)
class SeatingDecision:
    can_seat: bool
    reason: str | None = None


def evaluate_table_assignment(*, table_seats: int, party_size: int, is_occupied: bool) -> SeatingDecision:
    if party_size <= 0:
        return SeatingDecision(False, "Party size must be positive")
    if is_occupied:
        return SeatingDecision(False, "Table already occupied")
    if party_size > table_seats:
        return SeatingDecision(False, "Party size exceeds table capacity")
    return SeatingDecision(True)


def validate_reservation_transition(*, current_status: str, next_status: str) -> tuple[bool, str]:
    allowed = RESERVATION_ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None:
        return False, "Unknown reservation status"
    if next_status not in allowed:
        return False, "Reservation status transition is not allowed"
    return True, ""
