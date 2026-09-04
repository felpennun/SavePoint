"""Deterministic popularity-v1 baseline (REC-02, Pattern 6).

score = 3*completed + 2*playing + 1*pending + sum(rating_half_steps)/10,
aggregated per work from demo-account interactions already in PostgreSQL.
Never trained or computed against live/external input at request time --
this is a fixed, versioned formula over data already committed. Ties
broken by work UUID (ascending, stable). The DTO always declares
algorithm_id, generated_at (the cutoff), input_snapshot_sha256, and an
explicit non-personalization limitation, so it is never mistaken for or
presented as anything more than a simple aggregate baseline.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from catalogue.models import GameWork
from library.models import LibraryEntry

ALGORITHM_ID = "popularity-v1"

_STATUS_WEIGHTS = {"completed": 3, "playing": 2, "pending": 1, "abandoned": 0}


def rank_popularity_v1(cutoff: datetime | None = None) -> dict:
    cutoff = cutoff or datetime.now(timezone.utc)

    # A single resolved queryset (one query, one consistent snapshot under
    # PostgreSQL's default read-committed isolation) -- a concurrent write
    # mid-computation either lands entirely before or entirely after this
    # read, never partially mixed into it.
    entries = list(
        LibraryEntry.objects.filter(updated_at__lte=cutoff).values(
            "work_id", "current_status", "rating_half_steps"
        )
    )

    scores: dict[str, float] = {}
    for entry in entries:
        work_key = str(entry["work_id"])
        weight = _STATUS_WEIGHTS.get(entry["current_status"] or "", 0)
        rating_contribution = (entry["rating_half_steps"] or 0) / 10
        scores[work_key] = scores.get(work_key, 0.0) + weight + rating_contribution

    # Deterministic tie-break: score descending, then work UUID ascending
    # (canonical lowercase hyphenated string form sorts identically to
    # numeric UUID comparison, character-for-character, for same-length
    # strings).
    ranked_ids = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    # Hash the exact ordered (id, score) pairs that produced this result --
    # any two calls that hash the same are provably the same ranking, and a
    # concurrent mutation between calls is always visible as a hash change.
    input_snapshot_sha256 = hashlib.sha256(
        json.dumps(ranked_ids, sort_keys=False).encode("utf-8")
    ).hexdigest()

    works_by_id = GameWork.objects.in_bulk([UUID(work_id) for work_id, _ in ranked_ids])
    results = []
    for work_id, score in ranked_ids:
        work = works_by_id.get(UUID(work_id))
        if work is None:
            continue
        results.append(
            {
                "work_id": work_id,
                "slug": work.canonical_slug,
                "title": work.title_en or work.original_title,
                "score": round(score, 3),
            }
        )

    return {
        "algorithm_id": ALGORITHM_ID,
        "generated_at": cutoff.isoformat(),
        "input_snapshot_sha256": input_snapshot_sha256,
        "results": results,
        "limitation": (
            "Deterministic aggregate of demo-account interactions only. "
            "Not personalized, not a recommendation of taste, and not "
            "representative of broader player behavior."
        ),
    }
