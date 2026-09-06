---
gsd_state_version: 1.0
current_phase: 01.1
current_phase_name: Real-Scale Catalogue and Product Experience
status: executing
stopped_at: "Plans 01.1-01/02/06/04/08/03/05/09 merged (8/10). Session rate limit was hit at Wave 8; 01.1-09 finalized inline. Next Wave 9 = 01.1-10 (evidence) once the limit resets (~02:30 Paris). Stop at Wave 10 (01.1-07 author checkpoint)."
last_updated: "2026-09-05T23:25:00.000Z"
last_activity: 2026-09-05
last_activity_desc: "Plans 01.1-02 + 01.1-06 merged — importer proven + full apps/web redesign live"
state_head: 069f422
progress:
  total_phases: 9
  completed_phases: 1
  total_plans: 26
  completed_plans: 24
  percent: 12
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-04)

**Core value:** Users receive useful and explainable video-game recommendations from a well-organised collection, while every algorithmic result remains reproducible and defensible in the thesis.
**Current focus:** Phase 01.1 — Real-Scale Catalogue and Product Experience

## Current Position

Phase: 01.1 (Real-Scale Catalogue and Product Experience) — EXECUTING
Plan: 8 of 10 complete (01.1-01/02/06/04/08/03/05/09). Next: 01.1-10 (Wave 9 — Playwright/axe/screenshot evidence).
Status: Executing Phase 01.1 — Wave 3 done, next Wave 4
Last activity: 2026-09-05 — Plans 01.1-02 + 01.1-06 merged (069f422)

Progress: [████████░░] 80% (8 of 10 plans)

## Performance Metrics

**Velocity:**

- Total plans completed: 16
- Average duration: 25 min
- Total execution time: 25 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 16 | - | - |

**Recent Trend:**

- Last 5 plans: 01-01 (25 min)
- Trend: baseline established

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 25 min | 2 tasks | 7 files |
| Phase 01 P05 | 45min | 2 tasks | 5 files |
| Phase 01 P06 | 17min | 2 tasks | 15 files |
| Phase 01 P15 | 25min | 2 tasks | 12 files |
| Phase 01 P04 | 44min | 2 tasks | 30 files |
| Phase 01 P07 | 20min | 3 tasks | 16 files |
| Phase 01 P08 | 15min | 1 tasks | 10 files |
| Phase 01 P16 | 8min | 2 tasks | 3 files |
| Phase 01 P09 | 20min | 2 tasks | 22 files |
| Phase 01 P10 | 10min | 1 tasks | 2 files |
| Phase 01 P11 | 55min | 2 tasks | 6 files |
| Phase 01 P12 | 2 sessions | 2 tasks | 9 files |
| Phase 01 P14 | 1 session | 1 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- [Phase 1]: Ship a controlled, lawful, public vertical demo within three days; explicitly treat it as demo-grade.
- [Phases 2-8]: Harden data, evaluation, product, security, accessibility, operations, and evidence incrementally.
- [All phases]: Thesis and agent-methodology evidence is a continuous acceptance criterion.
- [Phase 01]: Next.js fijado a 16.3.4 tras rechazar el lock vulnerable de 16.2.12.
- [Phase 01]: Toda dependencia directa requiere pin exacto, evidencia oficial y aprobación humana.
- [Phase 01]: Replaced the fabricated Wikidata QID list in scripts/acquire_catalogue.py with a class-filtered live query (wdt:P31 wd:Q7889) plus dynamically-resolved platform sub-queries; fixed a URL-decoding bug that silently defaulted every cover image to placeholder. — The pre-existing hand-typed QID list contained non-video-game entities (a commune, an organ, a war); any hardcoded Wikidata QID must be verified live before use, never trusted from memory or a prior commit.
- [Phase 01]: Added dev-only Docker bind mounts (infra/compose.yaml) and fixed apps/api/pytest.ini's missing DJANGO_SETTINGS_MODULE -- both were silently breaking every future plan's docker compose run/pytest verification, not just plan 01-06's. — Without a bind mount, docker compose run always tested whatever code existed at the last image build, never the current working tree; without DJANGO_SETTINGS_MODULE actually loaded inside the container, any Django-DB test would fail to configure Django at all. Fixing both now prevents every subsequent plan in the phase from hitting the same wall.
- [Phase 01]: Scoped e2e/demo-journey.spec.ts (Plan 01-15 Task 2) to only what is verifiable without a login UI: the credential-contract (env-only, redacted-on-missing). The real browser login journey is an explicit test.describe.skip deferred to Plan 01-04, which also declares this file and will add the login page/endpoint. — Neither the Next.js login page nor the Django accounts login endpoint exist yet at Wave 4 -- both are Plan 01-04 deliverables (Wave 5). Fabricating a login test against non-existent infrastructure would be dishonest; the file is explicitly built incrementally across the two plans instead.
- [Phase 01]: Ran the plan 01-04 vertical tracer against the real stack (not just unit tests) and found/fixed 8 real infrastructure bugs: missing Docker port mappings, a Next.js rewrite trailing-slash redirect loop, a Django CSRF Origin mismatch through the same-origin proxy, dev-mode HMR hydration failure that let the login form leak credentials via URL query string, a locale-blind post-login redirect, and an incomplete middleware public-path list. Switched infra/compose.yaml's web service from `next dev` to a production build+start as the fix for the HMR issue. — None of these were found by unit tests alone -- they only surfaced when the full login->catalogue->status journey was actually driven through a real browser via Playwright, which is exactly what a type="tracer" plan exists to catch before six more waves build on top of a broken foundation. The production-build switch also better matches the project's own stated reproducibility principle (same commit/lockfiles build local and deployed).
- [Phase 01]: Resolved PROF-02's flagged assumption for Phase 1: every account is public by design (small controlled demo, no privacy toggle yet). The public profile serializer is a hand-built allowlist (never DRF ModelSerializer auto-introspection), verified by a recursive denylist scan plus hostile-fixture XSS tests. — Building the allowlist by hand means a new private model field requires an explicit decision to expose it, not an accidental one to hide it -- the opposite failure mode of auto-serialization. Phase 1's no-privacy-toggle choice keeps the "unauthorized vs nonexistent" indistinguishability requirement trivially satisfied (both cases collapse to the same 404 today) while leaving the response shape ready for a future toggle without a rewrite.
- [Phase 01]: Found Tailwind CSS had been a devDependency since Plan 01-03 but was never actually wired up (no postcss.config.mjs anywhere) -- added it as part of building the design token system. Also found and fixed a completely unconfigured Vitest path alias. — Both were genuine blocking gaps for this plan's own deliverables (globals.css's first @import line, and the i18n parity test's own @/ imports), not scope creep -- discovered only because this plan was the first to actually exercise either piece of tooling.
- [Phase 01]: Wired every UI-SPEC page (homepage, catalogue, detail, collection, profile, sources) to real backend data via GameCard/LibraryControls/RecommendationStrip, adding two new backend endpoints (MyLibraryView, SourcesView) the plan's file list didn't explicitly name but the pages genuinely needed to function. — Ten requirements (AUTH-01, PROF-02, CAT-01, CAT-03, CAT-06, LIB-01, LIB-02, INV-01, INV-02, REC-02) reached their last declaring plan here and are now marked complete -- the E2E suite proves rating and multi-copy persistence across a reload, not just the status field the earlier tracer plan covered, which is what closes out LIB-01/LIB-02/INV-01/INV-02 for real rather than by inference.
- [Phase 01]: Injected axe-core's already-approved local bundle directly via page.addScriptTag instead of adding the @axe-core/playwright wrapper package — Avoids a new-dependency approval round for what is functionally one line of glue code around an already-approved devDependency
- [Phase 01]: Introduced DJANGO_DEPLOY_ENV (local|production) to make check --deploy genuinely clean in each context via SILENCED_SYSTEM_CHECKS, instead of always showing expected-but-scary HTTP-only warnings — An explicit, required switch is auditable in a way that inferring the security profile from DEBUG or DATABASE_URL is not
- [Phase 01]: check-secrets.ps1 exempts only e2e/fixtures/hostile.json (holds the self-test canaries) and test files (assigned-secret-value/bearer-token patterns only) by path, never any file by content — Synthetic, reviewed fixture credentials are a normal testing pattern; a narrow, documented path exemption keeps every other file -- including README.md and .env.example -- genuinely scanned
- [Phase 01]: Pivoted the deployment topology mid-plan from a single-PaaS assumption to Vercel Hobby (web) + Render Free (api) + Neon Free (db), no card — Render Free's Docker-only model does not host two independently-scaled services plus a managed Postgres for free; the pivot keeps the same same-origin-proxy security architecture across two separately-hosted services
- [Phase 01]: Found and fixed three real deploy-path bugs (missing docs/ in the API image, non-portable random GameWork.id in the demo seed, /health/ redirected by Next.js middleware) plus a Vercel Hobby private-repo commit-author gotcha, each only visible against genuinely fresh infrastructure — The long-lived local dev Postgres volume masked two of these for the whole session; testing against a throwaway fresh container before every push is now the standing verification pattern for any fresh-database code path
- [Phase 01]: Deliberately left QUAL-03 open despite the tool reporting it structurally ready to mark complete -- the sign-off document explicitly states 400% zoom reflow and a screen-reader pass are still unverified manual checklist items — Marking a requirement complete when its own sign-off evidence names an open gap would misrepresent the actual state; readiness-to-mark-complete is structural (all declaring plans have summaries), not a substitute for checking the requirement's real acceptance criteria
- [Phase 01]: Phase 1 (Three-Day Public Demo Slice) ACCEPTED by the author, 2026-09-05, against commit 1af981e at https://save-point-orpin.vercel.app — All five ROADMAP success criteria linked to evidence in docs/verification/phase-01-signoff.md; two named open limitations (400% zoom, screen reader) stated rather than hidden
- [Phase 01.1]: IGDB v4 chosen as the real-scale catalogue source (ADR-006, DATA-04), over RAWG and scaled Wikidata, from a live authenticated probe (2026-09-05): 374,555 total games, 312,418 primary (game_type = 0), no monthly quota, 4 req/s + 8 concurrent. Import boundary is game_type = 0 only; covers are hotlinked to images.igdb.com (not mirrored) with the Phase 1 first-party placeholder as fallback; Phase 1's Wikidata offline corpus and the no-runtime-provider rule are retained. `requests==2.34.2` pinned (author-approved, PyPI-verified real release); django-allauth/dj-rest-auth explicitly rejected. The Twitch DSA (24h cache, no redistribution) is reconciled against IGDB's own API FAQ (store + serve permitted, keep after termination) treated as the "written authorization otherwise" the DSA contemplates — a reasoned position recorded verbatim for the thesis, not legal advice.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1 must fit the three-day demo constraint; keep seeded accounts/catalogue and popularity logic intentionally thin.
- Phase 2 must freeze the evaluation protocol before sophisticated recommender comparisons.
- Dataset and enrichment-provider legal terms require case-specific confirmation before adoption. — IGDB terms captured verbatim and reconciled in ADR-006 / docs/verification/igdb-api-probe.md §5 (2026-09-05). The FAQ-vs-DSA reading is a reasoned position for the author to accept, not legal advice; RAWG/Wikidata terms remain as previously recorded.
- Plan 01-04 (Wave 5) is mid-execution and paused on a real blocker: the frontend (apps/web) was scaffolded in Plan 01-03 WITHOUT @types/react or @types/react-dom in devDependencies. Re-enabling TypeScript build-error checking (next.config.ts's ignoreBuildErrors:true was itself a bug, now removed) surfaces this immediately -- every .tsx file in apps/web fails to type-check (useState/FormEvent not found on 'react', JSX.IntrinsicElements missing, react/jsx-runtime has no types).

Per project policy (01-01's package-legitimacy gate; deviation Rule 3's explicit exclusion for package-manager installs), a new dependency install requires human sign-off, not an agent's unilateral pnpm add -- even though @types/react and @types/react-dom are about as standard/low-risk as a package gets.

WHAT'S DONE (committed, tested, working): apps/api/accounts/{views,urls}.py + test_auth.py (7/7 passing), apps/api/library/{views,urls}.py + test_entry.py (8/8 passing), config/urls.py wiring, infra/compose.yaml port mappings (web:3000, api:8000) and demo env vars. Full backend suite: 62/62 passing.

WHAT'S UNCOMMITTED (working tree, not yet type-checked clean): apps/web/app/[locale]/** (layout, homepage, login page, catalogue page, game detail page + StatusControl), apps/web/lib/api.ts, apps/web/middleware.ts, apps/web/next.config.ts (rewrite proxy to Django + ignoreBuildErrors removed), and the deletion of the old flat apps/web/app/layout.tsx + page.tsx (replaced by the [locale] structure).

TO RESUME: get the user's explicit approval, then `pnpm add -D @types/react@<version matching react 19.2.7> @types/react-dom@<matching>` at the repo root (deps are hoisted there, see package.json), run `pnpm exec tsc --noEmit` in apps/web to confirm the errors clear, then continue: verify the dev server actually renders each page, write/run the e2e/demo-journey.spec.ts real login journey (replacing the 01-15 skip block), run the plan's two <verify> commands, then close out Plan 01-04 (SUMMARY.md, STATE/ROADMAP/REQUIREMENTS updates) exactly like 01-05/01-06/01-15 before it.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| Hardening | Production-strength controls beyond the Phase 1 demo boundary | Planned | Roadmap creation | v1 |

## Session Continuity

**Stopped at:** Plan 01.1-02 merged to `main` (`507f876`, pushed; issue #8 closed; worktree removed; 39 catalogue tests green post-merge). Now: Wave 3 = plan 01.1-06 (redesign, author pre-approved) + a background load of `savepoint-db-1` with the IGDB catalogue.

**Author is remote (on mobile), at-the-helm delegation in effect.** Pre-approvals recorded below in this section's history and in `.continue-here.md`. Stop for the author only on: a genuine 01.1-06 design ambiguity, the deploy phase, anything destructive, or a failure. Mobile push is OFF in the author's /config — leave decision messages in the conversation.

### Pre-approved, in flight

- **A — Plan 01.1-06 (Wave 3 redesign):** approved to run now. Task 1 (checkpoint "approve the UI-SPEC") is satisfied — `01.1-UI-SPEC.md` is checker-VERIFIED 7/7 ×3, `status: approved`. Before Task 2, ADD a per-surface coverage matrix to the UI-SPEC (rows: catalogue / detail / registration / recommendations, each naming desktop + mobile + accessibility + an explicit "approved" verdict) — the plan's Task 1 `<verify>` PowerShell gate greps for exactly that and the current spec lacks it. Then Task 2: implement across `apps/web` (globals.css tokens light+dark, AppShell navbar w/ ThemeToggle + login icon, GameCard w/ StatusPill/ScorePill/StarRating, catalogue, detail, NEW recommendations page, NEW register page visual/form-only) + collection + login per the post-approval additions (note the scope addition in the SUMMARY — they are not in the plan's `files_modified`). Verify: `pnpm --dir apps/web run build` passes. Brand assets are staged at `design/brand/` — wire per `design/brand/README.md` checklist (favicon route, AppShell brand, opengraph-image, drop the "02 / CRISTAL" round label).
- **B — Persistent catalogue load:** approved. Run the now-merged `import_igdb_catalogue` against the real dev DB `savepoint-db-1` in the background (~1–1.5h; must coexist with the existing 150-game `source="wikidata"` corpus + demo accounts/library — watch for coexistence bugs), then `pg_dump` a reusable snapshot (NOT a committed bulk file — ADR-006). This load also produces the deferred deterministic sample manifest for `igdb-catalogue-freeze.md`. Deployed Neon load deferred to the deploy phase (check free-tier size for ~312k rows then).

Last session: 2026-09-05T21:05:00Z

### Done this session (all merged + pushed to `origin/main` through `507f876`)

- **01.1-01** — ADR-006 (IGDB source, DATA-04), authenticated probe evidence, `requests==2.34.2` pinned; issue #7 closed; DATA-04 + CAT-02 Phase-4 duplicate traceability rows removed (author-confirmed leftovers). Also fixed the Windows GSD hook-shell bug.
- **01.1-02** — `Genre` model + `GameWork.genres` M2M + `IgdbImportRun` monotonic-cursor checkpoint; `IgdbClient` + `import_igdb_catalogue` (id-cursor batched atomic + advisory lock, checkpoint-after-commit, ADR-006 normalization, content checksum, cover accounting); fresh disposable-DB acceptance run — **312,463 primary works**, floor 281,200 cleared, SIGKILL interrupt + resume + idempotent convergence proven, aggregate freeze evidence in `docs/verification/igdb-catalogue-freeze.md`. Issue #8 closed. 39 catalogue tests green post-merge. The gsd-executor was stopped mid-finalization; the orchestrator completed Task 3 evidence + SUMMARY from the agent's reported values. **Sample-review manifest deferred** to the persistent-DB load (encoding fault ate the disposable-run JSON).
- **Wave 3 prep** — `01.1-UI-SPEC.md` checker-VERIFIED 7/7 ×3, `status: approved`; 4 design decisions author-ratified (light+dark theme w/ SSR cookie toggle; ~156px grid no list-toggle; tiered ScorePill + gold personal stars; genre shelves for REC-10); Collection screen + navbar person-icon login added on author direction; 6 mockups in `mockups/`.
- **Brand** — author's "Cristal" identity staged at `design/brand/` (mark/lockup/favicon/OG-banner × dark+light + mono; mojibake repaired). NOT wired to the app; `design/brand/README.md` has the 01.1-06 integration checklist.

Resume file: `.planning/phases/01.1-real-scale-catalogue-and-product-experience/.continue-here.md` (full state + the A/B pre-approvals + ordered next actions).
