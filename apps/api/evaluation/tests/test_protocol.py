"""Freeze guards for the evaluation protocol loader (EVAL-03, D-21).

Plan 02-08 Task 2. ``docs/methodology/protocol.json`` is the checked-in evidence
contract; these tests pin that it loads, that its hash is stable, and that the
loader fails closed on an over-budget tuning grid or an already-consumed test
split.
"""

from __future__ import annotations

import copy
import json

import pytest

from evaluation import protocol
from evaluation.protocol import Protocol, ProtocolError

EXPECTED_METRICS = ("precision@k", "recall@k", "ndcg@k", "map@k")


def _base_mapping(grid_size: int = 2) -> dict:
    return {
        "protocol_version": 1,
        "simulation": True,
        "limitation": "Simulation evidence only (EVAL-10).",
        "relevance": {"completed": True, "rating_half_steps_gte": 7},
        "k_values": [5, 10, 20],
        "headline": "ndcg@10",
        "split": {"strategy": "leave_one_out_per_user", "seed": 20260907},
        "candidate_set": "governed_corpus_minus_user_library_plus_heldout",
        "exclusions": "any_library_entry",
        "metrics": list(EXPECTED_METRICS),
        "tuning": {
            "select_on": "ndcg@10",
            "select_split": "validation",
            "test_runs": 1,
            "grid": _grid(grid_size),
        },
        "user_split": {"train": 3, "validation": 1, "test": 1, "seed": 20260908},
        "corpus_version": None,
        "snapshot_sha256": None,
    }


def _grid(size: int) -> list[dict]:
    return [
        {"combine_mode": "weighted_sum", "feature_set": f"fs_{i}", "params": {"w1": 0.5, "w2": 0.5}}
        for i in range(size)
    ]


# --------------------------------------------------------------------------- #
# The checked-in contract                                                      #
# --------------------------------------------------------------------------- #
def test_checked_in_protocol_loads_with_frozen_keys() -> None:
    frozen = protocol.load()

    assert isinstance(frozen, Protocol)
    assert protocol.REQUIRED_KEYS <= set(frozen.raw)
    assert frozen.k_values == (5, 10, 20)
    assert frozen.headline == "ndcg@10"
    assert frozen.metrics == EXPECTED_METRICS
    assert frozen.relevance == {"completed": True, "rating_half_steps_gte": 7}
    assert frozen.split["strategy"] == "leave_one_out_per_user"
    assert frozen.candidate_set == (
        "eligible_governed_corpus_rating_count_gte_1_or_valid_rating_"
        "minus_user_library_plus_heldout"
    )
    assert frozen.exclusions == "any_library_entry"
    assert frozen.simulation is True
    assert frozen.limitation.strip()
    # Plan 02-13 freezes the governed corpus and its evidence fingerprint.
    assert frozen.corpus_version == "2026.09.1"
    assert frozen.snapshot_sha256 == "648df3ded83dfab9e6f479a0d80291d3690e783e7b25f424b8e1e4260d839f01"
    assert frozen.protocol_version == 2
    assert frozen.candidate_set == (
        "eligible_governed_corpus_rating_count_gte_1_or_valid_rating_"
        "minus_user_library_plus_heldout"
    )


def test_checked_in_grid_is_18_configs_within_budget() -> None:
    frozen = protocol.load()
    grid = frozen.grid

    assert len(grid) == 18
    assert len(grid) <= protocol.MAX_GRID
    modes = [entry["combine_mode"] for entry in grid]
    assert modes.count("weighted_sum") == 9
    assert modes.count("multiplicative") == 3
    assert modes.count("two_stage") == 6


def test_evaluation_protocol_doc_documents_threats_to_validity() -> None:
    doc = (protocol.default_protocol_path().parent / "evaluation-protocol.md").read_text("utf-8")

    assert "## Amenazas a la validez" in doc
    assert "leave-one-out" in doc.lower()
    assert "simulation: true" in doc


# --------------------------------------------------------------------------- #
# Frozen hash                                                                  #
# --------------------------------------------------------------------------- #
def test_frozen_hash_is_stable_across_loads() -> None:
    assert protocol.load().frozen_hash() == protocol.load().frozen_hash()


def test_frozen_hash_is_key_order_independent() -> None:
    mapping = _base_mapping()
    reordered = dict(reversed(list(mapping.items())))

    assert protocol.from_mapping(mapping).frozen_hash() == protocol.from_mapping(reordered).frozen_hash()


def test_frozen_hash_moves_when_a_parameter_changes() -> None:
    mapping = _base_mapping()
    tweaked = copy.deepcopy(mapping)
    tweaked["relevance"]["rating_half_steps_gte"] = 8

    assert protocol.from_mapping(mapping).frozen_hash() != protocol.from_mapping(tweaked).frozen_hash()


# --------------------------------------------------------------------------- #
# Tuning-budget guard (D-21)                                                   #
# --------------------------------------------------------------------------- #
def test_grid_at_budget_is_accepted() -> None:
    frozen = protocol.from_mapping(_base_mapping(grid_size=protocol.MAX_GRID))
    assert len(frozen.grid) == protocol.MAX_GRID


def test_grid_over_budget_is_rejected() -> None:
    with pytest.raises(ProtocolError, match="budget"):
        protocol.from_mapping(_base_mapping(grid_size=protocol.MAX_GRID + 1))


def test_empty_grid_is_rejected() -> None:
    with pytest.raises(ProtocolError):
        protocol.from_mapping(_base_mapping(grid_size=0))


# --------------------------------------------------------------------------- #
# Consumed-test guard                                                          #
# --------------------------------------------------------------------------- #
def test_consumed_test_marker_blocks_reload(tmp_path) -> None:
    marker = tmp_path / "test-run.json"
    frozen = protocol.load()
    protocol.record_test_run(marker, frozen)

    with pytest.raises(ProtocolError, match="already been consumed"):
        protocol.load(test_run_marker=marker)


def test_consumed_test_marker_can_be_overridden_explicitly(tmp_path) -> None:
    marker = tmp_path / "test-run.json"
    protocol.record_test_run(marker, protocol.load())

    reloaded = protocol.load(test_run_marker=marker, allow_consumed_test=True)
    assert isinstance(reloaded, Protocol)


def test_marker_for_a_different_protocol_does_not_block(tmp_path) -> None:
    marker = tmp_path / "test-run.json"
    marker.write_text(json.dumps({"protocol_sha256": "deadbeef", "protocol_version": 0}), encoding="utf-8")

    assert isinstance(protocol.load(test_run_marker=marker), Protocol)


def test_missing_marker_is_a_noop(tmp_path) -> None:
    assert isinstance(protocol.load(test_run_marker=tmp_path / "nope.json"), Protocol)


# --------------------------------------------------------------------------- #
# Fail-closed structural validation                                            #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("dropped", sorted(protocol.REQUIRED_KEYS))
def test_missing_required_key_is_rejected(dropped: str) -> None:
    mapping = _base_mapping()
    mapping.pop(dropped)
    with pytest.raises(ProtocolError, match="missing required keys"):
        protocol.from_mapping(mapping)


def test_simulation_flag_must_be_true() -> None:
    mapping = _base_mapping()
    mapping["simulation"] = False
    with pytest.raises(ProtocolError, match="simulation"):
        protocol.from_mapping(mapping)


def test_relevance_rule_is_validated() -> None:
    mapping = _base_mapping()
    del mapping["relevance"]["rating_half_steps_gte"]
    with pytest.raises(ProtocolError, match="relevance"):
        protocol.from_mapping(mapping)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(ProtocolError, match="not valid JSON"):
        protocol.loads("{not json")


def test_missing_file_is_rejected(tmp_path) -> None:
    with pytest.raises(ProtocolError, match="not found"):
        protocol.load(tmp_path / "absent.json")
