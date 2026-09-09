"""Tests for the fs-v9 facet-aware content similarity contract."""

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


def test_optional_match_is_not_diluted_by_unrelated_profile_values() -> None:
    profile = {
        "genre:rpg": 1.0,
        "platform:pc": 1.0,
        "developer:team-cherry": 0.2,
        "developer:supergiant-games": 0.2,
        "developer:concernedape": 0.2,
        "developer:fromsoftware": 0.2,
    }
    candidate = {
        "genre:rpg": 0.5,
        "platform:console": 0.25,
        "developer:team-cherry": 0.1,
    }

    result = facet_similarity(profile, candidate)

    assert result["facet_scores"]["developer"] == pytest.approx(1.0)
    assert result["optional_bonus"] == pytest.approx(0.015)


def test_optional_bonus_uses_the_new_saga_and_developer_maxima() -> None:
    profile = {
        "genre:rpg": 1.0,
        "platform:pc": 1.0,
        "franchise:trusted-saga": 1.0,
        "developer:trusted-studio": 1.0,
    }
    candidate = {
        "genre:rpg": 0.5,
        "genre:shooter": 0.5,
        "platform:console": 0.25,
        "franchise:trusted-saga": 0.20,
        "developer:trusted-studio": 0.15,
    }

    result = facet_similarity(profile, candidate)

    assert result["optional_bonus"] == pytest.approx(0.035)


def test_core_precision_favors_narrower_candidate_metadata() -> None:
    profile = {
        "genre:rpg": 0.7,
        "genre:adventure": 0.3,
        "platform:pc": 1.0,
    }
    narrow = {
        "genre:rpg": 0.5,
        "platform:pc": 0.25,
    }
    broad = {
        "genre:rpg": 0.25,
        "genre:adventure": 0.25,
        "genre:shooter": 0.25,
        "genre:puzzle": 0.25,
        "platform:pc": 0.25,
    }

    narrow_result = facet_similarity(profile, narrow)
    broad_result = facet_similarity(profile, broad)

    assert narrow_result["facet_scores"]["genre"] > broad_result["facet_scores"]["genre"]


def test_core_genre_similarity_survives_missing_optional_facets() -> None:
    profile = {"genre:rpg": 1.0, "platform:pc": 1.0}
    candidate = {"genre:rpg": 0.5, "platform:console": 0.25}

    result = facet_similarity(profile, candidate)

    assert result["core_score"] == pytest.approx(2 / 3)
    assert result["score"] == pytest.approx(result["core_score"])
    assert result["facet_scores"]["franchise"] == 0.0
    assert result["facet_scores"]["developer"] == 0.0
