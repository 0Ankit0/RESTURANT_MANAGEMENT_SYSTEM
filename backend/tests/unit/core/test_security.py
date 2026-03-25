import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from hypothesis import given, strategies as st, settings as hypothesis_settings
from hypothesis import HealthCheck

from src.apps.core import security
from src.apps.core.security import TokenType
from src.apps.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        password = "TestPassword123"
        hashed = security.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_correct_password(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = security.get_password_hash(password)
        assert security.verify_password(password, hashed) is True
    
    def test_password_hashing_uses_pepper(self, monkeypatch):
        """Ensure password pepper is applied consistently."""
        password = "TestPassword123"

        monkeypatch.setattr("src.apps.core.config.settings.PASSWORD_PEPPER", "pepper1")
        hashed = security.get_password_hash(password)
        assert security.verify_password(password, hashed) is True

        monkeypatch.setattr("src.apps.core.config.settings.PASSWORD_PEPPER", "pepper2")
        assert security.verify_password(password, hashed) is False

    def test_verify_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = security.get_password_hash(password)
        assert security.verify_password(wrong_password, hashed) is False
    
    @given(st.text(min_size=8, max_size=50).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x and '\x00' not in x))
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000,
        max_examples=20
    )
    def test_hash_various_passwords(self, password):
        """Test hashing with various passwords using Hypothesis."""
        hashed = security.get_password_hash(password)
        assert security.verify_password(password, hashed) is True


class TestAccessToken:
    """Test access token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = 123
        token = security.create_access_token(user_id)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.ACCESS.value
        assert "jti" in payload
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        user_id = 123
        expires_delta = timedelta(minutes=30)
        token = security.create_access_token(user_id, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Check that expiry is approximately 30 minutes from now (within 1 minute tolerance)
        diff = (exp_time - now).total_seconds()
        assert 29 * 60 < diff < 31 * 60
    
    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        user_id = 123
        token = security.create_access_token(user_id)
        payload = security.verify_token(token, token_type=TokenType.ACCESS)
        
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.ACCESS.value
    
    def test_verify_token_wrong_type(self):
        """Test that wrong token type fails verification."""
        user_id = 123
        token = security.create_access_token(user_id)
        
        with pytest.raises(JWTError):
            security.verify_token(token, token_type=TokenType.REFRESH)


class TestRefreshToken:
    """Test refresh token creation and verification."""
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        user_id = 456
        token = security.create_refresh_token(user_id)
        assert token is not None
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.REFRESH.value
        assert "jti" in payload
    
    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token."""
        user_id = 456
        token = security.create_refresh_token(user_id)
        payload = security.verify_token(token, token_type=TokenType.REFRESH)
        
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.REFRESH.value


class TestPasswordResetToken:
    """Test password reset token creation."""
    
    def test_create_password_reset_token(self):
        """Test creating a password reset token."""
        user_id = 789
        token = security.create_password_reset_token(user_id)
        assert token is not None
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.PASSWORD_RESET.value
        assert "jti" in payload
    
    def test_verify_password_reset_token(self):
        """Test verifying a password reset token."""
        user_id = 789
        token = security.create_password_reset_token(user_id)
        payload = security.verify_token(token, token_type=TokenType.PASSWORD_RESET)
        
        assert payload["sub"] == str(user_id)


class TestEmailVerificationToken:
    """Test email verification token creation."""
    
    def test_create_email_verification_token(self):
        """Test creating an email verification token."""
        user_id = 101
        token = security.create_email_verification_token(user_id)
        assert token is not None
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.EMAIL_VERIFICATION.value
    
    def test_verify_email_verification_token(self):
        """Test verifying an email verification token."""
        user_id = 101
        token = security.create_email_verification_token(user_id)
        payload = security.verify_token(token, token_type=TokenType.EMAIL_VERIFICATION)
        
        assert payload["sub"] == str(user_id)


class TestTempAuthToken:
    """Test temporary auth token for OTP validation."""
    
    def test_create_temp_auth_token(self):
        """Test creating a temporary auth token."""
        user_id = 202
        token = security.create_temp_auth_token(user_id)
        assert token is not None
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == TokenType.TEMP_AUTH.value


class TestSecureUrlToken:
    """Test secure URL token creation and verification."""
    
    def test_create_secure_url_token(self):
        """Test creating a secure URL token."""
        data = {"user_id": 123, "action": "verify", "token": "abc123"}
        token = security.create_secure_url_token(data)
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_secure_url_token(self):
        """Test verifying a secure URL token."""
        data = {"user_id": 123, "action": "verify", "token": "abc123"}
        token = security.create_secure_url_token(data)
        verified_data = security.verify_secure_url_token(token)
        
        assert verified_data == data
        assert verified_data["user_id"] == 123
        assert verified_data["action"] == "verify"
    
    def test_verify_tampered_token(self):
        """Test that tampered tokens fail verification."""
        data = {"user_id": 123}
        token = security.create_secure_url_token(data)
        tampered_token = token[:-5] + "xxxxx"
        
        with pytest.raises(JWTError):
            security.verify_secure_url_token(tampered_token)
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x),
        st.one_of(
            st.text(max_size=50).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x),
            st.integers(),
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    @hypothesis_settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
    def test_secure_url_token_various_data(self, data):
        """Test secure URL tokens with various data using Hypothesis."""
        token = security.create_secure_url_token(data)
        verified = security.verify_secure_url_token(token)
        assert verified == data
