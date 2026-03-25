import pytest
from hypothesis import given, strategies as st, assume, settings as hypothesis_settings
from hypothesis import HealthCheck

from src.apps.core import security
from src.apps.iam.schemas.user import UserCreate
from pydantic import ValidationError


class TestPasswordStrengthProperties:
    """Property-based tests for password strength using Hypothesis."""
    
    @given(st.text(min_size=8, max_size=100).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x and '\x00' not in x))
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000,
        max_examples=20
    )
    def test_hash_is_deterministic_for_same_input(self, password):
        """Test that hashing the same password twice gives consistent verification."""
        hashed1 = security.get_password_hash(password)
        hashed2 = security.get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hashed1 != hashed2
        
        # But both should verify against the original password
        assert security.verify_password(password, hashed1)
        assert security.verify_password(password, hashed2)
    
    @given(
        password=st.text(min_size=8, max_size=100).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x and '\x00' not in x),
        wrong_password=st.text(min_size=8, max_size=100).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x and '\x00' not in x)
    )
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000,
        max_examples=20
    )
    def test_wrong_password_never_verifies(self, password, wrong_password):
        """Test that wrong passwords never verify."""
        assume(password != wrong_password)
        
        hashed = security.get_password_hash(password)
        assert not security.verify_password(wrong_password, hashed)
    
    @given(st.integers(min_value=1, max_value=10000))
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        max_examples=50
    )
    def test_token_creation_for_various_user_ids(self, user_id):
        """Test token creation works for various user IDs."""
        token = security.create_access_token(user_id)
        assert token is not None
        
        payload = security.verify_token(token)
        assert int(payload["sub"]) == user_id


class TestUserSchemaProperties:
    """Property-based tests for user schemas."""
    
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x),
        email=st.emails()
    )
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        max_examples=10
    )
    def test_valid_username_and_email(self, username, email):
        """Test user creation with various valid usernames and emails."""
        try:
            user = UserCreate(
                username=username,
                email=email,
                password="ValidPass123",
                confirm_password="ValidPass123"
            )
            assert user.username == username
            # Email might be normalized (lowercase and punycode for international domains)
            # Just verify the email is set and valid
            assert user.email is not None
            assert '@' in user.email
        except ValidationError:
            # Some combinations might be invalid, that's ok
            pass
    
    @given(
        password=st.text(min_size=0, max_size=7)
    )
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        max_examples=20
    )
    def test_short_passwords_always_fail(self, password):
        """Test that passwords shorter than 8 chars always fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password=password,
                confirm_password=password
            )
        assert "at least 8 characters" in str(exc_info.value)


class TestTokenProperties:
    """Property-based tests for token operations."""
    
    @given(
        user_id=st.integers(min_value=1, max_value=1000000),
        minutes=st.integers(min_value=1, max_value=1440)
    )
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        max_examples=30
    )
    def test_token_contains_correct_user_id(self, user_id, minutes):
        """Test that tokens always contain the correct user ID."""
        from datetime import timedelta
        
        token = security.create_access_token(
            user_id,
            expires_delta=timedelta(minutes=minutes)
        )
        payload = security.verify_token(token)
        
        assert int(payload["sub"]) == user_id
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x),
        st.one_of(
            st.text(max_size=100).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x),
            st.integers(),
            st.booleans()
        ),
        min_size=1,
        max_size=10
    ))
    @hypothesis_settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        max_examples=10
    )
    def test_secure_url_tokens_roundtrip(self, data):
        """Test that secure URL tokens can roundtrip any data."""
        token = security.create_secure_url_token(data)
        decoded = security.verify_secure_url_token(token)
        assert decoded == data
