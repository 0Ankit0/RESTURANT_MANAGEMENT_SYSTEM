"""Notification Pydantic schemas."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_serializer, field_validator

from src.apps.iam.utils.hashid import decode_id, encode_id
from src.apps.notification.models.notification import NotificationType


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str
    type: NotificationType = NotificationType.INFO
    extra_data: Optional[Any] = None

    @field_validator("user_id", mode="before")
    @classmethod
    def decode_user_id(cls, value: int | str) -> int:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid user_id")
            return decoded
        return value


class NotificationRead(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    type: NotificationType
    is_read: bool
    extra_data: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationList(BaseModel):
    items: list[NotificationRead]
    total: int
    unread_count: int
