from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EmailProvider(str, Enum):
    SMTP = "smtp"
    RESEND = "resend"
    SES = "ses"


class PushProvider(str, Enum):
    WEBPUSH = "webpush"
    FCM = "fcm"
    ONESIGNAL = "onesignal"


class SmsProvider(str, Enum):
    TWILIO = "twilio"
    VONAGE = "vonage"


class DeliveryResult(BaseModel):
    channel: str
    provider: str
    success: bool
    message_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    channel: str
    provider: str
    active: bool = False
    enabled: bool = False
    configured: bool = False
    fallback: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class CapabilitySummary(BaseModel):
    modules: dict[str, bool]
    active_providers: dict[str, str | None]
    fallback_providers: dict[str, list[str]]
