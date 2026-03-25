import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from src.apps.core.config import settings
from tests.factories import UserFactory


class TestTokenRefresh:
    """Test token refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh."""
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from src.apps.iam.models.token_tracking import TokenTracking
        from src.apps.core.security import TokenType, ALGORITHM
        
        # Create user
        hashed_pw = security.get_password_hash("TestPass123")
        user = UserFactory.build(
            username="refreshuser",
            hashed_password=hashed_pw,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a refresh token
        refresh_token = security.create_refresh_token(user.id)
        
        # Extract JTI from the token and create tracking entry
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        refresh_jti = refresh_payload.get("jti")
        
        token_tracking = TokenTracking(
            user_id=user.id,
            token_jti=refresh_jti,
            token_type=TokenType.REFRESH,
            ip_address="127.0.0.1",
            user_agent="test-agent",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db_session.add(token_tracking)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    @pytest.mark.asyncio
    async def test_refresh_token_cookie_uses_configured_cookie_settings(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from src.apps.iam.models.token_tracking import TokenTracking
        from src.apps.core.security import TokenType, ALGORITHM

        user = UserFactory.build(
            username="refreshcookieuser",
            hashed_password=security.get_password_hash("TestPass123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        refresh_token = security.create_refresh_token(user.id)
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        db_session.add(
            TokenTracking(
                user_id=user.id,
                token_jti=refresh_payload.get("jti"),
                token_type=TokenType.REFRESH,
                ip_address="127.0.0.1",
                user_agent="test-agent",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=true",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        cookie_header = response.headers.get("set-cookie", "").lower()
        assert f"samesite={settings.COOKIE_SAMESITE}" in cookie_header
    
    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, client: AsyncClient):
        """Test refresh without token."""
        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={}
        )
        
        assert response.status_code == 401
        assert "missing" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code in [401, 500]
