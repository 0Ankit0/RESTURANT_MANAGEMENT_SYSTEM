from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.apps.iam.models.user import User


class NotificationDeviceProvider(str, Enum):
    WEBPUSH = "webpush"
    FCM = "fcm"
    ONESIGNAL = "onesignal"


class NotificationDevicePlatform(str, Enum):
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"


class NotificationDevice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    provider: NotificationDeviceProvider = Field(index=True)
    platform: NotificationDevicePlatform = Field(index=True)
    token: Optional[str] = Field(default=None, max_length=2048)
    endpoint: Optional[str] = Field(default=None, max_length=2048)
    p256dh: Optional[str] = Field(default=None, max_length=512)
    auth: Optional[str] = Field(default=None, max_length=256)
    subscription_id: Optional[str] = Field(default=None, max_length=255, index=True)
    device_metadata: Optional[Any] = Field(default=None, sa_type=JSON)
    is_active: bool = Field(default=True, index=True)
    last_seen_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    user: Optional["User"] = Relationship(back_populates="notification_devices")
