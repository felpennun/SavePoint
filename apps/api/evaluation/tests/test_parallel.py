"""Tests for the parallel evaluation artifact contract."""

from __future__ import annotations

from evaluation import protocol
from evaluation.management.commands.run_evaluation_parallel import _merge_worker_artifacts


def _worker_result(frozen, algorithm_id: str, score: float) -> dict:
    artifact = {
        "protocol_version": frozen.protocol_version,
        "protocol_sha256": frozen.frozen_hash(),
        "corpus_version": "fixture",
        "snapshot_sha256": "snapshot",
        "popscore_snapshot_sha256": "popscore",
        "feature_set_version": "fs-v9",
        "split": "test",
        "split_manifest_sha256": "manifest",
        "algorithms": {
            algorithm_id: {
                "algorithm_id": algorithm_id,
                "per_user": [{"user_id": "1", "metrics": {"10": {"ndcg": score}}}],
                "aggregates": {},
                "beyond_accuracy": {},
            }
        },
    }
    return {
        "algorithm_id": algorithm_id,
        "status": "succeeded",
        "started_at": "2026-09-09T10:00:00+00:00",
        "finished_at": "2026-09-09T10:00:01+00:00",
        "duration_seconds": 1.0,
        "artifact": artifact,
    }


def test_parallel_merge_preserves_each_algorithm_and_records_sum() -> None:
    frozen = protocol.load()
    artifact = _merge_worker_artifacts(
        frozen,
        [_worker_result(frozen, "first", 1.0), _worker_result(frozen, "second", 0.5)],
        wall_started_at="2026-09-09T10:00:00+00:00",
        wall_finished_at="2026-09-09T10:00:01+00:00",
        wall_duration_seconds=1.0,
    )

    assert artifact["status"] == "succeeded"
    assert set(artifact["algorithms"]) == {"first", "second"}
    assert artifact["parallel_execution"]["sum_worker_duration_seconds"] == 2.0


def test_parallel_merge_returns_explicit_failure_manifest() -> None:
    frozen = protocol.load()
    failed = {
        "algorithm_id": "broken",
        "status": "failed",
        "error_type": "ValueError",
        "error": "fixture failure",
        "duration_seconds": 0.1,
    }
    artifact = _merge_worker_artifacts(
        frozen,
        [failed],
        wall_started_at="2026-09-09T10:00:00+00:00",
        wall_finished_at="2026-09-09T10:00:01+00:00",
        wall_duration_seconds=1.0,
    )

    assert artifact["status"] == "failed"
    assert artifact["algorithms"] == {}
    assert artifact["errors"][0]["algorithm_id"] == "broken"
