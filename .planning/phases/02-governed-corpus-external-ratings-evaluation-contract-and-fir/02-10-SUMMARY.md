---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 10
subsystem: api
tags: [recommender, content-based, cosine, feature-vector, random-baseline, django, stdlib, pure-python]

requires:
  - phase: 02-01
    provides: "catalogue/corpus.py::governed_works(corpus_version), PLATFORM_ALLOWLIST / ALLOWLIST_SLUGS, GameWork.in_corpus / corpus_version, CorpusRatingSnapshot"
  - phase: 02-02
    provides: "GameWork.rating / CorpusRatingSnapshot.rating (external user-rating snapshot the D-13 term will read)"
provides:
  - "recommendations/baselines.py::rank_random_v1 (REC-01) — seeded uniform draw from governed_works minus the user's library, DTO grammar identical to rank_popularity_v1"
  - "recommendations/_weights.py — _entry_weight / _STATUS_WEIGHTS / _RATING_DIVISOR promoted to a shared module; genre_heuristic.py re-exports them unchanged"
  - "recommendations/content/similarity.py::cosine — pure-stdlib (math.fsum), bounded [0,1], exact 1.0 on equal vectors"
  - "recommendations/content/features.py — FEATURE_SET_VERSION='fs-v1', feature_vector() (sparse genre:/platform: dict, 1/sqrt(k) per facet, NO rating dimension), coverage_report() (D-11 gate), genre_rating_profile() (CorpusRatingSnapshot-derived)"
  - "recommendations/content/profile.py::build_profile — activity-weighted mean of L2-normalised item vectors, prefers cached WorkFeatureVector"
  - "recommendations/models.py::WorkFeatureVector + migration 0001_work_feature_vector (unique per work+feature_set_version)"
  - "recommendations/management/commands/rebuild_feature_vectors.py — batched, idempotent update_or_create, --evidence-json writes the D-11 coverage report"
affects: [02-11, 02-13, 02-12]

actuals:
  tokens: 10500
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Pure-Python vector arithmetic (cosine, L2 normalize, 1/sqrt(k) facet weights) — no numpy, per Task 1 checkpoint:decision (pure-python, ratified 2026-09-07)"
    - "WorkFeatureVector as an explicit cache (not a trained model): idempotent rebuild command, feature_set_version in the DTO (REC-09)"
    - "Shared activity-weighting module (_weights.py) re-exported by the original owner for backwards compatibility"
    - "Feature facet gated by measured coverage (coverage_report) rather than assumed present (D-11)"

key-files:
  created:
    - apps/api/recommendations/baselines.py
    - apps/api/recommendations/_weights.py
    - apps/api/recommendations/content/__init__.py
    - apps/api/recommendations/content/similarity.py
    - apps/api/recommendations/content/features.py
    - apps/api/recommendations/content/profile.py
    - apps/api/recommendations/models.py
    - apps/api/recommendations/migrations/__init__.py
    - apps/api/recommendations/migrations/0001_work_feature_vector.py
    - apps/api/recommendations/management/__init__.py
    - apps/api/recommendations/management/commands/__init__.py
    - apps/api/recommendations/management/commands/rebuild_feature_vectors.py
    - apps/api/recommendations/tests/test_baselines.py
    - apps/api/recommendations/tests/test_content_features.py
  modified:
    - apps/api/recommendations/genre_heuristic.py

key-decisions:
  - "FEATURE_SET_VERSION = 'fs-v1' — genre + allowlist-platform facets, 1/sqrt(k) per-facet weights; bumped when the vector-building rules change (part of the REC-09 DTO)."
  - "Per-facet 1/sqrt(k) weighting applied to BOTH genre and platform facets (RESEARCH shows 1.0 for platforms; the plan's behaviour test pins genres at 1/sqrt(k), so the same rule is applied uniformly to keep many-facet works from dominating cosine)."
  - "franchise:/developer: facets: coverage_report measures 0% over the governed view this phase (importer does not fetch franchises / involved_companies), so both are omitted; _franchise_slugs / _developer_slugs are left as no-op seams (D-11, Open Question 4 / CAT-05 stays Phase 6)."
  - "genre_rating_profile reads CorpusRatingSnapshot (per-work mean across sources, then per-genre mean), never GameWork.total_rating (threat T-02-10-01). The rating term is NOT a vector dimension — combine.py (Plan 02-11) owns it."
  - "rank_random_v1 fingerprint hashes {seed, sorted candidate ids, ranked ids} as canonical JSON; candidates sorted by str(uuid) before the seeded draw so the result depends only on seed + candidate set, not DB row order (threat T-02-10-04)."
  - "cosine short-circuits to exactly 1.0 when the two mappings are equal (after the zero-norm guard), and clamps to [0,1] otherwise, so self-similarity is exact rather than 1.0 minus a rounding error."
  - "Migration renamed from Django's default 0001_initial.py to 0001_work_feature_vector.py to match the plan's declared filename."
  - "WorkFeatureVector uses a UUID primary key (consistent with catalogue models) despite RecommendationsConfig.default_auto_field = BigAutoField."

patterns-established:
  - "Pattern: baseline DTO parity — rank_random_v1 mirrors rank_popularity_v1's key grammar exactly (algorithm_id, generated_at, input_snapshot_sha256, results[{work_id,slug,title,score}], limitation)."
  - "Pattern: cache-not-model persistence — WorkFeatureVector rebuilt by an idempotent management command; profile.py reads cache-first with a compute fallback."

requirements-completed: [REC-01, REC-03]

coverage:
  - id: D1
    description: "recommendations/baselines.py::rank_random_v1 (REC-01): seeded uniform draw from governed_works(corpus_version) minus every work the user has a LibraryEntry for; deterministic per seed; DTO key grammar identical to rank_popularity_v1; limit clamped to available candidates; fingerprint over (seed, sorted candidate ids, ranked ids)."
    requirement: "REC-01"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_baselines.py#test_same_seed_produces_identical_ranking_and_fingerprint / test_different_seed_produces_a_different_order / test_never_returns_a_work_in_the_users_library / test_only_draws_from_the_governed_corpus / test_dto_grammar_matches_rank_popularity_v1 / test_limit_is_clamped_when_there_are_fewer_candidates / test_fingerprint_changes_when_the_candidate_set_changes"
        status: pass
    human_judgment: false
  - id: D2
    description: "recommendations/content/similarity.py::cosine: pure stdlib (math.fsum), bounded [0,1], exactly 1.0 on equal vectors, 0.0 on empty / zero-norm / orthogonal, matches the hand-computed value."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_baselines.py#test_cosine_of_a_vector_with_itself_is_exactly_one / test_cosine_is_bounded_between_zero_and_one / test_cosine_of_orthogonal_vectors_is_zero / test_cosine_with_an_empty_or_zero_vector_is_zero / test_cosine_matches_the_hand_computed_value"
        status: pass
    human_judgment: false
  - id: D3
    description: "_entry_weight / _STATUS_WEIGHTS / _RATING_DIVISOR promoted to recommendations/_weights.py; genre_heuristic.py re-exports them; REC-10 genre-taste heuristic behaviour byte-for-byte unchanged."
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_genre_heuristic.py (20 tests, full regression re-run green after the move)"
        status: pass
    human_judgment: false
  - id: D4
    description: "recommendations/content/features.py::feature_vector: sparse dict, genre:<slug> (1/sqrt(k)) + platform:<slug> (allowlist only, 1/sqrt(k)), no rating dimension (T-02-10-01); franchise:/developer: gated off by coverage_report measured coverage (D-11)."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content_features.py#test_feature_vector_is_a_sparse_dict_with_no_rating_dimension / test_genre_weights_are_one_over_sqrt_k / test_only_allowlisted_platforms_become_features / test_franchise_and_developer_features_are_gated_off_without_coverage / test_coverage_report_decides_inclusion_from_measured_coverage"
        status: pass
    human_judgment: false
  - id: D5
    description: "recommendations/content/profile.py::build_profile: activity-weighted mean of L2-normalised item vectors, _entry_weight reused verbatim; prefers cached WorkFeatureVector; returns {} for a user with no library or no genre-bearing history; monogenre library profiles to that genre at weight 1.0."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content_features.py#test_profile_of_a_monogenre_library_is_dominated_by_that_genre / test_profile_weights_by_entry_weight_verbatim / test_profile_is_empty_for_a_user_with_no_genre_bearing_history / test_profile_is_empty_for_a_user_with_no_library / test_profile_prefers_the_cached_work_feature_vector"
        status: pass
    human_judgment: false
  - id: D6
    description: "recommendations/models.py::WorkFeatureVector + migration 0001_work_feature_vector: unique per (work, feature_set_version); applies cleanly on a fresh test DB; rebuild_feature_vectors populates every governed work and is idempotent (update_or_create)."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content_features.py#test_rebuild_feature_vectors_populates_every_governed_work / test_rebuild_feature_vectors_is_idempotent / test_work_feature_vector_is_unique_per_work_and_feature_set"
        status: pass
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm --no-deps api sh -c 'python manage.py makemigrations --check --dry-run && python manage.py check'  ->  'No changes detected' / '0 issues'"
        status: pass
    human_judgment: false
  - id: D7
    description: "recommendations/content/features.py::genre_rating_profile: mean CorpusRatingSnapshot rating per genre over governed works with a snapshot for the corpus_version (per-work mean across sources, then per-genre mean); never reads GameWork.total_rating."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content_features.py#test_genre_rating_profile_is_the_mean_snapshot_rating_per_genre"
        status: pass
    human_judgment: false

duration: ~35min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 10: Baseline aleatorio + modelo de features de contenido Summary

**`rank_random_v1` (REC-01, suelo de comparación con la gramática de DTO de `rank_popularity_v1`) más el modelo de features puro-Python: vectores de contenido dispersos `genre:`/`platform:` con peso `1/sqrt(k)` y sin dimensión de rating, perfil de usuario ponderado por actividad, coseno stdlib, y la caché `WorkFeatureVector` con comando de reconstrucción idempotente.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-07 (worktree `agent-a059ab494e4617bb1`, base `d9f7381`)
- **Completed:** 2026-09-07
- **Tasks:** 2 ejecutadas (Tarea 1 era `checkpoint:decision`, ya ratificada como `pure-python` el 2026-09-07, commit `06ea337`)
- **Files modified:** 15 (14 creados, 1 modificado)

## Accomplishments

- **`rank_random_v1` (REC-01)** — dibujo uniforme con `random.Random(seed)` sobre `governed_works(corpus_version)` menos todo trabajo con `LibraryEntry` del usuario. Mismo `seed` -> mismo ranking exacto; `seen_ids` nunca aparece; nada fuera del corpus gobernado (ni DLC ni `in_corpus=False`). DTO con las mismas claves que `rank_popularity_v1` (`algorithm_id="random-v1"`, `generated_at`, `input_snapshot_sha256`, `results` `[{work_id, slug, title, score}]`, `limitation="Uniform random draw from the governed corpus; comparison floor only."`). Fingerprint = SHA-256 de JSON canónico de `{seed, sorted(candidate_ids), ranked_ids}`; los candidatos se ordenan por `str(uuid)` antes del sorteo, así el resultado depende solo de `seed` + conjunto de candidatos (T-02-10-04).
- **`recommendations/_weights.py`** — `_entry_weight` / `_STATUS_WEIGHTS` (`completed:3, playing:2, pending:1, abandoned:0`) / `_RATING_DIVISOR=10` promovidos desde `genre_heuristic.py`, que ahora los re-exporta con `# noqa: F401` — `from recommendations.genre_heuristic import _entry_weight` sigue resolviendo y los 20 tests de `test_genre_heuristic.py` pasan sin cambios.
- **`content/similarity.py::cosine`** — stdlib puro (`math.fsum` en numerador y normas), acotado a `[0,1]` (todos los pesos >= 0), `cosine(x, x) == 1.0` exacto por corto-circuito de igualdad tras el guard de norma cero, `0.0` con vector vacío / norma cero / ortogonal.
- **`content/features.py`** — `FEATURE_SET_VERSION="fs-v1"`; `feature_vector(work, include_franchise=False, include_developer=False)` devuelve un dict disperso: `genre:<slug>` (garantizado, peso `1/sqrt(n_generos)`), `platform:<slug>` solo para slugs en `ALLOWLIST_SLUGS` (peso `1/sqrt(n_plataformas_allowlist)`), sin clave de rating. `coverage_report(corpus_version)` mide la cobertura de franquicia/desarrollador sobre la vista gobernada (0% este fase — el importador no trae `franchises` / `involved_companies`) y decide `include_franchise` / `include_developer` contra un umbral documentado del 50% (D-11); `_franchise_slugs` / `_developer_slugs` quedan como seams no-op. `genre_rating_profile(corpus_version)` = media por género de la media por obra de `CorpusRatingSnapshot.rating` (nunca `GameWork.total_rating`, T-02-10-01) — la consume `combine.py` en el Plan 02-11.
- **`content/profile.py::build_profile(user, corpus_version)`** — una sola lectura resuelta de `LibraryEntry`; `w = _entry_weight(status, rating_half_steps)` por entrada; acumula `w * L2_normalize(feature_vector(work))`; divide por `sum(w)`; `{}` si el usuario no tiene biblioteca o no tiene historial con género. Lee `WorkFeatureVector` cacheado con fallback a cálculo en vivo.
- **`WorkFeatureVector` + migración `recommendations/0001_work_feature_vector.py`** — FK a `catalogue.GameWork`, `feature_set_version`, `vector_json` (JSONField), `updated_at`, `UniqueConstraint(work, feature_set_version)`. `rebuild_feature_vectors` recorre `governed_works(corpus_version)` por lotes con `update_or_create` (idempotente), aplica el gate de cobertura, y `--evidence-json` escribe el `coverage_report`.

## Task Commits

Cada tarea `tdd="true"` con commit RED explícito antes del GREEN (regla dura del prompt):

1. **Tarea 2 (tracer, TDD): baseline aleatorio + coseno stdlib (REC-01)**
   - RED — `50b3194` `test(02-10): add failing tests for random baseline and stdlib cosine [Refs #26]`
   - GREEN — `6a8341e` `feat(02-10): add random baseline and stdlib cosine similarity [Refs #26]`
2. **Tarea 3 (auto, TDD): vectores de features, perfil de usuario, caché `WorkFeatureVector`**
   - RED — `6043036` `test(02-10): add failing tests for feature vectors, profile, cache [Refs #26]`
   - GREEN — `d189117` `feat(02-10): add content feature vectors, user profile, cache (REC-03) [Refs #26]`

**Plan metadata:** `<metadata-commit>` (`docs(02-10): complete plan ... Closes #26`)

## Files Created/Modified

- `apps/api/recommendations/baselines.py` — `rank_random_v1` (REC-01).
- `apps/api/recommendations/_weights.py` — `_entry_weight` / `_STATUS_WEIGHTS` / `_RATING_DIVISOR` compartidos.
- `apps/api/recommendations/content/__init__.py` — paquete del laboratorio de contenido.
- `apps/api/recommendations/content/similarity.py` — `cosine` stdlib.
- `apps/api/recommendations/content/features.py` — `FEATURE_SET_VERSION`, `feature_vector`, `coverage_report`, `genre_rating_profile`.
- `apps/api/recommendations/content/profile.py` — `build_profile`.
- `apps/api/recommendations/models.py` — `WorkFeatureVector`.
- `apps/api/recommendations/migrations/0001_work_feature_vector.py` — crea `WorkFeatureVector` (+ `__init__.py`).
- `apps/api/recommendations/management/commands/rebuild_feature_vectors.py` — reconstrucción idempotente de la caché (+ `management/__init__.py`, `management/commands/__init__.py`).
- `apps/api/recommendations/tests/test_baselines.py` — 13 tests (7 `rank_random_v1`, 5 `cosine`, 1 valor calculado a mano).
- `apps/api/recommendations/tests/test_content_features.py` — 14 tests (vector, cobertura, `genre_rating_profile`, perfil, comando, unicidad).
- `apps/api/recommendations/genre_heuristic.py` — importa y re-exporta desde `_weights.py`; se borra la definición local duplicada de `_entry_weight`.

## Verification

| Check | Command | Result |
|---|---|---|
| Tarea 2 `<verify>` | `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/recommendations/tests/test_baselines.py apps/api/recommendations/tests/test_genre_heuristic.py -q` | 34 passed |
| Tarea 3 `<verify>` | `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/recommendations/tests/test_content_features.py -q` | 14 passed |
| Plan `<verification>` (app) | `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/recommendations -q` | 48 passed |
| Plan `<verification>` (suite completa) | `docker compose -f infra/compose.yaml run --rm --no-deps -w /workspace/apps/api api pytest -q` | 345 passed (0 regresiones) |
| Migraciones + system check | `docker compose ... run --rm --no-deps api sh -c 'python manage.py makemigrations --check --dry-run && python manage.py check'` | `No changes detected` / `0 issues` |

Regla Docker/DB respetada: todos los `run --rm --no-deps` (nunca `up`/`down`/`restart`); la migración `recommendations/0001` solo se aplicó en la BD de test efímera de pytest, nunca en el esquema del `savepoint-db-1` compartido.

## Decisions Made

Ver `key-decisions` en el frontmatter. Puntos destacados:

- **`pure-python` (Tarea 1, ratificada)** — coseno, normalización L2, pesos `1/sqrt(k)` y RNG (`random.Random(seed)`) escritos a mano. Cero dependencias nuevas; el gate de dependencias NO se dispara esta fase.
- **Peso `1/sqrt(k)` por faceta en géneros y plataformas** — RESEARCH sugiere `1.0` para plataformas, pero el test de comportamiento del plan fija géneros en `1/sqrt(k)`; se aplica la misma regla a ambas facetas para que una obra con muchas facetas no domine el numerador del coseno.
- **Franquicia/desarrollador omitidos** — `coverage_report` mide 0% de cobertura sobre la vista gobernada (el importador no trae esos campos), así que ninguna clave `franchise:` / `developer:` se emite. Los helpers quedan como seams para cuando el dato llegue (D-11; CAT-05 sigue siendo Fase 6).
- **Migración renombrada** `0001_initial.py` -> `0001_work_feature_vector.py` para casar con el nombre declarado en el plan.

## Deviations from Plan

None - plan executed exactly as written.

(La única fricción — corto-circuito de `cosine` para `{"a":0.0}` — se resolvió dentro de la iteración TDD RED->GREEN de la Tarea 2, moviendo el guard de norma cero antes del corto-circuito de igualdad. Es iteración sobre código nuevo, no un cambio de comportamiento planificado.)

## Issues Encountered

- **`cosine` devolvía `1.0` para dos vectores de norma cero iguales.** El corto-circuito `if p == v: return 1.0` se evaluaba antes del guard de norma cero. Corregido reordenando: primero se calculan las normas y se devuelve `0.0` si alguna es cero, luego el corto-circuito de igualdad. Detectado y arreglado en el ciclo RED->GREEN de la Tarea 2 antes de su primer verde.
- **`docker compose ... run --rm api pytest` sin ruta reporta ~26 errores de colección.** Rareza de entorno pre-existente (ya documentada en `02-08-SUMMARY.md` §Issues): desde `/workspace` pytest coge `[tool.pytest.ini_options]` de `pyproject.toml` (raíz) en vez de `apps/api/pytest.ini`, así que `DJANGO_SETTINGS_MODULE` no queda cableado y todo módulo que toca BD falla igual (19 antes de esta fase, ahora 26 — el delta son exactamente los 2 módulos de test nuevos + los ya existentes de `recommendations`/`library`/`evaluation` uniéndose al mismo fallo). Con `-w /workspace/apps/api` (o ruta `apps/api` explícita) pasan 345/345. En Git Bash de Windows hace falta `MSYS_NO_PATHCONV=1` para que `-w /workspace/apps/api` no se convierta a `C:/Program Files/Git/workspace/...`. Fuera del alcance de este plan (scope boundary); anotado para un arreglo de infra futuro.

## TDD Gate Compliance

Ambas tareas de código son `tdd="true"`. Secuencia en `git log --grep "02-10"`: `test(02-10)` (RED) -> `feat(02-10)` (GREEN) por cada tarea, cuatro commits en total. Los RED se ejecutaron y fallaron por `ModuleNotFoundError` antes de escribir la implementación. No hubo commit `refactor(...)` (no hizo falta).

## Known Stubs

- **`_franchise_slugs(work)` / `_developer_slugs(work)` devuelven `[]` incondicionalmente** (`apps/api/recommendations/content/features.py`). Intencional y documentado (D-11 / Open Question 4): el importador de catálogo no trae `franchises.name` ni `involved_companies` todavía, y CAT-05 (franquicias/desarrolladores como entidades) es Fase 6. `coverage_report` mide 0% y `feature_vector` no emite esas facetas ni con `include_franchise=True`. El seam existe para que `feature_vector` no cambie cuando el dato llegue; su inclusión la decide `coverage_report` contra el umbral del 50%. No bloquea el objetivo del plan (vectores `genre:`+`platform:` operativos y probados).

_Registrado también en el ledger de ventanas rotas si aplica (`gsd windows`)._

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **02-10 ya no bloquea a nadie por sí mismo.** Sus dependientes siguen con otros gates:
  - **02-11** (`depends_on: [02-10, 02-02, 02-08]`) — 02-10 y 02-08 hechos; queda gated en **02-02** (RAWG/IGDB ratings, en pausa por el trabajo live del autor).
  - **02-13** (`depends_on: [02-02, 02-08, 02-09, 02-11]`) — gated en 02-02, 02-09 y 02-11.
- **Contratos que 02-11 consumirá de aquí:** `rank_random_v1` (baseline en `run_evaluation`), `content/similarity.py::cosine`, `content/features.py::{feature_vector, FEATURE_SET_VERSION, genre_rating_profile, coverage_report}`, `content/profile.py::build_profile`, `WorkFeatureVector` + `rebuild_feature_vectors`, y `_weights.py::_entry_weight`.
- **IDs de requisito compartidos:** `REC-03` lo declaran también 02-11 y 02-12 (variantes con nombre + endpoint, y la página de recomendaciones). Se queda `Pending` en REQUIREMENTS.md hasta que esos planes cierren (gate de ID compartido). `REC-01` es exclusivo de 02-10 y queda cubierto.
- **`FEATURE_SET_VERSION` en el DTO (REC-09):** `'fs-v1'`. Si 02-11 mide cobertura suficiente de franquicia/desarrollador y las añade, hay que bumpear la versión y reconstruir la caché.

## Self-Check

- Los 14 ficheros creados + `02-10-SUMMARY.md` presentes en disco (verificado).
- Commits de tarea `50b3194`, `6a8341e`, `6043036`, `d189117` presentes en `git log`.
- `docker compose ... run --rm --no-deps -w /workspace/apps/api api pytest -q` -> 345 passed (re-ejecutado, 0 regresiones).
- `python manage.py makemigrations --check --dry-run` -> `No changes detected`; `python manage.py check` -> `0 issues`.

## Self-Check: PASSED

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Completed: 2026-09-07*
