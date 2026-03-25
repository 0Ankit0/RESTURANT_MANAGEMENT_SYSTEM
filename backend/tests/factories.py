from factory.faker import Faker
from factory.base import Factory
from datetime import datetime, timezone
from factory.declarations import LazyAttribute
from src.apps.iam.models.user import User, UserProfile
from src.apps.iam.models.login_attempt import LoginAttempt
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.core import security
from src.apps.core.security import TokenType


class UserFactory(Factory):
    """Factory for creating User instances."""
    
    class Meta(): # type: ignore
        model = User
    
    username = Faker("user_name")
    email = Faker("email")
    hashed_password = LazyAttribute(lambda obj: security.get_password_hash("TestPass123"))
    is_active = True
    is_superuser = False
    is_confirmed = False
    otp_enabled = False
    otp_verified = False
    otp_base32 = ""
    otp_auth_url = ""
    created_at = LazyAttribute(lambda _: datetime.now(timezone.utc))


class UserProfileFactory(Factory):
    """Factory for creating UserProfile instances."""
    
    class Meta(): # type: ignore
        model = UserProfile
    
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    phone = Faker("phone_number")
    image_url = Faker("image_url")
    bio = Faker("text", max_nb_chars=200)


class LoginAttemptFactory(Factory):
    """Factory for creating LoginAttempt instances."""
    
    class Meta(): # type: ignore
        model = LoginAttempt
    
    user_id = Faker("random_int", min=1, max=1000)
    ip_address = Faker("ipv4")
    user_agent = "Mozilla/5.0 Test Browser"
    success = True
    failure_reason = ""
    timestamp = LazyAttribute(lambda _: datetime.now(timezone.utc))


class TokenTrackingFactory(Factory):
    """Factory for creating TokenTracking instances."""
    
    class Meta(): # type: ignore
        model = TokenTracking
    
    user_id = Faker("random_int", min=1, max=1000)
    token_jti = Faker("uuid4")
    token_type = TokenType.ACCESS
    ip_address = Faker("ipv4")
    user_agent = "Mozilla/5.0 Test Browser"
    is_active = True
    created_at = LazyAttribute(lambda _: datetime.now(timezone.utc))
    expires_at = LazyAttribute(lambda _: datetime.now(timezone.utc))
