"""Deterministic genre-taste-v1 heuristic (REC-10, D-09).

A stateless, request-time aggregation over the signed-in user's own
``LibraryEntry`` rows -- the personal sibling of ``library/popularity.py``'s
non-personalized REC-02 baseline. It mirrors that module's DTO contract
(``algorithm_id`` + ``generated_at`` + ``input_snapshot_sha256`` + explicit
``limitation`` string, deterministic rating/genre/``canonical_slug`` order) but is
scoped strictly to ``request.user``:

   1. Weight the user's genres by their own recorded activity -- each of the
      user's library entries contributes ``_STATUS_WEIGHTS[status] +
      (rating_half_steps / 10)^2`` to every genre attached to that entry's work.
  2. Rank UNSEEN, non-DLC catalogue works by catalogue rating inside the
     genres they share with that taste vector. The user's genre affinity is
     retained as the first tie-breaker, followed by ``canonical_slug``.
  3. Break remaining ties by ``canonical_slug`` ascending; fingerprint the
     exact taste vector + ordered result so identical inputs hash identically.

There is NO trained model and NO persisted feature store here -- Phase 6
(REC-03) owns the real content-based recommender with versioned artifacts
and cold-start handling. This module is deliberately simpler and MUST NOT
be presented as, or compared against, that work. When the user has no
genre-bearing activity yet the result is an explicit insufficient-history
shape -- it NEVER falls back to the public popularity baseline (D-09).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Callable

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Case, F, FloatField, Sum, Value, When

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import GameWork, Genre
from catalogue.serializers import _cover, _platform_summary, _release_year
from library.models import LibraryEntry
from recommendations._weights import (  # noqa: F401  (re-exported for callers)
    _entry_weight,
    _RATING_DIVISOR,
    _STATUS_WEIGHTS,
)
from recommendations.cancellation import RecommendationComputationCancelled

# ``_STATUS_WEIGHTS`` / ``_RATING_DIVISOR`` / ``_entry_weight`` moved to the
# shared ``recommendations._weights`` module (Plan 02-10) so the content
# profile speaks the same activity-weighting language. They are re-exported
# here unchanged -- ``from recommendations.genre_heuristic import
# _entry_weight`` still resolves while the nonlinear rating policy remains
# shared with the content profile.
__all__ = ["ALGORITHM_ID", "rank_genre_taste_v1"]

ALGORITHM_ID = "genre-taste-v1"

# Documented request bound (threat T-01.1-11): the caller-supplied ``limit``
# is clamped into ``[_MIN_LIMIT, _MAX_LIMIT]`` and the ranking SQL carries a
# matching ``LIMIT`` so the candidate working set is never unbounded over
# the 300k-row catalogue.
_MIN_LIMIT = 1
_MAX_LIMIT = 50
_DEFAULT_LIMIT = 20
_MIN_CATALOGUE_RATING_COUNT = 1000
# The ranking SQL fetches this multiple of ``limit`` so the exact Python
# re-score + canonical_slug tie-break (L-03) has every boundary-tied work in
# hand before truncating. Still bounded: at most _MAX_LIMIT * this.
_CANDIDATE_OVERFETCH = 4

_LIMITATION = (
    "Deterministic primary-genre heuristic computed at request time from "
    "the signed-in user's own library only. It selects the genre appearing "
    "in the most library entries (canonical slug breaks ties), then unseen "
    "non-DLC catalogue works with that genre and at least 1,000 catalogue "
    "ratings are ordered "
    "by catalogue rating (unrated last), "
    "genre-overlap weight, and canonical_slug. This is a product feature, "
    "not a trained model or a "
    "persisted feature store, and is deliberately simpler than the Phase 6 "
    "content-based recommender comparison (REC-03). It is not the thesis's "
    "algorithmic contribution and must not be presented as, or evaluated "
    "against, that work."
)

_INSUFFICIENT_HISTORY_LIMITATION = (
    "The signed-in user has no genre-bearing rated or status-tracked "
    "library activity yet, so no personalised genre-taste ranking can be "
    "produced. This result deliberately does NOT fall back to the "
    "non-personalised public baseline (REC-02); the recommendations page "
    "must show an explicit empty/onboarding state instead."
)


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, int(limit)))


def _fingerprint(
    taste: dict,
    primary_genre_slug: str | None,
    ranked: list[tuple[str, float, float | None, int | None]],
) -> str:
    """Hash the exact taste vector and ordered result metadata.

    Identical inputs -> identical hash; any change to the user's activity or
    to the produced ranking is always visible as a hash change.
    """
    payload = {
        "algorithm_id": ALGORITHM_ID,
        "taste": sorted((str(genre_id), round(weight, 6)) for genre_id, weight in taste.items()),
        "primary_genre_slug": primary_genre_slug,
        "ranked": [
            (
                slug,
                round(score, 6),
                None if rating is None else round(rating, 6),
                rating_count,
            )
            for slug, score, rating, rating_count in ranked
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _insufficient_history(generated_at: datetime, taste: dict) -> dict:
    return {
        "algorithm_id": ALGORITHM_ID,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": _fingerprint(taste, None, []),
        "insufficient_history": True,
        "limitation": _INSUFFICIENT_HISTORY_LIMITATION,
        "primary_genre": None,
        "results": [],
    }


def rank_genre_taste_v1(
    user: AbstractBaseUser,
    limit: int | None = _DEFAULT_LIMIT,
    *,
    generated_at: datetime | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> dict:
    """Rank unseen catalogue works by ``user``'s own genre taste.

    ``generated_at`` is the snapshot cutoff: only library activity with
    ``updated_at <= generated_at`` feeds the taste vector, mirroring
    ``rank_popularity_v1``'s ``cutoff`` argument for reproducible results.
    """
    if should_continue is not None and not should_continue():
        raise RecommendationComputationCancelled
    generated_at = generated_at or datetime.now(timezone.utc)
    limit = _clamp_limit(limit)

    # 1. One resolved read of the user's own library -- the snapshot the
    #    ranking is computed against. ``seen_ids`` is every work the user has
    #    any entry for (status set or not); none of them may be recommended.
    entries = list(
        LibraryEntry.objects.filter(user=user, updated_at__lte=generated_at).values(
            "work_id", "current_status", "rating_half_steps"
        )
    )
    seen_ids = {entry["work_id"] for entry in entries}

    activity_by_work: dict[object, float] = {}
    for entry in entries:
        activity_by_work[entry["work_id"]] = activity_by_work.get(entry["work_id"], 0.0) + _entry_weight(
            entry["current_status"], entry["rating_half_steps"]
        )

    # 2. Fold each seen work's genres into the taste vector, bounded by the
    #    user's (small) library size.
    through = GameWork.genres.through
    taste_weights: dict[object, float] = {}
    genre_entry_counts: dict[object, int] = {}
    if seen_ids:
        for work_id, genre_id in through.objects.filter(gamework_id__in=seen_ids).values_list(
            "gamework_id", "genre_id"
        ):
            weight = activity_by_work.get(work_id, 0.0)
            if weight:
                taste_weights[genre_id] = taste_weights.get(genre_id, 0.0) + weight
                genre_entry_counts[genre_id] = genre_entry_counts.get(genre_id, 0) + 1

    if not taste_weights or sum(taste_weights.values()) <= 0:
        return _insufficient_history(generated_at, taste_weights)

    genre_metadata = {
        genre.id: (genre.slug, genre.name)
        for genre in Genre.objects.filter(id__in=taste_weights).only("id", "slug", "name")
    }
    primary_genre_id = min(
        taste_weights,
        key=lambda genre_id: (-genre_entry_counts[genre_id], genre_metadata[genre_id][0]),
    )
    primary_genre_slug, primary_genre_name = genre_metadata[primary_genre_id]
    primary_genre = {
        "slug": primary_genre_slug,
        "name": primary_genre_name,
        "entry_count": genre_entry_counts[primary_genre_id],
        "weight": round(taste_weights[primary_genre_id], 3),
    }

    # 3. Rank unseen governed candidates in the most frequent library genre.
    # and have a sufficiently reliable catalogue rating sample. This heuristic
    # shares the product candidate boundary: no future, DLC, ungoverned, or
    # rating-ineligible work may bypass the content recommendation corpus.
    #    The through table is the driving relation: filtered by the primary ``genre_id``
    #    (indexed) and grouped by work, so Postgres never scans the full
    #    catalogue -- and the bounded candidate slice caps the working set
    #    (threat T-01.1-11).
    #
    #    The DB orders on Sum(score_case) in IEEE-754 double precision, but
     #    nonlinear rating contributions are not exactly representable, so two
     #    works with the same *rational* score can carry different float
    #    sums. Over-fetch a multiple of ``limit`` here and let step 4 do the
    #    authoritative exact scoring + ``canonical_slug`` tie-break in Python
    #    before truncating -- so the documented cut-line semantics hold, not
    #    whatever order the float sums happened to land in (repo-review
    #    2026-09-06 L-03).
    candidate_pool = limit * _CANDIDATE_OVERFETCH
    score_case = Case(
        *[When(genre_id=genre_id, then=Value(float(weight))) for genre_id, weight in taste_weights.items()],
        default=Value(0.0),
        output_field=FloatField(),
    )
    governed_candidates = evaluation_candidate_works(
        eligibility_cutoff_date=generated_at.date()
    )
    ranked_rows = (
        through.objects.filter(genre_id=primary_genre_id)
        .filter(gamework_id__in=governed_candidates.values("id"))
        .filter(gamework__total_rating_count__gte=_MIN_CATALOGUE_RATING_COUNT)
        .exclude(gamework_id__in=list(seen_ids))
        .values("gamework_id")
        .annotate(taste_score=Sum(score_case))
        .order_by(
            F("gamework__total_rating").desc(nulls_last=True),
            "-taste_score",
            "gamework__canonical_slug",
        )[:candidate_pool]
    )
    ordered_work_ids = [row["gamework_id"] for row in ranked_rows]

    works = (
        governed_candidates.filter(id__in=ordered_work_ids)
        .prefetch_related("genres", "assets", "releases__platform")
        .in_bulk()
    )

    # 4. Recompute every score in Python from the authoritative taste vector
    #    (not the DB float sum) so the returned score, the per-item
    #    explanation, and the tie-break are exactly consistent, then re-sort.
    scored: list[tuple[float, float | None, str, GameWork, list[dict]]] = []
    for index, work_id in enumerate(ordered_work_ids):
        if index % 16 == 0 and should_continue is not None and not should_continue():
            raise RecommendationComputationCancelled
        work = works.get(work_id)
        if work is None:
            continue
        matched = [
            {
                "slug": genre.slug,
                "name": genre.name,
                "weight": round(taste_weights[genre.id], 3),
            }
            for genre in work.genres.all()
            if genre.id in taste_weights
        ]
        if not matched:
            continue
        matched.sort(key=lambda item: (-item["weight"], item["slug"]))
        score = sum(taste_weights[genre.id] for genre in work.genres.all() if genre.id in taste_weights)
        scored.append((score, work.total_rating, work.canonical_slug, work, matched))

    # Authoritative order: exact taste score desc, catalogue rating desc
    # (unrated last), then canonical_slug asc. Only now truncate to the
    # requested limit -- the DB slice above was a deliberately wider candidate
    # pool (L-03).
    scored.sort(
        key=lambda row: (
            -row[0],
            -(row[1] if row[1] is not None else -1.0),
            row[2],
        )
    )
    scored = scored[:limit]

    results = [
        {
            "work_id": str(work.id),
            "slug": work.canonical_slug,
            "title": work.title_en or work.original_title,
            "score": round(score, 3),
            "catalogue_rating": None if rating is None else round(rating, 2),
            "catalogue_rating_count": work.total_rating_count,
            "year": _release_year(work),
            "platform_summary": _platform_summary(work),
            "cover": _cover(work),
            "matched_genres": matched,
        }
        for score, rating, _slug, work, matched in scored
    ]

    return {
        "algorithm_id": ALGORITHM_ID,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": _fingerprint(
            taste_weights,
            primary_genre_slug,
            [
                (
                    item["slug"],
                    item["score"],
                    item["catalogue_rating"],
                    item["catalogue_rating_count"],
                )
                for item in results
            ],
        ),
        "insufficient_history": False,
        "limitation": _LIMITATION,
        "primary_genre": primary_genre,
        "results": results,
    }
