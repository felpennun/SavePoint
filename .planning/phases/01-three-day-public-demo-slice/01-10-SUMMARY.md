---
phase: 01-three-day-public-demo-slice
plan: 10
subsystem: accessibility
tags: [axe-core, playwright, wcag, keyboard]

requires:
  - phase: 01-09
    provides: [fully integrated, data-populated pages to actually scan]

provides:
  - Automated axe/keyboard/responsive/reduced-motion acceptance suite (e2e/a11y.spec.ts)
  - Documented, honest boundary between automated evidence and required human confirmation

affects: [01-11, 01-12]

actuals:
  tokens: 18000
  tasks: 1
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Inject an already-installed library's local bundle directly (page.addScriptTag pointing at node_modules/axe-core/axe.min.js) instead of adding a thin wrapper package for one call -- avoids a new-dependency approval round when the underlying library is already approved."
    - "Automated coverage notes in a human-verification checklist must explicitly say what they do and don't close out -- agent-generated evidence documented as agent-generated, never silently checking boxes reserved for human confirmation."

key-files:
  created:
    - e2e/a11y.spec.ts
  modified:
    - docs/verification/phase-01-manual.md

key-decisions:
  - "Used axe-core's local minified bundle directly via page.addScriptTag rather than installing @axe-core/playwright -- the underlying library was already an approved devDependency since Plan 01-01; the wrapper package would have been a new, unapproved dependency for what's functionally one line of glue code."
  - "Did not check any boxes in the pre-existing docs/verification/phase-01-manual.md checklist, even for sections this session's automated suite directly covers (keyboard journey, 320px reflow, reduced motion) -- added a clearly-labeled 'Automated coverage' note instead, since the document's own Sign-off section reserves checkbox confirmation for a human reviewer, and mechanically checking them from agent output would misrepresent automated evidence as human sign-off."

requirements-completed: []

coverage:
  - id: D1
    description: "Automated axe scan finds zero critical/serious violations across homepage, login, catalogue, sources, and one game detail page, in both locales, at both required viewports."
    requirement: QUAL-03
    verification:
      - kind: automated_ui
        ref: "e2e/a11y.spec.ts axe scan describe blocks (20 tests: 5 pages x 2 locales x 2 viewports)"
        status: pass
    human_judgment: false
  - id: D2
    description: "A full keyboard-only journey (skip link through sign-out) completes without a pointer, and 320px reflow / reduced-motion checks pass."
    requirement: QUAL-03
    verification:
      - kind: automated_ui
        ref: "e2e/a11y.spec.ts keyboard-only journey, horizontal-overflow, and reduced-motion describe blocks (6 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "400% zoom reflow and a basic screen-reader pass are documented as still requiring genuine human sensory verification -- not something automated output can honestly certify."
    requirement: QUAL-03
    verification: []
    human_judgment: true
    rationale: "These two checklist sections require an actual human at a real 400% browser zoom level and with a real screen reader (NVDA/VoiceOver) -- no automated proxy honestly substitutes for that sensory judgment. Left explicitly unchecked in docs/verification/phase-01-manual.md pending a real human session, per that document's own Sign-off protocol."

duration: 10min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 10: Automated Accessibility/Responsive Acceptance Summary

**26 automated tests -- axe (0 critical/serious violations) across 5 pages x 2 locales x 2 viewports, a full keyboard-only journey through the entire app, 320px reflow, and reduced-motion -- all green, with the two genuinely human-only checks (400% zoom, screen reader) honestly left unchecked in the manual protocol pending a real human session.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-04T18:25:29Z
- **Completed:** 2026-09-04T18:35:XXZ (approximate)
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Built `e2e/a11y.spec.ts`: axe-core injected directly from its already-approved local bundle (no new dependency), scanning every required page in both locales at both required viewports -- zero critical/serious violations found anywhere.
- Automated the full keyboard-only journey from the manual checklist: skip link, login, search, detail, status save, collection, public profile, sign-out -- all reachable and operable without a pointer.
- Automated 320px horizontal-overflow and `prefers-reduced-motion` checks.
- Updated the pre-existing (Plan 01-02) manual verification protocol with an honest "what's automated now" note, explicitly not checking off the two sections (400% zoom, screen reader) that genuinely require a human.

## Task Commits

1. **Task 1: Ejecutar aceptación accesible completa** - `9b4266a` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `e2e/a11y.spec.ts` - 26 tests: axe scans, keyboard journey, overflow, reduced motion.
- `docs/verification/phase-01-manual.md` - Added automated-coverage note; checklist itself untouched.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, in my own test] `import.meta.url` used in a non-ESM test file**
- **Found during:** First run of `e2e/a11y.spec.ts`
- **Issue:** Used `import.meta.url` to locate `axe.min.js`, but this Playwright suite (like the project's other `e2e/*.spec.ts` files) runs under a CommonJS-style transform, not real ESM -- `import.meta` isn't valid syntax there, and the whole file failed to load ("No tests found").
- **Fix:** Switched to `__dirname` (available in the actual CommonJS context this file runs under).
- **Committed in:** `9b4266a`

---

**Total deviations:** 1 (a bug in my own first draft, fixed before any assertion ran).

## Issues Encountered

None beyond the deviation above.

## User Setup Required

**Two manual verification sections remain genuinely open, not automatable:** `docs/verification/phase-01-manual.md`'s "Reflow at 400% zoom" and "Basic screen-reader pass" sections need a human reviewer with a real browser at 400% zoom and a real screen reader (NVDA/VoiceOver) before Phase 1's accessibility evidence can be signed off per that document's own protocol.

## Next Phase Readiness

- Plan 01-11 (offline reproducibility, secrets gate) and Plan 01-12 (deployment) can proceed; this plan's automated suite gives strong (though not exhaustive -- see the plan's own FLAGGED ASSUMPTION) accessibility evidence for the demo.
- The two open manual sections should be completed by a human before the phase's final sign-off (Plan 01-14).
- No blockers to continuing.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
