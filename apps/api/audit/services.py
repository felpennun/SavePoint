"""Single writer for sanitized audit events."""

from __future__ import annotations

import re
import uuid

from audit.models import AuditAction, AuditEvent, AuditResourceType, AuditResult


_SAFE_RESOURCE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_FORBIDDEN_TERMS = (
    "password",
    "passwd",
    "token",
    "cookie",
    "secret",
    "connection",
    "credential",
    "payload",
    "email",
)


def _safe_resource_id(resource_id: str | int | uuid.UUID) -> str:
    value = str(resource_id)
    lowered = value.lower()
    if any(term in lowered for term in _FORBIDDEN_TERMS) or not _SAFE_RESOURCE_ID.fullmatch(value):
        raise ValueError("Audit resource identifiers must be opaque and sanitized.")
    return value


def record_audit_event(
    *,
    actor,
    action: str,
    resource_type: str,
    resource_id: str | int | uuid.UUID,
    result: str,
    operation_ref: str | uuid.UUID | None = None,
) -> AuditEvent:
    """Append one allowlisted event without accepting arbitrary metadata."""

    if action not in AuditAction.values:
        raise ValueError("Audit action is not allowlisted.")
    if resource_type not in AuditResourceType.values:
        raise ValueError("Audit resource type is not allowlisted.")
    if result not in AuditResult.values:
        raise ValueError("Audit result is not allowlisted.")
    if actor is not None and not getattr(actor, "is_authenticated", False):
        raise ValueError("Audit actor must be an authenticated user or None.")
    try:
        operation_uuid = uuid.UUID(str(operation_ref)) if operation_ref is not None else uuid.uuid4()
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("Audit operation reference must be a UUID.") from exc

    return AuditEvent.objects.create(
        id=uuid.uuid4(),
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=_safe_resource_id(resource_id),
        result=result,
        operation_ref=operation_uuid,
    )

