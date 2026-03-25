"""PostHog analytics adapter.

Adapts the `posthog` Python SDK to the *AnalyticsProvider* strategy interface.
The SDK uses a background thread to batch and send events, so `capture`,
`identify`, etc. return almost instantly.  Only feature-flag lookups require
a real HTTP round-trip — those are wrapped in `asyncio.to_thread` to avoid
blocking the event loop.

To add a new provider (e.g. Mixpanel):
    1. Create ``adapters/mixpanel_adapter.py`` implementing AnalyticsProvider.
    2. Register it in ``factory.py``.
"""
import asyncio
import logging
from typing import Any

import posthog as _posthog_sdk

from src.apps.analytics.interface import AnalyticsProvider

logger = logging.getLogger(__name__)


class PostHogAdapter(AnalyticsProvider):
    """Adapter: wraps the PostHog Python SDK as an *AnalyticsProvider*."""

    def __init__(self, api_key: str, host: str) -> None:
        # The posthog module exposes a module-level client by default.
        # We configure it once here; all subsequent calls use the same client.
        _posthog_sdk.api_key = api_key
        _posthog_sdk.host = host
        # Suppress PostHog's noisy internal logs unless we're debugging
        _posthog_sdk.disabled = False
        _posthog_sdk.log = logging.getLogger("posthog")
        self._client = _posthog_sdk
        logger.info("PostHog analytics adapter initialised (host=%s)", host)

    # ------------------------------------------------------------------
    # Sending operations (fire-and-forget via SDK's background thread)
    # ------------------------------------------------------------------

    async def capture(
        self,
        distinct_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        self._client.capture(distinct_id, event, properties or {})

    async def identify(
        self,
        distinct_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        self._client.identify(distinct_id, properties or {})

    async def alias(self, distinct_id: str, alias: str) -> None:
        self._client.alias(distinct_id, alias)

    async def group(
        self,
        distinct_id: str,
        group_type: str,
        group_key: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        self._client.group_identify(group_type, group_key, properties or {})
        # Also associate the user with the group on their next event
        self._client.capture(
            distinct_id,
            "$groupidentify",
            {
                "$group_type": group_type,
                "$group_key": group_key,
                "$group_set": properties or {},
            },
        )

    async def page(
        self,
        distinct_id: str,
        path: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        props = {"$current_url": path, **(properties or {})}
        self._client.capture(distinct_id, "$pageview", props)

    # ------------------------------------------------------------------
    # Retrieving operations (real HTTP — run in thread to stay async)
    # ------------------------------------------------------------------

    async def get_feature_flag(
        self,
        distinct_id: str,
        flag_key: str,
        default: bool = False,
    ) -> bool | str:
        try:
            result = await asyncio.to_thread(
                self._client.feature_enabled, flag_key, distinct_id
            )
            return result if result is not None else default
        except Exception as exc:
            logger.warning("PostHog get_feature_flag error: %s", exc)
            return default

    async def get_all_feature_flags(
        self,
        distinct_id: str,
    ) -> dict[str, bool | str]:
        try:
            result = await asyncio.to_thread(
                self._client.get_all_flags, distinct_id
            )
            return result or {}
        except Exception as exc:
            logger.warning("PostHog get_all_feature_flags error: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def flush(self) -> None:
        await asyncio.to_thread(self._client.flush)

    async def shutdown(self) -> None:
        await asyncio.to_thread(self._client.shutdown)
        logger.info("PostHog analytics adapter shut down")
