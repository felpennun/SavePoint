"""Manual, allowlisted DTO projections for the research API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any

from evaluation.access import can_manage_platform, can_view_research
from evaluation.panel_contract import (
    ARTIFACT_RELATIVE_PATH,
    COHORT_RELATIVE_PATH,
    PROTOCOL_RELATIVE_PATH,
    PublishedRun,
)


RUN_KEYS = (
    "run_id",
    "status",
    "published_at",
    "protocol_version",
    "corpus_version",
    "split",
    "commit_sha",
    "feature_set_version",
    "seed_count",
    "artifact_sha256",
    "cohort_sha256",
    "protocol_sha256",
    "snapshot_sha256",
    "popscore_snapshot_sha256",
    "split_manifest_sha256",
)
ROW_KEYS = (
    "algorithm_id",
    "algorithm_label",
    "cohort_id",
    "cohort_label",
    "k",
    "evaluable_count",
    "population_count",
    "metrics",
    "timing",
    "not_evaluable_reason",
)
METRIC_KEYS = (
    "metric_id",
    "value",
    "unit",
    "higher_is_better",
    "unavailable_reason",
)
TIMING_KEYS = ("duration_seconds", "wall_ms", "cpu_ms", "unavailable_reason")


def _allowlisted(mapping: Mapping[str, Any], keys: Sequence[str]) -> dict[str, Any]:
    return {key: mapping.get(key) for key in keys}


def serialize_run(run: Mapping[str, Any]) -> dict[str, Any]:
    return _allowlisted(run, RUN_KEYS)


def serialize_option(option: Mapping[str, Any]) -> dict[str, str]:
    return {"id": str(option["id"]), "label": str(option["label"])}


def serialize_runs(payload: Mapping[str, Any]) -> dict[str, Any]:
    options = payload["filter_options"]
    return {
        "runs": [serialize_run(payload["run"])],
        "algorithms": [serialize_option(item) for item in options["algorithms"]],
        "cohorts": [serialize_option(item) for item in options["cohorts"]],
        "metrics": [serialize_option(item) for item in options["metrics"]],
        "formats": [serialize_option(item) for item in options["formats"]],
    }


def _serialize_metric(metric: Mapping[str, Any]) -> dict[str, Any]:
    return _allowlisted(metric, METRIC_KEYS)


def _serialize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    metrics = row["metrics"]
    timing = row["timing"]
    return {
        "algorithm_id": row["algorithm_id"],
        "algorithm_label": row["algorithm_label"],
        "cohort_id": row["cohort_id"],
        "cohort_label": row["cohort_label"],
        "k": row["k"],
        "evaluable_count": row["evaluable_count"],
        "population_count": row["population_count"],
        "metrics": {
            str(metric_id): _serialize_metric(metric)
            for metric_id, metric in metrics.items()
        },
        "timing": _allowlisted(timing, TIMING_KEYS),
        "not_evaluable_reason": row["not_evaluable_reason"],
    }


def _serialize_timings(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    timings: list[dict[str, Any]] = []
    for row in rows:
        algorithm_id = str(row["algorithm_id"])
        if algorithm_id in seen:
            continue
        seen.add(algorithm_id)
        timing = row["timing"]
        timings.append(
            {
                "algorithm_id": algorithm_id,
                **_allowlisted(timing, TIMING_KEYS),
            }
        )
    return timings


def serialize_comparison(payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = payload["rows"]
    return {
        "run": serialize_run(payload["run"]),
        "filters": dict(payload["filters"]),
        "filter_options": {
            key: [serialize_option(item) for item in payload["filter_options"][key]]
            for key in ("runs", "algorithms", "cohorts", "metrics", "formats")
        },
        "selected_metric_id": payload["selected_metric_id"],
        "rows": [_serialize_row(row) for row in rows],
        "metric_definitions": [
            _allowlisted(
                definition,
                ("metric_id", "label", "unit", "higher_is_better", "k", "run_level_only"),
            )
            for definition in payload["metric_definitions"]
        ],
        "timings": _serialize_timings(rows),
        "provenance": dict(payload["provenance"]),
        "limitations": [str(value) for value in payload["limitations"]],
        "downloads": [
            _allowlisted(download, ("format", "run_id", "available"))
            for download in payload["downloads"]
        ],
    }


def serialize_artifacts(published: PublishedRun) -> dict[str, Any]:
    run = serialize_run(published.run.to_dict())
    specs = (
        ("evaluation_result", ARTIFACT_RELATIVE_PATH, run["artifact_sha256"]),
        ("cohort_snapshot", COHORT_RELATIVE_PATH, run["cohort_sha256"]),
        ("methodology_protocol", PROTOCOL_RELATIVE_PATH, run["protocol_sha256"]),
    )
    return {
        "run": run,
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "filename": PurePosixPath(relative_path).name,
                "format": "json",
                "content_type": "application/json",
                "sha256": sha256,
                "published": True,
            }
            for artifact_id, relative_path, sha256 in specs
        ],
        "provenance": dict(published.evidence.provenance),
    }


def serialize_capabilities(user) -> dict[str, bool]:  # noqa: ANN001
    return {
        "can_view_research": can_view_research(user),
        "can_manage_platform": can_manage_platform(user),
    }


__all__ = [
    "serialize_artifacts",
    "serialize_capabilities",
    "serialize_comparison",
    "serialize_run",
    "serialize_runs",
]
