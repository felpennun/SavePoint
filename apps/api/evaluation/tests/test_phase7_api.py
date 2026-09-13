from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from evaluation.access import RESEARCH_VIEW_PERMISSION


User = get_user_model()
COMPARISON_URL = "/api/evaluation/comparison/"
RESEARCH_PERMISSION_CODENAME = RESEARCH_VIEW_PERMISSION.split(".", 1)[1]


@pytest.fixture
def research_permission(db):  # noqa: ANN001
    content_type, _ = ContentType.objects.get_or_create(
        app_label="evaluation",
        model="publication",
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=RESEARCH_PERMISSION_CODENAME,
        defaults={"name": "Can view the research panel"},
    )
    return permission


@pytest.fixture
def viewer(db, research_permission):  # noqa: ANN001
    user = User.objects.create_user(username="research-viewer", password="test-password")
    user.user_permissions.add(research_permission)
    return user


@pytest.fixture
def viewer_client(viewer):  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=viewer)
    return client


@pytest.mark.django_db
def test_viewer_can_read_real_v15_comparison(viewer_client) -> None:  # noqa: ANN001
    response = viewer_client.get(COMPARISON_URL, {"run": "evaluation-400-test-2026-09-12-v15"})

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["protocol_version"] == 15
    assert body["rows"]
    assert body["metric_definitions"]
    assert body["timings"]
    assert body["provenance"]["corpus_version"] == "2026.09.2"
    assert body["limitations"]
    assert "per_user" not in response.content.decode()
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_authenticated_user_without_research_permission_gets_neutral_404(db) -> None:
    user = User.objects.create_user(username="ordinary-user", password="test-password")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(COMPARISON_URL)

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
    assert "research" not in response.content.decode().lower()
