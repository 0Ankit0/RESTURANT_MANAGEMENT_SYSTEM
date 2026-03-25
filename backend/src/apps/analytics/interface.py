"""Analytics Strategy interface.

Every analytics provider (PostHog, Mixpanel, Amplitude, custom …) must
implement *AnalyticsProvider*.  The *AnalyticsService* depends only on this
abstract contract — swapping providers requires only a new adapter class.

Pattern notes
-------------
* **Strategy**: AnalyticsProvider defines the algorithm family (how analytics
  operations work). AnalyticsService uses a provider instance polymorphically.
* **Adapter**: Each concrete provider class (e.g. PostHogAdapter) adapts the
  third-party SDK's API to this interface, keeping the rest of the codebase
  decoupled from SDK specifics.
"""
from abc import ABC, abstractmethod
from typing import Any


class AnalyticsProvider(ABC):
    """Abstract analytics strategy — all providers must implement this."""

    # ------------------------------------------------------------------
    # Sending (write) operations
    # ------------------------------------------------------------------

    @abstractmethod
    async def capture(
        self,
        distinct_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Record a single event for *distinct_id*."""

    @abstractmethod
    async def identify(
        self,
        distinct_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Set or update persistent properties on a person."""

    @abstractmethod
    async def alias(self, distinct_id: str, alias: str) -> None:
        """Merge *alias* into the person record for *distinct_id*."""

    @abstractmethod
    async def group(
        self,
        distinct_id: str,
        group_type: str,
        group_key: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Associate *distinct_id* with a group (e.g. organisation/tenant)."""

    @abstractmethod
    async def page(
        self,
        distinct_id: str,
        path: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Record a page / screen view."""

    # ------------------------------------------------------------------
    # Retrieving (read) operations
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_feature_flag(
        self,
        distinct_id: str,
        flag_key: str,
        default: bool = False,
    ) -> bool | str:
        """Return the value of a feature flag for *distinct_id*."""

    @abstractmethod
    async def get_all_feature_flags(
        self,
        distinct_id: str,
    ) -> dict[str, bool | str]:
        """Return all feature flags and their values for *distinct_id*."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def flush(self) -> None:
        """Force-send any buffered events immediately."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Flush and cleanly shut down the provider (call on app shutdown)."""
