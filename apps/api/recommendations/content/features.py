"""Per-work content feature vectors and the corpus rating statistic (D-11/D-13).

A feature vector is a sparse ``{feature_key: weight}`` dict over a governed
``GameWork``:

* ``genre:<slug>``  -- guaranteed; every governed work has at least one genre.
* ``platform:<slug>`` -- allowlist platforms only (``catalogue.corpus``).
* ``franchise:<slug>`` / ``developer:<slug>`` -- only when measured coverage
  over the governed view clears ``FRANCHISE_COVERAGE_THRESHOLD`` /
  ``DEVELOPER_COVERAGE_THRESHOLD`` (D-11). The importer does not fetch
  ``franchises`` / ``involved_companies`` yet, so this phase measures 0 %
  coverage and emits neither -- the seam is here for when the data lands.

Within each facet the weight is ``1 / sqrt(k)`` for ``k`` keys in that facet,
so a many-genre work does not dominate the cosine numerator.

The **rating term is NOT a vector dimension** (threat T-02-10-01). The
corpus-level genre rating statistic lives in :func:`genre_rating_profile`,
read from the frozen ``CorpusRatingSnapshot`` for a ``corpus_version`` and
consumed by ``combine.py`` (Plan 02-11) -- never ``GameWork.total_rating``.
"""

from __future__ import annotations

import math

from catalogue.corpus import ALLOWLIST_SLUGS, governed_works
from catalogue.models import CorpusPopularitySnapshot, CorpusRatingSnapshot, GameWork, Genre

# Bump when the vector-building rules below change (part of the DTO, REC-09).
# v2 keeps the sparse categorical representation but makes the absence of
# unpersisted facets explicit in the signal manifest.  Cached v1 rows must not
# be reused: their provenance did not record that decision.
FEATURE_SET_VERSION = "fs-v3"

# D-11: a facet is only worth adding as a feature dimension if enough governed
# works actually carry it. 50 % is the documented floor -- below it the facet
# is mostly-absent noise that only inflates the vector.
FRANCHISE_COVERAGE_THRESHOLD = 0.5
DEVELOPER_COVERAGE_THRESHOLD = 0.5


def _facet_weight(count: int) -> float:
    return 1.0 / math.sqrt(count) if count else 0.0


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
    genre_weight = _facet_weight(len(genre_slugs))
    for slug in genre_slugs:
        vector[f"genre:{slug}"] = genre_weight

    platform_slugs = _platform_slugs(work)
    platform_weight = _facet_weight(len(platform_slugs))
    for slug in platform_slugs:
        vector[f"platform:{slug}"] = platform_weight

    if include_franchise:
        franchise_slugs = _franchise_slugs(work)
        franchise_weight = _facet_weight(len(franchise_slugs))
        for slug in franchise_slugs:
            vector[f"franchise:{slug}"] = franchise_weight

    if include_developer:
        developer_slugs = _developer_slugs(work)
        developer_weight = _facet_weight(len(developer_slugs))
        for slug in developer_slugs:
            vector[f"developer:{slug}"] = developer_weight

    return vector


def coverage_report(corpus_version: str | None = None) -> dict:
    """Measure franchise / developer coverage over the governed view and
    decide whether each facet is worth emitting (D-11).
    """

    works = governed_works(corpus_version)
    total = works.count()
    franchise_present = works.filter(franchises__isnull=False).distinct().count()
    developer_present = works.filter(developers__isnull=False).distinct().count()

    franchise_coverage = franchise_present / total if total else 0.0
    developer_coverage = developer_present / total if total else 0.0

    return {
        "corpus_version": corpus_version,
        "feature_set_version": FEATURE_SET_VERSION,
        "governed_count": total,
        "franchise_present": franchise_present,
        "developer_present": developer_present,
        "franchise_coverage": franchise_coverage,
        "developer_coverage": developer_coverage,
        "franchise_threshold": FRANCHISE_COVERAGE_THRESHOLD,
        "developer_threshold": DEVELOPER_COVERAGE_THRESHOLD,
        "include_franchise": franchise_coverage >= FRANCHISE_COVERAGE_THRESHOLD,
        "include_developer": developer_coverage >= DEVELOPER_COVERAGE_THRESHOLD,
        # These scalar families deliberately stay outside cosine similarity.
        # A raw primitive snapshot is deliberately not an aggregate score.
        # Composition and its recommender weight require a later approved
        # variant, never an ad-hoc request-time calculation.
        "popscore_primitives_available": CorpusPopularitySnapshot.objects.filter(
            corpus_version=corpus_version
        ).exists(),
        "rating_available": True,
        "rating_volume_available": True,
        "release_recency_available": True,
        "popscore_available": False,
    }


def normalise_rating(value: float | None) -> float | None:
    """Return an IGDB-scale rating in ``[0, 1]`` without imputing absence."""

    if value is None or not math.isfinite(value):
        return None
    return max(0.0, min(1.0, value / 100.0))


def normalise_rating_volume(value: int | None, ceiling: int | None) -> float | None:
    """Normalise ``log1p(rating_count)`` against one frozen candidate view.

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
