import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.user import User


class TestAuthenticationSecurity:
    """Test authentication security features."""
    
    @pytest.mark.asyncio
    async def test_password_validation(self, client: AsyncClient):
        """Test password strength validation."""
        # Test weak passwords
        weak_passwords = [
            ("short", "Password too short"),
            ("nouppercase123", "Password must contain uppercase"),
            ("NOLOWERCASE123", "Password must contain lowercase"),
            ("NoDigits!", "Password must contain digit"),
        ]
        
        for password, _ in weak_passwords:
            response = await client.post(
                "/api/v1/auth/signup/?set_cookie=false",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": password,
                    "confirm_password": password
                }
            )
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_duplicate_username_prevention(self, client: AsyncClient, db_session: AsyncSession):
        """Test that duplicate usernames are prevented."""
        user_data = {
            "username": "duplicate_test",
            "email": "user1@example.com",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123"
        }
        
        # First signup should succeed
        response1 = await client.post(
            "/api/v1/auth/signup/?set_cookie=false",
            json=user_data
        )
        assert response1.status_code == 200
        
        # Second signup with same username should fail
        user_data["email"] = "user2@example.com"
        response2 = await client.post(
            "/api/v1/auth/signup/?set_cookie=false",
            json=user_data
        )
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, client: AsyncClient):
        """Test that invalid tokens are rejected."""
        invalid_token = "invalid.token.value"
        headers = {"Authorization": f"Bearer {invalid_token}"}
        
        response = await client.post("/api/v1/auth/logout/", headers=headers)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_max_login_attempts_lockout(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        """Test lockout is enforced after too many failed login attempts."""
        # Reduce the thresholds for speed and determinism
        monkeypatch.setattr("src.apps.core.config.settings.MAX_LOGIN_ATTEMPTS", 2)
        monkeypatch.setattr("src.apps.core.config.settings.ACCOUNT_LOCKOUT_DURATION_MINUTES", 5)
        
        user_data = {
            "username": "lockout_user",
            "email": "lockout@example.com",
            "password": "ValidPass123",
            "confirm_password": "ValidPass123"
        }
        await client.post("/api/v1/auth/signup/?set_cookie=false", json=user_data)

        # Two failed attempts should be accepted (still under the limit)
        for _ in range(2):
            response = await client.post(
                "/api/v1/auth/login/?set_cookie=false",
                json={"username": "lockout_user", "password": "WrongPass"}
            )
            assert response.status_code == 400

        # Third attempt should be blocked by lockout
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "lockout_user", "password": "WrongPass"}
        )
        assert response.status_code == 429
        assert "too many login attempts" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_require_email_verification_before_login(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        """Test login is blocked when email verification is required and user is unconfirmed."""
        monkeypatch.setattr("src.apps.core.config.settings.REQUIRE_EMAIL_VERIFICATION", True)

        user_data = {
            "username": "verify_user",
            "email": "verify@example.com",
            "password": "ValidPass123",
            "confirm_password": "ValidPass123"
        }
        await client.post("/api/v1/auth/signup/?set_cookie=false", json=user_data)

        # Should be blocked until user is confirmed
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "verify_user", "password": "ValidPass123"}
        )
        assert response.status_code == 403

        # Confirm the user in DB and attempt login again
        result = await db_session.execute(select(User).where(User.username == "verify_user"))
        user = result.scalars().first()
        assert user is not None
        user.is_confirmed = True
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "verify_user", "password": "ValidPass123"}
        )
        assert response.status_code == 200
        assert "access" in response.json()
