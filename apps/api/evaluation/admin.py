"""Allowlisted, read-only research publication admin entry."""

from django.contrib import admin

from evaluation.models import ResearchPublication


class ResearchPublicationAdmin(admin.ModelAdmin):
    list_display = ("id",)
    readonly_fields = ("id",)

    def has_module_permission(self, request) -> bool:  # noqa: ANN001
        return bool(getattr(request.user, "is_authenticated", False))

    def has_view_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return bool(getattr(request.user, "is_authenticated", False))

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    site.register(ResearchPublication, ResearchPublicationAdmin)

