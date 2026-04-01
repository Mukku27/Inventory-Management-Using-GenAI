"""Audit helpers for AI-assisted inventory operations."""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

AUDIT_LOG_FILENAME = "ai_operation_audit.jsonl"
AUDIT_LOG_WARN_BYTES = 100 * 1024 * 1024  # 100 MB


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return str(value)


def get_audit_log_path(db_path: str | Path) -> Path:
    """Store audit events alongside the active database."""

    return Path(db_path).resolve().with_name(AUDIT_LOG_FILENAME)


def append_audit_event(db_path: str | Path, event_type: str, details: Mapping[str, Any]) -> Path:
    """Append a structured audit event to the JSONL log.

    Emits a :class:`UserWarning` when the log file exceeds
    ``AUDIT_LOG_WARN_BYTES`` (100 MB). The write still succeeds — the warning
    is a safety valve to surface runaway growth before it exhausts disk space.
    Full log rotation is deferred for a future iteration.
    """

    audit_path = get_audit_log_path(db_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    if audit_path.exists():
        file_size = audit_path.stat().st_size
        if file_size >= AUDIT_LOG_WARN_BYTES:
            warnings.warn(
                f"Audit log {audit_path} has reached "
                f"{file_size / (1024 * 1024):.1f} MB. "
                "Consider archiving or rotating it to avoid disk exhaustion.",
                UserWarning,
                stacklevel=2,
            )

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": str(event_type),
        "details": _to_json_safe(dict(details)),
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True))
        handle.write("\n")
    return audit_path
