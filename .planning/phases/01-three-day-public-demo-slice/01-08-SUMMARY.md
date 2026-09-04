---
phase: 01-three-day-public-demo-slice
plan: 08
subsystem: ui-shell
tags: [tailwindcss, i18n, accessibility, design-tokens]

requires:
  - phase: 01-04
    provides: "[locale] routing, session-aware layout"

provides:
  - Dark, cover-led design token system (replaceable CSS custom properties)
  - Parallel ES/EN dictionaries with a proven key-parity contract
  - Accessible AppShell (skip link, focus-trapped mobile menu, DOM-order-stable nav)
  - Working Tailwind pipeline (was installed but never actually wired up)

affects: [01-09, all-later-ui-work]

actuals:
  tokens: 22000
  tasks: 1
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Design tokens as CSS custom properties inside a Tailwind v4 @theme block -- component code references semantic names (--color-surface-base), never raw hex, so a future canonical palette swap touches one file."
    - "i18n key parity enforced by a runtime test that recursively diffs both dictionaries' key sets, not just relying on TypeScript's structural typing (which catches shape mismatches but not, e.g., an empty-string placeholder slipped into one locale)."
    - "Responsive nav renders the identical DOM/list in both TopNavigation and MobileMenu; only CSS visibility differs between breakpoints, so keyboard/screen-reader order never diverges from what's visually shown."

key-files:
  created:
    - apps/web/app/globals.css
    - apps/web/postcss.config.mjs
    - apps/web/i18n/dictionary.ts
    - apps/web/i18n/es.ts
    - apps/web/i18n/en.ts
    - apps/web/i18n/index.ts
    - apps/web/components/AppShell.tsx
    - apps/web/tests/i18n.test.ts
  modified:
    - apps/web/app/[locale]/layout.tsx
    - apps/web/vitest.config.ts

key-decisions:
  - "Tailwind CSS was a devDependency since Plan 01-03 but had no postcss.config.mjs -- it was never actually running. Added it as part of this plan since globals.css's first `@import \"tailwindcss\"` needed it to do anything."
  - "Task 1's file list is intentionally narrow (shell/tokens/i18n only); the plan's broader 'Artifacts this phase produces' section (GameCard, LibraryControls, RecommendationStrip, e2e/a11y.spec.ts, full page redesigns) describes the wave's eventual shape, not this single task's scope -- those pieces are later plans' declared deliverables (01-09 owns the component work, 01-10 owns accessibility validation)."

requirements-completed: []

coverage:
  - id: D1
    description: "ES and EN dictionaries declare exactly the same key set, with correct canonical zero/one/many count forms, and neither has an empty value."
    requirement: QUAL-03
    verification:
      - kind: unit
        ref: "apps/web/tests/i18n.test.ts (5 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Mobile menu traps focus, closes on Escape or route change, and returns focus to its trigger; skip link and a named nav landmark are present; desktop/mobile share identical DOM order."
    requirement: QUAL-03
    verification:
      - kind: manual_procedural
        ref: "Manual Playwright script: skip-link presence, nav landmark presence, mobile menu open/Escape-close/focus-return cycle, all confirmed against the real running app"
        status: pass
    human_judgment: true
    rationale: "This was verified with an ad-hoc script during the session, not a committed, repeatable automated test -- e2e/a11y.spec.ts (the actual automated axe/keyboard/responsive suite) is Plan 01-10's declared deliverable. Worth re-confirming once that suite exists rather than relying solely on this session's manual check."

duration: 15min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 08: Design Tokens, i18n, and App Shell Summary

**A working Tailwind pipeline (installed since Plan 01-03 but never actually wired up), a dark cover-led design token system, parallel ES/EN dictionaries with a proven parity contract, and an AppShell whose mobile menu correctly traps focus, closes on Escape/route change, and returns focus to its trigger -- confirmed in a real browser, not just asserted by a unit test.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-04T18:01:18Z
- **Completed:** 2026-09-04T18:07:13Z
- **Tasks:** 1
- **Files modified:** 10

## Accomplishments

- Discovered and fixed a real gap: Tailwind CSS has been a devDependency since Plan 01-03 but had no `postcss.config.mjs` -- it was never actually running. Added it.
- Built the D-17/D-18 dark, cover-led design token system as replaceable CSS custom properties, with WCAG AA contrast targets, a visible 2px focus ring, and 44px minimum touch targets baked in globally.
- Built typed, parity-tested ES/EN dictionaries with the canonical zero/one/many count-copy pattern from the UI-SPEC Copywriting Contract.
- Built `AppShell`/`TopNavigation`/`MobileMenu`: verified in an actual running browser (not just a unit test) that the mobile menu opens, traps Tab focus, closes on Escape, and returns focus to its trigger button.
- Also fixed `vitest.config.ts`, which had no path-alias configuration at all -- the `@/` imports this plan's own test needed would have failed immediately otherwise.

## Task Commits

1. **Task 1: Establecer shell, tokens e i18n completo** - `928e999` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

See `key-files` in frontmatter.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tailwind CSS was never actually wired up**
- **Found during:** Writing `globals.css`'s first line
- **Issue:** `@tailwindcss/postcss` has been a devDependency since Plan 01-03, but no `postcss.config.mjs` existed anywhere in `apps/web` to actually invoke it -- the `@import "tailwindcss"` directive would have been inert.
- **Fix:** Added `apps/web/postcss.config.mjs` registering the plugin.
- **Committed in:** `928e999`

**2. [Rule 3 - Blocking] Vitest had no path-alias configuration**
- **Found during:** First run of `tests/i18n.test.ts`, which imports via `@/i18n/...`
- **Issue:** `tsconfig.json` declares `"@/*": ["./*"]` for the TypeScript compiler and editor, but Vitest does not read `tsconfig.json`'s `paths` on its own -- `vitest.config.ts` had no `resolve.alias` at all.
- **Fix:** Added the matching alias, with a comment noting the two configs must be kept in sync manually.
- **Committed in:** `928e999`

---

**Total deviations:** 2 (both blocking infra gaps, not scope creep -- neither is optional for the plan's own stated deliverables to actually function).

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-09 can now build `GameCard`, `LibraryControls`, `RecommendationStrip`, and the full page redesigns on top of a working token system, i18n contract, and accessible shell, instead of having to bootstrap all of that itself.
- Plan 01-10 (accessibility validation, `e2e/a11y.spec.ts`) can build its automated axe/keyboard suite against a shell already manually confirmed to behave correctly, rather than discovering the focus-trap/skip-link/landmark work from scratch.
- D2's `human_judgment: true` flag is a reminder, not a blocker: this session's manual browser verification should be re-confirmed by 01-10's actual automated suite once it exists.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
