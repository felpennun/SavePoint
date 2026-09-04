---
phase: 01-three-day-public-demo-slice
plan: 04
subsystem: auth-tracer
tags: [nextjs, django, session-auth, csrf, e2e, playwright]

requires:
  - phase: 01-03
    provides: [Django/Next scaffold]
  - phase: 01-15
    provides: [bootstrap_demo_account command, credential-contract e2e tests]
  - phase: 01-06
    provides: [catalogue list/search/detail API]

provides:
  - Real session login/logout (CSRF-enforced pre-session, uniform errors, open-redirect discarded)
  - Owner-scoped, transactional library status endpoint (GET+POST) with append-only history
  - apps/web [locale] routing: homepage, login, catalogue, game detail with a working status control
  - Same-origin Next.js -> Django proxy, with every infra gap it exposed fixed
  - A real, passing browser E2E tracer: login -> catalogue -> status save -> reload -> logout

affects: [01-07, 01-08, 01-09, 01-10, all-later-frontend-plans]

actuals:
  tokens: 62000
  tasks: 2
  commits: 3

tech-stack:
  added:
    - "@types/react@19.2.18, @types/react-dom@19.2.7, @types/node@24.13.0 (devDependencies, via this workspace's pnpm catalog)"
  patterns:
    - "Same-origin API proxy via Next.js rewrites, not CORS-with-credentials -- keeps Django's session/CSRF cookies same-origin for the browser."
    - "Trust the backend's redirect target only when it echoes an explicit, already-locale-prefixed request; otherwise construct the locale-aware default client-side -- a locale-unaware backend must never own locale-prefixed navigation."
    - "Every mutable UI control that reflects server state (StatusControl) re-fetches its current value on mount instead of trusting client-side optimism -- the reload-persistence contract is enforced by always reading, never assuming."

key-files:
  created:
    - apps/web/app/[locale]/layout.tsx
    - apps/web/app/[locale]/page.tsx
    - apps/web/app/[locale]/login/page.tsx
    - apps/web/app/[locale]/catalogue/page.tsx
    - apps/web/app/[locale]/games/[id]/page.tsx
    - apps/web/app/[locale]/games/[id]/StatusControl.tsx
    - apps/web/lib/api.ts
    - apps/web/middleware.ts
    - apps/api/accounts/views.py
    - apps/api/accounts/urls.py
    - apps/api/accounts/tests/test_auth.py
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - apps/api/library/tests/test_entry.py
  modified:
    - apps/api/config/urls.py
    - apps/web/next.config.ts
    - apps/web/Dockerfile
    - infra/compose.yaml
    - e2e/demo-journey.spec.ts
    - package.json / pnpm-lock.yaml / pnpm-workspace.yaml

key-decisions:
  - "Reordered Task 1/Task 2 work: the E2E tracer genuinely cannot log in through the UI without the login endpoint, so accounts/views.py (nominally Task 2) was built alongside library/views.py (Task 1) rather than strictly sequentially. Both tasks' own acceptance criteria and verify commands still pass independently."
  - "DRF's APIView marks itself csrf_exempt at the Django-middleware level and only re-enforces CSRF inside SessionAuthentication once a user is already authenticated -- an anonymous login POST would otherwise carry no CSRF protection at all. LoginView explicitly re-applies Django's csrf_protect."
  - "infra/compose.yaml's web service runs a production build+start, not `next dev`: dev mode's HMR WebSocket reproducibly failed its handshake in this environment, which silently prevented React from finishing hydration -- a login click fell through to the browser's native form submit, putting the password in a URL query string. This also matches the project's own stated reproducibility principle (same commit/lockfiles build local and deployed)."
  - "Next.js's :path* rewrite capture always strips a trailing slash before matching, independent of skipTrailingSlashRedirect; since every Django URL is slash-terminated, Django's own APPEND_SLASH would otherwise redirect the slash back on and the client would follow that redirect right back into the same stripping -- fixed by appending the slash once in the rewrite destination template."
  - "Django's CSRF Origin check compares the browser's real Origin header against Host as Django itself sees it (api:8000 through the proxy, not localhost:3000) -- added DJANGO_CSRF_TRUSTED_ORIGINS rather than weakening the check."

requirements-completed: [AUTH-01, LIB-01, CAT-04, OPS-02]

coverage:
  - id: D1
    description: "Conventional login authenticates the bootstrap demo account and always lands on the catalogue, not a dashboard; invalid credentials return a uniform message; a POST without CSRF is rejected; logout invalidates the session."
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "apps/api/accounts/tests/test_auth.py (7 tests)"
        status: pass
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts (5 tests, real browser)"
        status: pass
    human_judgment: false
  - id: D2
    description: "A signed-in user can save a library status for a game; the value persists across a real page reload (read from PostgreSQL, never trusted client-side); identical resubmission does not duplicate history; one user cannot affect another's entry; DLC works are not independently actionable."
    requirement: LIB-01
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_entry.py (11 tests)"
        status: pass
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts session -> catalogue -> status test (reload assertion)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The full stack -- Next.js UI, Django API, PostgreSQL -- is reachable and functions together as a real reproducible local deployment (browser can reach both services; session cookies work same-origin through the proxy)."
    requirement: OPS-02
    verification:
      - kind: e2e
        ref: "e2e/demo-journey.spec.ts, run against docker compose up (production build)"
        status: pass
    human_judgment: true
    rationale: "Confirms local reproducibility for this session's environment; a genuinely fresh-machine `docker compose up` run (no prior image cache, no prior volume) has not been separately verified and is worth a human spot-check before relying on OPS-02 as fully proven."
  - id: D4
    description: "Canonical work identifiers (UUID primary keys) are used consistently by the newly-added status endpoint, not re-derived from any provider-specific value."
    requirement: CAT-04
    verification:
      - kind: unit
        ref: "apps/api/library/tests/test_entry.py::test_set_status_persists_and_reloads"
        status: pass
    human_judgment: false

duration: 44min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 04: Session-Catalogue-Status Tracer Summary

**Real login/logout with pre-session CSRF enforcement, an owner-scoped transactional library-status endpoint, and a [locale]-routed Next.js UI wired end-to-end through a same-origin Django proxy -- proven by an actual passing browser E2E test, which surfaced and forced fixes for five separate infrastructure bugs unit tests alone would never have caught.**

## Performance

- **Duration:** 44 min
- **Started:** 2026-09-04T17:03:27Z
- **Completed:** 2026-09-04T17:46:54Z
- **Tasks:** 2
- **Files modified:** ~30

## Accomplishments

- Built real login/logout (`accounts/views.py`): CSRF-enforced even pre-session (DRF's default would have skipped this for anonymous requests), uniform invalid-credential response, open-redirect targets discarded in favor of a safe default.
- Built the library status endpoint (`library/views.py`): owner-scoped via `select_for_update`+`transaction.atomic`, append-only `StatusTransition` history, idempotent identical-status retries, DLC works return 404, and a GET that returns the persisted value so the UI never has to trust its own optimism.
- Restructured `apps/web` into `[locale]` routing with four working pages (homepage, login, catalogue, game detail) and a real status-save control.
- Ran the actual stack end-to-end (not just unit tests) and, in doing so, found and fixed five genuine infrastructure bugs that would otherwise have silently broken every later frontend plan: missing Docker port mappings, a Next.js rewrite trailing-slash/redirect loop, a Django CSRF Origin mismatch through the proxy, dev-mode HMR hydration failure that let a login form leak credentials via URL, and a locale-blind post-login redirect.
- Final result: the plan's own two `<verify>` commands pass (`pytest library/tests/test_entry.py`: 11/11; `playwright demo-journey.spec.ts`: 5/5 in a real Chromium browser), and the full backend suite is 50/50.

## Task Commits

1. **Task 2 (backend, built first out of necessity -- see Decisions): accounts login/logout + library status endpoint** - `6af4881` (feat)
2. **Dependency fix discovered mid-task: real @types/react|react-dom|node** - `aa89ac6` (fix)
3. **Task 1: full tracer -- frontend, e2e journey, and every infra bug it surfaced** - `2d2ff01` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

See `key-files` in frontmatter for the full list. Notable: `infra/compose.yaml` now maps both services to host ports and runs `web` as a production build; `apps/web/next.config.ts` carries the same-origin proxy, the trailing-slash fix, and (correctly, this time) no `ignoreBuildErrors`.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task ordering: the E2E tracer cannot log in without the login endpoint**
- **Found during:** Starting Task 1
- **Issue:** Task 1's E2E test needs a real browser login, but the login view/page is nominally Task 2's deliverable.
- **Fix:** Built `accounts/views.py`/`urls.py` alongside `library/views.py` rather than strictly sequentially. Both tasks' declared acceptance criteria and verify commands still hold independently.
- **Committed in:** `6af4881`

**2. [Rule 2 - Missing Critical] Missing `@types/react`/`@types/react-dom`/`@types/node`, masked by crude `any`-typed shims and `ignoreBuildErrors: true`**
- **Found during:** Re-enabling TypeScript build checking (itself a fix -- see #3) before writing any real component code.
- **Issue:** `apps/web` had zero real TypeScript type safety for React or Node globals; a hand-written shim declared `process`/`Buffer`/`JSX.IntrinsicElements` as `any`.
- **Fix:** Paused, asked the user for explicit approval (new package installs require sign-off per this project's own package-legitimacy policy), then installed the real packages and removed the obsolete shim system and its Dockerfile step.
- **Files modified:** `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `apps/web/Dockerfile`, deleted `types/`
- **Verification:** `tsc --noEmit` clean; `next build` succeeds.
- **Committed in:** `aa89ac6`

**3. [Rule 1 - Bug] `next.config.ts` had `typescript: { ignoreBuildErrors: true }`**
- **Found during:** Reviewing existing scaffold before writing new frontend code
- **Issue:** Silently masked every TypeScript error at build time, directly contradicting the project's own "TypeScript strict contracts reduce API/state drift" research rationale.
- **Fix:** Removed. (This is what surfaced deviation #2.)
- **Committed in:** `2d2ff01`

**4. [Rule 3 - Blocking] Neither `api` nor `web` had a Docker port mapping**
- **Found during:** First attempt to actually load the app in a browser
- **Issue:** `infra/compose.yaml` had no `ports:` for either service -- the browser could not reach anything.
- **Fix:** Added `8000:8000` (api) and `3000:3000` (web).
- **Committed in:** `2d2ff01`

**5. [Rule 1 - Bug] No same-origin proxy from Next.js to Django**
- **Found during:** Same session as #4
- **Issue:** Without a proxy, the browser would need to call Django directly (a different origin/port), forcing CORS-with-credentials -- an anti-pattern this project's own research explicitly flags.
- **Fix:** Added a Next.js rewrite (`/api/:path*` -> Django), server-side-only `API_PROXY_TARGET`.
- **Committed in:** `2d2ff01`

**6. [Rule 1 - Bug] Rewrite trailing-slash redirect loop**
- **Found during:** First real request through the proxy (`/api/accounts/csrf/` never resolved)
- **Issue:** Next's `:path*` capture strips a trailing slash before matching, regardless of `skipTrailingSlashRedirect`; Django's own `APPEND_SLASH` then redirects it back on, and the client follows that redirect right back into the same stripping.
- **Fix:** `skipTrailingSlashRedirect: true` (stops Next's own redirect) plus an explicit trailing slash appended in the rewrite destination template (fixes every `/api/*` route in one place, since all Django URLs are slash-terminated).
- **Committed in:** `2d2ff01`

**7. [Rule 1 - Bug] Django CSRF Origin check rejected every request through the proxy**
- **Found during:** First login attempt through the proxy (403)
- **Issue:** The browser's real `Origin` header (`localhost:3000`) didn't match `request.get_host()` as Django saw it through the proxy (`api:8000`).
- **Fix:** `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` (both origins, since Playwright's default `baseURL` is `127.0.0.1`).
- **Committed in:** `2d2ff01`

**8. [Rule 1 - Bug, security-relevant] Login form leaked credentials into a URL query string under `next dev`**
- **Found during:** First real Playwright E2E run of the actual login page (not a manual `fetch()` bypass)
- **Issue:** `next dev`'s HMR WebSocket reproducibly failed its handshake (`ERR_INVALID_HTTP_RESPONSE`), which prevented React hydration from completing reliably; a click on the submit button sometimes fell through to the browser's native form submission (default GET), putting `username`/`password` directly in the URL.
- **Fix:** Two layers: (a) added `method="post"` to the `<form>` itself as defense-in-depth, so even an un-hydrated native submit can't leak via a GET query string; (b) switched `infra/compose.yaml`'s `web` service to a production build+start instead of `next dev`, eliminating the HMR flakiness that caused the race in the first place.
- **Committed in:** `2d2ff01`

**9. [Rule 1 - Bug] Post-login redirect ignored the user's actual locale**
- **Found during:** Full E2E run under Playwright's default `en-US` browser locale
- **Issue:** Django's `LoginView` is locale-unaware and defaults `next` to a bare `/catalogue`; the frontend trusted this literally, and the middleware's own locale-detection then picked `en` (from `Accept-Language`) rather than the locale the user was actually on, landing on `/en/catalogue` instead of `/es/catalogue`.
- **Fix:** The frontend only trusts Django's echoed `next` when it explicitly sent one (already locale-prefixed by the middleware); otherwise it constructs `/${locale}/catalogue` itself.
- **Committed in:** `2d2ff01`

**10. [Rule 1 - Bug] Middleware's public-path list incorrectly gated `/catalogue` and `/games`**
- **Found during:** First manual check of `/es/catalogue` (307 redirect to login, unexpected)
- **Issue:** Per UI-SPEC, only Collection requires authentication; catalogue and game detail are public browsing surfaces. The initial `PUBLIC_PATHS` list omitted both.
- **Fix:** Added `/catalogue` and `/games` to `PUBLIC_PATHS`.
- **Committed in:** `2d2ff01`

---

**Total deviations:** 10 (1 task-ordering necessity, 1 approved dependency install, 8 auto-fixed bugs). **Impact:** Every infra-level fix (#4-#10) was found only by actually running the full stack end-to-end rather than trusting unit tests in isolation -- this is exactly what a `type="tracer"` plan exists to catch before the next six waves build on top of a broken foundation. None were scope creep: each was a genuine blocker to the plan's own stated goal (a real, working vertical slice).

## Issues Encountered

Extensive debugging was required to isolate the credential-leak bug (deviation #8) from the CSRF-origin bug (#7) -- both manifested as "login doesn't work" and had to be diagnosed independently via direct `page.evaluate()` fetch calls, response/console event logging, and comparing dev-mode vs. production-build behavior.

## User Setup Required

None for local development. **For OPS-01 (deployment):** `DEMO_USERNAME`/`DEMO_PASSWORD` and `DJANGO_CSRF_TRUSTED_ORIGINS` (with the real deployed origin, not localhost) will need to be set as real environment values on whatever hosting platform Plan 01-12 targets -- documented here so that plan doesn't have to rediscover the CSRF-origin requirement from scratch.

## Next Phase Readiness

- Plan 01-07 (library/inventory/popularity, wave 6) can build directly on the now-real `LibraryEntry`/`StatusTransition` flow and the working accounts app.
- Plans 01-08/01-09 (UI waves) inherit a working `[locale]` routing structure, a functioning same-origin proxy, and a production-mode Docker setup -- the foundational plumbing that would otherwise have blocked each of them individually is now fixed once, here.
- D3's `human_judgment: true` flag (OPS-02) is a reminder, not a blocker: a genuinely fresh-machine `docker compose up --build` (no cached image, no existing volume) hasn't been separately verified in this session and is worth a quick spot-check before treating local reproducibility as fully proven.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
