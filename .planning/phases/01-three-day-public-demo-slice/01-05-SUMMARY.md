---
phase: 01-three-day-public-demo-slice
plan: 05
subsystem: data-acquisition
tags: [wikidata, sparql, wikimedia-commons, catalogue, licensing]

requires:
  - phase: 01-02
    provides: [PostgreSQL/test runtime, non-empty test runners]

provides:
  - 150-game CC0 catalogue snapshot spanning all required eras and platform families
  - Per-asset cover-image licence manifest (19 candidates, 17 approved, 2 placeholder)
  - Human-approved catalogue-freeze.md gating Plan 01-06's import

affects: [01-06, 01-07, 01-09, catalogue, library, thesis-evidence]

actuals:
  tokens: 21000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Multi-query SPARQL merge: coverage-critical sub-queries (era/platform) run before a broad sweep, and _aggregate truncates in that insertion order before sorting for deterministic output, so targeted coverage always survives the TARGET_COUNT cut."
    - "Never hardcode/guess a Wikidata QID from memory — resolve it live via SERVICE wikibase:mwapi and verify with FILTER EXISTS before using it in a join."

key-files:
  created:
    - data/raw/wikidata-games.json
    - data/manifests/catalogue.json
    - data/manifests/assets.json
    - docs/verification/catalogue-freeze.md
  modified:
    - scripts/acquire_catalogue.py

key-decisions:
  - "Replaced the pre-existing fabricated QID VALUES list (contained non-game entities: a French commune, an organ, a historical war) with a `?game wdt:P31 wd:Q7889` class-filtered query set, so every candidate is a verified real video game."
  - "Platform coverage (xbox/sega) resolved dynamically at runtime via Wikidata's own search index (wikibase:mwapi) plus an EXISTS check, never a hand-typed QID — a raw CONTAINS(LCASE(label)) scan over the full games class reliably 504-timed-out on the public endpoint."
  - "Human approved the corpus and all 17 licensed-candidate cover images as-is via checkpoint response 'corpus aprobado', after reviewing the full coverage matrix and per-asset licence table."

patterns-established:
  - "QID verification gate: before using any Wikidata entity ID in acquisition code, verify its label via a live query — do not trust a remembered or plan-authored ID."

requirements-completed: [DATA-01, DATA-02]

coverage:
  - id: D1
    description: "Curated 150-game catalogue candidate covering pre-1990 through 2020s eras and PC/PlayStation/Xbox/Nintendo/Sega platform families, CC0-licensed structured data."
    requirement: DATA-01
    verification:
      - kind: other
        ref: "python scripts/acquire_catalogue.py --validate-only"
        status: pass
    human_judgment: true
    rationale: "DATA-01 requires a 'legally suitable' dataset -- that is a legal/curation judgment the human author must make, not something an automated check can certify. Approved via checkpoint."
  - id: D2
    description: "Manifest records source, URL, licence, retrieval date, cutoff, query text, record count, and SHA-256 checksum linking catalogue.json/assets.json to the raw snapshot."
    requirement: DATA-02
    verification:
      - kind: other
        ref: "python scripts/acquire_catalogue.py --validate-only (checksum + structural validation)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per-asset cover-image licence freeze: 19 candidates reviewed, 17 approved with complete author/licence/licence-URL/source-URL, 2 auto-resolved to placeholder for incomplete metadata, zero left unresolved."
    verification:
      - kind: manual_procedural
        ref: "docs/verification/catalogue-freeze.md checkpoint review"
        status: pass
    human_judgment: true
    rationale: "Image licence/attribution acceptance is a legal decision (D-07); required explicit human sign-off before any asset can display."

duration: 45min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 05: Legally-Traceable Bilingual Catalogue Corpus Summary

**150-game CC0 catalogue snapshot from a corrected Wikidata query (real games only, dynamically-verified platform coverage) with a human-approved, per-file cover-image licence freeze.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-04T16:15:00Z
- **Completed:** 2026-09-04T16:36:31Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Rebuilt the catalogue acquisition query from a fabricated, hand-typed QID list into a dynamic `wdt:P31 wd:Q7889` (instance-of-video-game) class filter, with targeted era/platform sub-queries so D-05/D-06 coverage is guaranteed by construction rather than hoped for.
- Fixed a URL-decoding bug that silently sent every candidate cover image to the placeholder regardless of its actual licence.
- Ran the acquisition live against Wikidata/Commons: 150 games (all 5 required eras, all 5 required platform families, 77 distinct genres), 19 candidate cover images with 17 carrying complete, verifiable licence metadata.
- Presented the full coverage matrix and per-asset licence table to the human author at the blocking-human checkpoint; obtained explicit approval ("corpus aprobado") and recorded it, with checksums, in `docs/verification/catalogue-freeze.md` as APPROVED.

## Task Commits

Each task was committed atomically:

1. **Task 1: Preparar candidato de corpus y manifests sin importarlo** - `a2509e0` (feat)
2. **Task 2: Congelar corpus y allowlist de assets** - `8ef6074` (docs)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `scripts/acquire_catalogue.py` - Rewrote query strategy (class filter + dynamic platform resolution + retries), fixed `_image_title()` URL-decoding.
- `data/raw/wikidata-games.json` - Immutable curated snapshot (150 games, CC0).
- `data/manifests/catalogue.json` - Source/licence/checksum/coverage manifest for the snapshot.
- `data/manifests/assets.json` - Per-asset licence decision (17 candidate, 2 placeholder), all pending-human-review until this plan's Task 2.
- `docs/verification/catalogue-freeze.md` - Signed/dated APPROVED freeze record.

## Decisions Made

- Discarded the pre-existing (already-committed, but never executed) fabricated QID list entirely rather than patching individual bad entries — the whole selection method was untrustworthy, not just a few IDs.
- Chose to resolve platform QIDs live via Wikidata's own search service instead of hardcoding IDs from memory, after verifying that hardcoded IDs I initially considered were themselves wrong (pointed to unrelated entities).
- Left `infra/compose.yaml`/`apps/api/Dockerfile` unmodified even though they make the plan's literal Docker-based verify command unrunnable — that's out of this plan's `files_modified` scope; documented as a deviation instead of silently expanding scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fabricated QID list produced non-video-game candidates**
- **Found during:** Task 1, first execution attempt
- **Issue:** The `scripts/acquire_catalogue.py` already present in the repo (from an earlier, non-GSD-tracked commit) used a hand-typed `_CURATED_QIDS` VALUES list. Several QIDs resolved to non-games: a French commune (Q4945), the organ "spleen" (Q9371), the Yom Kippur War (Q49100), among others. Validation failed on era/platform coverage as a symptom, but the root defect was that the "curated" list was never actually verified against real game entities.
- **Fix:** Replaced the static list with a `?game wdt:P31 wd:Q7889` class filter plus targeted era (pre-1990, 2020s) and platform (Xbox, Sega) sub-queries, merged with insertion-order priority so coverage-critical results survive the TARGET_COUNT truncation.
- **Files modified:** `scripts/acquire_catalogue.py`
- **Verification:** Live run produced 150 games covering all 5 required eras and all 5 required platform families; `--validate-only` passes.
- **Committed in:** `a2509e0`

**2. [Rule 1 - Bug] Cover-image titles not URL-decoded before Commons lookup**
- **Found during:** Task 1, second execution attempt (after fixing the QID list)
- **Issue:** `_image_title()` built Commons file titles from the raw URL path without decoding percent-escapes, so e.g. `Assassin%27s_Creed` never matched the real title `Assassin's Creed`. Every one of the first run's 13 candidate images silently fell back to placeholder with empty licence/author fields — not because licensing was actually missing, but because every lookup failed to match a real Commons page.
- **Fix:** Added `urllib.parse.unquote()` before replacing underscores with spaces.
- **Files modified:** `scripts/acquire_catalogue.py`
- **Verification:** Re-run resolved real licence/author metadata for 17 of 19 candidates (up from 0 of 13).
- **Committed in:** `a2509e0`

**3. [Rule 3 - Blocking, documented not fixed] Plan's Docker-based verify command cannot run against current infra**
- **Found during:** Task 1 verification
- **Issue:** The plan's `<verify>` specifies `docker compose -f infra/compose.yaml run --rm api python -m json.tool data/manifests/catalogue.json`. The `api` service in `infra/compose.yaml` has no `volumes:` bind mount, and `apps/api/Dockerfile` only `COPY`s `apps/api/` into the image — `data/` is never visible inside the container, live-mounted or baked in.
- **Fix:** Not fixed — `infra/compose.yaml`/`apps/api/Dockerfile` are outside this plan's `files_modified` scope (Rule 3's scope boundary: do not auto-fix pre-existing issues unrelated to the current task). Substituted an equivalent local validation (`python -m json.tool` directly, plus the script's own `--validate-only` structural check) and documented the gap in `catalogue-freeze.md` for whichever future plan owns the compose/Dockerfile infra.
- **Files modified:** None (documentation only, in `catalogue-freeze.md`)
- **Verification:** `python -m json.tool` on all three JSON files passes; `--validate-only` passes.
- **Committed in:** `8ef6074`

---

**Total deviations:** 3 (2 auto-fixed bugs, 1 documented-not-fixed infra gap). **Impact:** Both bug fixes were necessary for the candidate corpus to be trustworthy at all — without them, the corpus would have contained non-games and every cover would have wrongly defaulted to placeholder. The infra gap is pre-existing and out of scope; flagged rather than silently expanded into.

## Issues Encountered

- The public Wikidata Query Service intermittently timed out (504) on the broader sub-queries under load; resolved with a bounded retry-with-backoff (3 attempts, 5s/20s) rather than failing the whole acquisition on a transient condition.
- An initial attempt to hardcode "well-known" Xbox/Sega platform QIDs from memory was itself wrong when verified live (resolved to a tennis player, a lizard species, etc.) — abandoned in favor of the dynamic `wikibase:mwapi` search + EXISTS verification approach now in the script. This reinforced the same lesson as deviation #1: never trust an unverified Wikidata QID.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-06 (catalogue import/search API) can proceed: the frozen, checksummed snapshot and manifests are the only inputs it should read.
- 17 real cover images are available for import; the remaining catalogue entries and the 2 unresolved-metadata assets use the first-party placeholder.
- No blockers. The Docker-verify infra gap (deviation #3) should be addressed whenever a plan next touches `infra/compose.yaml`/`apps/api/Dockerfile` — it will otherwise resurface for any future plan whose `<verify>` assumes `data/` or other host-created files are visible inside the `api` container.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
