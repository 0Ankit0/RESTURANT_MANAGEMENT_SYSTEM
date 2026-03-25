from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class GeneralSetting(SQLModel, table=True):
    __tablename__ = "generalsetting"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=255, unique=True, index=True)
    env_value: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    db_value: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    use_db_value: bool = Field(default=False)
    is_runtime_editable: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
