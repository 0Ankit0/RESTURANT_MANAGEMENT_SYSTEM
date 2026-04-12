from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RbacBootstrapState(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    version: str = Field(default="v1", max_length=64)
    bootstrapped_at: datetime = Field(default_factory=datetime.now, index=True)
    actor_user_id: int = Field(index=True)
    applied: bool = Field(default=False)
    run_count: int = Field(default=0, ge=0)
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))
