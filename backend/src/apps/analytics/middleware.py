"""Analytics request-tracking middleware.

Captures an ``api_request`` event for every HTTP request, tagged with
method, path, status code, and duration.  Skips health/docs/media paths
to avoid noise.

When analytics are disabled the middleware is still registered but all
captures are no-ops (AnalyticsService.capture is a no-op when disabled).
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.apps.analytics.events import ApiEvents

# Paths that are not worth tracking
_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi", "/media", "/favicon")


class AnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        path = request.url.path
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return response

        # Resolve analytics service from app state (always present after startup)
        analytics = getattr(request.app.state, "analytics", None)
        if analytics is None or not analytics.enabled:
            return response

        # Use authenticated user ID if available; else anonymous
        user_id: str | None = None
        try:
            user_id = str(request.state.user_id)
        except AttributeError:
            pass
        distinct_id = user_id or f"anon:{request.client.host if request.client else 'unknown'}"

        await analytics.capture(
            distinct_id,
            ApiEvents.REQUEST,
            {
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "is_error": response.status_code >= 400,
            },
        )

        return response
