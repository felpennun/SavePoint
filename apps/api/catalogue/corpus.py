"""The governed catalogue view and its D-01/D-03 rules.

The allowlist is keyed by IGDB's stable platform slug, not by display name or
the deprecated platform category. It is intentionally kept in one module so
the offline governance command, API filters, and research code share exactly
the same boundary.
"""

from __future__ import annotations

import re
from datetime import date

from django.db.models import QuerySet

from catalogue.models import GameWork


PLATFORM_ALLOWLIST: tuple[tuple[int, str, str], ...] = (
    (6, "pc-microsoft-windows", "Windows"),
    (14, "mac", "Mac"),
    (3, "linux", "Linux"),
    (7, "playstation", "PlayStation"),
    (8, "playstation-2", "PlayStation 2"),
    (9, "playstation-3", "PlayStation 3"),
    (48, "playstation-4", "PlayStation 4"),
    (167, "playstation-5", "PlayStation 5"),
    (38, "playstation-portable", "PSP"),
    (46, "playstation-vita", "Vita"),
    (11, "xbox", "Xbox"),
    (12, "xbox-360", "Xbox 360"),
    (49, "xbox-one", "Xbox One"),
    (169, "xbox-series-x-s", "Xbox Series X|S"),
    (18, "nes", "NES"),
    (19, "snes", "SNES"),
    (4, "nintendo-64", "Nintendo 64"),
    (21, "gamecube", "GameCube"),
    (5, "wii", "Wii"),
    (41, "wii-u", "Wii U"),
    (130, "nintendo-switch", "Switch"),
    (33, "game-boy", "Game Boy"),
    (22, "game-boy-color", "Game Boy Color"),
    (24, "game-boy-advance", "Game Boy Advance"),
    (20, "nintendo-ds", "Nintendo DS"),
    (37, "nintendo-3ds", "Nintendo 3DS"),
    (64, "sega-master-system", "Master System"),
    (29, "sega-mega-drive-genesis", "Mega Drive/Genesis"),
    (35, "sega-game-gear", "Game Gear"),
    (32, "sega-saturn", "Saturn"),
    (23, "dreamcast", "Dreamcast"),
    (59, "atari-2600", "Atari 2600"),
    (66, "atari-5200", "Atari 5200"),
    (60, "atari-7800", "Atari 7800"),
    (61, "atari-lynx", "Atari Lynx"),
    (62, "atari-jaguar", "Atari Jaguar"),
    (39, "ios", "iOS"),
    (34, "android", "Android"),
    (82, "web-browser", "Web browser"),
)

ALLOWLIST_SLUGS = frozenset(slug for _igdb_id, slug, _display_name in PLATFORM_ALLOWLIST)
MIN_RECOMMENDATION_TOTAL_RATING_COUNT = 10

def is_valid_name(name: str | None) -> bool:
    """Return whether a title has at least two alphanumeric characters."""

    value = (name or "").strip()
    return bool(value) and len(re.findall(r"[^\W_]", value, flags=re.UNICODE)) >= 2


def governed_works(
    corpus_version: str | None = None,
    *,
    eligibility_cutoff_date: date | None = None,
) -> QuerySet[GameWork]:
    """Return the released, dated catalogue view, optionally pinned to one version.

    ``in_corpus`` is catalogue membership, not recommendation eligibility. The
    governance command freezes it using its explicit ``--as-of-date``.
    """

    queryset = GameWork.objects.filter(is_dlc=False, in_corpus=True)
    if eligibility_cutoff_date is not None:
        queryset = queryset.filter(first_release_date__lte=eligibility_cutoff_date)
    if corpus_version is not None:
        queryset = queryset.filter(corpus_version=corpus_version)
    return queryset


def evaluation_candidate_works(
    corpus_version: str | None = None,
    *,
    eligibility_cutoff_date: date | None = None,
) -> QuerySet[GameWork]:
    """Return catalogue works eligible for recommendation algorithms.

    The full governed catalogue remains searchable. A recommendation candidate
    needs a non-null IGDB user rating and at least ten total IGDB ratings.
    """

    return governed_works(
        corpus_version, eligibility_cutoff_date=eligibility_cutoff_date
    ).filter(
        rating__isnull=False,
        total_rating_count__gte=MIN_RECOMMENDATION_TOTAL_RATING_COUNT,
    )
