"""Frozen, explainable IGDB engagement PopScore helpers."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable

from catalogue.models import CorpusPopularityScore, CorpusPopularitySnapshot


IGDB_ENGAGEMENT_TYPES = ("Visits", "Want to Play", "Playing", "Played")
POPSCORE_FORMULA_VERSION = "igdb-engagement-weighted-v2"
# Discovery is the strongest engagement intent; active and completed play are
# equally meaningful confirmations, while an aspirational wishlist signal is
# deliberately weakest. The values are part of the frozen PopScore contract.
POPSCORE_WEIGHTS: dict[str, float] = {
    "Visits": 0.40,
    "Playing": 0.25,
    "Played": 0.25,
    "Want to Play": 0.10,
}


def compose_popscore(parts: dict[str, float]) -> float | None:
    """Compose all required normalised IGDB engagement primitives."""

    if not all(name in parts for name in IGDB_ENGAGEMENT_TYPES):
        return None
    return math.fsum(POPSCORE_WEIGHTS[name] * parts[name] for name in IGDB_ENGAGEMENT_TYPES)


def normalised_popscore_by_work(
    corpus_version: str | None, work_ids: Iterable[object]
) -> dict[object, float]:
    """Return the weighted composition of the four normalised IGDB primitives.

    A missing primitive means the composed PopScore is absent. This prevents
    incomplete provider coverage from being treated as a measured low value.
    """

    if corpus_version is None:
        return {}
    values: dict[object, dict[str, float]] = {}
    for work_id, name, normalised_value in CorpusPopularitySnapshot.objects.filter(
        corpus_version=corpus_version,
        work_id__in=set(work_ids),
        popularity_type_name__in=IGDB_ENGAGEMENT_TYPES,
        normalised_value__isnull=False,
    ).values_list("work_id", "popularity_type_name", "normalised_value"):
        values.setdefault(work_id, {})[name] = normalised_value
    calculated = {
        work_id: score
        for work_id, parts in values.items()
        if (score := compose_popscore(parts)) is not None
    }
    if calculated:
        persisted = dict(
            CorpusPopularityScore.objects.filter(
                corpus_version=corpus_version,
                work_id__in=calculated,
                formula_version=POPSCORE_FORMULA_VERSION,
            ).values_list("work_id", "score")
        )
        return {work_id: persisted.get(work_id, score) for work_id, score in calculated.items()}
    return calculated


def popscore_snapshot_sha256(corpus_version: str | None) -> str | None:
    """Hash the exact primitive rows and normalisation used by a rank result."""

    if corpus_version is None:
        return None
    rows = list(
        CorpusPopularitySnapshot.objects.filter(
            corpus_version=corpus_version,
            popularity_type_name__in=IGDB_ENGAGEMENT_TYPES,
        ).values_list(
            "work_id",
            "popularity_type_name",
            "value",
            "normalised_value",
            "calculated_at",
            "source_updated_at",
            "payload_sha256",
        )
    )
    if not rows:
        return None
    payload = {
        "formula_version": POPSCORE_FORMULA_VERSION,
        "weights": POPSCORE_WEIGHTS,
        "primitives": sorted(
            (
                str(work_id),
                name,
                value,
                normalised_value,
                calculated_at.isoformat() if calculated_at else None,
                source_updated_at.isoformat() if source_updated_at else None,
                payload_sha256,
            )
            for (
                work_id,
                name,
                value,
                normalised_value,
                calculated_at,
                source_updated_at,
                payload_sha256,
            ) in rows
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
