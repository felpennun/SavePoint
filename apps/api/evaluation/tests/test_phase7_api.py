from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.core.cache import cache
from rest_framework.test import APIClient

from evaluation.access import PLATFORM_ADMIN_PERMISSION, RESEARCH_VIEW_PERMISSION


User = get_user_model()
COMPARISON_URL = "/api/evaluation/comparison/"
RUNS_URL = "/api/evaluation/runs/"
ARTIFACTS_URL = "/api/evaluation/artifacts/"
EXPORTS_URL = "/api/evaluation/exports/"
RESEARCH_PERMISSION_CODENAME = RESEARCH_VIEW_PERMISSION.split(".", 1)[1]


@pytest.fixture(autouse=True)
def _isolate_research_throttle_state():
    cache.clear()
    yield
    cache.clear()


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
def research_group(db, research_permission):  # noqa: ANN001
    group = Group.objects.create(name="Research Viewer")
    group.permissions.add(research_permission)
    return group


@pytest.fixture
def viewer(db, research_group):  # noqa: ANN001
    user = User.objects.create_user(username="research-viewer", password="test-password")
    user.groups.add(research_group)
    return user


@pytest.fixture
def viewer_client(viewer):  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=viewer)
    return client


@pytest.mark.django_db
def test_viewer_can_read_real_v15_comparison(viewer_client) -> None:  # noqa: ANN001
    response = viewer_client.get(COMPARISON_URL, {"run": "evaluation-400-test-2026-09-12-v15"})

    assert response.status_code == 200, response.content.decode()
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


@pytest.mark.django_db
def test_runs_expose_only_published_filter_options(viewer_client) -> None:  # noqa: ANN001
    response = viewer_client.get(RUNS_URL)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"runs", "algorithms", "cohorts", "metrics", "formats"}
    assert body["runs"][0]["run_id"] == "evaluation-400-test-2026-09-12-v15"
    assert [item["id"] for item in body["formats"]] == ["csv", "json", "svg"]
    assert "per_user" not in response.content.decode()


@pytest.mark.django_db
def test_artifacts_return_sanitized_metadata_and_checksums(viewer_client) -> None:  # noqa: ANN001
    response = viewer_client.get(ARTIFACTS_URL)

    assert response.status_code == 200
    body = response.json()
    assert len(body["artifacts"]) == 3
    for artifact in body["artifacts"]:
        assert set(artifact) == {
            "artifact_id",
            "filename",
            "format",
            "content_type",
            "sha256",
            "published",
        }
        assert artifact["published"] is True
        assert "\\" not in artifact["filename"]
        assert "/" not in artifact["filename"]
    text = response.content.decode()
    assert all(secret not in text.lower() for secret in ("password", "cookie", "token", "per_user"))
    assert "source_paths" not in body


@pytest.mark.parametrize("format_name", ["csv", "json", "svg"])
@pytest.mark.django_db
def test_exports_are_fixed_downloads_from_the_publication(viewer_client, format_name: str) -> None:  # noqa: ANN001
    response = viewer_client.get(
        EXPORTS_URL,
        {
            "format": format_name,
            "algorithm": "random-v1",
            "cohort": "active_history_10_to_20",
            "metric": "ndcg@10",
        },
    )

    assert response.status_code == 200, response.content.decode()
    expected_disposition = f'attachment; filename="evaluation-400-test-2026-09-12-v15.{format_name}"'
    assert response["Content-Disposition"] == expected_disposition
    assert response["X-Content-SHA256"]
    assert response["Cache-Control"] == "private, no-store"
    assert "per_user" not in response.content.decode()


@pytest.mark.django_db
def test_me_exposes_backend_capabilities_without_admin_conflation(viewer_client) -> None:  # noqa: ANN001
    body = viewer_client.get("/api/accounts/me/").json()

    assert body["capabilities"] == {
        "can_view_research": True,
        "can_manage_platform": False,
    }


@pytest.mark.parametrize(
    "url",
    [
        f"{COMPARISON_URL}?unknown=value",
        f"{COMPARISON_URL}?algorithm=random-v1&algorithm=content-cbf-weighted-v1",
        f"{COMPARISON_URL}?algorithm=random-v1__user_id",
        f"{EXPORTS_URL}?format=yaml",
        f"{EXPORTS_URL}?format=json&path=../../secret.txt",
        f"{COMPARISON_URL}?run=evaluation-400-test-2026-09-12-v16",
    ],
)
@pytest.mark.django_db
def test_query_and_export_inputs_fail_closed(viewer_client, url: str) -> None:  # noqa: ANN001
    response = viewer_client.get(url)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid research request."}


@pytest.fixture
def platform_permission(db):  # noqa: ANN001
    app_label, codename = PLATFORM_ADMIN_PERMISSION.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


@pytest.mark.django_db
def test_platform_admin_without_research_viewer_is_still_hidden(platform_permission) -> None:
    user = User.objects.create_user(username="platform-admin", password="test-password")
    user.user_permissions.add(platform_permission)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(COMPARISON_URL)

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


@pytest.mark.django_db
def test_combined_capabilities_are_separate_server_decisions(viewer, platform_permission) -> None:  # noqa: ANN001
    viewer.user_permissions.add(platform_permission)
    client = APIClient()
    client.force_authenticate(user=viewer)

    body = client.get("/api/accounts/me/").json()

    assert body["capabilities"] == {
        "can_view_research": True,
        "can_manage_platform": True,
    }


@pytest.mark.parametrize("path", [RUNS_URL, COMPARISON_URL, ARTIFACTS_URL, EXPORTS_URL])
@pytest.mark.django_db
def test_anonymous_research_requests_require_authentication(path: str) -> None:
    response = APIClient().get(path)

    assert response.status_code in (401, 403)
    assert "run_id" not in response.content.decode()


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.django_db
def test_non_get_methods_are_csrf_protected_and_never_mutate(viewer, method: str) -> None:  # noqa: ANN001
    client = APIClient(enforce_csrf_checks=True)
    assert client.login(username=viewer.username, password="test-password")

    response = client.generic(method, COMPARISON_URL, data="{}", content_type="application/json")

    assert response.status_code == 403
    assert "per_user" not in response.content.decode()


@pytest.mark.django_db
def test_no_rerun_route_is_published(viewer_client) -> None:  # noqa: ANN001
    response = viewer_client.get("/api/evaluation/rerun/")

    assert response.status_code == 404
    assert "runner" not in response.content.decode().lower()


@pytest.mark.django_db
def test_research_scope_throttles_repeated_reads(viewer_client) -> None:  # noqa: ANN001
    statuses = [viewer_client.get(RUNS_URL).status_code for _ in range(61)]

    assert 429 in statuses
    assert set(statuses) <= {200, 429}
