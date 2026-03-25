from hypothesis import given, settings as h_settings, strategies as st

from tests.factories import (
    UserFactory,
    UserProfileFactory,
    LoginAttemptFactory,
    TokenTrackingFactory,
)
from src.apps.core.security import TokenType


class TestUserFactory:
    """Test UserFactory."""
    
    def test_create_user(self):
        """Test creating a user with factory."""
        user = UserFactory.build()
        assert user.username is not None
        assert user.email is not None
        assert user.hashed_password is not None
        assert user.is_active is True
    
    def test_create_user_with_overrides(self):
        """Test creating user with custom values."""
        user = UserFactory.build(
            username="customuser",
            email="custom@example.com",
            is_superuser=True
        )
        assert user.username == "customuser"
        assert user.email == "custom@example.com"
        assert user.is_superuser is True
    
    @given(username=st.text(min_size=1, max_size=50))
    @h_settings(deadline=None)
    def test_create_users_various_usernames(self, username):
        """Test creating users with various usernames using Hypothesis."""
        user = UserFactory.build(username=username)
        assert user.username == username


class TestUserProfileFactory:
    """Test UserProfileFactory."""
    
    def test_create_profile(self):
        """Test creating a profile with factory."""
        profile = UserProfileFactory.build()
        assert profile.first_name is not None
        assert profile.last_name is not None
    
    def test_create_profile_with_overrides(self):
        """Test creating profile with custom values."""
        profile = UserProfileFactory.build(
            first_name="John",
            last_name="Doe"
        )
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"


class TestLoginAttemptFactory:
    """Test LoginAttemptFactory."""
    
    def test_create_login_attempt(self):
        """Test creating a login attempt with factory."""
        attempt = LoginAttemptFactory.build()
        assert attempt.user_id is not None
        assert attempt.ip_address is not None
        assert attempt.success is True
    
    def test_create_failed_attempt(self):
        """Test creating a failed login attempt."""
        attempt = LoginAttemptFactory.build(
            success=False,
            failure_reason="Invalid password"
        )
        assert attempt.success is False
        assert attempt.failure_reason == "Invalid password"


class TestTokenTrackingFactory:
    """Test TokenTrackingFactory."""
    
    def test_create_token_tracking(self):
        """Test creating a token tracking record with factory."""
        tracking = TokenTrackingFactory.build()
        assert tracking.user_id is not None
        assert tracking.token_jti is not None
        assert tracking.token_type == TokenType.ACCESS
        assert tracking.is_active is True
    
    def test_create_refresh_token_tracking(self):
        """Test creating refresh token tracking."""
        tracking = TokenTrackingFactory.build(token_type=TokenType.REFRESH)
        assert tracking.token_type == TokenType.REFRESH
