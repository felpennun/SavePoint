"""Tests for the fs-v6 facet-aware content similarity contract."""

from __future__ import annotations

import pytest

from recommendations.content.similarity import facet_similarity


def test_optional_metadata_is_not_a_bonus_by_itself() -> None:
    profile = {
        "genre:rpg": 1.0,
        "platform:pc": 1.0,
        "franchise:trusted-saga": 1.0,
        "developer:trusted-studio": 1.0,
    }
    without_optional = {
        "genre:rpg": 0.5,
        "platform:console": 0.25,
    }
    unrelated_optional = {
        **without_optional,
        "franchise:other-saga": 0.15,
        "developer:other-studio": 0.10,
    }

    missing = facet_similarity(profile, without_optional)
    unrelated = facet_similarity(profile, unrelated_optional)

    assert missing["score"] == pytest.approx(unrelated["score"])
    assert missing["optional_bonus"] == 0.0
    assert unrelated["optional_bonus"] == 0.0


def test_matching_saga_and_developer_add_only_a_personalised_bonus() -> None:
    profile = {
        "genre:rpg": 1.0,
        "platform:pc": 1.0,
        "franchise:trusted-saga": 1.0,
        "developer:trusted-studio": 1.0,
    }
    candidate = {
        "genre:rpg": 0.5,
        "platform:console": 0.25,
        "franchise:trusted-saga": 0.15,
        "developer:trusted-studio": 0.10,
    }

    result = facet_similarity(profile, candidate)

    assert result["core_score"] == pytest.approx(2 / 3)
    assert result["optional_bonus"] > 0
    assert result["score"] > result["core_score"]
    assert result["score"] <= 1.0
    assert result["facet_scores"]["franchise"] == 1.0
    assert result["facet_scores"]["developer"] == 1.0


def test_core_genre_similarity_survives_missing_optional_facets() -> None:
    profile = {"genre:rpg": 1.0, "platform:pc": 1.0}
    candidate = {"genre:rpg": 0.5, "platform:console": 0.25}

    result = facet_similarity(profile, candidate)

    assert result["core_score"] == pytest.approx(2 / 3)
    assert result["score"] == pytest.approx(result["core_score"])
    assert result["facet_scores"]["franchise"] == 0.0
    assert result["facet_scores"]["developer"] == 0.0

