---
phase: 01-three-day-public-demo-slice
plan: 06
subsystem: catalogue-api
tags: [django, postgresql, pg_trgm, drf, search]

requires:
  - phase: 01-03
    provides: [GameWork/GameRelease scaffold, Django migrations baseline]
  - phase: 01-05
    provides: [APPROVED catalogue-freeze.md, checksummed data/raw + data/manifests]

provides:
  - Full catalogue hierarchy models (Platform, Edition, GameAlias, RelatedContent, SourceRecord, AssetAttribution)
  - Fail-closed, idempotent, concurrency-safe import_catalogue command
  - GET /api/catalogue/games/ (list+tolerant search, paginated) and /api/catalogue/games/<slug>/ (detail)
  - Local dev-parity Docker bind mounts (api/web/data/docs) -- unblocks every future plan's `docker compose run` verify commands

affects: [01-07, 01-08, 01-09, 01-10, library, ui]

actuals:
  tokens: 34000
  tasks: 2
  commits: 2

tech-stack:
  added: [django.contrib.postgres (pg_trgm/GinIndex)]
  patterns:
    - "Tolerant search tiering: exact -> prefix -> TrigramSimilarity, each tier excluding IDs already matched by an earlier tier, so ordering is deterministic and stable across repeated calls."
    - "Fail-closed management command: refuses to touch PostgreSQL unless an external precondition (freeze APPROVED + checksum match) holds, verified before any write."
    - "Advisory-lock-guarded single transaction for import concurrency safety, instead of per-row locking."

key-files:
  created:
    - apps/api/catalogue/management/commands/import_catalogue.py
    - apps/api/catalogue/normalization.py
    - apps/api/catalogue/search.py
    - apps/api/catalogue/serializers.py
    - apps/api/catalogue/views.py
    - apps/api/catalogue/urls.py
    - apps/api/catalogue/migrations/0002_catalogue_hierarchy.py
    - apps/api/catalogue/tests/test_import.py
    - apps/api/catalogue/tests/test_search.py
    - apps/api/catalogue/tests/test_detail.py
  modified:
    - apps/api/catalogue/models.py
    - apps/api/config/settings.py
    - apps/api/config/urls.py
    - apps/api/pytest.ini
    - infra/compose.yaml

key-decisions:
  - "Added local-development-only Docker bind mounts (apps/api, apps/web, data, docs) to infra/compose.yaml. Without them every `docker compose run` was silently testing whatever code existed at the last image build, not the current working tree -- this would have blocked every remaining plan's verification, not just this one's. Does not affect the deployed image (Render builds fresh from the same Dockerfiles, no compose.yaml involved)."
  - "Fixed apps/api/pytest.ini to declare DJANGO_SETTINGS_MODULE directly -- the only copy of that setting lived in root pyproject.toml, which pytest.ini always shadows when both exist, and which never even ships into the built image. Any Django-DB test would have failed to configure Django at all."
  - "One GameRelease per (work, platform) pair, all sharing the corpus's single aggregate release_date -- the Wikidata acquisition doesn't carry per-platform release dates, so per-platform precision isn't available in Phase 1's data. Documented as a scope limitation, not silently over-claimed."
  - "RelatedContent (DLC linkage) exists in the schema and is fully constraint-tested, but the current import has no DLC source data to populate it with -- the acquisition's SPARQL query doesn't fetch a 'is DLC of' property. Left genuinely empty rather than fabricated."

requirements-completed: [CAT-01, CAT-03, CAT-04, CAT-06]

coverage:
  - id: D1
    description: "User can search video games by title, tolerating case, accents, and small typos, via exact -> prefix -> trigram-similarity tiers."
    requirement: CAT-01
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_search.py (7 tests: exact/prefix/accent/typo/pagination/dlc-exclusion/determinism)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each game has a detail page showing available data and its provenance (source, licence, retrieval date, checksum)."
    requirement: CAT-03
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_detail.py::test_detail_includes_hierarchy_and_provenance"
        status: pass
    human_judgment: false
  - id: D3
    description: "Canonical identifiers are internal immutable UUIDs; the Wikidata QID is retained only on SourceRecord, never as the primary key."
    requirement: CAT-04
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_import.py::test_import_creates_expected_hierarchy"
        status: pass
    human_judgment: false
  - id: D4
    description: "Catalogue remains usable with zero external network calls at request time (list/search/detail all served from local PostgreSQL only)."
    requirement: CAT-06
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_search.py::test_list_endpoint_no_external_network_call"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 06: Catalogue Import and API Summary

**Fail-closed idempotent import of the frozen 150-game corpus into a full PostgreSQL hierarchy (Platform/Edition/Alias/SourceRecord/AssetAttribution), served through a local-only tolerant-search list endpoint and a provenance-carrying detail endpoint.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-04T16:39:00Z
- **Completed:** 2026-09-04T16:56:08Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments

- Extended the catalogue schema with the full D-09 identity hierarchy (Platform, Edition, GameAlias, RelatedContent, SourceRecord, AssetAttribution) plus a `pg_trgm` GIN index for tolerant search.
- Built `import_catalogue`: refuses to run unless `catalogue-freeze.md` is APPROVED and the snapshot checksum matches; runs the entire import inside one transaction guarded by a PostgreSQL advisory lock so reruns and concurrent invocations never duplicate rows. Verified against the real frozen corpus, not just test fixtures: 150 games, 111 platforms, 742 releases, 239 aliases, 19 assets (17 approved) -- confirmed idempotent on a second real run.
- Implemented tolerant search (exact -> prefix -> trigram similarity), DLC/expansion exclusion from results, and deterministic pagination at 24/page.
- Wired `GET /api/catalogue/games/` and `GET /api/catalogue/games/<slug>/` with allowlisted DTOs, always-visible provenance, and DLC rendered as identity-only non-actionable child content.
- Fixed two infrastructure defects that would have silently blocked every remaining plan's Docker-based verification: missing bind mounts (`docker compose run` was testing stale, pre-build code) and a shadowed/dead `DJANGO_SETTINGS_MODULE` (pytest.ini vs. pyproject.toml).

## Task Commits

1. **Task 1: Crear jerarquía e importar atómicamente** - `88601c0` (feat)
2. **Task 2: Cablear listado, búsqueda y detalle** - `020941b` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `apps/api/catalogue/models.py` - Platform, Edition, GameAlias, RelatedContent, SourceRecord, AssetAttribution; platform FK on GameRelease.
- `apps/api/catalogue/migrations/0002_catalogue_hierarchy.py` - pg_trgm extension, new tables, GIN trigram index.
- `apps/api/catalogue/management/commands/import_catalogue.py` - Fail-closed, idempotent, advisory-lock-guarded import.
- `apps/api/catalogue/normalization.py` - Shared `normalize_title()` for import and search.
- `apps/api/catalogue/search.py` - Tiered tolerant search.
- `apps/api/catalogue/serializers.py` - GameCard/GameDetail/Provenance/RelatedContent DTOs.
- `apps/api/catalogue/views.py`, `apps/api/catalogue/urls.py`, `apps/api/config/urls.py` - List/search/detail endpoints.
- `infra/compose.yaml` - Dev-only bind mounts for api/web/data/docs.
- `apps/api/pytest.ini` - `DJANGO_SETTINGS_MODULE`, broadened `testpaths`.
- `apps/api/catalogue/tests/{test_import,test_search,test_detail}.py` - 20 tests total.

## Decisions Made

See `key-decisions` in frontmatter: bind mounts, pytest.ini fix, one-release-per-platform simplification, RelatedContent left empty (no source data yet, not fabricated).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `docker compose run` silently tested stale code**
- **Found during:** Task 1, first `makemigrations` attempt
- **Issue:** `infra/compose.yaml`'s `api`/`web` services had no bind mount and the Dockerfiles only `COPY` source at build time -- `makemigrations` initially reported `GameWork`/`GameRelease` as brand-new models, because the running container was still on the image built during Plan 01-02/01-03, before any of this plan's model changes existed.
- **Fix:** Added dev-only bind mounts (`../apps/api:/workspace/apps/api`, `../data:/workspace/data:ro`, `../docs:/workspace/docs:ro` for `api`; `../apps/web:/workspace/apps/web` plus anonymous volumes for `node_modules`/`.next` for `web`). Rebuilt the image once; subsequent runs reflect live edits without rebuilding.
- **Files modified:** `infra/compose.yaml`
- **Verification:** Re-ran `makemigrations`; correctly detected an incremental migration against the real current models.
- **Committed in:** `88601c0`

**2. [Rule 3 - Blocking] `DJANGO_SETTINGS_MODULE` never actually configured inside the test container**
- **Found during:** Task 1, before writing the first Django-DB test
- **Issue:** `DJANGO_SETTINGS_MODULE` was declared only in root `pyproject.toml`'s `[tool.pytest.ini_options]`. `apps/api/pytest.ini` exists and always wins over `pyproject.toml` when both are present, and the Dockerfile's `runner` stage never even copies root `pyproject.toml` into the image -- so the setting was dead in every real Docker test run, masked only because Plan 01-02's tests never touched the Django ORM.
- **Fix:** Added `DJANGO_SETTINGS_MODULE = config.settings` directly to `apps/api/pytest.ini`; also broadened `testpaths` from `tests` to `.` so per-app `catalogue/tests/`, and future `library/tests/`/`accounts/tests/`, are discovered by a bare `pytest` run.
- **Files modified:** `apps/api/pytest.ini`
- **Verification:** All Django-DB tests now run without a settings-configuration error.
- **Committed in:** `88601c0`

**3. [Rule 1 - Bug] `update_or_create` cannot create through a reverse-FK filter**
- **Found during:** Task 1, first test run of the import command
- **Issue:** Initial implementation called `GameWork.objects.update_or_create(source_records__source=..., source_records__source_id=..., defaults={...})` -- Django cannot construct a new `GameWork` from filter kwargs that traverse a reverse relation.
- **Fix:** Resolve the existing `SourceRecord` by `(source, source_id)` first (if any), update its linked `GameWork` directly; otherwise create a fresh `GameWork`.
- **Files modified:** `apps/api/catalogue/management/commands/import_catalogue.py`
- **Verification:** `test_import_is_idempotent` passes; real second run confirmed zero duplicate rows.
- **Committed in:** `88601c0`

**4. [Rule 2 - Missing Critical] AssetAttribution model lacked the actual image file URL**
- **Found during:** Task 1, writing the import command's asset-linking step
- **Issue:** The model as first drafted stored `source_url` (the Commons *page*) but not `file_url` (the raw raster image location) -- without it, a cover could never actually be rendered even after being approved.
- **Fix:** Added `file_url` field to `AssetAttribution` and regenerated the migration before it was committed (no extra migration needed).
- **Files modified:** `apps/api/catalogue/models.py`, `apps/api/catalogue/migrations/0002_catalogue_hierarchy.py`
- **Verification:** `test_cover_uses_approved_asset_with_attribution` asserts a real `file_url` is present.
- **Committed in:** `88601c0`

---

**Total deviations:** 4 (3 blocking infra/logic fixes, 1 missing-critical field). **Impact:** All four were necessary for the plan's own acceptance criteria (idempotent, fail-closed, correctly-linked covers) to actually hold, and two of them (bind mounts, pytest settings) would otherwise have silently broken every subsequent plan's Docker-based verification for the rest of the phase.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-15 (demo account bootstrap) can proceed independently in the same wave.
- Plan 01-07 (library/inventory/popularity) can build directly on `GameWork`/`GameRelease` once it starts.
- Plans 01-08/01-09 (UI) can consume `/api/catalogue/games/` and `/api/catalogue/games/<slug>/` as-is.
- The Docker dev-parity fix (bind mounts, pytest.ini) removes what would otherwise have been a recurring blocker for every remaining plan in this phase.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
