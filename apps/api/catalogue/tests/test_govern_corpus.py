import hashlib
import io
import json
from datetime import date

import pytest
from django.core.management import call_command

from catalogue.corpus import ALLOWLIST_SLUGS, evaluation_candidate_works
from catalogue.models import GameRelease, GameWork, Genre, Platform, SourceRecord


pytestmark = pytest.mark.django_db


def make_platform(slug: str = "pc-microsoft-windows") -> Platform:
    return Platform.objects.create(name=slug.replace("-", " "), slug=slug)


def make_work(
    source_id: int,
    *,
    title: str = "Valid Game",
    platform_slug: str = "pc-microsoft-windows",
    with_genre: bool = True,
    release_date: date | None = date(2020, 1, 1),
    is_dlc: bool = False,
) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=f"valid-game-{source_id}",
        original_title=title,
        first_release_date=release_date,
        is_dlc=is_dlc,
    )
    platform = Platform.objects.filter(slug=platform_slug).first() or make_platform(platform_slug)
    GameRelease.objects.create(
        work=work,
        platform=platform,
        release_name=f"{title} release {source_id}",
        release_date=release_date,
    )
    if with_genre:
        genre, _ = Genre.objects.get_or_create(
            igdb_id=source_id,
            defaults={"name": f"Genre {source_id}", "slug": f"genre-{source_id}"},
        )
        work.genres.add(genre)
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id=str(source_id),
        source_url=f"https://www.igdb.com/games/valid-game-{source_id}",
        retrieved_at="2026-09-07T00:00:00Z",
        licence="IGDB",
        snapshot_sha256=hashlib.sha256(str(source_id).encode()).hexdigest(),
    )
    return work


def run_governance(version: str = "2026.09.1") -> dict:
    output = io.StringIO()
    call_command(
        "govern_corpus",
        version=version,
        as_of_date="2026-09-09",
        evidence_json="-",
        stdout=output,
    )
    return json.loads(output.getvalue())


def test_govern_corpus_applies_every_d03_clause_and_keeps_unrated() -> None:
    valid = make_work(1, title="Unrated Valid Game")
    invalid_name = make_work(2, title="?")
    no_platform = make_work(3, platform_slug="arcade")
    no_genre = make_work(4, with_genre=False)
    no_date = make_work(5, release_date=None)
    dlc = make_work(6, is_dlc=True)

    evidence = run_governance()

    valid.refresh_from_db()
    assert valid.in_corpus is True
    assert valid.corpus_version == "2026.09.1"
    assert valid.total_rating is None  # no rating is not a D-03 exclusion
    for work in (invalid_name, no_platform, no_genre, no_date, dlc):
        work.refresh_from_db()
        assert work.in_corpus is False
        assert work.corpus_version == ""

    reasons = evidence["quality_report"]["exclusion_reason_histogram"]
    assert reasons == {
        "invalid_name": 1,
        "missing_allowlisted_platform": 1,
        "is_dlc": 1,
        "missing_genre": 1,
        "missing_first_release_date": 1,
        "future_release_date": 0,
    }
    assert evidence["quality_report"]["governed_count"] == 1
    assert evidence["quality_report"]["recommendation_candidate_count"] == 0
    assert len(evidence["sampled_manifest"]) == 1


def test_recommendation_candidates_require_rating_and_minimum_total_volume() -> None:
    threshold_candidate = make_work(20)
    threshold_candidate.rating = 72.0
    threshold_candidate.total_rating_count = 5
    threshold_candidate.save(update_fields=["rating", "total_rating_count"])
    higher_volume_candidate = make_work(21)
    higher_volume_candidate.rating = 80.0
    higher_volume_candidate.total_rating_count = 10
    higher_volume_candidate.save(update_fields=["rating", "total_rating_count"])
    missing_rating = make_work(22)
    missing_rating.total_rating_count = 100
    missing_rating.save(update_fields=["total_rating_count"])
    below_threshold = make_work(23)
    below_threshold.rating = 90.0
    below_threshold.total_rating_count = 4
    below_threshold.save(update_fields=["rating", "total_rating_count"])

    run_governance()

    assert set(evaluation_candidate_works("2026.09.1").values_list("id", flat=True)) == {
        threshold_candidate.id,
        higher_volume_candidate.id,
    }
    candidates = evaluation_candidate_works("2026.09.1").values_list("id", flat=True)
    assert missing_rating.id not in candidates
    assert below_threshold.id not in candidates


def test_govern_corpus_is_idempotent_and_emits_all_evidence_sections() -> None:
    make_work(10)
    first = run_governance()
    second = run_governance()

    assert first["checksum"] == second["checksum"]
    assert first["corpus_version"] == second["corpus_version"] == "2026.09.1"
    assert set(first) >= {
        "checksum",
        "data_dictionary",
        "quality_report",
        "sampled_manifest",
    }
    assert len(first["sampled_manifest"]) <= 300
    assert first["quality_report"]["coverage"]["total_rating"]["null_or_empty"] == 1
    assert first["quality_report"]["coverage"]["rating"]["null_or_empty"] == 1
    assert first["quality_report"]["unresolved_allowlist_slugs"]


def test_allowlist_contains_the_ratified_platform_set() -> None:
    assert len(ALLOWLIST_SLUGS) == 39
    assert {"pc-microsoft-windows", "playstation-5", "xbox-series-x-s"} <= ALLOWLIST_SLUGS
