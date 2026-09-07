"""Fold the Spanish-synopsis working log into the manifest the loader reads.

Inputs (all under ``data/localization/``):

* ``summaries-es.curated.json``  -- human-reviewed slug -> Spanish text. Always wins.
* ``summaries-es.work.jsonl``    -- append-only machine-translation log. One JSON
  object per line: ``{"slug", "sha256", "es", "engine", "at"}``.

Outputs (same directory):

* ``summaries-es.json``            -- slug -> Spanish text, consumed by
  ``manage.py load_localized_summaries``.
* ``summaries-es.provenance.json`` -- slug -> {src_sha256, engine, translated_at}.

Run from anywhere: ``python scripts/build_summaries_es.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

LOC = Path(__file__).resolve().parents[1] / "data" / "localization"
NL = "\n"


def main() -> None:
    curated_path = LOC / "summaries-es.curated.json"
    work_path = LOC / "summaries-es.work.jsonl"

    curated: dict[str, str] = {}
    if curated_path.exists():
        curated = json.loads(curated_path.read_text(encoding="utf-8"))

    machine: dict[str, str] = {}
    provenance: dict[str, dict] = {}
    if work_path.exists():
        for raw in work_path.read_text(encoding="utf-8").split(NL):
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            slug = rec["slug"]
            machine[slug] = rec["es"]
            provenance[slug] = {
                "src_sha256": rec.get("sha256"),
                "engine": rec.get("engine", "unknown"),
                "translated_at": rec.get("at"),
            }

    merged = {**machine, **curated}  # curated text overrides machine text
    for slug in curated:
        provenance[slug] = {"src_sha256": None, "engine": "human-reviewed", "translated_at": None}

    (LOC / "summaries-es.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=1, sort_keys=True) + NL,
        encoding="utf-8",
    )
    (LOC / "summaries-es.provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=1, sort_keys=True) + NL,
        encoding="utf-8",
    )
    print(
        f"curated={len(curated)} machine={len(machine)} "
        f"total={len(merged)} -> data/localization/summaries-es.json"
    )


if __name__ == "__main__":
    main()
