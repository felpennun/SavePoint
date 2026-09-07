"""Append one batch of Spanish synopsis translations to the working log.

Usage::

    python scripts/append_es_batch.py <batch.json> [--engine claude-sonnet-5]

``<batch.json>`` is a flat object mapping ``canonical_slug`` -> Spanish synopsis
text. Every slug must exist in ``data/localization/_pending-es.jsonl`` (the
popularity-ranked queue); the script copies that row's ``sha256`` of the English
source into the log so a later English re-import can detect drift. Slugs already
present in ``summaries-es.work.jsonl`` are skipped (idempotent resume). Records
are appended as JSON lines to ``data/localization/summaries-es.work.jsonl``.

Splitting is on ``"\n"`` only (never ``str.splitlines()``): some English
summaries contain U+0085 / U+2028 / U+2029.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

LOC = Path(__file__).resolve().parents[1] / "data" / "localization"
PENDING = LOC / "_pending-es.jsonl"
WORK = LOC / "summaries-es.work.jsonl"
NL = "\n"


def _iter_jsonl(path: Path):
    for raw in path.read_text(encoding="utf-8").split(NL):
        raw = raw.strip()
        if raw:
            yield json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", type=Path)
    parser.add_argument("--engine", default="claude-sonnet-5")
    args = parser.parse_args()

    batch: dict[str, str] = json.loads(args.batch.read_text(encoding="utf-8"))
    pending = {rec["slug"]: rec["sha256"] for rec in _iter_jsonl(PENDING)}
    done = {rec["slug"] for rec in _iter_jsonl(WORK)} if WORK.exists() else set()

    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    written = skipped = rejected = 0
    lines: list[str] = []
    for slug, es in batch.items():
        if slug not in pending:
            print(f"  ! unknown slug (not in pending queue): {slug}", file=sys.stderr)
            rejected += 1
            continue
        if slug in done:
            skipped += 1
            continue
        if not isinstance(es, str) or not es.strip():
            print(f"  ! empty translation: {slug}", file=sys.stderr)
            rejected += 1
            continue
        lines.append(
            json.dumps(
                {
                    "slug": slug,
                    "sha256": pending[slug],
                    "es": es.strip(),
                    "engine": args.engine,
                    "at": now,
                },
                ensure_ascii=False,
            )
        )
        written += 1

    if lines:
        with WORK.open("a", encoding="utf-8") as handle:
            handle.write(NL.join(lines) + NL)

    total_done = len(done) + written
    print(
        f"written={written} skipped_existing={skipped} rejected={rejected} | "
        f"progress {total_done}/{len(pending)}"
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
