"""Tests for content feature vectors, the user profile, and the
``WorkFeatureVector`` cache (Plan 02-10 Task 3, REC-03 / D-11 / D-12).

Pure Python + stdlib (Task 1 ``checkpoint:decision`` = ``pure-python``).
The feature vector is a sparse ``{feature_key: weight}`` dict with ``tag:``
(guaranteed) and ``platform:`` (allowlist only) facets; ``franchise:`` /
``developer:`` is emitted only when measured coverage over the governed view
clears a documented threshold (D-11); ``franchise:`` represents IGDB saga and
is emitted whenever observed. The rating term is NEVER a vector
dimension -- it lives in ``combine.py`` (Plan 02-11), fed from
``CorpusRatingSnapshot``.
"""

from __future__ import annotations

import math

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from catalogue.models import (
    CorpusRatingSnapshot,
    CuratedLabel,
    Developer,
    Franchise,
    GameRelease,
    GameWork,
    GameWorkCuratedLabel,
    Platform,
)
from library.models import LibraryEntry
from recommendations.content.features import (
    FACET_WEIGHTS,
    FEATURE_SET_VERSION,
    coverage_report,
    feature_vector,
    tag_rating_profile,
)
from recommendations.content.profile import build_profile, build_profile_inputs
from recommendations.models import WorkFeatureVector

User = get_user_model()

_CORPUS = "test-corpus"


# --------------------------------------------------------------------------- #
# Fixtures / helpers                                                           #
# --------------------------------------------------------------------------- #
@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="cbf-user-a", password="Cbf-User-A-Pass-9!")


@pytest.fixture
def genres(db):  # noqa: ANN001
    # Named "genres" for call-site continuity (genres["rpg"] etc.), but these
    # are CuratedLabel rows -- feature_vector/tag_rating_profile/tag_idf all
    # read work.curated_labels exclusively now, never the legacy Genre M2M
    # (2026-09-12: fixed test/production drift found live via duplicated UI
    # tags -- see ideas-vault "Evidencia UI-E2E ... QUAL-02").
    return {
        "rpg": CuratedLabel.objects.create(name="Role-playing (RPG)", slug="role-playing-rpg", kind=CuratedLabel.Kind.GENRE, curation_version="test"),
        "shooter": CuratedLabel.objects.create(name="Shooter", slug="shooter", kind=CuratedLabel.Kind.GENRE, curation_version="test"),
        "puzzle": CuratedLabel.objects.create(name="Puzzle", slug="puzzle", kind=CuratedLabel.Kind.GENRE, curation_version="test"),
    }


def _work(slug: str, *tags: CuratedLabel, governed: bool = True) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        is_dlc=False,
        in_corpus=governed,
        corpus_version=_CORPUS if governed else "",
    )
    for tag in tags:
        GameWorkCuratedLabel.objects.create(
            work=work, label=tag, source_kind="genre", source_value=tag.name
        )
    return work


def _release_on(work: GameWork, platform: Platform) -> GameRelease:
    return GameRelease.objects.create(
        work=work, platform=platform, release_name=f"{work.canonical_slug} ({platform.slug})"
    )


def _own(user, work, *, status="completed", rating=None):  # noqa: ANN001
    return LibraryEntry.objects.create(
        user=user, work=work, current_status=status, rating_half_steps=rating
    )


# --------------------------------------------------------------------------- #
# feature_vector                                                               #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_feature_vector_is_a_sparse_dict_with_no_rating_dimension(user_a, genres) -> None:  # noqa: ANN001
    work = _work("three-genre-rpg", genres["rpg"], genres["shooter"], genres["puzzle"])

    vector = feature_vector(work)

    assert set(vector) == {
        "tag:role-playing-rpg",
        "tag:shooter",
        "tag:puzzle",
    }
    assert all(weight > 0 for weight in vector.values())
    assert not any(key.startswith("rating") for key in vector)


@pytest.mark.django_db
def test_genre_weights_use_the_family_weight_over_sqrt_k(user_a, genres) -> None:  # noqa: ANN001
    work = _work("three-genre-rpg", genres["rpg"], genres["shooter"], genres["puzzle"])

    vector = feature_vector(work)

    expected = FACET_WEIGHTS["tag"] / math.sqrt(3)
    assert all(value == pytest.approx(expected) for value in vector.values())


@pytest.mark.django_db
def test_only_allowlisted_platforms_become_features(user_a, genres) -> None:  # noqa: ANN001
    allowed = Platform.objects.create(name="Windows", slug="pc-microsoft-windows")
    forbidden = Platform.objects.create(name="Fuchsia Handheld", slug="not-on-the-allowlist")
    work = _work("multi-platform-rpg", genres["rpg"])
    _release_on(work, allowed)
    _release_on(work, forbidden)

    vector = feature_vector(work)

    assert "platform:pc-microsoft-windows" in vector
    assert "platform:not-on-the-allowlist" not in vector
    assert not any(k.startswith("platform:") and "not-on-the-allowlist" in k for k in vector)


@pytest.mark.django_db
def test_franchise_and_developer_features_are_gated_off_without_coverage(user_a, genres) -> None:  # noqa: ANN001
    work = _work("no-franchise-data", genres["rpg"])

    # Even asked for explicitly, there is no franchise/developer data this
    # phase, so nothing is emitted (D-11).
    vector = feature_vector(work, include_franchise=True, include_developer=True)

    assert not any(k.startswith("franchise:") for k in vector)
    assert not any(k.startswith("developer:") for k in vector)


@pytest.mark.django_db
def test_coverage_report_decides_inclusion_from_measured_coverage(genres) -> None:  # noqa: ANN001
    for idx in range(4):
        _work(f"gov-{idx}", genres["rpg"])

    report = coverage_report(_CORPUS)

    assert report["governed_count"] == 4
    assert report["franchise_coverage"] == 0.0
    assert report["developer_coverage"] == 0.0
    assert report["include_franchise"] is False
    assert report["include_developer"] is False
    assert report["franchise_threshold"] == 0.0


@pytest.mark.django_db
def test_sparse_franchise_coverage_still_activates_the_saga_signal(genres) -> None:  # noqa: ANN001
    franchise = Franchise.objects.create(igdb_id=333, name="Sparse Saga", slug="sparse-saga")
    work = _work("sparse-franchise", genres["rpg"])
    work.franchises.add(franchise)
    _work("without-franchise", genres["rpg"])

    report = coverage_report(_CORPUS)

    assert report["franchise_coverage"] == pytest.approx(0.5)
    assert report["include_franchise"] is True
    assert feature_vector(work, include_franchise=True)["franchise:sparse-saga"] == pytest.approx(
        FACET_WEIGHTS["franchise"]
    )


@pytest.mark.django_db
def test_franchise_and_developer_features_activate_only_above_measured_coverage(genres) -> None:  # noqa: ANN001
    franchise = Franchise.objects.create(igdb_id=111, name="Quest Saga", slug="quest-saga")
    developer = Developer.objects.create(igdb_id=222, name="Quest Studio", slug="quest-studio")
    works = [_work(f"facet-{idx}", genres["rpg"]) for idx in range(4)]
    for work in works[:2]:
        work.franchises.add(franchise)
        work.developers.add(developer)

    report = coverage_report(_CORPUS)
    assert report["include_franchise"] is True
    assert report["include_developer"] is True

    vector = feature_vector(works[0], include_franchise=True, include_developer=True)
    assert vector["tag:role-playing-rpg"] == pytest.approx(FACET_WEIGHTS["tag"])
    assert vector["franchise:quest-saga"] == pytest.approx(FACET_WEIGHTS["franchise"])
    assert vector["developer:quest-studio"] == pytest.approx(FACET_WEIGHTS["developer"])


@pytest.mark.django_db
def test_platform_weight_is_lower_than_genre_and_higher_than_optional_facets(genres) -> None:  # noqa: ANN001
    platform = Platform.objects.create(name="Windows", slug="pc-microsoft-windows")
    work = _work("weighted-platform", genres["rpg"])
    _release_on(work, platform)

    vector = feature_vector(work)

    assert vector["tag:role-playing-rpg"] == pytest.approx(FACET_WEIGHTS["tag"])
    assert vector["platform:pc-microsoft-windows"] == pytest.approx(FACET_WEIGHTS["platform"])
    assert FACET_WEIGHTS == {
        "tag": 0.60,
        "theme": 0.20,
        "feature": 0.10,
        "mode": 0.05,
        "platform": 0.05,
        "franchise": 0.02,
        "developer": 0.015,
    }
    assert FACET_WEIGHTS["platform"] > FACET_WEIGHTS["franchise"] > FACET_WEIGHTS["developer"]


# --------------------------------------------------------------------------- #
# tag_rating_profile (corpus statistic, snapshot-derived)                      #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_tag_rating_profile_is_the_mean_snapshot_rating_per_tag(genres) -> None:  # noqa: ANN001
    from django.utils import timezone

    w1 = _work("rated-a", genres["rpg"])
    w2 = _work("rated-b", genres["rpg"])
    for work, rating in ((w1, 80.0), (w2, 90.0)):
        CorpusRatingSnapshot.objects.create(
            work=work, corpus_version=_CORPUS, source="igdb",
            rating=rating, rating_count=100, retrieved_at=timezone.now(),
        )

    profile = tag_rating_profile(_CORPUS)

    assert profile["role-playing-rpg"] == pytest.approx(85.0)


# --------------------------------------------------------------------------- #
# build_profile                                                                #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_profile_of_a_monogenre_library_is_dominated_by_that_genre(user_a, genres) -> None:  # noqa: ANN001
    for idx in range(3):
        _own(user_a, _work(f"owned-rpg-{idx}", genres["rpg"]), status="completed", rating=10)

    profile = build_profile(user_a, _CORPUS)

    assert set(profile) == {"tag:role-playing-rpg"}
    assert profile["tag:role-playing-rpg"] == pytest.approx(1.0)


@pytest.mark.django_db
def test_profile_uses_positive_rated_completed_and_playing_entries(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _own(user_a, _work("owned-shooter", genres["shooter"]), status="playing", rating=8)
    _own(user_a, _work("pending-puzzle", genres["puzzle"]), status="pending", rating=10)

    profile = build_profile(user_a, _CORPUS)

    assert profile["tag:role-playing-rpg"] > profile["tag:shooter"]
    assert profile["tag:role-playing-rpg"] == pytest.approx(4.0 / 6.64)
    assert profile["tag:shooter"] == pytest.approx(2.64 / 6.64)


@pytest.mark.django_db
def test_profile_records_own_seed_ratings_as_preference_intensity(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("rated-rpg", genres["rpg"]), status="completed", rating=10)
    _own(user_a, _work("rated-shooter", genres["shooter"]), status="completed", rating=7)

    inputs = build_profile_inputs(user_a, _CORPUS)

    assert inputs.positive_entry_count == 2
    assert inputs.positive_rating_sum_half_steps == 17
    assert inputs.as_dict()["positive_rating_mean_half_steps"] == pytest.approx(8.5)
    assert inputs.as_dict()["own_rating_role"] == "seed_preference_intensity"


@pytest.mark.django_db
def test_profile_is_empty_for_a_user_with_no_genre_bearing_history(user_a) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-no-genre"), status="completed", rating=10)

    assert build_profile(user_a, _CORPUS) == {}


@pytest.mark.django_db
def test_profile_is_empty_for_a_user_with_no_library(user_a) -> None:  # noqa: ANN001
    assert build_profile(user_a, _CORPUS) == {}


@pytest.mark.django_db
def test_profile_prefers_the_cached_work_feature_vector(user_a, genres) -> None:  # noqa: ANN001
    work = _work("owned-rpg", genres["rpg"])
    _own(user_a, work, status="completed", rating=10)
    # Cache says this work is pure shooter -- build_profile must use it.
    WorkFeatureVector.objects.create(
        work=work, feature_set_version=FEATURE_SET_VERSION, vector_json={"tag:shooter": 1.0}
    )

    profile = build_profile(user_a, _CORPUS)

    assert set(profile) == {"tag:shooter"}


# --------------------------------------------------------------------------- #
# WorkFeatureVector + rebuild_feature_vectors                                  #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_rebuild_feature_vectors_populates_every_governed_work(genres) -> None:  # noqa: ANN001
    governed = [_work(f"gov-{idx}", genres["rpg"]) for idx in range(5)]
    _work("ungoverned", genres["rpg"], governed=False)

    call_command("rebuild_feature_vectors", "--corpus-version", _CORPUS)

    assert WorkFeatureVector.objects.count() == 5
    for work in governed:
        row = WorkFeatureVector.objects.get(work=work, feature_set_version=FEATURE_SET_VERSION)
        assert row.vector_json == {
            "tag:role-playing-rpg": pytest.approx(FACET_WEIGHTS["tag"])
        }


@pytest.mark.django_db
def test_rebuild_feature_vectors_is_idempotent(genres) -> None:  # noqa: ANN001
    for idx in range(3):
        _work(f"gov-{idx}", genres["rpg"])

    call_command("rebuild_feature_vectors", "--corpus-version", _CORPUS)
    first = {row.work_id: row.vector_json for row in WorkFeatureVector.objects.all()}
    call_command("rebuild_feature_vectors", "--corpus-version", _CORPUS)
    second = {row.work_id: row.vector_json for row in WorkFeatureVector.objects.all()}

    assert WorkFeatureVector.objects.count() == 3
    assert first == second


@pytest.mark.django_db
def test_work_feature_vector_is_unique_per_work_and_feature_set(genres) -> None:  # noqa: ANN001
    from django.db import IntegrityError, transaction

    work = _work("gov-0", genres["rpg"])
    WorkFeatureVector.objects.create(
        work=work, feature_set_version=FEATURE_SET_VERSION, vector_json={}
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkFeatureVector.objects.create(
            work=work, feature_set_version=FEATURE_SET_VERSION, vector_json={}
        )
