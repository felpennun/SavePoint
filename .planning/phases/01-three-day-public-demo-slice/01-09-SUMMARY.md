---
phase: 01-three-day-public-demo-slice
plan: 09
subsystem: ui-integrated-surfaces
tags: [nextjs, django, drf, e2e]

requires:
  - phase: 01-06
    provides: [catalogue list/search/detail API]
  - phase: 01-07
    provides: [rating/copies/popularity/public-profile API]
  - phase: 01-08
    provides: [design tokens, i18n, AppShell]
  - phase: 01-16
    provides: [seeded demo interactions]

provides:
  - Homepage, catalogue, detail, collection, profile, and sources pages, all wired to real backend data
  - GameCard, LibraryControls (status+rating+copies), RecommendationStrip components
  - New backend endpoints -- MyLibraryView, SourcesView
  - An E2E test that proves rating and multi-copy persistence across a reload, not just status

affects: [01-10, 01-11]

actuals:
  tokens: 55000
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Secondary-panel failure isolation: a page's core record (game detail) always renders even when a secondary fetch (popularity strip) fails -- caught locally, degrades to an empty section, never blanks the page (UI-SPEC 'partial' state contract)."
    - "Backend DTOs carry ids alongside display labels for anything a client-side form needs to submit back (editions: [{id, name}], not [name]) -- a display-only shape silently blocks the next form that needs to reference the same entity."

key-files:
  created:
    - apps/web/components/GameCard.tsx
    - apps/web/components/LibraryControls.tsx
    - apps/web/components/RecommendationStrip.tsx
    - apps/web/app/[locale]/collection/page.tsx
    - apps/web/app/[locale]/profiles/[alias]/page.tsx
    - apps/web/app/[locale]/sources/page.tsx
    - apps/api/catalogue/tests/test_sources.py
  modified:
    - apps/web/app/[locale]/page.tsx
    - apps/web/app/[locale]/catalogue/page.tsx
    - apps/web/app/[locale]/games/[id]/page.tsx
    - apps/web/lib/api.ts
    - apps/web/middleware.ts
    - apps/web/components/AppShell.tsx
    - apps/api/catalogue/serializers.py
    - apps/api/catalogue/views.py
    - apps/api/catalogue/urls.py
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - e2e/demo-journey.spec.ts

key-decisions:
  - "StatusControl.tsx (from Plan 01-04) was deleted, superseded entirely by LibraryControls.tsx, which owns status, rating, and copies together -- the plan's declared file, not a StatusControl+extras split."
  - "Sources page data comes from a new SourcesView endpoint deriving from already-imported SourceRecord/AssetAttribution rows, not from Next.js reading data/manifests/*.json directly -- keeps the same-origin-proxy architecture consistent rather than introducing a second, file-system-based data path."
  - "The E2E rating/copies assertion is delta-based (count before vs. after within the same test run), not an absolute number -- this suite runs against the persistent dev database, not an isolated per-run test DB, so an absolute-count assertion would break on any second run."

requirements-completed: []

coverage:
  - id: D1
    description: "Full ES/EN journey: homepage sample, catalogue search/pagination, game detail with integrated status/rating/copy controls, saves a 3.5-star rating and two owned copies that both survive a page reload."
    requirement: LIB-01
    verification:
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts session -> catalogue -> status test (rating + copies extension)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Public profile page renders only the backend's allowlisted fields; public sources page shows dataset provenance derived from real imported data, degrading gracefully (503 + reload action) when nothing is imported yet."
    requirement: PROF-02
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_sources.py (2 tests)"
        status: pass
      - kind: manual_procedural
        ref: "Manual verification of /profiles/[alias] and /sources against the real running stack"
        status: pass
    human_judgment: true
    rationale: "The eight UI-SPEC state considerations (empty/loading/error/populated/partial/overflow/zero-one-many/long-text) this plan's must_haves cite are asserted here at a functional level (pages render, data flows, secondary-panel failures don't blank the page), not via the dedicated automated a11y/responsive suite -- that's Plan 01-10's declared deliverable (e2e/a11y.spec.ts). A full state-matrix audit is appropriately deferred there."

duration: 20min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 09: Integrated Public/Private Journey Surfaces Summary

**Every UI-SPEC page (homepage, catalogue, detail, collection, profile, sources) now wired to real backend data through GameCard/LibraryControls/RecommendationStrip, with an E2E test that proves a 3.5-star rating and two owned copies both survive a reload -- not just the status field the earlier tracer already covered.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-04T18:12:52Z
- **Completed:** 2026-09-04T18:25:29Z
- **Tasks:** 2
- **Files modified:** 22

## Accomplishments

- Built `LibraryControls` (status + rating + half-star range input + owned-copy form with release/edition selects), superseding the narrower `StatusControl` from the tracer plan.
- Built `GameCard` (whole-card link, lazy covers, no hover-only actions) and wired it into both the homepage sample and the catalogue grid.
- Added the Collection page and a new `MyLibraryView` endpoint (owner-scoped, only entries with a status set) -- this page didn't exist at all before this plan.
- Added the public Profile and Sources pages, the latter backed by a new `SourcesView` endpoint deriving dataset provenance from already-imported rows rather than reading manifest files across a service boundary.
- Fixed a real backend DTO gap discovered while building the copy form: `ReleaseSerializer.editions` returned display names only, with no `id` a form could actually submit.
- Expanded `e2e/demo-journey.spec.ts` to prove the plan's own acceptance criteria (3.5-star rating + two copies surviving reload), fixing two bugs surfaced only by running the real test against the real markup.

## Task Commits

1. **Combined commit (Task 1 + Task 2 -- see rationale below)** - `ae2da6b` (feat)

**Plan metadata:** commit follows this SUMMARY.

**Note on commit granularity:** Tasks 1 and 2 shared enough overlapping infrastructure (`lib/api.ts`, `AppShell`, `middleware.ts`) that splitting them into two commits would have meant an intermediate commit with a half-wired `AppShell` nav or an incomplete `lib/api.ts`. Committed together instead of forcing an artificial split.

## Files Created/Modified

See `key-files` in frontmatter.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `ReleaseSerializer.editions` had no `id` field**
- **Found during:** Building the copy-creation form in `LibraryControls`
- **Issue:** The DTO returned `["Deluxe Edition"]` (display names only) -- the copy-creation API needs a real `edition_id`, which the display-only shape couldn't provide.
- **Fix:** Changed to `[{"id": "...", "name": "Deluxe Edition"}]`; updated the one existing test (`test_detail.py`) that asserted the old shape.
- **Files modified:** `apps/api/catalogue/serializers.py`, `apps/api/catalogue/tests/test_detail.py`
- **Verification:** Full `apps/api/catalogue` suite passes; the copy form successfully submits real edition IDs in the E2E test.
- **Committed in:** `ae2da6b`

**2. [Rule 1 - Bug, in my own test] Stale title-extraction regex broken by the GameCard markup change**
- **Found during:** First run of the expanded E2E test
- **Issue:** The original tracer test (Plan 01-04) extracted a game's title from a single-line link (`"Title (Year) — Platform"`); after this plan replaced that markup with the multi-paragraph `GameCard`, the same string-splitting logic silently produced garbage, failing the title-match assertion.
- **Fix:** Target the title paragraph directly via its own locator instead of parsing the whole link's text.
- **Committed in:** `ae2da6b`

**3. [Rule 1 - Bug, in my own test] Invalid Playwright locator syntax, then an absolute-count assertion that broke on rerun**
- **Found during:** Same test run
- **Issue:** First attempt used an invalid mixed `">> text=A, text=B"` locator string; after fixing that, the next attempt asserted an exact copy count that only held on a completely fresh database -- a second run against the same persistent dev stack (which is how this session actually exercised it) accumulated copies from the prior run and failed.
- **Fix:** Proper `getByText(/^(Física|Digital)$/)` locator, and a before/after delta assertion instead of an absolute count.
- **Committed in:** `ae2da6b`

---

**Total deviations:** 3 (1 real backend DTO gap, 2 bugs in my own E2E test additions). **Impact:** The DTO fix was necessary for the copy form to function at all; the test fixes were necessary for the suite to be reliably rerunnable, which matters since this project's E2E tests run against a real persistent stack, not an isolated per-run database.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-10 (accessibility validation, `e2e/a11y.spec.ts`) now has real, data-populated pages to run axe/keyboard/responsive checks against, rather than empty stubs.
- Plan 01-11 (offline reproducibility, secrets gate) can proceed against a functionally complete UI surface.
- D2's `human_judgment: true` flag is a reminder: the eight UI-SPEC state considerations are proven functionally here, not yet via 01-10's dedicated automated suite.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
