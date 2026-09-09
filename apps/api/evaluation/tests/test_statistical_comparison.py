"""Reproducible paired statistical comparisons for evaluation artefacts."""

from __future__ import annotations

import pytest

from evaluation.statistics import (
    StatisticsConfig,
    compare_paired_algorithms,
    friedman_test,
    holm_adjust,
    wilcoxon_paired,
)


def _observations() -> dict[str, dict[str, float]]:
    return {
        "algorithm-a": {"u-1": 0.90, "u-2": 0.70, "u-3": 0.80, "u-4": 0.60},
        "algorithm-b": {"u-1": 0.80, "u-2": 0.60, "u-3": 0.70, "u-4": 0.50},
        "algorithm-c": {"u-1": 0.40, "u-2": 0.50, "u-3": 0.30, "u-4": 0.20},
    }


def test_compare_is_deterministic_and_pairs_by_user() -> None:
    config = StatisticsConfig(bootstrap_resamples=250, seed=20260909)
    first = compare_paired_algorithms(_observations(), config=config)
    second = compare_paired_algorithms(
        {
            name: dict(reversed(list(values.items())))
            for name, values in reversed(list(_observations().items()))
        },
        config=config,
    )

    assert first == second
    assert first["user_count"] == 4
    assert first["input_sha256"]
    assert first["configuration"]["seed"] == 20260909
    assert first["friedman"]["valid"] is True
    assert first["pairwise"]["holm"]["family_size"] == 3
    assert all("adjusted_p_value" in row for row in first["pairwise"]["comparisons"])


def test_wilcoxon_records_rounded_differences_zeros_and_ties() -> None:
    result = wilcoxon_paired(
        {"u-1": 0.70000000001, "u-2": 0.5, "u-3": 0.5},
        {"u-1": 0.7, "u-2": 0.4, "u-3": 0.4},
        config=StatisticsConfig(difference_decimals=8),
    )

    assert result["valid"] is True
    assert result["paired"] is True
    assert result["zero_count"] == 1
    assert result["tie_count"] == 1
    assert result["method"] == "approx"
    assert "zeros" in " ".join(result["warnings"])
    assert "ties" in " ".join(result["warnings"])


def test_all_zero_wilcoxon_is_explicitly_not_estimable() -> None:
    result = wilcoxon_paired(
        {"u-1": 0.5, "u-2": 0.5},
        {"u-1": 0.5, "u-2": 0.5},
    )

    assert result["valid"] is True
    assert result["estimable"] is False
    assert result["p_value"] is None
    assert result["zero_count"] == 2
    assert result["statistic"] is None


def test_friedman_rejects_unpaired_or_too_small_samples() -> None:
    with pytest.raises(ValueError, match="same users"):
        friedman_test(
            {
                "a": {"u-1": 0.1, "u-2": 0.2, "u-3": 0.3},
                "b": {"u-1": 0.2, "u-2": 0.3, "u-4": 0.4},
                "c": {"u-1": 0.3, "u-2": 0.4, "u-3": 0.5},
            }
        )

    with pytest.raises(ValueError, match="at least three algorithms"):
        friedman_test(
            {
                "a": {"u-1": 0.1, "u-2": 0.2, "u-3": 0.3},
                "b": {"u-1": 0.2, "u-2": 0.3, "u-3": 0.4},
            }
        )


def test_holm_uses_stable_order_for_equal_p_values() -> None:
    result = holm_adjust({"zeta": 0.01, "alpha": 0.01, "middle": 0.2})

    assert result["order"] == ["alpha", "zeta", "middle"]
    rows = {row["label"]: row for row in result["comparisons"]}
    assert rows["alpha"]["adjusted_p_value"] == rows["zeta"]["adjusted_p_value"]
    assert rows["alpha"]["rank"] == 1
    assert rows["zeta"]["rank"] == 2
    assert rows["middle"]["reject"] is False


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="bootstrap_resamples"):
        StatisticsConfig(bootstrap_resamples=0)

    with pytest.raises(ValueError, match="confidence_level"):
        StatisticsConfig(confidence_level=1.0)
