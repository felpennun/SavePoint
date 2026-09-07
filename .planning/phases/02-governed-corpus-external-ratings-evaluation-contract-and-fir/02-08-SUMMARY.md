---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 08
subsystem: testing
tags: [evaluation, recommender, protocol, metrics, ndcg, leave-one-out, frozen-contract, django]

requires:
  - phase: 02-01
    provides: "catalogue/corpus.py::governed_works(corpus_version), GameWork.in_corpus / corpus_version"
provides:
  - "apps/api/evaluation/ Django app (registered in INSTALLED_APPS after recommendations)"
  - "docs/methodology/protocol.json — frozen EVAL-03 contract (relevance D-17, K + headline D-19, LOO split D-18, 18-config tuning grid D-21, metric list D-22, disjoint user split, simulation:true)"
  - "docs/methodology/evaluation-protocol.md — Spanish prose + '## Amenazas a la validez' (DOC-04)"
  - "evaluation/protocol.py — fail-closed loader (ProtocolError), frozen_hash(), grid-budget guard, consumed-test run marker"
  - "evaluation/metrics.py — hand-written precision@k / recall@k / dcg@k / ndcg@k / average_precision / map@k (stdlib only)"
  - "evaluation/splits.py — relevant_positive_ids(), leave_one_out() with candidate manifest sha256, user_split()"
affects: [02-09, 02-10, 02-11, 02-13]

actuals:
  tokens: 12500
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Frozen machine-readable evidence contract (protocol.json) + fail-closed loader, analog of bootstrap_demo_accounts.parse_seed_contract"
    - "Hand-written, unit-tested ranking metrics (no scikit-learn / numpy) per STACK 'implement project metrics explicitly'"
    - "Deterministic per-(seed, user) leave-one-out with a hashed per-user candidate manifest (EVAL-01)"

key-files:
  created:
    - apps/api/evaluation/__init__.py
    - apps/api/evaluation/apps.py
    - apps/api/evaluation/protocol.py
    - apps/api/evaluation/metrics.py
    - apps/api/evaluation/splits.py
    - apps/api/evaluation/tests/__init__.py
    - apps/api/evaluation/tests/test_protocol.py
    - apps/api/evaluation/tests/test_metrics.py
    - apps/api/evaluation/tests/test_splits.py
    - docs/methodology/protocol.json
    - docs/methodology/evaluation-protocol.md
  modified:
    - apps/api/config/settings.py

key-decisions:
  - "protocol.json top-level keys: the 12 frozen keys (protocol_version, relevance, k_values, headline, split, candidate_set, exclusions, metrics, tuning, user_split, corpus_version, snapshot_sha256) plus simulation:true + limitation (EVAL-10) and provenance metadata (frozen_on, ratified_by)."
  - "Seeds frozen: split.seed = 20260907, user_split.seed = 20260908."
  - "corpus_version and snapshot_sha256 left as JSON null; Plan 02-13 resolves them against the active CorpusVersion."
  - "frozen_hash() = sha256 of canonical JSON (sort_keys, compact separators) of the whole raw contract — whitespace/key-order stable, semantics-sensitive."
  - "Consumed-test guard: a run marker recording this protocol's frozen_hash blocks reload unless protocol_version is bumped or allow_consumed_test=True is passed."
  - "leave_one_out uses random.Random(f'{seed}:{user.pk}') (string seed -> PYTHONHASHSEED-independent); candidate manifest hashes the sorted string forms of the UUID work ids."
  - "user_split requires exactly train+validation+test distinct ids so sizes match the protocol AND the union is the full set."

patterns-established:
  - "Pattern: evaluation contract frozen before any variant runs — loader raises ProtocolError on len(grid) > 24 or a consumed test split."
  - "Pattern: metrics written for the general multi-positive case even though Phase 2 LOO is single-positive, so Phase 3 reuses them unchanged."

requirements-completed: [EVAL-01, EVAL-02, EVAL-03, EVAL-10, DOC-04]

coverage:
  - id: D1
    description: "apps/api/evaluation/ app exists and is registered in INSTALLED_APPS after recommendations; pytest discovers apps/api/evaluation/tests/."
    requirement: "EVAL-03"
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api sh -c 'python manage.py check'"
        status: pass
      - kind: unit
        ref: "apps/api/evaluation/tests/ (54 tests collected and passing)"
        status: pass
    human_judgment: false
  - id: D2
    description: "docs/methodology/protocol.json freezes the 12 EVAL-03 keys (relevance D-17, K+headline D-19, LOO split D-18, candidate set, exclusions, metric list D-22, 18-config tuning grid D-21, disjoint user split, corpus_version/snapshot_sha256 placeholders) plus simulation:true / limitation."
    requirement: "EVAL-03"
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_protocol.py#test_checked_in_protocol_loads_with_frozen_keys / test_checked_in_grid_is_18_configs_within_budget"
        status: pass
    human_judgment: false
  - id: D3
    description: "evaluation/protocol.py loads and validates protocol.json fail-closed: ProtocolError on missing keys, non-true simulation, len(grid) > 24, or an already-consumed test split; frozen_hash() is stable and key-order independent."
    requirement: "EVAL-03"
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_protocol.py (grid budget, consumed-marker, missing-key, invalid-json, hash-stability)"
        status: pass
    human_judgment: false
  - id: D4
    description: "evaluation/metrics.py: hand-written precision@k, recall@k, dcg/ndcg@k, average_precision/map@k (stdlib only) verified against known-answer fixtures at K in {5,10,20}."
    requirement: "EVAL-03"
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_metrics.py (17 known-answer cases)"
        status: pass
    human_judgment: false
  - id: D5
    description: "evaluation/splits.py: relevant_positive_ids applies D-17; leave_one_out is deterministic per (seed, user), candidate set = governed_works(corpus_version) - remaining library + held-out item, with a stable candidate-manifest sha256 (EVAL-01); user_split is a seeded disjoint train/validation/test partition whose union is the whole set (EVAL-02 leakage note in the docstring)."
    requirement: "EVAL-01"
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_splits.py (8 tests: relevance rule, determinism, candidate membership, manifest stability, disjoint/covering split, wrong-count guard)"
        status: pass
    human_judgment: false
  - id: D6
    description: "docs/methodology/evaluation-protocol.md documents the protocol and a '## Amenazas a la validez' section (synthetic-user external validity, single-positive LOO bias, single-source rating bias, archetype circularity, one-way freeze) in Spanish per CONVENTIONS."
    requirement: "DOC-04"
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_protocol.py#test_evaluation_protocol_doc_documents_threats_to_validity"
        status: pass
    human_judgment: true
    rationale: "The presence of the section is test-enforced, but whether the threats-to-validity narrative is thesis-adequate is an author judgment (DOC-04)."

duration: 18min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 08: Congelar el protocolo de evaluación Summary

**Frozen `protocol.json` (relevance D-17, nDCG@10 headline, leave-one-out split, 18-config tuning grid, metric list) plus a fail-closed loader, hand-written ranking metrics, and a deterministic per-user LOO / disjoint user split — the evaluation contract is checked in before any advanced recommender runs.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-09-07 ~09:54 local (spawned after Task 1 ratification commit `e9be42d`)
- **Completed:** 2026-09-07 ~10:12 local
- **Tasks:** 2 executed (Task 1 was a `checkpoint:decision`, already ratified `ratify-as-proposed` on 2026-09-07)
- **Files modified:** 12 (11 created, 1 modified)

## Accomplishments

- New `apps/api/evaluation/` Django app registered in `INSTALLED_APPS` immediately after `recommendations.apps.RecommendationsConfig`; no models, no migrations; `pytest apps/api/evaluation` discovers all three test modules.
- `docs/methodology/protocol.json` freezes the EVAL-03 contract: relevance `{completed: true, rating_half_steps_gte: 7}` (D-17), `k_values [5,10,20]` + headline `ndcg@10` (D-19), leave-one-out-per-user split with `seed 20260907` (D-18), candidate set `governed_corpus_minus_user_library_plus_heldout`, exclusions `any_library_entry`, metric list `[precision@k, recall@k, ndcg@k, map@k]` (D-22), an 18-config tuning grid (`weighted_sum` 9 + `multiplicative` 3 + `two_stage` 6) scored on `validation` with `test_runs: 1` (D-21), a disjoint `user_split` 120/40/40 with `seed 20260908`, and `corpus_version` / `snapshot_sha256` as `null` placeholders for Plan 02-13. `simulation: true` + `limitation` per EVAL-10.
- `docs/methodology/evaluation-protocol.md` — Spanish methodology prose with a `## Amenazas a la validez` section (synthetic-user external validity, single-positive LOO bias, single-source rating bias, archetype circularity, one-way freeze).
- `evaluation/protocol.py` — fail-closed `load()` / `loads()` / `from_mapping()` raising `ProtocolError`; `frozen_hash()` over canonical JSON; `len(grid) > 24` guard (D-21); `record_test_run()` + consumed-test-split guard.
- `evaluation/metrics.py` — hand-written `precision_at_k`, `recall_at_k`, `dcg_at_k`, `idcg_at_k`, `ndcg_at_k`, `average_precision_at_k`, `map_at_k`, pure stdlib (`math.fsum` / `math.log2`), no scikit-learn / numpy.
- `evaluation/splits.py` — `relevant_positive_ids()` (D-17), `leave_one_out()` deterministic per `(seed, user.pk)` returning `(heldout_work_id, candidate_ids, remaining_library_ids, candidate_manifest_sha256)` with the candidate set built per RESEARCH Pitfall 6, and `user_split()` seeded disjoint 3-way partition. Docstring records the D-13 genre rating profile as a leakage-safe corpus statistic (EVAL-02).

## Task Commits

1. **Task 2 (tracer, TDD): app `evaluation`, frozen protocol, ranking metrics** — `2f51d16` (feat)
2. **Task 3 (auto, TDD): leave-one-out split + disjoint user partition** — `2696c54` (feat)

**Plan metadata:** `<metadata-commit>` (docs: complete plan)

_Task 1 (`checkpoint:decision`, `blocking-human`) was ratified before this executor ran; its commit is `e9be42d docs(02-08): ratify frozen evaluation protocol params`._

## Files Created/Modified

- `apps/api/evaluation/apps.py` — `EvaluationConfig`.
- `apps/api/config/settings.py` — `evaluation.apps.EvaluationConfig` added to `INSTALLED_APPS` after `recommendations`.
- `apps/api/evaluation/protocol.py` — protocol loader + freeze guards.
- `apps/api/evaluation/metrics.py` — top-N ranking metrics.
- `apps/api/evaluation/splits.py` — relevance rule, leave-one-out, user split.
- `apps/api/evaluation/tests/test_protocol.py` — 29 freeze-guard / structural tests.
- `apps/api/evaluation/tests/test_metrics.py` — 17 known-answer metric tests.
- `apps/api/evaluation/tests/test_splits.py` — 8 split tests.
- `docs/methodology/protocol.json` — frozen machine-readable contract.
- `docs/methodology/evaluation-protocol.md` — DOC-04 prose + threats to validity.

## Verification

| Check | Command | Result |
|---|---|---|
| Task 2 `<verify>` | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_protocol.py apps/api/evaluation/tests/test_metrics.py -q` | 46 passed |
| Task 3 `<verify>` | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_splits.py -q` | 8 passed |
| Plan `<verification>` (app) | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation -q` | 54 passed |
| Plan `<verification>` (full suite) | `docker compose -f infra/compose.yaml run --rm api pytest apps/api -q` | 280 passed (baseline 226 + 54 new; no regressions) |
| Full suite via `pytest.ini` dir | `docker compose ... run --rm -w /workspace/apps/api api pytest -q` | 280 passed |
| Django system check | `docker compose ... run --rm api python manage.py check` | 0 issues |

## Decisions Made

- **Placeholders as JSON `null`.** `corpus_version` and `snapshot_sha256` are `null` in `protocol.json`; the loader accepts `str | None` for both and Plan 02-13 resolves them against the active `CorpusVersion`.
- **`frozen_hash()` over canonical JSON of the whole `raw` contract** — stable under whitespace/key reordering, sensitive to any parameter change. This is the value Plans 02-11/02-13 and the thesis tables reference.
- **String seeding for LOO** (`random.Random(f"{seed}:{user.pk}")`) so held-out selection is reproducible independent of `PYTHONHASHSEED`.
- **Candidate manifest hashes UUID string forms** — `GameWork` PKs are UUIDs, not ints; `json.dumps(sorted(str(cid) ...))` gives a deterministic per-user manifest for EVAL-01.
- **`user_split` is strict** — it requires exactly `train + validation + test` distinct ids so both acceptance conditions (sizes match protocol AND union is the full set) hold; a wrong count raises `ValueError`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **UUID serialization in `leave_one_out` (fixed within Task 3 before its first green run).** The first run of `test_splits.py` failed with `TypeError: Object of type UUID is not JSON serializable` because `GameWork.id` is a `UUIDField`. Fixed by hashing `sorted(str(cid) for cid in candidate_ids)`. This was an in-task TDD RED→GREEN iteration on new code, not a change to planned behaviour.
- **Bare `docker compose ... run --rm api pytest` (no path) reports ~20 collection errors.** Pre-existing environment quirk: run from `/workspace` pytest picks up `pyproject.toml`'s `[tool.pytest.ini_options]` instead of `apps/api/pytest.ini`, so `DJANGO_SETTINGS_MODULE` is not wired and every DB-touching test module errors identically (19 before this plan, 20 after — the only delta is the new `test_splits.py` joining the same pre-existing failure). Running from `apps/api/` (`-w /workspace/apps/api`) or with an explicit `apps/api` path passes 280/280. Out of scope for this plan (scope boundary); noted for a future infra fix.

## TDD Gate Compliance

Both tasks are `tdd="true"`. Tests were written and run RED first (`test_splits.py` genuinely failed on the UUID bug before the fix), then GREEN. Per the project's hard rule "atomic commits, one per task", RED and GREEN are combined into a single `feat(02-08)` commit per task rather than separate `test(...)` / `feat(...)` commits. `git log --grep "02-08"` therefore shows one `feat` commit per task plus the Task 1 `docs` ratification commit.

## Known Stubs

None. `corpus_version` / `snapshot_sha256` are `null` by design (documented in `protocol.json`, `evaluation-protocol.md`, and the plan) and are resolved by Plan 02-13; the loader treats `None` as valid for these two keys only.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Wave 2 half-complete.** 02-08 is done; 02-02 (RAWG/IGDB ratings) remains paused on the author's separate live RAWG job — untouched by this plan.
- **Unblocked next in Phase 2:** with Wave 2's 02-08 done, the Wave 3 plans that depend on the evaluation contract can proceed once 02-02 also closes — `02-03` (tolerant search + multi-select filters, `depends_on: [02-01]`), `02-05`, `02-09` (synthetic users — consumes `evaluation/splits.py` + `protocol.json`), and `02-10` (`rank_random_v1` + content feature model). `02-09`, `02-11`, `02-13` will `protocol.load()` this frozen contract.
- **Shared requirement IDs:** EVAL-01, EVAL-10, DOC-04 are also declared by 02-09 / 02-13, so they stay `Pending` in REQUIREMENTS.md until those plans finish (shared-ID gate). EVAL-02 and EVAL-03 are owned solely by 02-08 and are marked complete.

## Self-Check: PASSED

- All 11 created files + `02-08-SUMMARY.md` present on disk.
- Task commits `2f51d16` and `2696c54` present in `git log`.
- `EvaluationConfig` present in `apps/api/config/settings.py` `INSTALLED_APPS`.
- All task `<verify>` commands and the plan `<verification>` full suite re-run green (280 passed).

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Completed: 2026-09-07*
