from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from fastapi import Request

from src.db import session as db_session_module
from src.apps.observability.service import record_rate_limit_event

def rate_limit_exceeded_handler(request: Request, exc: Exception):
    if isinstance(exc, RateLimitExceeded):
        async def _persist_rate_limit_event() -> None:
            async with db_session_module.async_session_factory() as session:
                await record_rate_limit_event(session, request=request, detail=str(exc))
                await session.commit()

        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist_rate_limit_event())
        except RuntimeError:
            pass
        return _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
