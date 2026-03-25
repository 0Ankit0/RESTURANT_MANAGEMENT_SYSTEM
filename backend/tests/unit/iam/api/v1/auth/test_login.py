import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from tests.factories import UserFactory


class TestLogin:
    """Test login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login."""
        # Create user with whitelisted IP
        hashed_pw = security.get_password_hash("TestPass123")
        user = UserFactory.build(
            username="loginuser",
            email="login@example.com",
            hashed_password=hashed_pw,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        login_data = {
            "username": "loginuser",
            "password": "TestPass123"
        }
        
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with wrong password."""
        hashed_pw = security.get_password_hash("TestPass123")
        user = UserFactory.build(
            username="wrongpwuser",
            hashed_password=hashed_pw
        )
        db_session.add(user)
        await db_session.commit()
        
        login_data = {
            "username": "wrongpwuser",
            "password": "WrongPass456"
        }
        
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json=login_data
        )
        
        assert response.status_code == 400
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "TestPass123"
        }
        
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json=login_data
        )
        
        assert response.status_code == 400
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user."""
        hashed_pw = security.get_password_hash("TestPass123")
        user = UserFactory.build(
            username="inactiveuser",
            hashed_password=hashed_pw,
            is_active=False
        )
        db_session.add(user)
        await db_session.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "TestPass123"
        }
        
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json=login_data
        )
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
