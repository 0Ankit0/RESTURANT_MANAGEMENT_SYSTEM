"""FastAPI dependency for analytics service injection."""
from fastapi import Request
from src.apps.analytics.service import AnalyticsService


def get_analytics(request: Request) -> AnalyticsService:
    """FastAPI dependency — injects the analytics service from app state."""
    return request.app.state.analytics
