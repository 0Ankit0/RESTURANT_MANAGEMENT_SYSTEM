from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import time
from typing import Any

import httpx

from src.apps.core.config import settings

_RETRYABLE_STATUS_CODES = {502, 503, 504}


def default_timeout(timeout: float | None = None) -> float:
    return float(timeout if timeout is not None else settings.HTTP_TIMEOUT_SECONDS)


def retry_attempts(retries: int | None = None) -> int:
    configured = settings.HTTP_RETRY_COUNT if retries is None else retries
    return max(0, int(configured))


async def retry_async(
    operation: Callable[[], Awaitable[httpx.Response]],
    *,
    retries: int | None = None,
    backoff_seconds: float | None = None,
    retryable_status_codes: set[int] | None = None,
) -> httpx.Response:
    attempts = retry_attempts(retries) + 1
    delay = float(
        settings.HTTP_BACKOFF_SECONDS if backoff_seconds is None else backoff_seconds
    )
    retryable_codes = retryable_status_codes or _RETRYABLE_STATUS_CODES
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = await operation()
            if response.status_code not in retryable_codes or attempt == attempts - 1:
                return response
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise

        if delay > 0 and attempt < attempts - 1:
            await asyncio.sleep(delay * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP operation failed without a response")


def retry_sync(
    operation: Callable[[], httpx.Response],
    *,
    retries: int | None = None,
    backoff_seconds: float | None = None,
    retryable_status_codes: set[int] | None = None,
) -> httpx.Response:
    attempts = retry_attempts(retries) + 1
    delay = float(
        settings.HTTP_BACKOFF_SECONDS if backoff_seconds is None else backoff_seconds
    )
    retryable_codes = retryable_status_codes or _RETRYABLE_STATUS_CODES
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = operation()
            if response.status_code not in retryable_codes or attempt == attempts - 1:
                return response
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise

        if delay > 0 and attempt < attempts - 1:
            time.sleep(delay * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP operation failed without a response")


def request_kwargs(
    *,
    timeout: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {"timeout": default_timeout(timeout)}
    if extra:
        payload.update(extra)
    return payload
