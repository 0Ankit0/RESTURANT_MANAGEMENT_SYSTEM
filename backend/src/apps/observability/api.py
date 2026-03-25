from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, desc, func, select

from src.apps.core.schemas import PaginatedResponse
from src.apps.iam.api.deps import get_current_active_superuser, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.observability.models import ObservabilityLogEntry, SecurityIncident
from src.apps.observability.schemas import (
    ObservabilityLogEntryRead,
    ObservabilityLogSummary,
    SecurityIncidentRead,
    SecurityIncidentUpdate,
)
from src.apps.observability.service import build_log_summary

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/logs", response_model=PaginatedResponse[ObservabilityLogEntryRead])
async def list_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
    search: str | None = Query(default=None),
    event_code: str | None = Query(default=None),
    route: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    log_id: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ObservabilityLogEntryRead]:
    del current_user
    query = select(ObservabilityLogEntry)
    count_query = select(func.count(col(ObservabilityLogEntry.id)))

    if level:
        query = query.where(ObservabilityLogEntry.level == level.upper())
        count_query = count_query.where(ObservabilityLogEntry.level == level.upper())
    if source:
        query = query.where(ObservabilityLogEntry.source == source)
        count_query = count_query.where(ObservabilityLogEntry.source == source)
    if event_code:
        query = query.where(ObservabilityLogEntry.event_code == event_code)
        count_query = count_query.where(ObservabilityLogEntry.event_code == event_code)
    if route:
        query = query.where(ObservabilityLogEntry.path == route)
        count_query = count_query.where(ObservabilityLogEntry.path == route)
    if request_id:
        query = query.where(ObservabilityLogEntry.request_id == request_id)
        count_query = count_query.where(ObservabilityLogEntry.request_id == request_id)
    if user_id:
        uid = decode_id_or_404(user_id)
        query = query.where(ObservabilityLogEntry.user_id == uid)
        count_query = count_query.where(ObservabilityLogEntry.user_id == uid)
    if log_id:
        lid = decode_id_or_404(log_id)
        query = query.where(ObservabilityLogEntry.id == lid)
        count_query = count_query.where(ObservabilityLogEntry.id == lid)
    if start_at:
        query = query.where(ObservabilityLogEntry.timestamp >= start_at)
        count_query = count_query.where(ObservabilityLogEntry.timestamp >= start_at)
    if end_at:
        query = query.where(ObservabilityLogEntry.timestamp <= end_at)
        count_query = count_query.where(ObservabilityLogEntry.timestamp <= end_at)
    if search:
        search_like = f"%{search}%"
        search_filter = or_(
            col(ObservabilityLogEntry.message).ilike(search_like),
            col(ObservabilityLogEntry.logger_name).ilike(search_like),
            col(ObservabilityLogEntry.ip_address).ilike(search_like),
            col(ObservabilityLogEntry.path).ilike(search_like),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    items = (
        await db.execute(query.order_by(desc(col(ObservabilityLogEntry.timestamp))).offset(skip).limit(limit))
    ).scalars().all()
    return PaginatedResponse[ObservabilityLogEntryRead].create(
        items=[ObservabilityLogEntryRead.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/logs/live", response_model=list[ObservabilityLogEntryRead])
async def list_live_logs(
    after_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    source: str | None = Query(default=None),
    level: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> list[ObservabilityLogEntryRead]:
    del current_user
    query = select(ObservabilityLogEntry)
    if after_id:
        query = query.where(col(ObservabilityLogEntry.id) > decode_id_or_404(after_id))
    if source:
        query = query.where(ObservabilityLogEntry.source == source)
    if level:
        query = query.where(ObservabilityLogEntry.level == level.upper())
    items = (
        await db.execute(query.order_by(col(ObservabilityLogEntry.id)).limit(limit))
    ).scalars().all()
    return [ObservabilityLogEntryRead.model_validate(item) for item in items]


@router.get("/logs/summary", response_model=ObservabilityLogSummary)
async def get_log_summary(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> ObservabilityLogSummary:
    del current_user
    return ObservabilityLogSummary(**(await build_log_summary(db)))


@router.get("/incidents", response_model=PaginatedResponse[SecurityIncidentRead])
async def list_incidents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    signal_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SecurityIncidentRead]:
    del current_user
    query = select(SecurityIncident)
    count_query = select(func.count(col(SecurityIncident.id)))
    if status_filter:
        query = query.where(SecurityIncident.status == status_filter)
        count_query = count_query.where(SecurityIncident.status == status_filter)
    if severity:
        query = query.where(SecurityIncident.severity == severity)
        count_query = count_query.where(SecurityIncident.severity == severity)
    if signal_type:
        query = query.where(SecurityIncident.signal_type == signal_type)
        count_query = count_query.where(SecurityIncident.signal_type == signal_type)
    if search:
        search_like = f"%{search}%"
        search_filter = or_(
            col(SecurityIncident.title).ilike(search_like),
            col(SecurityIncident.summary).ilike(search_like),
            col(SecurityIncident.ip_address).ilike(search_like),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    total = (await db.execute(count_query)).scalar_one()
    items = (
        await db.execute(query.order_by(desc(col(SecurityIncident.last_seen_at))).offset(skip).limit(limit))
    ).scalars().all()
    return PaginatedResponse[SecurityIncidentRead].create(
        items=[SecurityIncidentRead.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=SecurityIncidentRead)
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> SecurityIncidentRead:
    del current_user
    iid = decode_id_or_404(incident_id)
    incident = await db.get(SecurityIncident, iid)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return SecurityIncidentRead.model_validate(incident)


@router.patch("/incidents/{incident_id}", response_model=SecurityIncidentRead)
async def update_incident(
    incident_id: str,
    payload: SecurityIncidentUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> SecurityIncidentRead:
    iid = decode_id_or_404(incident_id)
    incident = await db.get(SecurityIncident, iid)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if payload.status not in {"acknowledged", "resolved"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status transition")
    incident.status = payload.status
    if payload.review_notes is not None:
        incident.review_notes = payload.review_notes
    incident.reviewed_by = current_user.id
    incident.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(incident)
    return SecurityIncidentRead.model_validate(incident)
