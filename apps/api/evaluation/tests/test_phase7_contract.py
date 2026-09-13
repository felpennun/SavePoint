from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from evaluation import panel_contract
from evaluation.panel_contract import PublicationContractError


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PUBLISHED_PATHS = (
    panel_contract.ARTIFACT_RELATIVE_PATH,
    panel_contract.COHORT_RELATIVE_PATH,
    panel_contract.PROTOCOL_RELATIVE_PATH,
)


def _copy_publication(tmp_path: Path) -> Path:
    for relative_path in PUBLISHED_PATHS:
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative_path, destination)
    return tmp_path


def test_load_real_v15_publication_and_builds_sanitized_comparison() -> None:
    published = panel_contract.load_published_run()
    payload = panel_contract.build_comparison_payload(published)

    assert published.run.run_id == "evaluation-400-test-2026-09-12-v15"
    assert published.run.protocol_version == 15
    assert published.run.corpus_version == "2026.09.2"
    assert published.run.protocol_sha256 == panel_contract.PUBLISHED_PROTOCOL_SHA256
    assert len(payload["rows"]) == 16 * 2 * 3
    assert payload["rows"][0]["algorithm_id"] == "cf-user-knn-v1"
    assert payload["rows"][0]["cohort_id"] == "active_history_10_to_20"
    assert payload["rows"][0]["metrics"]["ndcg@5"]["value"] == 0.01584847
    assert "per_user" not in json.dumps(payload, ensure_ascii=False)
    assert all(not Path(path).is_absolute() for path in published.evidence.source_paths)


def test_source_mutation_fails_before_dto_creation(tmp_path: Path) -> None:
    root = _copy_publication(tmp_path)
    artifact_path = root / panel_contract.ARTIFACT_RELATIVE_PATH
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["split"] = "validation"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(PublicationContractError, match="artifact checksum"):
        panel_contract.load_published_run(root=root)


def test_unknown_run_and_path_are_rejected() -> None:
    with pytest.raises(PublicationContractError, match="run_id is not allowlisted"):
        panel_contract.load_published_run("evaluation-400-test-2026-09-12-v16")

    with pytest.raises(PublicationContractError, match="source path is not allowlisted"):
        panel_contract._read_json(REPOSITORY_ROOT, "docs/methodology/other.json")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"algorithm_id": "not-published"}, "not published"),
        ({"cohort_id": "unknown"}, "not published"),
        ({"metric_id": "average@10"}, "not published"),
        ({"filters": {"metric_id": ["ndcg@10", "map@10"]}}, "repeated"),
        ({"filters": {"where": "1=1"}}, "unknown"),
        ({"filters": {"algorithm_id": "cf-user-knn-v1__user_id"}}, "invalid"),
    ],
)
def test_filter_allowlist_rejects_hostile_or_unknown_values(kwargs: dict, message: str) -> None:
    with pytest.raises(PublicationContractError, match=message):
        panel_contract.build_comparison_payload(**kwargs)


def test_cohort_rows_preserve_backend_order_and_null_non_evaluable_values() -> None:
    payload = panel_contract.build_comparison_payload(
        algorithm_id="content-cbf-weighted-v1",
        cohort_id="no_history",
        metric_id="ndcg@10",
    )

    assert payload["filters"] == {
        "algorithm_id": "content-cbf-weighted-v1",
        "cohort_id": "no_history",
        "metric_id": "ndcg@10",
    }
    assert [row["k"] for row in payload["rows"]] == [5, 10, 20]
    row = payload["rows"][1]
    assert row["evaluable_count"] == 0
    assert row["metrics"]["ndcg@10"]["value"] is None
    assert row["metrics"]["ndcg@10"]["unavailable_reason"]
    assert row["metrics"]["catalogue_coverage@10"]["value"] is None
    assert "desagregable" in row["metrics"]["catalogue_coverage@10"]["unavailable_reason"]


@pytest.mark.parametrize("export_format", ["csv", "json", "svg"])
def test_exports_are_allowlisted_and_contain_only_public_rows(export_format: str) -> None:
    export = panel_contract.build_export_payload(
        format=export_format,
        algorithm_id="content-cbf-weighted-v1",
        cohort_id="active_history_10_to_20",
        metric_id="ndcg@10",
    )

    assert export["format"] == export_format
    assert export["run_id"] == "evaluation-400-test-2026-09-12-v15"
    assert export["checksum_sha256"]
    assert "per_user" not in export["body"]
    assert "C:\\" not in export["body"]
    if export_format == "csv":
        assert export["body"].startswith("run_id,algorithm_id,cohort_id,k,")
    elif export_format == "json":
        assert json.loads(export["body"])["run"]["protocol_version"] == 15
    else:
        assert export["body"].startswith("<svg ")


def test_contract_module_does_not_import_or_invoke_evaluation_runner() -> None:
    source = (REPOSITORY_ROOT / "apps/api/evaluation/panel_contract.py").read_text(encoding="utf-8")
    assert "from evaluation.runner" not in source
    assert "run_evaluation_parallel" not in source
    assert "rank_content" not in source

