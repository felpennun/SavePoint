"""Shared title normalization for search and import (Pattern 5, D-10/D-12)."""

from __future__ import annotations

import unicodedata


def normalize_title(value: str) -> str:
    """Lowercase + Unicode NFKD + strip combining marks, so search and the
    alias index tolerate case, accents, and bilingual alternative titles."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()
