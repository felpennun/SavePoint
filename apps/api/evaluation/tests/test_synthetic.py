"""Tests for deterministic synthetic evaluation users (EVAL-09/EVAL-10)."""

from __future__ import annotations

from datetime import date

import pytest
from django.core.management import call_command

from accounts.models import DemoAccountIdentity, SIMULATED_ACCOUNT_MARKER
from catalogue.models import GameWork, Genre
from evaluation.archetypes import Archetype, DEFAULT_ARCHETYPES
from evaluation.synthetic import (
    SYNTHETIC_EVAL_USER_MARKER,
    SyntheticEntry,
    SyntheticGenerationError,
    SyntheticPopulation,
    SyntheticUser,
    generate,
    render_validation_report,
    _rating_count_weight,
    validate_population,
)
from library.models import LibraryEntry


def _works(count: int = 80) -> None:
    genres = [
        Genre.objects.create(igdb_id=index, name=f"Genre {index}", slug=f"genre-{index}")
        for index in range(1, 5)
    ]
    for index in range(count):
        work = GameWork.objects.create(
            canonical_slug=f"synthetic-work-{index}",
            original_title=f"Synthetic Work {index}",
            first_release_date=date(2010 + index % 15, 1, 1),
            rating=80.0,
            rating_count=10,
            total_rating_count=10,
            in_corpus=True,
            corpus_version="test",
        )
        work.genres.add(genres[index % len(genres)])


@pytest.fixture
def one_archetype(db):  # noqa: ANN001
    _works()
    return (
        Archetype(
            name="test-cold-start",
            label="Test cold-start",
            n_users=3,
            genre_pref_range=(1, 2),
            library_size_range=(1, 3),
            rating_generosity="medium",
            status_mix={"completed": 0.5, "pending": 0.5},
            cold_start=True,
        ),
    )


@pytest.mark.django_db
def test_same_seed_produces_identical_histories(one_archetype) -> None:  # noqa: ANN001
    first = generate(20260907, one_archetype, "test")
    second = generate(20260907, one_archetype, "test")
    assert first == second
    assert [entry for user in first.users for entry in user.entries]


@pytest.mark.parametrize(
    ("lower", "higher"),
    ((4, 5), (19, 20), (99, 100), (499, 500), (1999, 2000)),
)
def test_rating_count_weights_increase_by_bucket(lower: int, higher: int) -> None:
    assert _rating_count_weight(lower) < _rating_count_weight(higher)


@pytest.mark.django_db
def test_default_phase3_population_has_the_frozen_cohorts(db) -> None:  # noqa: ANN001
    _works()
    population = generate(20260909, DEFAULT_ARCHETYPES, "test")
    sizes = [len(user.entries) for user in population.users]
    assert len(population.users) == 400
    # Protocol v13: no size stratification below no_history -- every other
    # archetype draws a 10-20 entry library (evaluation/archetypes.py).
    assert sum(size == 0 for size in sizes) == 10
    assert sum(10 <= size <= 20 for size in sizes) == 390


@pytest.mark.django_db
def test_default_phase3_population_guarantees_five_eligible_positives(db) -> None:  # noqa: ANN001
    _works()
    population = generate(20260909, DEFAULT_ARCHETYPES, "test")
    for user in population.users:
        if user.no_history:
            continue
        guaranteed = [entry for entry in user.entries if entry.guaranteed]
        assert len(guaranteed) >= 5
        assert all(entry.current_status in ("completed", "playing") for entry in guaranteed)
        assert all(entry.rating_half_steps is not None and entry.rating_half_steps >= 7 for entry in guaranteed)


@pytest.mark.django_db
def test_guaranteed_flag_survives_the_owned_copy_backfill(db) -> None:  # noqa: ANN001
    # Regression: the owned-copy-guarantee rebuild used to reconstruct a
    # SyntheticEntry without forwarding `guaranteed`, silently dropping one
    # of the five guaranteed positives whenever no entry rolled owned_copy
    # by chance and the rebuild happened to land on a guaranteed entry.
    _works()
    for seed in range(20260911, 20260931):
        population = generate(seed, DEFAULT_ARCHETYPES, "test")
        for user in population.users:
            if user.no_history:
                continue
            assert sum(entry.guaranteed for entry in user.entries) >= 5, user.seed_key


@pytest.mark.django_db
def test_cold_start_is_one_to_three_and_marker_is_distinct(one_archetype) -> None:  # noqa: ANN001
    population = generate(20260907, one_archetype, "test")
    assert all(1 <= len(user.entries) <= 3 for user in population.cold_start_users)
    assert SYNTHETIC_EVAL_USER_MARKER != SIMULATED_ACCOUNT_MARKER


@pytest.mark.django_db
def test_validation_report_contains_archetype_counts(one_archetype) -> None:  # noqa: ANN001
    report = render_validation_report(generate(20260907, one_archetype, "test"))
    assert "test-cold-start" in report
    assert "Cohorte cold-start" in report
    assert "EVAL-10" in report


@pytest.mark.django_db
def test_command_dry_run_does_not_persist(one_archetype, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(
        "evaluation.management.commands.generate_synthetic_users.DEFAULT_ARCHETYPES",
        one_archetype,
    )
    call_command("generate_synthetic_users", seed=20260907, corpus_version="test", dry_run=True)
    assert DemoAccountIdentity.objects.count() == 0
    assert LibraryEntry.objects.count() == 0


@pytest.mark.django_db
def test_synthetic_command_persists_distinct_marker(one_archetype, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(
        "evaluation.management.commands.generate_synthetic_users.DEFAULT_ARCHETYPES",
        one_archetype,
    )
    call_command("generate_synthetic_users", seed=20260907, corpus_version="test")
    assert DemoAccountIdentity.objects.filter(marker=SYNTHETIC_EVAL_USER_MARKER).count() == 3
    assert not DemoAccountIdentity.objects.filter(marker=SIMULATED_ACCOUNT_MARKER).exists()
    assert LibraryEntry.objects.count() > 0


@pytest.mark.django_db
def test_invalid_population_is_rejected_before_any_write(db) -> None:  # noqa: ANN001
    work_id = GameWork.objects.create(
        canonical_slug="invalid-synthetic-work",
        original_title="Invalid Synthetic Work",
    ).id
    user = SyntheticUser(
        archetype="invalid",
        label="Invalid",
        ordinal=1,
        seed_key="synthetic-invalid-1",
        entries=(
            SyntheticEntry(work_id=work_id, current_status="pending", rating_half_steps=1),
        ),
    )
    with pytest.raises(SyntheticGenerationError):
        validate_population(SyntheticPopulation(seed=1, corpus_version="test", users=(user,)))
    assert DemoAccountIdentity.objects.count() == 0
