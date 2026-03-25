from src.apps.core.config import Settings, settings
from src.apps.core.storage import extract_relative_media_path


def test_build_media_url_uses_configured_media_base_url() -> None:
    parsed = Settings(
        MEDIA_BASE_URL="https://cdn.example.com/media",
        STORAGE_BACKEND="local",
    )
    assert parsed.media_base_url == "https://cdn.example.com/media"


def test_extract_relative_media_path_handles_absolute_media_url() -> None:
    original_server_host = settings.SERVER_HOST
    original_media_url = settings.MEDIA_URL
    original_media_base_url = settings.MEDIA_BASE_URL
    try:
        settings.SERVER_HOST = "https://api.example.com"
        settings.MEDIA_URL = "/media"
        settings.MEDIA_BASE_URL = ""
        relative = extract_relative_media_path("https://api.example.com/media/avatars/example.png")
        assert relative == "avatars/example.png"
    finally:
        settings.SERVER_HOST = original_server_host
        settings.MEDIA_URL = original_media_url
        settings.MEDIA_BASE_URL = original_media_base_url
