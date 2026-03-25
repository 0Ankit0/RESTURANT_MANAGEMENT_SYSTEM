"""Backward-compatible push helpers backed by the communications service."""
from typing import Any

from src.apps.communications import get_communications_service


def send_push_notification(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
    extra_data: Any = None,
) -> bool:
    result = get_communications_service().send_push(
        {
            "provider": "webpush",
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth,
            "title": title,
            "body": body,
            "data": extra_data,
        }
    )
    return result.success
