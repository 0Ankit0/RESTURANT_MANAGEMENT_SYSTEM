import pytest

from src.apps.communications.service import CommunicationsService
from src.apps.communications.types import DeliveryResult
from src.apps.core.config import settings


class _StubProvider:
    def __init__(self, name: str, *, configured: bool = True, success: bool = True) -> None:
        self.name = name
        self._configured = configured
        self._success = success
        self.calls = 0

    def is_configured(self) -> bool:
        return self._configured

    def send(self, **_: object) -> DeliveryResult:
        self.calls += 1
        return DeliveryResult(
            channel="email",
            provider=self.name,
            success=self._success,
            error=None if self._success else f"{self.name} failed",
        )


@pytest.mark.unit
def test_send_email_falls_back_to_next_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    service = CommunicationsService()
    primary = _StubProvider("smtp", success=False)
    fallback = _StubProvider("resend", success=True)
    service._email_providers = {"smtp": primary, "resend": fallback}  # type: ignore[attr-defined]

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "EMAIL_FALLBACK_PROVIDERS", ["resend"])

    result = service.send_email(
        subject="Template test",
        recipients=[{"email": "demo@example.com"}],
        template_name="ignored",
        context={"html_body": "<p>Hello</p>"},
        template_dir=".",
        inline_template=True,
    )

    assert primary.calls == 1
    assert fallback.calls == 1
    assert result.success is True
    assert result.provider == "resend"


@pytest.mark.unit
def test_provider_statuses_include_analytics() -> None:
    service = CommunicationsService()
    channels = {status.channel for status in service.get_provider_statuses()}
    assert {"email", "push", "sms", "analytics", "maps"}.issubset(channels)


@pytest.mark.unit
def test_map_public_config_respects_feature_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    service = CommunicationsService()

    monkeypatch.setattr(settings, "FEATURE_MAPS", True)
    monkeypatch.setattr(settings, "MAP_PROVIDER", "google")
    monkeypatch.setattr(settings, "OSM_MAPS_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_MAPS_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_MAPS_API_KEY", "demo-key")
    monkeypatch.setattr(settings, "GOOGLE_MAPS_MAP_ID", "demo-map")
    monkeypatch.setattr(settings, "MAP_DEFAULT_LATITUDE", 27.7)
    monkeypatch.setattr(settings, "MAP_DEFAULT_LONGITUDE", 85.3)
    monkeypatch.setattr(settings, "MAP_DEFAULT_ZOOM", 12)

    config = service.get_map_public_config()

    assert config["enabled"] is True
    assert config["provider"] == "google"
    assert config["providers"]["osm"]["enabled"] is True
    assert config["providers"]["google"]["enabled"] is True
    assert config["providers"]["google"]["api_key"] == "demo-key"
    assert config["default_center"]["latitude"] == 27.7


@pytest.mark.unit
def test_map_public_config_falls_back_when_google_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    service = CommunicationsService()

    monkeypatch.setattr(settings, "FEATURE_MAPS", True)
    monkeypatch.setattr(settings, "MAP_PROVIDER", "google")
    monkeypatch.setattr(settings, "OSM_MAPS_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_MAPS_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_MAPS_API_KEY", "")

    config = service.get_map_public_config()

    assert config["provider"] == "osm"
    assert config["providers"]["google"]["enabled"] is False
