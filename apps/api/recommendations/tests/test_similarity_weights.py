"""Tests for the current curated-tag similarity contract."""

from __future__ import annotations

import pytest

from catalogue.models import CuratedLabel, GameWork
from recommendations.content.features import (
    FACET_WEIGHTS,
    FEATURE_SET_VERSION,
    TAG_IDF_FORMULA_VERSION,
    feature_vector,
    tag_idf_profile,
)
from recommendations.content.similarity import SIMILARITY_RULE_VERSION, facet_similarity


def test_curated_tags_are_the_primary_content_facet() -> None:
    assert FACET_WEIGHTS == {
        "tag": 0.60,
        "theme": 0.20,
        "feature": 0.10,
        "mode": 0.05,
        "platform": 0.05,
        "franchise": 0.02,
        "developer": 0.015,
    }
    assert FEATURE_SET_VERSION == "fs-v13-family-weighted-tags"
    assert SIMILARITY_RULE_VERSION == "facet-similarity-v8"
    assert TAG_IDF_FORMULA_VERSION == "smoothed-idf-l2-per-family-v2"


def test_tag_and_platform_core_weights_sum_to_one() -> None:
    profile = {"tag:action": 1.0, "platform:pc": 1.0}
    candidate = {"tag:action": 1.0, "platform:pc": 1.0}

    evidence = facet_similarity(profile, candidate)

    assert evidence["core_score"] == pytest.approx(1.0)
    assert evidence["facet_scores"] == {
        "tag": 1.0,
        "platform": 1.0,
        "theme": 0.0,
        "mode": 0.0,
        "feature": 0.0,
        "franchise": 0.0,
        "developer": 0.0,
    }


@pytest.mark.django_db
def test_idf_gives_rare_tags_more_weight_without_changing_tag_block_norm() -> None:
    common = CuratedLabel.objects.create(name="Common", slug="common", kind="genre")
    rare = CuratedLabel.objects.create(name="Rare", slug="rare", kind="subgenre")
    works = []
    for index in range(3):
        work = GameWork.objects.create(
            canonical_slug=f"idf-work-{index}",
            original_title=f"IDF Work {index}",
            in_corpus=True,
            corpus_version="idf-test",
        )
        work.curated_labels.add(common)
        if index == 0:
            work.curated_labels.add(rare)
        works.append(work)

    idf = tag_idf_profile("idf-test")
    vector = feature_vector(works[0], tag_idf=idf)

    assert idf["rare"] > idf["common"]
    assert vector["tag:rare"] > vector["tag:common"]
    assert (
        vector["tag:rare"] ** 2 + vector["tag:common"] ** 2
    ) ** 0.5 == pytest.approx(FACET_WEIGHTS["tag"])
