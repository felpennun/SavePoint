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

from catalogue.models import GameWork
from catalogue.ratings import display_rating, savepoint_rating_stats
from evaluation.protocol import ProtocolError
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationState,
)
from recommendations.service import (
    RecommendationServiceError,
    active_corpus_version,
    recommend_for_user,
)
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.published import CONTENT_ALGORITHM_IDS
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
    "primary_tag",
    "results",
)
_ITEM_KEYS = (
    "work_id",
    "slug",
    "title",
    "score",
    "catalogue_rating",
    "catalogue_rating_count",
    "display_rating",
    "year",
    "platform_summary",
    "cover",
    "matched_tags",
)


def _with_current_display_ratings(payload: dict | None) -> dict | None:
    """Hydrate persisted recommendation items with the shared product score.

    Older snapshots may not contain ``display_rating`` because the value was
    added after they were generated. Hydrating at the response boundary keeps
    stale-but-valid snapshots numerically consistent with the game detail
    endpoint without rerunning any recommendation algorithm.
    """
    if not isinstance(payload, dict):
        return payload

    item_refs: list[dict] = []
    content = payload.get("content")
    if isinstance(content, dict):
        for section in content.values():
            if isinstance(section, dict) and isinstance(section.get("results"), list):
                item_refs.extend(item for item in section["results"] if isinstance(item, dict))
    tags = payload.get("tags")
    if isinstance(tags, dict) and isinstance(tags.get("results"), list):
        item_refs.extend(item for item in tags["results"] if isinstance(item, dict))
    enriched_items = _add_display_ratings(item_refs)
    enriched_by_identity = {id(item): enriched for item, enriched in zip(item_refs, enriched_items)}

    def enrich(item: dict) -> dict:
        return enriched_by_identity.get(id(item), item)

    enriched_content = {
        key: (
            {**section, "results": [enrich(item) for item in section["results"]]}
            if isinstance(section, dict) and isinstance(section.get("results"), list)
            else section
        )
        for key, section in content.items()
    } if isinstance(content, dict) else content
    enriched_tags = (
        {**tags, "results": [enrich(item) for item in tags["results"]]}
        if isinstance(tags, dict) and isinstance(tags.get("results"), list)
        else tags
    )
    return {**payload, "content": enriched_content, "tags": enriched_tags}


def _add_display_ratings(items: list[dict]) -> list[dict]:
    """Add the product-only blended score without changing algorithm output."""
    work_ids = [item.get("work_id") for item in items if item.get("work_id")]
    works = {
        str(work.id): work
        for work in GameWork.objects.in_bulk(work_ids).values()
    }
    stats = savepoint_rating_stats(works.keys())
    enriched = []
    for item in items:
        work = works.get(str(item.get("work_id")))
        if work is None:
            enriched.append(item)
            continue
        enriched.append(
            {
                **item,
                "display_rating": display_rating(
                    work, savepoint_stats=stats.get(work.id, (None, 0))
                ),
            }
        )
    return enriched


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

        payload = rank_genre_taste_v1(
            request.user,
            corpus_version=active_corpus_version(),
            limit=limit,
        )
        presentation_results = _add_display_ratings(payload["results"])
        return Response(
            {
                **{key: payload[key] for key in _DTO_KEYS},
                "results": [
                    {key: item[key] for key in _ITEM_KEYS} for item in presentation_results
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
        "display_rating",
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
        if algorithm_id not in CONTENT_ALGORITHM_IDS:
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
        presentation_results = _add_display_ratings(payload["results"])
        return Response(
            {
                **{key: payload[key] for key in self._DTO_KEYS if key != "results"},
                "results": [
                    {key: item[key] for key in self._ITEM_KEYS}
                    for item in presentation_results
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
        has_live_refresh = bool(
            job_statuses
            & {RecommendationJobStatus.QUEUED, RecommendationJobStatus.RUNNING}
        )
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
            status = "building" if has_live_refresh else "needs_refresh"
        elif not complete_job_set or not has_live_refresh:
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
                "sections": _with_current_display_ratings(snapshot.payload) if snapshot else None,
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
