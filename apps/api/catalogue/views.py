"""Catalogue list/search/detail endpoints -- entirely local, zero external
calls at request time (CAT-06/OPS-03)."""

from __future__ import annotations

import hashlib

from django.core.cache import cache
from django.db.models import Max, Min
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle
from rest_framework.views import APIView

from catalogue.models import (
    AssetAttribution,
    GameWork,
    Platform,
    RelatedContent,
    SourceRecord,
)
from catalogue.new_releases import get_or_bootstrap_snapshot
from catalogue.search import (
    DEFAULT_PAGE_SIZE,
    FilterValidationError,
    parse_catalogue_query,
    search_games,
)
from catalogue.ratings import savepoint_rating_stats
from catalogue.serializers import (
    SAVEPOINT_STATS_CONTEXT_KEY,
    GameCardSerializer,
    GameDetailSerializer,
    _cover,
    _display_title,
)
from library.models import LibraryEntry


LIST_CACHE_TTL_SECONDS = 120
DETAIL_CACHE_TTL_SECONDS = 300
# Public, short-lived: browsers and any CDN in front may reuse these answers for
# a minute and serve a slightly older copy while they revalidate.
PUBLIC_CACHE_CONTROL = "public, max-age=60, s-maxage=120, stale-while-revalidate=300"


def _public_cache(response: Response) -> Response:
    response["Cache-Control"] = PUBLIC_CACHE_CONTROL
    return response


def _card_context(works: list[GameWork]) -> dict:
    """Serializer context with a bulk SavePoint-rating stats map so a card
    list renders ``display_rating`` without a query per row."""
    return {
        SAVEPOINT_STATS_CONTEXT_KEY: savepoint_rating_stats([w.id for w in works])
    }

# DLC/expansion linkage relations surfaced by the "Para tus juegos" shelf.
DLC_RELATIONS = ("dlc", "expansion")


class NewReleasesThrottle(SimpleRateThrottle):
    """Per-IP scoped throttle for the anonymous "Novedades" shelf (D-24,
    threat T-02-05-04). Its own scope with an explicit rate so it never
    shares a bucket with catalogue search and needs no settings change."""

    scope = "catalogue_new_releases"
    rate = "120/min"

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


def _parse_page(raw: str | None) -> int:
    try:
        value = int(raw) if raw else 1
    except (TypeError, ValueError):
        raise FilterValidationError("invalid_page", "page must be a positive integer") from None
    if value < 1:
        raise FilterValidationError("invalid_page", "page must be a positive integer")
    return value


class GameListView(APIView):
    """List/search/filter games.

    GET /api/catalogue/games/?q=&page=&platform=&genre=&year_from=&year_to=
        &min_rating=&sort=

    Filters intersect. ``sort`` is a fixed allowlist key (never interpolated
    into ``order_by``). An unknown ``sort`` or an out-of-range / non-numeric
    ``year_*`` / ``min_rating`` is a bounded 400 (CAT-02, threat T-01.1-05).

    Anonymous scoped throttle (M-05): a text query runs a trigram lookup, so
    an unauthenticated request loop is rate-limited.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "catalogue_search"

    def get(self, request: Request) -> Response:
        try:
            cq = parse_catalogue_query(request.query_params)
        except FilterValidationError as exc:
            return Response({"detail": str(exc), "code": exc.code}, status=400)
        try:
            page = _parse_page(request.query_params.get("page"))
        except FilterValidationError as exc:
            return Response({"detail": str(exc), "code": exc.code}, status=400)
        # ``facets=lite`` is what the web page sends: only the filter options the
        # filter bar shows, cached; the full facet set stays the default.
        lite_facets = request.query_params.get("facets") == "lite"
        # The answer only depends on the validated query, never on who asks, so
        # the lite (web) variant is kept for a couple of minutes: the first visit
        # to a given filter pays for the count, the next ones are instant.
        cache_key = None
        if lite_facets:
            signature = "|".join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
            cache_key = "catalogue:list:" + hashlib.sha256(signature.encode("utf-8")).hexdigest()
            cached = cache.get(cache_key)
            if cached is not None:
                return _public_cache(Response(cached))
        result = search_games(cq.q, page=page, page_size=DEFAULT_PAGE_SIZE, cq=cq, lite_facets=lite_facets)
        results = list(result["results"])
        payload = {
            "results": GameCardSerializer(
                results, many=True, context=_card_context(results)
            ).data,
            "count": result["count"],
            "page": result["page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
            "sort": result["sort"],
            "facets": result["facets"],
        }
        if cache_key is not None:
            cache.set(cache_key, payload, LIST_CACHE_TTL_SECONDS)
            return _public_cache(Response(payload))
        return Response(payload)


class GameDetailView(APIView):
    """GET /api/catalogue/games/<slug>/"""

    def get(self, request: Request, slug: str) -> Response:
        locale = request.query_params.get("locale")
        if locale not in {"es", "en"}:
            locale = "en"
        # The detail answer depends only on the slug and the locale (never on
        # who asks), and building it takes a dozen queries, so it is kept for a
        # few minutes. Misses (404) are never cached.
        cache_key = "catalogue:detail:" + hashlib.sha256(f"{slug}|{locale}".encode("utf-8")).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return _public_cache(Response(cached))
        try:
            work = (
                GameWork.objects.select_related()
                .prefetch_related(
                    "releases__platform",
                    "releases__editions",
                    "assets",
                    "source_records",
                    "curated_labels",
                    "related_children__child_work__assets",
                    "related_children__child_work__releases__platform",
                )
                .get(canonical_slug=slug)
            )
        except GameWork.DoesNotExist:
            # Generic 404 -- never confirm/deny via a distinguishing message.
            return Response({"detail": "Not found."}, status=404)
        payload = GameDetailSerializer(work, context={"locale": locale}).data
        cache.set(cache_key, payload, DETAIL_CACHE_TTL_SECONDS)
        return _public_cache(Response(payload))


class NewReleasesView(APIView):
    """GET /api/catalogue/new-releases/ -- the home "Novedades" shelf (D-24).

    Serves the materialised ``NewReleasesSnapshot``: up to 20 governed,
    non-DLC works released in the last ~6 months, ranked by
    ``0.70 * recency + 0.30 * PopScore``. The ranking is recomputed only
    when the IGDB catalogue is (re-)imported (``materialize_new_releases``,
    also in the container startup chain) -- never per request -- so every
    page load returns the same frozen list until the next import. An empty
    window is ``[]`` with 200 (the frontend hides the whole shelf).
    """

    throttle_classes = [NewReleasesThrottle]

    def get(self, request: Request) -> Response:
        snapshot = get_or_bootstrap_snapshot()
        works_by_id = {
            str(work.id): work
            for work in GameWork.objects.filter(pk__in=snapshot.work_ids).prefetch_related(
                "assets", "releases__platform", "curated_labels"
            )
        }
        # Preserve the frozen order; drop any id that has since disappeared.
        works = [works_by_id[pk] for pk in snapshot.work_ids if pk in works_by_id]
        return Response(
            GameCardSerializer(
                works, many=True, context=_card_context(works)
            ).data
        )


class OwnedGamesDlcView(APIView):
    """GET /api/catalogue/owned-dlc/ -- the "Para tus juegos" shelf (D-15).

    Owner-scoped by construction (threat T-02-05-01): ``IsAuthenticated``
    and derived solely from ``request.user``'s library. No target-user
    parameter is read. Returns the DLC / expansions of base games the user
    owns, grouped by base game, projected through an explicit allowlist
    tuple (threat T-02-05-05). Child works are returned even when they sit
    outside ``governed_works()`` (D-03). A user with no resolvable DLC gets
    ``{"groups": []}`` and 200, never an error.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        library_work_ids = LibraryEntry.objects.filter(
            user=request.user
        ).values_list("work_id", flat=True)
        rows = (
            RelatedContent.objects.filter(
                parent_work_id__in=library_work_ids,
                relation__in=DLC_RELATIONS,
            )
            .select_related("parent_work", "child_work")
            .prefetch_related("child_work__assets")
            .order_by("parent_work__canonical_slug", "child_work__canonical_slug")
        )

        groups: dict[object, dict] = {}
        for row in rows:
            group = groups.setdefault(
                row.parent_work_id,
                {
                    "base_game": {
                        "slug": row.parent_work.canonical_slug,
                        "title": _display_title(row.parent_work),
                    },
                    "dlc": [],
                },
            )
            group["dlc"].append(
                {
                    "work_id": str(row.child_work_id),
                    "slug": row.child_work.canonical_slug,
                    "title": _display_title(row.child_work),
                    "cover": _cover(row.child_work),
                    "relation": row.relation,
                }
            )

        return Response({"groups": list(groups.values())})


CATALOGUE_STATS_CACHE_KEY = "catalogue:home-stats"
CATALOGUE_STATS_TTL_SECONDS = 3600


class CatalogueStatsView(APIView):
    """GET /api/catalogue/stats/ -- the figures shown on the home page: size of the
    governed catalogue, games with an IGDB score, platforms and the release years
    covered. Aggregates only (no per-user data), cached for an hour."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request: Request) -> Response:
        stats = cache.get(CATALOGUE_STATS_CACHE_KEY)
        if stats is None:
            from catalogue.corpus import governed_works
            from catalogue.search import ALLOWLIST_SLUGS

            works = governed_works()
            years = works.aggregate(first=Min("first_release_date"), last=Max("first_release_date"))
            stats = {
                "games": works.count(),
                "rated": works.filter(total_rating__isnull=False).count(),
                # The platforms the catalogue filter offers: the allow-listed ones
                # with at least one release in the governed catalogue.
                "platforms": Platform.objects.filter(slug__in=ALLOWLIST_SLUGS, releases__work__in=works)
                .distinct()
                .count(),
                "first_year": years["first"].year if years["first"] else None,
                "last_year": years["last"].year if years["last"] else None,
            }
            cache.set(CATALOGUE_STATS_CACHE_KEY, stats, CATALOGUE_STATS_TTL_SECONDS)
        return Response(stats)


class SourcesView(APIView):
    """GET /api/catalogue/sources/ -- dataset provenance summary for the
    Sources & Methodology page (DATA-02, D-08). Derived from the already-
    imported SourceRecord/AssetAttribution rows, not by re-reading raw
    manifest files across a service boundary."""

    def get(self, request: Request) -> Response:
        record = SourceRecord.objects.order_by("-retrieved_at").first()
        if record is None:
            return Response({"detail": "Sources unavailable."}, status=503)

        return Response(
            {
                "source": record.source,
                "source_url": record.source_url,
                "licence": record.licence,
                "retrieved_at": record.retrieved_at,
                "snapshot_sha256": record.snapshot_sha256,
                "record_count": GameWork.objects.count(),
                "approved_asset_count": AssetAttribution.objects.filter(display_allowed=True).count(),
                "total_asset_candidate_count": AssetAttribution.objects.count(),
            }
        )
