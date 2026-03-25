"""Backward-compatible SMS helper backed by the communications service."""

from src.apps.communications import get_communications_service


def send_sms_notification(
    to_number: str,
    body: str,
) -> bool:
    result = get_communications_service().send_sms(to_number=to_number, body=body)
    return result.success
