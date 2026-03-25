"""Notification-specific Celery tasks (email copy, push, SMS)."""
import logging
from pathlib import Path
from typing import Any, Dict, List

from celery import shared_task

from src.apps.core.celery_app import celery_app  # noqa: F401 — bind tasks to configured app

logger = logging.getLogger(__name__)

# Templates live in this module — resolved once at import time so Celery
# workers (which run in a separate process) get the correct absolute path.
NOTIFICATION_TEMPLATE_DIR = str(Path(__file__).resolve().parent.parent / "templates")


@shared_task(name="send_notification_email_task")
def send_notification_email_task(
    recipients: List[Dict[str, str]],
    subject: str,
    context: Dict[str, Any],
) -> bool:
    """Send an email copy of a notification using the notification module template."""
    from src.apps.core.tasks import send_email_task

    return send_email_task(
        subject=subject,
        recipients=recipients,
        template_name="notification",
        context=context,
        template_dir=NOTIFICATION_TEMPLATE_DIR,
    )


@shared_task(name="send_push_notification_task")
def send_push_notification_task(payload: Dict[str, Any]) -> bool:
    """Send a push notification through the configured communications layer."""
    from src.apps.communications import get_communications_service

    result = get_communications_service().send_push(payload)
    return result.success


@shared_task(name="send_sms_notification_task")
def send_sms_notification_task(to_number: str, body: str) -> bool:
    """Send an SMS notification through the configured communications layer."""
    from src.apps.communications import get_communications_service

    result = get_communications_service().send_sms(to_number=to_number, body=body)
    return result.success
