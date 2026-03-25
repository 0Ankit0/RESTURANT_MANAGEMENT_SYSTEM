import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from jose import jwt

from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.core import security
from src.apps.core.config import settings
from src.apps.core.security import TokenType, ALGORITHM
from tests.factories import UserFactory


class TestTokenManagement:
    """Test token management and tracking."""
    
    @pytest.mark.asyncio
    async def test_token_refresh_creates_new_tokens(self, client: AsyncClient, db_session: AsyncSession):
        """Test token refresh creates new tokens with proper rate limit handling."""
        # Add a small delay to avoid rate limiting from previous tests
        await asyncio.sleep(0.1)
        
        # Create user
        hashed_pw = security.get_password_hash("RefreshTest123")
        user = UserFactory.build(
            username="refreshtest_user",
            email="refreshtest@example.com",
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
        assert refresh_jti is not None
        
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
        
        # Add another small delay before making the request
        await asyncio.sleep(0.1)
        
        # Refresh to get new tokens
        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={"refresh_token": refresh_token}
        )
        
        # If we hit rate limit, wait and retry
        if response.status_code == 429:
            await asyncio.sleep(2)
            response = await client.post(
                "/api/v1/auth/refresh/?set_cookie=false",
                json={"refresh_token": refresh_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        
        # New tokens should be different from original
        assert data["access"] != refresh_token
        assert data["refresh"] != refresh_token
    
    @pytest.mark.asyncio
    async def test_token_tracking_on_refresh(self, client: AsyncClient, db_session: AsyncSession):
        """Test that token tracking records are created on refresh."""
        # Add delay to avoid rate limiting
        await asyncio.sleep(0.2)
        
        # Create user
        hashed_pw = security.get_password_hash("TrackTest123")
        user = UserFactory.build(
            username="tracktest_user",
            email="tracktest@example.com",
            hashed_password=hashed_pw,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create and track a refresh token
        refresh_token = security.create_refresh_token(user.id)
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        refresh_jti = refresh_payload.get("jti")
        assert refresh_jti is not None
        
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
        
        # Count tokens before refresh
        from sqlmodel import select, func
        result = await db_session.execute(
            select(func.count(TokenTracking.id)).where(TokenTracking.user_id == user.id) # type: ignore
        )
        count_before = result.scalar()
        
        await asyncio.sleep(0.2)
        
        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={"refresh_token": refresh_token}
        )
        
        if response.status_code == 429:
            await asyncio.sleep(2)
            response = await client.post(
                "/api/v1/auth/refresh/?set_cookie=false",
                json={"refresh_token": refresh_token}
            )
        
        assert response.status_code == 200
        
        # Refresh the session to get latest data
        await db_session.commit()
        
        # Count tokens after refresh (should have 2 more: new access + new refresh)
        result = await db_session.execute(
            select(func.count(TokenTracking.id)).where(TokenTracking.user_id == user.id) # type: ignore
        )
        count_after = result.scalar()
        assert count_after is not None
        assert count_before is not None
        
        # Should have at least 2 more tokens (new access and refresh)
        assert count_after >= count_before + 2
