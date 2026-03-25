from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_serializer, model_validator

from src.apps.iam.utils.hashid import encode_id
from src.apps.notification.models.notification_device import (
    NotificationDevicePlatform,
    NotificationDeviceProvider,
)


class NotificationDeviceRead(BaseModel):
    id: int
    user_id: int
    provider: NotificationDeviceProvider
    platform: NotificationDevicePlatform
    token: Optional[str] = None
    endpoint: Optional[str] = None
    subscription_id: Optional[str] = None
    is_active: bool
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    device_metadata: Optional[Any] = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class NotificationDeviceCreate(BaseModel):
    provider: NotificationDeviceProvider
    platform: NotificationDevicePlatform
    token: Optional[str] = None
    endpoint: Optional[str] = None
    p256dh: Optional[str] = None
    auth: Optional[str] = None
    subscription_id: Optional[str] = None
    device_metadata: Optional[Any] = None

    @model_validator(mode="after")
    def validate_payload(self) -> "NotificationDeviceCreate":
        if self.provider == NotificationDeviceProvider.WEBPUSH:
            if not all([self.endpoint, self.p256dh, self.auth]):
                raise ValueError("webpush requires endpoint, p256dh, and auth")
        elif self.provider == NotificationDeviceProvider.FCM:
            if not self.token:
                raise ValueError("fcm requires token")
        elif self.provider == NotificationDeviceProvider.ONESIGNAL:
            if not self.subscription_id:
                raise ValueError("onesignal requires subscription_id")
        return self


class WebPushDeviceCreate(BaseModel):
    platform: NotificationDevicePlatform = NotificationDevicePlatform.WEB
    endpoint: str
    p256dh: str
    auth: str
    device_metadata: Optional[Any] = None

    def to_device_create(self) -> NotificationDeviceCreate:
        return NotificationDeviceCreate(
            provider=NotificationDeviceProvider.WEBPUSH,
            platform=self.platform,
            endpoint=self.endpoint,
            p256dh=self.p256dh,
            auth=self.auth,
            device_metadata=self.device_metadata,
        )


class FcmDeviceCreate(BaseModel):
    platform: NotificationDevicePlatform
    token: str
    device_metadata: Optional[Any] = None

    def to_device_create(self) -> NotificationDeviceCreate:
        return NotificationDeviceCreate(
            provider=NotificationDeviceProvider.FCM,
            platform=self.platform,
            token=self.token,
            device_metadata=self.device_metadata,
        )


class OneSignalDeviceCreate(BaseModel):
    platform: NotificationDevicePlatform
    subscription_id: str
    device_metadata: Optional[Any] = None

    def to_device_create(self) -> NotificationDeviceCreate:
        return NotificationDeviceCreate(
            provider=NotificationDeviceProvider.ONESIGNAL,
            platform=self.platform,
            subscription_id=self.subscription_id,
            device_metadata=self.device_metadata,
        )
