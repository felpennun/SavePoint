from __future__ import annotations

from evaluation.cohort_analysis import analyse_artifact, render_markdown


def test_cohort_analysis_joins_rows_and_keeps_run_level_metrics_global() -> None:
    artifact = {
        "protocol_version": 15,
        "protocol_sha256": "protocol",
        "corpus_version": "fixture",
        "split": "test",
        "evaluation_population": {"evaluated_user_count": 1},
        "algorithms": {
            "content": {
                "per_user": [
                    {
                        "user_id": "1",
                        "metrics": {"5": {"precision": 0.2, "recall": 0.4, "ndcg": 0.3, "map": 0.1}},
                        "beyond_accuracy": {"5": {"intra_list_diversity": 0.8, "novelty": 3.0, "recommended_count": 5}},
                    }
                ],
                "beyond_accuracy": {"5": {"catalogue_coverage": {"value": 0.5}}},
            }
        },
    }
    manifest = {
        "manifest_sha256": "manifest",
        "users": [
            {"account_id": "1", "cohort": "active_history_10_to_20"},
            {"account_id": "2", "cohort": "no_history"},
        ],
    }

    report = analyse_artifact(artifact, manifest)

    active = report["cohorts"]["active_history_10_to_20"]
    assert active["population_user_count"] == 1
    assert active["evaluated_user_count"] == 1
    assert active["algorithms"]["content"]["summary_by_k"]["5"]["metrics"]["ndcg"] == 0.3
    assert active["algorithms"]["content"]["summary_by_k"]["5"]["beyond_accuracy"]["novelty"]["value"] == 3.0
    assert active["algorithms"]["content"]["run_level_only_metrics"]["5"]["catalogue_coverage"]["value"] == 0.5

    cold_start = report["cohorts"]["no_history"]
    assert cold_start["evaluated_user_count"] == 0
    assert cold_start["not_evaluable_reason"]
    assert "Métricas que permanecen globales" in render_markdown(report)
