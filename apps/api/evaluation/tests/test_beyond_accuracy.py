"""Known-answer tests for reproducible beyond-accuracy metrics."""

from __future__ import annotations

import math

import pytest

from evaluation.metrics import (
    catalogue_coverage_at_k,
    concentration_hhi_at_k,
    intra_list_diversity,
    novelty_at_k,
    prediction_coverage_at_k,
)


def test_catalogue_coverage_and_prediction_coverage_keep_distinct_denominators() -> None:
    ranked = [["a", "b"], ["a"]]
    candidates = [["a", "b", "c"], ["a", "b", "d"]]

    assert catalogue_coverage_at_k(ranked, {"a", "b", "c", "d"}, 2) == pytest.approx(0.5)
    assert prediction_coverage_at_k(ranked, candidates, 2) == pytest.approx(3 / 4)


def test_concentration_hhi_known_answer_and_empty_is_not_estimable() -> None:
    assert concentration_hhi_at_k([["a", "b"], ["a", "c"]], 2) == pytest.approx(0.375)
    assert concentration_hhi_at_k([], 10) is None


def test_ild_uses_mean_pairwise_cosine_distance_and_preserves_na() -> None:
    vectors = {
        "a": {"genre:rpg": 1.0},
        "b": {"genre:puzzle": 1.0},
        "c": {"genre:rpg": 1.0},
    }

    assert intra_list_diversity(["a", "b", "c"], vectors) == pytest.approx(2 / 3)
    assert intra_list_diversity(["a"], vectors) is None
    assert intra_list_diversity(["a", "missing"], vectors) is None


def test_novelty_uses_training_self_information_and_rejects_unknown_probability() -> None:
    probabilities = {"a": 0.5, "b": 0.25}

    assert novelty_at_k(["a", "b"], probabilities, 2) == pytest.approx(1.5)
    assert novelty_at_k(["a", "missing"], probabilities, 2) is None
    assert novelty_at_k([], probabilities, 2) is None
    assert novelty_at_k(["a"], {"a": 0.0}, 1) is None
    assert math.isfinite(novelty_at_k(["a", "b"], probabilities, 2) or 0.0)
