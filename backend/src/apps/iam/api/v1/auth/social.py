"""Social OAuth2 login endpoints — thin router, all logic delegated to utils and config."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from src.apps.core import security
from src.apps.core.config import OAUTH_PROVIDERS, settings
from src.apps.core.cookies import auth_cookie_options
from src.apps.core.http import default_timeout, retry_async
from src.apps.core.security import TokenType
from src.apps.iam.api.deps import get_db
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.iam.utils.ip_access import revoke_tokens_for_ip, get_client_ip
from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.events import AuthEvents
from src.apps.observability.service import record_successful_login_event, record_token_event
from src.apps.iam.utils.social import (
    extract_user_info,
    find_or_create_social_user,
    get_callback_url,
    get_provider_credentials,
)

router = APIRouter()

# Maps provider name → its enabled setting flag
_PROVIDER_ENABLED: dict[str, bool] = {
    "google": settings.GOOGLE_ENABLED,
    "github": settings.GITHUB_ENABLED,
    "facebook": settings.FACEBOOK_ENABLED,
}


def _assert_provider_enabled(provider: str) -> None:
    """Raise 400 if the provider is disabled or unknown."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' is not supported. Supported: {list(OAUTH_PROVIDERS.keys())}",
        )
    if not _PROVIDER_ENABLED.get(provider, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Social login with '{provider}' is not enabled.",
        )


@router.get(
    "/social/providers/",
    summary="List enabled social auth providers",
    description="Returns a list of social OAuth2 providers that are currently enabled.",
)
async def list_social_providers() -> dict:
    enabled = [p for p, on in _PROVIDER_ENABLED.items() if on]
    return {"providers": enabled}


@router.get(
    "/social/{provider}/",
    summary="Initiate social login",
    description="Redirects the browser to the OAuth2 provider's login page. Supported: google, github, facebook.",
)
async def social_login(provider: str) -> RedirectResponse:
    _assert_provider_enabled(provider)
    config = OAUTH_PROVIDERS[provider]
    client_id, _ = get_provider_credentials(provider)
    params: dict[str, Any] = {
        "client_id": client_id,
        "redirect_uri": get_callback_url(provider),
        "scope": config["scope"],
        "state": security.create_oauth_state(provider),
        **config.get("extra_params", {}),
    }
    return RedirectResponse(url=f"{config['authorize_url']}?{urlencode(params)}")


@router.get(
    "/social/{provider}/callback",
    summary="Handle OAuth2 callback",
    description=(
        "Exchanges the authorization code for tokens, retrieves user info, "
        "and issues JWT access/refresh tokens. Pass set_cookie=true to receive "
        "tokens via HttpOnly cookie instead of JSON."
    ),
)
async def social_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    set_cookie: bool = False,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> RedirectResponse:
    _assert_provider_enabled(provider)

    if not security.verify_oauth_state(state, provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state. Please try again.",
        )

    config = OAUTH_PROVIDERS[provider]
    client_id, client_secret = get_provider_credentials(provider)
    callback_url = get_callback_url(provider)

    async with httpx.AsyncClient() as http:
        # Exchange authorization code for provider access token
        try:
            token_resp = await retry_async(
                lambda: http.post(
                    config["token_url"],
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "redirect_uri": callback_url,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=default_timeout(),
                )
            )
            token_resp.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to obtain access token from {provider}",
            )

        provider_token: Optional[str] = token_resp.json().get("access_token")
        if not provider_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"No access token returned by {provider}",
            )

        # Fetch user profile from provider
        try:
            info_resp = await retry_async(
                lambda: http.get(
                    config["userinfo_url"],
                    headers={
                        "Authorization": f"Bearer {provider_token}",
                        "Accept": "application/json",
                        "User-Agent": "FastAPI-Template/1.0",
                    },
                    timeout=default_timeout(),
                )
            )
            info_resp.raise_for_status()
            user_info: dict[str, Any] = info_resp.json()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch user info from {provider}",
            )

        # GitHub may keep email private — fetch it from the dedicated emails endpoint
        if provider == "github" and not user_info.get("email"):
            try:
                emails_resp = await retry_async(
                    lambda: http.get(
                        config["emails_url"],
                        headers={
                            "Authorization": f"Bearer {provider_token}",
                            "Accept": "application/json",
                            "User-Agent": "FastAPI-Template/1.0",
                        },
                        timeout=default_timeout(),
                    )
                )
                emails_resp.raise_for_status()
                primary = next(
                    (e["email"] for e in emails_resp.json() if e.get("primary") and e.get("verified")),
                    None,
                )
                if primary:
                    user_info["email"] = primary
            except Exception:
                pass

    social_id, email, display_name = extract_user_info(provider, user_info)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not retrieve email from {provider}. Please grant email permission and try again.",
        )

    user = await find_or_create_social_user(db, provider, social_id, email, display_name)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account has been deactivated.")

    # Whitelist the current IP — social login is already authenticated by the provider
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")

    # Issue application JWT tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id)

    access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])

    # Revoke any existing active tokens for this user+IP before issuing new ones
    await revoke_tokens_for_ip(db, user.id, ip_address)

    db.add(TokenTracking(
        user_id=user.id,
        token_jti=access_payload["jti"],
        token_type=TokenType.ACCESS,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc),
    ))
    db.add(TokenTracking(
        user_id=user.id,
        token_jti=refresh_payload["jti"],
        token_type=TokenType.REFRESH,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
    ))
    await db.commit()
    await record_successful_login_event(
        db,
        user_id=user.id,
        ip_address=ip_address,
        request=request,
        method=f"social:{provider}",
    )
    await record_token_event(
        db,
        user_id=user.id,
        ip_address=ip_address,
        action="issued",
        request=request,
        metadata={"issued_tokens": 2, "auth_method": f"social:{provider}"},
    )
    await db.commit()

    await analytics.capture(
        str(user.id),
        AuthEvents.LOGGED_IN_SOCIAL,
        {"provider": provider, "ip_address": ip_address, "user_agent": user_agent},
    )

    # Redirect the popup back to the frontend auth-callback page with tokens as
    # query params. The /auth-callback page stores the tokens and continues the flow.
    frontend_callback = f"{settings.FRONTEND_URL}/auth-callback"

    if set_cookie:
        redirect_resp = RedirectResponse(url=frontend_callback, status_code=302)
        redirect_resp.set_cookie(
            key=settings.ACCESS_TOKEN_COOKIE,
            value=access_token,
            **auth_cookie_options(max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        )
        return redirect_resp

    return RedirectResponse(
        url=f"{frontend_callback}?access={access_token}&refresh={refresh_token}",
        status_code=302,
    )
