from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

from .user import User


class RoleBase(SQLModel):
    name: str = Field(
        unique=True,
        index=True,
        max_length=50,
        description="Unique role name"
    )
    description: str = Field(
        default="",
        max_length=255,
        description="Role description"
    )


class Role(RoleBase, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the role was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the role was last updated"
    )
    
    # Relationships
    user_roles: list["UserRole"] = Relationship(back_populates="role")
    role_permissions: list["RolePermission"] = Relationship(back_populates="role")


class PermissionBase(SQLModel):
    resource: str = Field(
        max_length=100,
        index=True,
        description="Resource identifier (e.g., 'users', 'posts', 'settings')"
    )
    action: str = Field(
        max_length=50,
        index=True,
        description="Action allowed on resource (e.g., 'read', 'write', 'delete')"
    )
    description: str = Field(
        default="",
        max_length=255,
        description="Permission description"
    )


class Permission(PermissionBase, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the permission was created"
    )
    
    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")


class UserRole(SQLModel, table=True):
    """Association table for User-Role many-to-many relationship"""
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    user_id: int = Field(
        foreign_key="user.id",
        index=True,
        description="User ID"
    )
    role_id: int = Field(
        foreign_key="role.id",
        index=True,
        description="Role ID"
    )
    assigned_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the role was assigned to the user"
    )
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="user_roles")
    role: Optional[Role] = Relationship(back_populates="user_roles")


class RolePermission(SQLModel, table=True):
    """Association table for Role-Permission many-to-many relationship"""
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    role_id: int = Field(
        foreign_key="role.id",
        index=True,
        description="Role ID"
    )
    permission_id: int = Field(
        foreign_key="permission.id",
        index=True,
        description="Permission ID"
    )
    granted_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the permission was granted to the role"
    )
    
    # Relationships
    role: Optional[Role] = Relationship(back_populates="role_permissions")
    permission: Optional[Permission] = Relationship(back_populates="role_permissions")
