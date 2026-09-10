"""Versioned mapping from raw IGDB facets to the editorial label vocabulary."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Final


CURATED_LABEL_VERSION: Final = "curated-labels-2026.09.10-v6"

# The UI may show these labels as one vocabulary. ``kind`` keeps their
# semantics available to recommenders and evaluation code.
CURATED_LABELS: tuple[tuple[str, str], ...] = (
    ("Action", "genre"),
    ("Adventure", "genre"),
    ("Anime", "theme"),
    ("Arcade", "genre"),
    ("Card Game", "genre"),
    ("Casual", "feature"),
    ("Co-op", "mode"),
    ("Comedy", "theme"),
    ("Cyberpunk", "genre"),
    ("Battle Royale", "subgenre"),
    ("Deckbuilder", "subgenre"),
    ("Educational", "theme"),
    ("Family Friendly", "feature"),
    ("Fantasy", "theme"),
    ("Fighting", "genre"),
    ("Historical", "theme"),
    ("Hack and Slash", "subgenre"),
    ("Horror", "theme"),
    ("Indie", "genre"),
    ("Kids", "theme"),
    ("JRPG", "subgenre"),
    ("MMO", "mode"),
    ("Metroidvania", "subgenre"),
    ("Mystery", "theme"),
    ("Multiplayer", "mode"),
    ("Open World", "feature"),
    ("Party", "theme"),
    ("Pixel Art", "feature"),
    ("Platformer", "genre"),
    ("Pinball", "genre"),
    ("Point-and-Click", "genre"),
    ("Puzzle", "genre"),
    ("RPG", "genre"),
    ("Racing", "genre"),
    ("Retro", "feature"),
    ("Roguelike", "subgenre"),
    ("Romance", "theme"),
    ("Sci-fi", "theme"),
    ("Sandbox", "feature"),
    ("Shooter", "genre"),
    ("Side Scroller", "feature"),
    ("Simulation", "genre"),
    ("Singleplayer", "mode"),
    ("Souls-like", "subgenre"),
    ("Sports", "genre"),
    ("Split Screen", "mode"),
    ("Superhero", "theme"),
    ("Stealth", "subgenre"),
    ("Story Rich", "feature"),
    ("Strategy", "genre"),
    ("Survival", "subgenre"),
    ("Tactical", "subgenre"),
    ("Trivia", "genre"),
    ("Turn-Based", "feature"),
    ("VR", "feature"),
    ("Visual Novel", "genre"),
    ("MOBA", "genre"),
    ("Music", "genre"),
)

# Existing closed IGDB facets. A source value may yield more than one
# editorial label when the target vocabulary intentionally exposes hierarchy.
GENRE_RULES: dict[str, tuple[str, ...]] = {
    "Adventure": ("Adventure",),
    "Arcade": ("Arcade",),
    "Card & Board Game": ("Card Game",),
    "Fighting": ("Fighting",),
    "Hack and slash/Beat 'em up": ("Hack and Slash",),
    "Indie": ("Indie",),
    "Platform": ("Platformer",),
    "Puzzle": ("Puzzle",),
    "Racing": ("Racing",),
    "Real Time Strategy (RTS)": ("Strategy",),
    "Role-playing (RPG)": ("RPG",),
    "Shooter": ("Shooter",),
    "Simulator": ("Simulation",),
    "Sport": ("Sports",),
    "Strategy": ("Strategy",),
    "Tactical": ("Tactical",),
    "Turn-based strategy (TBS)": ("Strategy", "Turn-Based"),
    "Visual Novel": ("Visual Novel",),
    "MOBA": ("MOBA",),
    "Music": ("Music",),
    "Pinball": ("Pinball",),
    "Point-and-click": ("Point-and-Click",),
    "Quiz/Trivia": ("Trivia",),
}

THEME_RULES: dict[str, tuple[str, ...]] = {
    "Action": ("Action",),
    "Comedy": ("Comedy",),
    "4X (explore, expand, exploit, and exterminate)": ("Strategy",),
    "Fantasy": ("Fantasy",),
    "Horror": ("Horror",),
    "Historical": ("Historical",),
    "Kids": ("Kids",),
    "Mystery": ("Mystery",),
    "Open world": ("Open World",),
    "Party": ("Party",),
    "Romance": ("Romance",),
    "Sandbox": ("Sandbox",),
    "Science fiction": ("Sci-fi",),
    "Stealth": ("Stealth",),
    "Survival": ("Survival",),
    "Educational": ("Educational",),
}

GAME_MODE_RULES: dict[str, tuple[str, ...]] = {
    "Battle Royale": ("Battle Royale", "Multiplayer"),
    "Co-operative": ("Co-op", "Multiplayer"),
    "Massively Multiplayer Online (MMO)": ("MMO", "Multiplayer"),
    "Multiplayer": ("Multiplayer",),
    "Single player": ("Singleplayer",),
    "Split screen": ("Split Screen",),
}

PLAYER_PERSPECTIVE_RULES: dict[str, tuple[str, ...]] = {
    "Virtual Reality": ("VR",),
}

def lookup_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(normalized.split())


def curation_manifest() -> dict[str, object]:
    payload = {
        "version": CURATED_LABEL_VERSION,
        "labels": [{"name": name, "kind": kind} for name, kind in CURATED_LABELS],
        "genre_rules": GENRE_RULES,
        "theme_rules": THEME_RULES,
        "game_mode_rules": GAME_MODE_RULES,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    payload["sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload
