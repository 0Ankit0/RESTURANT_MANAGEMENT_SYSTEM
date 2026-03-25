"""Analytics factory — builds the correct provider adapter from config.

Adding a new provider
---------------------
1. Create ``adapters/<name>_adapter.py`` implementing *AnalyticsProvider*.
2. Add an entry to ``_REGISTRY`` below.
3. Set ``ANALYTICS_PROVIDER=<name>`` in your ``.env``.
"""
import logging

from src.apps.core.config import settings
from src.apps.analytics.interface import AnalyticsProvider
from src.apps.analytics.service import AnalyticsService

logger = logging.getLogger(__name__)


def _build_provider() -> AnalyticsProvider | None:
    """Instantiate and return the configured analytics provider, or None."""
    if not settings.ANALYTICS_ENABLED:
        return None

    provider_name = settings.ANALYTICS_PROVIDER.lower()

    if provider_name == "posthog":
        if not settings.POSTHOG_API_KEY:
            logger.warning(
                "ANALYTICS_ENABLED=true but POSTHOG_API_KEY is empty — "
                "analytics disabled."
            )
            return None
        from src.apps.analytics.adapters.posthog_adapter import PostHogAdapter
        return PostHogAdapter(
            api_key=settings.POSTHOG_API_KEY,
            host=settings.POSTHOG_HOST,
        )

    if provider_name == "mixpanel":
        if not settings.MIXPANEL_PROJECT_TOKEN:
            logger.warning(
                "ANALYTICS_ENABLED=true but MIXPANEL_PROJECT_TOKEN is empty — "
                "analytics disabled."
            )
            return None
        from src.apps.analytics.adapters.mixpanel_adapter import MixpanelAdapter

        return MixpanelAdapter(
            project_token=settings.MIXPANEL_PROJECT_TOKEN,
            host=settings.MIXPANEL_API_HOST,
        )

    logger.warning(
        "Unknown ANALYTICS_PROVIDER=%r — analytics disabled.", provider_name
    )
    return None


def build_analytics_service() -> AnalyticsService:
    """Return an AnalyticsService wired to the configured provider."""
    provider = _build_provider()
    return AnalyticsService(provider)
