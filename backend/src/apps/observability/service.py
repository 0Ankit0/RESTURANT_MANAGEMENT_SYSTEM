from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from src.apps.core.config import settings
from src.apps.core.logging import get_log_context, log_output_enabled, set_log_context
from src.apps.iam.models.login_attempt import LoginAttempt
from src.apps.observability.models import ObservabilityLogEntry, SecurityIncident

log = logging.getLogger(__name__)

INCIDENT_ACTIVE_STATUSES = ("open", "acknowledged")
LEVEL_ORDER = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def failed_login_window() -> timedelta:
    return timedelta(minutes=settings.FAILED_LOGIN_BURST_WINDOW_MINUTES)


def token_churn_window() -> timedelta:
    return timedelta(minutes=settings.TOKEN_CHURN_WINDOW_MINUTES)


def rate_limit_spike_window() -> timedelta:
    return timedelta(minutes=settings.RATE_LIMIT_SPIKE_WINDOW_MINUTES)


def error_spike_window() -> timedelta:
    return timedelta(minutes=settings.ERROR_SPIKE_WINDOW_MINUTES)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_request_log_context(request: Request) -> dict[str, Any]:
    return {
        "request_id": request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12],
        "method": request.method,
        "path": request.url.path,
        "ip_address": request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "").strip()
        or (request.client.host if request.client else "unknown"),
        "user_agent": request.headers.get("user-agent", "unknown"),
    }


def _coerce_user_id(value: Any) -> int | None:
    if value in (None, "", "-", "anonymous"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_log_entry(
    *,
    level: str,
    logger_name: str,
    source: str,
    message: str,
    event_code: str = "",
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
    status_code: int | None = None,
    duration_ms: int | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    path: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
) -> ObservabilityLogEntry:
    context = get_log_context()
    if request is not None:
        context = {**context, **build_request_log_context(request)}
    entry = ObservabilityLogEntry(
        level=level.upper(),
        logger_name=logger_name,
        source=source,
        message=message,
        event_code=event_code,
        request_id=request_id or str(context.get("request_id", "")),
        method=method or str(context.get("method", "")),
        path=path or str(context.get("path", "")),
        status_code=status_code if status_code is not None else context.get("status_code"),
        duration_ms=duration_ms if duration_ms is not None else context.get("duration_ms"),
        user_id=user_id if user_id is not None else _coerce_user_id(context.get("user_id")),
        ip_address=ip_address or str(context.get("ip_address", "")),
        user_agent=user_agent or str(context.get("user_agent", "")),
        metadata_json=metadata or {},
    )
    return entry


async def create_log_entry(
    db: AsyncSession,
    *,
    level: str,
    logger_name: str,
    source: str,
    message: str,
    event_code: str = "",
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
    status_code: int | None = None,
    duration_ms: int | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    path: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
    flush: bool = True,
) -> ObservabilityLogEntry:
    level_name = level.upper()
    logging.getLogger(logger_name).log(
        getattr(logging, level_name, logging.INFO),
        message,
    )
    entry = _build_log_entry(
        level=level_name,
        logger_name=logger_name,
        source=source,
        message=message,
        event_code=event_code,
        metadata=metadata,
        request=request,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        path=path,
        method=method,
        request_id=request_id,
    )
    persist_level = LEVEL_ORDER.get(settings.LOG_PERSIST_MIN_LEVEL.upper(), logging.INFO)
    if not log_output_enabled("database"):
        return entry
    if LEVEL_ORDER.get(level_name, logging.INFO) < persist_level:
        return entry
    db.add(entry)
    if flush:
        await db.flush()
    return entry


async def prune_old_log_entries(db: AsyncSession) -> int:
    cutoff = utc_now() - timedelta(days=settings.LOG_RETENTION_DAYS)
    stale_logs = (
        await db.execute(
            select(ObservabilityLogEntry).where(ObservabilityLogEntry.timestamp < cutoff)
        )
    ).scalars().all()
    for entry in stale_logs:
        await db.delete(entry)
    return len(stale_logs)


async def create_or_update_incident(
    db: AsyncSession,
    *,
    signal_type: str,
    severity: str,
    title: str,
    summary: str,
    fingerprint: str,
    actor_user_id: int | None = None,
    subject_user_id: int | None = None,
    ip_address: str | None = None,
    related_log_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> SecurityIncident:
    now = utc_now()
    result = await db.execute(
        select(SecurityIncident).where(
            SecurityIncident.fingerprint == fingerprint,
            col(SecurityIncident.status).in_(INCIDENT_ACTIVE_STATUSES),
        )
    )
    incident = result.scalars().first()
    if incident:
        incident.occurrence_count += 1
        incident.last_seen_at = now
        incident.summary = summary
        incident.related_log_id = related_log_id or incident.related_log_id
        if metadata:
            incident.metadata_json = {**incident.metadata_json, **metadata}
        if actor_user_id is not None:
            incident.actor_user_id = actor_user_id
        if subject_user_id is not None:
            incident.subject_user_id = subject_user_id
        if ip_address:
            incident.ip_address = ip_address
        return incident

    incident = SecurityIncident(
        signal_type=signal_type,
        severity=severity,
        title=title,
        summary=summary,
        fingerprint=fingerprint,
        actor_user_id=actor_user_id,
        subject_user_id=subject_user_id,
        ip_address=ip_address or "",
        related_log_id=related_log_id,
        metadata_json=metadata or {},
    )
    db.add(incident)
    await db.flush()
    return incident


async def record_failed_login_event(
    db: AsyncSession,
    *,
    username: str,
    ip_address: str,
    failure_reason: str,
    request: Request,
    subject_user_id: int | None = None,
) -> ObservabilityLogEntry:
    entry = await create_log_entry(
        db,
        level="WARNING",
        logger_name="auth.login",
        source="auth",
        message=f"Failed login for {username}",
        event_code="auth.login_failed",
        metadata={"username": username, "failure_reason": failure_reason},
        request=request,
        user_id=subject_user_id,
        ip_address=ip_address,
    )
    await evaluate_failed_login_burst(
        db,
        username=username,
        ip_address=ip_address,
        subject_user_id=subject_user_id,
        related_log_id=entry.id,
    )
    return entry


async def evaluate_failed_login_burst(
    db: AsyncSession,
    *,
    username: str,
    ip_address: str,
    subject_user_id: int | None,
    related_log_id: int | None,
) -> None:
    window_start = utc_now() - failed_login_window()
    username_count = (
        await db.execute(
            select(func.count(col(LoginAttempt.id))).where(
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.timestamp >= window_start,
                LoginAttempt.attempted_username == username,
            )
        )
    ).scalar_one()
    ip_count = (
        await db.execute(
            select(func.count(col(LoginAttempt.id))).where(
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.timestamp >= window_start,
                LoginAttempt.ip_address == ip_address,
            )
        )
    ).scalar_one()
    threshold = settings.FAILED_LOGIN_BURST_THRESHOLD
    if username_count >= threshold:
        await create_or_update_incident(
            db,
            signal_type="auth.failed_login_burst",
            severity="high",
            title="Repeated failed logins for username",
            summary=(
                f"{username_count} failed login attempts for {username} "
                f"in {settings.FAILED_LOGIN_BURST_WINDOW_MINUTES} minutes."
            ),
            fingerprint=f"auth.failed_login_burst:username:{username}",
            subject_user_id=subject_user_id,
            ip_address=ip_address,
            related_log_id=related_log_id,
            metadata={"username": username, "attempt_count": username_count},
        )
    if ip_count >= threshold:
        await create_or_update_incident(
            db,
            signal_type="auth.failed_login_burst",
            severity="high",
            title="Repeated failed logins from IP",
            summary=(
                f"{ip_count} failed login attempts from {ip_address} "
                f"in {settings.FAILED_LOGIN_BURST_WINDOW_MINUTES} minutes."
            ),
            fingerprint=f"auth.failed_login_burst:ip:{ip_address}",
            subject_user_id=subject_user_id,
            ip_address=ip_address,
            related_log_id=related_log_id,
            metadata={"username": username, "attempt_count": ip_count},
        )


async def record_successful_login_event(
    db: AsyncSession,
    *,
    user_id: int,
    ip_address: str,
    request: Request,
    method: str,
) -> ObservabilityLogEntry:
    entry = await create_log_entry(
        db,
        level="INFO",
        logger_name="auth.login",
        source="auth",
        message=f"Successful {method} login",
        event_code="auth.login_success",
        metadata={"auth_method": method},
        request=request,
        user_id=user_id,
        ip_address=ip_address,
    )
    await evaluate_new_ip_login(
        db,
        user_id=user_id,
        ip_address=ip_address,
        related_log_id=entry.id,
    )
    return entry


async def evaluate_new_ip_login(
    db: AsyncSession,
    *,
    user_id: int,
    ip_address: str,
    related_log_id: int | None,
) -> None:
    prior_other_ip = (
        await db.execute(
            select(func.count(col(LoginAttempt.id))).where(
                LoginAttempt.user_id == user_id,
                LoginAttempt.success == True,  # noqa: E712
                LoginAttempt.ip_address != ip_address,
            )
        )
    ).scalar_one()
    current_ip_successes = (
        await db.execute(
            select(func.count(col(LoginAttempt.id))).where(
                LoginAttempt.user_id == user_id,
                LoginAttempt.success == True,  # noqa: E712
                LoginAttempt.ip_address == ip_address,
            )
        )
    ).scalar_one()
    if prior_other_ip > 0 and current_ip_successes == 1:
        await create_or_update_incident(
            db,
            signal_type="auth.new_ip_login",
            severity="medium",
            title="Login from a new IP address",
            summary=f"User {user_id} successfully logged in from a new IP: {ip_address}.",
            fingerprint=f"auth.new_ip_login:{user_id}:{ip_address}",
            subject_user_id=user_id,
            ip_address=ip_address,
            related_log_id=related_log_id,
            metadata={"user_id": user_id},
        )


async def record_token_event(
    db: AsyncSession,
    *,
    user_id: int,
    ip_address: str,
    action: str,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> ObservabilityLogEntry:
    event_code = "auth.token_issued" if action == "issued" else "auth.token_revoked"
    entry = await create_log_entry(
        db,
        level="INFO" if action == "issued" else "WARNING",
        logger_name="auth.tokens",
        source="auth",
        message=f"Token {action}",
        event_code=event_code,
        metadata=metadata,
        request=request,
        user_id=user_id,
        ip_address=ip_address,
    )
    await evaluate_token_churn(
        db,
        user_id=user_id,
        ip_address=ip_address,
        related_log_id=entry.id,
    )
    return entry


async def evaluate_token_churn(
    db: AsyncSession,
    *,
    user_id: int,
    ip_address: str,
    related_log_id: int | None,
) -> None:
    window_start = utc_now() - token_churn_window()
    churn_count = (
        await db.execute(
            select(func.count(col(ObservabilityLogEntry.id))).where(
                ObservabilityLogEntry.user_id == user_id,
                ObservabilityLogEntry.ip_address == ip_address,
                col(ObservabilityLogEntry.event_code).in_(("auth.token_issued", "auth.token_revoked")),
                ObservabilityLogEntry.timestamp >= window_start,
            )
        )
    ).scalar_one()
    if churn_count >= settings.TOKEN_CHURN_THRESHOLD:
        await create_or_update_incident(
            db,
            signal_type="auth.token_churn",
            severity="medium",
            title="High token churn detected",
            summary=(
                f"{churn_count} token lifecycle events were recorded for user "
                f"{user_id} from {ip_address} in {settings.TOKEN_CHURN_WINDOW_MINUTES} minutes."
            ),
            fingerprint=f"auth.token_churn:{user_id}:{ip_address}",
            subject_user_id=user_id,
            ip_address=ip_address,
            related_log_id=related_log_id,
            metadata={"count": churn_count},
        )


async def record_admin_privilege_change(
    db: AsyncSession,
    *,
    actor_user_id: int,
    subject_user_id: int,
    changes: dict[str, Any],
    request: Request | None = None,
) -> ObservabilityLogEntry:
    entry = await create_log_entry(
        db,
        level="WARNING",
        logger_name="admin.users",
        source="admin",
        message="Admin privilege change applied",
        event_code="admin.privilege_change",
        metadata=changes,
        request=request,
        user_id=actor_user_id,
        ip_address=get_log_context().get("ip_address", ""),
    )
    severity = "high" if "is_superuser" in changes else "medium"
    await create_or_update_incident(
        db,
        signal_type="admin.privilege_change",
        severity=severity,
        title="Sensitive user privilege change",
        summary=f"Admin {actor_user_id} changed account privileges for user {subject_user_id}.",
        fingerprint=f"admin.privilege_change:{subject_user_id}:{sorted(changes.keys())}",
        actor_user_id=actor_user_id,
        subject_user_id=subject_user_id,
        ip_address=entry.ip_address,
        related_log_id=entry.id,
        metadata=changes,
    )
    return entry


async def record_admin_role_change(
    db: AsyncSession,
    *,
    actor_user_id: int,
    subject_user_id: int | None,
    action: str,
    metadata: dict[str, Any],
    request: Request | None = None,
) -> ObservabilityLogEntry:
    entry = await create_log_entry(
        db,
        level="WARNING",
        logger_name="admin.rbac",
        source="admin",
        message=f"RBAC {action}",
        event_code="admin.role_change",
        metadata={"action": action, **metadata},
        request=request,
        user_id=actor_user_id,
    )
    await create_or_update_incident(
        db,
        signal_type="admin.role_change",
        severity="medium",
        title="RBAC configuration changed",
        summary=f"Admin {actor_user_id} performed {action}.",
        fingerprint=f"admin.role_change:{action}:{metadata}",
        actor_user_id=actor_user_id,
        subject_user_id=subject_user_id,
        ip_address=entry.ip_address,
        related_log_id=entry.id,
        metadata=metadata,
    )
    return entry


async def record_rate_limit_event(
    db: AsyncSession,
    *,
    request: Request,
    detail: str,
) -> ObservabilityLogEntry:
    entry = await create_log_entry(
        db,
        level="WARNING",
        logger_name="api.rate_limit",
        source="ops",
        message="Rate limit exceeded",
        event_code="ops.rate_limit_hit",
        metadata={"detail": detail},
        request=request,
        status_code=429,
        path=request.url.path,
    )
    await evaluate_rate_limit_spike(
        db,
        path=request.url.path,
        ip_address=entry.ip_address,
        related_log_id=entry.id,
    )
    return entry


async def evaluate_rate_limit_spike(
    db: AsyncSession,
    *,
    path: str,
    ip_address: str,
    related_log_id: int | None,
) -> None:
    window_start = utc_now() - rate_limit_spike_window()
    hit_count = (
        await db.execute(
            select(func.count(col(ObservabilityLogEntry.id))).where(
                ObservabilityLogEntry.event_code == "ops.rate_limit_hit",
                ObservabilityLogEntry.path == path,
                ObservabilityLogEntry.ip_address == ip_address,
                ObservabilityLogEntry.timestamp >= window_start,
            )
        )
    ).scalar_one()
    if hit_count >= settings.RATE_LIMIT_SPIKE_THRESHOLD:
        await create_or_update_incident(
            db,
            signal_type="ops.rate_limit_spike",
            severity="medium",
            title="Rate limit spike detected",
            summary=(
                f"{hit_count} rate limit hits were recorded for {path} from "
                f"{ip_address} in {settings.RATE_LIMIT_SPIKE_WINDOW_MINUTES} minutes."
            ),
            fingerprint=f"ops.rate_limit_spike:{path}:{ip_address}",
            ip_address=ip_address,
            related_log_id=related_log_id,
            metadata={"path": path, "count": hit_count},
        )


async def record_request_completion(
    db: AsyncSession,
    *,
    request: Request,
    status_code: int,
    duration_ms: int,
    message: str | None = None,
) -> ObservabilityLogEntry:
    level = "INFO"
    event_code = "http.request.completed"
    source = "api"
    if status_code >= 500:
        level = "ERROR"
        event_code = "ops.request_error"
    elif status_code >= 400:
        level = "WARNING"
        event_code = "http.request.client_error"
    entry = await create_log_entry(
        db,
        level=level,
        logger_name="api.requests",
        source=source,
        message=message or f"{request.method} {request.url.path} -> {status_code}",
        event_code=event_code,
        request=request,
        status_code=status_code,
        duration_ms=duration_ms,
    )
    if status_code >= 500:
        await evaluate_error_spike(
            db,
            path=request.url.path,
            related_log_id=entry.id,
            status_code=status_code,
        )
    return entry


async def evaluate_error_spike(
    db: AsyncSession,
    *,
    path: str,
    related_log_id: int | None,
    status_code: int,
) -> None:
    window_start = utc_now() - error_spike_window()
    error_count = (
        await db.execute(
            select(func.count(col(ObservabilityLogEntry.id))).where(
                ObservabilityLogEntry.event_code == "ops.request_error",
                ObservabilityLogEntry.path == path,
                ObservabilityLogEntry.timestamp >= window_start,
            )
        )
    ).scalar_one()
    if error_count >= settings.ERROR_SPIKE_THRESHOLD:
        await create_or_update_incident(
            db,
            signal_type="ops.error_spike",
            severity="high",
            title="Repeated 5xx responses detected",
            summary=(
                f"{error_count} server errors were recorded for {path} "
                f"in {settings.ERROR_SPIKE_WINDOW_MINUTES} minutes."
            ),
            fingerprint=f"ops.error_spike:{path}",
            related_log_id=related_log_id,
            metadata={"path": path, "status_code": status_code, "count": error_count},
        )


async def build_log_summary(db: AsyncSession) -> dict[str, int]:
    window_start = utc_now() - timedelta(hours=24)
    total_logs = (
        await db.execute(
            select(func.count(col(ObservabilityLogEntry.id))).where(
                ObservabilityLogEntry.timestamp >= window_start
            )
        )
    ).scalar_one()

    def _count_level(level: str) -> Any:
        return select(func.count(col(ObservabilityLogEntry.id))).where(
            ObservabilityLogEntry.timestamp >= window_start,
            ObservabilityLogEntry.level == level,
        )

    info_logs = (await db.execute(_count_level("INFO"))).scalar_one()
    warning_logs = (await db.execute(_count_level("WARNING"))).scalar_one()
    error_logs = (await db.execute(_count_level("ERROR"))).scalar_one()
    open_incidents = (
        await db.execute(
            select(func.count(col(SecurityIncident.id))).where(SecurityIncident.status == "open")
        )
    ).scalar_one()
    acknowledged_incidents = (
        await db.execute(
            select(func.count(col(SecurityIncident.id))).where(SecurityIncident.status == "acknowledged")
        )
    ).scalar_one()
    critical_incidents = (
        await db.execute(
            select(func.count(col(SecurityIncident.id))).where(
                col(SecurityIncident.status).in_(INCIDENT_ACTIVE_STATUSES),
                SecurityIncident.severity == "high",
            )
        )
    ).scalar_one()
    return {
        "total_logs_24h": total_logs,
        "info_logs_24h": info_logs,
        "warning_logs_24h": warning_logs,
        "error_logs_24h": error_logs,
        "open_incidents": open_incidents,
        "acknowledged_incidents": acknowledged_incidents,
        "critical_incidents": critical_incidents,
    }


def sync_request_context_from_request(request: Request) -> None:
    set_log_context(**build_request_log_context(request))
