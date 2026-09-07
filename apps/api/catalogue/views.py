"""Catalogue list/search/detail endpoints -- entirely local, zero external
calls at request time (CAT-06/OPS-03)."""

from __future__ import annotations

from datetime import date, timedelta

from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle
from rest_framework.views import APIView

from catalogue.corpus import governed_works
from catalogue.models import AssetAttribution, GameWork, RelatedContent, SourceRecord
from catalogue.search import (
    DEFAULT_PAGE_SIZE,
    FilterValidationError,
    parse_catalogue_query,
    search_games,
)
from catalogue.serializers import (
    GameCardSerializer,
    GameDetailSerializer,
    _cover,
    _display_title,
)
from library.models import LibraryEntry

# DLC/expansion linkage relations surfaced by the "Para tus juegos" shelf.
DLC_RELATIONS = ("dlc", "expansion")

# ~6 months, expressed in days so the window is a single indexed btree
# comparison on ``first_release_date`` (no calendar arithmetic per row).
NEW_RELEASE_WINDOW_DAYS = 183
NEW_RELEASE_LIMIT = 20


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
        return 1
    return value if value > 0 else 1


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
        page = _parse_page(request.query_params.get("page"))
        result = search_games(cq.q, page=page, page_size=DEFAULT_PAGE_SIZE, cq=cq)
        return Response(
            {
                "results": GameCardSerializer(result["results"], many=True).data,
                "count": result["count"],
                "page": result["page"],
                "page_size": result["page_size"],
                "has_next": result["has_next"],
                "sort": result["sort"],
                "facets": result["facets"],
            }
        )


class GameDetailView(APIView):
    """GET /api/catalogue/games/<slug>/"""

    def get(self, request: Request, slug: str) -> Response:
        try:
            work = (
                GameWork.objects.select_related()
                .prefetch_related(
                    "releases__platform", "releases__editions", "assets", "source_records", "genres"
                )
                .get(canonical_slug=slug)
            )
        except GameWork.DoesNotExist:
            # Generic 404 -- never confirm/deny via a distinguishing message.
            return Response({"detail": "Not found."}, status=404)
        return Response(GameDetailSerializer(work).data)


class NewReleasesView(APIView):
    """GET /api/catalogue/new-releases/ -- the home "Novedades" shelf (D-24).

    Up to 20 governed works whose ``first_release_date`` falls in the last
    ~6 months, newest first with ``canonical_slug`` as the deterministic
    tie-break. An empty window is ``[]`` with 200 (the frontend hides the
    whole shelf), never an error. DLC and works outside the governed corpus
    are excluded by ``governed_works()``.
    """

    throttle_classes = [NewReleasesThrottle]

    def get(self, request: Request) -> Response:
        cutoff = date.today() - timedelta(days=NEW_RELEASE_WINDOW_DAYS)
        works = (
            governed_works()
            .filter(first_release_date__gte=cutoff)
            .order_by(F("first_release_date").desc(nulls_last=True), "canonical_slug")
            .prefetch_related("assets", "releases__platform", "genres")[
                :NEW_RELEASE_LIMIT
            ]
        )
        return Response(GameCardSerializer(works, many=True).data)


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
