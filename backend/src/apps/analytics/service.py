"""AnalyticsService — the public API consumed by the rest of the application.

This class is the *Context* in the Strategy pattern: it holds a reference to
an *AnalyticsProvider* and delegates every call to it.  When analytics are
disabled (provider is None) all methods silently no-op, so call sites never
need to guard against ``None``.
"""
import logging
from typing import Any

from src.apps.analytics.interface import AnalyticsProvider

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    High-level analytics service used throughout the application.

    Instantiate via :func:`src.apps.analytics.factory.build_analytics_service`
    or the module-level helpers in :mod:`src.apps.analytics`.
    """

    def __init__(self, provider: AnalyticsProvider | None) -> None:
        self._provider = provider
        if provider is None:
            logger.debug("Analytics disabled — all calls are no-ops.")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """True when a provider is configured and analytics are active."""
        return self._provider is not None

    # ------------------------------------------------------------------
    # Sending operations
    # ------------------------------------------------------------------

    async def capture(
        self,
        distinct_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Record a named event for *distinct_id* (a user ID or anonymous ID)."""
        if self._provider:
            try:
                await self._provider.capture(distinct_id, event, properties)
            except Exception as exc:
                logger.warning("Analytics capture error: %s", exc)

    async def identify(
        self,
        distinct_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Attach persistent traits to a person record."""
        if self._provider:
            try:
                await self._provider.identify(distinct_id, properties)
            except Exception as exc:
                logger.warning("Analytics identify error: %s", exc)

    async def alias(self, distinct_id: str, alias: str) -> None:
        """Merge *alias* into the person identified by *distinct_id*."""
        if self._provider:
            try:
                await self._provider.alias(distinct_id, alias)
            except Exception as exc:
                logger.warning("Analytics alias error: %s", exc)

    async def group(
        self,
        distinct_id: str,
        group_type: str,
        group_key: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Associate *distinct_id* with a group (e.g. organisation / tenant)."""
        if self._provider:
            try:
                await self._provider.group(distinct_id, group_type, group_key, properties)
            except Exception as exc:
                logger.warning("Analytics group error: %s", exc)

    async def page(
        self,
        distinct_id: str,
        path: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Record a page / screen view."""
        if self._provider:
            try:
                await self._provider.page(distinct_id, path, properties)
            except Exception as exc:
                logger.warning("Analytics page error: %s", exc)

    # ------------------------------------------------------------------
    # Retrieving operations
    # ------------------------------------------------------------------

    async def get_feature_flag(
        self,
        distinct_id: str,
        flag_key: str,
        default: bool = False,
    ) -> bool | str:
        """Return the feature-flag value for *distinct_id*, or *default*."""
        if self._provider:
            try:
                return await self._provider.get_feature_flag(distinct_id, flag_key, default)
            except Exception as exc:
                logger.warning("Analytics get_feature_flag error: %s", exc)
        return default

    async def get_all_feature_flags(
        self,
        distinct_id: str,
    ) -> dict[str, bool | str]:
        """Return all feature flags for *distinct_id*."""
        if self._provider:
            try:
                return await self._provider.get_all_feature_flags(distinct_id)
            except Exception as exc:
                logger.warning("Analytics get_all_feature_flags error: %s", exc)
        return {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def flush(self) -> None:
        """Force-flush any pending events to the provider."""
        if self._provider:
            try:
                await self._provider.flush()
            except Exception as exc:
                logger.warning("Analytics flush error: %s", exc)

    async def shutdown(self) -> None:
        """Flush and shut down the provider (call on application shutdown)."""
        if self._provider:
            try:
                await self._provider.shutdown()
            except Exception as exc:
                logger.warning("Analytics shutdown error: %s", exc)
