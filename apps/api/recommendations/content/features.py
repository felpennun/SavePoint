"""Per-work content feature vectors and the corpus rating statistic (D-11/D-13).

A feature vector is a sparse ``{feature_key: weight}`` dict over a governed
``GameWork``. Facets have a deliberately descending semantic importance:

* ``genre:<slug>``  -- weight 0.50; guaranteed for every governed work.
* ``platform:<slug>`` -- weight 0.25; allowlist platforms only.
* ``franchise:<slug>`` -- weight 0.15; IGDB saga signal when present.
* ``developer:<slug>`` -- weight 0.10; emitted when the governed
  view contains the facet. Franchise is the IGDB saga signal and has no
  minimum coverage gate: missing saga data is omitted per work. Developer
  coverage retains its 50 % gate (D-11).

Within each facet the configured facet weight is divided by ``sqrt(k)`` for
``k`` keys in that facet, so a work with many values in one family does not
dominate the cosine numerator.

The **rating term is NOT a vector dimension** (threat T-02-10-01). The
corpus-level genre rating statistic lives in :func:`genre_rating_profile`,
read from the frozen ``CorpusRatingSnapshot`` for a ``corpus_version`` and
consumed by ``combine.py`` (Plan 02-11) -- never ``GameWork.total_rating``.
"""

from __future__ import annotations

import math
from datetime import date

from django.db.models import Count

from catalogue.corpus import ALLOWLIST_SLUGS, evaluation_candidate_works, governed_works
from catalogue.models import CorpusPopularitySnapshot, CorpusRatingSnapshot, GameWork, Genre
from catalogue.popularity import IGDB_ENGAGEMENT_TYPES

# Bump when the vector-building or similarity rules change (part of the DTO,
# REC-09). fs-v6 keeps the weighted sparse features but the ranker now compares
# user-facing facet affinity instead of applying cosine directly to the raw
# vector. Cached rows from earlier contracts must not be reused.
FEATURE_SET_VERSION = "fs-v6"

# Shared scalar-signal contract. The product workers and offline runner both
# call the same ranker, so this version is included in the published
# configuration fingerprint whenever the transformation changes.
RATING_SIGNAL_VERSION = "rating-confidence-v2"
RATING_QUALITY_POWER = 2.0
RATING_VOLUME_BOOST = 0.20
RATING_VOLUME_FLOOR = 1.0 - RATING_VOLUME_BOOST

# These weights express the semantic hierarchy of the content signal. fs-v6
# uses genre/platform as the core and saga/developer as bounded confirmation
# bonuses. They remain part of the versioned contract, not request-time tuning
# parameters.
FACET_WEIGHTS: dict[str, float] = {
    "genre": 0.50,
    "platform": 0.25,
    "franchise": 0.15,
    "developer": 0.10,
}

# Saga/franchise is semantically meaningful even when sparse; absent facets are
# omitted from each work vector instead of excluding the whole signal family.
FRANCHISE_COVERAGE_THRESHOLD = 0.0
# D-11: developer remains gated at 50 % because its sparse coverage is treated
# differently from the explicitly requested saga signal.
DEVELOPER_COVERAGE_THRESHOLD = 0.5


def _facet_weight(facet: str, count: int) -> float:
    """Return the configured family weight split across its observed values."""

    return FACET_WEIGHTS[facet] / math.sqrt(count) if count else 0.0


def _genre_slugs(work: GameWork) -> list[str]:
    return sorted({genre.slug for genre in work.genres.all()})


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


def feature_vector(
    work: GameWork,
    *,
    include_franchise: bool = False,
    include_developer: bool = False,
    feature_set_version: str = FEATURE_SET_VERSION,  # noqa: ARG001  (reserved for future schemes)
) -> dict[str, float]:
    """Return the sparse content feature vector for ``work``.

    ``include_franchise`` / ``include_developer`` are honoured only when the
    underlying data exists; with no data (this phase) they are no-ops.
    """

    vector: dict[str, float] = {}

    genre_slugs = _genre_slugs(work)
    genre_weight = _facet_weight("genre", len(genre_slugs))
    for slug in genre_slugs:
        vector[f"genre:{slug}"] = genre_weight

    platform_slugs = _platform_slugs(work)
    platform_weight = _facet_weight("platform", len(platform_slugs))
    for slug in platform_slugs:
        vector[f"platform:{slug}"] = platform_weight

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


def coverage_report(corpus_version: str | None = None) -> dict:
    """Measure facet coverage and decide which signal families are emitted.

    IGDB ``franchise`` is the saga signal and is included whenever at least one
    governed work carries it; missing values remain sparse rather than imputed.
    Developer keeps the documented 50 % coverage gate.
    """

    works = governed_works(corpus_version)
    total = works.count()
    candidate_count = evaluation_candidate_works(corpus_version).count()
    genre_present = works.filter(genres__isnull=False).distinct().count()
    platform_present = works.filter(
        releases__platform__slug__in=ALLOWLIST_SLUGS
    ).distinct().count()
    franchise_present = works.filter(franchises__isnull=False).distinct().count()
    developer_present = works.filter(developers__isnull=False).distinct().count()

    franchise_coverage = franchise_present / total if total else 0.0
    developer_coverage = developer_present / total if total else 0.0

    snapshot_filter = CorpusRatingSnapshot.objects.filter(
        work_id__in=works.values("id"),
    )
    if corpus_version is not None:
        snapshot_filter = snapshot_filter.filter(corpus_version=corpus_version)
    snapshot_rating_present = snapshot_filter.filter(rating__isnull=False).values("work_id").distinct().count()
    snapshot_volume_present = snapshot_filter.filter(
        total_rating_count__isnull=False
    ).values("work_id").distinct().count()
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
        id__in=snapshot_filter.filter(rating__isnull=False).values("work_id"),
    ).distinct().count()

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
            "volume_source": "total_rating_count",
            "volume_floor": RATING_VOLUME_FLOOR,
            "volume_boost": RATING_VOLUME_BOOST,
        },
        "governed_count": total,
        "algorithm_candidate_count": candidate_count,
        "feature_coverage": {
            "genres": field_coverage(genre_present),
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
            "external_user_rating_snapshot": "genre-median fallback when absent",
            "rating_volume_snapshot": "missing signal excluded and active weights renormalized",
            "release_recency": "missing, future, or unrated release returns null",
            "popscore_complete": "missing primitive excludes composed PopScore",
        },
    }


def normalise_rating(value: float | None) -> float | None:
    """Return a linear IGDB rating in ``[0, 1]`` without imputing absence."""

    if value is None or not math.isfinite(value):
        return None
    return max(0.0, min(1.0, value / 100.0))


def rating_quality_signal(value: float | None) -> float | None:
    """Emphasise high IGDB ratings while preserving the bounded scale."""

    normalised = normalise_rating(value)
    return None if normalised is None else normalised**RATING_QUALITY_POWER


def compose_rating_confidence(
    rating_quality: float | None,
    rating_volume: float | None,
) -> float | None:
    """Combine quality and volume without letting volume replace quality.

    ``rating_volume`` is already the corpus-view-normalised logarithmic
    ``total_rating_count`` signal. Missing volume leaves the quality signal
    unchanged; otherwise volume can boost it within a fixed 20% band.
    """

    if rating_quality is None:
        return None
    quality = max(0.0, min(1.0, rating_quality))
    if rating_volume is None:
        return quality
    volume = max(0.0, min(1.0, rating_volume))
    return quality * (RATING_VOLUME_FLOOR + RATING_VOLUME_BOOST * volume)


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


def genre_rating_profile(corpus_version: str | None = None) -> dict[str, float]:
    """Mean external rating per genre over governed works that carry a
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

    through = GameWork.genres.through
    genre_slug_by_id = dict(Genre.objects.values_list("id", "slug"))
    buckets: dict[str, list[float]] = {}
    for work_id, genre_id in through.objects.filter(
        gamework_id__in=work_rating
    ).values_list("gamework_id", "genre_id"):
        slug = genre_slug_by_id.get(genre_id)
        if slug is not None:
            buckets.setdefault(slug, []).append(work_rating[work_id])

    return {
        slug: math.fsum(values) / len(values) for slug, values in buckets.items()
    }
