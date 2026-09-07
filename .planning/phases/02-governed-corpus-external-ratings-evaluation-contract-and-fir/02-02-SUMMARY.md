---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 02
subsystem: database
tags: [igdb, rawg, ratings, corpus-snapshot, django, postgres, provenance]

requires:
  - phase: 02-01
    provides: "governed corpus view (govern_corpus, governed_works, CorpusVersion 2026.09.1, CorpusRatingSnapshot model)"
provides:
  - "Ampliación de GAME_FIELDS de IGDB con rating/rating_count/total_rating_count/summary/alternative_names y creación de GameAlias en el importador"
  - "snapshot_corpus_ratings: comando insert-only que congela el rating de usuario de IGDB por corpus_version (27.014 filas source=igdb para 2026.09.1)"
  - "Cliente RAWG offline acotado + enrich_rawg_ratings con reconciliación determinista (slug exacto -> título normalizado + año, sin fuzzy)"
  - "Ejecución RAWG autenticada N=10.000: 8.575 CorpusRatingSnapshot(source=rawg), GameWork.rating intacto, cobertura combinada 13,9330 % (sin cambio)"
  - "ADR-008 (ratings externos gobernados) con el resultado autenticado y el hallazgo de que RAWG aporta contraste de fuente, no cobertura"
affects: [evaluation-protocol, recommender, thesis-data-chapter, search-filters]

actuals:
  tokens: 4200
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Enriquecimiento externo insert-only por corpus_version: get_or_create nunca update; un re-import mueve GameWork.rating vivo pero jamás toca una fila de snapshot"
    - "Reconciliación de identidad externa determinista y contable: slug exacto, luego título normalizado + año; toda fila no emparejada se descarta y se cuenta, nunca fuzzy"
    - "Ejecución offline larga en lotes con --offset para resistir reinicios del contenedor db de un worktree concurrente; cada lote es su propia transacción idempotente"

key-files:
  created:
    - "apps/api/catalogue/rawg.py (cliente RAWG offline, host fijo, sin redirects, backoff 429/5xx)"
    - "apps/api/catalogue/management/commands/enrich_rawg_ratings.py"
    - "apps/api/catalogue/management/commands/snapshot_corpus_ratings.py"
    - "apps/api/catalogue/tests/test_rawg_reconcile.py"
    - "apps/api/catalogue/tests/test_rating_snapshot.py"
    - "docs/adr/ADR-008-external-ratings.md"
  modified:
    - "apps/api/catalogue/igdb.py (GAME_FIELDS)"
    - "apps/api/catalogue/management/commands/import_igdb_catalogue.py (_normalize + _upsert, GameAlias)"
    - "apps/api/catalogue/models.py (campos de rating de usuario en GameWork)"
    - "infra/compose.yaml (db shm_size: 256mb)"
    - "docs/verification/igdb-catalogue-freeze.md (cobertura de rating + resultado RAWG autenticado)"
    - ".gitignore (.rawg-evidence*.json)"

key-decisions:
  - "add-rawg N=10.000 (ratificado por el autor 2026-09-07): RAWG entra como segunda fuente acotada, no como import de catálogo"
  - "RAWG se ejecutó en 18 lotes de 500 con --offset y --no-deps para no recrear el contenedor db compartido con el worktree concurrente de 02-08"
  - "El hallazgo medido (RAWG no añade cobertura sobre el corte top-N-por-rating_count) se documenta tal cual en ADR-008 y en el freeze doc; no se maquilla la cifra"

patterns-established:
  - "Verificación bloqueante pre-ejecución: consultar IgdbImportRun/GameWork/governed_works/coverage directamente en la BD y exigir coincidencia antes de lanzar cualquier comando; nunca confiar en un exit code"
  - "Evidencia JSON de enriquecimiento fuera del control de versiones (misma regla que data/snapshots/, ADR-006 §4)"

requirements-completed: [DATA-05, DATA-06, DATA-07, DATA-08, DOC-02]

coverage:
  - id: D1
    description: "GAME_FIELDS de IGDB amplía rating/rating_count/total_rating_count/summary/alternative_names y el importador crea GameAlias por obra (reconcile-then-drop-stale)"
    requirement: "DATA-05"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_igdb_import.py (21 passed, part of `pytest apps/api/catalogue -q` -> 70 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "snapshot_corpus_ratings escribe CorpusRatingSnapshot(source=igdb) solo por INSERT por corpus_version; un re-import posterior mueve GameWork.rating pero no toca ninguna fila de snapshot"
    requirement: "DATA-06"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_rating_snapshot.py (insert-only + immutability + non-active-version rejection)"
        status: pass
      - kind: integration
        ref: "manual: re-run enrich_rawg_ratings --offset 500 --limit 200 -> snapshots_inserted=0; GameWork.rating SHA-256 fingerprint identical before/after the 10k run"
        status: pass
    human_judgment: false
  - id: D3
    description: "Reconciliación IGDB<->RAWG determinista: slug exacto, luego título normalizado + año de lanzamiento; fila no emparejada descartada y contada, sin fuzzy"
    requirement: "DATA-07"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_rawg_reconcile.py (exact-slug preference, normalized title+year, rejection of title/year mismatch)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ejecución RAWG autenticada N=10.000 sobre el corpus gobernado 2026.09.1: cobertura RAWG medida (8.575/10.000), GameWork.rating no mutado, cobertura combinada 13,9330 %"
    requirement: "DATA-08"
    verification:
      - kind: integration
        ref: "docker compose run api python manage.py enrich_rawg_ratings --corpus-version 2026.09.1 --limit 10000 (18 batches); per-batch evidence JSON in scratchpad; post-run DB query"
        status: pass
    human_judgment: true
    rationale: "El número de cobertura y su interpretación (RAWG aporta contraste, no cobertura) alimentan la narrativa de datos del TFG; el autor debe revisar que ADR-008 y el freeze doc reflejan lo que quiere defender."
  - id: D5
    description: "ADR-008 documenta los campos de rating de IGDB (definiciones verbatim), la decisión IGDB-primario + RAWG acotado, y la regla de reconciliación, con los 7 encabezados en español que exige check-evidence.ps1"
    requirement: "DOC-02"
    verification:
      - kind: manual_procedural
        ref: "grep -E '^## ' docs/adr/ADR-008-external-ratings.md -> 7 headings; 'Autor de la decisión' present; https:// URLs present"
        status: pass
    human_judgment: true
    rationale: "check-evidence.ps1 no ejecutable en worktree aislado (harness bloquea PowerShell); verificado con equivalente grep. Un revisor debe correr el script canónico desde el checkout principal."

duration: 80min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 02: Import IGDB user ratings + secondary RAWG source Summary

**IGDB user-rating fields + immutable per-corpus_version snapshots, plus a bounded authenticated RAWG enrichment (8.575/10.000 works matched) that proved RAWG adds a corroborating rating source but zero new coverage over the governed corpus (combined coverage stays 13,9330 %).**

## Performance

- **Duration:** ~80 min (dominated by the 18-batch live RAWG run and recovery from two infrastructure failures)
- **Started:** 2026-09-07T07:45:00Z (approx)
- **Completed:** 2026-09-07T09:05:00Z (approx)
- **Tasks:** 3 (tasks 1-2 committed in a prior session; task 3 this session)
- **Files modified this session:** 5 (+ 1 new SUMMARY)

## Accomplishments

- **Task 1 (prior session, `a2c24e3`):** `GAME_FIELDS` widened with `rating`, `rating_count`, `total_rating_count`, `summary`, `alternative_names.name`, franchises/collections/companies; `_upsert` now creates `GameAlias` per work with reconcile-then-drop-stale (root-cause fix for the search bug), Wikidata aliases preserved.
- **Task 2 (prior session, `e51388f`):** `snapshot_corpus_ratings` management command — insert-only `CorpusRatingSnapshot(source="igdb")` per `corpus_version`, rejects a non-active version without `--force`, reports measured coverage. 27.014 IGDB snapshots frozen for `2026.09.1`; measured user-rating coverage 13,9330 % (`rating`), 15,8197 % (`total_rating`).
- **Task 3 (this session):** author-ratified `add-rawg N=10.000` executed live. Blocking pre-checks passed (IGDB import `complete`, 312.710 `GameWork`, 193.885 governed, 27.014 IGDB ratings, 0 RAWG rows). `shm_size: 256mb` added to the Compose `db` service. Ran `enrich_rawg_ratings --corpus-version 2026.09.1 --limit 10000` in 18 batches of 500.
  - **10.000** works considered (top by IGDB `rating_count`), **8.575** matched (exact slug or normalized title + release year), **1.425** not matched (discarded and counted, no fuzzy), **0** matched-without-usable-rating.
  - **8.575** `CorpusRatingSnapshot(source="rawg")` inserted (0-100 scale, max 96,6, none out of range); **8.553** `SourceRecord(source="rawg")` with ficha URL + retrieved_at + payload hash.
  - **`GameWork.rating` NOT mutated** — SHA-256 fingerprint over `(id, rating, rating_count)` for all 27.014 rated governed works identical before and after.
  - **Combined `igdb` OR `rawg` coverage over 193.885 governed works: 27.014 = 13,9330 % — unchanged.** RAWG-only new coverage: **0 works**. The bounded slice orders by IGDB `rating_count`, so all 10.000 processed works already had an IGDB user rating; RAWG contributes an independent cross-check, not additional coverage. Recorded verbatim in ADR-008 and `igdb-catalogue-freeze.md`.
- **Idempotency:** re-running any `--offset` inserts nothing (`snapshots_inserted = 0`, verified on range 500-700).
- **Tests:** `pytest apps/api/catalogue -q` -> **70 passed**.

## Task Commits

1. **Task 1: IGDB user ratings + GameAlias** - `a2c24e3` (feat, prior session)
2. **Task 2: immutable CorpusRatingSnapshot** - `e51388f` (feat, prior session)
3. **RAWG client + command + ADR + tests (paused)** - `a718e8d` (wip, prior session)
4. **Task 3a: db shm_size** - `794d091` (fix)
5. **Task 3b: authenticated RAWG run + evidence** - `9cbcdeb` (feat)

**Plan metadata:** `<this commit>` (docs: close plan, `Closes #18`)

## Files Created/Modified (this session)

- `infra/compose.yaml` - `db` service `shm_size: "256mb"` (mitigates the DiskFull seen in the IGDB evidence step)
- `docs/adr/ADR-008-external-ratings.md` - "Resultado autenticado — 2026-09-07" table; "Consecuencias" corrected: RAWG is a corroborating provenance for the most-rated works, not a coverage lever (0 new works)
- `docs/verification/igdb-catalogue-freeze.md` - "Ejecución autenticada RAWG — 2026-09-07" subsection with the measured table and DATA-07/DATA-08 interpretation
- `.planning/phases/02-.../02-02-CHECKPOINT.md` - "Resultado de la ejecución RAWG" section; status already `complete`
- `.gitignore` - `.rawg-evidence*.json` patterns

## Decisions Made

- **Batched RAWG run (18 x 500 with `--offset`, `--no-deps`)** instead of one `--limit 10000` transaction. Two reasons discovered live: (a) plan 02-08 runs concurrently in another worktree and its `docker compose` activity recreated the shared `db` container, killing a single long transaction mid-run; (b) the command wraps the whole loop in one `transaction.atomic()`, so a single failure loses everything. Batches are each their own idempotent transaction; a lost batch costs <=500 RAWG requests and is retried.
- **Evidence JSON to the scratchpad, not the repo tree.** The plan's suggested `--evidence-json /workspace/apps/api/.rawg-evidence.json` lands inside version control; used `--evidence-json -` (stdout) captured per batch into the session scratchpad, plus `.gitignore` patterns as a backstop.
- **Report the honest zero.** RAWG added 0 governed works to coverage. Documented as the measured result with its cause (selection ordered by IGDB `rating_count`), not smoothed over. If real additional coverage is wanted later, the selection criterion must change to governed works *without* an IGDB rating (new ADR revision + quota re-check).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `_emit` evidence path mangled by MSYS; switched to stdout capture**
- **Found during:** Task 3 (first chunked run attempt)
- **Issue:** Passing `--evidence-json /workspace/apps/api/.rawg-evidence.$OFF.json` through Git Bash rewrote `/workspace/...` to a Windows path; `Path.mkdir` raised `PermissionError: [Errno 13] Permission denied: 'C:'` *after* the transaction had already committed snapshots.
- **Fix:** Ran the command with `MSYS_NO_PATHCONV=1` and `--evidence-json -`, capturing each batch's JSON to the session scratchpad (outside version control). No source change required.
- **Verification:** All 18 batches emitted valid JSON; aggregate reconciles with the post-run DB counts.
- **Committed in:** n/a (operational, no repo change)

**2. [Rule 3 - Blocking] Concurrent worktree recreating the shared `db` container**
- **Found during:** Task 3 (initial single `--limit 10000` run)
- **Issue:** The first run died with `AdminShutdown: terminating connection due to administrator command` — plan 02-08's worktree ran `docker compose` and reconciled the shared `savepoint-db-1` container, dropping the connection mid-transaction. Nothing committed (single atomic block rolled back cleanly; DB fingerprint verified intact).
- **Fix:** Switched to `--no-deps` on every run (so this plan never recreates `db`) and to 18 idempotent `--offset` batches so a container recreate costs at most one batch.
- **Verification:** All 18 batches completed on first attempt after the switch; `pytest apps/api/catalogue -q` green; DB fingerprint unchanged.
- **Committed in:** `794d091` (shm_size), operational otherwise

**3. [Rule 1 - Bug, pre-existing, NOT fixed] `SourceRecord(source="rawg")` FK overwrite for RAWG games matched to 2 IGDB works**
- **Found during:** Task 3 post-run analysis (8.575 snapshots vs 8.553 SourceRecords)
- **Issue:** 22 RAWG game ids each reconcile to two distinct governed `GameWork` rows (IGDB regional/duplicate entries). `enrich_rawg_ratings` does `SourceRecord.objects.update_or_create(source, source_id, defaults={"work": work, ...})`, so the second match *updates* the shared SourceRecord's `work` FK to the later work. Both works still get their own immutable `CorpusRatingSnapshot`, so ratings data is correct; only the RAWG provenance row for those 22 points to one of the two works.
- **Why not fixed:** Pre-existing behaviour in code committed in `a718e8d` (not introduced this session), affects 22/8.575 rows (0,26 %), does not touch `GameWork.rating` or any snapshot, and a fix (per-work RAWG SourceRecord, or a through model) is an architectural change to the provenance schema (Rule 4 territory). Logged here and to `.planning/WINDOWS.md` for a follow-up.

---

**Total deviations:** 2 blocking (auto-worked-around, no source change), 1 pre-existing bug documented and deferred.
**Impact on plan:** The plan's Task 3 intent (measure real RAWG coverage, freeze evidence, don't mutate `GameWork.rating`) was met exactly. The infrastructure workarounds did not change what was measured.

## Issues Encountered

- **RAWG request budget:** the first single run + two failed retry attempts of the buggy chunked driver burned ~4.000-5.000 RAWG requests before the clean 18-batch pass (~9.000 more). Total well under the 20.000/month free cap, but with less margin than a clean single pass would have left. No 429s or auth failures observed at any point.
- **`docs/verification/igdb-catalogue-freeze.md`** carries pre-existing mojibake (`terminÃ³`) in the "Resultado autenticado de IGDB" block from an earlier session's encoding slip — left untouched (out of scope, separate defect).

## Known Stubs

None. All shipped code paths are wired to real data (live IGDB import, live RAWG API, persistent governed corpus).

## User Setup Required

None for the code. For thesis-evidence sign-off: a reviewer should run `scripts/check-evidence.ps1` and `scripts/check-secrets.ps1` from the main checkout (both blocked for worktree-isolated agents; verified here with grep equivalents — 7 ADR headings present, no secret values in the diff).

## State / Board (owned by orchestrator)

Per the execute-phase instructions, this plan did **not** modify `.planning/STATE.md`, `.planning/ROADMAP.md`, or `.planning/REQUIREMENTS.md` — the orchestrator reconciles those after both wave-2 plans (02-02, 02-08) land. `requirements-completed` above lists the IDs this plan satisfies (DATA-05, DATA-06, DATA-07, DATA-08, DOC-02) for that reconciliation. GitHub issue #18 is closed by the plan-metadata commit.

## Next Phase Readiness

- The harness / recommender must read `CorpusRatingSnapshot.filter(corpus_version=ACTIVE, source="igdb")` (27.014 rows for `2026.09.1`), never `GameWork.total_rating`. `source="rawg"` rows (8.575) are available as an independent cross-check but do not extend coverage.
- Phase 2 success criterion 2 is observable: every work with an external rating carries it with source + `retrieved_at`, immutably snapshotted per `corpus_version`, with a deterministic, documented reconciliation rule (executable slug/title+year matching in `enrich_rawg_ratings.py` + `test_rawg_reconcile.py`).
- Open follow-up: the 22-row RAWG `SourceRecord` FK-overwrite (see Deviation 3) if per-work RAWG provenance is later needed.

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Completed: 2026-09-07*
