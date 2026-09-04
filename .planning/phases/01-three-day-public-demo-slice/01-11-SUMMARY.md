---
phase: 01-three-day-public-demo-slice
plan: 11
subsystem: infra-security
tags: [docker-compose, healthcheck, secret-scanner, django-deploy-checks]

requires:
  - phase: 01-10
    provides: [data-populated, tested UI surface to run the full offline stack against]
  - phase: 01-16
    provides: [seed_demo command wired into the startup chain]

provides:
  - A clean checkout that reaches a fully seeded, healthy demo via one command, no network required
  - A self-testing secret scanner covering Git/build/image/log surfaces
  - A fail-closed DJANGO_DEPLOY_ENV settings profile satisfying `check --deploy`

affects: [01-12, 01-13, 01-14]

actuals:
  tokens: 62000
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - "A Compose service's anonymous-volume-masked build output (apps/web/.next, deliberately not bind-mounted so a stale host build never leaks into the container) is not readable from the host filesystem -- a host-side scanner must `docker compose cp` it out first, not assume a bind mount exists."
    - "Django's SILENCED_SYSTEM_CHECKS is the correct, idiomatic way to allowlist *specific, documented* `check --deploy` warnings for a genuinely-different-but-valid environment (plain HTTP behind Docker Compose, no TLS terminator) without weakening the checks Django runs everywhere else -- narrower and more auditable than a blanket --fail-level toggle."
    - "A secret-shape regex scanned against minified JS needs a positive signal (e.g. a digit) and an exclusion of code-punctuation chars ()? in the captured value, or it flags i18n dictionary entries (`password: \"Contraseña\"`) and coincidental substrings inside unrelated expressions as false positives."

key-files:
  created:
    - .env.example
    - scripts/check-secrets.ps1
  modified:
    - infra/compose.yaml
    - apps/api/config/settings.py
    - e2e/fixtures/hostile.json
    - README.md

key-decisions:
  - "Introduced DJANGO_DEPLOY_ENV (local|production) rather than inferring the security profile from DEBUG or DATABASE_URL -- an explicit, required switch is auditable in a way that inferring from unrelated settings is not, and it lets `check --deploy` be genuinely clean (via SILENCED_SYSTEM_CHECKS) in local mode instead of always showing expected-but-scary warnings."
  - "check-secrets.ps1 exempts exactly two things by path, never by content: e2e/fixtures/hostile.json (its whole documented purpose is holding the synthetic canaries the scanner self-tests against) and test files (**/tests/**, *.spec.ts, *.test.ts -- synthetic, reviewed fixture credentials are a normal Django/Playwright testing pattern, not a leak). Every other file, including README.md and .env.example, is scanned for real."
  - "Lengthened the local DJANGO_SECRET_KEY placeholder to 67 characters (still explicitly labeled not-a-secret, D-02) instead of silencing Django's W009 weak-key check -- removing the actual condition that trips the warning is more honest than suppressing the warning about it."

requirements-completed: []

coverage:
  - id: D1
    description: "A clean checkout reaches a fully seeded, healthy demo (db+api+web) via `docker compose up --build --wait` alone, with the migrate->import->bootstrap->seed chain running automatically and idempotently; disabling external network afterward does not affect the journey."
    requirement: OPS-02
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml up --build --wait (all three services report healthy; api logs show 150 games imported, demo account rotated, 6/6 seed interactions matching popularity-v1)"
        status: pass
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts + e2e/a11y.spec.ts, full suite (32 tests) against the running compose stack"
        status: pass
    human_judgment: false
  - id: D2
    description: "The demo works fully offline: no runtime code path calls an external provider, confirmed architecturally, not just by observation."
    requirement: OPS-03
    verification:
      - kind: static_analysis
        ref: "grep across apps/api for requests./httpx./urllib.request/fetch( outside tests/ and the one-time import tooling -- zero matches"
        status: pass
    human_judgment: false
  - id: D3
    description: "No secret appears in Git, image layers, the built browser bundle, or captured logs; a scanner that cannot detect its own known-bad canaries is never trusted to report a clean real scan."
    requirement: SEC-02
    verification:
      - kind: automated_cli
        ref: "scripts/check-secrets.ps1: self-test against e2e/fixtures/hostile.json's 7 synthetic canaries (all detected), then 4 real surfaces scanned non-emptily (3123 Git files, 394 build files, 2 images, ~99KB of logs) with zero non-allowlisted matches"
        status: pass
    human_judgment: false
  - id: D4
    description: "Production Django settings fail closed (no silent downgrade) and `check --deploy` passes cleanly in both the local-HTTP and production profiles, each on its own documented terms."
    requirement: SEC-02
    verification:
      - kind: automated_cli
        ref: "manage.py check --deploy: local profile -> 0 issues, 4 silenced (documented HTTP-only warnings); production profile with the local placeholder key (67 chars) -> 0 issues, 0 silenced; production profile with a short key -> RuntimeError at settings import, before any request is served"
        status: pass
    human_judgment: false

duration: 55min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 11: Offline Reproducibility and Secret Gate Summary

**One command (`docker compose up --build --wait`) now takes a clean checkout to a fully seeded, healthy, network-independent demo, and a self-testing secret scanner proves nothing leaked into Git, the built bundle, image layers, or logs -- all 111 backend + 6 frontend + 32 e2e tests green against the real stack.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-09-04T18:40:00Z (approx.)
- **Completed:** 2026-09-04T19:35:00Z (approx.)
- **Tasks:** 2
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- Wired the fixed offline startup chain (`migrate` → `import_catalogue` → `bootstrap_demo_account` → `seed_demo` → `runserver`) directly into `infra/compose.yaml`'s `api` service, with a `/health/`-based healthcheck and a healthcheck for `web` gating startup order -- verified end-to-end on a real `--build --wait` run with all three services reaching `Healthy`.
- Added `.env.example` (every runtime env var this project reads, names/inert-placeholders only) and a `README.md` runbook covering build/migrate/import/bootstrap/seed/rotate/health/URLs.
- Confirmed architecturally (not just observed) that no runtime API code path makes an outbound HTTP call -- the offline claim rests on an empty grep result, not on "it worked once."
- Built `scripts/check-secrets.ps1`: self-tests against 7 synthetic canary patterns in `e2e/fixtures/hostile.json` before trusting itself, then scans Git-tracked files, the Next.js build output (copied out of the `web` container's anonymous volume, which the host cannot otherwise read), Docker image history/inspect output, and captured `docker compose logs` -- all four non-emptily, zero non-allowlisted matches.
- Added a `DJANGO_DEPLOY_ENV` (`local`/`production`) profile to `apps/api/config/settings.py`: `local` silences exactly the four `check --deploy` warnings that are Django's own documented guidance for plain-HTTP-behind-Compose (no TLS terminator), `production` requires HSTS/SSL-redirect/secure-cookies and a ≥50-character secret key, failing closed with a `RuntimeError` at settings-import time otherwise.

## Task Commits

1. **Combined commit (Task 1 + Task 2)** - `543195e` (feat)

**Note on commit granularity:** Both tasks touched `README.md` (runbook vs. secret-gate section) and share the same verification run (a single live compose stack); splitting would have produced an artificial intermediate commit with a half-documented runbook. Same rationale as Plan 01-09.

## Files Created/Modified

See `key-files` in frontmatter.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, in my own script] PowerShell 5.1 `2>&1` on native `docker` calls wrapped successful stderr progress output as a terminating error**
- **Found during:** First run of `check-secrets.ps1` against the live stack
- **Issue:** `$ErrorActionPreference = "Stop"` combined with `docker compose cp ... 2>&1 | Out-Null` turned `docker`'s normal "Copying..." progress text (written to stderr on a zero exit code) into a `NativeCommandError` that halted the script.
- **Fix:** Switched the script to `$ErrorActionPreference = "Continue"` (every native call is already checked explicitly via `$LASTEXITCODE`/output) and removed `2>&1` from all `docker`/`docker compose` invocations.
- **Committed in:** `543195e`

**2. [Rule 1 - Bug, in my own script] `e2e/fixtures/hostile.json`'s own canaries permanently fail the Git-tracked-file scan of itself**
- **Found during:** Second run, after fixing (1)
- **Issue:** The fixture's whole purpose is holding secret-shaped canary values so the scanner can self-test -- meaning the real Git scan would always find them and never pass, forever.
- **Fix:** Added a narrow, explicit, documented path exemption for exactly that one file (all patterns), plus a separate exemption for genuine test files (`**/tests/**`, `*.spec.ts`, `*.test.ts`) from only the two patterns (`assigned-secret-value`, `bearer-token`) that legitimately fire on synthetic Django/Playwright test-fixture credentials.
- **Committed in:** `543195e`

**3. [Rule 1 - Bug, in my own script] `assigned-secret-value` regex flagged i18n dictionary text and minified-JS noise as secrets**
- **Found during:** Same run, scanning the built Next.js bundle
- **Issue:** The Spanish i18n dictionary's own `password: "Contraseña"` entry, and a coincidental `token="))?.split("` substring inside unrelated cookie-parsing code, both satisfied the original loose `[^'"]{8,}` value pattern.
- **Fix:** Tightened the regex to require the captured value contain a digit and exclude `()?` -- kills both false-positive classes while still matching the digit-containing canary and genuine test passwords.
- **Committed in:** `543195e`

---

**Total deviations:** 3, all bugs in my own new script caught and fixed before it was trusted to gate anything. **Impact:** None reached the committed state -- the script only ever ran clean, self-consistent, and non-vacuously against the real tree.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None -- no external service configuration required. `DEMO_USERNAME`/`DEMO_PASSWORD` remain local-dev-only placeholders (D-02); rotating them for any non-local use is documented in README.md.

## Next Phase Readiness

- Plan 01-12 (deployment) can build from the same Dockerfiles/Compose architecture verified here -- the plan's own gate (creating real cloud resources) still requires the user's explicit go-ahead per the earlier-established checkpoint.
- Plan 01-13 (evidence docs) has a concrete, reproducible local baseline (health, secret scan, deploy check) to cite.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
