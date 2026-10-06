# Phase 1 sign-off: Three-Day Public Demo Slice

**Status: ACCEPTED** by Felipe (author), 2026-09-05, against commit `1af981e1c97f2c46bf07671ad1ec13fe7461bf7a`, deployed at `https://save-point-orpin.vercel.app` (API: `https://savepoint-api-37nz.onrender.com`).

This document is the final human acceptance of Phase 1 per `.planning/phases/01-three-day-public-demo-slice/01-14-PLAN.md`. It links the automated evidence, the author's manual walkthrough, and the author's own forward-looking decisions. It does not hide or soften any limitation to present the demo as more complete than it is.

## Automated evidence (this session, same commit)

| Check | Command | Result |
|---|---|---|
| Full Playwright suite | `corepack pnpm exec playwright test` | 32 passed, 1 skipped (deployed-smoke skips without live `BASE_URL`; verified separately below) |
| Secret scan | `powershell -File scripts/check-secrets.ps1` | PASS — 3145 Git files, 225 build files, 2 images, ~16KB logs scanned, zero non-allowlisted matches |
| Evidence/ledger integrity | `powershell -File scripts/check-evidence.ps1` | PASS — 5 ADRs, 15 ledger entries, schema/types/actors/paths/hashes/coverage/secret-scan all valid |
| Deployed smoke (real URL) | `playwright test e2e/deployed-smoke.spec.ts` against `https://save-point-orpin.vercel.app` | PASS, 2026-09-05T10:00Z, commit `ff5aa2ee7ae460f780187f1fc13298bfb2e12fbe` confirmed identical on Render's and Vercel's `/health/` |

Note: the deployed smoke's confirmed commit (`ff5aa2e...`) predates this document's own commit (`1af981e...`, which only touches docs/ledger/test-robustness files, not application code) — no app-code change happened between the smoke and this sign-off.

## ROADMAP success criteria (Phase 1)

1. **A visitor can open the public deployment, sign in, search the local catalogue, and inspect a game with source info offline.** — Verified: deployed smoke's login → catalogue → detail journey; `docs/sources` page backed by `SourcesView`; catalogue import is offline-only (no runtime provider calls, confirmed by static analysis in Plan 01-11).
2. **A signed-in user can change status, rate, and register copies while ownership stays private.** — Verified: `e2e/demo-journey.spec.ts` (rating + two copies survive reload); `PublicProfileView`'s hand-built allowlist serializer (Plan 01-04).
3. **An authorised visitor can see a popularity recommendation from demo data.** — Verified: `library/popularity.py::rank_popularity_v1()`, self-verified against `data/demo/seed-v1.json`'s checksummed expected results on every seed load.
4. **A clean machine starts the demo offline from pinned instructions, no secret anywhere.** — Verified: Plan 01-11's fresh-database `docker compose up --build --wait` run; `scripts/check-secrets.ps1` PASS above.
5. **Keyboard-usable, responsive, and thesis evidence (source/legal, architecture, agent inputs/outputs, verification, limitations, author decisions) captured.** — Verified: `e2e/a11y.spec.ts` (26 tests); `docs/adr/ADR-*.md` (5 ADRs); `docs/methodology/agent-ledger.jsonl` (15 entries, PASS above).

## Author's manual walkthrough

The author confirmed, against the live public URL: the full journey (homepage, login, search, game detail/provenance, status, rating, copies, collection, public profile, popularity, logout) works correctly. No blocking defect was found.

**Reused from Plan 01-10's automated coverage** (not re-walked by hand this session, per that plan's own honest boundary): the ES/EN × mobile/desktop axe scans and the full keyboard-only journey are covered by `e2e/a11y.spec.ts`.

**Open, explicitly not re-verified by the author this session** (carried over from Plan 01-10's manual checklist, `docs/verification/phase-01-manual.md`):
- Reflow at 400% zoom
- A basic screen-reader pass (NVDA/VoiceOver)

These remain the only two unchecked boxes in `docs/verification/phase-01-manual.md`. They do not block this sign-off because the automated axe/keyboard/reflow-at-320px coverage already gives strong (if not exhaustive) accessibility evidence, and the author judged the demo acceptable to sign off with this specific, named limitation rather than an unstated gap.

## Author decisions and next steps (recorded for the thesis)

The author accepted Phase 1 as delivered and requested an immediate follow-up phase, prioritized as follows (author's own ordering, not the agent's default):

1. **Mass catalogue import + interface redesign** (first priority)
2. Real login system with preloaded users (second priority)
3. Catalogue sorting/filtering (by platform, genre, etc.) and search filters (scope to be confirmed during that phase's planning)
4. An independent recommendations page (by genre / user taste)

**Data source decision:** IGDB was chosen over RAWG or scaling the existing Wikidata pipeline for the mass catalogue import. The author explicitly noted that complete cover-image coverage across the full catalogue matters and may be delivered incrementally after the initial import, without blocking the rest of that phase's work. This decision, and its rationale, is recorded here for the thesis's decision log and will be elaborated in that phase's own ADR once planned.

These are **improvements for a new phase**, not defects in Phase 1's own delivered scope — Phase 1's own five success criteria (above) are all met by what already exists.

## Limitations (stated, not hidden)

- The demo's catalogue (150 games) and account model (one demo account) are intentionally small, matching Phase 1's own three-day controlled-demo scope; the new phase addresses this directly.
- Render's free tier sleeps after 15 minutes of inactivity (documented in `docs/deployment/public-demo.md`); a visitor may see a ~1-minute cold-start delay.
- 400% zoom reflow and a screen-reader pass remain open manual checklist items (see above).
- `docs/methodology/agent-ledger.jsonl` records one genuinely unrecoverable historical artifact reference (an intermediate draft of `scripts/check-secrets.ps1` from a different agent run that was overwritten before being committed) — disclosed honestly in that entry's `unverifiable_inputs`/`limitations` fields rather than hidden or falsified.

---
*Signed off: 2026-09-05*
*Commit: `1af981e1c97f2c46bf07671ad1ec13fe7461bf7a`*
