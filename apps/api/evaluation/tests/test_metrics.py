"""Known-answer fixtures for the hand-written ranking metrics (D-22).

Plan 02-08 Task 2. Every expectation here is computed by hand (or by an
independent reference in-test) at K in {5, 10, 20}, so a regression in
``evaluation.metrics`` cannot hide behind a shared implementation.
"""

from __future__ import annotations

import math

import pytest

from evaluation.metrics import (
    average_precision_at_k,
    dcg_at_k,
    map_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

# 20 ranked ids; relevant items sit at 1-indexed ranks 1, 5, 10, 17.
RANKED = [f"r{i:02d}" for i in range(20)]
RELEVANT = {"r00", "r04", "r09", "r16"}


def _reference_ndcg(ranked: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log(i + 2, 2) for i, wid in enumerate(ranked[:k]) if wid in relevant)
    ideal = sum(1.0 / math.log(i + 2, 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0


# --------------------------------------------------------------------------- #
# precision@k / recall@k — exact fractions at K in {5, 10, 20}                 #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("k", "expected_precision", "expected_recall"),
    [(5, 0.4, 0.5), (10, 0.3, 0.75), (20, 0.2, 1.0)],
)
def test_precision_and_recall_known_answers(k: int, expected_precision: float, expected_recall: float) -> None:
    assert precision_at_k(RANKED, RELEVANT, k) == pytest.approx(expected_precision)
    assert recall_at_k(RANKED, RELEVANT, k) == pytest.approx(expected_recall)


def test_precision_and_recall_small_fixture() -> None:
    assert precision_at_k(["a", "b", "c", "d"], {"a", "c"}, 2) == 0.5
    assert recall_at_k(["a", "b", "c", "d"], {"a", "c"}, 2) == 0.5


# --------------------------------------------------------------------------- #
# nDCG@k                                                                       #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("k", [5, 10, 20])
def test_ndcg_matches_independent_reference(k: int) -> None:
    assert ndcg_at_k(RANKED, RELEVANT, k) == pytest.approx(_reference_ndcg(RANKED, RELEVANT, k))


def test_ndcg_single_positive_at_rank_one_is_one() -> None:
    assert ndcg_at_k(["hit", "b", "c", "d", "e"], {"hit"}, 5) == 1.0


def test_ndcg_single_positive_lower_is_log_discount() -> None:
    # positive at 1-indexed rank 2 -> dcg = 1/log2(3), ideal = 1.0
    assert ndcg_at_k(["a", "hit"], {"hit"}, 5) == pytest.approx(1.0 / math.log2(3))


def test_ndcg_all_relevant_ranked_first_is_one() -> None:
    assert ndcg_at_k(RANKED, {"r00", "r01", "r02", "r03"}, 20) == pytest.approx(1.0)


def test_ndcg_is_zero_without_relevant_items() -> None:
    assert ndcg_at_k(RANKED, set(), 10) == 0.0


def test_dcg_is_zero_for_non_positive_k() -> None:
    assert dcg_at_k(RANKED, RELEVANT, 0) == 0.0


# --------------------------------------------------------------------------- #
# average precision / MAP                                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("k", "expected"),
    [
        (5, (1.0 + 2 / 5) / 4),                       # hits at ranks 1, 5
        (10, (1.0 + 2 / 5 + 3 / 10) / 4),             # + rank 10
        (20, (1.0 + 2 / 5 + 3 / 10 + 4 / 17) / 4),    # + rank 17
    ],
)
def test_average_precision_known_answers(k: int, expected: float) -> None:
    assert average_precision_at_k(RANKED, RELEVANT, k) == pytest.approx(expected)


def test_map_is_mean_of_average_precision() -> None:
    q1 = (["x", "a", "b", "c", "d"], {"x"})          # AP@5 = 1.0
    q2 = (["a", "b", "y", "c", "d"], {"y"})          # AP@5 = 1/3
    result = map_at_k([q1[0], q2[0]], [q1[1], q2[1]], 5)

    assert result == pytest.approx((1.0 + 1 / 3) / 2)


def test_map_of_empty_input_is_zero() -> None:
    assert map_at_k([], [], 10) == 0.0
