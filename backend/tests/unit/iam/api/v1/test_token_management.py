import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.login_attempt import LoginAttempt
from src.apps.iam.models.user import User
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.core import security
from src.apps.core.security import TokenType


class TestTokenTracking:
    """Test token tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_login_creates_token_tracking(self, client: AsyncClient, db_session: AsyncSession):
        """Test that login creates token tracking records."""
        # Create user with whitelisted IP and unique username
        username = f"trackuser_{uuid.uuid4().hex[:8]}"
        hashed_pw = security.get_password_hash("TestPass123")
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=hashed_pw,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Login
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": username, "password": "TestPass123"}
        )
        
        assert response.status_code == 200
        
        # Check token tracking records were created
        result = await db_session.execute(
            select(TokenTracking).where(TokenTracking.user_id == user.id)
        )
        tokens = result.scalars().all()
        
        # Should have access and refresh token tracking
        assert len(tokens) >= 2
        token_types = [t.token_type for t in tokens]
        assert TokenType.ACCESS in token_types
        assert TokenType.REFRESH in token_types
    
    @pytest.mark.asyncio
    async def test_signup_creates_token_tracking(self, client: AsyncClient, db_session: AsyncSession):
        """Test that signup creates token tracking records."""
        signup_data = {
            "username": "signuptrack",
            "email": "signuptrack@example.com",
            "password": "TestPass123",
            "confirm_password": "TestPass123"
        }
        
        response = await client.post(
            "/api/v1/auth/signup/?set_cookie=false",
            json=signup_data
        )
        
        assert response.status_code == 200
        
        # Get the created user
        result = await db_session.execute(
            select(User).where(User.username == "signuptrack")
        )
        user = result.scalars().first()
        assert user is not None
        
        # Check token tracking
        token_result = await db_session.execute(
            select(TokenTracking).where(TokenTracking.user_id == user.id)
        )
        tokens = token_result.scalars().all()
        assert len(tokens) >= 2


class TestLoginAttemptTracking:
    """Test login attempt tracking."""
    
    @pytest.mark.asyncio
    async def test_failed_login_tracked(self, client: AsyncClient, db_session: AsyncSession):
        """Test failed login attempts are tracked."""
        # Try to login with non-existent user
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "nonexistent", "password": "TestPass123"}
        )
        
        assert response.status_code == 400
        
        # Check login attempt was tracked
        result = await db_session.execute(
            select(LoginAttempt).where(LoginAttempt.success == False)
        )
        attempts = result.scalars().all()
        assert len(attempts) > 0
    
    @pytest.mark.asyncio
    async def test_successful_login_tracked(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login attempts are tracked."""
        # Create user with whitelisted IP
        hashed_pw = security.get_password_hash("TestPass123")
        user = User(
            username="successtrack",
            email="success@example.com",
            hashed_password=hashed_pw,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Login
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "successtrack", "password": "TestPass123"}
        )
        
        assert response.status_code == 200
        
        # Check successful login was tracked
        result = await db_session.execute(
            select(LoginAttempt).where(
                LoginAttempt.user_id == user.id,
                LoginAttempt.success == True
            )
        )
        attempt = result.scalars().first()
        assert attempt is not None
        assert attempt.success is True
