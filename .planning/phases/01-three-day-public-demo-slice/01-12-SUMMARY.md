---
phase: 01-three-day-public-demo-slice
plan: 12
subsystem: public-deployment
tags: [render, vercel, neon, playwright, deployment]

requires:
  - phase: 01-11
    provides: [offline-reproducible Docker images, secret gate, fail-closed production settings profile]

provides:
  - A real public HTTPS demo (Vercel Hobby web + Render Free api + Neon Free db, no card) with a green Playwright smoke against it
  - infra/render.yaml (secret-free Blueprint), e2e/deployed-smoke.spec.ts (parametrized, host-allowlisted revision smoke), docs/deployment/public-demo.md (runbook + evidence)
  - GitHub Issues/Projects tracking for the remainder of the phase (established mid-plan, at the user's request)

affects: [01-14]

actuals:
  tokens: 95000
  tasks: 2
  commits: 9

tech-stack:
  added: []
  patterns:
    - "Test a fresh-database code path (import, seed, first-ever migration) against a genuinely new container, never the long-lived local dev Postgres volume -- the reused volume already contains state from months of idempotent reruns and silently masks exactly this class of bug (two of three deploy bugs this plan found were invisible locally for that reason)."
    - "Any identifier embedded in a cross-database-portable manifest (a demo seed, a fixture) must be deterministic across independent imports (a slug, a hash of stable input) -- never a database-assigned random primary key, which a fresh import on a different database will never reproduce."
    - "Next.js middleware's `matcher` runs before `next.config.ts` rewrites -- any path meant to be proxied straight through (not locale-prefixed) must be explicitly excluded from a locale-redirect matcher or it gets caught first."
    - "A deployed-smoke's network-monitoring assertions need two narrow, explicit exceptions to stay meaningful against a real client-side-routed app: an asset-host allowlist for intentionally external resources (never a blanket bypass), and filtering net::ERR_ABORTED specifically (browser-cancelled prefetches, not real failures) out of the requestfailed tally."
    - "Vercel Hobby on a private repo silently blocks auto-deploy for any commit whose author email GitHub does not link to the project-owning account -- fix by using that account's GitHub-issued noreply email (<user-id>+<username>@users.noreply.github.com) as the local git user.email, not a personal address that might be verified elsewhere."

key-files:
  created:
    - CONTRIBUTING.md
  modified:
    - infra/render.yaml
    - apps/api/render-start.sh
    - apps/api/Dockerfile
    - apps/api/accounts/management/commands/seed_demo.py
    - apps/api/accounts/tests/test_seed_demo.py
    - data/demo/seed-v1.json
    - apps/web/middleware.ts
    - e2e/deployed-smoke.spec.ts
    - docs/deployment/public-demo.md

key-decisions:
  - "Adapted the approved topology from a single-PaaS Docker deployment to Vercel Hobby (web) + Render Free (api) + Neon Free (db) mid-plan, after confirming with the user that no payment card would be used anywhere -- Render Free's Docker-only web service model doesn't natively host two independently-scaled services plus a managed Postgres without cost, so the frontend moved to Vercel's native Next.js build while keeping the same same-origin-proxy architecture (browser only ever talks to Vercel; API_PROXY_TARGET is server-side-only)."
  - "Established a GitHub Issues + Projects workflow mid-session at the user's explicit request: one issue per PLAN.md (not per task), closed via `Closes #N` commit trailers, documented in full in the new CONTRIBUTING.md. This is now the standing policy for the rest of the milestone, not just this plan."
  - "Fixed the seed manifest's non-portability at the source (canonical_slug everywhere) rather than making GameWork.id itself deterministic -- a smaller, more targeted change that didn't require a migration or touching the import path's primary-key semantics, and canonical_slug was already present in every interaction for this exact purpose."
  - "The deployed smoke's failure/host checks got two narrow, explicit carve-outs (Wikimedia Commons asset hosts; net::ERR_ABORTED) discovered only by actually running the smoke against the real deployment -- neither was guessable in advance, and both are scoped tightly enough that a genuinely new problem (an unexpected host, a real network failure) still fails the test."

requirements-completed: []

coverage:
  - id: D1
    description: "A real public HTTPS URL exists, serving the same reviewed images/data as the local Compose environment, with no secret in Git, the Blueprint, or any build artifact."
    requirement: OPS-01
    verification:
      - kind: automated_cli
        ref: "infra/render.yaml uses only sync:false/generateValue for every credential; scripts/check-secrets.ps1 (Plan 01-11) already covers Git/build/image/log surfaces for this same repo state"
        status: pass
      - kind: manual_procedural
        ref: "Render (savepoint-api) and Vercel (savepoint-web) dashboards, user-authenticated creation per docs/deployment/public-demo.md's manual order"
        status: pass
    human_judgment: true
    rationale: "Provider account creation, dashboard configuration, and payment-free-tier confirmation are inherently human actions this session cannot perform or verify from first principles -- the user created both services, entered the corrected Neon connection string, and confirmed no card was used anywhere."
  - id: D2
    description: "The deployed smoke (health -> homepage -> login -> catalogue -> detail) is green against the real URLs, with the exact Git commit confirmed identical on both Render's and Vercel's health responses, and no request to an unexpected host or a real network failure."
    requirement: OPS-01
    verification:
      - kind: e2e
        ref: "e2e/deployed-smoke.spec.ts run by the user against https://save-point-orpin.vercel.app, 2026-09-05T10:00Z"
        status: pass
    human_judgment: false
  - id: D3
    description: "Three real deploy-path bugs (missing docs/ in the API image; non-portable random GameWork.id in the demo seed manifest; Next.js middleware redirecting /health/ instead of proxying it) were found by testing against genuinely fresh state and fixed, each verified locally before pushing."
    requirement: OPS-03
    verification:
      - kind: integration
        ref: "Each fix verified against a throwaway, never-before-imported Postgres container (not the reused local dev volume) before being pushed; full backend suite 112/112 after the seed_demo fix"
        status: pass
    human_judgment: false
---

# Phase 01 Plan 12: Public Deployment Summary

**SavePoint is now live at a real public HTTPS URL — Vercel Hobby + Render Free + Neon Free, zero cost, no card — with a green end-to-end Playwright smoke confirming the exact same Git commit on both halves of the stack, after finding and fixing three real deploy-path bugs that only surfaced against genuinely fresh infrastructure.**

## Performance

- **Duration:** ~2 sessions across a pause/resume checkpoint (task 2 is a `blocking-human-action` gate by design)
- **Tasks:** 2
- **Files modified:** 9 (1 created)

## Accomplishments

- Adapted the deployment topology from the plan's original single-PaaS assumption to the user-approved Vercel Hobby + Render Free + Neon Free split, preserving the same-origin-proxy security architecture across two independently-hosted services.
- Diagnosed and fixed a Neon `DATABASE_URL` misconfiguration (a literal `host.neon.tech` placeholder pasted instead of the real endpoint) purely from Render's log output, without ever needing to see the connection string.
- Found and fixed three genuine, previously-undetected deploy-path bugs, each only visible against infrastructure that had never run the app before:
  1. `apps/api/Dockerfile` never copied `docs/` into the image, so `import_catalogue`'s fail-closed freeze-document check always failed on Render.
  2. `data/demo/seed-v1.json` hardcoded a random `GameWork.id` captured from one specific local database; fixed by keying every lookup/comparison on the deterministic `canonical_slug` instead, which every interaction already carried as `work_slug`.
  3. `apps/web/middleware.ts`'s locale-redirect matcher caught `/health/` before `next.config.ts`'s dedicated proxy rewrite could run, 307-redirecting the deployment's own revision-marker endpoint.
- Diagnosed a Vercel-Hobby-specific "commit author did not have contributing access" block (private-repo collaboration limit tied to unverified commit-author email) and fixed it by switching the repo's `git user.email` to the project owner's GitHub-issued noreply address.
- Fixed two false-positive classes in `e2e/deployed-smoke.spec.ts`'s own network-monitoring assertions (an unallowlisted-but-legitimate Wikimedia Commons asset host; `net::ERR_ABORTED` from cancelled Next.js `<Link>` prefetches) discovered only by running the smoke for real.
- Established, at the user's explicit request mid-plan, a GitHub Issues + Projects workflow (`CONTRIBUTING.md`, one issue per plan, closed via `Closes #N` trailers) that is now the standing policy for the rest of the milestone.
- Recorded full deployment evidence in `docs/deployment/public-demo.md`: both HTTPS URLs, the confirmed-matching Git commit, and the smoke's UTC pass time. No `PENDING` fields remain.

## Task Commits

1. **Task 1: Blueprint + runbook (earlier session)** - `efda1c5` (feat), `c0b86ec` (test)
2. **Task 2: provisioning, debugging, and closing the smoke loop** - `637ff63`, `c252a82`, `54484fb`, `17580cc` (earlier session, topology pivot + Render argv fixes) then this session's `c7d5d26`, `3d1976e`, `ff5aa2e`, `1f1743a`, `5cd9b69`, `60ec3ed`, `b820078`

**Note on commit count:** Task 2 is a `blocking-human-action` checkpoint spanning two sessions and a real, iterative debugging loop against live infrastructure (each fix required a real Render/Vercel round-trip to observe the next failure) -- this is the expected shape for this kind of plan, not scope creep.

## Files Created/Modified

See `key-files` in frontmatter. Also created this session (not phase-declared, but directly required to track and close out the remaining deploy work at the user's request): `CONTRIBUTING.md`, and GitHub Issues #2-#6 plus the "SavePoint" Projects board.

## Decisions Made

See `key-decisions` in frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Render Free cannot host the original single-PaaS topology as planned**
- **Found during:** Task 2 provisioning
- **Issue:** The plan's original assumption (one PaaS hosting both web and api as Docker services plus managed Postgres, all free) didn't hold for Render Free's actual service model.
- **Fix:** User-approved pivot to Vercel Hobby (web, native Next.js build) + Render Free (api, Docker) + Neon Free (db) -- same architecture, same secret boundary, still zero cost.
- **Committed in:** `637ff63` and follow-ups (earlier session).

**2. [Rule 1 - Bug] `docs/` missing from the API Docker image**
- **Found during:** First real Render deploy attempt
- **Issue:** `CommandError: Catalogue freeze document not found at /workspace/docs/verification/catalogue-freeze.md`. `docs/` only ever reached `/workspace/docs` locally via Compose's bind mount; the Dockerfile copied `data/` for the same PaaS-has-no-bind-mount reason but never `docs/`.
- **Fix:** Added `COPY --chown=savepoint:savepoint docs ./docs`. Verified against a fresh local build with no bind mounts.
- **Committed in:** `c7d5d26`

**3. [Rule 1 - Bug] `seed_demo` referenced a non-portable random `GameWork.id`**
- **Found during:** Second Render deploy attempt (after fix #2)
- **Issue:** `CommandError: Seed references unknown work 9229d748-... -- run import_catalogue before seed_demo.` `GameWork.id` is `models.UUIDField(default=uuid.uuid4)`; the manifest's hardcoded ids only ever matched the local dev database by coincidence (idempotent reruns against the same long-lived volume never changed them).
- **Fix:** Keyed every manifest lookup/comparison on `canonical_slug`/`work_slug` instead; removed `work_id` from the manifest and recomputed `interactions_sha256`; updated the test fixture to stop hardcoding `GameWork.id`. Verified against a genuinely fresh, throwaway Postgres container. Full backend suite: 112/112.
- **Committed in:** `3d1976e`

**4. [Rule 1 - Bug] `/health/` redirected instead of proxied on Vercel**
- **Found during:** First Vercel `/health/` check after deployment
- **Issue:** `apps/web/middleware.ts`'s `matcher` excluded `api`/`_next`/`favicon.ico` but not `health`; the locale-redirect logic caught it first (treating "health" as an unrecognized locale segment) and 307-redirected to `/es/health/` before `next.config.ts`'s dedicated rewrite ever ran.
- **Fix:** Added `health` to the matcher's exclusion. Verified locally against the full Compose stack.
- **Committed in:** `ff5aa2e`

**5. [Rule 1 - Bug, environmental] Vercel Hobby blocked auto-deploy over commit-author attribution**
- **Found during:** Checking whether Vercel had redeployed past `ff5aa2e`
- **Issue:** "The deployment was blocked because the commit author did not have contributing access... Hobby Plan does not support collaboration for private repositories." The repo's `git user.email` was a personal address verified under a *different* GitHub account than the one owning the Vercel project.
- **Fix:** Set the repo-local `git user.email` to the owning account's GitHub-issued noreply address (`<id>+<username>@users.noreply.github.com`, always verified, unique to that account). First commit with the corrected identity deployed normally.
- **Committed in:** `1f1743a` (and every commit after)

**6. [Rule 1 - Bug, in my own test] Deployed smoke flagged a legitimate external asset host**
- **Found during:** First real run of `e2e/deployed-smoke.spec.ts`
- **Issue:** `Error: unexpected network host(s): upload.wikimedia.org` -- a completely intentional, documented external cover-image host (data provenance/licensing), not a bug. The rest of the journey (login, catalogue, detail, title match) already passed.
- **Fix:** Added a narrow `ALLOWLISTED_ASSET_HOSTS` set (`upload.wikimedia.org`, `commons.wikimedia.org` only) rather than weakening the same-origin check generally.
- **Committed in:** `5cd9b69`

**7. [Rule 1 - Bug, in my own test] Deployed smoke flagged cancelled Next.js prefetches as failed requests**
- **Found during:** Second real run of the smoke (after fix #6)
- **Issue:** `failedRequests` listed GETs to pages the test never directly navigated to (`/es/sources`, a duplicate `/es/catalogue`, extra `/es/games/...`) -- Next.js `<Link>` background prefetches (nav bar, catalogue cards) cancelled by subsequent navigation, reported by Chromium as `requestfailed` with `net::ERR_ABORTED`, not a real network or server failure.
- **Fix:** Filtered `net::ERR_ABORTED` specifically out of the failure tally; any other `requestfailed` reason still fails the test.
- **Committed in:** `60ec3ed`

---

**Total deviations:** 7 (1 architectural pivot approved by the user, 4 real deploy-path/infra bugs, 2 bugs in this plan's own smoke test). **Impact:** Every one was found by actually exercising the real deployed system rather than trusting local verification alone -- consistent with this whole phase's pattern of infrastructure gaps only surfacing under real end-to-end pressure.

## Issues Encountered

A real Neon connection string was accidentally printed into this session's tool output once, while checking its format via the `neon` CLI. The user was told to rotate that password as a precaution. No further commands that could print a live secret were run afterward; `scripts/check-secrets.ps1`'s canary patterns were used as the reference for what counts as secret-shaped going forward.

## User Setup Required

None further -- Render, Vercel, and Neon are all live and configured. Rotation/rollback/teardown procedures are documented in `docs/deployment/public-demo.md`.

## Next Phase Readiness

- OPS-01's deployment evidence is complete (real, zero-cost public URL; green smoke against the exact deployed commit) but the requirement itself stays open in REQUIREMENTS.md until Plan 01-14, which also declares it as part of final human sign-off.
- Plan 01-14 (final human sign-off) can now proceed -- its dependency on 01-12 is satisfied.
- The two still-open manual accessibility checklist sections (400% zoom, screen reader, from Plan 01-10) and Plan 01-14's own sign-off protocol are the only items left before Phase 1 can be marked complete.
- No blockers.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-05*
