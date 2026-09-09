"""Tests for deterministic MMR recommendation selection."""

from recommendations.content.diversity import mmr_rerank


def test_mmr_keeps_the_best_item_then_prefers_a_distinct_relevant_item() -> None:
    scored = [
        (0.90, "alpha", {"work_id": "alpha", "signals": {}}),
        (0.88, "beta", {"work_id": "beta", "signals": {}}),
        (0.75, "gamma", {"work_id": "gamma", "signals": {}}),
    ]
    vectors = {
        "alpha": {"genre:rpg": 1.0},
        "beta": {"genre:rpg": 1.0},
        "gamma": {"genre:shooter": 1.0},
    }

    result = mmr_rerank(scored, vectors, lambda_value=0.80)

    assert [item["work_id"] for item in result] == ["alpha", "gamma", "beta"]
    assert result[0]["signals"]["mmr_redundancy"] == 0.0
    assert result[1]["signals"]["mmr_redundancy"] == 0.0
    assert result[2]["signals"]["mmr_redundancy"] == 1.0
    assert result[2]["signals"]["mmr_score"] < result[1]["signals"]["mmr_score"]


def test_mmr_tie_breaking_is_stable_by_slug() -> None:
    scored = [
        (0.80, "zeta", {"work_id": "zeta", "signals": {}}),
        (0.80, "alpha", {"work_id": "alpha", "signals": {}}),
    ]

    assert [item["work_id"] for item in mmr_rerank(scored, {})] == ["alpha", "zeta"]
