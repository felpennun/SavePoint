---
phase: "2"
slug: "governed-corpus-external-ratings-evaluation-contract-and-fir"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-06"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `02-RESEARCH.md` §"Validation Architecture". The per-task
> verification map is completed by `gsd-planner` / `gsd-nyquist-auditor` once
> the PLAN.md files exist.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-django 4.14.0 (backend); Vitest (frontend, `apps/web/vitest.config.ts`); Playwright 1.62.x (e2e, `playwright.config.ts`) |
| **Config file** | `apps/api/pytest.ini` (`DJANGO_SETTINGS_MODULE=config.settings`, `testpaths=.`, `python_files=test_*.py`); `apps/web/vitest.config.ts`; `playwright.config.ts` |
| **Quick run command** | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue apps/api/recommendations apps/api/evaluation -x` |
| **Full suite command** | `docker compose -f infra/compose.yaml run --rm api pytest` + `corepack pnpm --dir apps/web run test` + `corepack pnpm exec playwright test` |
| **Estimated runtime** | ~90 seconds backend quick; ~6 min full (backend + web + Playwright) |

---

## Sampling Rate

- **After every task commit:** Run the scoped quick command for the touched app (`pytest apps/api/<app> -x` or `pnpm --dir apps/web run test`).
- **After every plan wave:** Run the full suite command.
- **Before `/gsd-verify-work`:** Full suite green, plus the manual reviews below.
- **Max feedback latency:** ~90 seconds (scoped quick pytest).

---

## Per-Task Verification Map

> Completed by `gsd-planner` when tasks are authored, then audited by
> `gsd-nyquist-auditor`. Requirement→test seeds below come from `02-RESEARCH.md`.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-XX-XX | XX | — | DATA-03 | — | `govern_corpus` idempotent (re-run → identical checksum) | integration | `pytest apps/api/catalogue/tests/test_govern_corpus.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | DATA-05/06 | — | `CorpusRatingSnapshot` insert-only; re-import updates live `GameWork`, never the snapshot | integration | `pytest apps/api/catalogue/tests/test_rating_snapshot.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | DATA-07 | SSRF/redirect (RAWG fetch) | IGDB↔RAWG reconcile: exact slug then title+year; unmatched dropped + counted | unit | `pytest apps/api/catalogue/tests/test_rawg_reconcile.py -x` | ❌ W0 (RAWG only) | ⬜ pending |
| 2-XX-XX | XX | — | CAT-02 | injection (query params) | Multi-select: genres AND, platforms OR, per-value chips, unknown slug ignored, `distinct()` | integration | `pytest apps/api/catalogue/tests/test_search.py -x` | ✅ extend | ⬜ pending |
| 2-XX-XX | XX | — | (search bug) | — | `backfill_game_aliases` creates primary + `title_en` + alt-name aliases; idempotent; search then finds IGDB works | integration | `pytest apps/api/catalogue/tests/test_alias_backfill.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | REC-01 | — | `rank_random_v1` seeded, deterministic, governed candidates only, excludes library | unit | `pytest apps/api/recommendations/tests/test_baselines.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | REC-03/08/09 | — | each `content-cbf-*` variant: cosine, combination mode, contribution table, DTO carries feature/corpus/snapshot versions | integration | `pytest apps/api/recommendations/tests/test_content.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | REC-06 | — | `< 3` genre-bearing entries → `insufficient_history` + non-empty cold-start fallback | integration | `pytest apps/api/recommendations/tests/test_content.py -k cold_start -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | REC-07 | — | every consumed work excluded from every variant | unit | `pytest apps/api/recommendations/tests/test_content.py -k exclude -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | EVAL-09 | — | `generate_synthetic_users`: ~8 archetypes × ~25 + cold-start cohort; same seed → identical histories; validation report | integration | `pytest apps/api/evaluation/tests/test_synthetic.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | EVAL-01/02/03 | — | frozen `protocol.json` (grid ≤24, K, relevance, LOO); same candidate set across algorithms; test runs once; refuses tuning-on-test | integration | `pytest apps/api/evaluation/tests/test_protocol.py apps/api/evaluation/tests/test_runner.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | EVAL (metrics) | — | P@K, R@K, nDCG@K, MAP@K match known-answer fixtures at K∈{5,10,20} | unit | `pytest apps/api/evaluation/tests/test_metrics.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | D-24 | — | "Novedades": `in_corpus` + `first_release_date` last 6 months, desc, `canonical_slug` tie, ≤20, hidden if 0 | integration | `pytest apps/api/catalogue/tests/test_new_releases.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | D-15 | — | "Para tus juegos": DLC of owned base games; DLC excluded from governed catalogue but queryable here | integration | `pytest apps/api/catalogue/tests/test_owned_dlc.py -x` | ❌ W0 | ⬜ pending |
| 2-XX-XX | XX | — | QUAL-05 | XSS (rendered text) | catalogue/detail/recommendations/home pass axe (dark+light), 44px targets, focus ring, 400%/320px reflow, EN/ES parity | e2e | `pnpm exec playwright test e2e/a11y.spec.ts` | ✅ extend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/api/catalogue/tests/test_govern_corpus.py` — DATA-03
- [ ] `apps/api/catalogue/tests/test_rating_snapshot.py` — DATA-05/06
- [ ] `apps/api/catalogue/tests/test_alias_backfill.py` — search bug
- [ ] `apps/api/catalogue/tests/test_new_releases.py`, `apps/api/catalogue/tests/test_owned_dlc.py` — D-24, D-15
- [ ] `apps/api/catalogue/tests/test_rawg_reconcile.py` — DATA-07 (only if RAWG lands in scope)
- [ ] `apps/api/recommendations/tests/test_baselines.py` — REC-01
- [ ] `apps/api/recommendations/tests/test_content.py` — REC-03/06/07/08/09
- [ ] `apps/api/evaluation/` app + `tests/{test_protocol,test_synthetic,test_splits,test_metrics,test_runner}.py` — EVAL-01/02/03/09
- [ ] `docs/methodology/protocol.json` + a `test_protocol.py` schema/consistency check
- [ ] Extend `apps/api/catalogue/tests/test_search.py` (multi-select), `e2e/a11y.spec.ts` (new surfaces), `apps/web` catalogue-filters unit tests (array params)
- [ ] Add `evaluation` to `INSTALLED_APPS`; confirm `pytest.ini` `testpaths=.` picks up `apps/api/evaluation/tests/`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `govern_corpus` re-run produces an identical checksum | DATA-03 | Determinism over ~312k rows is a property best eyeballed against a recorded hash | Run `govern_corpus` twice on the same DB; diff the two `corpus_manifest` checksums |
| Interrupt-and-resume of the ratings re-import | DATA-05 | SIGKILL/resume behaviour needs a real process kill against a throwaway DB | Start the re-import against a disposable PostgreSQL, SIGKILL mid-run, resume, confirm forward-only progress + idempotent convergence |
| Synthetic-user validation report matches the archetype spec | EVAL-09 | Statistical shape ("does this population look like the 8 archetypes") is a judgement call | Regenerate with a fixed seed; read the validation report; confirm per-archetype counts, library-size and rating distributions |
| One full `run_evaluation` produces a complete artifact JSON with content variants beating random on nDCG@10 | EVAL-01/DOC-04 | End-to-end protocol sanity is a whole-artifact review | Run `run_evaluation` once; inspect the artifact JSON for every frozen field and a plausible nDCG@10 ordering (content > random) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
