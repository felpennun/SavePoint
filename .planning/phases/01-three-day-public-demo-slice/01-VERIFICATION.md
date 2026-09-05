---
phase: 01-three-day-public-demo-slice
verified: 2026-09-05T11:15:00Z
status: human_needed
score: 5/5 roadmap success criteria verified (23/23 requirement IDs traced; 2 tracking-only items flagged below)
behavior_unverified: 0
overrides_applied: 2
overrides:
  - must_have: "The demo is keyboard-usable and responsive at desktop/mobile widths -- reflow at 400% zoom"
    reason: "Genuinely requires a human at a real 400% browser zoom level; no automated proxy honestly substitutes. Author explicitly reviewed and accepted the demo with this named limitation open rather than hiding it (docs/verification/phase-01-signoff.md, docs/verification/phase-01-manual.md)."
    accepted_by: "Felipe (author, phase-01-signoff.md)"
    accepted_at: "2026-09-05"
  - must_have: "The demo's thesis evidence includes a basic screen-reader pass (NVDA/VoiceOver)"
    reason: "Genuinely requires a human with a real screen reader; automated axe scanning is strong complementary evidence but not a substitute. Author explicitly reviewed and accepted the demo with this named limitation open rather than hiding it."
    accepted_by: "Felipe (author, phase-01-signoff.md)"
    accepted_at: "2026-09-05"
re_verification:
  previous_status: none (initial verification)
human_verification:
  - test: "Decide whether DATA-01/DATA-02 should be marked Complete in .planning/REQUIREMENTS.md, or given an explicit deferral rationale (as QUAL-03 has)."
    expected: "REQUIREMENTS.md's traceability table state matches the actual evidentiary and editorial intent for these two requirements."
    why_human: "Plans 01-05 and 01-13 both self-declare `requirements-completed: [DATA-01, DATA-02]` in their SUMMARY frontmatter, and substantive evidence exists (docs/verification/catalogue-freeze.md, docs/adr/ADR-003-data-sources.md, data/manifests/catalogue.json's checksum/licence/retrieval-date fields) -- yet REQUIREMENTS.md still lists both as Pending, unlike QUAL-03 whose Pending status is explicitly and separately justified in the sign-off. This looks like an unresolved bookkeeping gap rather than a documented editorial decision; only the author/thesis owner can say which it is."
  - test: "Correct or clarify the sign-off's claim in docs/verification/phase-01-signoff.md ('These remain the only two unchecked boxes in docs/verification/phase-01-manual.md') against the actual state of that document."
    expected: "The sign-off accurately describes the manual checklist's state for thesis-evidence purposes."
    why_human: "Independent inspection of docs/verification/phase-01-manual.md shows every checkbox in every section is unchecked (`- [ ]`), not just the two in 'Reflow at 400% zoom' and 'Basic screen-reader pass'. This is consistent with Plan 01-10's own documented decision not to mechanically check boxes even for sections its automated suite covers (reserving checkbox confirmation for a human reviewer) -- but the sign-off's specific phrasing overstates how much of the checklist was actually closed out by checkbox, which matters for a thesis document meant to be reproduced/audited by a reviewer."
---

# Phase 1: Three-Day Public Demo Slice Verification Report

**Phase Goal:** A tribunal visitor can use a visible, lawful SavePoint vertical slice online within three days, while the same controlled demo starts reproducibly offline.
**Verified:** 2026-09-05T11:15:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

**Note on phase mode:** ROADMAP.md marks this phase `Mode: mvp`, but its `Goal:` field is a narrative sentence, not a `"As a ___, I want ___, so that ___."` user story (`gsd_run query user-story.validate` returns `valid: false` for it). Per the MVP-mode gate this would normally require refusing verification and requesting a re-run of `/gsd mvp-phase 01`. Given this is a retroactive, goal-backward verification of an already-signed-off phase, explicitly directed by the orchestrator to check the phase's own five ROADMAP Success Criteria against the codebase and cross-reference the 23 stated requirement IDs, I proceeded with standard goal-backward verification using those five Success Criteria as the observable truths, rather than blocking on the story-format mismatch. Flagging this here so it is not silently absorbed: ROADMAP.md's goal field for this phase should either be rewritten to the mandated user-story shape or the phase's mode should be corrected, before the next MVP-mode phase inherits the same non-conforming pattern.

## Independent verification performed (not just SUMMARY-reading)

- Read all 16 `01-*-PLAN.md` files (must_haves, requirements, prohibitions) and all 16 `01-*-SUMMARY.md` files.
- Read `.planning/REQUIREMENTS.md`, `docs/verification/phase-01-signoff.md`, `docs/verification/phase-01-manual.md`.
- Confirmed git history: HEAD is `786889d` ("Phase 1 human sign-off — ACCEPTED"), one commit past the sign-off's own cited `1af981e`. Diffed `ff5aa2e` (the commit the deployed smoke actually confirmed live) against HEAD — zero changes to `apps/`, `infra/`, or the demo-journey/a11y e2e specs. The sign-off's claim that "no app-code change happened between the smoke and this sign-off" is independently confirmed true.
- Independently hit the live public deployment (not trusting the sign-off's own record of having done so): `https://savepoint-api-37nz.onrender.com/health/` → `200 {"status":"ok","commit":"ff5aa2e..."}`; `https://save-point-orpin.vercel.app/` → `307` to `/es`; `/es`, `/es/catalogue`, `/es/login` all → `200` with real, non-empty, non-placeholder HTML (titles "SavePoint", catalogue grid text, Spanish login labels "Usuario"/"Contraseña"); grepped fetched pages for secret-shaped strings — none found.
- Ran `scripts/check-evidence.ps1` myself: **PASS** — 5 non-vacuous ADRs, fail-first canaries reject invalid type/hash, 16 ledger entries valid (schema/types/actors/paths/hashes/coverage/secret-scan).
- Ran `scripts/check-secrets.ps1` myself: Git-tracked-file phase (3147 files) and Docker-image-layer phase (2 images) both scanned clean; the two container-dependent phases (Next.js build output, captured compose logs) reported `FAIL` only because no `docker compose up` stack is currently running in this environment — an environmental limitation of this verification session, not a code defect (the sign-off's own same-day, same-commit run already exercised all four surfaces non-emptily with zero non-allowlisted matches).
- Read and independently assessed the actual implementation (not the summaries' description of it) for: `apps/api/accounts/serializers.py` (public-profile allowlist), `apps/api/library/popularity.py` (popularity-v1), `infra/render.yaml` (Blueprint secret-freedom), `.env.example`-adjacent grep for hardcoded `DEMO_PASSWORD` literals (none found).
- Grepped `apps/api` for `requests.|httpx.|urllib.request|fetch(` outside tests/tooling — zero matches, independently confirming the OPS-03/CAT-06 "no runtime external call" claim rather than trusting the SUMMARY's own grep.
- Counted actual test functions in every backend test file and every e2e spec against the numbers claimed in SUMMARY.md files — all counts matched exactly (e.g., `e2e/a11y.spec.ts`'s 5 literal `test(` call sites times its `for` loops over 2 locales × 2 viewports × 5 pages produce the claimed 26 executed tests; read the full file to confirm this, not just grep count).
- Scanned all modified files for `TBD`/`FIXME`/`XXX`/`TODO`/placeholder patterns — none found.
- Diffed the currently-uncommitted `.planning/REQUIREMENTS.md` change to confirm what this session's close-out actually flipped (OPS-01, DOC-01, AGENT-01/02/03 → Complete) versus what it left untouched (DATA-01, DATA-02, QUAL-03 stayed Pending both before and after).

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A visitor can open the public deployment, sign into a controlled account, search a small lawful local catalogue, and inspect a game with source information even when external enrichment is unavailable. | ✓ VERIFIED | Live: `/health/` (API) returns `200` with matching commit; `/es`, `/es/catalogue`, `/es/login` return real rendered HTML. Code: `apps/api/catalogue/views.py`/`search.py` (tolerant exact→prefix→trigram search, zero external calls -- grep-confirmed independently), `SourcesView`/`sources` page backed by `SourceRecord`/`AssetAttribution` rows from the frozen Wikidata/Commons import (`docs/verification/catalogue-freeze.md`, `docs/adr/ADR-003-data-sources.md`). `apps/api/accounts/views.py` implements real Django session login/logout with pre-session CSRF enforcement (`apps/api/accounts/tests/test_auth.py`, 7 tests). |
| 2 | A signed-in user can change backlog status, rate a game, and register multiple physical or digital copies while private ownership details remain absent from the public profile. | ✓ VERIFIED | `apps/api/library/services.py`/`models.py`: rating is a nullable 1-10 integer with a DB CheckConstraint (`test_rating.py`, 7 tests); `OwnedCopy` idempotent-by-key creation, cross-table release/edition membership validated at service layer (`test_copies.py`, 8 tests). `apps/api/accounts/serializers.py::build_public_profile()` is a hand-built allowlist (`alias`, `activity`, `summary` only) -- independently read in full; it never touches `OwnedCopy`, ratings, email, or internal IDs, and is verified by a recursive-denylist + hostile-fixture XSS test (`test_public_profile.py`, 6 tests). |
| 3 | An authorised visitor can open a public profile and see a simple popularity recommendation produced from the demo data. | ✓ VERIFIED | `apps/api/library/popularity.py::rank_popularity_v1()` independently read in full: deterministic weighted aggregate over already-committed `LibraryEntry` rows, UUID tie-break, SHA-256 self-check of its own output, explicit non-personalization `limitation` string always present in the DTO (`test_popularity.py`, 9 tests incl. real concurrent read-during-write). `data/demo/seed-v1.json` + `seed_demo.py` self-verify against 6 checksummed expected popularity-v1 results on every load. |
| 4 | A clean machine can start the same demo from documented, pinned instructions without Internet/API dependency, and no secret appears in Git, browser assets, logs, images, or public artifacts. | ✓ VERIFIED | `infra/compose.yaml` wires `migrate → import_catalogue → bootstrap_demo_account → seed_demo → runserver` with healthchecks (previously verified end-to-end by the executor per 01-11-SUMMARY.md; this session independently re-ran the Git-tracked-file and Docker-image-layer phases of `scripts/check-secrets.ps1`, both scanned non-emptily and clean -- the two container-dependent phases only failed here because no stack is currently running, not because of a code defect). `infra/render.yaml` independently read: every credential is `sync: false` or `generateValue: true`, zero literals. Grep for `DEMO_PASSWORD\s*=\s*['"]` across tracked `.py`/`.ts`/`.yaml` returns nothing outside tests. Zero outbound-HTTP call sites in `apps/api` runtime code (independently grepped). |
| 5 | The demo is keyboard-usable and responsive at desktop/mobile widths, and its source/legal record, architecture rationale, agent inputs/outputs, verification, limitations, and author decisions are captured as thesis evidence. | ✓ VERIFIED, with 2 named overrides | `e2e/a11y.spec.ts` independently read in full (not just grep-counted): 2 locales × 2 viewports × 5 pages of axe scans + 4 overflow checks + 1 reduced-motion check + 1 full keyboard-only journey = 26 tests, matching the claimed count exactly. `docs/adr/ADR-001..005` independently read (ADR-003 in full): each cites real sources, alternatives, checksums, and reversibility. `docs/methodology/agent-ledger.jsonl` independently parsed: 16 valid JSON lines, types `{proposal:4, automated-check:8, author-decision:4}`, matching the ledger's own claimed separation of contribution vs. authorship. `scripts/check-evidence.ps1` re-run by this verifier: PASS. **Two explicitly-named, human-accepted open items remain** (400% zoom reflow; NVDA/VoiceOver screen-reader pass) -- see overrides above; these were never hidden by the author's sign-off. |

**Score:** 5/5 roadmap success criteria verified (2 sub-items carried as accepted overrides, not silent passes).

### Requirements Coverage

All 23 requirement IDs assigned to this phase in ROADMAP.md are claimed by at least one of the 16 plans' `requirements:` frontmatter; no orphaned requirements found (full union of all 16 plans' `requirements:` fields exactly equals the 23-ID list).

| Requirement | REQUIREMENTS.md status | Evidence | Verdict |
|---|---|---|---|
| AUTH-01 | Complete | `bootstrap_demo_account` (11 tests), real login/logout (`test_auth.py`, 7 tests), live login page renders | ✓ SATISFIED |
| PROF-02 | Complete | `PublicProfileSerializer`/`build_public_profile()` allowlist, 6 tests | ✓ SATISFIED |
| CAT-01 | Complete | Tolerant exact→prefix→trigram search, 9 tests | ✓ SATISFIED |
| CAT-03 | Complete | Detail endpoint carries provenance/hierarchy, 5 tests | ✓ SATISFIED |
| CAT-04 | Complete | UUID PKs; QID retained only on `SourceRecord`, verified by import tests | ✓ SATISFIED |
| CAT-06 | Complete | Zero runtime external calls (independently grepped); `test_list_endpoint_no_external_network_call` | ✓ SATISFIED |
| LIB-01 | Complete | Status transitions, transactional, owner-scoped, 14 tests + e2e reload assertion | ✓ SATISFIED |
| LIB-02 | Complete | Rating DB CheckConstraint 1-10, 7 tests | ✓ SATISFIED |
| INV-01 | Complete | Idempotent multi-copy creation under real concurrency, 8 tests | ✓ SATISFIED |
| INV-02 | Complete | Release/edition membership validated at service layer, tested | ✓ SATISFIED |
| INV-05 | Complete | Recursive-denylist + hostile-fixture XSS test on public profile | ✓ SATISFIED |
| **DATA-01** | **Pending** | `docs/verification/catalogue-freeze.md` (150 games, human-approved "corpus aprobado"), `docs/adr/ADR-003-data-sources.md` cite CC0/Commons licensing with sources | ⚠️ Evidence exists but tracker disagrees with plan self-declarations -- see human_verification |
| **DATA-02** | **Pending** | `data/manifests/catalogue.json` records source/URL/licence/date/cutoff/SHA-256, independently readable | ⚠️ Evidence exists but tracker disagrees with plan self-declarations -- see human_verification |
| REC-02 | Complete | `rank_popularity_v1()`, deterministic, versioned, 9 tests | ✓ SATISFIED |
| SEC-02 | Complete | `check-secrets.ps1` self-tests + Git/image scan re-run clean this session; no hardcoded credentials found | ✓ SATISFIED |
| OPS-01 | Complete (flipped this session) | Live public URL independently curled and confirmed healthy at the sign-off's cited commit | ✓ SATISFIED |
| OPS-02 | Complete | `infra/compose.yaml` full local chain, previously verified end-to-end (01-11-SUMMARY.md) | ✓ SATISFIED |
| OPS-03 | Complete | Zero outbound calls (independently grepped); `docker compose up` offline run documented | ✓ SATISFIED |
| QUAL-03 | Pending (deliberately) | 26 automated a11y tests green (independently confirmed); 2 named manual items open, accepted via override above | ✓ Correctly reflects reality -- see overrides |
| DOC-01 | Complete (flipped this session) | 5 ADRs independently read, sourced and reversible | ✓ SATISFIED |
| AGENT-01 | Complete (flipped this session) | `docs/methodology/agent-method.md`, ledger actor separation | ✓ SATISFIED |
| AGENT-02 | Complete (flipped this session) | Ledger hashes/paths, `check-evidence.ps1` fail-first canaries | ✓ SATISFIED |
| AGENT-03 | Complete (flipped this session) | Ledger `{proposal, automated-check, author-decision}` type separation, independently parsed | ✓ SATISFIED |

No ORPHANED requirements found.

### Prohibitions (judgment-tier, routed to human checkpoint per honest-verifier protocol)

Every plan's `must_haves.prohibitions` entry carries `status: unresolved, verification: judgment` in its PLAN frontmatter (never flipped to `resolved` post-execution) -- e.g. "the public profile must not infer private ownership," "the popularity baseline must not be presented as personalized," "the UI must not fabricate testimonials/coverage/licences." These are LLM-judgment, non-authoritative items by design (not a schema gap). Spot-checking the ones with the clearest code surface (public-profile allowlist, popularity DTO's `limitation` string, `infra/render.yaml`'s secret-freedom) found no violations in the actual code. This is a non-authoritative sample, not an exhaustive re-audit of all ~20 prohibitions across all 16 plans -- flagging that fact rather than silently passing the full set. **Human review recommended, not a blocker**: none of the spot-checked prohibitions show a violation, and no plan's own SUMMARY reports one either.

### Anti-Patterns Found

None. Scanned every file named in all 16 plans' `files_modified` plus a broad recursive grep across `apps/`, `e2e/`, `scripts/`, `infra/` for `TBD`/`FIXME`/`XXX`/`TODO`/`placeholder`/`coming soon`/`not yet implemented` — zero matches (the word "placeholder" appears only in code and docs referring to the deliberate first-party cover-image placeholder policy for unlicensed assets, not an implementation stub).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Evidence ledger passes fail-first schema/hash/type/secret checks | `powershell -File scripts/check-evidence.ps1` | `PASS: 5 non-vacuous ADRs...`, `PASS: 16 ledger entries...` | ✓ PASS |
| Secret scanner detects its own canaries and scans Git/image surfaces clean | `powershell -File scripts/check-secrets.ps1` | Self-test PASS (7/7 canaries); 3147 Git files and 2 Docker images scanned clean; 2 container-dependent phases FAIL only because no live stack is running in this session | ⚠️ PARTIAL (environmental, not a code defect -- see narrative) |
| Public API health endpoint reachable and matches sign-off's cited commit | `curl https://savepoint-api-37nz.onrender.com/health/` | `200 {"status":"ok","commit":"ff5aa2ee..."}` | ✓ PASS |
| Public web app renders real content, not a placeholder | `curl https://save-point-orpin.vercel.app/es`, `/es/catalogue`, `/es/login` | All `200`, real HTML (19-43KB), no secret-shaped strings found | ✓ PASS |
| No runtime outbound HTTP calls in API code (CAT-06/OPS-03) | `grep -rn "requests\.\|httpx\.\|urllib.request\|fetch(" apps/api` (excl. tests/tooling) | Zero matches | ✓ PASS |
| Zero application-code drift between the deployed/confirmed commit and current HEAD | `git diff --stat ff5aa2e HEAD -- apps/ infra/ e2e/demo-journey.spec.ts e2e/a11y.spec.ts` | No output (zero diff) | ✓ PASS |

### Decision Coverage

Not run as a separate gate: this phase's `01-CONTEXT.md` decisions (D-01 through D-20) are the same decisions traced individually against artifacts throughout the Requirements Coverage and Observable Truths tables above (e.g., D-09 canonical identity → CAT-04; D-13/D-15/D-16 rating/copies → LIB-02/INV-01/INV-02; D-17-D-20 shell → QUAL-03). No decision was found abandoned without a corresponding artifact.

## Gaps Summary

No FAILED truths, no MISSING/STUB artifacts, no NOT_WIRED key links were found. The phase goal is genuinely achieved: a real, independently-verified public deployment serves the full described vertical slice, and the offline/local reproducibility, privacy boundary, and evidence trail all hold up under direct inspection of the code (not just the SUMMARY narratives describing it).

Two items surfaced by this independent verification were **not** caught by the human sign-off and are routed to the developer for a decision (see `human_verification` above and the frontmatter):

1. **DATA-01/DATA-02 traceability inconsistency.** Plans 01-05 and 01-13 both self-report these as completed requirements with real supporting evidence, but `.planning/REQUIREMENTS.md` keeps both `Pending` — unlike QUAL-03, whose `Pending` status has an explicit, separately-documented rationale. This may be an intentional conservative stance (the corpus is about to be superseded by IGDB in Phase 1.1) or a bookkeeping oversight; only the author can say which.
2. **Sign-off checkbox-count inaccuracy.** `docs/verification/phase-01-signoff.md` states "these remain the only two unchecked boxes in `docs/verification/phase-01-manual.md`," but every checkbox in that document is unchecked (by Plan 01-10's own deliberate design, which reserves checkbox-checking for a human reviewer even where automated coverage exists). The substance is not wrong — real automated evidence exists for the sections that appear unchecked, and the two 100%-manual items are correctly identified as still open — but the specific sentence overstates what was closed out by checkbox, which matters for a thesis document meant to be independently reproduced.

Neither item changes the phase's demonstrated success: the demo works, is live, is privacy-safe, is offline-reproducible, and its evidence trail is real and substantive. Both items are documentation/traceability precision issues, not functional gaps.

---
*Verified: 2026-09-05T11:15:00Z*
*Verifier: Claude (gsd-verifier)*
