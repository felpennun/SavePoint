"""Immutable, allowlisted projections for the Phase 7 research panel.

The panel consumes a published evaluation artifact and its cohort snapshot.  It
must never import the evaluation runner or reconstruct rankings from live data.
This module therefore treats the three checked-in files as a publication
boundary: their relative paths, bytes, identity fields and public projections
are all explicit.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class PublicationContractError(ValueError):
    """Raised when a published source or requested filter fails closed."""


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PUBLISHED_RUN_ID = "evaluation-400-test-2026-09-12-v15"
PUBLISHED_PROTOCOL_VERSION = 15
PUBLISHED_PROTOCOL_SHA256 = "d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a"
PUBLISHED_CORPUS_VERSION = "2026.09.2"
PUBLISHED_SNAPSHOT_SHA256 = "c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc"
PUBLISHED_POPSCORE_SNAPSHOT_SHA256 = "16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097"
PUBLISHED_ARTIFACT_SHA256 = "5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab"
PUBLISHED_COHORT_SHA256 = "7417c29ffa02de5e512bc8f2aeb4ba9a992a53d50f85af76dc441cf1a555aab0"
PUBLISHED_SPLIT = "test"

ARTIFACT_RELATIVE_PATH = "apps/api/evaluation-400-test-2026-09-12-v15.artifact.json"
COHORT_RELATIVE_PATH = "docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.json"
PROTOCOL_RELATIVE_PATH = "docs/methodology/protocol.json"

ACCURACY_METRICS = ("precision", "recall", "ndcg", "map")
BEYOND_ACCURACY_METRICS = ("intra_list_diversity", "novelty", "recommended_count")
RUN_LEVEL_ONLY_METRICS = ("catalogue_coverage", "concentration_hhi", "prediction_coverage")
EXPORT_FORMATS = ("csv", "json", "svg")
K_VALUES = (5, 10, 20)

_ALLOWED_SOURCE_PATHS = frozenset(
    {ARTIFACT_RELATIVE_PATH, COHORT_RELATIVE_PATH, PROTOCOL_RELATIVE_PATH}
)
_FILTER_KEYS = frozenset({"run_id", "algorithm_id", "cohort_id", "metric_id"})
_FILTER_FORMAT_KEYS = frozenset({"run_id", "algorithm_id", "cohort_id", "metric_id", "format"})


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    status: str
    published_at: str | None
    protocol_version: int
    corpus_version: str
    split: str
    commit_sha: str
    feature_set_version: str
    seed_count: int
    artifact_sha256: str
    cohort_sha256: str
    protocol_sha256: str
    snapshot_sha256: str
    popscore_snapshot_sha256: str
    split_manifest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "published_at": self.published_at,
            "protocol_version": self.protocol_version,
            "corpus_version": self.corpus_version,
            "split": self.split,
            "commit_sha": self.commit_sha,
            "feature_set_version": self.feature_set_version,
            "seed_count": self.seed_count,
            "artifact_sha256": self.artifact_sha256,
            "cohort_sha256": self.cohort_sha256,
            "protocol_sha256": self.protocol_sha256,
            "snapshot_sha256": self.snapshot_sha256,
            "popscore_snapshot_sha256": self.popscore_snapshot_sha256,
            "split_manifest_sha256": self.split_manifest_sha256,
        }


@dataclass(frozen=True)
class MetricValue:
    metric_id: str
    value: float | int | None
    unit: str
    higher_is_better: bool
    unavailable_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "value": self.value,
            "unit": self.unit,
            "higher_is_better": self.higher_is_better,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass(frozen=True)
class ComparisonRow:
    algorithm_id: str
    algorithm_label: str
    cohort_id: str
    cohort_label: str
    k: int
    evaluable_count: int
    population_count: int
    metrics: Mapping[str, MetricValue]
    duration_seconds: float | None
    timing_unavailable_reason: str | None
    not_evaluable_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_id": self.algorithm_id,
            "algorithm_label": self.algorithm_label,
            "cohort_id": self.cohort_id,
            "cohort_label": self.cohort_label,
            "k": self.k,
            "evaluable_count": self.evaluable_count,
            "population_count": self.population_count,
            "metrics": {key: value.to_dict() for key, value in self.metrics.items()},
            "timing": {
                "duration_seconds": self.duration_seconds,
                "wall_ms": (
                    None
                    if self.duration_seconds is None
                    else round(self.duration_seconds * 1000, 3)
                ),
                "cpu_ms": None,
                "unavailable_reason": self.timing_unavailable_reason,
            },
            "not_evaluable_reason": self.not_evaluable_reason,
        }


@dataclass(frozen=True)
class EvidenceDetails:
    provenance: Mapping[str, Any]
    configuration: Mapping[str, Any]
    limitations: tuple[str, ...]
    source_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance": dict(self.provenance),
            "configuration": _thaw(self.configuration),
            "limitations": list(self.limitations),
            "source_paths": list(self.source_paths),
        }


@dataclass(frozen=True)
class PublishedRun:
    run_id: str
    artifact: Mapping[str, Any]
    cohorts: Mapping[str, Any]
    protocol: Mapping[str, Any]
    run: RunSummary
    evidence: EvidenceDetails
    algorithm_ids: tuple[str, ...]
    cohort_ids: tuple[str, ...]
    metric_ids: tuple[str, ...]


@dataclass(frozen=True)
class ExportPayload:
    format: str
    run_id: str
    filters: Mapping[str, str]
    checksum_sha256: str
    content_type: str
    filename: str
    body: str
    rows: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "run_id": self.run_id,
            "filters": dict(self.filters),
            "checksum_sha256": self.checksum_sha256,
            "content_type": self.content_type,
            "filename": self.filename,
            "body": self.body,
            "rows": [_thaw(row) for row in self.rows],
        }


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(root: Path, relative_path: str) -> tuple[dict[str, Any], str]:
    if relative_path not in _ALLOWED_SOURCE_PATHS:
        raise PublicationContractError(f"source path is not allowlisted: {relative_path}")
    path = root / relative_path
    try:
        data = path.read_bytes()
        parsed = json.loads(data.decode("utf-8-sig"))
    except FileNotFoundError as exc:
        raise PublicationContractError(f"published source is missing: {relative_path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationContractError(f"published source is unreadable: {relative_path}") from exc
    if not isinstance(parsed, dict):
        raise PublicationContractError(f"published source must be an object: {relative_path}")
    return parsed, _sha256(data)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicationContractError(message)


def _require_text(value: Any, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"published field is invalid: {name}")
    return value


def _validate_protocol(protocol: Mapping[str, Any]) -> None:
    # The checked-in pointer can be a newer methodology protocol.  It is never
    # used to recalculate the v15 result; only identity anchors shared by the
    # publication are accepted here.  The artifact's v15 identity remains the
    # authoritative protocol version and checksum.
    version = protocol.get("protocol_version")
    _require(isinstance(version, int) and version >= PUBLISHED_PROTOCOL_VERSION, "protocol version predates published run")
    _require(protocol.get("simulation") is True, "protocol simulation flag drifted")
    _require(protocol.get("corpus_version") == PUBLISHED_CORPUS_VERSION, "protocol corpus version drifted")
    _require(protocol.get("snapshot_sha256") == PUBLISHED_SNAPSHOT_SHA256, "protocol snapshot checksum drifted")
    _require(protocol.get("popscore_snapshot_sha256") == PUBLISHED_POPSCORE_SNAPSHOT_SHA256, "protocol PopScore checksum drifted")
    _require(protocol.get("k_values") == list(K_VALUES), "protocol K values drifted")
    _require(protocol.get("headline") == "ndcg@10", "protocol headline drifted")
    split = protocol.get("split")
    _require(isinstance(split, Mapping), "protocol split is invalid")
    _require(split.get("strategy") == "leave_fraction_out_dominant_tag_per_user", "protocol split strategy drifted")
    _require(split.get("seed") == 20260907, "protocol leave-one-out seed drifted")
    user_split = protocol.get("user_split")
    _require(isinstance(user_split, Mapping), "protocol user split is invalid")
    _require(user_split.get("seed") == 20260908, "protocol user split seed drifted")


def _validate_publication(
    artifact: Mapping[str, Any],
    artifact_sha256: str,
    cohorts: Mapping[str, Any],
    cohort_sha256: str,
    protocol: Mapping[str, Any],
) -> None:
    _require(artifact_sha256 == PUBLISHED_ARTIFACT_SHA256, "published artifact checksum drifted")
    _require(cohort_sha256 == PUBLISHED_COHORT_SHA256, "published cohort snapshot checksum drifted")
    _require(artifact.get("status") == "succeeded", "published artifact is not succeeded")
    _require(artifact.get("protocol_version") == PUBLISHED_PROTOCOL_VERSION, "artifact protocol version drifted")
    _require(artifact.get("protocol_sha256") == PUBLISHED_PROTOCOL_SHA256, "artifact protocol checksum drifted")
    _require(artifact.get("corpus_version") == PUBLISHED_CORPUS_VERSION, "artifact corpus version drifted")
    _require(artifact.get("snapshot_sha256") == PUBLISHED_SNAPSHOT_SHA256, "artifact snapshot checksum drifted")
    _require(artifact.get("popscore_snapshot_sha256") == PUBLISHED_POPSCORE_SNAPSHOT_SHA256, "artifact PopScore checksum drifted")
    _require(artifact.get("split") == PUBLISHED_SPLIT, "artifact split drifted")
    _require(artifact.get("simulation") is True, "artifact simulation flag drifted")
    _require(isinstance(artifact.get("algorithms"), Mapping) and artifact["algorithms"], "artifact algorithms are missing")
    population = artifact.get("evaluation_population")
    _require(isinstance(population, Mapping), "artifact evaluation population is invalid")
    _require(population.get("evaluated_user_count") == 79, "artifact evaluated population drifted")

    _require(cohorts.get("artifact_protocol_version") == PUBLISHED_PROTOCOL_VERSION, "cohort protocol version drifted")
    _require(cohorts.get("artifact_protocol_sha256") == PUBLISHED_PROTOCOL_SHA256, "cohort protocol checksum drifted")
    _require(cohorts.get("corpus_version") == PUBLISHED_CORPUS_VERSION, "cohort corpus version drifted")
    _require(cohorts.get("split") == PUBLISHED_SPLIT, "cohort split drifted")
    _require(cohorts.get("population_count") == population.get("split_total") == 400, "cohort population drifted")
    _require(isinstance(cohorts.get("cohorts"), Mapping) and cohorts["cohorts"], "cohorts are missing")
    _require(set(cohorts["cohorts"]) == {"active_history_10_to_20", "no_history"}, "cohort allowlist drifted")
    _require(set(cohorts["cohorts"]["active_history_10_to_20"]["algorithms"]) == set(artifact["algorithms"]), "active cohort algorithms drifted")
    _require(set(cohorts["cohorts"]["no_history"]["algorithms"]) == set(artifact["algorithms"]), "cold-start cohort algorithms drifted")
    limitations = cohorts.get("limitations")
    _require(isinstance(limitations, Mapping), "cohort limitations are missing")
    _require(tuple(limitations.get("run_level_only_metrics", ())) == RUN_LEVEL_ONLY_METRICS, "run-level metric allowlist drifted")
    _validate_protocol(protocol)


def _metric_ids(artifact: Mapping[str, Any], cohorts: Mapping[str, Any]) -> tuple[str, ...]:
    del cohorts
    return tuple(f"{metric}@{k}" for k in K_VALUES for metric in ACCURACY_METRICS + BEYOND_ACCURACY_METRICS) + tuple(
        f"{metric}@{k}" for k in K_VALUES for metric in RUN_LEVEL_ONLY_METRICS
    )


def _configuration(artifact: Mapping[str, Any], protocol: Mapping[str, Any]) -> Mapping[str, Any]:
    tuning = protocol.get("tuning", {})
    return _freeze(
        {
            "feature_set_version": artifact.get("feature_set_version"),
            "k_values": list(K_VALUES),
            "headline": "ndcg@10",
            "seeds": artifact.get("seeds"),
            "split": artifact.get("split"),
            "evaluation_population": artifact.get("evaluation_population"),
            "tuning": {
                "select_on": tuning.get("select_on"),
                "select_split": tuning.get("select_split"),
                "test_runs": tuning.get("test_runs"),
                "grid_size": len(tuning.get("grid", ())) if isinstance(tuning.get("grid"), list) else None,
            },
            "parallel_execution": artifact.get("parallel_execution"),
            "environment": None,
        }
    )


def load_published_run(run_id: str = PUBLISHED_RUN_ID, *, root: str | Path | None = None) -> PublishedRun:
    """Read and validate one explicitly published run without side effects."""

    if run_id != PUBLISHED_RUN_ID:
        raise PublicationContractError(f"run_id is not allowlisted: {run_id}")
    repository_root = Path(root).resolve() if root is not None else REPOSITORY_ROOT
    artifact, artifact_sha256 = _read_json(repository_root, ARTIFACT_RELATIVE_PATH)
    cohorts, cohort_sha256 = _read_json(repository_root, COHORT_RELATIVE_PATH)
    protocol, _protocol_file_sha256 = _read_json(repository_root, PROTOCOL_RELATIVE_PATH)
    _validate_publication(artifact, artifact_sha256, cohorts, cohort_sha256, protocol)

    algorithm_ids = tuple(artifact["algorithms"].keys())
    cohort_ids = tuple(cohorts["cohorts"].keys())
    published_at = artifact.get("parallel_execution", {}).get("wall_finished_at")
    run = RunSummary(
        run_id=run_id,
        status=artifact["status"],
        published_at=published_at if isinstance(published_at, str) else None,
        protocol_version=PUBLISHED_PROTOCOL_VERSION,
        corpus_version=PUBLISHED_CORPUS_VERSION,
        split=PUBLISHED_SPLIT,
        commit_sha=_require_text(artifact.get("code_commit"), "code_commit"),
        feature_set_version=_require_text(artifact.get("feature_set_version"), "feature_set_version"),
        seed_count=len(artifact.get("seeds", {})) if isinstance(artifact.get("seeds"), Mapping) else 0,
        artifact_sha256=artifact_sha256,
        cohort_sha256=cohort_sha256,
        protocol_sha256=PUBLISHED_PROTOCOL_SHA256,
        snapshot_sha256=PUBLISHED_SNAPSHOT_SHA256,
        popscore_snapshot_sha256=PUBLISHED_POPSCORE_SNAPSHOT_SHA256,
        split_manifest_sha256=_require_text(artifact.get("split_manifest_sha256"), "split_manifest_sha256"),
    )
    cohort_limitations = cohorts["limitations"]
    evidence = EvidenceDetails(
        provenance=_freeze(
            {
                "protocol_version": PUBLISHED_PROTOCOL_VERSION,
                "protocol_sha256": PUBLISHED_PROTOCOL_SHA256,
                "corpus_version": PUBLISHED_CORPUS_VERSION,
                "snapshot_sha256": PUBLISHED_SNAPSHOT_SHA256,
                "popscore_snapshot_sha256": PUBLISHED_POPSCORE_SNAPSHOT_SHA256,
                "split_manifest_sha256": artifact["split_manifest_sha256"],
                "code_commit": artifact["code_commit"],
                "artifact_sha256": artifact_sha256,
                "cohort_sha256": cohort_sha256,
                "simulation": True,
            }
        ),
        configuration=_configuration(artifact, protocol),
        limitations=(
            _require_text(artifact.get("limitation"), "limitation"),
            _require_text(cohort_limitations.get("explanation"), "cohort limitation explanation"),
        ),
        source_paths=(ARTIFACT_RELATIVE_PATH, COHORT_RELATIVE_PATH, PROTOCOL_RELATIVE_PATH),
    )
    return PublishedRun(
        run_id=run_id,
        artifact=_freeze(artifact),
        cohorts=_freeze(cohorts),
        protocol=_freeze(protocol),
        run=run,
        evidence=evidence,
        algorithm_ids=algorithm_ids,
        cohort_ids=cohort_ids,
        metric_ids=_metric_ids(artifact, cohorts),
    )


def _one_filter(filters: Mapping[str, Any], key: str) -> str | None:
    if key not in filters:
        return None
    value = filters[key]
    if isinstance(value, (list, tuple, set, frozenset)):
        raise PublicationContractError(f"repeated filter value is not allowed: {key}")
    if not isinstance(value, str) or not value or any(token in value for token in ("__", "=", "&", "|", ";", "'", '"')):
        raise PublicationContractError(f"invalid filter value: {key}")
    return value


def _normalise_filters(
    published: PublishedRun,
    filters: Mapping[str, Any] | None = None,
    **values: Any,
) -> dict[str, str]:
    merged: dict[str, Any] = {}
    if filters is not None:
        if not isinstance(filters, Mapping):
            raise PublicationContractError("filters must be a mapping")
        merged.update(filters)
    merged.update({key: value for key, value in values.items() if value is not None})
    if set(merged) - _FILTER_KEYS:
        raise PublicationContractError("unknown research filter")
    normalised: dict[str, str] = {}
    allowed = {
        "run_id": {published.run_id},
        "algorithm_id": set(published.algorithm_ids),
        "cohort_id": set(published.cohort_ids),
        "metric_id": set(published.metric_ids),
    }
    for key in _FILTER_KEYS:
        value = _one_filter(merged, key)
        if value is not None:
            if value not in allowed[key]:
                raise PublicationContractError(f"filter value is not published: {key}={value}")
            normalised[key] = value
    return {key: normalised[key] for key in ("run_id", "algorithm_id", "cohort_id", "metric_id") if key in normalised}


def _metric_definition(metric_id: str) -> dict[str, Any]:
    metric_name, raw_k = metric_id.rsplit("@", 1)
    k = int(raw_k)
    unit = "count" if metric_name == "recommended_count" else "ratio"
    return {
        "metric_id": metric_id,
        "label": metric_id,
        "unit": unit,
        "higher_is_better": metric_name not in {"concentration_hhi"},
        "k": k,
        "run_level_only": metric_name in RUN_LEVEL_ONLY_METRICS,
    }


def _summary_metric(summary: Mapping[str, Any], metric: str, k: int) -> float | int | None:
    if metric in ACCURACY_METRICS:
        metrics = summary.get("metrics", {})
        value = metrics.get(metric) if isinstance(metrics, Mapping) else None
    else:
        beyond = summary.get("beyond_accuracy", {})
        entry = beyond.get(metric) if isinstance(beyond, Mapping) else None
        value = entry.get("value") if isinstance(entry, Mapping) else None
    if value is None:
        return None
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"published metric is invalid: {metric}@{k}")
    _require(math.isfinite(float(value)), f"published metric is not finite: {metric}@{k}")
    return value


def _row(published: PublishedRun, algorithm_id: str, cohort_id: str, k: int) -> ComparisonRow:
    cohort = published.cohorts["cohorts"][cohort_id]
    algorithm = cohort["algorithms"][algorithm_id]
    summary = algorithm["summary_by_k"][str(k)]
    metrics: dict[str, MetricValue] = {}
    unavailable_reason = cohort.get("not_evaluable_reason")
    for metric in ACCURACY_METRICS + BEYOND_ACCURACY_METRICS:
        metric_id = f"{metric}@{k}"
        metrics[metric_id] = MetricValue(
            metric_id=metric_id,
            value=_summary_metric(summary, metric, k),
            unit="count" if metric == "recommended_count" else "ratio",
            higher_is_better=True,
            unavailable_reason=unavailable_reason,
        )
    run_level_reason = "Métrica conservada solo a nivel de ejecución; no es desagregable por cohorte."
    for metric in RUN_LEVEL_ONLY_METRICS:
        metric_id = f"{metric}@{k}"
        metrics[metric_id] = MetricValue(
            metric_id=metric_id,
            value=None,
            unit="ratio",
            higher_is_better=metric != "concentration_hhi",
            unavailable_reason=run_level_reason,
        )
    artifact_algorithm = published.artifact["algorithms"][algorithm_id]
    duration = artifact_algorithm.get("duration_seconds")
    _require(isinstance(duration, (int, float)) and not isinstance(duration, bool), f"algorithm timing is invalid: {algorithm_id}")
    return ComparisonRow(
        algorithm_id=algorithm_id,
        algorithm_label=algorithm_id,
        cohort_id=cohort_id,
        cohort_label=cohort_id,
        k=k,
        evaluable_count=int(summary.get("user_count", 0)),
        population_count=int(cohort.get("population_user_count", 0)),
        metrics=MappingProxyType(metrics),
        duration_seconds=float(duration),
        timing_unavailable_reason="El artefacto no conserva CPU por cohorte; se muestra la duración del worker del algoritmo.",
        not_evaluable_reason=unavailable_reason,
    )


def _filter_options(published: PublishedRun) -> dict[str, list[dict[str, str]]]:
    return {
        "runs": [{"id": published.run_id, "label": published.run_id}],
        "algorithms": [{"id": value, "label": value} for value in published.algorithm_ids],
        "cohorts": [{"id": value, "label": value} for value in published.cohort_ids],
        "metrics": [{"id": value, "label": value} for value in published.metric_ids],
        "formats": [{"id": value, "label": value.upper()} for value in EXPORT_FORMATS],
    }


def build_comparison_payload(
    published: PublishedRun | None = None,
    filters: Mapping[str, Any] | None = None,
    *,
    run_id: str | None = None,
    algorithm_id: str | None = None,
    cohort_id: str | None = None,
    metric_id: str | None = None,
) -> dict[str, Any]:
    """Build the sole public comparison shape from an already-loaded run."""

    loaded = published or load_published_run(run_id or PUBLISHED_RUN_ID)
    if run_id is not None and run_id != loaded.run_id:
        raise PublicationContractError("run_id does not match loaded publication")
    selected = _normalise_filters(
        loaded,
        filters,
        run_id=run_id,
        algorithm_id=algorithm_id,
        cohort_id=cohort_id,
        metric_id=metric_id,
    )
    algorithms: Sequence[str] = loaded.algorithm_ids
    cohorts: Sequence[str] = loaded.cohort_ids
    if "algorithm_id" in selected:
        algorithms = (selected["algorithm_id"],)
    if "cohort_id" in selected:
        cohorts = (selected["cohort_id"],)
    rows = tuple(
        _row(loaded, algorithm, cohort, k)
        for cohort in cohorts
        for algorithm in algorithms
        for k in K_VALUES
    )
    row_dicts = tuple(row.to_dict() for row in rows)
    metric_definitions = tuple(_metric_definition(metric_id) for metric_id in loaded.metric_ids)
    return {
        "run": loaded.run.to_dict(),
        "filters": selected,
        "filter_options": _filter_options(loaded),
        "selected_metric_id": selected.get("metric_id", "ndcg@10"),
        "rows": list(row_dicts),
        "metric_definitions": list(metric_definitions),
        "evidence": loaded.evidence.to_dict(),
        "provenance": loaded.evidence.to_dict()["provenance"],
        "limitations": list(loaded.evidence.limitations),
        "downloads": [
            {"format": value, "run_id": loaded.run_id, "available": True}
            for value in EXPORT_FORMATS
        ],
    }


def _csv_body(rows: Sequence[Mapping[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("run_id", "algorithm_id", "cohort_id", "k", "evaluable_count", "metric_id", "value", "unit"))
    for row in rows:
        metrics = row["metrics"]
        for metric_id, metric in metrics.items():
            writer.writerow((PUBLISHED_RUN_ID, row["algorithm_id"], row["cohort_id"], row["k"], row["evaluable_count"], metric_id, metric["value"], metric["unit"]))
    return output.getvalue()


def _svg_body(payload: Mapping[str, Any]) -> str:
    metric_id = payload["selected_metric_id"]
    bars = []
    for index, row in enumerate(payload["rows"]):
        value = row["metrics"].get(metric_id, {}).get("value")
        label = f"{row['algorithm_id']} / {row['cohort_id']} / K={row['k']}"
        text_value = "null" if value is None else str(value)
        y = 24 + index * 24
        bars.append(f'<text x="8" y="{y}">{label}: {text_value}</text>')
    height = max(40, 32 + len(bars) * 24)
    return '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 1180 {height}"><title id="title">{metric}</title><desc id="desc">Values are identical to the accessible comparison table.</desc>{bars}</svg>'.format(
        height=height,
        metric=metric_id,
        bars="".join(bars),
    )


def build_export_payload(
    published: PublishedRun | None = None,
    format: str = "json",
    filters: Mapping[str, Any] | None = None,
    *,
    run_id: str | None = None,
    algorithm_id: str | None = None,
    cohort_id: str | None = None,
    metric_id: str | None = None,
) -> dict[str, Any]:
    """Create a safe export from the comparison DTO, never from ``per_user``."""

    if not isinstance(format, str) or format not in EXPORT_FORMATS:
        raise PublicationContractError("export format is not allowlisted")
    comparison = build_comparison_payload(
        published,
        filters,
        run_id=run_id,
        algorithm_id=algorithm_id,
        cohort_id=cohort_id,
        metric_id=metric_id,
    )
    rows = tuple(comparison["rows"])
    if format == "csv":
        body = _csv_body(rows)
        content_type = "text/csv; charset=utf-8"
    elif format == "svg":
        body = _svg_body(comparison)
        content_type = "image/svg+xml; charset=utf-8"
    else:
        body = json.dumps(
            {
                "run": comparison["run"],
                "filters": comparison["filters"],
                "rows": rows,
                "metric_definitions": comparison["metric_definitions"],
                "provenance": comparison["provenance"],
                "limitations": comparison["limitations"],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        content_type = "application/json; charset=utf-8"
    result = ExportPayload(
        format=format,
        run_id=comparison["run"]["run_id"],
        filters=MappingProxyType(dict(comparison["filters"])),
        checksum_sha256=_sha256(body.encode("utf-8")),
        content_type=content_type,
        filename=f"{PUBLISHED_RUN_ID}.{format}",
        body=body,
        rows=rows,
    )
    return result.to_dict()


__all__ = [
    "ComparisonRow",
    "EvidenceDetails",
    "ExportPayload",
    "MetricValue",
    "PublicationContractError",
    "PublishedRun",
    "RunSummary",
    "build_comparison_payload",
    "build_export_payload",
    "load_published_run",
]
