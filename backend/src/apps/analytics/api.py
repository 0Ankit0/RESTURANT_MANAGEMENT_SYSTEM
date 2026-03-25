"""Analytics API endpoints.

Provides server-side feature-flag resolution so clients don't need to
embed PostHog API keys.  All endpoints require authentication.
"""
from typing import Any
from fastapi import APIRouter, Depends

from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.iam.api.deps import get_current_user
from src.apps.iam.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/feature-flags/",
    summary="Get all feature flags for the current user",
    description="Returns all PostHog (or configured provider) feature flags evaluated for the authenticated user.",
)
async def get_feature_flags(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics),
) -> dict[str, Any]:
    flags = await analytics.get_all_feature_flags(str(current_user.id))
    return {"flags": flags, "analytics_enabled": analytics.enabled}


@router.get(
    "/feature-flags/{flag_key}/",
    summary="Get a single feature flag for the current user",
)
async def get_feature_flag(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics),
) -> dict[str, Any]:
    value = await analytics.get_feature_flag(str(current_user.id), flag_key)
    return {"flag_key": flag_key, "value": value, "analytics_enabled": analytics.enabled}
