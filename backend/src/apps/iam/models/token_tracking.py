from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SAEnum
from src.apps.core.security import TokenType

if TYPE_CHECKING:
    from .user import User


class TokenTrackingBase(SQLModel):
    token_jti: str = Field(
        max_length=255,
        index=True,
        unique=True,
        description="JWT ID (JTI) - unique identifier for the token"
    )
    token_type: TokenType = Field(
        sa_column=Column(SAEnum(TokenType, values_callable=lambda e: [m.value for m in e])),
        description="Type of token: access, refresh"
    )
    ip_address: str = Field(
        max_length=45,
        description="IP address where token was issued"
    )
    user_agent: str = Field(
        max_length=255,
        description="User agent string when token was issued"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the token is still active"
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        description="When the token was revoked"
    )
    revoke_reason: str = Field(
        default="",
        max_length=255,
        description="Reason for token revocation"
    )
    expires_at: datetime = Field(
        description="When the token expires"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the token was created"
    )


class TokenTracking(TokenTrackingBase, table=True):
    """
    Model to track issued tokens for users, including their status and metadata.
    """
    id: int = Field(
        default=None,
        primary_key=True,
        description="Unique identifier for the token tracking entry"
    )
    user_id: Optional[int] = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        description="ID of the user this token belongs to"
    )

    # Relationships
    user: Optional[User] = Relationship(back_populates="tokens")
