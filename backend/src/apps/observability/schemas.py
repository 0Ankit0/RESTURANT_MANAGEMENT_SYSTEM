from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_serializer

from src.apps.iam.utils.hashid import encode_id


class _HashIdModel(BaseModel):
    @field_serializer(
        "id",
        "user_id",
        "actor_user_id",
        "subject_user_id",
        "reviewed_by",
        "related_log_id",
        check_fields=False,
    )
    def serialize_ids(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class ObservabilityLogEntryRead(_HashIdModel):
    id: int
    timestamp: datetime
    level: str
    logger_name: str
    source: str
    message: str
    event_code: str
    request_id: str
    method: str
    path: str
    status_code: int | None
    duration_ms: int | None
    user_id: int | None
    ip_address: str
    user_agent: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")

    model_config = {"from_attributes": True}


class ObservabilityLogSummary(BaseModel):
    total_logs_24h: int
    info_logs_24h: int
    warning_logs_24h: int
    error_logs_24h: int
    open_incidents: int
    acknowledged_incidents: int
    critical_incidents: int


class SecurityIncidentRead(_HashIdModel):
    id: int
    signal_type: str
    severity: str
    status: str
    title: str
    summary: str
    fingerprint: str
    occurrence_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    actor_user_id: int | None
    subject_user_id: int | None
    ip_address: str
    related_log_id: int | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    review_notes: str
    reviewed_by: int | None
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class SecurityIncidentUpdate(BaseModel):
    status: str
    review_notes: str | None = None
