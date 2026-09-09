"""Deterministic, database-backed synthetic-user population generation."""

from __future__ import annotations

import random
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
from evaluation.archetypes import Archetype, DEFAULT_ARCHETYPES, validate_archetypes
from evaluation.protocol import load as load_protocol
from library.models import BacklogStatus, LibraryEntry


SYNTHETIC_EVAL_USER_MARKER = "synthetic-eval-user"
SYNTHETIC_LOCK_KEY = 7250209


@dataclass(frozen=True)
class SyntheticEntry:
    work_id: UUID
    current_status: str
    rating_half_steps: int | None


@dataclass(frozen=True)
class SyntheticUser:
    archetype: str
    label: str
    ordinal: int
    seed_key: str
    entries: tuple[SyntheticEntry, ...]


@dataclass(frozen=True)
class SyntheticPopulation:
    seed: int
    corpus_version: str | None
    users: tuple[SyntheticUser, ...]

    @property
    def cold_start_users(self) -> tuple[SyntheticUser, ...]:
        return tuple(user for user in self.users if len(user.entries) <= 3)


@dataclass(frozen=True)
class _WorkCandidate:
    work_id: UUID
    genres: frozenset[str]
    first_release_date: date | None


class SyntheticGenerationError(ValueError):
    """Raised before writes when the corpus cannot satisfy the scenario."""


def _work_candidates(corpus_version: str | None) -> list[_WorkCandidate]:
    works = evaluation_candidate_works(corpus_version).prefetch_related("genres").order_by("id")
    return [
        _WorkCandidate(
            work_id=work.id,
            genres=frozenset(genre.slug for genre in work.genres.all()),
            first_release_date=work.first_release_date,
        )
        for work in works
    ]


def _rating(rng: random.Random, generosity: str) -> int | None:
    if rng.random() < 0.15:
        return None
    ranges = {"severe": (2, 7), "medium": (4, 9), "generous": (6, 10)}
    low, high = ranges.get(generosity, ranges["medium"])
    return rng.randint(low, high)


def _pool_for(
    archetype: Archetype,
    preferred: set[str],
    works: list[_WorkCandidate],
) -> list[_WorkCandidate]:
    matching = [work for work in works if work.genres.intersection(preferred)]
    if len(matching) < archetype.library_size_range[1]:
        matching = works
    if archetype.saga_concentration and preferred:
        saga_genre = sorted(preferred)[0]
        saga = [work for work in matching if saga_genre in work.genres]
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
    works = _work_candidates(corpus_version)
    if not works:
        raise SyntheticGenerationError("the governed corpus contains no works")

    available_genres = sorted({genre for work in works for genre in work.genres})
    users: list[SyntheticUser] = []
    for archetype in selected:
        archetype_rng = random.Random(f"{seed}:{archetype.name}")
        min_genres, max_genres = archetype.genre_pref_range
        genre_count = min(archetype_rng.randint(min_genres, max_genres), len(available_genres))
        preferred = set(archetype_rng.sample(available_genres, genre_count)) if genre_count else set()
        pool = _pool_for(archetype, preferred, works)
        for ordinal in range(1, archetype.n_users + 1):
            user_rng = random.Random(f"{seed}:{archetype.name}:{ordinal}")
            min_size, max_size = archetype.library_size_range
            requested_size = user_rng.randint(min_size, max_size)
            if archetype.cold_start:
                requested_size = user_rng.randint(1, 3)
            if requested_size > len(pool):
                raise SyntheticGenerationError(
                    f"corpus has {len(pool)} candidates but {archetype.name} needs {requested_size}"
                )
            chosen = user_rng.sample(pool, requested_size)
            states = list(archetype.status_mix)
            weights = list(archetype.status_mix.values())
            entries = [
                SyntheticEntry(
                    work_id=work.work_id,
                    current_status=user_rng.choices(states, weights=weights, k=1)[0],
                    rating_half_steps=_rating(user_rng, archetype.rating_generosity),
                )
                for work in chosen
            ]
            _ensure_positive(entries)
            users.append(
                SyntheticUser(
                    archetype=archetype.name,
                    label=archetype.label,
                    ordinal=ordinal,
                    seed_key=f"synthetic-{archetype.name}-{ordinal}",
                    entries=tuple(entries),
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
        if not user.entries:
            raise SyntheticGenerationError("every synthetic user needs at least one library entry")
        if len({entry.work_id for entry in user.entries}) != len(user.entries):
            raise SyntheticGenerationError("a synthetic user cannot contain duplicate works")
        if not any(
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
    user_model = get_user_model()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [SYNTHETIC_LOCK_KEY])
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
            anchor_ids.append(str(anchor_id))
    return {"created": created, "updated": updated, "anchor_ids": anchor_ids}


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
        f"- Cohorte cold-start (1–3 juegos): **{len(population.cold_start_users)}**",
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
            "La misma semilla, versión de corpus y especificación de arquetipos deben producir los mismos identificadores de obra, estados y valoraciones. La cohorte cold-start se mantiene separada para evaluar el enrutamiento con historial insuficiente. La generación no incorpora datos personales ni pretende estimar la distribución de jugadores reales.",
            "",
        ]
    )
    return "\n".join(lines)


def default_report_path() -> Path:
    return Path(settings.BASE_DIR).parent.parent / "docs" / "verification" / "synthetic-users-validation.md"
