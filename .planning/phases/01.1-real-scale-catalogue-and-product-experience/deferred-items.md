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
