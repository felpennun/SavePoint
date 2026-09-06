# Phase 01.1 — Product Surface Verification (pre-review evidence)

Automated evidence for the four Phase 01.1 product surfaces (catalogue,
detail, registration, recommendations) at the approved desktop and mobile
viewports. Produced by Plan 01.1-10; consumed by Plan 01.1-07 (human author
review). Requirements in scope: QUAL-05, CAT-02, AUTH-02, REC-10.

## Playwright Results

Command (verify gate 1, executed from the worktree root):

    corepack pnpm exec playwright test e2e/a11y.spec.ts e2e/demo-journey.spec.ts --project=chromium

Environment: Chromium (Playwright 1.62.1). Target: a local production build
(`next build && next start`) of this worktree, `PLAYWRIGHT_BASE_URL` set to
that build; `DEMO_USERNAME` / `DEMO_PASSWORD` supplied from the runtime
environment (values withheld by design). API traffic proxied to the running
`infra/compose.yaml` Django stack.

Totals: 41 tests in 2 files — 41 passed, 0 failed, 0 skipped. Two
consecutive green runs (stability check). Exit code 0.

Per-file:

- `e2e/a11y.spec.ts` — 34 tests. Public-page axe scans (es/en x desktop/mobile),
  320–375px horizontal-overflow gate, reduced-motion, the keyboard-only
  acceptance journey, plus the new per-surface product-evidence block:
  catalogue (filter state survives reload, full-catalogue count line,
  pagination, keyboard focus on search), detail (cover or first-party
  fallback, ScorePill present-or-omitted, static IGDB provenance +
  attribution), registration (labelled fields, client-side mismatch
  validation with password clearing), and the recommendations auth gate
  (signed-out visit redirects to `/login?next=`, no personal nav links).
  Each surface runs at both `desktop` (1280x800) and `mobile` (375x812).
- `e2e/demo-journey.spec.ts` — 7 tests. The demo credential contract, the
  demo login tracer (session -> catalogue -> status -> rating -> copies,
  reload-persistence), logout invalidation, the fresh-account registration
  journey (real `POST /api/accounts/register/`; on a spent per-IP rate
  budget it asserts the localized rate-limit state instead — itself a
  required UI-SPEC state), and the authenticated demo-session surfaces test
  that exercises collection + recommendations at `desktop` and `mobile`
  (disclosure, shelves-or-onboarding, mobile content reflow, axe).

Viewport labels used throughout: `desktop` = 1280x800, `mobile` = 375x812
(>= the 320px UI-SPEC floor).

Playwright verdict: PASS

## axe Results

axe-core 4.13.0 injected via the existing local-bundle `addScriptTag`
pattern (no `@axe-core/playwright` dependency added). Gate: zero
critical/serious violations. Results by surface:

- catalogue — PASS. Scanned unfiltered (es/en x desktop/mobile, existing
  suite) and filtered (genre applied, desktop + mobile, new block). No
  critical/serious violations.
- detail — PASS. One representative game detail page scanned es/en x
  desktop/mobile (existing suite, now waiting for the detail navigation to
  settle before injecting axe) and desktop + mobile in the new block. No
  critical/serious violations.
- registration — PASS. `/es/register` scanned desktop + mobile with a
  surfaced validation error present. No critical/serious violations.
- recommendations — PASS. Authenticated `/es/recommendations` (demo
  session) scanned desktop + mobile with the algorithm/limitation
  disclosure and onboarding state rendered. No critical/serious violations.
- supporting context — homepage, login, sources scanned es/en x
  desktop/mobile: no critical/serious violations.

axe verdict: PASS

## Screenshot Artifacts

Every pair below was written by Playwright during the gate-1 run; each path
is repository-relative and points to a committed PNG.

| Surface | Viewport | Screenshot artifact |
| --- | --- | --- |
| catalogue | desktop | e2e/artifacts/phase-01.1/catalogue-desktop.png |
| catalogue | mobile | e2e/artifacts/phase-01.1/catalogue-mobile.png |
| detail | desktop | e2e/artifacts/phase-01.1/detail-desktop.png |
| detail | mobile | e2e/artifacts/phase-01.1/detail-mobile.png |
| registration | desktop | e2e/artifacts/phase-01.1/registration-desktop.png |
| registration | mobile | e2e/artifacts/phase-01.1/registration-mobile.png |
| recommendations | desktop | e2e/artifacts/phase-01.1/recommendations-desktop.png |
| recommendations | mobile | e2e/artifacts/phase-01.1/recommendations-mobile.png |

## Surface Coverage

Desktop + mobile + accessibility roll-up per surface (see 01.1-UI-SPEC
`## Per-Surface Coverage Matrix`). Each row: functional assertions +
screenshot at both viewports, axe clean, mobile reflow checked.

| Surface | Viewports | Accessibility | Reflow | Verdict |
| --- | --- | --- | --- | --- |
| catalogue | desktop + mobile | axe PASS | no horizontal scroll at 375px PASS | PASS |
| detail | desktop + mobile | axe PASS | mobile single-column, no horizontal scroll PASS | PASS |
| registration | desktop + mobile | axe PASS | no horizontal scroll at 375px PASS | PASS |
| recommendations | desktop + mobile | axe PASS | content region no horizontal scroll at 375px PASS | PASS |

Notes carried to Plan 01.1-07 / follow-up:

- Genre recommendation shelves could not be shown with real data: both the
  demo account and freshly registered accounts return
  `insufficient_history` from `GET /api/recommendations/genre-taste/` in the
  seeded dev environment, so the recommendations evidence captures the
  algorithm/limitation disclosure + the explicit onboarding state. The
  shelf-grouping logic itself is unit-tested in Plan 01.1-09. The test
  asserts "shelves OR onboarding" so a history-bearing environment is also
  covered.
- The shared authenticated top navigation (brand + theme toggle +
  account switcher + mobile menu button) overflows horizontally below
  ~430px. This is chrome shared by every authenticated page, not a
  property of any single surface's content region (each surface's `<main>`
  reflows cleanly at 375px), and needs a design decision on mobile chrome
  density. Logged in
  `.planning/phases/01.1-real-scale-catalogue-and-product-experience/deferred-items.md`.
