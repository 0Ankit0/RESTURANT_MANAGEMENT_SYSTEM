from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.apps.iam.models.user import User


class TenantRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ── Tenant ───────────────────────────────────────────────────────────────────

class TenantBase(SQLModel):
    name: str = Field(max_length=100, description="Display name of the tenant")
    slug: str = Field(
        max_length=63,
        unique=True,
        index=True,
        regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
        description="URL-safe unique identifier (lowercase, hyphens allowed)",
    )
    description: str = Field(default="", max_length=500, description="Tenant description")
    is_active: bool = Field(default=True, description="Whether the tenant is active")


class Tenant(TenantBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        description="User ID of the tenant owner",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    members: list["TenantMember"] = Relationship(back_populates="tenant")
    invitations: list["TenantInvitation"] = Relationship(back_populates="tenant")
    owner: Optional["User"] = Relationship(
        back_populates="owned_tenants",
        sa_relationship_kwargs={"foreign_keys": "[Tenant.owner_id]"},
    )


# ── TenantMember ─────────────────────────────────────────────────────────────

class TenantMemberBase(SQLModel):
    role: TenantRole = Field(
        default=TenantRole.MEMBER,
        description="Role of the user within the tenant",
    )
    is_active: bool = Field(default=True, description="Whether the membership is active")


class TenantMember(TenantMemberBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(
        default=None,
        foreign_key="tenant.id",
        index=True,
        ondelete="CASCADE",
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        index=True,
        ondelete="CASCADE",
    )
    joined_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="members")
    user: Optional["User"] = Relationship(back_populates="tenant_memberships")


# ── TenantInvitation ─────────────────────────────────────────────────────────

class TenantInvitationBase(SQLModel):
    email: str = Field(max_length=255, index=True, description="Invited email address")
    role: TenantRole = Field(default=TenantRole.MEMBER, description="Role granted on acceptance")
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)


class TenantInvitation(TenantInvitationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(
        default=None,
        foreign_key="tenant.id",
        index=True,
        ondelete="CASCADE",
    )
    invited_by: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        description="User ID who sent the invitation",
    )
    token: str = Field(max_length=255, unique=True, index=True, description="One-time invitation token")
    expires_at: datetime = Field(description="When the invitation expires")
    created_at: datetime = Field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = Field(default=None)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="invitations")
    inviter: Optional["User"] = Relationship(
        back_populates="sent_invitations",
        sa_relationship_kwargs={"foreign_keys": "[TenantInvitation.invited_by]"},
    )
