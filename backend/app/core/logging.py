from __future__ import annotations

import json
import logging as std_logging
import re
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


KST = timezone(timedelta(hours=9))
SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|service[_-]?key|servicekey|authorization|access[_-]?token|refresh[_-]?token|token|secret|password)",
    re.IGNORECASE,
)
AUTH_VALUE_PATTERN = re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
RESIDENT_ID_PATTERN = re.compile(r"\b\d{6}-\d{7}\b")
BUSINESS_ID_PATTERN = re.compile(r"\b(\d{3})-?(\d{2})-?(\d{5})\b")
MAX_LOG_STRING_LENGTH = 1200

_CONFIGURED_LOG_DIR: Path | None = None
_PACKAGE_LOGGER = std_logging.getLogger("wisdom_procurement")
_PACKAGE_LOGGER.addHandler(std_logging.NullHandler())
_PACKAGE_LOGGER.propagate = False


class JsonLineFormatter(std_logging.Formatter):
    def format(self, record: std_logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(KST).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.msg if isinstance(record.msg, str) else ""),
            "message": sanitize_log_value(record.getMessage()),
        }
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(sanitize_log_context(context))
        if record.exc_info:
            exc_type, exc_value, _traceback = record.exc_info
            payload["exception_type"] = exc_type.__name__ if exc_type else ""
            payload["exception_message"] = sanitize_log_value(str(exc_value) if exc_value else "")
            payload["stacktrace"] = sanitize_log_value("".join(traceback.format_exception(*record.exc_info)))
        return json.dumps(payload, ensure_ascii=False, default=str)


def new_request_id() -> str:
    return uuid.uuid4().hex


def configure_backend_logging(
    log_dir: str | Path,
    *,
    level: str = "INFO",
    max_mb: int = 20,
    backups: int = 10,
) -> Path:
    target_dir = Path(log_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    root_logger = std_logging.getLogger("wisdom_procurement")
    root_logger.setLevel(_parse_level(level))
    root_logger.handlers.clear()
    root_logger.propagate = False

    formatter = JsonLineFormatter()
    max_bytes = max(1, int(max_mb)) * 1024 * 1024
    backup_count = max(0, int(backups))

    all_handler = RotatingFileHandler(
        target_dir / "backend.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    all_handler.setLevel(_parse_level(level))
    all_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        target_dir / "backend-error.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(std_logging.ERROR)
    error_handler.setFormatter(formatter)

    root_logger.addHandler(all_handler)
    root_logger.addHandler(error_handler)

    global _CONFIGURED_LOG_DIR
    _CONFIGURED_LOG_DIR = target_dir
    return target_dir


def configured_log_dir() -> Path | None:
    return _CONFIGURED_LOG_DIR


def get_logger(name: str) -> std_logging.Logger:
    if name.startswith("wisdom_procurement"):
        return std_logging.getLogger(name)
    return std_logging.getLogger(f"wisdom_procurement.{name}")


def log_event(logger: std_logging.Logger, event: str, *, level: str = "info", **context: Any) -> None:
    log_level = _parse_level(level)
    logger.log(log_level, event, extra={"event": event, "context": sanitize_log_context(context)})


def log_exception(logger: std_logging.Logger, event: str, exc: BaseException, **context: Any) -> None:
    logger.error(
        event,
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"event": event, "context": sanitize_log_context(context)},
    )


def sanitize_log_context(payload: dict[str, Any]) -> dict[str, Any]:
    return {str(key): sanitize_log_value(value, key=str(key)) for key, value in payload.items()}


def sanitize_log_value(value: Any, *, key: str = "") -> Any:
    if _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(child_key): sanitize_log_value(child_value, key=str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_log_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        return _sanitize_string(value)
    return value


def _parse_level(level: str) -> int:
    return getattr(std_logging, (level or "INFO").strip().upper(), std_logging.INFO)


def _is_sensitive_key(key: str) -> bool:
    return bool(key and SENSITIVE_KEY_PATTERN.search(key))


def _sanitize_string(value: str) -> str:
    sanitized = _sanitize_url(value)
    sanitized = AUTH_VALUE_PATTERN.sub(r"\1 [REDACTED]", sanitized)
    sanitized = RESIDENT_ID_PATTERN.sub("[REDACTED_RRN]", sanitized)
    sanitized = BUSINESS_ID_PATTERN.sub(lambda match: f"{match.group(1)}-**-*****", sanitized)
    if len(sanitized) > MAX_LOG_STRING_LENGTH:
        return f"{sanitized[:MAX_LOG_STRING_LENGTH]}...[truncated]"
    return sanitized


def _sanitize_url(value: str) -> str:
    if "?" not in value:
        return value
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if not parsed.query:
        return value
    query = []
    changed = False
    for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
        if _is_sensitive_key(key):
            query.append((key, "[REDACTED]"))
            changed = True
        else:
            query.append((key, item_value))
    if not changed:
        return value
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query, doseq=True), parsed.fragment))
