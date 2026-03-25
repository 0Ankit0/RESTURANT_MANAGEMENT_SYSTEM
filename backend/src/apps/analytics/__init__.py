"""Analytics module — Strategy + Adapter pattern.

Usage
-----
    from src.apps.analytics import get_analytics
    analytics = get_analytics()           # singleton, safe when disabled
    await analytics.capture(user_id, "user_signed_up", {"plan": "free"})
"""
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.factory import build_analytics_service

_service: AnalyticsService | None = None


def init_analytics() -> AnalyticsService:
    """Build and cache the analytics service singleton."""
    global _service
    _service = build_analytics_service()
    return _service


def get_analytics() -> AnalyticsService:
    """Return the cached analytics service (initialises lazily if needed)."""
    global _service
    if _service is None:
        _service = build_analytics_service()
    return _service


async def shutdown_analytics() -> None:
    """Flush pending events and shut down the provider cleanly."""
    global _service
    if _service is not None:
        await _service.shutdown()
