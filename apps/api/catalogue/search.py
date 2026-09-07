"""Tolerant catalogue search + CAT-02 filter/sort/facets.

Tolerant search (Pattern 5, D-10/D-12): exact match first, then prefix, then
trigram similarity for small typos -- always over the normalized (casefolded,
accent-stripped) alias index, entirely local (CAT-06: zero external calls,
works with the provider unavailable).

CAT-02 (Plan 01.1-03, extended in Plan 02-03): ``platform`` / ``genre`` are
repeated multi-select params -- several ``genre`` values are ANDed ("has all"),
several ``platform`` values are ORed ("available on any") -- while ``year_from``
/ ``year_to`` / ``min_rating`` stay single-valued and intersect on top. A fixed
``sort`` allowlist maps to a deterministic ``order_by`` with a
``canonical_slug`` tie-break. Client sort text is NEVER interpolated into
``order_by`` -- an unknown key is a bounded 400, handled by
:func:`parse_catalogue_query`. Out-of-range / non-numeric year and rating, and
more than :data:`MAX_MULTISELECT_VALUES` repeated facet values, are likewise a
bounded 400. The public list, search, and facets all operate over the governed
corpus view (:func:`catalogue.corpus.governed_works`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, Count, F, IntegerField, Max, Min, QuerySet, Value, When

from catalogue.corpus import governed_works
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
# Relevance is a stepped discovery ordering, not a visibility filter. A larger
# rating sample gets an earlier tier; the IGDB score then ranks games within
# each tier. The final tier contains works with fewer than ten ratings or no
# rating-count data at all.
RELEVANCE_RATING_COUNT_TIERS: tuple[tuple[int, int], ...] = (
    (1000, 0),
    (500, 1),
    (200, 2),
    (100, 3),
    (50, 4),
    (10, 5),
)

# Cap repeated ``genre`` / ``platform`` params so a single request can never
# fan a query out into an unbounded chain of joins (threat T-02-03-02, V5 DoS).
MAX_MULTISELECT_VALUES = 20


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
# ``relevance`` is the default discovery mode with or without a text query.
# It means a stepped rating-count order followed by the IGDB score.
SORT_KEYS: tuple[str, ...] = ("relevance", *SORT_ORDERS.keys())
DEFAULT_SORT_NO_QUERY = "relevance"
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
    genres: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
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


def _multi_values(params: Mapping[str, str], key: str) -> tuple[str, ...]:
    """Read every repeated value of ``key`` -- ``getlist`` when the mapping
    supports it (DRF ``request.query_params`` / Django ``QueryDict``), else the
    single ``get`` value -- then trim, drop blanks, and de-duplicate in order.

    Raises :class:`FilterValidationError` past :data:`MAX_MULTISELECT_VALUES`
    repeated values so a request cannot fan a query out into an unbounded join
    chain (threat T-02-03-02).
    """
    getlist = getattr(params, "getlist", None)
    if callable(getlist):
        raw = list(getlist(key))
    else:
        one = params.get(key)
        raw = [one] if one is not None else []
    if len(raw) > MAX_MULTISELECT_VALUES:
        raise FilterValidationError(
            "too_many_facet_values",
            f"at most {MAX_MULTISELECT_VALUES} {key} values allowed",
        )
    cleaned = tuple(dict.fromkeys(s.strip() for s in raw if s and s.strip()))
    if len(cleaned) > MAX_MULTISELECT_VALUES:
        raise FilterValidationError(
            "too_many_facet_values",
            f"at most {MAX_MULTISELECT_VALUES} {key} values allowed",
        )
    return cleaned


def parse_catalogue_query(params: Mapping[str, str]) -> CatalogueQuery:
    """Validate raw query params into a :class:`CatalogueQuery`.

    Raises :class:`FilterValidationError` for an unknown ``sort`` key, an
    out-of-range / non-numeric ``year_from`` / ``year_to`` / ``min_rating``, or
    more than :data:`MAX_MULTISELECT_VALUES` repeated ``genre`` / ``platform``
    values. Unknown ``platform`` / ``genre`` slugs are NOT an error here -- they
    are resolved (and silently dropped if absent) in :func:`_apply_filters`,
    matching the UI-SPEC "unknown facet value -> ignored" contract.
    """
    q = (params.get("q") or "").strip() or None

    raw_sort = (params.get("sort") or "").strip()
    if raw_sort and raw_sort not in SORT_KEYS:
        raise FilterValidationError("invalid_sort", f"unknown sort key: {raw_sort!r}")
    if not raw_sort:
        sort = DEFAULT_SORT_WITH_QUERY if q else DEFAULT_SORT_NO_QUERY
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

    genres = _multi_values(params, "genre")
    platforms = _multi_values(params, "platform")

    return CatalogueQuery(
        q=q,
        genres=genres,
        platforms=platforms,
        year_from=year_from,
        year_to=year_to,
        min_rating=min_rating,
        sort=sort,
    )


def _apply_filters(qs: QuerySet[GameWork], cq: CatalogueQuery) -> QuerySet[GameWork]:
    """Intersect the requested facet filters onto ``qs``.

    Several ``genre`` values are ANDed -- one chained ``filter`` per genre, each
    adding a join, so ``.distinct()`` is required once any facet joined
    (Pitfall 3). Several ``platform`` values are ORed -- a single ``__in`` over
    the resolved slugs. An unknown platform/genre slug resolves to no row and is
    dropped (the filter simply does not apply) rather than forcing an empty
    result set.
    """
    joined = False
    if cq.platforms:
        valid_platforms = list(
            Platform.objects.filter(slug__in=cq.platforms).values_list("slug", flat=True)
        )
        if valid_platforms:
            qs = qs.filter(releases__platform__slug__in=valid_platforms)
            joined = True
    if cq.genres:
        valid_genres = set(
            Genre.objects.filter(slug__in=cq.genres).values_list("slug", flat=True)
        )
        for slug in cq.genres:
            if slug in valid_genres:
                qs = qs.filter(genres__slug=slug)
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


def _relevance_order(qs: QuerySet[GameWork]) -> QuerySet[GameWork]:
    """Order discovery results by rating-count confidence, then IGDB score.

    The tier is deliberately expressed in the database query so pagination is
    applied after the complete deterministic ranking rather than after a
    Python-side page-sized approximation.
    """
    tier = Case(
        *(
            When(total_rating_count__gte=threshold, then=Value(rank))
            for threshold, rank in RELEVANCE_RATING_COUNT_TIERS
        ),
        default=Value(len(RELEVANCE_RATING_COUNT_TIERS)),
        output_field=IntegerField(),
    )
    return qs.annotate(relevance_tier=tier).order_by(
        "relevance_tier",
        F("total_rating").desc(nulls_last=True),
        "canonical_slug",
    )


def search_games(
    query: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    *,
    cq: CatalogueQuery | None = None,
) -> dict:
    """Return a paginated, deterministically-ordered result set plus facets.

    ``cq`` carries the validated CAT-02 filters/sort. When omitted the call
    behaves exactly as the pre-CAT-02 endpoint did for filtering: an
    empty/whitespace-only query returns the unfiltered catalogue, now ordered
    by the stepped relevance ranking.
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

    # Text-scoped base: the governed corpus view (is_dlc=False, in_corpus=True),
    # narrowed to alias matches when a query is present. This set drives both
    # the facets and the filters; the ~312k non-governed rows stay out of the
    # public catalogue for later discovery phases.
    scoped = governed_works()
    ordered_ids: list[str] = []
    if stripped:
        ordered_ids = _ordered_matching_work_ids(normalize_title(stripped))
        scoped = scoped.filter(id__in=ordered_ids)

    facets = _facets(scoped)

    filtered = _apply_filters(scoped, cq)

    if cq.sort == "relevance":
        ordered_qs = _relevance_order(filtered)
        total = ordered_qs.count()
        page_works = list(_prefetched(ordered_qs)[start : start + page_size])
    else:
        ordered_qs = filtered.order_by(*SORT_ORDERS[cq.sort])
        total = ordered_qs.count()
        page_works = list(_prefetched(ordered_qs)[start : start + page_size])

    return {
        "results": page_works,
        "count": total,
        "page": page,
        "page_size": page_size,
        "has_next": start + page_size < total,
        "sort": cq.sort,
        "facets": facets,
    }
