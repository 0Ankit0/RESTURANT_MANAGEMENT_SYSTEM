import logging
from typing import Any

from src.apps.core.config import settings

from .interfaces import EmailProviderBase, PushProviderBase, SmsProviderBase
from .providers import (
    FcmPushProvider,
    OneSignalPushProvider,
    ResendEmailProvider,
    SesEmailProvider,
    SmtpEmailProvider,
    TwilioSmsProvider,
    VonageSmsProvider,
    WebPushProvider,
    render_template,
)
from .types import CapabilitySummary, DeliveryResult, ProviderStatus

logger = logging.getLogger(__name__)

_service: "CommunicationsService | None" = None


class CommunicationsService:
    def __init__(self) -> None:
        self._email_providers: dict[str, EmailProviderBase] = {
            "smtp": SmtpEmailProvider(),
            "resend": ResendEmailProvider(),
            "ses": SesEmailProvider(),
        }
        self._push_providers: dict[str, PushProviderBase] = {
            "webpush": WebPushProvider(),
            "fcm": FcmPushProvider(),
            "onesignal": OneSignalPushProvider(),
        }
        self._sms_providers: dict[str, SmsProviderBase] = {
            "twilio": TwilioSmsProvider(),
            "vonage": VonageSmsProvider(),
        }
        self._analytics_providers: dict[str, bool] = {
            "posthog": bool(settings.POSTHOG_API_KEY),
            "mixpanel": bool(settings.MIXPANEL_PROJECT_TOKEN),
        }

    def _provider_chain(self, active: str, fallbacks: list[str], registry: dict[str, Any]) -> list[Any]:
        ordered: list[Any] = []
        for name in [active, *fallbacks]:
            provider = registry.get(name)
            if provider and provider not in ordered:
                ordered.append(provider)
        return ordered

    def get_capabilities(self) -> CapabilitySummary:
        return CapabilitySummary(
            modules={
                "auth": settings.FEATURE_AUTH,
                "multitenancy": settings.FEATURE_MULTITENANCY,
                "notifications": settings.FEATURE_NOTIFICATIONS,
                "websockets": settings.FEATURE_WEBSOCKETS,
                "finance": settings.FEATURE_FINANCE,
                "analytics": settings.FEATURE_ANALYTICS,
                "social_auth": settings.FEATURE_SOCIAL_AUTH,
                "maps": settings.FEATURE_MAPS,
            },
            active_providers={
                "email": settings.EMAIL_PROVIDER if settings.EMAIL_ENABLED else None,
                "push": settings.PUSH_PROVIDER if settings.PUSH_ENABLED else None,
                "sms": settings.SMS_PROVIDER if settings.SMS_ENABLED else None,
                "analytics": settings.ANALYTICS_PROVIDER if settings.ANALYTICS_ENABLED else None,
                "maps": settings.MAP_PROVIDER if settings.FEATURE_MAPS else None,
            },
            fallback_providers={
                "email": settings.EMAIL_FALLBACK_PROVIDERS,
                "push": settings.PUSH_FALLBACK_PROVIDERS,
                "sms": settings.SMS_FALLBACK_PROVIDERS,
                "maps": [],
            },
        )

    def get_provider_statuses(self) -> list[ProviderStatus]:
        statuses: list[ProviderStatus] = []
        for channel, active, fallbacks, registry, enabled in [
            ("email", settings.EMAIL_PROVIDER, settings.EMAIL_FALLBACK_PROVIDERS, self._email_providers, settings.EMAIL_ENABLED),
            ("push", settings.PUSH_PROVIDER, settings.PUSH_FALLBACK_PROVIDERS, self._push_providers, settings.PUSH_ENABLED),
            ("sms", settings.SMS_PROVIDER, settings.SMS_FALLBACK_PROVIDERS, self._sms_providers, settings.SMS_ENABLED),
        ]:
            for name, provider in registry.items():
                statuses.append(
                    ProviderStatus(
                        channel=channel,
                        provider=name,
                        active=enabled and name == active,
                        enabled=enabled,
                        configured=provider.is_configured(),
                        fallback=name in fallbacks,
                    )
                )
        for name, configured in self._analytics_providers.items():
            statuses.append(
                ProviderStatus(
                    channel="analytics",
                    provider=name,
                    active=settings.ANALYTICS_ENABLED and name == settings.ANALYTICS_PROVIDER,
                    enabled=settings.ANALYTICS_ENABLED,
                    configured=configured,
                    fallback=False,
                )
            )
        for name, configured in [
            ("osm", settings.OSM_MAPS_ENABLED),
            ("google", bool(settings.GOOGLE_MAPS_ENABLED and settings.GOOGLE_MAPS_API_KEY)),
        ]:
            statuses.append(
                ProviderStatus(
                    channel="maps",
                    provider=name,
                    active=settings.FEATURE_MAPS and name == settings.MAP_PROVIDER,
                    enabled=settings.FEATURE_MAPS,
                    configured=configured,
                    fallback=False,
                )
            )
        return statuses

    def send_email(
        self,
        *,
        subject: str,
        recipients: list[dict[str, str]],
        template_name: str,
        context: dict[str, Any],
        template_dir: str,
        inline_template: bool = False,
    ) -> DeliveryResult:
        html_body = str(context.get("html_body", "")) if inline_template else render_template(template_dir, template_name, context)
        text_body = context.get("text_body")
        last_result = DeliveryResult(channel="email", provider=settings.EMAIL_PROVIDER, success=False)
        for provider in self._provider_chain(
            settings.EMAIL_PROVIDER,
            settings.EMAIL_FALLBACK_PROVIDERS,
            self._email_providers,
        ):
            if not provider.is_configured():
                continue
            try:
                result = provider.send(
                    subject=subject,
                    recipients=recipients,
                    html_body=html_body,
                    text_body=text_body,
                )
                logger.info("email_delivery provider=%s success=%s", provider.name, result.success)
                if result.success:
                    return result
                last_result = result
            except Exception as exc:
                logger.warning("email_delivery_failed provider=%s error=%s", provider.name, exc)
                last_result = DeliveryResult(
                    channel="email",
                    provider=provider.name,
                    success=False,
                    error=str(exc),
                )
        return last_result

    def send_push(self, payload: dict[str, Any]) -> DeliveryResult:
        target_provider = str(payload.get("provider") or settings.PUSH_PROVIDER)
        last_result = DeliveryResult(channel="push", provider=target_provider, success=False)
        for provider in self._provider_chain(
            target_provider,
            settings.PUSH_FALLBACK_PROVIDERS,
            self._push_providers,
        ):
            if not provider.is_configured():
                continue
            try:
                result = provider.send(payload)
                logger.info("push_delivery provider=%s success=%s", provider.name, result.success)
                if result.success:
                    return result
                last_result = result
            except Exception as exc:
                logger.warning("push_delivery_failed provider=%s error=%s", provider.name, exc)
                last_result = DeliveryResult(
                    channel="push",
                    provider=provider.name,
                    success=False,
                    error=str(exc),
                )
        return last_result

    def send_sms(self, *, to_number: str, body: str) -> DeliveryResult:
        last_result = DeliveryResult(channel="sms", provider=settings.SMS_PROVIDER, success=False)
        for provider in self._provider_chain(
            settings.SMS_PROVIDER,
            settings.SMS_FALLBACK_PROVIDERS,
            self._sms_providers,
        ):
            if not provider.is_configured():
                continue
            try:
                result = provider.send(to_number=to_number, body=body)
                logger.info("sms_delivery provider=%s success=%s", provider.name, result.success)
                if result.success:
                    return result
                last_result = result
            except Exception as exc:
                logger.warning("sms_delivery_failed provider=%s error=%s", provider.name, exc)
                last_result = DeliveryResult(
                    channel="sms",
                    provider=provider.name,
                    success=False,
                    error=str(exc),
                )
        return last_result

    def get_push_public_config(self) -> dict[str, Any]:
        return {
            "provider": settings.PUSH_PROVIDER if settings.PUSH_ENABLED else None,
            "providers": {
                "webpush": {
                    "enabled": settings.PUSH_ENABLED and bool(settings.VAPID_PUBLIC_KEY),
                    "vapid_public_key": settings.VAPID_PUBLIC_KEY,
                },
                "fcm": {
                    "enabled": settings.PUSH_ENABLED and bool(
                        settings.FCM_SERVER_KEY
                        or settings.FCM_SERVICE_ACCOUNT_JSON
                        or settings.FCM_SERVICE_ACCOUNT_FILE
                    ),
                    "project_id": settings.FCM_PROJECT_ID,
                    "web_vapid_key": settings.FCM_WEB_VAPID_KEY,
                    "api_key": settings.FCM_API_KEY,
                    "app_id": settings.FCM_APP_ID,
                    "messaging_sender_id": settings.FCM_MESSAGING_SENDER_ID,
                    "auth_domain": settings.FCM_AUTH_DOMAIN,
                    "storage_bucket": settings.FCM_STORAGE_BUCKET,
                    "measurement_id": settings.FCM_MEASUREMENT_ID,
                },
                "onesignal": {
                    "enabled": settings.PUSH_ENABLED and bool(settings.ONESIGNAL_APP_ID and settings.ONESIGNAL_API_KEY),
                    "app_id": settings.ONESIGNAL_APP_ID,
                    "web_app_id": settings.ONESIGNAL_WEB_APP_ID or settings.ONESIGNAL_APP_ID,
                },
            },
        }

    def is_push_provider_available(self, provider_name: str) -> bool:
        provider = self._push_providers.get(provider_name)
        return bool(settings.PUSH_ENABLED and provider and provider.is_configured())

    def get_available_push_providers(self) -> list[str]:
        return [
            name
            for name, provider in self._push_providers.items()
            if settings.PUSH_ENABLED and provider.is_configured()
        ]

    def get_map_public_config(self) -> dict[str, Any]:
        maps_enabled = settings.FEATURE_MAPS
        google_enabled = bool(
            maps_enabled and settings.GOOGLE_MAPS_ENABLED and settings.GOOGLE_MAPS_API_KEY
        )
        osm_enabled = bool(maps_enabled and settings.OSM_MAPS_ENABLED)

        active_provider = settings.MAP_PROVIDER if maps_enabled else None
        if active_provider == "google" and not google_enabled:
            active_provider = "osm" if osm_enabled else None
        if active_provider == "osm" and not osm_enabled:
            active_provider = "google" if google_enabled else None

        return {
            "enabled": maps_enabled,
            "provider": active_provider,
            "default_center": {
                "latitude": settings.MAP_DEFAULT_LATITUDE,
                "longitude": settings.MAP_DEFAULT_LONGITUDE,
                "zoom": settings.MAP_DEFAULT_ZOOM,
            },
            "providers": {
                "osm": {
                    "enabled": osm_enabled,
                    "label": "OpenStreetMap",
                },
                "google": {
                    "enabled": google_enabled,
                    "label": "Google Maps",
                    "api_key": settings.GOOGLE_MAPS_API_KEY if google_enabled else "",
                    "map_id": settings.GOOGLE_MAPS_MAP_ID,
                },
            },
        }


def get_communications_service() -> CommunicationsService:
    global _service
    if _service is None:
        _service = CommunicationsService()
    return _service
