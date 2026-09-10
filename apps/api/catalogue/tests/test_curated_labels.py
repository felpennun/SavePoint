"""Tests for the initial unified editorial label mapping."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from catalogue.models import (
    CuratedLabel,
    GameMode,
    GameWork,
    GameWorkCuratedLabel,
    Genre,
    Keyword,
    PlayerPerspective,
    Subgenre,
    Theme,
)


def _work(slug: str, *, genre: Genre | None = None, theme: Theme | None = None, mode: GameMode | None = None, perspective: PlayerPerspective | None = None, keyword: Keyword | None = None) -> GameWork:
    work = GameWork.objects.create(canonical_slug=slug, original_title=slug)
    if genre:
        work.genres.add(genre)
    if theme:
        work.themes.add(theme)
    if mode:
        work.game_modes.add(mode)
    if perspective:
        work.player_perspectives.add(perspective)
    if keyword:
        work.keywords.add(keyword)
    return work


@pytest.mark.django_db
def test_initial_mapping_uses_target_labels_and_only_hack_and_slash() -> None:
    combined = Genre.objects.create(igdb_id=25, name="Hack and slash/Beat 'em up", slug="igdb-25")
    card_board = Genre.objects.create(igdb_id=26, name="Card & Board Game", slug="igdb-26")
    tactical = Genre.objects.create(igdb_id=24, name="Tactical", slug="igdb-24")
    fantasy = Theme.objects.create(igdb_id=17, name="Fantasy", slug="igdb-17")
    cooperative = GameMode.objects.create(igdb_id=5, name="Co-operative", slug="igdb-5")
    battle_royale = GameMode.objects.create(igdb_id=6, name="Battle Royale", slug="igdb-6")
    split_screen = GameMode.objects.create(igdb_id=7, name="Split screen", slug="igdb-7")
    virtual_reality = PlayerPerspective.objects.create(igdb_id=4, name="Virtual Reality", slug="igdb-4")
    four_x = Theme.objects.create(
        igdb_id=32,
        name="4X (explore, expand, exploit, and exterminate)",
        slug="igdb-32",
    )
    metroidvania = Keyword.objects.create(igdb_id=1, name="metroidvania", slug="keyword-1")
    deckbuilder = Keyword.objects.create(igdb_id=2, name="roguelike deckbuilder", slug="keyword-2")
    metroidvania_subgenre = Subgenre.objects.create(
        name="metroidvania", slug="metroidvania", curation_version="test"
    )
    cyberpunk = Keyword.objects.create(igdb_id=3, name="cyberpunk", slug="keyword-3")
    cyberpunk_subgenre = Subgenre.objects.create(
        name="cyberpunk", slug="cyberpunk", curation_version="test"
    )
    deckbuilder_subgenre = Subgenre.objects.create(
        name="roguelike deckbuilding", slug="roguelike-deckbuilding", curation_version="test"
    )

    one_work = _work("one", genre=combined, theme=fantasy, mode=cooperative, keyword=metroidvania)
    one_work.subgenres.add(metroidvania_subgenre)
    two = _work("two", mode=battle_royale, keyword=deckbuilder)
    two.subgenres.add(deckbuilder_subgenre)
    cyber = _work("cyber", keyword=cyberpunk)
    cyber.subgenres.add(cyberpunk_subgenre)
    card = _work("card", genre=card_board)
    _work("three", genre=tactical)
    _work("four-x", theme=four_x)
    _work("split-vr", mode=split_screen, perspective=virtual_reality)

    call_command("curate_labels", stdout=StringIO())

    one = GameWork.objects.get(canonical_slug="one")
    assert set(one.curated_labels.values_list("name", flat=True)) == {
        "Co-op",
        "Fantasy",
        "Hack and Slash",
        "Metroidvania",
        "Multiplayer",
    }
    assert not CuratedLabel.objects.filter(name="Beat'em up").exists()
    assert set(two.curated_labels.values_list("name", flat=True)) == {
        "Battle Royale",
        "Deckbuilder",
        "Multiplayer",
        "Roguelike",
    }
    assert two.curated_labels.filter(name="RPG").count() == 0
    assert set(cyber.curated_labels.values_list("name", flat=True)) == {"Cyberpunk"}
    assert set(card.curated_labels.values_list("name", flat=True)) == {"Card Game"}
    assert GameWork.objects.get(canonical_slug="three").curated_labels.get(name="Tactical")
    assert GameWork.objects.get(canonical_slug="four-x").curated_labels.get(name="Strategy")
    assert set(GameWork.objects.get(canonical_slug="split-vr").curated_labels.values_list("name", flat=True)) == {
        "Split Screen",
        "VR",
    }
    assert not GameWorkCuratedLabel.objects.filter(source_kind="keyword").exists()


@pytest.mark.django_db
def test_initial_mapping_is_idempotent() -> None:
    genre = Genre.objects.create(igdb_id=1, name="Music", slug="igdb-1")
    _work("music-one", genre=genre)

    call_command("curate_labels", stdout=StringIO())
    first = GameWorkCuratedLabel.objects.count()
    call_command("curate_labels", stdout=StringIO())

    assert GameWorkCuratedLabel.objects.count() == first
    assert CuratedLabel.objects.count() == 58
