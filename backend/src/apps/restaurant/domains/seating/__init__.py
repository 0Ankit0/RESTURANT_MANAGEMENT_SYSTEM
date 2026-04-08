"""Seating domain utilities."""

from dataclasses import dataclass


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
