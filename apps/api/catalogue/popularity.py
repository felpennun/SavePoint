"""Frozen, explainable IGDB engagement PopScore helpers."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable

from catalogue.models import CorpusPopularitySnapshot


IGDB_ENGAGEMENT_TYPES = ("Visits", "Want to Play", "Playing", "Played")


def normalised_popscore_by_work(
    corpus_version: str | None, work_ids: Iterable[object]
) -> dict[object, float]:
    """Return the unweighted mean of the four normalised IGDB primitives.

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
    return {
        work_id: math.fsum(parts[name] for name in IGDB_ENGAGEMENT_TYPES) / len(IGDB_ENGAGEMENT_TYPES)
        for work_id, parts in values.items()
        if all(name in parts for name in IGDB_ENGAGEMENT_TYPES)
    }


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
    payload = sorted(
        (
            str(work_id),
            name,
            value,
            normalised_value,
            calculated_at.isoformat() if calculated_at else None,
            source_updated_at.isoformat() if source_updated_at else None,
            payload_sha256,
        )
        for work_id, name, value, normalised_value, calculated_at, source_updated_at, payload_sha256 in rows
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
