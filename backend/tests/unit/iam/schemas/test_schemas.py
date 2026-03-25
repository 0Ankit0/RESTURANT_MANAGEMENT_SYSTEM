import pytest
from pydantic import ValidationError
from hypothesis import given, strategies as st

from src.apps.iam.schemas.user import (
    UserCreate,
    LoginRequest,
    ChangePasswordRequest,
    ResetPasswordConfirm,
)


class TestUserCreate:
    """Test UserCreate schema validation."""
    
    def test_valid_user_create(self):
        """Test creating user with valid data."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
            "is_active": True,
            "is_superuser": False,
            "is_confirmed": False
        }
        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_password_too_short(self):
        """Test password validation fails when too short."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="Short1",
                confirm_password="Short1"
            )
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test password validation fails without uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                confirm_password="testpass123"
            )
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test password validation fails without lowercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="TESTPASS123",
                confirm_password="TESTPASS123"
            )
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_no_digit(self):
        """Test password validation fails without digit."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="TestPassword",
                confirm_password="TestPassword"
            )
        assert "digit" in str(exc_info.value)
    
    def test_passwords_dont_match(self):
        """Test password confirmation validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="TestPass123",
                confirm_password="DifferentPass123"
            )
        assert "do not match" in str(exc_info.value)
    
    def test_invalid_email(self):
        """Test email validation with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="TestPass123",
                confirm_password="TestPass123"
            )


class TestChangePasswordRequest:
    """Test ChangePasswordRequest schema validation."""
    
    def test_valid_change_password(self):
        """Test valid password change request."""
        request = ChangePasswordRequest(
            current_password="OldPass123",
            new_password="NewPass456",
            confirm_password="NewPass456"
        )
        assert request.current_password == "OldPass123"
        assert request.new_password == "NewPass456"
    
    def test_new_password_validation(self):
        """Test new password must meet strength requirements."""
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(
                current_password="OldPass123",
                new_password="weak",
                confirm_password="weak"
            )
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_passwords_must_match(self):
        """Test new password and confirmation must match."""
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(
                current_password="OldPass123",
                new_password="NewPass456",
                confirm_password="Different456"
            )
        assert "do not match" in str(exc_info.value)


class TestResetPasswordConfirm:
    """Test ResetPasswordConfirm schema validation."""
    
    def test_valid_reset_password(self):
        """Test valid password reset confirmation."""
        request = ResetPasswordConfirm(
            token="some-token",
            new_password="NewPass123",
            confirm_password="NewPass123"
        )
        assert request.token == "some-token"
        assert request.new_password == "NewPass123"
    
    def test_passwords_must_match(self):
        """Test passwords must match in reset."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordConfirm(
                token="some-token",
                new_password="NewPass123",
                confirm_password="Different123"
            )
        assert "do not match" in str(exc_info.value)


class TestLoginRequest:
    """Test LoginRequest schema."""
    
    def test_valid_login_request(self):
        """Test valid login request."""
        request = LoginRequest(
            username="testuser",
            password="TestPass123"
        )
        assert request.username == "testuser"
        assert request.password == "TestPass123"
    
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=100)
    )
    def test_login_request_various_inputs(self, username, password):
        """Test login request with various inputs using Hypothesis."""
        request = LoginRequest(username=username, password=password)
        assert request.username == username
        assert request.password == password
