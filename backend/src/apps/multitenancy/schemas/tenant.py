from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_serializer, field_validator
import re
from src.apps.multitenancy.models.tenant import TenantRole, InvitationStatus
from src.apps.iam.utils.hashid import encode_id


# ── Request schemas ──────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str
    slug: str
    description: str = ""

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
        if len(v) < 2 or len(v) > 63:
            raise ValueError("Slug must be between 2 and 63 characters")
        return v


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TenantMemberUpdate(BaseModel):
    role: TenantRole


class TenantInvitationCreate(BaseModel):
    email: EmailStr
    role: TenantRole = TenantRole.MEMBER


class AcceptInvitationRequest(BaseModel):
    token: str


# ── Response schemas ─────────────────────────────────────────────────────────

class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    is_active: bool
    owner_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("owner_id")
    def serialize_owner_id(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class TenantMemberResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    role: TenantRole
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "tenant_id", "user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class TenantInvitationResponse(BaseModel):
    id: int
    tenant_id: int
    email: str
    role: TenantRole
    status: InvitationStatus
    invited_by: Optional[int]
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_serializer("id", "tenant_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("invited_by")
    def serialize_invited_by(self, value: Optional[int]) -> Optional[str]:
        return encode_id(value) if value is not None else None


class TenantWithMembersResponse(TenantResponse):
    members: list[TenantMemberResponse] = []
