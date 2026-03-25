
import logging
from pathlib import Path
from src.apps.core.config import settings
from fastapi_mail import NameEmail
from typing import Any,Dict,List
from jinja2 import Environment,FileSystemLoader

logger = logging.getLogger(__name__)

# Basic Template setup
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

class EmailService:
    @staticmethod
    async def send_email(
        subject: str,
        recipients: List[NameEmail],
        template_name: str,
        context: Dict[str, Any],
    ) -> None:
        """send an email using a template.
        NOTE: This requires SMTP settings in env (e.g. SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
        for now, we'll log if the settings are missing.
        """
        # Use Celery for background task processing
        from src.apps.core.tasks import send_email_task
        
        # Convert NameEmail objects to dict for serialization
        recipients_dict = [{"name": r.name, "email": r.email} for r in recipients]
        
        # Queue email task in background
        send_email_task.delay(subject, recipients_dict, template_name, context)
        logger.info(f"Email task queued: Subject: {subject}, Recipients: {recipients_dict}")

    @staticmethod
    async def send_welcome_email(user) -> None:
        from src.apps.iam.tasks import send_welcome_email_task
        user_data = {
            "username": user.username,
            "email": user.email,
            "first_name": getattr(user, 'first_name', '')
        }
        send_welcome_email_task.delay(user_data)
        logger.info(f"Welcome email task queued for user: {user.email}")

    @staticmethod
    async def send_password_reset_email(user, token:str) -> None:
        # Create secure URL token with embedded user_id
        from src.apps.core import security
        from src.apps.iam.tasks import send_password_reset_email_task
        
        secure_token = security.create_secure_url_token({
            "user_id": user.id,
            "token": token,
            "purpose": "password_reset"
        }, expires_hours=1)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?t={secure_token}"
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "first_name": getattr(user, 'first_name', '')
        }
        send_password_reset_email_task.delay(user_data, reset_url)
        logger.info(f"Password reset email task queued for user: {user.email}")

    @staticmethod
    async def send_verification_email(user, token: str) -> None:
        # Create secure URL token with embedded user_id
        from src.apps.core import security
        from src.apps.iam.tasks import send_verification_email_task
        
        secure_token = security.create_secure_url_token({
            "user_id": user.id,
            "token": token,
            "purpose": "email_verification"
        }, expires_hours=24)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?t={secure_token}"
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "first_name": getattr(user, 'first_name', '')
        }
        send_verification_email_task.delay(user_data, verification_url)
        logger.info(f"Verification email task queued for user: {user.email}")