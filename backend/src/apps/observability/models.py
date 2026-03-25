from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ObservabilityLogEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=utc_now, index=True)
    level: str = Field(max_length=16, index=True)
    logger_name: str = Field(max_length=255, index=True)
    source: str = Field(max_length=64, index=True)
    message: str = Field(max_length=1024)
    event_code: str = Field(default="", max_length=128, index=True)
    request_id: str = Field(default="", max_length=64, index=True)
    method: str = Field(default="", max_length=16, index=True)
    path: str = Field(default="", max_length=255, index=True)
    status_code: int | None = Field(default=None, index=True)
    duration_ms: int | None = Field(default=None)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    ip_address: str = Field(default="", max_length=45, index=True)
    user_agent: str = Field(default="", max_length=255)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))


class SecurityIncident(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    signal_type: str = Field(max_length=128, index=True)
    severity: str = Field(max_length=16, index=True)
    status: str = Field(default="open", max_length=16, index=True)
    title: str = Field(max_length=255)
    summary: str = Field(max_length=1024)
    fingerprint: str = Field(max_length=255, index=True)
    occurrence_count: int = Field(default=1)
    first_seen_at: datetime = Field(default_factory=utc_now, index=True)
    last_seen_at: datetime = Field(default_factory=utc_now, index=True)
    actor_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    subject_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    ip_address: str = Field(default="", max_length=45, index=True)
    related_log_id: int | None = Field(default=None, foreign_key="observabilitylogentry.id", index=True)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    review_notes: str = Field(default="", max_length=2048)
    reviewed_by: int | None = Field(default=None, foreign_key="user.id", index=True)
    reviewed_at: datetime | None = Field(default=None)
