"""Allowlisted library projections for controlled demo operations."""

from django.contrib import admin

from accounts.admin import PlatformModelAdmin
from library.models import CustomList, GameComment, LibraryEntry, OwnedCopy, StatusTransition, CustomListItem


class LibraryEntryAdmin(PlatformModelAdmin):
    list_display = ("user", "work", "current_status", "rating_half_steps", "updated_at")
    list_filter = ("current_status",)
    search_fields = ("user__username", "work__original_title")
    fields = ("user", "work", "current_status", "rating_half_steps", "is_platinum", "updated_at")
    readonly_fields = ("updated_at",)


class OwnedCopyAdmin(PlatformModelAdmin):
    list_display = ("user", "work", "format", "release", "created_at")
    list_filter = ("format", "conservation_state")
    search_fields = ("user__username", "work__original_title", "store")
    fields = (
        "user", "work", "release", "edition", "format", "idempotency_key", "purchase_date",
        "price", "currency", "store", "conservation_state", "storage_location", "created_at",
    )
    readonly_fields = ("created_at",)


class GameCommentAdmin(PlatformModelAdmin):
    list_display = ("user", "work", "visibility", "created_at", "updated_at")
    list_filter = ("visibility",)
    search_fields = ("user__username", "work__original_title", "text")
    fields = ("user", "work", "text", "visibility", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


class CustomListAdmin(PlatformModelAdmin):
    list_display = ("user", "name", "visibility", "version", "updated_at")
    list_filter = ("visibility",)
    search_fields = ("user__username", "name")
    fields = ("user", "name", "public_slug", "visibility", "version", "created_at", "updated_at")
    readonly_fields = ("public_slug", "created_at", "updated_at")


class ReadOnlyLibraryAdmin(PlatformModelAdmin):
    def get_readonly_fields(self, request, obj=None):  # noqa: ANN001, ARG002
        return tuple(field.name for field in self.model._meta.concrete_fields)

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


class StatusTransitionAdmin(ReadOnlyLibraryAdmin):
    list_display = ("entry", "from_status", "to_status", "changed_at")
    fields = ("id", "entry", "from_status", "to_status", "changed_at")


class CustomListItemAdmin(ReadOnlyLibraryAdmin):
    list_display = ("list", "work", "position", "created_at")
    fields = ("id", "list", "work", "position", "created_at")


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    for model, model_admin in (
        (LibraryEntry, LibraryEntryAdmin),
        (OwnedCopy, OwnedCopyAdmin),
        (GameComment, GameCommentAdmin),
        (CustomList, CustomListAdmin),
        (StatusTransition, StatusTransitionAdmin),
        (CustomListItem, CustomListItemAdmin),
    ):
        site.register(model, model_admin)
