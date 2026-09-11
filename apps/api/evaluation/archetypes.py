"""Parametric synthetic-user scenarios used by the frozen evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Archetype:
    """A reproducible user scenario, independent from any account credential."""

    name: str
    label: str
    n_users: int
    genre_pref_range: tuple[int, int]
    library_size_range: tuple[int, int]
    rating_generosity: str
    status_mix: dict[str, float]
    cold_start: bool = False
    no_history: bool = False
    release_bias: str | None = None
    saga_concentration: float = 0.0


PHASE_2_ARCHETYPES: tuple[Archetype, ...] = (
    Archetype(
        name="monogenero-severo", label="Monogénero severo", n_users=25,
        genre_pref_range=(1, 2), library_size_range=(5, 15), rating_generosity="severe",
        status_mix={"completed": 0.55, "playing": 0.10, "pending": 0.25, "abandoned": 0.10},
    ),
    Archetype(
        name="monogenero-generoso", label="Monogénero generoso", n_users=25,
        genre_pref_range=(1, 2), library_size_range=(5, 15), rating_generosity="generous",
        status_mix={"completed": 0.45, "playing": 0.15, "pending": 0.30, "abandoned": 0.10},
    ),
    Archetype(
        name="omnivoro-medio", label="Omnívoro medio", n_users=25,
        genre_pref_range=(5, 8), library_size_range=(20, 40), rating_generosity="medium",
        status_mix={"completed": 0.45, "playing": 0.15, "pending": 0.30, "abandoned": 0.10},
    ),
    Archetype(
        name="completista-saga", label="Completista de saga", n_users=25,
        genre_pref_range=(1, 3), library_size_range=(20, 40), rating_generosity="medium",
        status_mix={"completed": 0.70, "playing": 0.10, "pending": 0.15, "abandoned": 0.05},
        saga_concentration=0.80,
    ),
    Archetype(
        name="explorador-novedades", label="Explorador de novedades", n_users=25,
        genre_pref_range=(3, 5), library_size_range=(20, 40), rating_generosity="medium",
        status_mix={"completed": 0.25, "playing": 0.25, "pending": 0.40, "abandoned": 0.10},
        release_bias="recent",
    ),
    Archetype(
        name="coleccionista-pendientes", label="Coleccionista de pendientes", n_users=25,
        genre_pref_range=(3, 5), library_size_range=(50, 70), rating_generosity="medium",
        status_mix={"completed": 0.15, "playing": 0.10, "pending": 0.70, "abandoned": 0.05},
    ),
    Archetype(
        name="jugador-ocasional-cold-start", label="Jugador ocasional cold-start", n_users=25,
        genre_pref_range=(1, 3), library_size_range=(1, 3), rating_generosity="medium",
        status_mix={"completed": 0.45, "playing": 0.15, "pending": 0.35, "abandoned": 0.05},
        cold_start=True,
    ),
    Archetype(
        name="veterano-biblioteca-grande", label="Veterano de biblioteca grande", n_users=25,
        genre_pref_range=(5, 8), library_size_range=(50, 70), rating_generosity="generous",
        status_mix={"completed": 0.55, "playing": 0.15, "pending": 0.20, "abandoned": 0.10},
    ),
)


# Phase 3 replaces the 200-user Phase 2 evaluation population with this
# deterministic 400-user population.  The cohorts are explicit so the
# resulting manifest can be checked without inferring them from labels.
#
# Protocol v13 revision (2026-09-11): every non-`no_history` archetype now
# shares one `library_size_range` (10-20) instead of the earlier
# sparse/normal/intensive stratification (1-4 / 5-10 / 11-20). That
# stratification let leave-one-out routinely drop a user below the content
# ranker's `_COLD_START_ENTRIES` (3) threshold, collapsing most content
# variants to their non-personalised fallback for the majority of the test
# split (documented in evaluation-results-400-test-2026-09-10.md). The three
# archetypes below keep their original names and taste parameters
# (genre_pref_range, rating_generosity, status_mix, release_bias) for
# account-identity continuity across regenerations -- only their size range
# and `cold_start` flag changed; `generate()` now also draws a PopScore-tier
# and a guaranteed-eligible tier within every non-empty library (see
# synthetic.py `POPSCORE_TIER_FRACTION` / `GUARANTEED_ELIGIBLE_MINIMUM`).
DEFAULT_ARCHETYPES: tuple[Archetype, ...] = (
    Archetype(
        name="sin-historial-monogenero", label="Sin historial monogénero", n_users=5,
        genre_pref_range=(1, 2), library_size_range=(0, 0), rating_generosity="medium",
        status_mix={"pending": 1.0}, no_history=True,
    ),
    Archetype(
        name="sin-historial-omnivoro", label="Sin historial omnívoro", n_users=5,
        genre_pref_range=(5, 8), library_size_range=(0, 0), rating_generosity="medium",
        status_mix={"pending": 1.0}, no_history=True,
    ),
    Archetype(
        name="cold-start-monogenero", label="Cold-start monogénero", n_users=33,
        genre_pref_range=(1, 2), library_size_range=(10, 20), rating_generosity="severe",
        status_mix={"completed": 0.55, "pending": 0.35, "abandoned": 0.10},
    ),
    Archetype(
        name="cold-start-explorador", label="Cold-start explorador", n_users=33,
        genre_pref_range=(3, 5), library_size_range=(10, 20), rating_generosity="medium",
        status_mix={"completed": 0.35, "playing": 0.15, "pending": 0.40, "abandoned": 0.10},
        release_bias="recent",
    ),
    Archetype(
        name="cold-start-generoso", label="Cold-start generoso", n_users=34,
        genre_pref_range=(3, 6), library_size_range=(10, 20), rating_generosity="generous",
        status_mix={"completed": 0.45, "playing": 0.15, "pending": 0.35, "abandoned": 0.05},
    ),
    Archetype(
        name="normal-monogenero", label="Usuario normal monogénero", n_users=80,
        genre_pref_range=(1, 3), library_size_range=(10, 20), rating_generosity="severe",
        status_mix={"completed": 0.55, "playing": 0.10, "pending": 0.25, "abandoned": 0.10},
    ),
    Archetype(
        name="normal-omnivoro", label="Usuario normal omnívoro", n_users=80,
        genre_pref_range=(5, 8), library_size_range=(10, 20), rating_generosity="medium",
        status_mix={"completed": 0.45, "playing": 0.15, "pending": 0.30, "abandoned": 0.10},
        saga_concentration=0.35,
    ),
    Archetype(
        name="normal-explorador", label="Usuario normal explorador", n_users=80,
        genre_pref_range=(3, 5), library_size_range=(10, 20), rating_generosity="generous",
        status_mix={"completed": 0.25, "playing": 0.25, "pending": 0.40, "abandoned": 0.10},
        release_bias="recent",
    ),
    Archetype(
        name="intensivo-veterano", label="Usuario intensivo veterano", n_users=50,
        genre_pref_range=(5, 8), library_size_range=(10, 20), rating_generosity="generous",
        status_mix={"completed": 0.55, "playing": 0.15, "pending": 0.20, "abandoned": 0.10},
    ),
)


def validate_archetypes(archetypes: tuple[Archetype, ...] | list[Archetype]) -> None:
    """Validate the scenario contract before a generation can be persisted."""

    if not archetypes:
        raise ValueError("at least one synthetic-user archetype is required")
    names: set[str] = set()
    for archetype in archetypes:
        if archetype.name in names:
            raise ValueError("synthetic-user archetype names must be unique")
        names.add(archetype.name)
        if archetype.n_users < 1:
            raise ValueError("synthetic-user archetypes must contain at least one user")
        if archetype.genre_pref_range[0] < 1 or archetype.genre_pref_range[0] > archetype.genre_pref_range[1]:
            raise ValueError("invalid preferred-genre range")
        if archetype.library_size_range[0] < 0 or archetype.library_size_range[0] > archetype.library_size_range[1]:
            raise ValueError("invalid library-size range")
        if archetype.no_history and archetype.library_size_range != (0, 0):
            raise ValueError("no-history archetypes must have an empty library range")
        if not archetype.no_history and archetype.library_size_range[0] < 1:
            raise ValueError("non-empty archetypes must have at least one library entry")
        if archetype.cold_start and archetype.library_size_range[1] > 4:
            raise ValueError("cold-start archetypes must have a maximum library size of four")
        if abs(sum(archetype.status_mix.values()) - 1.0) > 1e-9:
            raise ValueError("status probabilities must sum to one")
