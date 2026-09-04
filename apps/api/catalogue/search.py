"""Tolerant catalogue search (Pattern 5, D-10/D-12): exact match first, then
prefix, then trigram similarity for small typos -- always over the
normalized (casefolded, accent-stripped) alias index, entirely local
(CAT-06: zero external calls, works with the provider unavailable).
"""

from __future__ import annotations

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from catalogue.models import GameAlias, GameWork
from catalogue.normalization import normalize_title

TRIGRAM_SIMILARITY_THRESHOLD = 0.3
DEFAULT_PAGE_SIZE = 24


def _base_works() -> QuerySet[GameWork]:
    # D-11: DLC/expansions never appear as independent search/list results.
    return GameWork.objects.filter(is_dlc=False)


def _ordered_matching_work_ids(normalized_query: str) -> list[str]:
    exact_ids = list(
        GameAlias.objects.filter(normalized_value=normalized_query, work__is_dlc=False)
        .order_by("work_id")
        .values_list("work_id", flat=True)
    )
    seen = set(exact_ids)

    prefix_ids = [
        wid
        for wid in GameAlias.objects.filter(
            normalized_value__startswith=normalized_query, work__is_dlc=False
        )
        .order_by("normalized_value", "work_id")
        .values_list("work_id", flat=True)
        if wid not in seen
    ]
    seen.update(prefix_ids)

    trigram_ids = [
        wid
        for wid in GameAlias.objects.filter(work__is_dlc=False)
        .annotate(similarity=TrigramSimilarity("normalized_value", normalized_query))
        .filter(similarity__gte=TRIGRAM_SIMILARITY_THRESHOLD)
        .order_by("-similarity", "normalized_value", "work_id")
        .values_list("work_id", flat=True)
        if wid not in seen
    ]

    ordered: list[str] = []
    result_seen: set[str] = set()
    for wid in [*exact_ids, *prefix_ids, *trigram_ids]:
        if wid not in result_seen:
            result_seen.add(wid)
            ordered.append(wid)
    return ordered


def search_games(query: str | None, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """Return a paginated, deterministically-ordered result set.

    An empty/whitespace-only query returns the unfiltered, alphabetically
    ordered catalogue (matches the UI-SPEC "Whitespace-only becomes
    unfiltered catalogue" contract) rather than an empty result.
    """
    page = max(page, 1)
    page_size = max(page_size, 1)
    stripped = (query or "").strip()

    if not stripped:
        works_qs = _base_works().order_by("original_title", "id")
        total = works_qs.count()
        start = (page - 1) * page_size
        page_works = list(works_qs[start : start + page_size])
    else:
        normalized_query = normalize_title(stripped)
        ordered_ids = _ordered_matching_work_ids(normalized_query)
        total = len(ordered_ids)
        start = (page - 1) * page_size
        page_ids = ordered_ids[start : start + page_size]
        works_by_id = GameWork.objects.in_bulk(page_ids)
        page_works = [works_by_id[wid] for wid in page_ids if wid in works_by_id]

    return {
        "results": page_works,
        "count": total,
        "page": page,
        "page_size": page_size,
        "has_next": start + page_size < total,
    }
