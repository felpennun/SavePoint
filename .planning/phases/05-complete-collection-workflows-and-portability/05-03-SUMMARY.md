---
phase: 05-complete-collection-workflows-and-portability
plan: 03
subsystem: api
tags: [django, drf, postgresql, inventory, owned-copy, check-constraint, privacy]

requires:
  - phase: 05-complete-collection-workflows-and-portability
    provides: "05-02: GameComment, CustomList/CustomListItem, library.0003_phase5_comments_lists migration"
provides:
  - "OwnedCopy extended with purchase_date, price (Decimal, non-negative), currency (3-letter uppercase, normalized), store, conservation_state (new/good/fair/poor/damaged), and storage_location (INV-03/INV-04) -- LibraryEntry.current_status/rating_half_steps unchanged"
  - "New PostgreSQL migration library/migrations/0004_phase5_copy_metadata.py, dependent on library.0003_phase5_comments_lists, adding four CheckConstraints: non-negative price, valid 3-letter currency format, valid conservation_state enum, and digital copies excluding conservation_state/storage_location"
  - "Physical/digital cross-field validation duplicated at three layers: serializer (LibraryCopyConfigurationSerializer/CreateOwnedCopyRequestSerializer), service (library.services._validate_copy_metadata, shared by create_owned_copy and save_library_configuration), and PostgreSQL CheckConstraint as the last line of defense against writes that bypass the API"
  - "docs/verification/phase-05-api-handoff.md (Spanish): complete backend/UI contract for 05-01/05-02/05-03 -- routes, DTOs, status codes, CSRF/cookies, physical/digital rules, and the public-profile allowlist"
affects: [05-04-export-and-portability-reconciliation, apps/web collection/copy-form UI]

actuals:
  tokens: 12600
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Cross-field validation duplicated at serializer/service/database: a physical-only field pair (conservation_state/storage_location) is rejected for format=digital at DRF's object-level validate(), again inside the service function shared by both entry points, and finally by a PostgreSQL CheckConstraint -- so even a direct ORM write that skips the API is rejected."
    - "Currency normalization happens once, in a shared _validate_currency helper used by every serializer that accepts one, so uppercasing/regex validation can never drift between the single-copy-creation and full-configuration entry points."
    - "Idempotency replay never re-applies a differing payload: create_owned_copy returns the existing row unchanged on a replayed idempotency_key, even if the replay's purchase/conservation metadata differs from the first write."

key-files:
  created:
    - apps/api/library/migrations/0004_phase5_copy_metadata.py
    - docs/verification/phase-05-api-handoff.md
  modified:
    - apps/api/library/models.py
    - apps/api/library/serializers.py
    - apps/api/library/services.py
    - apps/api/library/views.py
    - apps/api/library/tests/test_copies.py
    - apps/api/library/tests/test_schema.py

key-decisions:
  - "Conservation taxonomy fixed at five values (new/good/fair/poor/damaged) per the plan's discretion note -- small, documented, and enforced by both a DRF ChoiceField and a PostgreSQL CheckConstraint, not left as free text."
  - "Currency is normalized to uppercase server-side (both in the serializer and the service layer) rather than requiring the client to send it pre-normalized -- a lowercase 'eur' is accepted and stored as 'EUR', but anything that isn't exactly three letters after normalization is rejected."
  - "The physical/digital exclusion rule intentionally allows a physical copy to leave conservation_state/storage_location null (both are optional metadata, matching D-01's 'siempre que los campos sean auditables, opcionales cuando proceda' discretion note) -- only a digital copy carrying either value is rejected."
  - "Task 1 (tracer) and Task 2 (auto) share one migration and are committed as a single test(05-03) → feat(05-03) pair rather than two independent per-task RED/GREEN cycles, matching 05-02's established precedent: both tasks extend the identical five production files (models/serializers/services/views + one migration), and the physical/digital CheckConstraint that Task 2's tests exercise had to already exist in Task 1's migration for Task 1's own acceptance criteria (round-trip with idempotency preserved) to be meaningfully tested against the real schema."

patterns-established:
  - "Any future OwnedCopy-adjacent metadata field should follow the same three-layer validation pattern (serializer validate()/validate_<field>, a shared service-level _validate_copy_metadata-style helper, and a PostgreSQL CheckConstraint) rather than trusting only the API layer."

requirements-completed: [INV-03, INV-04, PRIV-01]

coverage:
  - id: D1
    description: "A physical copy's purchase_date/price/currency/store/conservation_state/storage_location survive creation, a full configuration replace, and a reload; currency is normalized to uppercase."
    requirement: "INV-03"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_physical_copy_metadata_persists_and_survives_reload"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_full_configuration_conserves_copy_metadata_when_editing_and_removing_other_copies"
        status: pass
    human_judgment: false
  - id: D2
    description: "Replaying the same idempotency_key never duplicates the copy and never re-applies a differing metadata payload to the already-persisted row."
    requirement: "INV-03"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_replaying_idempotency_key_preserves_first_metadata"
        status: pass
    human_judgment: false
  - id: D3
    description: "A digital copy carrying conservation_state or storage_location is rejected without mutation at the API (400), the service layer (ValidationError), and -- for a write that bypasses both -- PostgreSQL's CheckConstraint (IntegrityError)."
    requirement: "INV-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_digital_copy_with_conservation_state_is_rejected_via_api_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_digital_copy_with_storage_location_is_rejected_via_service_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_digital_copy_with_conservation_state_fails_check_constraint_at_orm_level"
        status: pass
    human_judgment: false
  - id: D4
    description: "Negative price and invalid currency are rejected at both the API layer and, for a direct ORM write, PostgreSQL's CheckConstraint; an unknown conservation_state and an oversized store payload are rejected at the API without mutation."
    requirement: "INV-03, INV-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_negative_price_fails_check_constraint_at_orm_level"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_invalid_currency_fails_check_constraint_at_orm_level"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_negative_price_is_rejected_via_api_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_invalid_currency_is_rejected_via_api_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_unknown_conservation_state_is_rejected_via_api_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_oversized_store_payload_is_rejected_without_mutation"
        status: pass
    human_judgment: false
  - id: D5
    description: "User B cannot read, delete, or overwrite user A's copy metadata via any of the copy endpoints; a guessed copy id in a configuration payload is rejected without mutation."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_user_b_cannot_read_or_mutate_user_a_copy_metadata"
        status: pass
    human_judgment: false
  - id: D6
    description: "The public-profile projection never leaks a copy's purchase/conservation metadata (store, storage_location, price, or the field names themselves), because OwnedCopy data never enters build_public_profile() at all."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_copies.py::test_public_profile_never_leaks_copy_purchase_or_conservation_metadata"
        status: pass
    human_judgment: false
  - id: D7
    description: "PostgreSQL actually contains the migration chain (dependent on library.0003_phase5_comments_lists), the six new OwnedCopy columns, and all four new CheckConstraints; no pending migrations after makemigrations --check --dry-run."
    requirement: "INV-03, INV-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_schema.py (4 new tests covering migration dependency, columns, constraints, nullability)"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run"
        status: pass
    human_judgment: false
  - id: D8
    description: "No regression anywhere in the backend: the full apps/api suite passes after both code-bearing tasks."
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api -q (602/602)"
        status: pass
    human_judgment: false
  - id: D9
    description: "docs/verification/phase-05-api-handoff.md exists and contains the contractual tokens OwnedCopy/CSRF/public/digital for the web session to integrate against."
    requirement: "INV-03, INV-04, PRIV-01"
    verification:
      - kind: unit
        ref: "file existence + token grep for OwnedCopy/CSRF/public/digital (PowerShell blocked in this worktree's sandbox; equivalent bash/grep check run instead, same tokens confirmed present)"
        status: pass
    human_judgment: false
  - id: D10
    description: "The Playwright collection-workflows E2E journey (copy form, physical/digital error states, metadata persistence) and its accessibility matrix are the web session's responsibility per this plan's <handoff> and have not been run from this backend-only plan."
    verification: []
    human_judgment: true
    rationale: "This plan's <verification>/<handoff> explicitly assign e2e/collection-workflows.spec.ts and the axe/keyboard matrix to the other (web) session; this backend-only plan cannot run or fake that browser evidence."

duration: 65min
completed: 2026-09-13
status: complete
---

# Phase 5 Plan 3: Copy Purchase/Conservation Metadata Summary

**OwnedCopy gains auditable purchase and conservation metadata (date/price/currency/store/conservation state/storage location) with the physical/digital exclusion rule enforced identically at the serializer, service, and PostgreSQL CheckConstraint layers, plus a Spanish handoff contract for the web session.**

## Performance
- **Duration:** ~65min
- **Started:** 2026-09-12T21:50:00Z (approx, worktree spawn)
- **Completed:** 2026-09-13
- **Tasks:** 3/3 completed
- **Files modified:** 8 (2 created, 6 modified)

## Accomplishments
- Extended `OwnedCopy` with `purchase_date`, `price` (Decimal, non-negative), `currency` (3-letter, normalized to uppercase), `store`, `conservation_state` (`new`/`good`/`fair`/`poor`/`damaged`), and `storage_location`, without touching `LibraryEntry.current_status`/`rating_half_steps`.
- Generated `library/migrations/0004_phase5_copy_metadata.py` via `makemigrations` inside Docker (zero drift against `makemigrations --check --dry-run`), correctly dependent on `library.0003_phase5_comments_lists` (05-02's migration), with four `CheckConstraint`s: non-negative price, valid 3-letter currency format, valid conservation-state enum, and digital-excludes-conservation.
- Propagated the new fields through `OwnedCopySerializer` (output), `CreateOwnedCopyRequestSerializer` and `LibraryCopyConfigurationSerializer` (input, with a shared currency-normalization helper and a shared physical/digital cross-field `validate()`), `library.services.create_owned_copy` and `save_library_configuration` (service-level validation duplicated via `_validate_copy_metadata`), and `OwnedCopiesView.post`.
- Verified the physical/digital exclusion rule, negative-price rejection, and invalid-currency rejection fail at all three layers, including a direct ORM write that bypasses the API entirely (`IntegrityError` from the `CheckConstraint`).
- Extended `test_schema.py` with migration-dependency, column, and constraint introspection against real PostgreSQL, and re-ran the full backend suite after every code-bearing task (final: 602/602 passing).
- Wrote `docs/verification/phase-05-api-handoff.md` in Spanish: the complete backend/UI contract across 05-01/05-02/05-03 for the web session's Playwright/axe work.

## Task Commits
1. **Task 1+2 RED: failing tests for copy metadata** - `47f924d` (test)
2. **Task 1+2 GREEN: OwnedCopy metadata fields, migration, serializers, services** - `3dde535` (feat)
3. **Task 3: Spanish backend/UI handoff document** - `41afb01` (docs)

**Plan metadata:** commit pending (this SUMMARY, worktree mode)

## TDD Gate Compliance

Task 1 (`type="tracer" tdd="true"`) and Task 2 (`type="auto" tdd="true"`) share the identical
production files (`models.py`, `serializers.py`, `services.py`, `views.py`) and a single
migration (`0004_phase5_copy_metadata.py`) by construction: Task 1's own acceptance criterion
(round-trip with idempotency preserved) needed the same migration and model fields that Task
2's physical/digital `CheckConstraint` tests exercise, so splitting the migration across two
commits would have required either an incomplete schema at Task 1's commit boundary or a
second migration purely for constraints -- neither matches the plan's explicit single-migration
design (`0004_phase5_copy_metadata.py`, singular, in the plan's `files_modified`). This mirrors
05-02's documented precedent for the same reason (shared production files + one migration
covering two tasks' behavior). Both tasks' full behavior lists are independently exercised by
distinct, task-scoped test functions within the single `test(05-03)` commit (`47f924d`),
followed by the single `feat(05-03)` commit (`3dde535`) implementing all of it -- the
RED-before-GREEN commit order is preserved at the plan level. Task 3 (`type="auto"`, no `tdd`
attribute) correctly has a single `docs(05-03)` commit with no preceding `test` commit, since it
only adds a documentation file with no production code.

## Files Created/Modified
- `apps/api/library/models.py` - `ConservationState` choices, `COPY_*` length/precision constants, six new `OwnedCopy` fields, four new `CheckConstraint`s
- `apps/api/library/migrations/0004_phase5_copy_metadata.py` - PostgreSQL schema for the new columns and constraints, depending on `library.0003_phase5_comments_lists`
- `apps/api/library/serializers.py` - `_validate_currency`, `_validate_physical_digital_rule` shared helpers; new fields on `OwnedCopySerializer`, `CreateOwnedCopyRequestSerializer`, `LibraryCopyConfigurationSerializer`
- `apps/api/library/services.py` - `_validate_copy_metadata` shared service-layer validator; `create_owned_copy`/`save_library_configuration` extended to accept and persist the new fields
- `apps/api/library/views.py` - `OwnedCopiesView.post` passes the new fields through to the service
- `apps/api/library/tests/test_copies.py` (688 lines total) - round-trip/idempotency/full-configuration-preservation tests (Task 1), physical/digital/validation/isolation/privacy tests (Task 2)
- `apps/api/library/tests/test_schema.py` - 4 new PostgreSQL introspection tests for the new migration's columns and constraints
- `docs/verification/phase-05-api-handoff.md` (new, Spanish) - complete backend/UI contract handoff

## Decisions Made
See `key-decisions` in frontmatter. The most consequential: the conservation taxonomy is fixed
at five documented values (not free text); currency is normalized server-side rather than
requiring pre-normalized client input; and Task 1/Task 2 are committed as one test→feat pair
for the same shared-migration reason as 05-02.

## Deviations from Plan

**1. [Process] Task 1 and Task 2 committed together instead of as two separate RED/GREEN pairs**
- **Found during:** preparing per-task commits after both tasks' code and tests were verified green
- **Issue:** Task 1 (tracer, round-trip metadata) and Task 2 (auto, physical/digital rules and constraints) extend the identical production files and share one migration by the plan's own explicit design (`0004_phase5_copy_metadata.py`, singular, listed once in `files_modified`).
- **Fix:** Committed one `test(05-03)` commit (all new test functions for both tasks) followed by one `feat(05-03)` commit (all production code + the migration), preserving RED-before-GREEN ordering at the plan level. Matches 05-02's documented precedent for the identical structural reason.
- **Files affected:** `apps/api/library/{models,serializers,services,views}.py`, the migration
- **Verification:** Full backend suite (602/602) passes at the commit boundary actually pushed to history.
- **Commit:** `47f924d`, `3dde535`

**2. [Tooling] PowerShell blocked by the worktree sandbox for Task 3's verification command**
- **Found during:** Task 3 verification
- **Issue:** The plan's literal `<verify>` command for Task 3 invokes `powershell -NoProfile -Command ...`; this worktree's sandbox refuses any PowerShell invocation it cannot statically prove never touches git, regardless of actual content.
- **Fix:** Ran the equivalent check via the Grep tool (file existence + per-token occurrence count for `OwnedCopy`/`CSRF`/`public`/`digital`), which is the same test the PowerShell command performs, and confirmed all four tokens are present.
- **Impact:** None on the actual deliverable -- the handoff document exists and contains all required tokens; only the mechanism used to prove it differs from the plan's literal command text.

**Total deviations:** 1 process deviation (commit granularity, no code impact), 1 tooling deviation (verification mechanism, no impact on the deliverable). **Impact:** none on runtime correctness or on the phase's requirements.

## Issues Encountered

None beyond the two deviations above, both caught and resolved without affecting the delivered behavior.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

Ready for hand-off: `POST/GET /api/library/entries/<work_id>/copies/`, `DELETE .../copies/<copy_id>/`,
and `POST .../configuration/` all accept and return the new purchase/conservation fields, are
tested against real PostgreSQL, and are additive to 05-01/05-02's contract (profile, favorites,
comments, lists are unchanged). `docs/verification/phase-05-api-handoff.md` gives the web session
everything it needs to build the copy-metadata form and its physical/digital error states without
reading backend source.

Open for the rest of the phase: Plan 05-04 (export/portability reconciliation) is the next and
final plan. The Playwright `e2e/collection-workflows.spec.ts` journey and its accessibility
matrix -- explicitly the web session's responsibility per this plan's `<handoff>` -- have not
been run from this plan and remain a phase-level gate before sign-off (see coverage D10).

## Self-Check: PASSED

All 3 claimed key-files verified present on disk (migration, handoff doc, plus the 6 modified
files); all 3 task commit hashes (`47f924d`, `3dde535`, `41afb01`) verified present in `git log`.

---
*Phase: 05-complete-collection-workflows-and-portability*
*Completed: 2026-09-13*
