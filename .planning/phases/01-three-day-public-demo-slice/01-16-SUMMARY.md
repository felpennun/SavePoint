---
phase: 01-three-day-public-demo-slice
plan: 16
subsystem: demo-data
tags: [seed, popularity-v1, idempotent]

requires:
  - phase: 01-06
    provides: [imported catalogue, real GameWork UUIDs]
  - phase: 01-07
    provides: [LibraryEntry rating/status, popularity.py]
  - phase: 01-15
    provides: [bootstrap_demo_account, DemoAccountAnchor]

provides:
  - Versioned, checksummed, credential-free demo interaction manifest
  - Idempotent, fail-closed, advisory-lock-guarded seed_demo command
  - A verified, reproducible 6-result popularity-v1 baseline for later public-surface E2E tests

affects: [01-09]

actuals:
  tokens: 20000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Self-verifying manifest: a command that loads data checks the manifest's own checksum AND re-derives the expected downstream computation (popularity-v1) from what it just wrote, failing loudly on either data drift or formula drift, rather than trusting a one-time author's assertion forever."

key-files:
  created:
    - data/demo/seed-v1.json
    - apps/api/accounts/management/commands/seed_demo.py
    - apps/api/accounts/tests/test_seed_demo.py

key-decisions:
  - "The manifest references the bootstrap account by its stable DemoAccountAnchor UUID (from Plan 01-15), not a raw Django integer PK or a username -- consistent with that plan's own pattern of decoupling identity from a mutable, credential-adjacent field."
  - "Interaction data (6 games, real UUIDs pulled from the already-imported catalogue) was hand-picked to produce 6 distinct, non-tied popularity-v1 scores, keeping the deterministic-ordering assertion simple; the tie-break-by-UUID behavior itself is already covered by Plan 01-07's own popularity tests, so this plan didn't need to re-prove it."

requirements-completed: []

coverage:
  - id: D1
    description: "Demo interactions load only after catalogue import and library schema exist, never create or rotate credentials, and are denylist-scanned for credential-shaped keys before any mutation."
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_seed_demo.py (13 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Two loads (and three real concurrent loads) reproduce identical IDs, statuses, ratings, and digest -- no partial state under concurrency."
    requirement: LIB-01
    verification:
      - kind: unit
        ref: "test_seed_is_idempotent, test_concurrent_seed_invocations_leave_no_partial_state"
        status: pass
    human_judgment: false
  - id: D3
    description: "The versioned fixture produces exactly the six expected popularity-v1 results (order and score) declared in the manifest."
    requirement: REC-02
    verification:
      - kind: unit
        ref: "test_seed_loads_and_matches_expected_popularity_exactly"
        status: pass
      - kind: other
        ref: "Real run against the live imported catalogue: 'popularity-v1 matches 6/6 expected results', confirmed on both a fresh and a repeat (idempotent) invocation"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 16: Deterministic Demo Interaction Seed Summary

**A versioned, checksummed, credential-free interaction manifest referencing real imported catalogue works, loaded by a fail-closed, idempotent, advisory-lock-guarded command that re-verifies its own popularity-v1 output against the manifest's declared expectation -- confirmed both in tests and against the actual live catalogue.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-04T18:08:15Z
- **Completed:** 2026-09-04T18:12:02Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Pulled 6 real `GameWork` UUIDs from the already-imported catalogue and hand-computed a deterministic, non-tied `popularity-v1` expectation (scores 4.0 down to 0.2) so the seed's correctness is self-checking, not asserted by hand.
- `seed_demo`: fails closed before any mutation if the bootstrap account or any referenced work is missing; denylist-scans the whole manifest for credential-shaped keys; verifies checksum; loads inside an advisory-lock-guarded transaction; then re-derives `popularity-v1` from what it just committed and fails loudly on any mismatch.
- Verified against the real running stack, not just pytest: a fresh run and a repeat run both report "popularity-v1 matches 6/6 expected results" against the actual live imported catalogue.

## Task Commits

1. **Task 1: Definir interacciones demo versionadas sin credenciales** - `618ba04` (feat)
2. **Task 2: Cargar y comprobar estados, ratings y popularidad** - `d3506f7` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `data/demo/seed-v1.json` - Versioned manifest: account anchor UUID, cutoff, 6 interactions, interactions checksum, full expected popularity-v1 result set.
- `apps/api/accounts/management/commands/seed_demo.py` - Fail-closed, idempotent, advisory-lock-guarded loader with self-verification.
- `apps/api/accounts/tests/test_seed_demo.py` - 13 tests (6 manifest-only, 7 full-load including a real 3-thread concurrency test).

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

None. Both tasks' `<verify>` commands passed on the first implementation; no bugs were found during this plan (a first for this session -- prior plans each surfaced at least one real defect).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-09's public-surface E2E tests (profile, popularity/recommendation strip) now have real, reproducible demo data to assert against instead of an empty catalogue.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
