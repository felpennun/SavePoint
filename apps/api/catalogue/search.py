"""Tolerant catalogue search + CAT-02 filter/sort/facets.

Tolerant search (Pattern 5, D-10/D-12): exact match first, then prefix, then
trigram similarity for small typos -- always over the normalized (casefolded,
accent-stripped) alias index, entirely local (CAT-06: zero external calls,
works with the provider unavailable).

CAT-02 (Plan 01.1-03): ``platform`` / ``genre`` / ``year_from`` / ``year_to`` /
``min_rating`` filters intersect on top of that result set, and a fixed
``sort`` allowlist maps to a deterministic ``order_by`` with a
``canonical_slug`` tie-break. Client sort text is NEVER interpolated into
``order_by`` -- an unknown key is a bounded 400, handled by
:func:`parse_catalogue_query`. Out-of-range / non-numeric year and rating are
likewise a bounded 400.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Count, F, Max, Min, QuerySet

from catalogue.models import GameAlias, GameWork, Genre, Platform
from catalogue.normalization import normalize_title

TRIGRAM_SIMILARITY_THRESHOLD = 0.3
# Cap the fuzzy-match candidate set so a single request can never fan out to
# the whole alias table (M-05). Comfortably larger than any realistic page.
TRIGRAM_CANDIDATE_CAP = 200
DEFAULT_PAGE_SIZE = 24

YEAR_MIN = 1958
RATING_MIN = 0.0
RATING_MAX = 100.0


def _year_max() -> int:
    return date.today().year + 2


# Fixed sort allowlist. Each key resolves to a tuple of ``order_by`` arguments
# that ALWAYS ends with ``canonical_slug`` so every ordering is total and
# stable across calls. Nothing derived from client input ever reaches this
# dict -- an unrecognised key raises before a query is built.
SORT_ORDERS: dict[str, tuple] = {
    "title_asc": ("original_title", "canonical_slug"),
    "title_desc": ("-original_title", "canonical_slug"),
    "release_newest": (F("first_release_date").desc(nulls_last=True), "canonical_slug"),
    "release_oldest": (F("first_release_date").asc(nulls_last=True), "canonical_slug"),
    "rating_desc": (F("total_rating").desc(nulls_last=True), "canonical_slug"),
}
# ``relevance`` is only meaningful with a text query; with no ``q`` it falls
# back to ``release_newest`` (UI-SPEC Screen Contract 2).
SORT_KEYS: tuple[str, ...] = ("relevance", *SORT_ORDERS.keys())
DEFAULT_SORT_NO_QUERY = "release_newest"
DEFAULT_SORT_WITH_QUERY = "relevance"


class FilterValidationError(ValueError):
    """A catalogue query parameter is unknown or out of its allowed range.

    The endpoint turns this into a bounded HTTP 400; it never reaches the ORM.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass
class CatalogueQuery:
    q: str | None = None
    platform: str | None = None
    genre: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    min_rating: float | None = None
    sort: str = "relevance"


def _parse_int(raw: str, code: str, label: str) -> int:
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        raise FilterValidationError(code, f"{label} must be an integer") from None


def _parse_float(raw: str, code: str, label: str) -> float:
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        raise FilterValidationError(code, f"{label} must be a number") from None


def parse_catalogue_query(params: Mapping[str, str]) -> CatalogueQuery:
    """Validate raw query params into a :class:`CatalogueQuery`.

    Raises :class:`FilterValidationError` for an unknown ``sort`` key or an
    out-of-range / non-numeric ``year_from`` / ``year_to`` / ``min_rating``.
    Unknown ``platform`` / ``genre`` slugs are NOT an error here -- they are
    resolved (and silently dropped if absent) in :func:`search_games`, matching
    the UI-SPEC "unknown facet value -> ignored" contract.
    """
    q = (params.get("q") or "").strip() or None

    raw_sort = (params.get("sort") or "").strip()
    if raw_sort and raw_sort not in SORT_KEYS:
        raise FilterValidationError("invalid_sort", f"unknown sort key: {raw_sort!r}")
    if not raw_sort:
        sort = DEFAULT_SORT_WITH_QUERY if q else DEFAULT_SORT_NO_QUERY
    elif raw_sort == "relevance" and not q:
        sort = DEFAULT_SORT_NO_QUERY
    else:
        sort = raw_sort

    year_from = year_to = None
    if params.get("year_from"):
        year_from = _parse_int(params["year_from"], "invalid_year", "year_from")
    if params.get("year_to"):
        year_to = _parse_int(params["year_to"], "invalid_year", "year_to")
    year_ceiling = _year_max()
    for value in (year_from, year_to):
        if value is not None and not (YEAR_MIN <= value <= year_ceiling):
            raise FilterValidationError(
                "year_out_of_range", f"year must be between {YEAR_MIN} and {year_ceiling}"
            )
    if year_from is not None and year_to is not None and year_from > year_to:
        year_from, year_to = year_to, year_from

    min_rating = None
    if params.get("min_rating"):
        min_rating = _parse_float(params["min_rating"], "invalid_rating", "min_rating")
        if not (RATING_MIN <= min_rating <= RATING_MAX):
            raise FilterValidationError(
                "rating_out_of_range",
                f"min_rating must be between {int(RATING_MIN)} and {int(RATING_MAX)}",
            )

    platform = (params.get("platform") or "").strip() or None
    genre = (params.get("genre") or "").strip() or None

    return CatalogueQuery(
        q=q,
        platform=platform,
        genre=genre,
        year_from=year_from,
        year_to=year_to,
        min_rating=min_rating,
        sort=sort,
    )


def _base_works() -> QuerySet[GameWork]:
    # D-11: DLC/expansions never appear as independent search/list results.
    return GameWork.objects.filter(is_dlc=False)


def _apply_filters(qs: QuerySet[GameWork], cq: CatalogueQuery) -> QuerySet[GameWork]:
    """Intersect the requested facet filters onto ``qs``.

    An unknown platform/genre slug resolves to no row and is dropped (the
    filter simply does not apply) rather than forcing an empty result set.
    """
    joined = False
    if cq.platform and Platform.objects.filter(slug=cq.platform).exists():
        qs = qs.filter(releases__platform__slug=cq.platform)
        joined = True
    if cq.genre and Genre.objects.filter(slug=cq.genre).exists():
        qs = qs.filter(genres__slug=cq.genre)
        joined = True
    if cq.year_from is not None:
        qs = qs.filter(first_release_date__gte=date(cq.year_from, 1, 1))
    if cq.year_to is not None:
        qs = qs.filter(first_release_date__lte=date(cq.year_to, 12, 31))
    if cq.min_rating is not None:
        qs = qs.filter(total_rating__gte=cq.min_rating)
    if joined:
        qs = qs.distinct()
    return qs


def _prefetched(qs: QuerySet[GameWork]) -> QuerySet[GameWork]:
    return qs.prefetch_related("releases__platform", "assets", "genres")


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

    # Pre-filter with the `%` operator (``__trigram_similar``) so the GIN
    # trigram index does the selection; only then score + order the survivors,
    # and cap the set. Without the `%` pre-filter this computed SIMILARITY()
    # for every alias row on every request (M-05).
    trigram_ids = [
        wid
        for wid in GameAlias.objects.filter(
            work__is_dlc=False, normalized_value__trigram_similar=normalized_query
        )
        .annotate(similarity=TrigramSimilarity("normalized_value", normalized_query))
        .filter(similarity__gte=TRIGRAM_SIMILARITY_THRESHOLD)
        .order_by("-similarity", "normalized_value", "work_id")
        .values_list("work_id", flat=True)[:TRIGRAM_CANDIDATE_CAP]
        if wid not in seen
    ]

    ordered: list[str] = []
    result_seen: set[str] = set()
    for wid in [*exact_ids, *prefix_ids, *trigram_ids]:
        if wid not in result_seen:
            result_seen.add(wid)
            ordered.append(wid)
    return ordered


def _facets(scoped: QuerySet[GameWork]) -> dict:
    """Facet options + counts over the text-scoped result set (before the
    platform/genre/year/rating filters and before pagination).

    Three aggregate queries, none of which scale with the page size.
    """
    platforms = [
        {"slug": row["slug"], "name": row["name"], "count": row["count"]}
        for row in Platform.objects.filter(releases__work__in=scoped)
        .annotate(count=Count("releases__work", distinct=True))
        .order_by("name")
        .values("slug", "name", "count")
    ]
    genres = [
        {"slug": row["slug"], "name": row["name"], "count": row["count"]}
        for row in Genre.objects.filter(works__in=scoped)
        .annotate(count=Count("works", distinct=True))
        .order_by("name")
        .values("slug", "name", "count")
    ]
    span = scoped.aggregate(min=Min("first_release_date"), max=Max("first_release_date"))
    return {
        "platforms": platforms,
        "genres": genres,
        "year_range": {
            "min": span["min"].year if span["min"] else None,
            "max": span["max"].year if span["max"] else None,
        },
    }


def search_games(
    query: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    *,
    cq: CatalogueQuery | None = None,
) -> dict:
    """Return a paginated, deterministically-ordered result set plus facets.

    ``cq`` carries the validated CAT-02 filters/sort. When omitted the call
    behaves exactly as the pre-CAT-02 endpoint did: an empty/whitespace-only
    query returns the unfiltered, alphabetically ordered catalogue.
    """
    page = max(page, 1)
    page_size = max(page_size, 1)
    if cq is None:
        stripped_probe = (query or "").strip()
        cq = CatalogueQuery(
            q=stripped_probe or None,
            sort=DEFAULT_SORT_WITH_QUERY if stripped_probe else DEFAULT_SORT_NO_QUERY,
        )

    stripped = (cq.q or query or "").strip()
    start = (page - 1) * page_size

    # Text-scoped base: DLC-excluded catalogue, narrowed to alias matches when
    # a query is present. This set drives both the facets and the filters.
    scoped = _base_works()
    ordered_ids: list[str] = []
    if stripped:
        ordered_ids = _ordered_matching_work_ids(normalize_title(stripped))
        scoped = scoped.filter(id__in=ordered_ids)

    facets = _facets(scoped)

    filtered = _apply_filters(scoped, cq)

    effective_sort = cq.sort
    if effective_sort == "relevance" and not stripped:
        effective_sort = DEFAULT_SORT_NO_QUERY

    if effective_sort == "relevance":
        allowed = set(filtered.values_list("id", flat=True))
        ranked = [wid for wid in ordered_ids if wid in allowed]
        total = len(ranked)
        page_ids = ranked[start : start + page_size]
        works_by_id = {w.id: w for w in _prefetched(GameWork.objects.filter(id__in=page_ids))}
        page_works = [works_by_id[wid] for wid in page_ids if wid in works_by_id]
    else:
        ordered_qs = filtered.order_by(*SORT_ORDERS[effective_sort])
        total = ordered_qs.count()
        page_works = list(_prefetched(ordered_qs)[start : start + page_size])

    return {
        "results": page_works,
        "count": total,
        "page": page,
        "page_size": page_size,
        "has_next": start + page_size < total,
        "sort": effective_sort,
        "facets": facets,
    }
