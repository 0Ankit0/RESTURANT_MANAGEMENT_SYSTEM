from typing import Optional
from sqlmodel import Field, SQLModel


class CasbinRule(SQLModel, table=True):
    """
    Casbin policy rule storage model.

    The adapter persists both permission policies (`ptype="p"`) and role/grouping
    tuples (`ptype="g"`) into the same table. For this project's model:

    - `p` rows map to `(role, domain, resource, action)`
    - `g` rows map to `(user_id, role, domain)`

    Table name must match what `casbin-async-sqlalchemy-adapter` expects.
    """
    __tablename__ = "casbin_rule"  # type: ignore[assignment]

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    ptype: str = Field(
        max_length=255,
        index=True,
        description="Policy type (p for policy, g for grouping/role)"
    )
    v0: str = Field(
        default="",
        max_length=255,
        nullable=True,
        index=True,
        description="p: role name, g: user id"
    )
    v1: str = Field(
        default="",
        max_length=255,
        nullable=True,
        index=True,
        description="p: domain, g: role name"
    )
    v2: str = Field(
        default="",
        max_length=255,
        nullable=True,
        index=True,
        description="p: resource, g: domain"
    )
    v3: str = Field(
        default="",
        max_length=255,
        nullable=True,
        description="p: action, g: unused"
    )
    v4: str = Field(
        default="",
        max_length=255,
        nullable=True,
        description="Unused in the current Casbin model"
    )
    v5: str = Field(
        default="",
        max_length=255,
        nullable=True,
        description="Unused in the current Casbin model"
    )
