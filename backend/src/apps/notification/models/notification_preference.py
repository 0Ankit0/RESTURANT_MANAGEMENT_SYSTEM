"""User notification channel preference model."""
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.apps.iam.models.user import User


class NotificationPreference(SQLModel, table=True):
    """
    Stores per-user notification channel preferences.

    A row is auto-created (with all defaults) the first time a user's
    preferences are read or updated.  The *_enabled flags gate whether a
    given channel is used when a notification is dispatched.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)

    # ── Channel flags ──────────────────────────────────────────────────────
    websocket_enabled: bool = Field(
        default=True,
        description="Deliver notifications via WebSocket (real-time, always-on by default)",
    )
    email_enabled: bool = Field(
        default=False,
        description="Send notifications via email",
    )
    push_enabled: bool = Field(
        default=False,
        description="Send browser / mobile push notifications (requires push subscription)",
    )
    sms_enabled: bool = Field(
        default=False,
        description="Send SMS / text-message notifications (requires verified phone number)",
    )

    # ── Web-Push subscription data (populated by the browser after opt-in) ─
    push_endpoint: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Push service endpoint URL provided by the browser",
    )
    push_p256dh: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Browser public key (base64url) for payload encryption",
    )
    push_auth: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Auth secret (base64url) for payload encryption",
    )

    # Relationship
    user: Optional["User"] = Relationship(back_populates="notification_preference")
