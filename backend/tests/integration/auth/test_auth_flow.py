import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.user import User


class TestCompleteAuthenticationFlow:
    """End-to-end authentication flow integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete user lifecycle from signup to logout."""
        # Step 1: User Signup
        signup_data = {
            "username": "lifecycle_user",
            "email": "lifecycle@example.com",
            "password": "LifeCycle123!",
            "confirm_password": "LifeCycle123!",
            "first_name": "Life",
            "last_name": "Cycle"
        }
        
        signup_response = await client.post(
            "/api/v1/auth/signup/?set_cookie=false",
            json=signup_data
        )
        assert signup_response.status_code == 200
        signup_data_resp = signup_response.json()
        assert "access" in signup_data_resp
        assert "refresh" in signup_data_resp
        access_token_1 = signup_data_resp["access"]
        refresh_token_1 = signup_data_resp["refresh"]
        
        # Verify user was created
        result = await db_session.execute(
            select(User).where(User.username == "lifecycle_user")
        )
        user = result.scalars().first()
        assert user is not None
        assert user.email == "lifecycle@example.com"
        assert user.is_active is True
        
        # Verify profile was created
        assert user.profile is not None
        assert user.profile.first_name == "Life"
        assert user.profile.last_name == "Cycle"
        
        # Step 2: Login with credentials
        login_response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "lifecycle_user", "password": "LifeCycle123!"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["access"]
        refresh_token_login = login_data["refresh"]
        
        # Step 3: Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh/?set_cookie=false",
            json={"refresh_token": refresh_token_login}
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        access_token_2 = refresh_data["access"]
        refresh_token_2 = refresh_data["refresh"]
        assert access_token_2 != access_token_1
        assert refresh_token_2 != refresh_token_1
        
        # Step 4: Login again with new token works
        login_response_2 = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "lifecycle_user", "password": "LifeCycle123!"}
        )
        assert login_response_2.status_code == 200
        login_data_2 = login_response_2.json()

        # Step 5: Logout
        headers_2 = {"Authorization": f"Bearer {login_data_2['access']}"}
        logout_response = await client.post("/api/v1/auth/logout/", headers=headers_2)
        assert logout_response.status_code == 200
