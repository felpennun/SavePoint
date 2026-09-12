"""Deterministic, database-backed synthetic-user population generation."""

from __future__ import annotations

import random
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction

from accounts.models import DemoAccountIdentity, demo_identity_anchor_id
from catalogue.corpus import evaluation_candidate_works
from catalogue.popularity import normalised_popscore_by_work
from evaluation.archetypes import Archetype, DEFAULT_ARCHETYPES, validate_archetypes
from evaluation.protocol import load as load_protocol
from library.models import BacklogStatus, CopyFormat, LibraryEntry, OwnedCopy


SYNTHETIC_EVAL_USER_MARKER = "synthetic-eval-user"
SYNTHETIC_PHASE2_MARKER = "synthetic-eval-user-phase2"
SYNTHETIC_LOCK_KEY = 7250209
RATING_COUNT_WEIGHT_BUCKETS = (
    (5, 1.0),
    (20, 2.0),
    (100, 4.0),
    (500, 8.0),
    (2000, 16.0),
    (None, 32.0),
)
# Protocol v13 (2026-09-11): each non-empty library draws a PopScore-tier
# fraction (rounded up) from works with a complete IGDB PopScore composite
# (recommendations/catalogue.popularity.normalised_popscore_by_work returns
# only works with all four primitives), so most of a synthetic collection is
# a recognisable, popular title rather than a long-tail one. Within that
# tier, at least GUARANTEED_ELIGIBLE_MINIMUM entries are forced to
# `completed`/`playing` with a rating in GUARANTEED_RATING_HALF_STEPS, so
# leave-one-out always has enough relevant-positive, profile-eligible
# entries left after retiring one (D-17 relevance + the content profile's
# `_COLD_START_ENTRIES` activity requirement, recommendations/content/rank.py).
#
# Candidate protocol v15 (2026-09-11/12, not yet frozen): raised from 5 to 8
# to support a proposed leave-THREE-out study where all 3 retired items must
# also share the user's single most-weighted content tag. 5 guaranteed
# positives only left a margin of 1 above _COLD_START_ENTRIES=3 after
# retiring one; retiring three from that pool left as few as 2 for 19% of
# the current test split (measured directly, not assumed). 8 guaranteed
# restores the same +2 margin retiring three that 5 already gave retiring
# one.
#
# GUARANTEED_SAME_TAG_POOL_MINIMUM guards a second, distinct failure mode
# the author caught by inspection, not measurement: an earlier version of
# this constant (named GUARANTEED_SAME_TAG_MINIMUM = 3) only guaranteed
# *enough* same-tag positives to retire three -- if a user had exactly 3
# sharing their dominant tag, retiring exactly those 3 would leave zero
# remaining evidence of that tag in their profile, making "does it still
# recommend genre-matching content" an impossible task by construction
# (all the removed-genre signal is gone), not a meaningful one. 6 guarantees
# 3 survive retiring 3, so the profile still signals the genre being tested.
# Still drawn from the same archetype-preferred-tag-biased pool
# (`_pool_for`), so it is also expected to raise same-tag availability, not
# just the raw count -- verify empirically before freezing, same as every
# other population change this session.
POPSCORE_TIER_FRACTION = 0.75
GUARANTEED_ELIGIBLE_MINIMUM = 8
GUARANTEED_SAME_TAG_POOL_MINIMUM = 6
GUARANTEED_STATUS_CHOICES = (BacklogStatus.COMPLETED, BacklogStatus.PLAYING)
GUARANTEED_RATING_HALF_STEPS = (7, 8, 9, 10)
LEGACY_PHASE2_ARCHETYPES = frozenset(
    {
        "monogenero-severo",
        "monogenero-generoso",
        "omnivoro-medio",
        "completista-saga",
        "explorador-novedades",
        "coleccionista-pendientes",
        "jugador-ocasional-cold-start",
        "veterano-biblioteca-grande",
    }
)


@dataclass(frozen=True)
class SyntheticEntry:
    work_id: UUID
    current_status: str
    rating_half_steps: int | None
    release_id: UUID | None = None
    edition_id: UUID | None = None
    owned_copy: bool = False
    # Evaluation-manifest evidence only (protocol v13): True for the forced
    # completed/playing, rating>=3.5 entries drawn from the PopScore tier
    # that guarantee a usable leave-one-out positive. Not persisted on
    # LibraryEntry -- the product model has no such concept.
    guaranteed: bool = False


@dataclass(frozen=True)
class SyntheticUser:
    archetype: str
    label: str
    ordinal: int
    seed_key: str
    entries: tuple[SyntheticEntry, ...]
    no_history: bool = False


@dataclass(frozen=True)
class SyntheticPopulation:
    seed: int
    corpus_version: str | None
    users: tuple[SyntheticUser, ...]

    @property
    def cold_start_users(self) -> tuple[SyntheticUser, ...]:
        return tuple(user for user in self.users if 1 <= len(user.entries) <= 4)

    @property
    def no_history_users(self) -> tuple[SyntheticUser, ...]:
        return tuple(user for user in self.users if not user.entries)


@dataclass(frozen=True)
class _WorkCandidate:
    work_id: UUID
    tags: frozenset[str]
    first_release_date: date | None
    rating_count: int
    release_id: UUID | None
    edition_id: UUID | None


class SyntheticGenerationError(ValueError):
    """Raised before writes when the corpus cannot satisfy the scenario."""


def _work_candidates(
    corpus_version: str | None,
    *,
    minimum_rating_count: int | None = None,
) -> list[_WorkCandidate]:
    queryset = evaluation_candidate_works(corpus_version)
    if minimum_rating_count is not None:
        queryset = queryset.filter(rating_count__gte=minimum_rating_count)
    works = (
        queryset
        .prefetch_related("curated_labels", "releases__editions")
        .order_by("id")
    )
    candidates: list[_WorkCandidate] = []
    for work in works:
        releases = list(work.releases.all())
        release = releases[0] if releases else None
        editions = list(release.editions.all()) if release is not None else []
        candidates.append(
            _WorkCandidate(
                work_id=work.id,
                tags=frozenset(tag.slug for tag in work.curated_labels.all()),
                first_release_date=work.first_release_date,
                rating_count=work.rating_count or 0,
                release_id=release.id if release is not None else None,
                edition_id=editions[0].id if editions else None,
            )
        )
    return candidates


def _rating(rng: random.Random, generosity: str) -> int | None:
    if rng.random() < 0.15:
        return None
    ranges = {"severe": (2, 7), "medium": (4, 9), "generous": (6, 10)}
    low, high = ranges.get(generosity, ranges["medium"])
    return rng.randint(low, high)


def _rating_count_weight(rating_count: int | None) -> float:
    """Return the stepped collection weight for an IGDB user-rating count.

    The weights are deliberately sublinear: popularity affects exposure, but
    does not erase genre preferences or make the synthetic catalogue collapse
    onto only the most rated works.
    """

    count = max(int(rating_count or 0), 1)
    for maximum, weight in RATING_COUNT_WEIGHT_BUCKETS:
        if maximum is None or count < maximum:
            return weight
    raise AssertionError("rating-count weight buckets must have an open final bucket")


def _weighted_sample_without_replacement(
    pool: list[_WorkCandidate], size: int, rng: random.Random
) -> list[_WorkCandidate]:
    """Sample distinct works with an increasing, stepped rating-count bias."""

    available = list(pool)
    selected: list[_WorkCandidate] = []
    for _ in range(size):
        weights = [_rating_count_weight(work.rating_count) for work in available]
        choice = rng.choices(available, weights=weights, k=1)[0]
        selected.append(choice)
        available.remove(choice)
    return selected


def _pool_for(
    archetype: Archetype,
    preferred: set[str],
    works: list[_WorkCandidate],
) -> list[_WorkCandidate]:
    matching = [work for work in works if work.tags.intersection(preferred)]
    if len(matching) < archetype.library_size_range[1]:
        matching = works
    if archetype.saga_concentration and preferred:
        saga_genre = sorted(preferred)[0]
        saga = [work for work in matching if saga_genre in work.tags]
        if len(saga) >= archetype.library_size_range[0]:
            matching = saga + [work for work in matching if work not in saga]
    if archetype.release_bias == "recent":
        dated = sorted(
            matching,
            key=lambda work: (
                work.first_release_date is not None,
                work.first_release_date or date.min,
            ),
            reverse=True,
        )
        recent_count = max(archetype.library_size_range[1], len(dated) // 3)
        matching = dated[:recent_count]
    return matching


def _ensure_positive(entries: list[SyntheticEntry]) -> None:
    """Ensure every simulated profile contributes at least one relevant item."""

    if any(
        entry.current_status == BacklogStatus.COMPLETED
        or (entry.rating_half_steps or 0) >= 7
        for entry in entries
    ):
        return
    first = entries[0]
    entries[0] = SyntheticEntry(
        work_id=first.work_id,
        current_status=BacklogStatus.COMPLETED,
        rating_half_steps=max(first.rating_half_steps or 0, 7),
    )


def generate(
    seed: int,
    archetypes: Iterable[Archetype] = DEFAULT_ARCHETYPES,
    corpus_version: str | None = None,
) -> SyntheticPopulation:
    """Generate an in-memory population; this function never writes to the DB."""

    selected = tuple(archetypes)
    validate_archetypes(selected)
    protocol = load_protocol()
    works = _work_candidates(corpus_version, minimum_rating_count=1)
    if not works:
        raise SyntheticGenerationError(
            "the governed corpus contains no works with rating_count >= 1"
        )
    # PopScore-complete subset of the already-eligible pool (protocol v13):
    # normalised_popscore_by_work only returns works with all four IGDB
    # engagement primitives, so this frozenset is exactly the "known/popular
    # enough to have measurable engagement" pool the PopScore tier draws from.
    popscore_ids = frozenset(
        normalised_popscore_by_work(corpus_version, [work.work_id for work in works])
    )
    available_tags = sorted({tag for work in works for tag in work.tags})
    users: list[SyntheticUser] = []
    for archetype in selected:
        min_tags, max_tags = archetype.genre_pref_range
        for ordinal in range(1, archetype.n_users + 1):
            user_rng = random.Random(f"{seed}:{archetype.name}:{ordinal}")
            # Candidate protocol v15 (2026-09-12, not yet frozen): each user
            # now draws their *own* preferred-tag set, instead of one set
            # shared by every user of the same archetype (the previous
            # behaviour -- e.g. all 33 "cold-start-monogenero" users had the
            # exact same 1-2 preferred tags). A tag that is only ever "most
            # weighted" because it happens to win a near-tie inside a pool
            # shared by dozens of people is a fragile signal to build a
            # leave-N-out-by-tag study on; an individually induced
            # preference is a real, stable one to test against.
            tag_count = min(user_rng.randint(min_tags, max_tags), len(available_tags))
            preferred = set(user_rng.sample(available_tags, tag_count)) if tag_count else set()
            pool = _pool_for(archetype, preferred, works)
            min_size, max_size = archetype.library_size_range
            requested_size = user_rng.randint(min_size, max_size)
            if requested_size > len(pool):
                raise SyntheticGenerationError(
                    f"corpus has {len(pool)} candidates but {archetype.name} needs {requested_size}"
                )
            guaranteed_ids: frozenset[UUID] = frozenset()
            if requested_size == 0:
                chosen: list[_WorkCandidate] = []
            else:
                popscore_count = math.ceil(POPSCORE_TIER_FRACTION * requested_size)
                free_count = requested_size - popscore_count
                popscore_pool = [work for work in pool if work.work_id in popscore_ids]
                if len(popscore_pool) < popscore_count:
                    # Not enough PopScore-complete supply within this
                    # archetype's tag-preferred pool -- widen to the whole
                    # eligible corpus before giving up (mirrors _pool_for's
                    # own tag-affinity fallback).
                    popscore_pool = [work for work in works if work.work_id in popscore_ids]
                if len(popscore_pool) < popscore_count:
                    # This corpus has too little (or no) PopScore coverage to
                    # fill the realism tier at all -- degrade to the general
                    # eligible pool rather than fail generation. The
                    # guaranteed-eligible entries below still come from this
                    # tier, so the leave-one-out guarantee is unaffected;
                    # only the "known/popular" realism preference is lost.
                    popscore_pool = pool if len(pool) >= popscore_count else works
                if len(popscore_pool) < popscore_count:
                    raise SyntheticGenerationError(
                        f"corpus has only {len(popscore_pool)} eligible candidates "
                        f"but {archetype.name} needs {popscore_count}"
                    )
                guaranteed_target = min(GUARANTEED_ELIGIBLE_MINIMUM, popscore_count)
                # Candidate protocol v15: force at least GUARANTEED_SAME_TAG_
                # MINIMUM of the guaranteed positives to share one tag,
                # instead of leaving tag concentration to chance. Without
                # this, whichever tag ends up dominating a user's *weighted*
                # content profile (recommendations/content/profile.py) was
                # only reliably matched by >=3 of their own eligible
                # positives for ~88% of users even after raising
                # GUARANTEED_ELIGIBLE_MINIMUM alone (measured directly,
                # 2026-09-11) -- a fixed-size random draw from the preferred-
                # tag pool doesn't guarantee any *one* tag repeats enough
                # times. The cluster tag is the best-supplied preferred tag in
                # this user's own PopScore-tier pool, so it is deterministic
                # given the seed and never starves a user of a tag with no
                # supply.
                cluster_tag = None
                if preferred:
                    tag_supply = Counter(
                        tag for work in popscore_pool for tag in work.tags if tag in preferred
                    )
                    if tag_supply:
                        cluster_tag = max(tag_supply.items(), key=lambda item: (item[1], item[0]))[0]
                same_tag_pool = (
                    [work for work in popscore_pool if cluster_tag in work.tags] if cluster_tag else []
                )
                same_tag_target = min(GUARANTEED_SAME_TAG_POOL_MINIMUM, guaranteed_target, len(same_tag_pool))
                same_tag_chosen = (
                    _weighted_sample_without_replacement(same_tag_pool, same_tag_target, user_rng)
                    if same_tag_target
                    else []
                )
                remaining_popscore_pool = [
                    work for work in popscore_pool
                    if work.work_id not in {chosen.work_id for chosen in same_tag_chosen}
                ]
                remaining_popscore_target = popscore_count - len(same_tag_chosen)
                if remaining_popscore_target > len(remaining_popscore_pool):
                    remaining_popscore_pool = [
                        work for work in works
                        if work.work_id in popscore_ids
                        and work.work_id not in {chosen.work_id for chosen in same_tag_chosen}
                    ]
                if remaining_popscore_target > len(remaining_popscore_pool):
                    raise SyntheticGenerationError(
                        f"corpus has only {len(remaining_popscore_pool)} eligible candidates "
                        f"but {archetype.name} needs {remaining_popscore_target} more after the "
                        "same-tag guarantee"
                    )
                rest_chosen = _weighted_sample_without_replacement(
                    remaining_popscore_pool, remaining_popscore_target, user_rng
                )
                popscore_chosen = same_tag_chosen + rest_chosen
                guaranteed_ids = frozenset(
                    work.work_id for work in popscore_chosen[:guaranteed_target]
                )
                free_chosen: list[_WorkCandidate] = []
                if free_count:
                    excluded = {work.work_id for work in popscore_chosen}
                    free_pool = [work for work in pool if work.work_id not in excluded]
                    if len(free_pool) < free_count:
                        free_pool = [work for work in works if work.work_id not in excluded]
                    if len(free_pool) < free_count:
                        raise SyntheticGenerationError(
                            f"corpus has only {len(free_pool)} remaining candidates "
                            f"but {archetype.name} needs {free_count} more"
                        )
                    free_chosen = _weighted_sample_without_replacement(
                        free_pool, free_count, user_rng
                    )
                chosen = popscore_chosen + free_chosen
            states = list(archetype.status_mix)
            weights = list(archetype.status_mix.values())
            entries = []
            for work in chosen:
                if work.work_id in guaranteed_ids:
                    status = user_rng.choice(GUARANTEED_STATUS_CHOICES)
                    rating = user_rng.choice(GUARANTEED_RATING_HALF_STEPS)
                else:
                    status = user_rng.choices(states, weights=weights, k=1)[0]
                    rating = _rating(user_rng, archetype.rating_generosity)
                entries.append(
                    SyntheticEntry(
                        work_id=work.work_id,
                        current_status=status,
                        rating_half_steps=rating,
                        release_id=work.release_id,
                        edition_id=work.edition_id,
                        owned_copy=bool(work.release_id and user_rng.random() < 0.35),
                        guaranteed=work.work_id in guaranteed_ids,
                    )
                )
            if entries:
                _ensure_positive(entries)
                if not any(entry.owned_copy for entry in entries):
                    for index, entry in enumerate(entries):
                        if entry.release_id is not None:
                            entries[index] = SyntheticEntry(
                                work_id=entry.work_id,
                                current_status=entry.current_status,
                                rating_half_steps=entry.rating_half_steps,
                                release_id=entry.release_id,
                                edition_id=entry.edition_id,
                                owned_copy=True,
                                guaranteed=entry.guaranteed,
                            )
                            break
            users.append(
                SyntheticUser(
                    archetype=archetype.name,
                    label=archetype.label,
                    ordinal=ordinal,
                    seed_key=f"synthetic-{archetype.name}-{ordinal}",
                    entries=tuple(entries),
                    no_history=archetype.no_history,
                )
            )
    generated = SyntheticPopulation(seed=seed, corpus_version=corpus_version, users=tuple(users))
    validate_population(generated, relevance_floor=protocol.relevance_rating_floor)
    return generated


def validate_population(population: SyntheticPopulation, *, relevance_floor: int = 7) -> None:
    """Validate invariants before the persistence transaction begins."""

    if not population.users:
        raise SyntheticGenerationError("synthetic population is empty")
    seen_keys: set[str] = set()
    for user in population.users:
        if user.seed_key in seen_keys:
            raise SyntheticGenerationError("synthetic seed keys must be unique")
        seen_keys.add(user.seed_key)
        if not user.entries and not user.no_history:
            raise SyntheticGenerationError("every non-empty synthetic user needs a library entry")
        if len({entry.work_id for entry in user.entries}) != len(user.entries):
            raise SyntheticGenerationError("a synthetic user cannot contain duplicate works")
        if user.entries and not any(
            entry.current_status == BacklogStatus.COMPLETED
            or (entry.rating_half_steps or 0) >= relevance_floor
            for entry in user.entries
        ):
            raise SyntheticGenerationError("every synthetic user needs one relevant-positive work")


def apply_population(population: SyntheticPopulation) -> dict[str, object]:
    """Persist a validated population atomically and idempotently."""

    validate_population(population)
    created = 0
    updated = 0
    anchor_ids: list[str] = []
    user_ids: dict[str, str] = {}
    user_model = get_user_model()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [SYNTHETIC_LOCK_KEY])
        # Retire the legacy Phase 2 population from the active evaluation
        # marker while preserving its accounts and library data for audit.
        for archetype_name in LEGACY_PHASE2_ARCHETYPES:
            DemoAccountIdentity.objects.filter(
                marker=SYNTHETIC_EVAL_USER_MARKER,
                seed_key__startswith=f"synthetic-{archetype_name}-",
            ).update(marker=SYNTHETIC_PHASE2_MARKER)
        for synthetic_user in population.users:
            anchor_id = demo_identity_anchor_id(synthetic_user.seed_key)
            identity = (
                DemoAccountIdentity.objects.select_related("user")
                .filter(seed_key=synthetic_user.seed_key)
                .first()
            )
            if identity is None:
                username = f"synthetic-{synthetic_user.archetype}-{synthetic_user.ordinal}"
                if user_model.objects.filter(username=username).exists():
                    raise SyntheticGenerationError(
                        "a synthetic username collides with an unrelated account"
                    )
                user = user_model.objects.create(username=username, is_active=False)
                user.set_unusable_password()
                user.save(update_fields=["password"])
                identity = DemoAccountIdentity.objects.create(
                    id=anchor_id,
                    seed_key=synthetic_user.seed_key,
                    user=user,
                    is_simulated=True,
                    marker=SYNTHETIC_EVAL_USER_MARKER,
                    display_label=(
                        f"Usuario sintético — {synthetic_user.label} #{synthetic_user.ordinal}"
                    ),
                )
                created += 1
            elif identity.marker != SYNTHETIC_EVAL_USER_MARKER:
                raise SyntheticGenerationError(
                    "a synthetic seed key belongs to a non-synthetic account"
                )
            else:
                updated += 1
            OwnedCopy.objects.filter(user=identity.user).delete()
            LibraryEntry.objects.filter(user=identity.user).delete()
            LibraryEntry.objects.bulk_create(
                [
                    LibraryEntry(
                        user=identity.user,
                        work_id=entry.work_id,
                        current_status=entry.current_status,
                        rating_half_steps=entry.rating_half_steps,
                    )
                    for entry in synthetic_user.entries
                ]
            )
            OwnedCopy.objects.bulk_create(
                [
                    OwnedCopy(
                        user=identity.user,
                        work_id=entry.work_id,
                        release_id=entry.release_id,
                        edition_id=entry.edition_id,
                        format=(
                            CopyFormat.PHYSICAL
                            if index % 2 == 0
                            else CopyFormat.DIGITAL
                        ),
                        idempotency_key=f"{synthetic_user.seed_key}-{entry.work_id}",
                    )
                    for index, entry in enumerate(synthetic_user.entries)
                    if entry.owned_copy and entry.release_id is not None
                ]
            )
            anchor_ids.append(str(anchor_id))
            user_ids[synthetic_user.seed_key] = str(identity.user_id)
    return {
        "created": created,
        "updated": updated,
        "anchor_ids": anchor_ids,
        "user_ids": user_ids,
    }


def _cohort_for(user: SyntheticUser) -> str:
    # Protocol v13: every non-empty library is drawn from the same 10-20
    # range (archetypes.py), so the earlier sparse/normal/intensive
    # stratification by size no longer applies -- there is just the
    # no_history cold-start cohort and everyone else.
    if user.no_history:
        return "no_history"
    return "active_history_10_to_20"


def render_population_manifest(
    population: SyntheticPopulation,
    *,
    account_ids: dict[str, str] | None = None,
) -> str:
    """Render the machine-readable, hash-pinned synthetic population manifest."""

    payload = {
        "schema_version": "phase3-synthetic-population-v1",
        "seed": population.seed,
        "corpus_version": population.corpus_version,
        "active_marker": SYNTHETIC_EVAL_USER_MARKER,
        "population_count": len(population.users),
        "rating_count_min": 1,
        "rating_count_weight_buckets": [
            {"max_exclusive": maximum, "weight": weight}
            for maximum, weight in RATING_COUNT_WEIGHT_BUCKETS
        ],
        "popscore_tier_fraction": POPSCORE_TIER_FRACTION,
        "guaranteed_eligible_minimum": GUARANTEED_ELIGIBLE_MINIMUM,
        "guaranteed_rating_half_steps_choices": list(GUARANTEED_RATING_HALF_STEPS),
        "split": {"train": 240, "validation": 80, "test": 80, "seed": 20260908},
        "users": [
            {
                "seed_key": user.seed_key,
                "account_id": (account_ids or {}).get(user.seed_key),
                "archetype": user.archetype,
                "cohort": _cohort_for(user),
                "library_size": len(user.entries),
                "guaranteed_count": sum(entry.guaranteed for entry in user.entries),
                "entries": [
                    {
                        "work_id": str(entry.work_id),
                        "current_status": entry.current_status,
                        "rating_half_steps": entry.rating_half_steps,
                        "release_id": str(entry.release_id) if entry.release_id else None,
                        "edition_id": str(entry.edition_id) if entry.edition_id else None,
                        "owned_copy": entry.owned_copy,
                        "guaranteed": entry.guaranteed,
                    }
                    for entry in user.entries
                ],
            }
            for user in population.users
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    payload["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def render_validation_report(population: SyntheticPopulation) -> str:
    """Render a reproducible Spanish validation report from a population."""

    lines = [
        "# Validación de usuarios sintéticos",
        "",
        "Este informe describe una población generada de forma paramétrica. Sus resultados son evidencia de simulación y no deben interpretarse como evidencia sobre usuarios reales (EVAL-10).",
        "",
        f"- Semilla: `{population.seed}`",
        f"- Versión de corpus: `{population.corpus_version or 'no especificada'}`",
        f"- Usuarios generados: **{len(population.users)}**",
        f"- Sin historial (0 juegos): **{len(population.no_history_users)}**",
        f"- Cohorte cold-start (1–4 juegos): **{len(population.cold_start_users)}**",
        f"- Historial normal (5–10 juegos): **{sum(5 <= len(user.entries) <= 10 for user in population.users)}**",
        f"- Historial intensivo (>10 juegos): **{sum(len(user.entries) > 10 for user in population.users)}**",
        "",
        "## Resumen por arquetipo",
        "",
        "| Arquetipo | Usuarios | Biblioteca media | Mín. | Máx. | Distribución de ratings | Estados |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    by_archetype: dict[str, list[SyntheticUser]] = {}
    for user in population.users:
        by_archetype.setdefault(user.archetype, []).append(user)
    for archetype, users in by_archetype.items():
        sizes = [len(user.entries) for user in users]
        ratings = Counter(entry.rating_half_steps for user in users for entry in user.entries)
        statuses = Counter(entry.current_status for user in users for entry in user.entries)
        histogram = ", ".join(
            f"{key if key is not None else 'sin rating'}: {value}"
            for key, value in sorted(
                ratings.items(), key=lambda item: -1 if item[0] is None else item[0]
            )
        )
        status_text = ", ".join(f"{key}: {value}" for key, value in sorted(statuses.items()))
        lines.append(
            f"| {archetype} | {len(users)} | {sum(sizes) / len(sizes):.2f} | "
            f"{min(sizes)} | {max(sizes)} | {histogram} | {status_text} |"
        )
    lines.extend(
        [
            "",
            "## Interpretación",
            "",
            "La misma semilla, versión de corpus y especificación de arquetipos deben producir los mismos identificadores de obra, estados y valoraciones. Las cohortes sin historial y cold-start se mantienen separadas para evaluar el enrutamiento con historial insuficiente. La generación no incorpora datos personales ni pretende estimar la distribución de jugadores reales.",
            "",
        ]
    )
    return "\n".join(lines)


def default_report_path() -> Path:
    return Path(settings.BASE_DIR).parent.parent / "docs" / "verification" / "synthetic-users-validation.md"
