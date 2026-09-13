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
from django.db.models import (
    Case,
    Count,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import ExtractYear

from catalogue.corpus import ALLOWLIST_SLUGS, governed_works
from catalogue.models import (
    CorpusPopularityScore,
    CorpusVersion,
    CuratedLabel,
    Developer,
    Edition,
    Franchise,
    GameAlias,
    GameMode,
    GameWork,
    Genre,
    Platform,
    Publisher,
)
from django.utils.text import slugify
from catalogue.normalization import normalize_title

TRIGRAM_SIMILARITY_THRESHOLD = 0.3
# Cap the fuzzy-match candidate set so a single request can never fan out to
# the whole alias table (M-05). Comfortably larger than any realistic page.
TRIGRAM_CANDIDATE_CAP = 200
DEFAULT_PAGE_SIZE = 25

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
SORT_KEYS: tuple[str, ...] = ("popscore_desc", "relevance", *SORT_ORDERS.keys())
DEFAULT_SORT_NO_QUERY = "popscore_desc"
DEFAULT_SORT_WITH_QUERY = "popscore_desc"


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
    tags: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    editions: tuple[str, ...] = ()
    genres: tuple[str, ...] = ()
    franchises: tuple[str, ...] = ()
    developers: tuple[str, ...] = ()
    publishers: tuple[str, ...] = ()
    modes: tuple[str, ...] = ()
    year_from: int | None = None
    year_to: int | None = None
    date_from: date | None = None
    date_to: date | None = None
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


def _raw_values(params: Mapping[str, str], key: str) -> list[str]:
    getlist = getattr(params, "getlist", None)
    if callable(getlist):
        return list(getlist(key))
    one = params.get(key)
    return [one] if one is not None else []


def _multi_values(params: Mapping[str, str], key: str, *aliases: str) -> tuple[str, ...]:
    """Read every repeated value of ``key`` -- ``getlist`` when the mapping
    supports it (DRF ``request.query_params`` / Django ``QueryDict``), else the
    single ``get`` value -- then trim, drop blanks, and de-duplicate in order.

    Raises :class:`FilterValidationError` past :data:`MAX_MULTISELECT_VALUES`
    repeated values so a request cannot fan a query out into an unbounded join
    chain (threat T-02-03-02).
    """
    raw: list[str] = []
    for candidate in (key, *aliases):
        raw.extend(_raw_values(params, candidate))
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


def _parse_date_bound(raw: str, code: str, label: str, *, end: bool) -> date:
    value = str(raw).strip()
    try:
        if len(value) == 4 and value.isdigit():
            year = int(value)
            return date(year, 12, 31) if end else date(year, 1, 1)
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise FilterValidationError(code, f"{label} must be YYYY or YYYY-MM-DD") from None


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

    tags = _multi_values(params, "tag", "tags")
    platforms = _multi_values(params, "platform", "platforms")
    editions = _multi_values(params, "edition", "editions")
    genres = _multi_values(params, "genre", "genres")
    franchises = _multi_values(params, "franchise", "franchises")
    developers = _multi_values(params, "developer", "developers")
    publishers = _multi_values(params, "publisher", "publishers")
    modes = _multi_values(params, "mode", "modes")

    date_from = date_to = None
    if params.get("date_from"):
        date_from = _parse_date_bound(params["date_from"], "invalid_date", "date_from", end=False)
    elif year_from is not None:
        date_from = date(year_from, 1, 1)
    if params.get("date_to"):
        date_to = _parse_date_bound(params["date_to"], "invalid_date", "date_to", end=True)
    elif year_to is not None:
        date_to = date(year_to, 12, 31)
    date_ceiling = date(year_ceiling, 12, 31)
    for value in (date_from, date_to):
        if value is not None and not (date(YEAR_MIN, 1, 1) <= value <= date_ceiling):
            raise FilterValidationError(
                "date_out_of_range", f"date must be between {YEAR_MIN} and {year_ceiling}"
            )
    if date_from is not None and date_to is not None and date_from > date_to:
        date_from, date_to = date_to, date_from

    return CatalogueQuery(
        q=q,
        tags=tags,
        platforms=platforms,
        editions=editions,
        genres=genres,
        franchises=franchises,
        developers=developers,
        publishers=publishers,
        modes=modes,
        year_from=year_from,
        year_to=year_to,
        date_from=date_from,
        date_to=date_to,
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
    if cq.editions:
        editions = Edition.objects.filter(release__work__in=qs).values_list("name", flat=True)
        requested_editions = set(cq.editions)
        valid_editions = {
            name for name in editions if slugify(name) in requested_editions
        }
        if valid_editions:
            qs = qs.filter(releases__editions__name__in=valid_editions)
            joined = True
    for values, relation in (
        (cq.genres, "genres"),
        (cq.franchises, "franchises"),
        (cq.developers, "developers"),
        (cq.publishers, "publishers"),
        (cq.modes, "game_modes"),
    ):
        if values:
            model = {
                "genres": Genre,
                "franchises": Franchise,
                "developers": Developer,
                "publishers": Publisher,
                "game_modes": GameMode,
            }[relation]
            valid = set(model.objects.filter(slug__in=values).values_list("slug", flat=True))
            for slug in values:
                if slug in valid:
                    qs = qs.filter(**{f"{relation}__slug": slug})
                    joined = True
    if cq.tags:
        valid_tags = set(
            CuratedLabel.objects.filter(slug__in=cq.tags).values_list("slug", flat=True)
        )
        for slug in cq.tags:
            if slug in valid_tags:
                qs = qs.filter(curated_labels__slug=slug)
                joined = True
    if cq.year_from is not None:
        qs = qs.filter(first_release_date__gte=date(cq.year_from, 1, 1))
    if cq.year_to is not None:
        qs = qs.filter(first_release_date__lte=date(cq.year_to, 12, 31))
    if cq.date_from is not None:
        qs = qs.filter(first_release_date__gte=cq.date_from)
    if cq.date_to is not None:
        qs = qs.filter(first_release_date__lte=cq.date_to)
    if cq.min_rating is not None:
        qs = qs.filter(total_rating__gte=cq.min_rating)
    if joined:
        qs = qs.distinct()
    return qs


def _prefetched(qs: QuerySet[GameWork]) -> QuerySet[GameWork]:
    return qs.prefetch_related(
        "releases__platform",
        "assets",
        "curated_labels",
    )


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


def _relation_facets(scoped: QuerySet[GameWork], model, relation: str) -> list[dict]:
    rows = (
        model.objects.filter(**{f"{relation}__in": scoped})
        .annotate(count=Count(f"{relation}", distinct=True))
        .order_by("name", "slug")
        .values("slug", "name", "count")
    )
    return [
        {"slug": row["slug"], "name": row["name"], "count": row["count"]}
        for row in rows
    ]


def _edition_facets(scoped: QuerySet[GameWork]) -> list[dict]:
    """Return Edition options using a derived slug, preserving its hierarchy."""
    rows = (
        Edition.objects.filter(release__work__in=scoped)
        .annotate(count=Count("release__work", distinct=True))
        .order_by("name", "id")
        .values("name", "count")
    )
    deduped: dict[str, dict] = {}
    for row in rows:
        option_slug = slugify(row["name"])
        if not option_slug:
            continue
        entry = deduped.setdefault(
            option_slug,
            {"slug": option_slug, "name": row["name"], "count": 0},
        )
        entry["count"] += row["count"]
    return [deduped[key] for key in sorted(deduped, key=lambda value: (deduped[value]["name"], value))]


def _facets(scoped: QuerySet[GameWork]) -> dict:
    """Facet options + counts over the text-scoped governed set.

    Facets are deliberately calculated before the requested page (and before
    the optional facet filters) so a copied GET URL always describes the same
    available catalogue vocabulary. Each dimension is one bounded aggregate;
    no page-sized Python loop or external provider is involved.
    """
    platforms = [
        {"slug": row["slug"], "name": row["name"], "count": row["count"]}
        for row in Platform.objects.filter(
            slug__in=ALLOWLIST_SLUGS, releases__work__in=scoped
        )
        .annotate(count=Count("releases__work", distinct=True))
        .order_by("name")
        .values("slug", "name", "count")
    ]
    tags = _relation_facets(scoped, CuratedLabel, "works")
    genres = _relation_facets(scoped, Genre, "works")
    franchises = _relation_facets(scoped, Franchise, "works")
    developers = _relation_facets(scoped, Developer, "works")
    publishers = _relation_facets(scoped, Publisher, "works")
    modes = _relation_facets(scoped, GameMode, "works")
    dates = [
        {"value": str(row["year"]), "label": str(row["year"]), "count": row["count"]}
        for row in scoped.filter(first_release_date__isnull=False)
        .annotate(year=ExtractYear("first_release_date"))
        .values("year")
        .annotate(count=Count("id"))
        .order_by("year")
    ]
    span = scoped.aggregate(min=Min("first_release_date"), max=Max("first_release_date"))
    return {
        "platforms": platforms,
        "editions": _edition_facets(scoped),
        "genres": genres,
        "franchises": franchises,
        "developers": developers,
        "publishers": publishers,
        "modes": modes,
        "tags": tags,
        "dates": dates,
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
        "id",
    )


def _popscore_order(qs: QuerySet[GameWork]) -> QuerySet[GameWork]:
    """Order by the materialised PopScore from the active corpus version."""

    active_version = (
        CorpusVersion.objects.filter(is_active=True)
        .order_by("-created_at")
        .values("version")[:1]
    )
    score = (
        CorpusPopularityScore.objects.filter(
            work_id=OuterRef("pk"),
            corpus_version=Subquery(active_version),
        )
        .values("score")[:1]
    )
    return qs.annotate(popscore=Subquery(score)).order_by(
        F("popscore").desc(nulls_last=True),
        "canonical_slug",
        "id",
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

    if cq.sort == "popscore_desc":
        ordered_qs = _popscore_order(filtered)
        total = ordered_qs.count()
        page_works = list(_prefetched(ordered_qs)[start : start + page_size])
    elif cq.sort == "relevance":
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
