"""Authenticated genre-taste recommendations API (REC-10, D-09).

Threat T-01.1-10 (information disclosure): ``IsAuthenticated`` plus a
``request.user``-only service call -- the endpoint accepts no target user
and never returns another account's taste. Threat T-01.1-11 (DoS): the
``limit`` query parameter is parsed strictly and clamped to the service's
documented bound before the ranking query runs.
"""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogue.models import CorpusVersion
from recommendations.content.rank import rank_content_v1
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.genre_heuristic import rank_genre_taste_v1

# Allowlist echoed back verbatim so a future change to the service DTO can
# never widen the wire contract without a deliberate edit here.
_DTO_KEYS = (
    "algorithm_id",
    "generated_at",
    "input_snapshot_sha256",
    "insufficient_history",
    "limitation",
    "results",
)
_ITEM_KEYS = (
    "work_id",
    "slug",
    "title",
    "score",
    "catalogue_rating",
    "catalogue_rating_count",
    "year",
    "platform_summary",
    "cover",
    "matched_genres",
)


class RecommendationsView(APIView):
    """GET /api/recommendations/genre-taste/

    Owner-scoped by construction: the ranking is derived solely from
    ``request.user``'s own library activity. Distinct from the public
    popularity baseline (REC-02) and from Phase 6's model comparison
    (REC-03) -- the ``algorithm_id`` and ``limitation`` in the response
    make that boundary explicit for the frontend.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        raw_limit = request.query_params.get("limit")
        if raw_limit is not None:
            try:
                limit: int | None = int(raw_limit)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "limit must be an integer between 1 and 50."},
                    status=400,
                )
        else:
            limit = None

        payload = rank_genre_taste_v1(request.user, limit=limit)
        return Response(
            {
                **{key: payload[key] for key in _DTO_KEYS},
                "results": [
                    {key: item[key] for key in _ITEM_KEYS} for item in payload["results"]
                ],
            }
        )


class ContentRecsView(APIView):
    """GET /api/recommendations/content/ for the signed-in owner only."""

    permission_classes = [IsAuthenticated]

    _DTO_KEYS = (
        "algorithm_id",
        "generated_at",
        "input_snapshot_sha256",
        "feature_set_version",
        "corpus_version",
        "snapshot_sha256",
        "insufficient_history",
        "limitation",
        "results",
    )
    _ITEM_KEYS = (
        "work_id",
        "slug",
        "title",
        "score",
        "contributions",
        "rating_term",
        "rating_term_is_fallback",
    )

    def get(self, request: Request) -> Response:
        raw_limit = request.query_params.get("limit")
        if raw_limit is not None:
            try:
                limit: int | None = int(raw_limit)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "limit must be an integer between 1 and 50."},
                    status=400,
                )
        else:
            limit = None

        algorithm_id = request.query_params.get(
            "algorithm_id", "content-cbf-weighted-v1"
        )
        if algorithm_id not in ALGORITHM_REGISTRY:
            return Response({"detail": "unknown algorithm_id"}, status=400)

        corpus_version = (
            CorpusVersion.objects.filter(is_active=True)
            .order_by("-created_at")
            .values_list("version", flat=True)
            .first()
        )
        payload = rank_content_v1(
            request.user,
            algorithm_id,
            limit=limit,
            corpus_version=corpus_version,
        )
        return Response(
            {
                **{key: payload[key] for key in self._DTO_KEYS if key != "results"},
                "results": [
                    {key: item[key] for key in self._ITEM_KEYS}
                    for item in payload["results"]
                ],
            }
        )
