"""Shared English-alias set construction for the catalogue.

Tolerant search (:mod:`catalogue.search`) matches *only* on
``GameAlias.normalized_value``, so every code path that creates a work -- the
IGDB importer and the one-off :mod:`catalogue.management.commands.backfill_game_aliases`
command -- must agree on which alias rows a work should have. This module owns
that decision so the two stay in lockstep.
"""

from __future__ import annotations

from collections.abc import Iterable

from catalogue.normalization import normalize_title

# Every alias this module builds is an English-locale alias. The Spanish
# aliases the legacy Wikidata importer created are never touched here.
ALIAS_LOCALE = "en"


def desired_aliases(
    name: str,
    title_en: str = "",
    alternative_names: Iterable[str] = (),
) -> dict[str, str]:
    """Return ``{normalized_value: display_value}`` for a work's English aliases.

    The primary alias is ``name``. Each non-empty ``alternative_names`` entry is
    added; the first spelling wins on a normalized-value collision. ``title_en``
    is added only when it normalizes to a value not already present. Strings that
    normalize to ``""`` (empty / whitespace / accent-only) are dropped.
    """
    aliases: dict[str, str] = {}
    for value in (name, *alternative_names):
        text = (value or "").strip()
        if not text:
            continue
        normalized = normalize_title(text)
        if normalized:
            aliases.setdefault(normalized, text)

    extra = (title_en or "").strip()
    if extra:
        normalized = normalize_title(extra)
        if normalized and normalized not in aliases:
            aliases[normalized] = extra

    return aliases
