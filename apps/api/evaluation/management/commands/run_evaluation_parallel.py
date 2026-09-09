"""Parallel offline evaluation with one process per algorithm."""

from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from evaluation import protocol
from evaluation.runner import SnapshotCoverageError, _headline_statistical_comparison, default_algorithms, run


def _run_algorithm_process(payload: dict[str, Any]) -> dict[str, Any]:
    """Run one algorithm in an isolated interpreter and return timing data."""

    import django
    from django.db import connections

    django.setup()
    connections.close_all()
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    algorithm_id = payload["algorithm_id"]
    try:
        frozen = protocol.from_mapping(payload["protocol"])
        algorithm = default_algorithms()[algorithm_id]
        artifact = run(
            frozen,
            payload["corpus_version"],
            algorithms={algorithm_id: algorithm},
            split=payload["split"],
        )
        result = {
            "algorithm_id": algorithm_id,
            "status": "succeeded",
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.perf_counter() - started, 6),
            "artifact": artifact,
        }
        connections.close_all()
        return result
    except Exception as exc:  # noqa: BLE001 - parent records a bounded failure manifest
        connections.close_all()
        return {
            "algorithm_id": algorithm_id,
            "status": "failed",
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.perf_counter() - started, 6),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def _merge_worker_artifacts(
    frozen: protocol.Protocol,
    worker_results: list[dict[str, Any]],
    *,
    wall_started_at: str,
    wall_finished_at: str,
    wall_duration_seconds: float,
) -> dict[str, Any]:
    """Merge complete single-algorithm artifacts after contract checks."""

    successful = [result for result in worker_results if result["status"] == "succeeded"]
    if len(successful) != len(worker_results):
        errors = [
            {
                "algorithm_id": result["algorithm_id"],
                "status": result["status"],
                "error_type": result.get("error_type"),
                "error": result.get("error"),
            }
            for result in worker_results
            if result["status"] != "succeeded"
        ]
        return {
            "status": "failed",
            "protocol_version": frozen.protocol_version,
            "protocol_sha256": frozen.frozen_hash(),
            "split": frozen.raw.get("split", {}).get("strategy"),
            "worker_timings": worker_results,
            "parallel_execution": {
                "process_per_algorithm": True,
                "worker_count": len(worker_results),
                "wall_started_at": wall_started_at,
                "wall_finished_at": wall_finished_at,
                "wall_duration_seconds": round(wall_duration_seconds, 6),
            },
            "errors": errors,
            "algorithms": {},
        }

    first = successful[0]["artifact"]
    shared_keys = (
        "protocol_version",
        "protocol_sha256",
        "corpus_version",
        "snapshot_sha256",
        "popscore_snapshot_sha256",
        "feature_set_version",
        "split",
        "split_manifest_sha256",
    )
    for result in successful[1:]:
        artifact = result["artifact"]
        for key in shared_keys:
            if artifact.get(key) != first.get(key):
                raise ValueError(f"parallel workers disagree on {key}")
    algorithms = {
        algorithm_id: result["artifact"]["algorithms"][algorithm_id]
        for algorithm_id, result in sorted(
            ((result["algorithm_id"], result) for result in successful),
            key=lambda row: row[0],
        )
    }
    return {
        **first,
        "status": "succeeded",
        "algorithms": algorithms,
        "worker_timings": worker_results,
        "parallel_execution": {
            "process_per_algorithm": True,
            "worker_count": len(worker_results),
            "wall_started_at": wall_started_at,
            "wall_finished_at": wall_finished_at,
            "wall_duration_seconds": round(wall_duration_seconds, 6),
            "sum_worker_duration_seconds": round(
                sum(float(result["duration_seconds"]) for result in worker_results), 6
            ),
        },
        "statistical_comparisons": {
            frozen.headline: _headline_statistical_comparison(frozen, algorithms),
        },
    }


class Command(BaseCommand):
    help = "Run every offline algorithm in parallel over the synthetic evaluation population."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument(
            "--split", choices=("validation", "test"), default="test",
            help="validation is for tuning; test is the one-shot final comparison",
        )
        parser.add_argument(
            "--evidence-json", default="",
            help="write evidence to this path; '-' writes pure JSON to stdout",
        )
        parser.add_argument(
            "--max-workers", type=int, default=0,
            help="limit process concurrency; 0 means one process per algorithm",
        )
        parser.add_argument("--marker-path", default="", help="override the test marker path")

    @staticmethod
    def _marker_path(option: str) -> Path:
        return Path(option) if option else Path(settings.BASE_DIR) / ".evaluation-test-run.json"

    def _emit_evidence(self, target: str, artifact: dict[str, Any]) -> None:
        blob = json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if target == "-":
            self.stdout.write(blob, ending="")
            return
        if not target:
            return
        path = Path(target)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(blob, encoding="utf-8")
        except OSError as exc:
            raise CommandError(f"cannot write parallel evaluation evidence: {exc}") from exc
        self.stderr.write(f"evidence written: {path}")

    def handle(self, *args: Any, **options: Any) -> None:
        marker_path = self._marker_path(options.get("marker_path", ""))
        try:
            frozen = protocol.load(test_run_marker=marker_path, allow_consumed_test=False)
            corpus_version = options["corpus_version"]
            if frozen.corpus_version and frozen.corpus_version != corpus_version:
                raise CommandError("--corpus-version does not match the frozen protocol")
        except (protocol.ProtocolError, SnapshotCoverageError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        algorithm_ids = list(default_algorithms())
        declared_algorithm_ids = frozen.raw.get("tuning", {}).get("evaluation_algorithms")
        if declared_algorithm_ids is not None and declared_algorithm_ids != algorithm_ids:
            raise CommandError(
                "protocol.tuning.evaluation_algorithms does not match the registered offline suite"
            )
        max_workers = options.get("max_workers") or len(algorithm_ids)
        if max_workers < 1:
            raise CommandError("--max-workers must be >= 1")
        max_workers = min(max_workers, len(algorithm_ids))
        payloads = [
            {
                "algorithm_id": algorithm_id,
                "protocol": frozen.raw,
                "corpus_version": corpus_version,
                "split": options["split"],
            }
            for algorithm_id in algorithm_ids
        ]
        wall_started_at = datetime.now(timezone.utc)
        wall_started = time.perf_counter()
        worker_results: list[dict[str, Any]] = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_algorithm_process, payload) for payload in payloads]
            for future in as_completed(futures):
                try:
                    worker_results.append(future.result())
                except Exception as exc:  # noqa: BLE001 - convert pool failure to an explicit manifest
                    worker_results.append(
                        {
                            "algorithm_id": "unknown-process",
                            "status": "failed",
                            "error_type": type(exc).__name__,
                            "error": str(exc)[:500],
                        }
                    )
        wall_finished_at = datetime.now(timezone.utc)
        try:
            artifact = _merge_worker_artifacts(
                frozen,
                sorted(worker_results, key=lambda result: result["algorithm_id"]),
                wall_started_at=wall_started_at.isoformat(),
                wall_finished_at=wall_finished_at.isoformat(),
                wall_duration_seconds=time.perf_counter() - wall_started,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self._emit_evidence(options.get("evidence_json", ""), artifact)
        if artifact["status"] != "succeeded":
            raise CommandError("one or more offline algorithm workers failed; no test marker was recorded")
        if options["split"] == "test":
            protocol.record_test_run(marker_path, frozen)
        if not options.get("evidence_json"):
            self.stdout.write(json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True))
        elif options["evidence_json"] != "-":
            self.stdout.write(self.style.SUCCESS(
                f"Parallel evaluation completed for {len(algorithm_ids)} algorithms"
            ))
