# Phase 01.1 — Deferred Items

Out-of-scope discoveries logged during execution. Not fixed here; routed to
a follow-up plan / phase.

## From Plan 01.1-10 (automated product evidence)

### D-01.1-10-a — Authenticated top-nav overflows horizontally below ~430px

- **Found during:** Plan 01.1-10, mobile reflow evidence for the
  recommendations surface (demo session).
- **What:** When a visitor is signed in, the shared header packs brand +
  `ThemeToggle` (icon + "Tema: {estado}" text) + `AccountSwitcher` (icon +
  "Cuenta simulada: {alias}" + chevron) + the mobile-menu button into one
  non-wrapping flex row. At 375px this row is ~483px wide → page-level
  horizontal scroll on every authenticated page.
- **Scope call:** This is chrome shared by all authenticated pages, not a
  property of any single Plan 01.1-10 surface. Each surface's own `<main>`
  content region reflows cleanly at 375px (verified). Fixing the header
  needs a design decision (icon-only toggles on mobile, abbreviated
  labels, or moving one control into the disclosure) that touches the
  approved 01.1-UI-SPEC Navbar contract.
- **Not done because:** Plan 01.1-10's files are the two e2e suites + the
  review doc; a navbar redesign is a UI-SPEC change, not an evidence-capture
  change. The unauthenticated header overflow (logged-out chrome) WAS fixed
  in this plan (header gap/padding made responsive) because it blocked the
  pre-existing `e2e/a11y.spec.ts` 320–375px overflow gate.
- **Suggested owner:** a small follow-up UI plan, or fold into Plan 01.1-07
  review follow-ups. Affected: `apps/web/components/AppShell.tsx`,
  `apps/web/components/ThemeToggle.tsx`, `apps/web/components/AccountSwitcher.tsx`.

## AUTH-02 / SC3 — plural simulated accounts built but not wired into any runtime

**Status: deferred to a small follow-up plan.** `DemoAccountIdentity` +
`bootstrap_demo_accounts` (env-only `DEMO_ACCOUNTS` JSON contract) are fully
implemented and tested (Plan 01.1-04, 28 tests). But nothing activates the plural
path in a running environment: `infra/compose.yaml` and `apps/api/render-start.sh`
still call the singular `bootstrap_demo_account`, so the live product exposes one
preloaded account. Phase 01.1 verification records SC3 as PARTIAL for this reason.

**Why it was not fixed at phase close-out (2026-09-06):** the "one-line" fix
(swap the startup command + set a local `DEMO_ACCOUNTS`) does NOT work against a
database that already holds the Phase 1 `demo-visitor` user — `bootstrap_demo_accounts`
aborts with `SeedContractError: A seed username collides with an existing, unrelated
account` because that pre-existing user has no matching `DemoAccountIdentity` for the
legacy anchor key. It was tried and reverted; the dev stack was restored.

**The real fix (follow-up plan):** make `bootstrap_demo_accounts` *reconcile* a
pre-existing user under `LEGACY_ANCHOR_KEY` (adopt it into a `DemoAccountIdentity`)
instead of treating it as unrelated — the same "coexist with existing state" pattern
as the `fix(01.1-02)` Platform-slug reconcile. Then wire the plural command into
`infra/compose.yaml` (with a local, inert `DEMO_ACCOUNTS` placeholder value in the
D-02 spirit) and make `render-start.sh` use the plural command when `DEMO_ACCOUNTS`
is set (falling back to singular otherwise). During the deploy pass the author sets a
real `DEMO_ACCOUNTS` value in the Render service environment.
