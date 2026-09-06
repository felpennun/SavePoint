"""Catalogue list/search/detail endpoints -- entirely local, zero external
calls at request time (CAT-06/OPS-03)."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from catalogue.models import AssetAttribution, GameWork, SourceRecord
from catalogue.search import (
    DEFAULT_PAGE_SIZE,
    FilterValidationError,
    parse_catalogue_query,
    search_games,
)
from catalogue.serializers import GameCardSerializer, GameDetailSerializer


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
