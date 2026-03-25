"""Social auth utility helpers: credential lookup, user info normalisation, user creation."""
import re
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core.config import OAUTH_PROVIDERS, settings
from src.apps.iam.models.user import User, UserProfile


def get_provider_credentials(provider: str) -> tuple[str, str]:
    """Return (client_id, client_secret) for *provider* from settings."""
    mapping: dict[str, tuple[str, str]] = {
        "google": (settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
        "github": (settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET),
        "facebook": (settings.FACEBOOK_CLIENT_ID, settings.FACEBOOK_CLIENT_SECRET),
    }
    if provider not in mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' is not supported. Supported: {list(OAUTH_PROVIDERS.keys())}",
        )
    return mapping[provider]


def get_callback_url(provider: str) -> str:
    """Build the absolute callback URL for *provider*."""
    return f"{settings.SERVER_HOST}{settings.API_V1_STR}/auth/social/{provider}/callback"


def extract_user_info(provider: str, data: dict[str, Any]) -> tuple[str, Optional[str], Optional[str]]:
    """Return (social_id, email, display_name) from the provider's raw userinfo payload."""
    if provider == "google":
        return str(data.get("sub") or data.get("id", "")), data.get("email"), data.get("name")
    if provider == "github":
        return str(data.get("id", "")), data.get("email"), data.get("name") or data.get("login")
    if provider == "facebook":
        return str(data.get("id", "")), data.get("email"), data.get("name")
    # Generic fallback for future providers
    return str(data.get("id") or data.get("sub", "")), data.get("email"), data.get("name")


def split_name(full_name: Optional[str]) -> tuple[str, str]:
    """Split a full name string into (first_name, last_name)."""
    if not full_name:
        return "", ""
    parts = full_name.strip().split(" ", 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


async def unique_username(db: AsyncSession, email: str) -> str:
    """Derive a unique username from the local part of *email*."""
    base = re.sub(r"[^a-zA-Z0-9_]", "", email.split("@")[0])[:30] or "user"
    result = await db.execute(select(User).where(User.username == base))
    if not result.scalars().first():
        return base
    for _ in range(10):
        candidate = f"{base}_{uuid.uuid4().hex[:6]}"
        result = await db.execute(select(User).where(User.username == candidate))
        if not result.scalars().first():
            return candidate
    return f"user_{uuid.uuid4().hex[:8]}"


async def find_or_create_social_user(
    db: AsyncSession,
    provider: str,
    social_id: str,
    email: str,
    display_name: Optional[str],
) -> User:
    """
    Resolve a social login to a User row:
      1. Match by (provider, social_id) — returning user.
      2. Match by email — link social identity to existing account.
      3. Create a brand-new account with a generated username.
    """
    # 1. Exact social-account match
    result = await db.execute(
        select(User).where(User.social_provider == provider, User.social_id == social_id)
    )
    user = result.scalars().first()
    if user:
        return user

    # 2. Email match → link social identity to existing account
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user:
        user.social_provider = provider
        user.social_id = social_id
        if not user.is_confirmed:
            user.is_confirmed = True  # provider has already verified the email
        await db.commit()
        await db.refresh(user)
        return user

    # 3. Create brand-new account
    username = await unique_username(db, email)
    first_name, last_name = split_name(display_name)
    new_user = User(
        username=username,
        email=email,
        hashed_password=None,
        is_confirmed=True,
        social_provider=provider,
        social_id=social_id,
    )
    db.add(new_user)
    db.add(UserProfile(first_name=first_name, last_name=last_name, user=new_user))
    await db.commit()
    await db.refresh(new_user)
    return new_user
