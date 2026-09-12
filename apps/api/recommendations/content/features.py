"""Per-work content feature vectors and the corpus rating statistic (D-11/D-13).

A feature vector is a sparse ``{feature_key: weight}`` dict over a governed
``GameWork``. fs-v13 splits the former single curated-tag bucket into four
independently-weighted families, each with its own smoothed IDF, plus the
existing platform/franchise/developer facets:

* ``tag:<slug>``  -- weight 0.60; genre + subgenre merged (the primary taste
  axis: a subgenre like Souls-like is a genuine refinement of a genre like
  RPG, not a competing signal, so the two share one IDF-weighted bucket).
* ``theme:<slug>`` -- weight 0.20; mood/setting (Horror, Fantasy, Sci-fi...).
* ``feature:<slug>`` -- weight 0.10; format/technical descriptors (Open
  World, VR, Retro...).
* ``mode:<slug>`` -- weight 0.05; social context (Singleplayer, Co-op...).
* ``platform:<slug>`` -- weight 0.05; allowlist platforms only.
* ``franchise:<slug>`` -- weight 0.02; IGDB saga signal when present.
* ``developer:<slug>`` -- weight 0.015; emitted when the governed
  view contains the facet. Franchise is the IGDB saga signal and has no
  minimum coverage gate: missing saga data is omitted per work. Developer
  coverage retains its 50 % gate (D-11).

``tag`` and ``platform`` are the two CORE facets in ``similarity.py``'s
``facet_similarity()``: their weighted affinities are averaged, renormalised
over whichever of the two is present on both sides of a comparison. Theme,
mode, feature, franchise, and developer are OPTIONAL/bonus facets: a match
only ever adds to the score, and an absent value on either side contributes
neither a bonus nor a penalty -- it is excluded from that comparison
entirely, never folded into core's renormalised denominator. This is a
deliberate correction (2026-09-12, author-caught): an earlier design that put
all five families into one renormalised core pool let a work missing rarer
metadata (say, no theme) look *relatively* stronger on genre alone than an
equally-genre-matched work that also carries a theme -- rewarding sparse
metadata instead of staying neutral to it. Keeping only near-universal-
coverage facets (tag, platform) in the renormalised core avoids that bias:
genre is measured the same way regardless of what else a work happens to
have tagged.

Within each family, smoothed inverse document frequency (IDF) gives rare
curated values more weight than generic ones, scoped to that family's OWN
population (see :func:`_compute_family_idf_profile`) -- not the whole
governed corpus, or a sparsely-covered family like ``feature`` would look
artificially rarer (and so more heavily weighted) than its true population
warrants. The resulting per-family values are L2-normalised to that family's
configured weight, so e.g. the complete tag block remains 0.60 regardless of
the number or rarity of a work's genre/subgenre tags. Franchise and developer
continue to divide their configured family weight by ``sqrt(k)`` for ``k``
observed keys (no IDF -- see ``exact_match_scale`` in ``similarity.py``).

The **rating term is NOT a vector dimension** (threat T-02-10-01). The
corpus-level genre rating statistic lives in :func:`genre_rating_profile`,
read from the frozen ``CorpusRatingSnapshot`` for a ``corpus_version`` and
consumed by ``combine.py`` (Plan 02-11) -- never ``GameWork.total_rating``.
"""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from datetime import date
from functools import lru_cache
from typing import Callable, Iterator

from django.db.models import Count, Exists, OuterRef

from catalogue.corpus import ALLOWLIST_SLUGS, evaluation_candidate_works, governed_works
from catalogue.models import (
    CorpusPopularitySnapshot,
    CorpusRatingSnapshot,
    CuratedLabel,
    GameRelease,
    GameWork,
)
from catalogue.popularity import IGDB_ENGAGEMENT_TYPES

# Bump when the vector-building or similarity rules change (part of the DTO,
# REC-09). fs-v13 splits the former single curated-tag bucket (fs-v12) into
# tag (genre+subgenre)/theme/mode/feature, each with its own IDF, and gives
# platform its own IDF instead of a flat 1/sqrt(k) split. Cached rows from
# earlier contracts must not be reused.
FEATURE_SET_VERSION = "fs-v13-family-weighted-tags"

# Shared scalar-signal contract. The product workers and offline runner both
# call the same ranker, so this version is included in the published
# configuration fingerprint whenever the transformation changes.
RATING_SIGNAL_VERSION = "rating-confidence-v5-final"
RATING_QUALITY_POWER = 2.0
# Equivalent pseudo-observations used to shrink a sparse candidate rating
# towards the frozen corpus mean.  It is deliberately a fixed contract value,
# never a request-time or user-specific tuning parameter.
RATING_BAYESIAN_PRIOR_COUNT = 25.0
RATING_CONFIDENCE_PRIOR_COUNT = RATING_BAYESIAN_PRIOR_COUNT

# These weights express the semantic hierarchy of the content signal
# (2026-09-12 author decision, fs-v13): genre+subgenre anchors taste: theme,
# mode, and feature are bounded confirmation bonuses layered on top -- the
# same bonus treatment franchise/developer already had, just with different
# maxima -- and platform is a minor core tie-break, not a taste signal in its
# own right. They remain part of the versioned contract, not request-time
# tuning parameters.
FACET_WEIGHTS: dict[str, float] = {
    "tag": 0.60,
    "theme": 0.20,
    "feature": 0.10,
    "mode": 0.05,
    "platform": 0.05,
    "franchise": 0.02,
    "developer": 0.015,
}

# Which CuratedLabel.Kind values feed which similarity family. Genre and
# subgenre share the "tag" family/vector-namespace deliberately: a subgenre
# is a refinement of a genre, not a competing signal (author decision,
# 2026-09-12) -- see the module docstring.
_FAMILY_KINDS: dict[str, tuple[str, ...]] = {
    "tag": (CuratedLabel.Kind.GENRE, CuratedLabel.Kind.SUBGENRE),
    "theme": (CuratedLabel.Kind.THEME,),
    "mode": (CuratedLabel.Kind.MODE,),
    "feature": (CuratedLabel.Kind.FEATURE,),
}
_KIND_TO_FAMILY: dict[str, str] = {
    kind: family for family, kinds in _FAMILY_KINDS.items() for kind in kinds
}

# IDF is frozen per governed corpus version and is part of the feature-set
# contract. Additive smoothing keeps every observed tag finite, including a
# tag that appears in exactly one work.
TAG_IDF_FORMULA_VERSION = "smoothed-idf-l2-per-family-v2"
TAG_IDF_SMOOTHING = 1.0

# Saga/franchise is semantically meaningful even when sparse; absent facets are
# omitted from each work vector instead of excluding the whole signal family.
FRANCHISE_COVERAGE_THRESHOLD = 0.0
# D-11: developer remains gated at 50 % because its sparse coverage is treated
# differently from the explicitly requested saga signal.
DEVELOPER_COVERAGE_THRESHOLD = 0.5

@contextmanager
def _feature_stats_lock() -> Iterator[None]:
    """Keep the statistics hook cheap; immutable values are process-cached."""

    # The previous advisory lock serialized all workers behind one expensive
    # report. The EXISTS-based queries below are independent and the long-lived
    # workers cache their corpus-version result, so no database lock is needed.
    yield


def _facet_weight(facet: str, count: int) -> float:
    """Return the configured family weight split across its observed values."""

    return FACET_WEIGHTS[facet] / math.sqrt(count) if count else 0.0


def _curated_slugs_by_family(work: GameWork) -> dict[str, list[str]]:
    """Group a work's curated-label evidence into its similarity families.

    ``GameWorkCuratedLabel`` is an evidence table: more than one row can
    exist for the same (work, label) pair when independent curation sources
    agree (see catalogue/serializers.py::_tags) -- this dedupes by slug per
    family before returning, so a doubly-evidenced value is never counted
    twice building the vector.
    """

    by_family: dict[str, set[str]] = {}
    for label in work.curated_labels.all():
        family = _KIND_TO_FAMILY.get(label.kind)
        if family is None:
            continue
        by_family.setdefault(family, set()).add(label.slug)
    return {family: sorted(slugs) for family, slugs in by_family.items()}


def _tag_slugs(work: GameWork) -> list[str]:
    """Genre + subgenre only -- see ``_FAMILY_KINDS["tag"]``."""

    return _curated_slugs_by_family(work).get("tag", [])


def _compute_family_idf_profile(
    kinds: tuple[str, ...], corpus_version: str | None
) -> dict[str, float]:
    """Smoothed IDF for one CuratedLabel-based similarity family.

    ``N`` is the number of governed works carrying at least one label from
    THIS family, not the whole governed corpus (2026-09-12 author decision):
    scoring a sparsely-covered family like ``feature`` (~13% coverage)
    against the full corpus size would inflate its IDF values relative to a
    near-universal family like ``tag``, purely because the reference
    population is the wrong size for that family, not because its values are
    genuinely rarer.
    """

    with _feature_stats_lock():
        works = governed_works(corpus_version)
        family_label_ids = set(
            CuratedLabel.objects.filter(kind__in=kinds).values_list("id", flat=True)
        )
        if not family_label_ids:
            return {}

        through = GameWork.curated_labels.through
        rows = (
            through.objects.filter(
                work_id__in=works.values("id"), label_id__in=family_label_ids
            )
            .values("work_id", "label_id")
            .distinct()
        )
        document_frequency: dict[object, int] = {}
        works_with_family: set[object] = set()
        for row in rows:
            label_id = row["label_id"]
            document_frequency[label_id] = document_frequency.get(label_id, 0) + 1
            works_with_family.add(row["work_id"])
        document_count = len(works_with_family)
        if not document_count:
            return {}

        slug_by_id = dict(
            CuratedLabel.objects.filter(id__in=family_label_ids).values_list("id", "slug")
        )
        return {
            slug_by_id[label_id]: math.log(
                (document_count + TAG_IDF_SMOOTHING) / (df + TAG_IDF_SMOOTHING)
            )
            + 1.0
            for label_id, df in document_frequency.items()
            if label_id in slug_by_id
        }


def _compute_platform_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Smoothed IDF for allowlisted platforms, scoped the same way as
    :func:`_compute_family_idf_profile` -- ``N`` is governed works with at
    least one allowlisted release, not the whole corpus."""

    with _feature_stats_lock():
        works = governed_works(corpus_version)
        rows = (
            GameRelease.objects.filter(
                work_id__in=works.values("id"), platform__slug__in=ALLOWLIST_SLUGS
            )
            .values("work_id", "platform__slug")
            .distinct()
        )
        document_frequency: dict[str, int] = {}
        works_with_platform: set[object] = set()
        for row in rows:
            slug = row["platform__slug"]
            document_frequency[slug] = document_frequency.get(slug, 0) + 1
            works_with_platform.add(row["work_id"])
        document_count = len(works_with_platform)
        if not document_count:
            return {}
        return {
            slug: math.log((document_count + TAG_IDF_SMOOTHING) / (df + TAG_IDF_SMOOTHING)) + 1.0
            for slug, df in document_frequency.items()
        }


def _compute_tag_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    return _compute_family_idf_profile(_FAMILY_KINDS["tag"], corpus_version)


def _compute_theme_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    return _compute_family_idf_profile(_FAMILY_KINDS["theme"], corpus_version)


def _compute_mode_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    return _compute_family_idf_profile(_FAMILY_KINDS["mode"], corpus_version)


def _compute_feature_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    return _compute_family_idf_profile(_FAMILY_KINDS["feature"], corpus_version)


@lru_cache(maxsize=8)
def _cached_tag_idf_profile(corpus_version: str | None) -> dict[str, float]:
    return _compute_tag_idf_profile(corpus_version)


@lru_cache(maxsize=8)
def _cached_theme_idf_profile(corpus_version: str | None) -> dict[str, float]:
    return _compute_theme_idf_profile(corpus_version)


@lru_cache(maxsize=8)
def _cached_mode_idf_profile(corpus_version: str | None) -> dict[str, float]:
    return _compute_mode_idf_profile(corpus_version)


@lru_cache(maxsize=8)
def _cached_feature_idf_profile(corpus_version: str | None) -> dict[str, float]:
    return _compute_feature_idf_profile(corpus_version)


@lru_cache(maxsize=8)
def _cached_platform_idf_profile(corpus_version: str | None) -> dict[str, float]:
    return _compute_platform_idf_profile(corpus_version)


def _cached_or_computed(
    compute: Callable[[str | None], dict[str, float]],
    cached: Callable[[str | None], dict[str, float]],
    corpus_version: str | None,
) -> dict[str, float]:
    if os.environ.get("SAVEPOINT_RECOMMENDATION_STATS_CACHE") == "1":
        return dict(cached(corpus_version))
    return compute(corpus_version)


def tag_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Return genre+subgenre IDF values, cached only by long-lived workers."""

    return _cached_or_computed(_compute_tag_idf_profile, _cached_tag_idf_profile, corpus_version)


def theme_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Return theme IDF values, cached only by long-lived workers."""

    return _cached_or_computed(_compute_theme_idf_profile, _cached_theme_idf_profile, corpus_version)


def mode_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Return mode IDF values, cached only by long-lived workers."""

    return _cached_or_computed(_compute_mode_idf_profile, _cached_mode_idf_profile, corpus_version)


def feature_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Return feature IDF values, cached only by long-lived workers."""

    return _cached_or_computed(_compute_feature_idf_profile, _cached_feature_idf_profile, corpus_version)


def platform_idf_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Return platform IDF values, cached only by long-lived workers."""

    return _cached_or_computed(_compute_platform_idf_profile, _cached_platform_idf_profile, corpus_version)


def all_family_idf_profiles(corpus_version: str | None = None) -> dict[str, dict[str, float]]:
    """Convenience bundle of all five per-family IDF profiles at once, for
    callers that precompute and thread every family through a batch ranking
    pass (mirrors the historical single ``tag_idf`` threading pattern)."""

    return {
        "tag": tag_idf_profile(corpus_version),
        "theme": theme_idf_profile(corpus_version),
        "mode": mode_idf_profile(corpus_version),
        "feature": feature_idf_profile(corpus_version),
        "platform": platform_idf_profile(corpus_version),
    }


def _platform_slugs(work: GameWork) -> list[str]:
    return sorted(
        {
            release.platform.slug
            for release in work.releases.all()
            if release.platform is not None and release.platform.slug in ALLOWLIST_SLUGS
        }
    )


def _franchise_slugs(work: GameWork) -> list[str]:
    return sorted({franchise.slug for franchise in work.franchises.all()})


def _developer_slugs(work: GameWork) -> list[str]:
    return sorted({developer.slug for developer in work.developers.all()})


def _family_vector_block(
    slugs: list[str], facet: str, idf: dict[str, float] | None
) -> dict[str, float]:
    """Shared IDF-weighted, L2-normalised-to-budget block for one facet.

    With an IDF profile, values are weighted by rarity and L2-normalised so
    the family's contribution stays at its configured ``FACET_WEIGHTS``
    budget regardless of how many or how rare a work's own values are.
    Without one (flat fallback, matches pre-fs-v9 behaviour for isolated
    callers with no corpus context), the budget just splits evenly by
    ``1/sqrt(k)``.
    """

    if not slugs:
        return {}
    if idf:
        idf_values = {slug: max(float(idf.get(slug, 1.0)), 0.0) for slug in slugs}
        idf_norm = math.sqrt(math.fsum(value * value for value in idf_values.values()))
        if not idf_norm:
            return {}
        return {
            slug: FACET_WEIGHTS[facet] * value / idf_norm for slug, value in idf_values.items()
        }
    weight = _facet_weight(facet, len(slugs))
    return {slug: weight for slug in slugs}


def feature_vector(
    work: GameWork,
    *,
    include_franchise: bool = False,
    include_developer: bool = False,
    tag_idf: dict[str, float] | None = None,
    theme_idf: dict[str, float] | None = None,
    mode_idf: dict[str, float] | None = None,
    feature_idf: dict[str, float] | None = None,
    platform_idf: dict[str, float] | None = None,
    feature_set_version: str = FEATURE_SET_VERSION,  # noqa: ARG001  (reserved for future schemes)
) -> dict[str, float]:
    """Return the sparse content feature vector for ``work``.

    ``include_franchise`` / ``include_developer`` are honoured only when the
    underlying data exists; with no data (this phase) they are no-ops.
    """

    vector: dict[str, float] = {}
    by_family = _curated_slugs_by_family(work)

    for slug, value in _family_vector_block(by_family.get("tag", []), "tag", tag_idf).items():
        vector[f"tag:{slug}"] = value
    for slug, value in _family_vector_block(by_family.get("theme", []), "theme", theme_idf).items():
        vector[f"theme:{slug}"] = value
    for slug, value in _family_vector_block(by_family.get("mode", []), "mode", mode_idf).items():
        vector[f"mode:{slug}"] = value
    for slug, value in _family_vector_block(
        by_family.get("feature", []), "feature", feature_idf
    ).items():
        vector[f"feature:{slug}"] = value

    platform_slugs = _platform_slugs(work)
    for slug, value in _family_vector_block(platform_slugs, "platform", platform_idf).items():
        vector[f"platform:{slug}"] = value

    if include_franchise:
        franchise_slugs = _franchise_slugs(work)
        franchise_weight = _facet_weight("franchise", len(franchise_slugs))
        for slug in franchise_slugs:
            vector[f"franchise:{slug}"] = franchise_weight

    if include_developer:
        developer_slugs = _developer_slugs(work)
        developer_weight = _facet_weight("developer", len(developer_slugs))
        for slug in developer_slugs:
            vector[f"developer:{slug}"] = developer_weight

    return vector


def _compute_coverage_report(corpus_version: str | None = None) -> dict:
    """Measure facet coverage and decide which signal families are emitted.

    IGDB ``franchise`` is the saga signal and is included whenever at least one
    governed work carries it; missing values remain sparse rather than imputed.
    Developer keeps the documented 50 % coverage gate.
    """

    with _feature_stats_lock():
        works = governed_works(corpus_version)
        total = works.count()
        candidate_count = evaluation_candidate_works(corpus_version).count()

        # These used to be JOIN + DISTINCT counts over every GameWork column.
        # EXISTS keeps the count on the indexed GameWork primary key and avoids
        # materialising duplicate joined rows for multi-valued facets.
        tag_present = works.filter(
            Exists(GameWork.objects.filter(pk=OuterRef("pk"), curated_labels__isnull=False))
        ).count()
        platform_present = works.filter(
            Exists(
                GameWork.objects.filter(
                    pk=OuterRef("pk"),
                    releases__platform__slug__in=ALLOWLIST_SLUGS,
                )
            )
        ).count()
        franchise_present = works.filter(
            Exists(GameWork.objects.filter(pk=OuterRef("pk"), franchises__isnull=False))
        ).count()
        developer_present = works.filter(
            Exists(GameWork.objects.filter(pk=OuterRef("pk"), developers__isnull=False))
        ).count()

        snapshot_filter = CorpusRatingSnapshot.objects.filter(
            work_id=OuterRef("pk"),
        )
        if corpus_version is not None:
            snapshot_filter = snapshot_filter.filter(corpus_version=corpus_version)
        snapshot_rating_exists = snapshot_filter.filter(rating__isnull=False)
        snapshot_volume_exists = snapshot_filter.filter(total_rating_count__isnull=False)
        snapshot_rating_present = works.filter(Exists(snapshot_rating_exists)).count()
        snapshot_volume_present = works.filter(Exists(snapshot_volume_exists)).count()
        popscore_present = (
            CorpusPopularitySnapshot.objects.filter(
                corpus_version=corpus_version,
                work_id__in=works.values("id"),
                popularity_type_name__in=IGDB_ENGAGEMENT_TYPES,
                normalised_value__isnull=False,
            )
            .values("work_id")
            .annotate(type_count=Count("popularity_type_name", distinct=True))
            .filter(type_count=len(IGDB_ENGAGEMENT_TYPES))
            .count()
        )
        dated_and_rated = works.filter(
            first_release_date__isnull=False,
            first_release_date__lte=date.today(),
        ).filter(Exists(snapshot_rating_exists)).count()

        franchise_coverage = franchise_present / total if total else 0.0
        developer_coverage = developer_present / total if total else 0.0

    def field_coverage(present: int) -> dict[str, int | float]:
        return {
            "present": present,
            "missing": max(total - present, 0),
            "coverage": present / total if total else 0.0,
        }

    return {
        "corpus_version": corpus_version,
        "feature_set_version": FEATURE_SET_VERSION,
        "facet_weights": FACET_WEIGHTS,
        "rating_signal": {
            "version": RATING_SIGNAL_VERSION,
            "quality_power": RATING_QUALITY_POWER,
            "prior_source": "total_rating_count_weighted_frozen_corpus_mean",
            "prior_count": RATING_BAYESIAN_PRIOR_COUNT,
            "observation_count_source": "total_rating_count",
        },
        "family_idf": {
            "formula_version": TAG_IDF_FORMULA_VERSION,
            "smoothing": TAG_IDF_SMOOTHING,
            "document_count_definition": "governed works carrying >=1 value from that family (not the whole corpus)",
            "document_frequency_definition": "governed works (within that family's own population) carrying the value",
        },
        "governed_count": total,
        "algorithm_candidate_count": candidate_count,
        "feature_coverage": {
            "tags": field_coverage(tag_present),
            "platforms": field_coverage(platform_present),
            "franchises": field_coverage(franchise_present),
            "developers": field_coverage(developer_present),
        },
        "scalar_signal_coverage": {
            "external_user_rating_snapshot": field_coverage(snapshot_rating_present),
            "rating_volume_snapshot": field_coverage(snapshot_volume_present),
            "release_recency": field_coverage(dated_and_rated),
            "popscore_complete": field_coverage(popscore_present),
        },
        "franchise_present": franchise_present,
        "developer_present": developer_present,
        "franchise_coverage": franchise_coverage,
        "developer_coverage": developer_coverage,
        "franchise_threshold": FRANCHISE_COVERAGE_THRESHOLD,
        "developer_threshold": DEVELOPER_COVERAGE_THRESHOLD,
        "include_franchise": franchise_present > 0,
        "include_developer": developer_coverage >= DEVELOPER_COVERAGE_THRESHOLD,
        # These scalar families deliberately stay outside cosine similarity.
        # A raw primitive snapshot is deliberately not an aggregate score.
        # Composition and its recommender weight require a later approved
        # variant, never an ad-hoc request-time calculation.
        "popscore_primitives_available": CorpusPopularitySnapshot.objects.filter(
            corpus_version=corpus_version
        ).exists(),
        "rating_available": snapshot_rating_present > 0,
        "rating_volume_available": snapshot_volume_present > 0,
        "release_recency_available": dated_and_rated > 0,
        "popscore_available": popscore_present > 0,
        "null_handling": {
            "categorical_features": "missing facet omitted from sparse vector",
            "external_user_rating_snapshot": "genre-median fallback only when candidate rating is absent",
            "rating_volume_snapshot": "reported as evidence only; Bayesian shrinkage uses total_rating_count",
            "release_recency": "missing, future, or unrated release returns null",
            "popscore_complete": "missing primitive excludes composed PopScore",
        },
    }


@lru_cache(maxsize=8)
def _cached_coverage_report(corpus_version: str | None) -> dict:
    return _compute_coverage_report(corpus_version)


def coverage_report(corpus_version: str | None = None) -> dict:
    """Return coverage, cached only by long-lived worker processes."""

    if os.environ.get("SAVEPOINT_RECOMMENDATION_STATS_CACHE") == "1":
        return dict(_cached_coverage_report(corpus_version))
    return _compute_coverage_report(corpus_version)


def normalise_rating(value: float | None) -> float | None:
    """Return a linear IGDB rating in ``[0, 1]`` without imputing absence."""

    if value is None or not math.isfinite(value):
        return None
    return max(0.0, min(1.0, value / 100.0))


def rating_quality_signal(value: float | None) -> float | None:
    """Return the legacy raw-rating adapter for ``rating_quality``."""

    return rating_quality(normalise_rating(value))


def rating_bayesian_normalized(
    rating: float | None,
    total_rating_count: int | None,
    prior_mean: float | None,
) -> float | None:
    """Return the frozen Bayesian IGDB rating on the normalized scale."""

    return normalise_rating(bayesian_rating(rating, total_rating_count, prior_mean))


def rating_quality(rating_bayesian_normalized: float | None) -> float | None:
    """Emphasize high Bayesian ratings without leaving the ``[0, 1]`` scale."""

    if rating_bayesian_normalized is None or not math.isfinite(rating_bayesian_normalized):
        return None
    bounded = max(0.0, min(1.0, rating_bayesian_normalized))
    return bounded**RATING_QUALITY_POWER


def rating_confidence(total_rating_count: int | None) -> float:
    """Return ``n / (n + m)`` for the frozen IGDB evidence count."""

    count = max(0, total_rating_count or 0)
    return count / (count + RATING_CONFIDENCE_PRIOR_COUNT)


def rating_final(
    rating_bayesian_normalized: float | None,
    total_rating_count: int | None,
) -> float | None:
    """Combine Bayesian quality and evidence confidence exactly once."""

    quality = rating_quality(rating_bayesian_normalized)
    return None if quality is None else quality * rating_confidence(total_rating_count)


def bayesian_rating(
    rating: float | None,
    total_rating_count: int | None,
    prior_mean: float | None,
) -> float | None:
    """Shrink a candidate IGDB rating towards the frozen corpus mean.

    The formula is the standard empirical-Bayes weighted mean:
    ``(n * rating + m * prior_mean) / (n + m)``, where ``n`` is the
    candidate's IGDB ``total_rating_count`` and ``m`` is the fixed prior
    count.  Missing observations remain missing; they are not silently
    converted into a quality signal.
    """

    if rating is None or not math.isfinite(rating):
        return None
    if prior_mean is None or not math.isfinite(prior_mean):
        return rating
    count = max(0, total_rating_count or 0)
    return ((count * rating) + (RATING_BAYESIAN_PRIOR_COUNT * prior_mean)) / (
        count + RATING_BAYESIAN_PRIOR_COUNT
    )


def compose_rating_confidence(
    rating_quality: float | None,
    rating_volume: float | None,
) -> float | None:
    """Return a legacy candidate term without applying volume a second time.

    ``rating_volume`` remains an explainability field in existing DTOs, but
    must not be applied a second time: its raw count has already determined
    the Bayesian rating before the quality transformation.
    """

    if rating_quality is None:
        return None
    return max(0.0, min(1.0, rating_quality))


def normalise_rating_volume(value: int | None, ceiling: int | None) -> float | None:
    """Normalise ``log1p(total_rating_count)`` against one frozen view.

    The caller supplies the maximum count observed in that view, which makes
    the value reproducible and prevents an outlier from leaking a live global
    statistic into a frozen run.
    """

    if value is None or ceiling is None or value < 0 or ceiling <= 0:
        return None
    denominator = math.log1p(ceiling)
    if denominator == 0:
        return 0.0
    return math.log1p(value) / denominator


def tag_rating_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Mean external rating per curated tag over governed works that carry a
    ``CorpusRatingSnapshot`` rating for ``corpus_version``.

    A *corpus* statistic derived from the frozen snapshot, not user data, so
    it is leakage-safe across evaluation splits (EVAL-02). Per work the rating
    is the mean of its snapshot rows (there may be more than one source); per
    genre it is the mean of its works' ratings.
    """

    governed_ids = set(
        governed_works(corpus_version).values_list("id", flat=True)
    )
    if not governed_ids:
        return {}

    snapshots = CorpusRatingSnapshot.objects.filter(
        work_id__in=governed_ids, rating__isnull=False
    )
    if corpus_version is not None:
        snapshots = snapshots.filter(corpus_version=corpus_version)

    per_work: dict[object, list[float]] = {}
    for work_id, rating in snapshots.values_list("work_id", "rating"):
        per_work.setdefault(work_id, []).append(rating)
    if not per_work:
        return {}

    work_rating = {
        work_id: math.fsum(ratings) / len(ratings)
        for work_id, ratings in per_work.items()
    }

    through = GameWork.curated_labels.through
    tag_slug_by_id = dict(CuratedLabel.objects.values_list("id", "slug"))
    buckets: dict[str, list[float]] = {}
    # GameWorkCuratedLabel is an evidence table: the same (work, label) pair
    # can carry more than one row when independent curation sources agree
    # (see catalogue/serializers.py::_tags). .distinct() collapses those back
    # to one (work, tag) pair each, or an agreed-upon work's rating would be
    # counted into the tag's average once per corroborating source instead
    # of once per work.
    for work_id, tag_id in (
        through.objects.filter(work_id__in=work_rating)
        .values_list("work_id", "label_id")
        .distinct()
    ):
        slug = tag_slug_by_id.get(tag_id)
        if slug is not None:
            buckets.setdefault(slug, []).append(work_rating[work_id])

    return {
        slug: math.fsum(values) / len(values) for slug, values in buckets.items()
    }


# Compatibility alias for historical experiment callers. New workers must use
# the curated-tag name and the ``tag:`` vector namespace.
genre_rating_profile = tag_rating_profile


def corpus_rating_prior(
    corpus_version: str | None = None,
    *,
    eligibility_cutoff_date: date | None = None,
) -> float | None:
    """Return the ``total_rating_count``-weighted IGDB corpus mean.

    This uses the immutable ``CorpusRatingSnapshot`` selected by the governed
    corpus version, so the web workers and offline runner use the same prior.
    A row without a usable count contributes one observation solely as a safe
    fallback for legacy fixture data; governed recommendation candidates have
    a count of at least five.
    """

    snapshots = CorpusRatingSnapshot.objects.filter(
        work_id__in=governed_works(
            corpus_version,
            eligibility_cutoff_date=eligibility_cutoff_date,
        ).values("id"),
        rating__isnull=False,
    )
    if corpus_version is not None:
        snapshots = snapshots.filter(corpus_version=corpus_version)

    numerator = 0.0
    denominator = 0
    for rating, total_rating_count in snapshots.values_list("rating", "total_rating_count"):
        if rating is None or not math.isfinite(rating):
            continue
        count = max(1, total_rating_count or 0)
        numerator += rating * count
        denominator += count
    return numerator / denominator if denominator else None
