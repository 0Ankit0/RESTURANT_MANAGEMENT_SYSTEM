from __future__ import annotations

from fastapi import Response

from src.apps.core.config import settings


def auth_cookie_options(*, max_age: int) -> dict[str, object]:
    options: dict[str, object] = {
        "httponly": True,
        "secure": settings.SECURE_COOKIES,
        "samesite": settings.COOKIE_SAMESITE,
        "max_age": max_age,
    }
    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN
    return options


def clear_auth_cookies(response: Response) -> None:
    delete_options = {
        "domain": settings.COOKIE_DOMAIN,
        "secure": settings.SECURE_COOKIES,
        "httponly": True,
        "samesite": settings.COOKIE_SAMESITE,
    }
    response.delete_cookie(key=settings.ACCESS_TOKEN_COOKIE, **delete_options)
    response.delete_cookie(key=settings.REFRESH_TOKEN_COOKIE, **delete_options)
