from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import Client

from accounts.services import (
    IRREVERSIBLE_DELETE_CONFIRMATION,
    anonymize_account,
    delete_account_irreversibly,
)
from accounts.models import AccountProfile
from audit.models import AuditEvent
from evaluation.access import PLATFORM_ADMIN_PERMISSION, RESEARCH_VIEW_PERMISSION, can_manage_platform
from platform_admin.admin_site import platform_admin_site


User = get_user_model()


def _permission(qualified_name: str) -> Permission:
    app_label, codename = qualified_name.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


@pytest.mark.django_db
def test_platform_admin_site_uses_distinct_capability_not_staff_or_name():
    admin_user = User.objects.create_user(username="not-staff-admin", password="password")
    platform_group = Group.objects.create(name="Platform Admin")
    platform_group.permissions.add(_permission(PLATFORM_ADMIN_PERMISSION))
    admin_user.groups.add(platform_group)
    assert admin_user.is_staff is False
    assert can_manage_platform(admin_user) is True

    viewer = User.objects.create_user(username="viewer", password="password", is_staff=True)
    viewer_group = Group.objects.create(name="Research Viewer")
    viewer_group.permissions.add(_permission(RESEARCH_VIEW_PERMISSION))
    viewer.groups.add(viewer_group)

    admin_client = Client()
    admin_client.force_login(admin_user)
    viewer_client = Client()
    viewer_client.force_login(viewer)

    admin_response = admin_client.get("/admin/")
    viewer_response = viewer_client.get("/admin/")

    assert admin_response.status_code == 200
    assert viewer_response.status_code == 302
    assert "/admin/login/" in viewer_response["Location"]


@pytest.mark.django_db
def test_accounts_get_no_phase7_groups_without_explicit_provisioning():
    demo = User.objects.create_user(username="demo-without-role", password="password")
    registered = User.objects.create_user(username="registered-without-role", password="password")

    assert list(demo.groups.values_list("name", flat=True)) == []
    assert list(registered.groups.values_list("name", flat=True)) == []


@pytest.mark.django_db
def test_explicit_uuid_role_bootstrap_is_idempotent_and_separate():
    user = User.objects.create_user(username="explicit-role-target", password="password")
    profile = AccountProfile.objects.get_or_create(user=user)[0]
    explicit_uuid = uuid.uuid4()
    profile.admin_uuid = explicit_uuid
    profile.save(update_fields=["admin_uuid"])

    call_command("bootstrap_phase7_roles", platform_admin_user_id=str(explicit_uuid))
    call_command("bootstrap_phase7_roles", user_id=str(explicit_uuid), group="Research Viewer")
    call_command("bootstrap_phase7_roles", user_id=str(explicit_uuid), group="Platform Admin")

    user.refresh_from_db()
    assert set(user.groups.values_list("name", flat=True)) == {"Platform Admin", "Research Viewer"}
    assert can_manage_platform(user) is True
    assert user.has_perm(RESEARCH_VIEW_PERMISSION) is True
    assert user.has_perm("evaluation.export_research_panel") is True


@pytest.mark.django_db
def test_anonymization_is_idempotent_and_audited_without_personal_data():
    actor = User.objects.create_superuser(username="privacy-admin", password="password")
    target = User.objects.create_user(
        username="real-alias", password="password", email="person@example.test", first_name="Person"
    )
    profile = AccountProfile.objects.get_or_create(user=target)[0]
    profile.bio = "Private bio"
    profile.avatar_url = "https://example.test/avatar.png"
    profile.save()

    anonymize_account(actor=actor, target_user=target, operation_ref="00000000-0000-0000-0000-000000000101")
    anonymize_account(actor=actor, target_user=target, operation_ref="00000000-0000-0000-0000-000000000102")

    target.refresh_from_db()
    target.profile.refresh_from_db()
    assert target.is_active is False
    assert target.username.startswith("anonymous-")
    assert target.email == ""
    assert target.profile.is_anonymized is True
    assert target.profile.bio == ""
    assert target.profile.avatar_url == ""
    assert AuditEvent.objects.filter(resource_id=str(target.pk)).count() == 2
    assert "person@example.test" not in str(
        AuditEvent.objects.filter(resource_id=str(target.pk)).values()
    )


@pytest.mark.django_db
def test_irreversible_delete_requires_superuser_confirmation_and_audits_first():
    editor = User.objects.create_user(username="ordinary-editor", password="password")
    target = User.objects.create_user(username="delete-target", password="password")

    with pytest.raises(PermissionDenied):
        delete_account_irreversibly(
            actor=editor,
            target_user=target,
            confirmation=IRREVERSIBLE_DELETE_CONFIRMATION,
        )

    superuser = User.objects.create_superuser(username="delete-superuser", password="password")
    with pytest.raises(ValidationError):
        delete_account_irreversibly(actor=superuser, target_user=target, confirmation="DELETE")

    target_id = target.pk
    delete_account_irreversibly(
        actor=superuser,
        target_user=target,
        confirmation=IRREVERSIBLE_DELETE_CONFIRMATION,
        operation_ref="00000000-0000-0000-0000-000000000202",
    )
    assert not User.objects.filter(pk=target_id).exists()
    assert AuditEvent.objects.filter(resource_id=str(target_id), action="account.deleted").exists()


@pytest.mark.django_db
def test_admin_privacy_endpoint_requires_post_and_csrf():
    admin_user = User.objects.create_superuser(username="admin-privacy", password="password")
    profile = AccountProfile.objects.get_or_create(
        user=User.objects.create_user(username="admin-target", password="password")
    )[0]
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin_user)

    get_response = client.get(f"/admin/accounts/accountprofile/{profile.pk}/anonymize/")
    post_response = client.post(f"/admin/accounts/accountprofile/{profile.pk}/anonymize/")

    assert get_response.status_code == 405
    assert post_response.status_code == 403


@pytest.mark.django_db
def test_platform_admin_registry_is_allowlisted_and_operational_data_is_readonly():
    registered_models = {model._meta.label for model in platform_admin_site._registry}
    assert "auth.User" in registered_models
    assert "accounts.AccountProfile" in registered_models
    assert "catalogue.GameWork" in registered_models
    assert "catalogue.IgdbImportRun" in registered_models
    assert "recommendations.RecommendationRefreshJob" in registered_models
    assert "audit.AuditEvent" in registered_models
    assert all(
        "rerun" not in model_admin.__class__.__name__.lower()
        for model_admin in platform_admin_site._registry.values()
    )

    audit_admin = platform_admin_site._registry[AuditEvent]
    assert audit_admin.has_add_permission(None) is False
    assert audit_admin.has_change_permission(None) is False
    assert audit_admin.has_delete_permission(None) is False
