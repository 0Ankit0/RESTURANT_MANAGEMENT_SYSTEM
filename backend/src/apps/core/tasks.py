import logging
from pathlib import Path
from typing import Any, Dict, List

from celery import shared_task

from src.apps.communications import get_communications_service
from src.apps.core.celery_app import celery_app  # noqa: F401
from src.apps.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "apps" / "iam" / "templates"


@shared_task(name="send_email_task")
def send_email_task(
    subject: str,
    recipients: List[Dict[str, str]],
    template_name: str,
    context: Dict[str, Any],
    template_dir: str | None = None,
    inline_template: bool = False,
) -> bool:
    resolved_dir = str(Path(template_dir) if template_dir else TEMPLATE_DIR)

    if not settings.EMAIL_ENABLED and settings.DEBUG:
        sep = "=" * 60
        lines = [
            "",
            sep,
            "  DEV EMAIL (not sent)",
            sep,
            f"  To      : {', '.join(r['email'] for r in recipients)}",
            f"  Subject : {subject}",
            f"  Template: {template_name}",
            sep,
            "",
        ]
        print("\n".join(lines), flush=True)
        return True

    try:
        result = get_communications_service().send_email(
            subject=subject,
            recipients=recipients,
            template_name=template_name,
            context=context,
            template_dir=resolved_dir,
            inline_template=inline_template,
        )
        if not result.success:
            logger.error("Failed to send email via %s: %s", result.provider, result.error)
        return result.success
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
