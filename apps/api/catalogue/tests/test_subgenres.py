"""Tests for the explicit, versioned raw-keyword to subgenre curation."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from catalogue.models import GameWork, Keyword, Subgenre
from catalogue.subgenres import canonical_name_for_keyword


def _keyword(igdb_id: int, name: str) -> Keyword:
    return Keyword.objects.create(igdb_id=igdb_id, name=name, slug=f"keyword-{igdb_id}")


def _work(slug: str, *keywords: Keyword) -> GameWork:
    work = GameWork.objects.create(canonical_slug=slug, original_title=slug)
    work.keywords.set(keywords)
    return work


def test_explicit_mapping_collapses_roguelike_variants() -> None:
    assert canonical_name_for_keyword("rogue-like") == "roguelike"
    assert canonical_name_for_keyword("roguelite") == "roguelike"
    assert canonical_name_for_keyword("roguelike") == "roguelike"
    assert canonical_name_for_keyword("pixel graphics") == "pixelart"
    assert canonical_name_for_keyword("side-scrolling") == "sidescroller"
    assert canonical_name_for_keyword("minigames") == "minigame"
    assert canonical_name_for_keyword("shmup") == "shoot'em up"
    assert canonical_name_for_keyword("action-adventure") == "action adventure"
    assert canonical_name_for_keyword("trading card game") == "card game"
    assert canonical_name_for_keyword("card battler") == "card game"
    assert canonical_name_for_keyword("unlisted community tag") is None


@pytest.mark.django_db
def test_curation_excludes_marked_keywords_and_unlisted_values() -> None:
    roguelike = _keyword(1, "roguelike")
    roguelite = _keyword(2, "roguelite")
    game_dev = _keyword(3, "game dev")
    unlisted = _keyword(4, "unlisted community tag")
    _work("first", roguelike, game_dev, unlisted)
    _work("second", roguelite)

    output = StringIO()
    call_command("curate_subgenres", stdout=output, evidence_json="-")

    assert Subgenre.objects.values_list("name", flat=True).get() == "roguelike"
    subgenre = Subgenre.objects.get(name="roguelike")
    assert set(subgenre.source_keywords.values_list("name", flat=True)) == {"roguelike", "roguelite"}
    assert set(subgenre.works.values_list("canonical_slug", flat=True)) == {"first", "second"}
    assert "game dev" not in set(Subgenre.objects.values_list("name", flat=True))
    assert "unlisted community tag" not in set(Subgenre.objects.values_list("name", flat=True))


@pytest.mark.django_db
def test_curation_deduplicates_multiple_raw_rows_and_drops_singletons() -> None:
    first_space_combat = _keyword(24, "space combat")
    second_space_combat = _keyword(18526, "space combat")
    singleton = _keyword(25, "nature minds")
    _work("space-a", first_space_combat)
    _work("space-b", second_space_combat)
    _work("nature", singleton)

    call_command("curate_subgenres", evidence_json="-")

    assert set(Subgenre.objects.values_list("name", flat=True)) == {"spacecombat"}
    space = Subgenre.objects.get(name="spacecombat")
    assert space.source_keywords.count() == 2
    assert space.works.count() == 2
