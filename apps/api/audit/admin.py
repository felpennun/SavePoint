"""Read-only audit projection; all writes use the audit service."""

from django.contrib import admin

from audit.models import AuditEvent
from accounts.admin import PlatformModelAdmin


class AuditEventAdmin(PlatformModelAdmin):
    list_display = ("occurred_at", "action", "resource_type", "resource_id", "result", "operation_ref")
    list_filter = ("action", "resource_type", "result")
    search_fields = ("resource_id", "operation_ref")
    fields = ("id", "actor", "action", "resource_type", "resource_id", "occurred_at", "result", "operation_ref")
    readonly_fields = fields

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    site.register(AuditEvent, AuditEventAdmin)
