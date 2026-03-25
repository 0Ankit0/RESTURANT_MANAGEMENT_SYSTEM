from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_serializer
from src.apps.iam.utils.hashid import encode_id


# ── Request schemas ──────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str
    description: str = ""


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionCreate(BaseModel):
    resource: str
    action: str
    description: str = ""


class RoleAssignment(BaseModel):
    """user_id and role_id are encoded hashids supplied by the client."""
    user_id: str
    role_id: str


class PermissionAssignment(BaseModel):
    """role_id and permission_id are encoded hashids supplied by the client."""
    role_id: str
    permission_id: str


class CheckPermissionRequest(BaseModel):
    resource: str
    action: str


# ── Response schemas ─────────────────────────────────────────────────────────

class PermissionResponse(BaseModel):
    id: int
    resource: str
    action: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)


class UserRoleResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    assigned_at: datetime
    role: RoleResponse

    model_config = {"from_attributes": True}

    @field_serializer("id", "user_id", "role_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class RolePermissionResponse(BaseModel):
    id: int
    role_id: int
    permission_id: int
    granted_at: datetime
    permission: PermissionResponse

    model_config = {"from_attributes": True}

    @field_serializer("id", "role_id", "permission_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class CheckPermissionResponse(BaseModel):
    user_id: int
    resource: str
    action: str
    allowed: bool

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)


class UserRolesResponse(BaseModel):
    user_id: int
    roles: list[RoleResponse]

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)


class RolePermissionsResponse(BaseModel):
    role_id: int
    permissions: list[PermissionResponse]

    @field_serializer("role_id")
    def serialize_role_id(self, value: int) -> str:
        return encode_id(value)


class RoleAssignmentResponse(BaseModel):
    message: str
    user_role_id: int

    @field_serializer("user_role_id")
    def serialize_user_role_id(self, value: int) -> str:
        return encode_id(value)


class PermissionAssignmentResponse(BaseModel):
    message: str
    role_permission_id: int

    @field_serializer("role_permission_id")
    def serialize_role_permission_id(self, value: int) -> str:
        return encode_id(value)


class CasbinRolesResponse(BaseModel):
    user_id: int
    domain: str
    roles: list[str]

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)


class CasbinPermissionsResponse(BaseModel):
    user_id: int
    domain: str
    permissions: list[list[str]]

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)
