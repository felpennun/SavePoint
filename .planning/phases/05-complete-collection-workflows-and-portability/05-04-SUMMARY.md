---
phase: 05-complete-collection-workflows-and-portability
plan: 04
subsystem: api
tags: [django, drf, postgresql, csv, portability, documentation, threat-model-reconciliation]

requires:
  - phase: 05-complete-collection-workflows-and-portability
    provides: "05-01/02/03: AccountProfile/FavoriteSlot, GameComment/CustomList/CustomListItem, OwnedCopy purchase/conservation metadata"
provides:
  - "GET /api/library/export/collection.csv (PORT-01/PORT-04): owner-scoped, deterministic, UTF-8, schema_version=1 CSV covering favorites/collection/copies/comments/list items"
  - "apps/api/library/export.py: neutralize_spreadsheet_formula (idempotent OWASP CSV-injection mitigation), build_export_rows (total order with internal-UUID tie-breaks never written to the CSV)"
  - "05-PORTABILITY-RECONCILIATION.md: decision matrix reconciling PROF-01/PORT-01..04 against D-01/D-08/D-09; confirms CustomList is the primary new aggregate, not an alias"
  - "docs/verification/phase-05-signoff.md: Spanish backend evidence signoff for the whole phase (commands, migrations, requirement matrix, STRIDE mitigations, explicit Playwright/axe handoff)"
affects: [phase-06-public-discovery, phase-07-research-panel-and-hardening, apps/web collection/export UI]

actuals:
  tokens: 12800
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Export-as-read-contract: a dedicated export.py builds rows from explicitly named fields (never values()/__dict__/the public-profile projection), with a fixed CSV_FIELDNAMES column order and a schema_version cell for forward compatibility"
    - "Total order with non-exported tie-breaks: every export section sorts by the columns it actually writes (slot/work_slug/list_name+position), falling back to internal, never-written UUIDs (GameWork/OwnedCopy/CustomList/CustomListItem) so two exports of unchanged data are byte-identical regardless of queryset iteration order"
    - "Idempotent formula-injection neutralization: neutralize_spreadsheet_formula checks for an existing tab prefix before adding one, so applying it twice (or replaying an export) never accumulates tabs"

key-files:
  created:
    - apps/api/library/export.py
    - apps/api/library/tests/test_export.py
    - .planning/phases/05-complete-collection-workflows-and-portability/05-PORTABILITY-RECONCILIATION.md
    - docs/verification/phase-05-signoff.md
  modified:
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - .planning/phases/05-complete-collection-workflows-and-portability/05-VALIDATION.md
    - ideas-vault/Fases/Fase 5 - Coleccion y portabilidad.md
    - ideas-vault/Conceptos/Importacion y exportacion.md
    - ideas-vault/Conceptos/Listas personalizadas.md

key-decisions:
  - "The CSV is a single unified schema (record_type discriminator: favorite/collection/copy/comment/list_item) rather than multiple files or per-entity CSVs, matching 05-RESEARCH.md's Pattern 5 recommendation (Assumption A5) -- one deterministic download, one contract to test."
  - "Export section order is fixed (favorites, collection, copies, comments, list items); within each section, rows sort by the columns actually exported, with internal stable UUIDs as the final tie-break that is never written to the CSV -- verified with two deliberately-tied fixtures (two copies of the same work with identical metadata; two differently-named... actually identically-named lists holding the same work at the same position) that still produce byte-identical repeated exports."
  - "The export endpoint's filename is fixed (savepoint-collection-export.csv), never derived from the caller's alias or any other user-controlled text, closing off any header-injection surface via Content-Disposition."
  - "REQUIREMENTS.md and ROADMAP.md already carried the reconciled PROF-01/PORT-01..04 wording (CSV-only PORT-01, PORT-02/03 explicitly assigned to Phase 7) from prior phase-level roadmap work -- Task 2 verified this by inspection rather than re-editing already-correct canonical sources, and instead produced the new 05-PORTABILITY-RECONCILIATION.md decision matrix plus vault updates that were genuinely stale (still describing the original wider JSON/import scope)."

patterns-established:
  - "Any future data-export surface in this codebase should follow export.py's shape: a pure row-builder function, a fixed versioned column contract, owner-scoped queries only, and a cell-level neutralization pass applied uniformly (never a column allowlisted out of the formula check just because it 'looks numeric')."

requirements-completed: [PORT-01, PORT-04]

coverage:
  - id: D1
    description: "An authenticated user downloads a UTF-8 CSV with a fixed, versioned header covering their own authorized favorites/collection/copies/comments/list-items; a second user's data never appears."
    requirement: "PORT-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_export_contains_only_the_owners_authorized_data"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_anonymous_export_request_is_rejected"
        status: pass
    human_judgment: false
  - id: D2
    description: "The export never includes secrets, session data, passwords, or unnecessary internal IDs (work/copy/list/item UUIDs, idempotency keys) -- only human-facing slugs/titles/names identify a row."
    requirement: "PORT-01, PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_export_never_includes_secrets_sessions_or_unnecessary_internal_ids"
        status: pass
    human_judgment: false
  - id: D3
    description: "Two unchanged exports produce byte-identical content, including when rows tie on every exported column (two copies of the same work with identical metadata; two identically-named lists holding the same work at the same position) -- the tie is resolved by an internal, never-exported UUID."
    requirement: "PORT-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_repeated_export_without_changes_is_byte_identical"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_tied_copies_of_the_same_work_are_ordered_stably_and_repeat_identically"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_tied_list_items_across_different_lists_are_ordered_stably_and_repeat_identically"
        status: pass
    human_judgment: false
  - id: D4
    description: "Values starting with =, +, -, or @ are neutralized with a tab prefix before serialization, idempotently (applying the function twice never adds a second tab), across store/comment/list-name cells."
    requirement: "PORT-04"
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_export.py::test_neutralize_spreadsheet_formula_prefixes_hostile_values"
        status: pass
      - kind: unit
        ref: "apps/api/library/tests/test_export.py::test_neutralize_spreadsheet_formula_is_idempotent"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_export.py::test_hostile_store_and_comment_values_are_neutralized_in_the_export"
        status: pass
    human_judgment: false
  - id: D5
    description: "The migration chain is unchanged/still valid (no pending migrations), and the full apps/api backend suite passes after adding the export endpoint -- no regression anywhere, including catalogue/recommendations."
    verification:
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput (No migrations to apply.)"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run (No changes detected)"
        status: pass
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api -q (619/619)"
        status: pass
    human_judgment: false
  - id: D6
    description: "PROF-01/PORT-01..04 are reconciled against D-01/D-08/D-09 in a dedicated decision matrix; PORT-02/PORT-03 are confirmed pending and assigned to Phase 7 with zero import/parser endpoint or feature test anywhere in apps/api/library; CustomList is documented as the primary new aggregate, not an alias."
    requirement: "PORT-01, PORT-02, PORT-03"
    verification:
      - kind: unit
        ref: "grep-based equivalent of the plan's PowerShell verify: file/token/regex checks against 05-PORTABILITY-RECONCILIATION.md and ideas-vault notes, plus a recursive filename/content scan of apps/api/library for import|parser -- zero matches"
        status: pass
    human_judgment: false
  - id: D7
    description: "The phase's backend evidence (commands, migrations, requirement matrix, STRIDE mitigations for this plan) is signed off in Spanish, with the Playwright/axe browser verification explicitly assigned to the web session and not fabricated as backend-executed evidence."
    verification:
      - kind: unit
        ref: "docs/verification/phase-05-signoff.md (file existence + content review)"
        status: pass
    human_judgment: true
    rationale: "The document's completeness and tone are a documentation-quality judgment call, and its central claim (browser evidence pending) is itself a human-relevant fact -- a human should confirm the signoff accurately represents what is and isn't verified before treating the phase as closed."
  - id: D8
    description: "The Playwright e2e/collection-workflows.spec.ts journey and its accessibility matrix (registration/login, profile, comments, lists, copy form, CSV download) are the web session's responsibility per this plan's <handoff> and have not been run from this backend-only plan."
    verification: []
    human_judgment: true
    rationale: "This plan's <verification>/<handoff> explicitly assign the Playwright/axe execution to the other (web) session; this backend-only plan cannot run or fake that browser evidence, and the phase-level sign-off is not complete until that evidence is attached."

duration: 70min
completed: 2026-09-13
status: complete
---

# Phase 5 Plan 4: CSV Export, Portability Reconciliation, and Phase Signoff Summary

**Owner-scoped, deterministic, formula-injection-safe CSV export (PORT-01/PORT-04) plus a documented reconciliation confirming PORT-02/PORT-03 stay pending for Phase 7 and a Spanish backend evidence signoff for the whole phase.**

## Performance
- **Duration:** ~70min
- **Started:** 2026-09-12T22:00:00Z (approx, worktree spawn)
- **Completed:** 2026-09-13
- **Tasks:** 3/3 completed
- **Files modified:** 10 (4 created, 6 modified)

## Accomplishments
- Built `apps/api/library/export.py`: a pure, owner-scoped CSV row-builder with a fixed `schema_version=1` column contract (`favorite`/`collection`/`copy`/`comment`/`list_item` record types), a total sort order whose tie-breaks are internal UUIDs never written to the CSV, and an idempotent OWASP-style formula-injection neutralization applied uniformly to every cell.
- Added `GET /api/library/export/collection.csv` (`IsAuthenticated`, fixed non-user-derived filename) and verified it end-to-end with 33 new tests covering privacy/isolation, byte-for-byte determinism (including two genuinely tied-row scenarios), UTF-8 content, and formula neutralization -- following a real RED (confirmed `ImportError` with the implementation temporarily removed) before GREEN.
- Ran the full backend suite after the change: `apps/api/accounts/tests apps/api/library/tests` (247 passed) and the complete `apps/api` suite (619 passed), plus `migrate --noinput`/`makemigrations --check --dry-run` clean.
- Wrote `05-PORTABILITY-RECONCILIATION.md`: a decision matrix reconciling PROF-01/PORT-01..04 against D-01/D-08/D-09, confirming `CustomList` is a new primary aggregate (not an alias), and verifying (by grep-equivalent scan) that no import/parser endpoint, filename, or feature test exists anywhere under `apps/api/library`.
- Updated three stale `ideas-vault` notes (still describing the original wider JSON/import scope) to reflect the actual CSV-only closure and the `CustomList` naming.
- Wrote `docs/verification/phase-05-signoff.md` in Spanish: commands executed, migrations, the full requirement matrix, this plan's STRIDE mitigations, the new endpoint's UI contract, explicit limitations, and the Playwright/axe handoff assigned to the web session (not fabricated as backend-executed).

## Task Commits
1. **Task 1 RED: failing test for owner-scoped CSV export contract** - `a94e890` (test)
2. **Task 1 GREEN: owner-scoped CSV export endpoint** - `fc56ef0` (feat)
3. **Task 2: reconcile PORT-01/02/03 scope and vault notes** - `9ec5a3e` (docs)
4. **Task 3: Phase 5 backend evidence signoff and Playwright/axe handoff** - `7c44258` (docs)

**Plan metadata:** commit pending (this SUMMARY, worktree mode)

## TDD Gate Compliance

Task 1 (`type="tracer" tdd="true"`) followed a genuine RED-GREEN cycle, verified rather than assumed: with `export.py`/the `views.py`/`urls.py` changes stashed out of the working tree, `pytest apps/api/library/tests/test_export.py` failed at collection with `ModuleNotFoundError: No module named 'library.export'` (confirmed RED), committed as `test(05-04)` (`a94e890`). The implementation was then restored from the stash, the same 33 tests were re-run and passed, and committed as `feat(05-04)` (`fc56ef0`) -- `git log --oneline --grep` confirms `test(05-04)` precedes `feat(05-04)`. Tasks 2 and 3 (`type="auto"`, no `tdd` attribute) correctly have no preceding `test` commit, since neither adds production code -- both are documentation/reconciliation work.

## Files Created/Modified
- `apps/api/library/export.py` (new) - `CSV_SCHEMA_VERSION`, `CSV_FIELDNAMES`, `neutralize_spreadsheet_formula`, `build_export_rows`, `render_collection_csv`
- `apps/api/library/views.py` - `ExportCollectionView` (GET, `IsAuthenticated`, `HttpResponse` with `text/csv` content type and fixed `Content-Disposition`)
- `apps/api/library/urls.py` - `export/collection.csv` route
- `apps/api/library/tests/test_export.py` (new, 324 lines) - privacy/isolation, secrets/internal-ID absence, anonymous-rejection, byte-identical-repeat, formula-neutralization (parametrized + idempotency + end-to-end), and two deliberately-tied-row determinism tests
- `.planning/phases/05-complete-collection-workflows-and-portability/05-PORTABILITY-RECONCILIATION.md` (new) - decision matrix (PROF-01/PORT-01..04), `CustomList` primary-aggregate decision, verified absence of import/parser surface in `apps/api/library`
- `.planning/phases/05-complete-collection-workflows-and-portability/05-VALIDATION.md` - requirement-status table, closure checklist, links to the signoff document
- `docs/verification/phase-05-signoff.md` (new, Spanish) - phase-wide backend evidence signoff, requirement matrix, STRIDE mitigations for this plan, UI contract for the new endpoint, explicit limitations, Playwright/axe handoff
- `ideas-vault/Fases/Fase 5 - Coleccion y portabilidad.md`, `ideas-vault/Conceptos/Importacion y exportacion.md`, `ideas-vault/Conceptos/Listas personalizadas.md` - updated from the original wider (JSON/import) scope to the actual CSV-only closure, linked to the reconciliation document

## Decisions Made
See `key-decisions` in frontmatter. The most consequential: the CSV uses one unified `record_type`-discriminated schema rather than multiple files; export ordering is a strict total order (exported columns first, internal never-exported UUIDs as the final tie-break) verified against two deliberately-constructed tie scenarios; and `REQUIREMENTS.md`/`ROADMAP.md` were found already reconciled from prior phase-level roadmap work, so Task 2's new content went into `05-PORTABILITY-RECONCILIATION.md` and the genuinely-stale vault notes instead of re-editing already-correct canonical sources.

## Deviations from Plan

**1. [Process] REQUIREMENTS.md/ROADMAP.md required no further edit**
- **Found during:** Task 2
- **Issue:** The plan's `<files>` list for Task 2 includes `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md`. On inspection, both already carried the fully reconciled wording (PORT-01 CSV-only with JSON explicitly excluded from the Phase 5 closure; PORT-02/PORT-03 explicitly `Pending`/assigned to `Phase 7` in the traceability table; PROF-01 already worded as "biography and optional HTTPS avatar while the login alias remains immutable") -- apparently from an earlier phase-level roadmap revision, not from this plan.
- **Fix:** Verified the existing wording against the plan's own decision matrix requirements (matched exactly) and made no edit to either file, to avoid an unnecessary/risky diff to already-correct canonical sources. Documented the finding explicitly in the Task 2 commit message and in `05-PORTABILITY-RECONCILIATION.md`'s "Cierre" section.
- **Files affected:** none (no edit made)
- **Verification:** Read both files' Phase 5/PORT-* sections in full before deciding; cross-checked every clause against the plan's required decision matrix content.
- **Commit:** `9ec5a3e` (commit message documents the finding)

**Total deviations:** 1 process deviation (no-op where the plan anticipated an edit), 0 code bugs. **Impact:** none -- the canonical sources already stated exactly what the plan required; forcing a cosmetic edit would have added risk without changing meaning.

## Issues Encountered

One test-authoring bug caught and fixed before any commit (not a plan deviation): the first version of `test_export_contains_only_the_owners_authorized_data` created an `OwnedCopy` with `currency="eur"` (lowercase), which raised `IntegrityError` against the pre-existing `library_copy_currency_format_valid` `CheckConstraint` (uppercase-only, from Plan 05-03). Fixed by using `currency="EUR"` directly, since the test exercises the export contract, not currency normalization (already covered by 05-03's own tests).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

Ready for hand-off: `GET /api/library/export/collection.csv` is stable, tested against real PostgreSQL, and additive to 05-01/05-02/05-03's contract (all prior endpoints unchanged). The web session can wire a download action against this single URL with no additional backend work.

Phase 5 backend evidence is complete across all four plans (619/619 full `apps/api` suite). The Playwright `e2e/collection-workflows.spec.ts` journey and its accessibility matrix -- explicitly the web session's responsibility per this plan's `<handoff>` -- remain the one open item before the phase's full (backend + browser) verification can be considered closed (see coverage D8). PORT-02/PORT-03 remain intentionally open, assigned to Phase 7, per `05-PORTABILITY-RECONCILIATION.md`.

## Self-Check: PASSED

All 4 created files verified present on disk (`apps/api/library/export.py`, `apps/api/library/tests/test_export.py`, `05-PORTABILITY-RECONCILIATION.md`, `docs/verification/phase-05-signoff.md`); all 4 task commit hashes (`a94e890`, `fc56ef0`, `9ec5a3e`, `7c44258`) verified present in `git log`.

---
*Phase: 05-complete-collection-workflows-and-portability*
*Completed: 2026-09-13*
