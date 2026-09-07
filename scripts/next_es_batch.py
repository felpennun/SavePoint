"""Print the next N untranslated rows from the popularity-ranked queue.

Usage::  python scripts/next_es_batch.py [N]   (default N=120)

Emits one JSON object per line -- ``{"slug": ..., "en": ...}`` -- for queue rows
in ``data/localization/_pending-es.jsonl`` that are not yet in
``summaries-es.work.jsonl``. Feed these to a translator, then hand the resulting
``{slug: spanish}`` object to ``scripts/append_es_batch.py``.

Splitting is on ``"\n"`` only (never ``str.splitlines()``): some English
summaries contain U+0085 / U+2028 / U+2029, which ``splitlines()`` would treat
as line breaks and shatter a JSON record across "lines".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LOC = Path(__file__).resolve().parents[1] / "data" / "localization"
NL = "\n"


def _iter_jsonl(path: Path):
    for raw in path.read_text(encoding="utf-8").split(NL):
        raw = raw.strip()
        if raw:
            yield json.loads(raw)


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 120

    work = LOC / "summaries-es.work.jsonl"
    done = {rec["slug"] for rec in _iter_jsonl(work)} if work.exists() else set()

    emitted = 0
    for rec in _iter_jsonl(LOC / "_pending-es.jsonl"):
        if rec["slug"] in done:
            continue
        print(json.dumps({"slug": rec["slug"], "en": rec["en"]}, ensure_ascii=False))
        emitted += 1
        if emitted >= n:
            break

    print(f"# emitted {emitted}; done {len(done)}", file=sys.stderr)


if __name__ == "__main__":
    main()
