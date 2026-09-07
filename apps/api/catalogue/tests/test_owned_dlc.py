"""Tests for ``OwnedGamesDlcView`` -- the owner-scoped "Para tus juegos"
shelf (Plan 02-05 Task 2, D-15, threat T-02-05-01).

The endpoint is ``IsAuthenticated`` and derives everything from
``request.user``: it accepts no target-user parameter, returns the DLC /
expansions of base games in the caller's library grouped by base game, and
returns those child works even when they sit outside the governed corpus.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import GameWork, RelatedContent
from library.models import LibraryEntry

pytestmark = pytest.mark.django_db

User = get_user_model()

_ENDPOINT = "/api/catalogue/owned-dlc/"


def _work(slug: str, *, is_dlc: bool = False, in_corpus: bool = True) -> GameWork:
    return GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        title_en=slug.replace("-", " ").title(),
        is_dlc=is_dlc,
        in_corpus=in_corpus,
        corpus_version="2026.09.1" if in_corpus else "",
    )


def _dlc_of(parent: GameWork, child: GameWork, relation: str = "dlc") -> RelatedContent:
    return RelatedContent.objects.create(
        parent_work=parent, child_work=child, relation=relation
    )


@pytest.fixture
def user_a():
    return User.objects.create_user(username="dlc-user-a", password="Dlc-User-A-Pass-9!")


@pytest.fixture
def user_b():
    return User.objects.create_user(username="dlc-user-b", password="Dlc-User-B-Pass-9!")


def test_requires_authentication() -> None:
    response = APIClient().get(_ENDPOINT)
    assert response.status_code == 403


def test_returns_dlc_of_owned_base_games_grouped_by_base(user_a) -> None:
    base = _work("owned-base")
    dlc_one = _work("owned-base-dlc-1", is_dlc=True)
    dlc_two = _work("owned-base-expansion", is_dlc=True)
    _dlc_of(base, dlc_one, "dlc")
    _dlc_of(base, dlc_two, "expansion")
    LibraryEntry.objects.create(user=user_a, work=base, current_status="playing")

    client = APIClient()
    client.force_authenticate(user=user_a)
    body = client.get(_ENDPOINT).json()

    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["base_game"] == {"slug": "owned-base", "title": "Owned Base"}
    child_slugs = {item["slug"] for item in group["dlc"]}
    assert child_slugs == {"owned-base-dlc-1", "owned-base-expansion"}
    # Allowlist-echo item projection -- identity + cover only.
    assert set(group["dlc"][0].keys()) == {"work_id", "slug", "title", "cover", "relation"}


def test_dlc_of_unowned_base_game_is_absent(user_a) -> None:
    owned = _work("mine")
    not_owned = _work("not-mine")
    _dlc_of(owned, _work("mine-dlc", is_dlc=True))
    _dlc_of(not_owned, _work("not-mine-dlc", is_dlc=True))
    LibraryEntry.objects.create(user=user_a, work=owned, current_status="completed")

    client = APIClient()
    client.force_authenticate(user=user_a)
    body = client.get(_ENDPOINT).json()

    all_child_slugs = {
        item["slug"] for group in body["groups"] for item in group["dlc"]
    }
    assert all_child_slugs == {"mine-dlc"}


def test_child_work_outside_governed_corpus_is_still_returned(user_a) -> None:
    base = _work("governed-base")
    ungoverned_dlc = _work("ungoverned-dlc", is_dlc=True, in_corpus=False)
    _dlc_of(base, ungoverned_dlc)
    LibraryEntry.objects.create(user=user_a, work=base, current_status="playing")

    client = APIClient()
    client.force_authenticate(user=user_a)
    body = client.get(_ENDPOINT).json()

    child_slugs = {item["slug"] for group in body["groups"] for item in group["dlc"]}
    assert "ungoverned-dlc" in child_slugs


def test_user_without_dlc_gets_empty_groups(user_a) -> None:
    LibraryEntry.objects.create(
        user=user_a, work=_work("plain-game"), current_status="playing"
    )

    client = APIClient()
    client.force_authenticate(user=user_a)
    response = client.get(_ENDPOINT)

    assert response.status_code == 200
    assert response.json() == {"groups": []}


def test_target_user_query_param_is_ignored(user_a, user_b) -> None:
    a_base = _work("a-base")
    _dlc_of(a_base, _work("a-base-dlc", is_dlc=True))
    LibraryEntry.objects.create(user=user_a, work=a_base, current_status="playing")

    # user_b owns nothing; asking for user_a's id must not leak user_a's DLC.
    client = APIClient()
    client.force_authenticate(user=user_b)
    body = client.get(_ENDPOINT, {"user": str(user_a.id)}).json()

    assert body == {"groups": []}
