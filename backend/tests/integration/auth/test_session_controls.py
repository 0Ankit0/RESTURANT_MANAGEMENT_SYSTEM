import pytest
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from src.apps.core.config import settings
from src.apps.core.security import ALGORITHM, TokenType
from src.apps.iam.models.token_tracking import TokenTracking
from tests.factories import UserFactory


async def _create_user(db_session: AsyncSession, username: str) -> int:
    user = UserFactory.build(
        username=username,
        email=f"{username}@example.com",
        hashed_password=security.get_password_hash("Password123!"),
        is_active=True,
        is_confirmed=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id


@pytest.mark.asyncio
async def test_login_refresh_logout_and_revoke_all(client: AsyncClient, db_session: AsyncSession):
    user_id = await _create_user(db_session, "session_user")

    login_resp = await client.post(
        "/api/v1/auth/login/?set_cookie=false",
        json={"username": "session_user", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["access"]
    assert login_data["refresh"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh/?set_cookie=false",
        json={"refresh_token": login_data["refresh"]},
    )
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert refreshed["refresh"] != login_data["refresh"]

    # old refresh token cannot be reused after rotation
    reused_resp = await client.post(
        "/api/v1/auth/refresh/?set_cookie=false",
        json={"refresh_token": login_data["refresh"]},
    )
    assert reused_resp.status_code == 401

    headers = {"Authorization": f"Bearer {refreshed['access']}"}
    logout_resp = await client.post("/api/v1/auth/logout/", headers=headers)
    assert logout_resp.status_code == 200

    list_after_logout = await client.get("/api/v1/tokens/", headers=headers)
    assert list_after_logout.status_code == 401

    # login again to create active session and then revoke all
    login_resp_2 = await client.post(
        "/api/v1/auth/login/?set_cookie=false",
        json={"username": "session_user", "password": "Password123!"},
    )
    second_tokens = login_resp_2.json()
    headers_2 = {"Authorization": f"Bearer {second_tokens['access']}"}

    revoke_all_resp = await client.post("/api/v1/tokens/revoke-all", headers=headers_2)
    assert revoke_all_resp.status_code == 200

    compromised_refresh = await client.post(
        "/api/v1/auth/refresh/?set_cookie=false",
        json={"refresh_token": second_tokens["refresh"]},
    )
    assert compromised_refresh.status_code == 401

    result = await db_session.execute(
        select(TokenTracking).where(TokenTracking.user_id == user_id)
    )
    tracked = result.scalars().all()
    assert tracked
    assert any(t.revoke_reason for t in tracked)


@pytest.mark.asyncio
async def test_compromised_session_revoked_refresh_fails(client: AsyncClient, db_session: AsyncSession):
    user_id = await _create_user(db_session, "compromised_user")

    refresh_token = security.create_refresh_token(user_id)
    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    tracked_refresh = TokenTracking(
        user_id=user_id,
        token_jti=payload["jti"],
        token_type=TokenType.REFRESH,
        ip_address="127.0.0.1",
        user_agent="test-agent",
        is_active=False,
        revoked_at=datetime.now(timezone.utc),
        revoke_reason="security_alert",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(tracked_refresh)
    await db_session.commit()

    refresh_resp = await client.post(
        "/api/v1/auth/refresh/?set_cookie=false",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
    assert "revoked" in refresh_resp.json()["detail"].lower()
