"""Random comparison-floor baseline (REC-01).

``rank_random_v1`` is a uniform seeded draw from the governed corpus minus the
signed-in user's own library. It exists only as the lower bound every named
content variant (Plan 02-11) and the evaluation harness (Plan 02-13) are
scored against -- it is deliberately not personalised and must never be
surfaced as a recommendation of taste.

The DTO grammar is byte-for-byte the same as ``library/popularity.py``'s
``rank_popularity_v1`` (``algorithm_id`` + ``generated_at`` +
``input_snapshot_sha256`` + ``results`` + ``limitation``). Reproducibility
(threat T-02-10-04): the draw is ``random.Random(seed)`` over a
canonically-ordered candidate list, and the fingerprint hashes
``(seed, sorted(candidate_ids), ranked_ids)`` so an identical call always
hashes identically and any change to the candidate set is visible.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone

from django.contrib.auth.models import AbstractBaseUser

from catalogue.corpus import governed_works
from library.models import LibraryEntry

ALGORITHM_ID = "random-v1"

_MIN_LIMIT = 1
_MAX_LIMIT = 50
_DEFAULT_LIMIT = 10

_LIMITATION = "Uniform random draw from the governed corpus; comparison floor only."


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, int(limit)))


def rank_random_v1(
    user: AbstractBaseUser,
    seed: int = 42,
    limit: int | None = _DEFAULT_LIMIT,
    *,
    corpus_version: str | None = None,
    candidate_ids: set[object] | tuple[object, ...] | None = None,
    generated_at: datetime | None = None,
) -> dict:
    """Rank ``limit`` governed works drawn uniformly at random for ``user``.

    ``seed`` fully determines the draw. ``corpus_version`` pins the governed
    view; ``generated_at`` is recorded in the DTO for parity with the other
    baselines but does not filter candidates (a random floor has no notion of
    a cutoff).
    """

    generated_at = generated_at or datetime.now(timezone.utc)
    limit = _clamp_limit(limit)

    seen_ids = {
        row["work_id"]
        for row in LibraryEntry.objects.filter(user=user).values("work_id")
    }

    candidate_query = governed_works(corpus_version)
    if candidate_ids is not None:
        candidate_query = candidate_query.filter(id__in=set(candidate_ids))
    else:
        candidate_query = candidate_query.exclude(id__in=seen_ids)
    candidates = list(candidate_query.values_list("id", "canonical_slug", "title_en", "original_title"))
    # Canonical order before the seeded draw so the result depends only on
    # ``seed`` and the candidate *set*, never on the DB's row order.
    candidates.sort(key=lambda row: str(row[0]))

    draw_count = min(limit, len(candidates))
    drawn = random.Random(seed).sample(candidates, k=draw_count)

    candidate_ids = [str(row[0]) for row in candidates]
    ranked_ids = [str(row[0]) for row in drawn]
    input_snapshot_sha256 = hashlib.sha256(
        json.dumps(
            {"seed": seed, "candidates": candidate_ids, "ranked": ranked_ids},
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    results = [
        {
            "work_id": str(work_id),
            "slug": canonical_slug,
            "title": title_en or original_title,
            # Inverse rank as a nominal score so the DTO item shape matches
            # rank_popularity_v1; it carries no meaning beyond draw order.
            "score": float(draw_count - position),
        }
        for position, (work_id, canonical_slug, title_en, original_title) in enumerate(drawn)
    ]

    return {
        "algorithm_id": ALGORITHM_ID,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": input_snapshot_sha256,
        "results": results,
        "limitation": _LIMITATION,
    }
