from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.apps.core.logging import clear_log_context, set_log_context
from src.apps.observability.service import (
    build_request_log_context,
    record_request_completion,
)
from src.db import session as db_session_module


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP with allowances for Swagger UI
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = perf_counter()
        clear_log_context()
        set_log_context(**build_request_log_context(request))
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = int((perf_counter() - started) * 1000)
            set_log_context(
                status_code=response.status_code if response is not None else 500,
                duration_ms=duration_ms,
                user_id=getattr(request.state, "current_user_id", None),
            )
            if not (
                request.method == "GET"
                and request.url.path.startswith("/api/v1/observability")
            ):
                async with db_session_module.async_session_factory() as session:
                    await record_request_completion(
                        session,
                        request=request,
                        status_code=response.status_code if response is not None else 500,
                        duration_ms=duration_ms,
                    )
                    await session.commit()
            clear_log_context()
