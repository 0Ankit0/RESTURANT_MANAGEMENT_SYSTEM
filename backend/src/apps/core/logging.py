from __future__ import annotations

import logging
import logging.config
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.apps.core.config import settings

_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})
_VALID_LOG_OUTPUTS = frozenset({"console", "database", "web", "file"})


def get_log_context() -> dict[str, Any]:
    return dict(_request_context.get())


def set_log_context(**values: Any) -> None:
    current = get_log_context()
    for key, value in values.items():
        if value is None:
            current.pop(key, None)
        else:
            current[key] = value
    _request_context.set(current)


def clear_log_context() -> None:
    _request_context.set({})


def get_enabled_log_outputs() -> set[str]:
    outputs = {
        str(item).strip().lower()
        for item in settings.LOG_OUTPUTS
        if str(item).strip()
    }
    normalized = {item for item in outputs if item in _VALID_LOG_OUTPUTS}
    if "web" in normalized:
        normalized.add("database")
    if not normalized:
        normalized.add("console")
    return normalized


def log_output_enabled(output: str) -> bool:
    normalized = output.strip().lower()
    outputs = get_enabled_log_outputs()
    return normalized in outputs


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = get_log_context()
        record.request_id = context.get("request_id", "-")
        record.method = context.get("method", "-")
        record.path = context.get("path", "-")
        record.status_code = context.get("status_code", "-")
        record.duration_ms = context.get("duration_ms", "-")
        record.user_id = context.get("user_id", "-")
        record.ip_address = context.get("ip_address", "-")
        record.user_agent = context.get("user_agent", "-")
        return True


class StructuredConsoleFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

    def format(self, record: logging.LogRecord) -> str:
        base = (
            f"{self.formatTime(record)} "
            f"{record.levelname:<8} "
            f"{record.name} "
            f"{record.getMessage()}"
        )
        context = []
        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "ip_address",
        ):
            value = getattr(record, key, "-")
            if value not in {"-", None, ""}:
                context.append(f"{key}={value}")
        if context:
            base = f"{base} | {' '.join(context)}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging() -> None:
    sqlalchemy_level = "INFO" if settings.LOG_SQL_QUERIES else "WARNING"
    outputs = get_enabled_log_outputs()
    handlers: dict[str, dict[str, Any]] = {}
    active_handlers: list[str] = []

    if "console" in outputs:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "structured",
            "filters": ["request_context"],
        }
        active_handlers.append("console")

    if "file" in outputs:
        log_file_path = Path(settings.LOG_FILE_PATH)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": settings.LOG_LEVEL,
            "filename": str(log_file_path),
            "encoding": "utf-8",
            "formatter": "structured",
            "filters": ["request_context"],
        }
        active_handlers.append("file")

    if not active_handlers:
        handlers["null"] = {
            "class": "logging.NullHandler",
        }
        active_handlers.append("null")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {
                    "()": "src.apps.core.logging.RequestContextFilter",
                }
            },
            "formatters": {
                "structured": {
                    "()": "src.apps.core.logging.StructuredConsoleFormatter",
                }
            },
            "handlers": {
                **handlers
            },
            "root": {
                "handlers": active_handlers,
                "level": settings.LOG_LEVEL,
            },
            "loggers": {
                "uvicorn": {"level": settings.LOG_LEVEL, "handlers": active_handlers, "propagate": False},
                "uvicorn.error": {"level": settings.LOG_LEVEL, "handlers": active_handlers, "propagate": False},
                "uvicorn.access": {"level": settings.LOG_LEVEL, "handlers": active_handlers, "propagate": False},
                "fastapi": {"level": settings.LOG_LEVEL, "handlers": active_handlers, "propagate": False},
                "sqlalchemy.engine": {"level": sqlalchemy_level, "handlers": active_handlers, "propagate": False},
            },
        }
    )
