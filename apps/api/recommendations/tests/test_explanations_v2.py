"""Deterministic, localisable explanation tokens for Phase 3."""

from __future__ import annotations

from recommendations.content.explain import explain
from recommendations.content.variants import ALGORITHM_REGISTRY


def test_reason_signals_are_stable_and_limited_to_present_overlap() -> None:
    spec = ALGORITHM_REGISTRY["content-cbf-weighted-v1"]
    candidate = {"genre:rpg": 0.5, "platform:pc": 1.0, "genre:ignored": 0.2}
    profile = {"genre:rpg": 0.4, "platform:pc": 0.3, "genre:absent": 1.0}

    first = explain(candidate, profile, spec)
    second = explain(candidate, profile, spec)

    assert first == second
    assert first["reason_signals"] == [
        {"kind": "platform", "value": "pc", "contribution_pct": 0.6},
        {"kind": "genre", "value": "rpg", "contribution_pct": 0.4},
    ]
    assert len(first["reason_signals"]) == 2
    assert all(signal["value"] != "absent" for signal in first["reason_signals"])


def test_no_overlap_returns_no_reason_and_preserves_negative_evidence() -> None:
    spec = ALGORITHM_REGISTRY["content-cbf-neg-v1"]

    result = explain(
        {"genre:rpg": 1.0},
        {"genre:puzzle": 1.0},
        spec,
        negative_similarity=0.75,
    )

    assert result["contributions"] == []
    assert result["reason_signals"] == []
    assert result["negative_similarity"] == 0.75
