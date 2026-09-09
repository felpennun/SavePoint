"""Reproducible statistical comparisons for evaluation artefacts.

The unit of analysis is always the user.  Public functions accept a mapping
from algorithm id to ``{user_id: metric_value}``, align observations by user
id, and reject incomplete pairing instead of silently imputing values.

SciPy owns the statistical distributions; the returned dictionaries keep the
configuration, method, sample size, warnings, and deterministic input hash so
the result can be embedded in a citable JSON artefact.  This module is not
used for tuning: it compares already selected runs only.
"""

from __future__ import annotations

import hashlib
import json
import math
import warnings
from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import stats


STATISTICS_VERSION = "statistics-v1"
DEFAULT_BOOTSTRAP_RESAMPLES = 2_000
MAX_BOOTSTRAP_RESAMPLES = 50_000
BOOTSTRAP_METHODS = frozenset({"BCa", "basic", "percentile"})
WILCOXON_METHODS = frozenset({"auto", "exact", "approx"})
WILCOXON_ZERO_METHODS = frozenset({"wilcox", "pratt", "zsplit"})


@dataclass(frozen=True)
class StatisticsConfig:
    """Serializable parameters for one statistical-comparison family."""

    confidence_level: float = 0.95
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES
    seed: int = 20260909
    bootstrap_method: str = "BCa"
    bootstrap_fallback_method: str = "percentile"
    difference_decimals: int = 12
    wilcoxon_zero_method: str = "wilcox"
    wilcoxon_method: str = "auto"
    alpha: float = 0.05

    def __post_init__(self) -> None:
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be strictly between 0 and 1")
        if not 0 < self.bootstrap_resamples <= MAX_BOOTSTRAP_RESAMPLES:
            raise ValueError(
                f"bootstrap_resamples must be between 1 and {MAX_BOOTSTRAP_RESAMPLES}"
            )
        if self.bootstrap_method not in BOOTSTRAP_METHODS:
            raise ValueError(f"unsupported bootstrap_method: {self.bootstrap_method}")
        if self.bootstrap_fallback_method not in BOOTSTRAP_METHODS:
            raise ValueError(
                f"unsupported bootstrap_fallback_method: {self.bootstrap_fallback_method}"
            )
        if self.bootstrap_method == self.bootstrap_fallback_method:
            raise ValueError("bootstrap fallback must differ from the primary method")
        if not isinstance(self.difference_decimals, int) or self.difference_decimals < 0:
            raise ValueError("difference_decimals must be a non-negative integer")
        if self.wilcoxon_zero_method not in WILCOXON_ZERO_METHODS:
            raise ValueError(
                f"unsupported wilcoxon_zero_method: {self.wilcoxon_zero_method}"
            )
        if self.wilcoxon_method not in WILCOXON_METHODS:
            raise ValueError(f"unsupported wilcoxon_method: {self.wilcoxon_method}")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be strictly between 0 and 1")

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-compatible configuration fields in stable order."""

        return asdict(self)


def _config(config: StatisticsConfig | None) -> StatisticsConfig:
    return config or StatisticsConfig()


def _sort_key(value: object) -> tuple[str, str]:
    return type(value).__name__, str(value)


def _paired_arrays(
    first: Mapping[object, float], second: Mapping[object, float]
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Align two metric mappings by user id and validate finite values."""

    first_ids = set(first)
    second_ids = set(second)
    if first_ids != second_ids:
        missing_from_first = sorted(second_ids - first_ids, key=_sort_key)
        missing_from_second = sorted(first_ids - second_ids, key=_sort_key)
        raise ValueError(
            "paired observations must contain the same users; "
            f"missing_from_first={missing_from_first!r}, "
            f"missing_from_second={missing_from_second!r}"
        )
    if not first_ids:
        raise ValueError("paired observations require at least one user")

    user_ids = sorted(first_ids, key=_sort_key)
    left = np.asarray([float(first[user_id]) for user_id in user_ids], dtype=float)
    right = np.asarray([float(second[user_id]) for user_id in user_ids], dtype=float)
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("paired observations must contain only finite numbers")
    return left, right, [str(user_id) for user_id in user_ids]


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


def _warning_text(items: Sequence[warnings.WarningMessage]) -> list[str]:
    return list(dict.fromkeys(str(item.message) for item in items))


def _bootstrap_result(
    left: np.ndarray,
    right: np.ndarray,
    cfg: StatisticsConfig,
    method: str,
) -> tuple[float, float, list[str]]:
    """Run SciPy bootstrap and return its interval plus emitted warnings."""

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = stats.bootstrap(
            (left, right),
            lambda values_left, values_right: np.mean(values_left - values_right),
            paired=True,
            vectorized=False,
            n_resamples=cfg.bootstrap_resamples,
            confidence_level=cfg.confidence_level,
            method=method,
            rng=np.random.default_rng(cfg.seed),
        )
    low = float(result.confidence_interval.low)
    high = float(result.confidence_interval.high)
    if not math.isfinite(low) or not math.isfinite(high):
        raise ValueError("bootstrap produced a non-finite confidence interval")
    return low, high, _warning_text(captured)


def bootstrap_paired_mean_difference(
    first: Mapping[object, float],
    second: Mapping[object, float],
    *,
    config: StatisticsConfig | None = None,
) -> dict[str, Any]:
    """Estimate a paired mean difference and a deterministic confidence interval."""

    cfg = _config(config)
    left, right, user_ids = _paired_arrays(first, second)
    observed = float(np.mean(np.round(left - right, cfg.difference_decimals)))
    warnings_out: list[str] = []
    if len(user_ids) < 2:
        warnings_out.append("paired bootstrap requires at least two users")
        return {
            "valid": True,
            "estimable": False,
            "paired": True,
            "n": len(user_ids),
            "estimate": observed,
            "difference": observed,
            "confidence_interval": {
                "level": cfg.confidence_level,
                "low": None,
                "high": None,
            },
            "method": "not_estimable_insufficient_users",
            "method_name": "scipy.stats.bootstrap",
            "seed": cfg.seed,
            "bootstrap_resamples": cfg.bootstrap_resamples,
            "warnings": warnings_out,
        }
    method = cfg.bootstrap_method
    fallback_from: str | None = None
    try:
        low, high, emitted = _bootstrap_result(left, right, cfg, method)
        warnings_out.extend(emitted)
    except (ValueError, RuntimeError, FloatingPointError) as exc:
        fallback_from = method
        warnings_out.append(f"primary bootstrap method {method} was not estimable: {exc}")
        method = cfg.bootstrap_fallback_method
        low, high, emitted = _bootstrap_result(left, right, cfg, method)
        warnings_out.extend(emitted)
        warnings_out.append(f"bootstrap fallback applied: {method}")

    result: dict[str, Any] = {
        "valid": True,
        "estimable": True,
        "paired": True,
        "n": len(user_ids),
        "estimate": observed,
        "difference": observed,
        "confidence_interval": {
            "level": cfg.confidence_level,
            "low": low,
            "high": high,
        },
        "method": method,
        "method_name": "scipy.stats.bootstrap",
        "seed": cfg.seed,
        "bootstrap_resamples": cfg.bootstrap_resamples,
        "warnings": list(dict.fromkeys(warnings_out)),
    }
    if fallback_from is not None:
        result["fallback_from"] = fallback_from
    return result


def _validate_algorithm_observations(
    observations: Mapping[str, Mapping[object, float]], *, minimum_algorithms: int
) -> tuple[list[str], list[str], list[np.ndarray]]:
    if len(observations) < minimum_algorithms:
        if minimum_algorithms == 3:
            raise ValueError("Friedman test requires at least three algorithms")
        raise ValueError(f"requires at least {minimum_algorithms} algorithms")
    if not observations:
        raise ValueError("observations cannot be empty")

    algorithm_ids = sorted(observations)
    first_ids = set(observations[algorithm_ids[0]])
    if not first_ids:
        raise ValueError("observations require at least one user")
    for algorithm_id in algorithm_ids[1:]:
        if set(observations[algorithm_id]) != first_ids:
            raise ValueError("all algorithms must contain the same users")
    user_ids = sorted(first_ids, key=_sort_key)
    arrays = []
    for algorithm_id in algorithm_ids:
        values = np.asarray(
            [float(observations[algorithm_id][user_id]) for user_id in user_ids],
            dtype=float,
        )
        if not np.isfinite(values).all():
            raise ValueError("observations must contain only finite numbers")
        arrays.append(values)
    return algorithm_ids, [str(value) for value in user_ids], arrays


def friedman_test(
    observations: Mapping[str, Mapping[object, float]],
) -> dict[str, Any]:
    """Run the global Friedman test on aligned per-user observations."""

    algorithm_ids, user_ids, arrays = _validate_algorithm_observations(
        observations, minimum_algorithms=3
    )
    if len(user_ids) < 3:
        raise ValueError("Friedman test requires at least three users")
    warnings_out: list[str] = []
    if len(user_ids) <= 10:
        warnings_out.append("Friedman chi-square approximation may be unreliable for n <= 10")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = stats.friedmanchisquare(*arrays)
    warnings_out.extend(_warning_text(captured))
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    if not math.isfinite(statistic) or not math.isfinite(p_value):
        warnings_out.append("Friedman returned a non-finite result for a degenerate distribution")
    return {
        "valid": True,
        "estimable": math.isfinite(statistic) and math.isfinite(p_value),
        "n": len(user_ids),
        "algorithm_count": len(algorithm_ids),
        "algorithms": algorithm_ids,
        "statistic": statistic if math.isfinite(statistic) else None,
        "p_value": p_value if math.isfinite(p_value) else None,
        "method": "scipy.stats.friedmanchisquare",
        "warnings": list(dict.fromkeys(warnings_out)),
    }


def _tie_count(nonzero_differences: np.ndarray) -> int:
    if not len(nonzero_differences):
        return 0
    _, counts = np.unique(np.abs(nonzero_differences), return_counts=True)
    return int(np.sum(np.maximum(counts - 1, 0)))


def wilcoxon_paired(
    first: Mapping[object, float],
    second: Mapping[object, float],
    *,
    config: StatisticsConfig | None = None,
) -> dict[str, Any]:
    """Run a bilateral paired Wilcoxon test with explicit tie/zero handling."""

    cfg = _config(config)
    left, right, user_ids = _paired_arrays(first, second)
    differences = np.round(left - right, cfg.difference_decimals)
    zero_count = int(np.count_nonzero(differences == 0.0))
    tie_count = _tie_count(differences[differences != 0.0])
    warnings_out: list[str] = []
    if zero_count:
        warnings_out.append(
            f"zeros present: {zero_count}; zero_method={cfg.wilcoxon_zero_method}"
        )
    if tie_count:
        warnings_out.append(f"ties present after rounding: {tie_count}")

    if zero_count == len(differences):
        warnings_out.append("all paired differences are zero; Wilcoxon is not estimable")
        return {
            "valid": True,
            "estimable": False,
            "paired": True,
            "n": len(user_ids),
            "effective_n": 0,
            "zero_count": zero_count,
            "tie_count": tie_count,
            "mean_difference": 0.0,
            "statistic": None,
            "p_value": None,
            "method": "not_estimable_all_differences_zero",
            "method_requested": cfg.wilcoxon_method,
            "zero_method": cfg.wilcoxon_zero_method,
            "alternative": "two-sided",
            "warnings": warnings_out,
        }

    if len(differences) < 2:
        warnings_out.append("paired Wilcoxon requires at least two users")
        return {
            "valid": True,
            "estimable": False,
            "paired": True,
            "n": len(user_ids),
            "effective_n": len(differences) - zero_count,
            "zero_count": zero_count,
            "tie_count": tie_count,
            "mean_difference": float(np.mean(differences)),
            "statistic": None,
            "p_value": None,
            "method": "not_estimable_insufficient_users",
            "method_requested": cfg.wilcoxon_method,
            "zero_method": cfg.wilcoxon_zero_method,
            "alternative": "two-sided",
            "warnings": warnings_out,
        }

    method = cfg.wilcoxon_method
    if method == "auto":
        method = "exact" if zero_count == 0 and tie_count == 0 else "approx"
    elif method == "exact" and (zero_count or tie_count):
        method = "approx"
        warnings_out.append("exact Wilcoxon is invalid with zeros or ties; method changed to approx")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = stats.wilcoxon(
            differences,
            zero_method=cfg.wilcoxon_zero_method,
            alternative="two-sided",
            method=method,
        )
    warnings_out.extend(_warning_text(captured))
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    return {
        "valid": True,
        "estimable": math.isfinite(statistic) and math.isfinite(p_value),
        "paired": True,
        "n": len(user_ids),
        "effective_n": len(differences) - zero_count,
        "zero_count": zero_count,
        "tie_count": tie_count,
        "mean_difference": float(np.mean(differences)),
        "statistic": statistic if math.isfinite(statistic) else None,
        "p_value": p_value if math.isfinite(p_value) else None,
        "method": method,
        "method_requested": cfg.wilcoxon_method,
        "zero_method": cfg.wilcoxon_zero_method,
        "alternative": "two-sided",
        "warnings": list(dict.fromkeys(warnings_out)),
    }


def holm_adjust(
    p_values: Mapping[str, float], *, alpha: float = 0.05
) -> dict[str, Any]:
    """Apply Holm step-down correction with stable label tie-breaking."""

    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")
    normalized = {str(label): float(value) for label, value in p_values.items()}
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in normalized.values()):
        raise ValueError("Holm p-values must be finite numbers in [0, 1]")

    ordered = sorted(normalized, key=lambda label: (normalized[label], label))
    family_size = len(ordered)
    previous = 0.0
    rows: list[dict[str, Any]] = []
    for rank, label in enumerate(ordered, start=1):
        adjusted = min(1.0, max(previous, (family_size - rank + 1) * normalized[label]))
        previous = adjusted
        rows.append(
            {
                "label": label,
                "rank": rank,
                "p_value": normalized[label],
                "adjusted_p_value": adjusted,
                "reject": adjusted <= alpha,
            }
        )
    return {
        "method": "holm-step-down",
        "alpha": alpha,
        "family_size": family_size,
        "order": ordered,
        "comparisons": rows,
    }


def compare_paired_algorithms(
    observations: Mapping[str, Mapping[object, float]],
    *,
    config: StatisticsConfig | None = None,
    pairs: Sequence[tuple[str, str]] | None = None,
    family: str = "algorithm-comparison",
) -> dict[str, Any]:
    """Produce a complete serializable statistical comparison artefact."""

    cfg = _config(config)
    algorithm_ids, user_ids, _arrays = _validate_algorithm_observations(
        observations, minimum_algorithms=2
    )
    selected_pairs = list(pairs or combinations(algorithm_ids, 2))
    for first_id, second_id in selected_pairs:
        if first_id not in observations or second_id not in observations:
            raise ValueError(f"unknown algorithm in pair: {(first_id, second_id)!r}")
        if first_id == second_id:
            raise ValueError("comparison pairs must contain two different algorithms")

    comparisons: list[dict[str, Any]] = []
    for first_id, second_id in selected_pairs:
        label = f"{first_id}__vs__{second_id}"
        wilcoxon = wilcoxon_paired(
            observations[first_id], observations[second_id], config=cfg
        )
        bootstrap = bootstrap_paired_mean_difference(
            observations[first_id], observations[second_id], config=cfg
        )
        comparisons.append(
            {
                "label": label,
                "first": first_id,
                "second": second_id,
                "bootstrap": bootstrap,
                "wilcoxon": wilcoxon,
            }
        )

    p_values = {
        row["label"]: row["wilcoxon"]["p_value"]
        for row in comparisons
        if row["wilcoxon"]["p_value"] is not None
    }
    holm = holm_adjust(p_values, alpha=cfg.alpha)
    holm_by_label = {row["label"]: row for row in holm["comparisons"]}
    for row in comparisons:
        adjusted = holm_by_label.get(row["label"])
        row["adjusted_p_value"] = adjusted["adjusted_p_value"] if adjusted else None
        row["holm_reject"] = adjusted["reject"] if adjusted else False
        row["holm_rank"] = adjusted["rank"] if adjusted else None
    return {
        "statistics_version": STATISTICS_VERSION,
        "family": family,
        "configuration": cfg.as_dict(),
        "algorithm_order": algorithm_ids,
        "user_count": len(user_ids),
        "input_sha256": _canonical_hash(
            {
                algorithm_id: {
                    str(user_id): float(observations[algorithm_id][user_id])
                    for user_id in sorted(observations[algorithm_id], key=_sort_key)
                }
                for algorithm_id in algorithm_ids
            }
        ),
        "friedman": _safe_friedman(observations),
        "pairwise": {
            "comparisons": comparisons,
            "holm": holm,
        },
    }


def _safe_friedman(observations: Mapping[str, Mapping[object, float]]) -> dict[str, Any]:
    try:
        return friedman_test(observations)
    except ValueError as exc:
        return {
            "valid": False,
            "estimable": False,
            "n": len(next(iter(observations.values()), {})),
            "algorithm_count": len(observations),
            "statistic": None,
            "p_value": None,
            "method": "scipy.stats.friedmanchisquare",
            "warnings": [str(exc)],
        }


# Explicit alias used by callers that want to name the output rather than the
# implementation detail of the comparison.
statistical_comparison = compare_paired_algorithms
