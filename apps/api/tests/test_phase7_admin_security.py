from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client

from evaluation.access import PLATFORM_ADMIN_PERMISSION, RESEARCH_VIEW_PERMISSION, can_manage_platform


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
