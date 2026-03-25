from datetime import datetime, timedelta, timezone
from typing import Any, Union
from enum import Enum
import uuid
import base64

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.apps.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _apply_pepper(password: str) -> str:
    """Append a secret pepper to the password before hashing/verifying.

    The pepper is an additional secret value stored in the application
    configuration layer, so if an attacker obtains the password hashes they
    still need the pepper to brute-force passwords.
    """
    pepper = settings.PASSWORD_PEPPER or ""
    return password + pepper

ALGORITHM = "HS256"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    TEMP_AUTH = "temp_auth"
    BEARER = "bearer"


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.ACCESS.value,
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.REFRESH.value,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_password_reset_token(subject: Union[str, Any]) -> str:
    """Create a password reset token valid for 1 hour"""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.PASSWORD_RESET.value,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_email_verification_token(subject: Union[str, Any]) -> str:
    """Create an email verification token valid for 24 hours"""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.EMAIL_VERIFICATION.value,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_temp_auth_token(subject: Union[str, Any]) -> str:
    """Create a temporary auth token for OTP validation, valid for 5 minutes"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.TEMP_AUTH.value,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: TokenType | None = None) -> dict:
    """
    Decode and verify a JWT token.
    If token_type is provided, checks that the 'type' claim matches.
    Raises jwt.JWTError if the token is invalid, expired, or has wrong type.
    Returns the payload dictionary on success.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    if token_type and payload.get("type") != token_type.value:
        raise JWTError(f"Invalid token type, expected {token_type.value}")
    return payload

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_apply_pepper(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_apply_pepper(password))


def validate_password_strength(password: str) -> None:
    """Validate password strength based on current settings.

    Raises ValueError when the password does not meet requirements.
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")

    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")

    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")

    if settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit")

    if settings.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`"
        if not any(c in special_chars for c in password):
            raise ValueError("Password must contain at least one special character")


def create_secure_url_token(data: dict[str, Any], expires_hours: int = 24) -> str:
    """
    Create a secure, encrypted, tamper-proof URL token.
    Data is encrypted and signed using JWT.
    Returns a URL-safe base64 encoded token.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode = {
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "data": data
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    # Make it URL-safe
    url_safe_token = base64.urlsafe_b64encode(encoded_jwt.encode()).decode()
    return url_safe_token


def verify_secure_url_token(url_token: str) -> dict[str, Any]:
    """
    Verify and decrypt a secure URL token.
    Returns the data dict if valid, raises JWTError if invalid/expired/tampered.
    """
    try:
        # Decode from URL-safe base64
        encoded_jwt = base64.urlsafe_b64decode(url_token.encode()).decode()
        payload = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("data", {})
    except Exception as e:
        raise JWTError(f"Invalid or tampered token: {str(e)}")


def create_oauth_state(provider: str) -> str:
    """Create a signed, short-lived JWT used as the OAuth2 *state* parameter for CSRF protection."""
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "sub": provider,
        "nonce": str(uuid.uuid4()),
        "type": "oauth_state",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_oauth_state(state: str, provider: str) -> bool:
    """Return True if *state* is a valid, unexpired oauth_state token for *provider*."""
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("type") == "oauth_state" and payload.get("sub") == provider
    except JWTError:
        return False
