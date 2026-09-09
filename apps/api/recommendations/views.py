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
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from evaluation.protocol import ProtocolError
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationState,
)
from recommendations.service import RecommendationServiceError, recommend_for_user
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.genre_heuristic import rank_genre_taste_v1
from recommendations.published import SECTION_ALGORITHM_IDS, configuration_fingerprint

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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "recommendations"

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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "recommendations"

    _DTO_KEYS = (
        "protocol_version",
        "algorithm_id",
        "generated_at",
        "input_snapshot_sha256",
        "feature_set_version",
        "corpus_version",
        "snapshot_sha256",
        "popscore_snapshot_sha256",
        "candidate_manifest_sha256",
        "candidate_count",
        "explorable_count",
        "eligibility_cutoff_date",
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
        "year",
        "platform_summary",
        "cover",
        "reason",
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

        try:
            payload = recommend_for_user(
                request.user,
                algorithm_id,
                limit=limit,
            )
        except (ProtocolError, RecommendationServiceError):
            return Response(
                {"detail": "recommendations are temporarily unavailable"}, status=503
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


class RecommendationSnapshotView(APIView):
    """Return the latest complete personal bundle without waiting for refresh."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        state, _ = RecommendationState.objects.get_or_create(user=request.user)
        snapshot = state.active_snapshot
        config_fingerprint = configuration_fingerprint()
        jobs = list(
            state.user.recommendation_refresh_jobs.filter(
                requested_revision=state.collection_revision,
                configuration_fingerprint=config_fingerprint,
                algorithm_id__in=SECTION_ALGORITHM_IDS,
            )
            .order_by("algorithm_id")
        )
        complete_job_set = len(jobs) == len(SECTION_ALGORITHM_IDS)
        job_statuses = {job.status for job in jobs}
        current_snapshot = (
            snapshot is not None
            and snapshot.collection_revision == state.collection_revision
            and snapshot.configuration_fingerprint == config_fingerprint
        )
        if state.collection_revision == 0 and snapshot is None:
            status = "empty"
        elif current_snapshot:
            status = "ready"
        elif snapshot is None:
            # A collection may predate the asynchronous worker. Do not create
            # work merely because the user opened the page; a new library
            # mutation will create the next revision and enqueue it via the
            # signal. Existing users therefore see the onboarding state until
            # they update their catalogue.
            status = "building" if jobs else "needs_refresh"
        elif not complete_job_set:
            status = "needs_refresh"
        else:
            status = "stale"

        response = Response(
            {
                "status": status,
                "current_revision": state.collection_revision,
                "published_revision": snapshot.collection_revision if snapshot else None,
                "generated_at": snapshot.generated_at.isoformat() if snapshot else None,
                "job_status": "failed" if RecommendationJobStatus.FAILED in job_statuses else (
                    "running" if RecommendationJobStatus.RUNNING in job_statuses else (
                        "queued" if RecommendationJobStatus.QUEUED in job_statuses else None
                    )
                ),
                "error": "refresh_failed" if RecommendationJobStatus.FAILED in job_statuses else None,
                "sections": snapshot.payload if snapshot else None,
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
