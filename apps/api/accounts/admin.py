"""Capability-gated account administration and privacy operations."""

from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import path

from accounts.models import AccountProfile
from accounts.services import (
    IRREVERSIBLE_DELETE_CONFIRMATION,
    anonymize_account,
    delete_account_irreversibly,
)


User = get_user_model()


class PlatformModelAdmin(admin.ModelAdmin):
    """Make model access depend on the enclosing capability-gated site."""

    def has_module_permission(self, request) -> bool:  # noqa: ANN001
        return bool(self.admin_site.has_permission(request))

    def has_view_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return bool(self.admin_site.has_permission(request))

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


class PlatformUserAdmin(PlatformModelAdmin):
    list_display = ("username", "is_active", "is_superuser", "date_joined")
    list_filter = ("is_active", "is_superuser")
    search_fields = ("username",)
    fields = ("username", "first_name", "last_name", "email", "is_active", "is_superuser", "date_joined")
    readonly_fields = ("date_joined",)


class AccountProfileAdmin(PlatformModelAdmin):
    list_display = ("user", "admin_uuid", "is_anonymized", "anonymized_at", "updated_at")
    list_filter = ("is_anonymized",)
    search_fields = ("user__username", "admin_uuid")
    readonly_fields = ("admin_uuid", "is_anonymized", "anonymized_at", "created_at", "updated_at")
    fields = (
        "user",
        "admin_uuid",
        "bio",
        "avatar_url",
        "collection_visibility",
        "favorites_visibility",
        "is_anonymized",
        "anonymized_at",
        "created_at",
        "updated_at",
    )
    actions = ("anonymize_selected",)

    def get_urls(self):  # noqa: ANN201
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/anonymize/",
                self.admin_site.admin_view(self.anonymize_view),
                name="accounts_accountprofile_anonymize",
            ),
            path(
                "<path:object_id>/delete-account/",
                self.admin_site.admin_view(self.delete_account_view),
                name="accounts_accountprofile_delete_account",
            ),
        ]
        return custom_urls + urls

    def anonymize_selected(self, request, queryset) -> None:  # noqa: ANN001
        for profile in queryset.select_related("user"):
            anonymize_account(actor=request.user, target_user=profile.user)
        self.message_user(request, "Selected accounts were anonymized.", messages.SUCCESS)

    anonymize_selected.short_description = "Anonymize selected accounts"

    def anonymize_view(self, request, object_id: str):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        profile = get_object_or_404(AccountProfile.objects.select_related("user"), pk=object_id)
        anonymize_account(actor=request.user, target_user=profile.user)
        self.message_user(request, "Account anonymized.", messages.SUCCESS)
        return redirect("admin:accounts_accountprofile_changelist")

    def delete_account_view(self, request, object_id: str):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        profile = get_object_or_404(AccountProfile.objects.select_related("user"), pk=object_id)
        try:
            delete_account_irreversibly(
                actor=request.user,
                target_user=profile.user,
                confirmation=request.POST.get("confirmation", ""),
            )
        except (PermissionDenied, ValidationError) as exc:
            self.message_user(request, str(exc), messages.ERROR)
            return redirect("admin:accounts_accountprofile_change", object_id)
        self.message_user(request, "Account permanently deleted.", messages.SUCCESS)
        return redirect("admin:accounts_accountprofile_changelist")


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    site.register(User, PlatformUserAdmin)
    site.register(AccountProfile, AccountProfileAdmin)
