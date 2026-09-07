---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 03
subsystem: api
tags: [django, postgres, pg_trgm, search, catalogue, management-command, drf]

# Dependency graph
requires:
  - phase: 02-01
    provides: "catalogue/corpus.py::governed_works() (is_dlc=False, in_corpus=True) + in_corpus/corpus_version columns"
  - phase: 02-02
    provides: "GameAlias creation inside import_igdb_catalogue._upsert; GameAlias model + GIN trigram index"
provides:
  - "backfill_game_aliases one-off command that revives tolerant search over the imported catalogue"
  - "catalogue/aliasing.py::desired_aliases — the canonical English alias-set builder"
  - "catalogue/search.py multi-select genre (AND) / platform (OR) filters via repeated params"
  - "public catalogue list, search and facets scoped to governed_works()"
affects: [02-04, 02-05, 02-06]

# Actuals (#2632)
actuals:
  tokens: 9000
  tasks: 2
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared alias-set builder (catalogue/aliasing.py) so importer and backfill agree on GameAlias rows"
    - "PK-paged offline backfill (filter(id__gt=last).order_by(id)[:N]) — no held server-side cursor across per-page transactions"
    - "Duck-typed getlist() reader so parse_catalogue_query accepts QueryDict and plain dict"

key-files:
  created:
    - "apps/api/catalogue/aliasing.py"
    - "apps/api/catalogue/management/commands/backfill_game_aliases.py"
    - "apps/api/catalogue/tests/test_alias_backfill.py"
  modified:
    - "apps/api/catalogue/search.py"
    - "apps/api/catalogue/tests/test_search.py"

key-decisions:
  - "backfill_game_aliases iterates every GameWork (not just alias-less rows) so idempotency is proven through the unique constraint + bulk_create(ignore_conflicts=True), matching the plan must-have truth"
  - "VACUUM ANALYZE is skipped with a stderr notice when connection.in_atomic_block is True (it cannot run in a transaction); the real one-off path is covered by a transaction=True test"
  - "aliasing.py is a new standalone module used only by the backfill; import_igdb_catalogue._upsert keeps its own inline copy of the same logic (untouched — owned by 02-02). A later cleanup can DRY them onto desired_aliases()"
  - "parse_catalogue_query keeps plain-dict single-value support (get) alongside getlist so existing dict-based call sites and tests are unaffected"
  - "Multi-select cap enforced on both the raw repeated-value count and the de-duplicated count (bounded 400, code too_many_facet_values)"

patterns-established:
  - "Pattern: repeated query params read with getlist, trimmed, blank-dropped, order-preserving de-dupe, capped at MAX_MULTISELECT_VALUES"
  - "Pattern: genres = chained filter(genres__slug=g) (AND) + one .distinct() when any facet joined (Pitfall 3); platforms = single releases__platform__slug__in (OR)"

requirements-completed: [CAT-02]

coverage:
  - id: D1
    description: "backfill_game_aliases creates the primary + distinct title_en English aliases for every GameWork and is idempotent via the (work, locale, normalized_value) unique constraint"
    requirement: "CAT-02"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_alias_backfill.py#test_backfill_creates_primary_and_distinct_title_en_aliases"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_alias_backfill.py#test_backfill_is_idempotent_second_run_adds_no_rows"
        status: pass
    human_judgment: false
  - id: D2
    description: "After the backfill a work is found by exact, prefix and trigram-typo title match through catalogue.search"
    requirement: "CAT-02"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_alias_backfill.py#test_backfill_makes_work_findable_by_exact_prefix_and_trigram"
        status: pass
    human_judgment: false
  - id: D3
    description: "backfill runs VACUUM ANALYZE catalogue_gamealias after the batches and its summary leaks no secrets"
    requirement: "CAT-02"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_alias_backfill.py#test_backfill_runs_vacuum_analyze_after_batches"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_alias_backfill.py#test_backfill_summary_reports_counts_and_leaks_no_secrets"
        status: pass
    human_judgment: false
  - id: D4
    description: "parse_catalogue_query reads all repeated genre/platform values, de-dupes, drops blanks, and returns a bounded 400 past 20 values; plain-dict single values still work"
    requirement: "CAT-02"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_search.py#test_parse_reads_all_repeated_genre_and_platform_values"
        status: pass
      - kind: unit
        ref: "apps/api/catalogue/tests/test_search.py#test_parse_dedupes_and_drops_blank_repeated_values"
        status: pass
      - kind: unit
        ref: "apps/api/catalogue/tests/test_search.py#test_parse_rejects_more_than_twenty_repeated_facet_values"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_endpoint_rejects_more_than_twenty_repeated_values_with_bounded_400"
        status: pass
    human_judgment: false
  - id: D5
    description: "genres = AND without join duplicates, platforms = OR, unknown slug dropped (not emptying), min_rating single-valued"
    requirement: "CAT-02"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_multiple_genres_are_ANDed_without_join_duplicates"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_multiple_platforms_are_ORed"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_unknown_repeated_slug_is_dropped_not_emptying"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_min_rating_remains_single_valued"
        status: pass
    human_judgment: false
  - id: D6
    description: "Public list, search and facets operate over governed_works(); an in_corpus=False work is invisible in all three"
    requirement: "CAT-02"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py#test_non_governed_work_hidden_from_list_search_and_facets"
        status: pass
    human_judgment: false

# Metrics
duration: 22min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 03: Tolerant search backfill + multi-select filters Summary

**One-off `backfill_game_aliases` command that revives alias-only tolerant search over the imported IGDB catalogue, plus repeated-param genre=AND / platform=OR filters in `catalogue/search.py` scoped to `governed_works()` (CAT-02).**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-09-07T11:07:00+02:00
- **Completed:** 2026-09-07T11:24:00+02:00
- **Tasks:** 2 (both `tdd="true"`; Task 1 `type="tracer"`)
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- **`backfill_game_aliases`** (new offline command): for every `GameWork` it rebuilds the desired English alias set (primary `original_title` + `title_en` when it normalizes distinctly) and `bulk_create(ignore_conflicts=True, batch_size=5000)`s the missing rows. Work rows are paged by ascending PK (`filter(id__gt=last).order_by("id")[:2000]`) so no server-side cursor is held across the per-page `transaction.atomic()` + `pg_advisory_xact_lock(725_0203_03)`. After the batches it runs `VACUUM ANALYZE catalogue_gamealias` (skipped with a notice inside an open transaction). `--evidence-json` emits a counts-only summary.
- **`catalogue/aliasing.py::desired_aliases`**: the canonical `{normalized_value: display_value}` builder, shared-ready between the importer and the backfill.
- **`catalogue/search.py` multi-select**: `CatalogueQuery.genre/platform` (`str | None`) became `genres`/`platforms` (`tuple[str, ...]`). `parse_catalogue_query` reads every repeated `genre`/`platform` value via `getlist` (falls back to `get` for plain dicts), trims, drops blanks, de-dupes in order, and returns a bounded 400 (`too_many_facet_values`) past 20 values. `_apply_filters` ANDs genres (one chained `filter` each) with a single `.distinct()` when any facet joined, and ORs platforms (one `releases__platform__slug__in`). Unknown slugs are still silently dropped.
- **Governed scoping**: the public list, search and `_facets` now derive from `catalogue.corpus.governed_works()` (`is_dlc=False, in_corpus=True`); `_base_works()` was removed. `min_rating` stays single-valued over `total_rating`; the `sort` allowlist is unchanged.

## Task Commits

1. **Task 1: `backfill_game_aliases` (tracer, TDD)**
   - `dae5780` test(02-03): add failing tests for backfill_game_aliases
   - `95d10fe` feat(02-03): add backfill_game_aliases one-off command (+ `catalogue/aliasing.py`)
2. **Task 2: multi-select filters + governed scoping (TDD)**
   - `31eaa11` test(02-03): add failing tests for multi-select filters + governed scoping
   - `fedd11b` feat(02-03): multi-select genre/platform filters + governed scoping

**Plan metadata:** see plan-close commit (`Closes #19`).

## Files Created/Modified

- `apps/api/catalogue/aliasing.py` — NEW. `desired_aliases(name, title_en, alternative_names)` → `{normalized_value: value}`; `ALIAS_LOCALE = "en"`.
- `apps/api/catalogue/management/commands/backfill_game_aliases.py` — NEW. PK-paged, batched, advisory-locked alias backfill + `VACUUM ANALYZE` + `--evidence-json`.
- `apps/api/catalogue/tests/test_alias_backfill.py` — NEW. 5 tests (alias set, exact/prefix/trigram search, idempotency, redacted summary, VACUUM path).
- `apps/api/catalogue/search.py` — multi-select `CatalogueQuery`, `_multi_values` reader + cap, `_apply_filters` AND/OR rewrite, `governed_works()` scoping, `_base_works()` removed.
- `apps/api/catalogue/tests/test_search.py` — `_make_work`/`_work` fixtures default `in_corpus=True`; 12 new tests for repeated params, AND/OR, unknown-slug, cap-400, governed scoping, single-valued `min_rating`.

## Decisions Made

- **Iterate every `GameWork`, not just alias-less ones.** The plan's must-have truth requires idempotency *through the unique constraint*, so the backfill re-emits the full desired set every run and lets `ignore_conflicts=True` absorb dupes. `created = COUNT(after) - COUNT(before)` reports real inserts.
- **`aliasing.py` used only by the backfill.** `import_igdb_catalogue._upsert` (merged in 02-02, outside this plan's file boundary) keeps its own inline copy of the same construction. The new module is written to be the shared home for a future DRY pass; behaviour is identical (name + `alternative_names` via `setdefault`, then `title_en` if distinct).
- **`VACUUM ANALYZE` is conditional on `connection.in_atomic_block`.** `VACUUM` cannot run in a transaction; the guard makes the command safe to call from a wrapped-transaction context, and the real path is proven by a `@pytest.mark.django_db(transaction=True)` test.
- **Kept plain-dict support in `parse_catalogue_query`.** `getattr(params, "getlist", None)` is used when present, else `get`; existing dict-based call sites (and ~10 existing tests) are unaffected.

## Deviations from Plan

**1. [Rule 3 — sanctioned helper] Created `catalogue/aliasing.py`**
- **Found during:** Task 1
- **Issue:** The plan's `<action>` left it to the executor whether to extract a shared `desired_aliases` helper; the Artifacts list names it as "(posible)".
- **Fix:** Added `apps/api/catalogue/aliasing.py` as a standalone module and consumed it from `backfill_game_aliases`. Did **not** modify `import_igdb_catalogue.py` (owned by 02-02; its inline logic is behaviourally identical).
- **Files modified:** `apps/api/catalogue/aliasing.py` (new)
- **Verification:** `test_alias_backfill.py` asserts the exact per-work alias set.
- **Committed in:** `95d10fe`

---

**Total deviations:** 1 (sanctioned artifact from the plan's own Artifacts list).
**Impact on plan:** None. No scope creep; importer left untouched to respect the wave-3 file boundary.

## Issues Encountered

- **`.iterator()` + per-batch transactions.** An early design used `GameWork.objects.iterator(chunk_size=...)` while opening `transaction.atomic()` per flush; committing mid-iteration can invalidate a PostgreSQL server-side cursor. Switched to explicit PK paging (`filter(id__gt=last).order_by("id")[:N]`) — indexed range scans, no held cursor. Resolved before any commit.
- **`governed_works()` scoping broke every existing search fixture** (they created works with the default `in_corpus=False`). Fixed by defaulting `in_corpus=True` in the `test_search.py` `_make_work`/`_work` helpers and adding an explicit `in_corpus=False`-is-hidden test. `test_detail.py`'s one list-endpoint assertion is a negative check and stays green.

## Verification

- `pytest apps/api/catalogue/tests/test_alias_backfill.py apps/api/catalogue/tests/test_search.py -q` → **42 passed** (5 backfill + 37 search).
- `pytest apps/api/catalogue -q` (plan regression) → **75 passed** (was 70).
- `pytest apps/api -q` (full regression) → **295 passed** (was 280; +15 new tests here, others from prior waves).
- All runs via `docker compose -f infra/compose.yaml run --rm --no-deps api pytest …` (shared `savepoint-db-1` never recreated).

### Tracer feedback gate (Task 1)

Task 1 is `type="tracer"` with no `gate` attribute. The proven slice — backfill → alias rows → exact/prefix/trigram search — is exercised end-to-end by `test_backfill_makes_work_findable_by_exact_prefix_and_trigram`. `<verify>` re-run green; expanded into Task 2 without a checkpoint.

## User Setup Required

None. `backfill_game_aliases` is a manual offline command (`python manage.py backfill_game_aliases [--evidence-json PATH]`); it makes no external calls and registers no scheduler.

## Next Phase Readiness

- **CAT-02 backend complete.** Multi-select genre/platform filtering with governed-corpus scoping is live; `02-04` (the `FacetMenu` multi-select UI) can consume the repeated-param contract, and `02-05` / `02-06` build the catalogue API / ficha on `governed_works()`.
- **`backfill_game_aliases` is ready to run against the persistent dev DB** as part of the wave-3 data step (after `govern_corpus` has set `in_corpus`), reviving search over the full ~193k governed works. It has not been run against real data in this worktree (offline command, no fixture data).
- **Next unblocked plans in Phase 2:** `02-05`, `02-09`, `02-10` (rest of wave 3 — the `02-09` archetype and `02-10` pure-python checkpoints are already ratified per STATE), then wave 4 (`02-04`).

## Self-Check: PASSED

- Files: `apps/api/catalogue/aliasing.py`, `apps/api/catalogue/management/commands/backfill_game_aliases.py`, `apps/api/catalogue/tests/test_alias_backfill.py`, `apps/api/catalogue/search.py`, `apps/api/catalogue/tests/test_search.py`, `02-03-SUMMARY.md` — all present.
- Commits: `dae5780`, `95d10fe`, `31eaa11`, `fedd11b` — all present in `git log`.
- Tests: 42 targeted / 75 catalogue / 295 full `apps/api` — all green.

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Completed: 2026-09-07*
