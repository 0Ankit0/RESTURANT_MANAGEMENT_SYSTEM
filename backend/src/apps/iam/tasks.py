"""IAM-specific Celery email tasks (welcome, password reset, verification, new-IP)."""
from typing import Any, Dict

from celery import shared_task

from src.apps.core.celery_app import celery_app  # noqa: F401 — bind tasks to configured app


@shared_task(name="send_welcome_email_task")
def send_welcome_email_task(user_data: Dict[str, Any]) -> bool:
    """Send a welcome email after successful registration."""
    from src.apps.core.tasks import send_email_task

    recipients = [{"name": user_data.get("username", ""), "email": user_data["email"]}]
    context = {
        "user": {"email": user_data["email"], "first_name": user_data.get("first_name", "")},
    }
    return send_email_task("Welcome to Our Service!", recipients, "welcome", context)


@shared_task(name="send_password_reset_email_task")
def send_password_reset_email_task(user_data: Dict[str, Any], reset_url: str) -> bool:
    """Send a password-reset email."""
    from src.apps.core.tasks import send_email_task

    recipients = [{"name": user_data.get("username", ""), "email": user_data["email"]}]
    context = {
        "user": {"email": user_data["email"], "first_name": user_data.get("first_name", "")},
        "reset_url": reset_url,
    }
    return send_email_task("Reset Your Password", recipients, "password_reset", context)


@shared_task(name="send_verification_email_task")
def send_verification_email_task(user_data: Dict[str, Any], verification_url: str) -> bool:
    """Send an email-address verification email."""
    from src.apps.core.tasks import send_email_task

    recipients = [{"name": user_data.get("username", ""), "email": user_data["email"]}]
    context = {
        "user": {"email": user_data["email"], "first_name": user_data.get("first_name", "")},
        "verification_url": verification_url,
    }
    return send_email_task("Verify Your Email Address", recipients, "email_verification", context)
