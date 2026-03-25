from datetime import datetime, timedelta

from src.apps.iam.models.user import User, UserProfile
from src.apps.iam.models.login_attempt import LoginAttempt
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.core.security import TokenType


class TestUserModel:
    """Test User model."""
    
    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pw",
            is_active=True,
            is_superuser=False,
            is_confirmed=False
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.is_confirmed is False
    
    def test_user_defaults(self):
        """Test user default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pw"
        )
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.is_confirmed is False
        assert user.otp_enabled is False
        assert user.otp_verified is False


class TestUserProfileModel:
    """Test UserProfile model."""
    
    def test_profile_creation(self):
        """Test creating a user profile."""
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            bio="Test bio"
        )
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.phone == "+1234567890"


class TestLoginAttemptModel:
    """Test LoginAttempt model."""
    
    def test_login_attempt_success(self):
        """Test successful login attempt."""
        attempt = LoginAttempt(
            user_id=1,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            success=True,
            failure_reason=""
        )
        assert attempt.success is True
        assert attempt.failure_reason == ""
    
    def test_login_attempt_failure(self):
        """Test failed login attempt."""
        attempt = LoginAttempt(
            user_id=1,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            success=False,
            failure_reason="Invalid password"
        )
        assert attempt.success is False
        assert attempt.failure_reason == "Invalid password"


class TestTokenTrackingModel:
    """Test TokenTracking model."""
    
    def test_token_tracking_creation(self):
        """Test creating a token tracking record."""
        tracking = TokenTracking(
            user_id=1,
            token_jti="unique-jti-123",
            token_type=TokenType.ACCESS,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            is_active=True,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert tracking.user_id == 1
        assert tracking.token_jti == "unique-jti-123"
        assert tracking.token_type == TokenType.ACCESS
        assert tracking.is_active is True
