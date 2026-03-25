from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .user import User

class BaseLoginAttempt(SQLModel):
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of when the login attempt occurred"
    )
    ip_address: str = Field(
        max_length=45,
        description="IP address from which the login attempt was made"
    )
    attempted_username: str = Field(
        default="",
        max_length=150,
        description="Username submitted during the login attempt"
    )
    user_agent: str = Field(
        max_length=255,
        description="User agent string from the login attempt"
    )
    success: bool = Field(
        default=False,
        description="Indicates whether the login attempt was successful"
    )
    failure_reason: str = Field(
        default="",
        max_length=255,
        description="Reason for login failure, if applicable"
    )

class LoginAttempt(BaseLoginAttempt, table=True):
    """
    Model to track login attempts for users, including metadata about the attempt and whether it was successful. 
    This can be used for security monitoring, brute-force attack prevention, and user behavior analysis.
    """
    id: int = Field(
        default=None, 
        primary_key=True,
        description="Unique identifier for the login attempt"
    )
    user_id: Optional[int] = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        description="ID of the user associated with the login attempt"
    )

    # Relationships
    user: Optional[User] = Relationship(back_populates="login_attempts",passive_deletes=True)
        
