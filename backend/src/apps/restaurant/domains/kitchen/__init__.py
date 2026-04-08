"""Kitchen domain utilities."""


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"in_preparation", "voided"},
    "in_preparation": {"ready", "delayed", "voided"},
    "delayed": {"in_preparation", "ready", "voided"},
    "ready": {"served", "voided"},
    "served": set(),
    "voided": set(),
}


def can_transition_ticket(*, current_status: str, next_status: str) -> bool:
    allowed = _ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None:
        return False
    return next_status in allowed
