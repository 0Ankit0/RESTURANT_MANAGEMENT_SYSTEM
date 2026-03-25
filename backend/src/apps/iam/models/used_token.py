from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class UsedTokenBase(SQLModel):
    token_jti: str = Field(
        max_length=255,
        index=True,
        unique=True,
        description="JWT ID (JTI) of the used token to prevent replay"
    )
    token_purpose: str = Field(
        max_length=50,
        description="Purpose of the token (e.g., email_verification, password_reset, ip_action)"
    )
    used_at: datetime = Field(
        default_factory=datetime.now,
        description="When the token was used"
    )


class UsedToken(UsedTokenBase, table=True):
    """
    Model to track used tokens (by their JTI) to prevent replay attacks, especially for critical actions like email verification and password resets.
    """
    id: int = Field(
        default=None,
        primary_key=True,
        description="Unique identifier for the used token entry"
    )
    user_id: Optional[int] = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        description="ID of the user this token belongs to"
    )
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="used_tokens")
