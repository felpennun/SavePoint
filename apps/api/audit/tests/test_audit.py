from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.utils import timezone

from audit.models import AuditAction, AuditEvent
from audit.services import record_audit_event


User = get_user_model()


@pytest.mark.django_db
def test_audit_event_is_sanitized_and_keeps_actor_and_operation_reference():
    actor = User.objects.create_user(username="audit-actor", password="password")
    event = record_audit_event(
        actor=actor,
        action=AuditAction.ACCOUNT_ANONYMIZED,
        resource_type="account",
        resource_id=actor.pk,
        result="succeeded",
    )

    assert event.actor_id == actor.pk
    assert event.operation_ref is not None
    assert event.occurred_at <= timezone.now()
    assert not hasattr(event, "payload")


@pytest.mark.django_db
def test_audit_service_rejects_unknown_actions_and_sensitive_identifiers():
    actor = User.objects.create_user(username="audit-validation", password="password")

    with pytest.raises(ValueError):
        record_audit_event(
            actor=actor,
            action="account.changed",
            resource_type="account",
            resource_id=actor.pk,
            result="succeeded",
        )
    with pytest.raises(ValueError):
        record_audit_event(
            actor=actor,
            action=AuditAction.ACCOUNT_ANONYMIZED,
            resource_type="account",
            resource_id="password=leaked",
            result="succeeded",
        )


@pytest.mark.django_db
def test_audit_database_rejects_update_and_delete():
    event = record_audit_event(
        actor=None,
        action=AuditAction.ACCOUNT_DEACTIVATED,
        resource_type="account",
        resource_id="42",
        result="succeeded",
    )

    with pytest.raises(DatabaseError):
        AuditEvent.objects.filter(pk=event.pk).update(result="already_applied")
    with pytest.raises(DatabaseError):
        AuditEvent.objects.filter(pk=event.pk).delete()

