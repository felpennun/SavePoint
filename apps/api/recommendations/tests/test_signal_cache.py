"""Cross-process shared content-signal cache (2026-09-11)."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone

from catalogue.models import CorpusRatingSnapshot, CorpusVersion, CuratedLabel, GameWork
from library.models import LibraryEntry
from recommendations.content import signal_cache
from recommendations.content.rank import rank_content_v1
from recommendations.models import RecommendationSignalCache

CORPUS = "signal-cache-test"
User = get_user_model()


@pytest.fixture
def corpus(db):  # noqa: ANN001
    CorpusVersion.objects.create(
        version=CORPUS, ruleset_sha256="b" * 64, is_active=True, governed_count=4
    )


@pytest.fixture
def user(db):  # noqa: ANN001
    return User.objects.create_user(username="signal-cache-user", password="Signal-Cache-Pass-9!")


def _label(slug: str) -> CuratedLabel:
    return CuratedLabel.objects.create(
        name=slug, slug=slug, kind=CuratedLabel.Kind.GENRE, curation_version="test"
    )


def _work(slug: str, *labels: CuratedLabel) -> GameWork:
    item = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug,
        in_corpus=True,
        corpus_version=CORPUS,
        rating=80.0,
        total_rating_count=10,
        first_release_date=date(2020, 1, 1),
    )
    item.curated_labels.set(labels)
    CorpusRatingSnapshot.objects.create(
        work=item,
        corpus_version=CORPUS,
        source="igdb",
        rating=80.0,
        rating_count=10,
        retrieved_at=django_timezone.now(),
    )
    return item


def _seed(user, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user, work=work, current_status="completed", rating_half_steps=10)


def test_signal_cache_stores_one_row_per_user_revision_configuration(corpus, user) -> None:  # noqa: ANN001
    rpg = _label("signal-cache-rpg")
    candidate = _work("signal-cache-candidate", rpg)
    for index in range(3):
        _seed(user, _work(f"signal-cache-seed-{index}", rpg))

    candidate_ids = {candidate.id}
    bundle = signal_cache.build_corpus_bundle(user, CORPUS, candidate_ids)
    row = signal_cache.build_and_store_signal_cache(
        user=user,
        requested_revision=1,
        configuration_fingerprint="test-config",
        corpus_version=CORPUS,
        bundle=bundle,
    )

    assert RecommendationSignalCache.objects.filter(pk=row.pk).exists()
    assert str(candidate.id) in row.rating_term_json
    assert str(candidate.id) in row.similarity_json
    assert row.profile_inputs_json["positive_entry_count"] == 3

    # Re-running the signals job for the same key replaces the row rather
    # than creating a second one (matches the job queue's own coalescing).
    signal_cache.build_and_store_signal_cache(
        user=user,
        requested_revision=1,
        configuration_fingerprint="test-config",
        corpus_version=CORPUS,
        bundle=bundle,
    )
    assert RecommendationSignalCache.objects.filter(
        user=user, requested_revision=1, configuration_fingerprint="test-config"
    ).count() == 1


def test_rank_content_v1_reads_the_stored_signal_cache_instead_of_recomputing(corpus, user) -> None:  # noqa: ANN001
    rpg = _label("signal-cache-rpg-2")
    candidate = _work("signal-cache-candidate-2", rpg)
    for index in range(3):
        _seed(user, _work(f"signal-cache-seed-2-{index}", rpg))

    candidate_ids = {candidate.id}
    bundle = signal_cache.build_corpus_bundle(user, CORPUS, candidate_ids)
    row = signal_cache.build_and_store_signal_cache(
        user=user,
        requested_revision=1,
        configuration_fingerprint="test-config",
        corpus_version=CORPUS,
        bundle=bundle,
    )

    # Poison the stored rating_term for the one candidate with an
    # unmistakable, otherwise-impossible value: if rank_content_v1's warm
    # loop actually reads this cache (rather than recomputing rating_term
    # fresh from the snapshot), the poisoned value must reach the result.
    row.rating_term_json[str(candidate.id)] = [0.4242, False]
    row.save(update_fields=["rating_term_json"])

    prepared = signal_cache.load_prepared(row, user=user, bundle=bundle)
    result = rank_content_v1(
        user,
        "content-cbf-weighted-v1",
        corpus_version=CORPUS,
        candidate_ids=candidate_ids,
        prepared=prepared,
    )

    assert result["insufficient_history"] is False
    assert len(result["results"]) == 1
    assert result["results"][0]["rating_term"] == pytest.approx(0.4242)

    # An uncached call recomputes rating_term from the (unpoisoned) snapshot
    # and must not see the poisoned value -- proving the two paths are
    # actually independent, not accidentally sharing module-level state.
    uncached = rank_content_v1(
        user, "content-cbf-weighted-v1", corpus_version=CORPUS, candidate_ids=candidate_ids
    )
    assert uncached["results"][0]["rating_term"] != pytest.approx(0.4242)
