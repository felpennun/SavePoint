"""Versioned editorial mapping from raw IGDB keywords to subgenres.

The raw ``Keyword`` rows are deliberately untouched. Only names listed in
``CURATION_RULES`` can enter the derived subgenre corpus; an omitted keyword is
not silently promoted to a subgenre.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Final


SUBGENRE_CURATION_VERSION: Final = "subgenres-2026.09.10-v4"
MIN_WORK_FREQUENCY: Final = 2

# The first item is the canonical display value; the remaining items are raw
# IGDB spellings accepted for that value. The list is intentionally explicit:
# editorial changes must be reviewable and reproducible rather than inferred
# from an aggressive fuzzy matcher.
CURATION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("1990s", ("1990's", "1990s")),
    ("1-bit", ("1bit", "1-bit")),
    ("autobattler", ("auto battler", "autobattler")),
    ("autochess", ("auto chess", "autochess")),
    ("bossfight", ("boss fight", "bossfight")),
    ("colorblind friendly", ("color-blind friendly", "colorblind friendly")),
    ("cross-play", ("crossplay", "cross-play")),
    ("deckbuilding", ("deck building", "deck-building", "deckbuilding", "deckbuilder")),
    ("dungeons & dragons", ("dungeons dragons", "dungeons & dragons")),
    ("e-sports", ("esports", "e-sports")),
    ("fanservice", ("fan service", "fanservice")),
    ("gamedev", ("game dev", "gamedev")),
    ("gamejam", ("game jam", "gamejam")),
    ("gameshow", ("game show", "gameshow")),
    ("highscore", ("high score", "highscore")),
    ("hip-hop", ("hiphop", "hip-hop")),
    ("lovecraft", ("h. p. lovecraft", "h.p.lovecraft", "lovecraft")),
    ("k-pop", ("kpop", "k-pop")),
    ("match3", ("match 3", "match3")),
    ("minigame", ("mini game", "minigame", "minigames")),
    ("minigolf", ("mini golf", "minigolf")),
    ("natureminds", ("nature minds", "natureminds")),
    ("non-linear", ("nonlinear", "non-linear")),
    ("old school", ("oldschool", "old school")),
    ("online co-op", ("onlinecoop", "online coop", "online co-op")),
    ("pacman", ("pac-man", "pacman")),
    ("pixelart", ("pixel art", "pixelart", "pixel graphics")),
    ("post-apocalyptic", ("postapocalyptic", "post-apocalyptic")),
    ("roadtrip", ("road trip", "roadtrip")),
    ("rollercoaster", ("roller coaster", "rollercoaster")),
    ("shoot'em up", ("shoot 'em up", "shoot'em up", "shootemup", "shmup")),
    ("shopkeeper", ("shop keeper", "shopkeeper")),
    ("sidescroller", ("side scroller", "sidescroller", "side-scrolling")),
    ("spacecombat", ("space combat", "spacecombat")),
    ("spaceship", ("space ship", "spaceship", "spaceships")),
    ("spellcaster", ("spell caster", "spellcaster")),
    ("superhero", ("super hero", "superhero")),
    ("superpower", ("superpowers", "super power", "superpower")),
    ("swordplay", ("sword play", "swordplay")),
    ("swordsorcery", ("sword & sorcery", "sword sorcery", "swordsorcery")),
    ("tangledcrisis", ("tangled crisis", "tangledcrisis")),
    ("tinyrogue", ("tiny rogue", "tinyrogue")),
    ("tmtamstudio", ("tmtam studio", "tmtamstudio")),
    ("wargame", ("war game", "wargame")),
    ("action adventure", ("action-adventure", "action adventure")),
    ("hidden object", ("hidden object",)),
    ("psychological horror", ("psychological horror",)),
    ("turn-based", ("turn-based", "turn based")),
    ("music and rhythm", ("music and rhythm",)),
    ("bullet hell", ("bullet hell",)),
    ("tower defense", ("tower defense",)),
    ("cyberpunk", ("cyberpunk",)),
    ("survival horror", ("survival horror",)),
    ("brawler", ("brawler",)),
    ("turn-based rpg", ("turn-based rpg", "turn based rpg")),
    ("2d platformer", ("2d platformer",)),
    ("dark fantasy", ("dark fantasy",)),
    ("dating simulation", ("dating simulation",)),
    ("city builder", ("city builder",)),
    ("precision platforming", ("precision platforming",)),
    ("puzzle platformer", ("puzzle platformer",)),
    ("anime", ("anime", "adapted to - anime", "based on - anime", "anime-based playable characters")),
    ("casual", ("casual", "casual game")),
    ("family friendly", ("family friendly",)),
    ("metroidvania", ("metroidvania",)),
    ("souls-like", ("soulslike", "souls-like", "souls like")),
    ("story rich", ("story rich",)),
    ("roguelike", ("rogue-like", "roguelite", "roguelike")),
    ("jrpg", ("japanese rpg", "jrpg")),
    ("action rpg", ("arpg", "actionrpg", "action-rpg", "action rpg")),
    ("battle royale", ("battle royales", "battle royale")),
    (
        "card game",
        (
            "playing cards",
            "card based combat",
            "card battler",
            "card collection",
            "collecting card game - ccg",
            "collectible card game",
            "trading card game",
            "based on - card game",
            "hanafuda card games",
            "strategy card",
            "tabletop card game",
        ),
    ),
    ("action roguelike", ("action roguelite", "action roguelike")),
    ("roguelike deckbuilding", ("roguelike deckbuilder", "roguelike deckbuilding")),
)

EXCLUDED_CANONICAL_NAMES: Final[frozenset[str]] = frozenset(
    {"gamedev", "gamejam", "gameshow", "highscore"}
)


def lookup_key(value: str) -> str:
    """Normalize only spelling representation, not semantic content."""

    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(normalized.split())


def canonical_name_for_keyword(value: str) -> str | None:
    """Return the explicitly curated canonical name, if any."""

    key = lookup_key(value)
    for canonical, variants in CURATION_RULES:
        if key in {lookup_key(variant) for variant in variants}:
            return canonical
    return None


def is_excluded_canonical(canonical_name: str) -> bool:
    return canonical_name in EXCLUDED_CANONICAL_NAMES


def curation_manifest() -> dict[str, object]:
    payload = {
        "version": SUBGENRE_CURATION_VERSION,
        "min_work_frequency": MIN_WORK_FREQUENCY,
        "excluded_canonical_names": sorted(EXCLUDED_CANONICAL_NAMES),
        "rules": [
            {"canonical": canonical, "variants": list(variants)}
            for canonical, variants in CURATION_RULES
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    payload["sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload
