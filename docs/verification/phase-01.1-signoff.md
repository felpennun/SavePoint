# Phase 01.1 sign-off: Real-Scale Catalogue and Product Experience

**Status: CONDITIONALLY ACCEPTED** by Felipe (author), 2026-09-06, against commit `2d49fc8df2beaf7fb741a68c9f835b7f51f57295`.

Not deployed — every plan in this phase is merged to `origin/main` and runs only on the
local `docker compose` stack (see *Deployment status* below).

This document is the phase-close record for Phase 01.1, the author-requested real-scale
follow-up to Phase 1 (which is separately signed off in
`docs/verification/phase-01-signoff.md`). It links the automated evidence, the phase
goal-verification, and the author's own decisions. It does not soften the one partial
success criterion or the carried limitations to present the phase as more complete than it
is.

## Nature of this acceptance

The phase's human product-quality gate (QUAL-05 / D-07, Plan 01.1-07) was closed as a
**conditional advance author approval**. On 2026-09-06, before going offline, the author
explicitly authorised APPROVED for all four D-07 surfaces (catalogue, game detail,
registration, recommendations) at desktop and mobile, conditioned on the automated
evidence passing — which it did. The approval was made against the in-session screenshot
set, **not** a full live per-viewport walkthrough; that walkthrough is deferred by author
choice, with the stated intent to run a dedicated design-refinement pass once functionality
is complete and to expect UI changes regardless. This is recorded verbatim in
`docs/verification/phase-01.1-product-review.md` → `## Author Review`, and in
`.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-07-SUMMARY.md`.

## Automated evidence (this session, at or near commit `2d49fc8`)

| Check | Command | Result |
|---|---|---|
| Backend test suite | `docker compose -f infra/compose.yaml run --rm api pytest apps/api -q` | passing (accounts demo-identity, catalogue search/filter/sort, recommendations heuristic, importer) |
| Frontend build | `pnpm --dir apps/web run build` | success, no type/build error (Next 16.3.4 + React 19 + TS + Tailwind v4) |
| Frontend unit / i18n parity | `pnpm --dir apps/web test` | 16 passed (includes EN/ES message-key parity) |
| Product Playwright + axe | `pnpm exec playwright test e2e/a11y.spec.ts e2e/demo-journey.spec.ts --project=chromium` | 41 passed across 3 consecutive runs; axe zero critical/serious on catalogue, detail, registration, recommendations (plus homepage/login/sources) at desktop 1280×800 and mobile 375×812 |
| Screenshot artifacts | committed under `e2e/artifacts/phase-01.1/` | 8 files — catalogue / detail / registration / recommendations × desktop / mobile |
| Product-review structure gate | `powershell -File` regex over `docs/verification/phase-01.1-product-review.md` | PASS — `Playwright verdict: PASS`, `axe verdict: PASS`, bounded 8-row Screenshot Artifacts table, per-surface desktop+mobile PASS |
| Author-review gate | `powershell -File` regex (Plan 01.1-07 Task 2) | `AUTHOR-REVIEW GATE: PASS` |
| Secret scan | `powershell -File scripts/check-secrets.ps1` | PASS exit 0 — running containers/images/logs + tree scanned, zero non-allowlisted secret-shaped matches |
| Real-scale catalogue load | `docs/verification/igdb-catalogue-freeze.md` + `.sample.json` | 312,483 IGDB primary works (`game_type = 0`) loaded into dev DB alongside the 150-work Wikidata corpus; content checksum `ff3d67525c92…`, aggregate coverage, 300-row deterministic sampled-review manifest; `GET /api/catalogue/games/` → `count: 312633` |
| Dependency policy | `powershell -File scripts/check-dependencies.ps1` | PASS — only `requests==2.34.2` added this phase, pinned + legitimacy recorded |

## Success criteria

Full detail:
`.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-VERIFICATION.md`
(`status: gaps_found`, `score: 4/5`).

| # | Criterion | Verdict |
|---|---|---|
| SC1 | Real-scale IGDB-sourced catalogue with documented licence/attribution and per-work provenance | **VERIFIED** — 312,633 works; ADR-006 DATA-04 comparison; `docs/verification/igdb-api-probe.md` redacted probe evidence with verbatim DSA + IGDB FAQ terms; sources API + game-detail provenance |
| SC2 | Sort and filter the catalogue by platform, genre and other metadata | **VERIFIED** — `parse_catalogue_query` allowlists `platform` / `genre` / `year_from` / `year_to` / `min_rating` + a 6-key `sort` set, each with a `canonical_slug` tie-break; hostile / off-list input → bounded 400; facet DTO with no N+1; URL-shareable `FilterBar`; migration `0004` adds the scalar fields + 4 indexes |
| SC3 | Multiple distinct preloaded accounts each sign in and out independently | **PARTIAL** — `DemoAccountIdentity` + `bootstrap_demo_accounts` (env-only `DEMO_ACCOUNTS` JSON, `validate_password`, advisory lock, all-or-nothing) are built and tested and were proven live in `savepoint_test`; but no running environment activates the plural seed — `infra/compose.yaml` and `apps/api/render-start.sh` still call the singular `bootstrap_demo_account`, and no `DEMO_ACCOUNTS` is set. The live product exposes one preloaded account. Deferred — see below. |
| SC4 | Interface reads as a professional cataloguing product | **VERIFIED (conditional author approval)** — first-party light/dark CSS-variable token system with no-flash SSR `sp-theme` cookie; `ThemeToggle`; `ScorePill` / `StatusPill` / `StarRating` / `CoverImage` / `FilterBar`; all D-07 surfaces redesigned; `01.1-UI-SPEC.md` checker-VERIFIED 7/7; Playwright 41 pass + axe clean + 8 screenshots |
| SC5 | Dedicated recommendations page: genre suggestions from the user's own activity, distinct from the popularity baseline | **VERIFIED** — `rank_genre_taste_v1`, a stateless per-request heuristic that **never** falls back to popularity (D-09), with `input_snapshot_sha256` and a distinct `insufficient_history` shape; `RecommendationsView` is `IsAuthenticated`; ADR-007 documents it as a heuristic and explicitly **not** the thesis ML contribution; auth-gated web page with algorithm + limitation disclosure and an authenticated-only nav link |

**Phase verdict:** 4/5 criteria VERIFIED, 1 PARTIAL. The phase substantially achieves its
goal; the one gap is a runtime-wiring step with a documented follow-up, not missing
capability.

## Named limitations carried out of this phase

Recorded in
`.planning/phases/01.1-real-scale-catalogue-and-product-experience/deferred-items.md`:

1. **SC3 — plural preloaded accounts not wired into any runtime.** The mechanism is built
   and tested; activating it needs `bootstrap_demo_accounts` to *reconcile* the
   pre-existing `demo-visitor` user under `LEGACY_ANCHOR_KEY` — the same "coexist with
   existing state" pattern as `fix(01.1-02)`. A close-out attempt to wire it directly
   aborted with `SeedContractError` against the existing dev DB and was reverted. This is a
   small follow-up plan (reconcile-then-wire), not new design work.
2. **`total_rating` is NULL on all 312,633 rows.** No prior source carried it; the importer
   now captures it but has not been re-run. The "Minimum IGDB rating" filter and the
   `rating_desc` sort are contractually correct but currently inert.
3. **`first_release_date` is populated for roughly 75% of rows** (backfilled from releases
   via a correlated subquery in migration `0004`; rows with no dated release stay NULL).
4. **The recommendations page shows the onboarding / `insufficient_history` state** for the
   demo account and freshly registered accounts, which have no genre-bearing library
   history in the seeded dev DB. The personalised ranking itself is deterministically
   unit-tested.
5. **Authenticated top navigation overflows horizontally below ~430px** (shared chrome, not
   a single surface). Needs a mobile-chrome-density design decision.
   (`deferred-items.md` → `### D-01.1-10-a`.)
6. **Game-detail page reads a little sparse** — conditional genre chips; the cover could be
   larger / more dominant. Cosmetic.
7. **Full live per-viewport author walkthrough is outstanding** by author choice (see
   *Nature of this acceptance*).

## Deployment status

**Nothing from Phase 01.1 is deployed.** No deploy command was run during this phase. All
merged work is on `origin/main`. The Phase 1 public demo
(`docs/verification/phase-01-signoff.md`, `https://save-point-orpin.vercel.app`, API
`https://savepoint-api-37nz.onrender.com`, commit `1af981e`) still serves the pre-redesign
UI against the 150-work Wikidata catalogue.

Deploying Phase 01.1 would require, as a separate and explicit author decision:

- pushing the redesigned `apps/web` frontend;
- applying this phase's new migrations (genre + IGDB import fields, and
  `catalogue/0004_catalogue_filter_sort_fields`);
- loading the deployed database with the IGDB catalogue (~312k rows) — **check the hosting
  tier's size limit first**; a 93 MB `pg_dump` of the loaded dev DB is at
  `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (gitignored) as a restore
  path;
- deciding whether to also re-run the importer to populate `total_rating`.

Because roughly twenty pushes to `main` happened this session, the Vercel and Render
dashboards should be checked for auto-triggered builds against the still-unloaded
production database before any deploy decision.

## Author decisions and next steps (recorded for the thesis)

- The author accepted Phase 01.1 as delivered, **conditionally**, and asked for the phase
  to be closed autonomously (2026-09-06) with checkpoints, a full-repo review, and a
  conservative cleanup.
- The cosmetic items (game-detail density, authenticated top-nav overflow, recommendations
  onboarding state) are for a **dedicated design-refinement pass** once functionality is
  complete; the author explicitly expects UI changes regardless of whether the phase closes
  now.
- The SC3 wiring gap is for a **small follow-up plan**.
- **Deployment** is a separate decision the author will make when reviewing this package.
- Phase 2 (Governed Corpus and Frozen Evaluation Contract) is **not** started.

## Reversibility

Every plan in this phase is a discrete commit on `main`, pushed. The phase-complete state
is tagged `phase-01.1-complete` at commit `2d49fc8`. The dev database can be restored from
`data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` via `pg_restore` in minutes.

---
*Signed off: 2026-09-06 (conditional advance approval)*
*Commit: `2d49fc8df2beaf7fb741a68c9f835b7f51f57295`*
*Phase 1.0 sign-off (separate, already accepted): `docs/verification/phase-01-signoff.md`*
