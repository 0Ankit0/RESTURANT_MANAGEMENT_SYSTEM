from __future__ import annotations

from pathlib import Path
from typing import Final
from urllib.parse import urlparse

from src.apps.core.config import settings

_LOCAL_STORAGE_BACKEND: Final[str] = "local"
_S3_STORAGE_BACKEND: Final[str] = "s3"


def _normalize_relative_path(path: str) -> str:
    return path.lstrip("/").replace("\\", "/")


def build_media_url(relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    return f"{settings.media_base_url.rstrip('/')}/{normalized}"


def extract_relative_media_path(value: str) -> str:
    if not value:
        return ""

    normalized = value.strip()
    media_base = settings.media_base_url.rstrip("/")
    if media_base and normalized.startswith(f"{media_base}/"):
        return _normalize_relative_path(normalized[len(media_base) + 1 :])

    local_media_base = f"{settings.SERVER_HOST.rstrip('/')}{settings.MEDIA_URL.rstrip('/')}"
    if normalized.startswith(f"{local_media_base}/"):
        return _normalize_relative_path(normalized[len(local_media_base) + 1 :])

    if normalized.startswith(f"{settings.MEDIA_URL.rstrip('/')}/"):
        return _normalize_relative_path(
            normalized[len(settings.MEDIA_URL.rstrip("/")) + 1 :]
        )

    parsed = urlparse(normalized)
    if parsed.scheme and parsed.path:
        return _normalize_relative_path(parsed.path.split("/", 2)[-1])

    return _normalize_relative_path(normalized)


def _s3_client():
    import boto3
    from botocore.config import Config

    client_kwargs: dict[str, object] = {
        "service_name": "s3",
        "region_name": settings.S3_REGION,
        "config": Config(
            s3={"addressing_style": "path" if settings.S3_USE_PATH_STYLE else "virtual"}
        ),
    }
    if settings.S3_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    if settings.AWS_ACCESS_KEY_ID:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    secret = settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
    if secret:
        client_kwargs["aws_secret_access_key"] = secret
    return boto3.client(**client_kwargs)


def save_media_bytes(
    relative_path: str,
    content: bytes,
    *,
    content_type: str | None = None,
) -> str:
    normalized = _normalize_relative_path(relative_path)
    if settings.STORAGE_BACKEND == _S3_STORAGE_BACKEND:
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET must be configured when STORAGE_BACKEND=s3")
        put_kwargs = {
            "Bucket": settings.S3_BUCKET,
            "Key": normalized,
            "Body": content,
        }
        if content_type:
            put_kwargs["ContentType"] = content_type
        _s3_client().put_object(**put_kwargs)
        return build_media_url(normalized)

    target = Path(settings.MEDIA_DIR) / normalized
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return build_media_url(normalized)


def delete_media(relative_path_or_url: str) -> None:
    relative_path = extract_relative_media_path(relative_path_or_url)
    if not relative_path:
        return

    if settings.STORAGE_BACKEND == _S3_STORAGE_BACKEND:
        if not settings.S3_BUCKET:
            return
        _s3_client().delete_object(Bucket=settings.S3_BUCKET, Key=relative_path)
        return

    target = Path(settings.MEDIA_DIR) / relative_path
    if target.is_file():
        target.unlink()


def storage_uses_local_filesystem() -> bool:
    return settings.STORAGE_BACKEND == _LOCAL_STORAGE_BACKEND
