"""Structured operation events with a deliberately tiny safe surface."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("savepoint.operations")

OPERATION_STATUSES = frozenset({"queued", "running", "succeeded", "failed"})
OPERATION_TYPES = frozenset({"collection_import", "backup", "restore", "recommendation_job"})
RESOURCE_TYPES = frozenset({"collection_import", "backup", "restore", "recommendation_job"})
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
_SAFE_ACTOR = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class SensitiveOperationData(ValueError):
    """Raised when an operational identifier is not safe to log."""


def _safe_identifier(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise SensitiveOperationData(f"{field} is not a safe operational identifier")
    return value


def redact_public_error(error: BaseException | str | None) -> str | None:
    """Map arbitrary failures to a public code and never retain their text."""
    if error is None:
        return None
    return "operation_failed"


def build_operation_event(
    *,
    operation_ref: str | uuid.UUID,
    actor: str,
    operation_type: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None = None,
    resource_type: str,
    resource_id: str,
    duration_ms: int | None = None,
    error: BaseException | str | None = None,
) -> dict[str, Any]:
    """Build one JSON-safe event from explicit, non-sensitive fields only."""
    try:
        operation_uuid = uuid.UUID(str(operation_ref))
    except (ValueError, AttributeError, TypeError) as exc:
        raise SensitiveOperationData("operation_ref must be a UUID") from exc
    if not _SAFE_ACTOR.fullmatch(actor or ""):
        raise SensitiveOperationData("actor must be a technical identifier")
    if operation_type not in OPERATION_TYPES or status not in OPERATION_STATUSES:
        raise SensitiveOperationData("operation type or status is not allowlisted")
    if resource_type not in RESOURCE_TYPES:
        raise SensitiveOperationData("resource type is not allowlisted")
    safe_resource_id = _safe_identifier(resource_id, field="resource_id")
    if started_at.tzinfo is None:
        raise SensitiveOperationData("started_at must be timezone-aware")
    if finished_at is not None and finished_at.tzinfo is None:
        raise SensitiveOperationData("finished_at must be timezone-aware")
    if duration_ms is not None and (isinstance(duration_ms, bool) or not 0 <= duration_ms <= 86_400_000):
        raise SensitiveOperationData("duration_ms is outside the supported range")
    event: dict[str, Any] = {
        "operation_ref": str(operation_uuid),
        "actor": actor,
        "operation_type": operation_type,
        "status": status,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "resource_type": resource_type,
        "resource_id": safe_resource_id,
    }
    if finished_at is not None:
        event["finished_at"] = finished_at.astimezone(timezone.utc).isoformat()
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    public_error = redact_public_error(error)
    if public_error is not None:
        event["error_code"] = public_error
    return event


def emit_operation_event(**kwargs: Any) -> dict[str, Any]:
    """Build and emit one allowlisted event; return the exact emitted DTO."""
    event = build_operation_event(**kwargs)
    logger.info(json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return event
