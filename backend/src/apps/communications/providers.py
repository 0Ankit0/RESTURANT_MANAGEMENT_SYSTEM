import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType, NameEmail
from jinja2 import Environment, FileSystemLoader

from src.apps.core.config import settings
from src.apps.core.http import default_timeout, retry_sync

from .interfaces import EmailProviderBase, PushProviderBase, SmsProviderBase
from .types import DeliveryResult, EmailProvider, PushProvider, SmsProvider

logger = logging.getLogger(__name__)


def render_template(template_dir: str, template_name: str, context: dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(f"emails/{template_name}.html")
    return template.render(**context)


class SmtpEmailProvider(EmailProviderBase):
    name = EmailProvider.SMTP.value

    def is_configured(self) -> bool:
        return settings.EMAIL_ENABLED and bool(
            settings.EMAIL_HOST
            and settings.EMAIL_PORT
            and settings.EMAIL_HOST_USER
            and settings.EMAIL_FROM_ADDRESS
        )

    def send(
        self,
        *,
        subject: str,
        recipients: list[dict[str, str]],
        html_body: str,
        text_body: str | None = None,
    ) -> DeliveryResult:
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.EMAIL_HOST_USER,
            MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
            MAIL_FROM=settings.EMAIL_FROM_ADDRESS,
            MAIL_PORT=int(settings.EMAIL_PORT),
            MAIL_SERVER=settings.EMAIL_HOST,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=Path("."),
        )
        recipient_objects = [NameEmail(name=item.get("name", ""), email=item["email"]) for item in recipients]
        message = MessageSchema(
            subject=subject,
            recipients=recipient_objects,
            body=html_body,
            subtype=MessageType.html,
        )
        asyncio.run(FastMail(conf).send_message(message))
        return DeliveryResult(channel="email", provider=self.name, success=True)


class ResendEmailProvider(EmailProviderBase):
    name = EmailProvider.RESEND.value

    def is_configured(self) -> bool:
        return bool(settings.RESEND_API_KEY and settings.RESEND_FROM_ADDRESS)

    def send(
        self,
        *,
        subject: str,
        recipients: list[dict[str, str]],
        html_body: str,
        text_body: str | None = None,
    ) -> DeliveryResult:
        response = retry_sync(
            lambda: httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.RESEND_FROM_ADDRESS,
                    "to": [r["email"] for r in recipients],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body or "",
                },
                timeout=default_timeout(),
            )
        )
        response.raise_for_status()
        return DeliveryResult(
            channel="email",
            provider=self.name,
            success=True,
            message_id=response.json().get("id"),
        )


class SesEmailProvider(EmailProviderBase):
    name = EmailProvider.SES.value

    def is_configured(self) -> bool:
        return bool(
            settings.SES_FROM_ADDRESS
            and settings.AWS_REGION
            and settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
        )

    def send(
        self,
        *,
        subject: str,
        recipients: list[dict[str, str]],
        html_body: str,
        text_body: str | None = None,
    ) -> DeliveryResult:
        import boto3

        client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY.get_secret_value(),
        )
        result = client.send_email(
            Source=settings.SES_FROM_ADDRESS,
            Destination={"ToAddresses": [r["email"] for r in recipients]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Html": {"Data": html_body},
                    "Text": {"Data": text_body or ""},
                },
            },
        )
        return DeliveryResult(
            channel="email",
            provider=self.name,
            success=True,
            message_id=result.get("MessageId"),
        )


class WebPushProvider(PushProviderBase):
    name = PushProvider.WEBPUSH.value

    def is_configured(self) -> bool:
        return settings.PUSH_ENABLED and bool(
            settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY
        )

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        from pywebpush import webpush

        webpush(
            subscription_info={
                "endpoint": payload["endpoint"],
                "keys": {"p256dh": payload["p256dh"], "auth": payload["auth"]},
            },
            data=json.dumps(
                {
                    "title": payload["title"],
                    "body": payload["body"],
                    "data": payload.get("data"),
                }
            ),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
        )
        return DeliveryResult(channel="push", provider=self.name, success=True)


class FcmPushProvider(PushProviderBase):
    name = PushProvider.FCM.value

    def is_configured(self) -> bool:
        return settings.PUSH_ENABLED and bool(
            settings.FCM_SERVER_KEY
            or (
                settings.FCM_PROJECT_ID
                and (
                    settings.FCM_SERVICE_ACCOUNT_JSON
                    or settings.FCM_SERVICE_ACCOUNT_FILE
                )
            )
        )

    def _access_token(self) -> str | None:
        if settings.FCM_SERVICE_ACCOUNT_JSON:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            info = json.loads(settings.FCM_SERVICE_ACCOUNT_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            credentials.refresh(Request())
            return credentials.token

        if settings.FCM_SERVICE_ACCOUNT_FILE:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            credentials = service_account.Credentials.from_service_account_file(
                settings.FCM_SERVICE_ACCOUNT_FILE,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            credentials.refresh(Request())
            return credentials.token

        return None

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        access_token = self._access_token()
        if access_token and settings.FCM_PROJECT_ID:
            response = retry_sync(
                lambda: httpx.post(
                    f"https://fcm.googleapis.com/v1/projects/{settings.FCM_PROJECT_ID}/messages:send",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "message": {
                            "token": payload["token"],
                            "notification": {
                                "title": payload["title"],
                                "body": payload["body"],
                            },
                            "data": payload.get("data") or {},
                        }
                    },
                    timeout=default_timeout(),
                )
            )
        else:
            response = retry_sync(
                lambda: httpx.post(
                    "https://fcm.googleapis.com/fcm/send",
                    headers={
                        "Authorization": f"key={settings.FCM_SERVER_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "to": payload["token"],
                        "notification": {
                            "title": payload["title"],
                            "body": payload["body"],
                        },
                        "data": payload.get("data") or {},
                    },
                    timeout=default_timeout(),
                )
            )
        response.raise_for_status()
        data = response.json()
        return DeliveryResult(
            channel="push",
            provider=self.name,
            success=bool(data.get("name")) or data.get("failure", 0) == 0,
            metadata=data,
        )


class OneSignalPushProvider(PushProviderBase):
    name = PushProvider.ONESIGNAL.value

    def is_configured(self) -> bool:
        return settings.PUSH_ENABLED and bool(
            settings.ONESIGNAL_APP_ID and settings.ONESIGNAL_API_KEY
        )

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        response = retry_sync(
            lambda: httpx.post(
                "https://api.onesignal.com/notifications",
                headers={
                    "Authorization": f"Key {settings.ONESIGNAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "app_id": settings.ONESIGNAL_APP_ID,
                    "include_subscription_ids": [payload["subscription_id"]],
                    "headings": {"en": payload["title"]},
                    "contents": {"en": payload["body"]},
                    "data": payload.get("data") or {},
                },
                timeout=default_timeout(),
            )
        )
        response.raise_for_status()
        data = response.json()
        return DeliveryResult(
            channel="push",
            provider=self.name,
            success=True,
            message_id=data.get("id"),
            metadata=data,
        )


class TwilioSmsProvider(SmsProviderBase):
    name = SmsProvider.TWILIO.value

    def is_configured(self) -> bool:
        return settings.SMS_ENABLED and bool(
            settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_FROM_NUMBER
        )

    def send(self, *, to_number: str, body: str) -> DeliveryResult:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=to_number,
        )
        return DeliveryResult(
            channel="sms",
            provider=self.name,
            success=True,
            message_id=message.sid,
        )


class VonageSmsProvider(SmsProviderBase):
    name = SmsProvider.VONAGE.value

    def is_configured(self) -> bool:
        return settings.SMS_ENABLED and bool(
            settings.VONAGE_API_KEY
            and settings.VONAGE_API_SECRET
            and settings.VONAGE_FROM_NUMBER
        )

    def send(self, *, to_number: str, body: str) -> DeliveryResult:
        response = retry_sync(
            lambda: httpx.post(
                "https://rest.nexmo.com/sms/json",
                data={
                    "api_key": settings.VONAGE_API_KEY,
                    "api_secret": settings.VONAGE_API_SECRET,
                    "from": settings.VONAGE_FROM_NUMBER,
                    "to": to_number,
                    "text": body,
                },
                timeout=default_timeout(),
            )
        )
        response.raise_for_status()
        payload = response.json()
        first = (payload.get("messages") or [{}])[0]
        status = str(first.get("status", "1"))
        return DeliveryResult(
            channel="sms",
            provider=self.name,
            success=status == "0",
            message_id=first.get("message-id"),
            metadata=payload,
            error=None if status == "0" else first.get("error-text"),
        )
