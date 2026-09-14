"""Sanitized audit records whose database history cannot be rewritten."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditAction(models.TextChoices):
    ACCOUNT_ANONYMIZED = "account.anonymized", "Account anonymized"
    ACCOUNT_DELETED = "account.deleted", "Account deleted"
    ACCOUNT_DEACTIVATED = "account.deactivated", "Account deactivated"


class AuditResourceType(models.TextChoices):
    ACCOUNT = "account", "Account"
    PROFILE = "profile", "Profile"
    CATALOGUE = "catalogue", "Catalogue"
    IMPORT = "import", "Import"
    JOB = "job", "Job"
    EXPERIMENT = "experiment", "Experiment"


class AuditResult(models.TextChoices):
    SUCCEEDED = "succeeded", "Succeeded"
    ALREADY_APPLIED = "already_applied", "Already applied"


class AuditEvent(models.Model):
    """One immutable event with no free-form payload or personal data."""

    id = models.UUIDField(primary_key=True, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=32, choices=AuditAction.choices)
    resource_type = models.CharField(max_length=16, choices=AuditResourceType.choices)
    resource_id = models.CharField(max_length=64)
    occurred_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=16, choices=AuditResult.choices)
    operation_ref = models.UUIDField(unique=True)

    class Meta:
        ordering = ("occurred_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(action__in=[choice.value for choice in AuditAction]),
                name="audit_action_allowlisted",
            ),
            models.CheckConstraint(
                condition=models.Q(resource_type__in=[choice.value for choice in AuditResourceType]),
                name="audit_resource_type_allowlisted",
            ),
            models.CheckConstraint(
                condition=models.Q(result__in=[choice.value for choice in AuditResult]),
                name="audit_result_allowlisted",
            ),
            models.CheckConstraint(
                condition=models.Q(resource_id__regex=r"^[A-Za-z0-9._:-]{1,64}$"),
                name="audit_resource_id_sanitized",
            ),
        ]

    def save(self, *args, **kwargs):  # noqa: ANN002, ANN003
        if self._state.adding is False:
            raise ValidationError("Audit events are append-only.")
        return super().save(*args, **kwargs)

