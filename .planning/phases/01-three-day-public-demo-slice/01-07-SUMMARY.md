---
phase: 01-three-day-public-demo-slice
plan: 07
subsystem: library-profile-popularity
tags: [django, drf, postgresql, privacy, popularity-baseline]

requires:
  - phase: 01-04
    provides: [LibraryEntry/StatusTransition, session auth]
  - phase: 01-06
    provides: [catalogue hierarchy: Platform, Edition, GameWork]

provides:
  - Exact half-step rating persistence with a DB-level range constraint
  - Idempotent, ownership-validated OwnedCopy creation
  - Allowlisted public profile projection (never model auto-serialization)
  - Deterministic, versioned popularity-v1 baseline

affects: [01-08, 01-09, ui-components-LibraryControls-RecommendationStrip]

actuals:
  tokens: 48000
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Cross-table membership (release belongs to work, edition belongs to release) is validated at the service layer, not a DB CheckConstraint -- Postgres CHECK operates on a single row's own columns only."
    - "select_for_update() cannot protect a not-yet-existing row from a concurrent INSERT; the real safety net for create-or-return-existing is the UNIQUE constraint plus catching IntegrityError as an expected 'lost the race' outcome, not an outer-transaction-poisoning error."
    - "Public projections are hand-built allowlist dicts, never DRF ModelSerializer auto-introspection -- a new private model field then requires an explicit decision to expose it, not an accidental one to hide it."

key-files:
  created:
    - apps/api/library/migrations/0002_rating_copies.py
    - apps/api/library/services.py
    - apps/api/library/serializers.py
    - apps/api/library/popularity.py
    - apps/api/library/tests/test_schema.py
    - apps/api/library/tests/test_rating.py
    - apps/api/library/tests/test_copies.py
    - apps/api/library/tests/test_popularity.py
    - apps/api/accounts/serializers.py
    - apps/api/accounts/tests/test_public_profile.py
  modified:
    - apps/api/library/models.py
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - apps/api/accounts/views.py
    - apps/api/accounts/urls.py
    - infra/compose.yaml

key-decisions:
  - "PROF-02's FLAGGED ASSUMPTION resolved for Phase 1: every account is public by design (small, controlled demo, no privacy toggle). The 'unauthorized vs. nonexistent' indistinguishability requirement is satisfied trivially today (both collapse to the same 404) and the response shape is built so a future privacy toggle wouldn't need a rewrite."
  - "Popularity's 'no partial mixing under concurrency' requirement is satisfied by resolving the entire scoring queryset in one query (list()), relying on PostgreSQL's read-committed isolation to give a single consistent snapshot, rather than building elaborate locking around a read-only aggregate."

requirements-completed: [LIB-02, INV-01, INV-02, INV-05, REC-02]

coverage:
  - id: D1
    description: "Rating accepts every integer 1-10 (half-star steps) or null; 0, 11, floats, and out-of-range values are rejected without rounding, enforced at both the service layer and a PostgreSQL CheckConstraint."
    requirement: LIB-02
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_rating.py (8 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "A user can register multiple distinct copies of the same game; retrying with the same idempotency key returns the existing copy instead of duplicating, including under real concurrent requests."
    requirement: INV-01
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_copies.py (9 tests, 2 run on real threads)"
        status: pass
    human_judgment: false
  - id: D3
    description: "A copy's release and edition must belong to the selected work/release respectively; mismatched combinations are rejected."
    requirement: INV-02
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_copies.py::test_release_must_belong_to_the_selected_work, ::test_edition_must_belong_to_the_selected_release"
        status: pass
    human_judgment: false
  - id: D4
    description: "The public profile projection never exposes private fields (copies, ratings, email, internal IDs, session data) even recursively, is isolated per user, and returns hostile alias/title text as inert data, never markup."
    requirement: INV-05
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_public_profile.py (6 tests, including a recursive denylist scan and two hostile-fixture XSS tests)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Popularity is a deterministic, versioned (popularity-v1) aggregate baseline -- same input produces the same order/scores/hash, zero activity returns an explicit empty list, ties break by UUID, and the DTO always declares its own limitation."
    requirement: REC-02
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_popularity.py (9 tests, including a real concurrent read-during-write test)"
        status: pass
    human_judgment: true
    rationale: "REC-02's own must_haves flags the formula weights (3/2/1/0 plus rating/10) as needing author approval before being presented as anything beyond a Phase 1 demonstration baseline -- the code enforces determinism and honest labeling, but the specific weighting choice is a judgment call for the author, not something a test can validate."

duration: 20min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 07: Library, Public Profile, and Popularity Summary

**Exact half-step ratings, idempotent multi-copy ownership with cross-table membership validation, a hand-built allowlist public profile that survives a recursive-denylist and hostile-fixture XSS scan, and a deterministic, versioned popularity-v1 baseline that never mixes partial state under concurrency.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-04T17:49:22Z
- **Completed:** 2026-09-04T18:01:18Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments

- `LibraryEntry.rating_half_steps`: nullable 1-10 integer with a PostgreSQL CheckConstraint backing the service-layer validation.
- `OwnedCopy`: release/edition membership validated against the work at the service layer (DB constraints can't express cross-table membership); idempotent creation proven correct under real concurrent threads, including the fix for a genuine race (see Deviations).
- `build_public_profile()`: a hand-built allowlist, verified by a recursive denylist scan and two hostile-fixture XSS tests reusing the project's existing `e2e/fixtures/hostile.json`.
- `rank_popularity_v1()`: deterministic, versioned, UUID-tie-broken, checksummed baseline, verified under a real concurrent read-during-write test.
- All three tasks' own `<verify>` commands pass; full backend suite: 93/93.

## Task Commits

1. **Task 1: Guardar rating exacto y múltiples copias válidas** - `5aeecec` (feat)
2. **Task 2: Publicar únicamente el perfil allowlisted** - `0baec0d` (feat)
3. **Task 3: Calcular baseline de popularidad reproducible** - `7c3941f` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

See `key-files` in frontmatter.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `select_for_update()` cannot lock a row that doesn't exist yet**
- **Found during:** First concurrency test run for `create_owned_copy`
- **Issue:** The initial implementation locked on the "does a copy with this idempotency key already exist" check before creating -- but PostgreSQL has no row to lock until one exists, so two concurrent requests both passed that check before either committed, then both attempted the INSERT and one hit `IntegrityError` on the UNIQUE constraint, which propagated as a real failure instead of the expected "lost the race" outcome.
- **Fix:** Removed the pointless lock on the pre-check; wrapped the actual `create()` in a nested `transaction.atomic()` (a savepoint, so a failure there doesn't poison an outer transaction) and caught `IntegrityError` as the expected signal to re-fetch and return the winner's row.
- **Files modified:** `apps/api/library/services.py`
- **Verification:** `test_concurrent_idempotency_key_replay_creates_exactly_one_copy` (3 real threads) passes.
- **Committed in:** `5aeecec`

**2. [Rule 1 - Bug] Redundant `source=` kwarg in `OwnedCopySerializer`**
- **Found during:** First test run of the copies endpoint
- **Issue:** Same DRF assertion pattern hit in earlier plans -- `source="release_id"` on a field literally named `release_id`.
- **Fix:** Removed the redundant kwargs.
- **Committed in:** `5aeecec`

**3. [Rule 3 - Blocking] `e2e/` was not bind-mounted into the api container**
- **Found during:** First run of the hostile-fixture XSS tests, which read `e2e/fixtures/hostile.json`
- **Issue:** Only `apps/api`, `data`, and `docs` had bind mounts; `e2e/` did not, so the file wasn't visible inside the container.
- **Fix:** Added `../e2e:/workspace/e2e:ro` to `infra/compose.yaml`'s `api` service.
- **Committed in:** `0baec0d`

**4. [Rule 1 - Bug, in my own test] Off-by-one in a `Path(__file__).resolve().parents[N]` calculation**
- **Found during:** Same test run as #3
- **Issue:** `parents[5]` resolved one level above the container's `/workspace` root; should have been `parents[4]`.
- **Fix:** Corrected the index.
- **Committed in:** `0baec0d`

**5. [Rule 1 - Bug, in my own test] A hostile-text payload containing a literal `/` broke URL routing, unrelated to XSS**
- **Found during:** Same test run
- **Issue:** Using `<script>...</script>` (which contains `/` inside the closing tag) as a URL path segment doesn't exercise text-escaping safety at all -- Django's `<str:alias>` converter simply doesn't match segments containing `/`, so the request 404'd for a routing reason that had nothing to do with the actual security property being tested.
- **Fix:** Selected a slash-free payload from the same hostile-fixtures file for the URL-path test; the slash-containing payload is still exercised via the request-body-based hostile-title test, where it's valid JSON string content rather than a URL segment.
- **Committed in:** `0baec0d`

---

**Total deviations:** 5 (1 real concurrency bug in service code, 1 serializer bug, 1 infra bind-mount gap, 2 bugs in my own test code). **Impact:** All necessary; #1 is the only one that would have shipped a real production bug (a spurious 500 under genuine concurrent copy creation) had the concurrency test not caught it.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 7 (Plan 01-16, demo seed data) and Wave 6's sibling work can proceed.
- Plans 01-08/01-09 (UI waves) can wire `LibraryControls`/`RecommendationStrip` directly against the now-complete rating/copies/popularity endpoints.
- REC-02's `human_judgment: true` flag is a reminder: the popularity-v1 formula weights are a demonstration choice, not yet author-approved as the final Phase 1 baseline -- worth a quick confirmation before treating it as locked.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
