"""Read-only HTTP views over the frozen research publication."""

from __future__ import annotations

from django.http import HttpResponse
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from evaluation.access import ResearchViewerPermission
from evaluation.panel_contract import (
    PUBLISHED_RUN_ID,
    PublicationContractError,
    build_comparison_payload,
    build_export_payload,
    load_published_run,
)
from evaluation.serializers import (
    serialize_artifacts,
    serialize_comparison,
    serialize_runs,
)


QUERY_NAMES = {"run", "algorithm", "cohort", "metric"}
EXPORT_QUERY_NAMES = QUERY_NAMES | {"format"}
CONTRACT_FILTER_NAMES = {
    "run": "run_id",
    "algorithm": "algorithm_id",
    "cohort": "cohort_id",
    "metric": "metric_id",
}
EXPORT_FORMATS = {"csv", "json", "svg"}
NEUTRAL_ERROR = {"detail": "Invalid research request."}


def _query_values(request: Request, allowed: set[str]) -> tuple[dict[str, str] | None, Response | None]:
    values: dict[str, str] = {}
    for name in request.query_params.keys():
        if name not in allowed:
            return None, Response(NEUTRAL_ERROR, status=400)
        entries = request.query_params.getlist(name)
        if len(entries) != 1 or not entries[0]:
            return None, Response(NEUTRAL_ERROR, status=400)
        values[name] = entries[0]
    return values, None


def _contract_filters(values: dict[str, str]) -> dict[str, str]:
    return {
        CONTRACT_FILTER_NAMES[name]: value
        for name, value in values.items()
        if name in CONTRACT_FILTER_NAMES
    }


def _publication_error() -> Response:
    return Response({"detail": "Published research evidence is unavailable."}, status=503)


class ResearchReadOnlyView(APIView):
    permission_classes: list[type[BasePermission]] = [ResearchViewerPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "research"

    def finalize_response(self, request, response, *args, **kwargs):  # noqa: ANN001
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        response["Vary"] = "Cookie"
        return response


class ResearchRunsView(ResearchReadOnlyView):
    def get(self, request: Request) -> Response:
        values, error = _query_values(request, set())
        if error is not None:
            return error
        del values
        try:
            published = load_published_run()
            payload = build_comparison_payload(published)
        except PublicationContractError:
            return _publication_error()
        return Response(serialize_runs(payload))


class ResearchComparisonView(ResearchReadOnlyView):
    def get(self, request: Request) -> Response:
        values, error = _query_values(request, QUERY_NAMES)
        if error is not None:
            return error
        assert values is not None
        try:
            published = load_published_run(values.get("run", PUBLISHED_RUN_ID))
            payload = build_comparison_payload(
                published,
                filters=_contract_filters(values),
            )
        except PublicationContractError:
            return Response(NEUTRAL_ERROR, status=400)
        return Response(serialize_comparison(payload))


class ResearchArtifactsView(ResearchReadOnlyView):
    def get(self, request: Request) -> Response:
        values, error = _query_values(request, {"run"})
        if error is not None:
            return error
        assert values is not None
        try:
            published = load_published_run(values.get("run", PUBLISHED_RUN_ID))
        except PublicationContractError:
            return Response(NEUTRAL_ERROR, status=400)
        return Response(serialize_artifacts(published))


class ResearchExportsView(ResearchReadOnlyView):
    def get(self, request: Request) -> HttpResponse | Response:
        values, error = _query_values(request, EXPORT_QUERY_NAMES)
        if error is not None:
            return error
        assert values is not None
        format_name = values.get("format")
        if format_name not in EXPORT_FORMATS:
            return Response(NEUTRAL_ERROR, status=400)
        try:
            published = load_published_run(values.get("run", PUBLISHED_RUN_ID))
            export = build_export_payload(
                published,
                format=format_name,
                filters=_contract_filters(values),
            )
        except PublicationContractError:
            return Response(NEUTRAL_ERROR, status=400)

        response = HttpResponse(export["body"], content_type=export["content_type"])
        response["Content-Disposition"] = f'attachment; filename="{export["filename"]}"'
        response["X-Content-SHA256"] = export["checksum_sha256"]
        response["Cache-Control"] = "private, no-store"
        response["Vary"] = "Cookie"
        return response


__all__ = [
    "ResearchArtifactsView",
    "ResearchComparisonView",
    "ResearchExportsView",
    "ResearchRunsView",
]
