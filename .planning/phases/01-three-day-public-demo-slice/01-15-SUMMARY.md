---
phase: 01-three-day-public-demo-slice
plan: 15
subsystem: auth
tags: [django, auth, demo-account, playwright]

requires:
  - phase: 01-03
    provides: [Django/Next scaffold, migrations baseline]

provides:
  - Idempotent, rotatable demo account (accounts app, DemoAccountAnchor, bootstrap_demo_account command)
  - e2e credential-contract tests ahead of the login UI

affects: [01-04, e2e, accounts]

actuals:
  tokens: 15000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Stable non-sensitive anchor UUID pattern: identify a singleton row independent of a mutable, runtime-provided field (username), so rotating that field renames the same row instead of creating a duplicate."

key-files:
  created:
    - apps/api/accounts/models.py
    - apps/api/accounts/migrations/0001_initial.py
    - apps/api/accounts/management/commands/bootstrap_demo_account.py
    - apps/api/accounts/tests/test_bootstrap_demo_account.py
    - e2e/demo-journey.spec.ts
  modified:
    - apps/api/config/settings.py

key-decisions:
  - "Task 2's e2e/demo-journey.spec.ts is genuinely built incrementally: Plan 01-04 (Wave 5) also declares this file and adds the real browser login journey once the login page and Django accounts endpoints exist. Neither exists at Wave 4, so this plan implements and proves only what it actually owns -- the credential contract (env-only, redacted-on-missing, no fabricated identity) -- and leaves an explicit test.describe.skip documenting what 01-04 completes."
  - "DemoAccountAnchor uses a hardcoded, non-sensitive constant UUID (not a secret) as its primary key, so the single demo account can be found and rotated regardless of what DEMO_USERNAME currently is."
  - "validate_password() from Django's own password_validation module is used for the length/strength check rather than a custom rule, consistent with the project's 'don't hand-roll auth' constraint."

requirements-completed: [AUTH-01, SEC-02, OPS-02]

coverage:
  - id: D1
    description: "The controlled demo account exists before any E2E login test and keeps a stable identity across reruns and password rotations."
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_bootstrap_demo_account.py (11 tests: create/idempotent/rotate/collision/concurrency)"
        status: pass
    human_judgment: false
  - id: D2
    description: "DEMO_USERNAME/DEMO_PASSWORD are read exclusively from the runtime environment; missing values fail closed before any mutation; no credential, hash, or canary value ever appears in stdout/stderr."
    requirement: SEC-02
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_bootstrap_demo_account.py::test_stdout_and_stderr_never_contain_credentials, ::test_failed_run_error_output_never_contains_credentials"
        status: pass
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts credential-contract tests"
        status: pass
    human_judgment: false
  - id: D3
    description: "Reproducible local bootstrap: the same command run against a clean or already-provisioned database converges to one demo account."
    requirement: OPS-02
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_bootstrap_demo_account.py::test_concurrent_bootstrap_creates_exactly_one_account"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 15: Demo Account Bootstrap Summary

**Idempotent, rotation-safe demo account via a fixed non-sensitive anchor UUID decoupled from the runtime username, with a redacted-credential e2e contract test ahead of the login UI that Plan 01-04 will build.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-04T16:57:00Z
- **Completed:** 2026-09-04T17:22:00Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Scaffolded the `accounts` app (didn't exist yet) with `DemoAccountAnchor`, a stable non-sensitive UUID identifying the single demo account independent of the mutable `DEMO_USERNAME` value.
- Built `bootstrap_demo_account`: fails closed before any mutation if either env var is missing, validates password policy via Django's own `validate_password`, rotates via `set_password`, serialized by a PostgreSQL advisory lock so concurrent runs create exactly one account. Verified: 11/11 tests including real concurrent-thread invocation.
- Confirmed by direct test assertion that stdout/stderr/error messages never contain the username, password, or password hash, in both success and failure paths.
- Wrote `e2e/demo-journey.spec.ts` scoped to what this plan can honestly prove (credential contract) with an explicit, documented `test.describe.skip` block for the real login journey Plan 01-04 completes once the UI exists.

## Task Commits

1. **Task 1: Crear y rotar la cuenta demo idempotentemente** - `90f31f4` (feat)
2. **Task 2: Hacer que el trazador consuma exclusivamente credenciales runtime** - `36ae8a6` (test)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `apps/api/accounts/models.py` - `DemoAccountAnchor` + fixed anchor UUID constant.
- `apps/api/accounts/migrations/0001_initial.py` - Accounts app baseline migration.
- `apps/api/accounts/management/commands/bootstrap_demo_account.py` - Fail-closed, idempotent, advisory-lock-guarded bootstrap/rotate.
- `apps/api/accounts/tests/test_bootstrap_demo_account.py` - 11 tests.
- `apps/api/config/settings.py` - Registered `accounts` app.
- `e2e/demo-journey.spec.ts` - Credential-contract tests; login journey stubbed for 01-04.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] First e2e test design made it impossible to ever pass in the scenario it was meant to verify**
- **Found during:** Task 2, first Playwright run with env vars unset
- **Issue:** The initial test threw an `Error` inside the test body when `DEMO_USERNAME`/`DEMO_PASSWORD` were missing (to simulate the "fails with a redacted diagnostic" behavior) -- but Playwright reports a thrown error as a *failed* test, so the test could only ever "pass" when the vars happened to already be set, defeating its own purpose. A second bug in the same test used `.not.toContain("")` against an unset var's empty-string fallback, which always fails since every string contains the empty string.
- **Fix:** Rewrote as a pure-function test (`readDemoCredentials()`) exercised against a synthetic env object, independent of the ambient environment's real state, so the redaction contract is verified deterministically regardless of what's actually set on the running machine.
- **Files modified:** `e2e/demo-journey.spec.ts`
- **Verification:** Ran the suite twice, once with `DEMO_USERNAME`/`DEMO_PASSWORD` unset and once set -- both runs pass consistently.
- **Committed in:** `36ae8a6`

---

**Total deviations:** 1 auto-fixed (test-logic bug in my own draft, not the underlying command). **Impact:** No effect on the `bootstrap_demo_account` command itself, which passed its own 11 tests on the first correct implementation; the fix corrected only the e2e test's internal logic.

## Issues Encountered

None beyond the deviation above. The genuine cross-plan dependency gap (no login UI/endpoint exists yet for a full e2e login journey) is not an "issue" so much as expected sequencing -- documented in key-decisions and left as an explicit skip for Plan 01-04.

## User Setup Required

None - no external service configuration required. (DEMO_USERNAME/DEMO_PASSWORD themselves are runtime configuration, not a new external service.)

## Next Phase Readiness

- Plan 01-06 (this wave's sibling) already completed independently.
- Plan 01-04 (Wave 5) can now bootstrap the demo account as a precondition and should replace `e2e/demo-journey.spec.ts`'s skipped login-journey block with the real browser flow, calling `readDemoCredentials(process.env)` from this file rather than re-deriving its own credential-reading logic.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
