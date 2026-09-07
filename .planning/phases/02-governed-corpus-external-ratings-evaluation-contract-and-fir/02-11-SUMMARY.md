---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 11
subsystem: api
tags: [recommendations, content-based, ratings, explainability, django, deterministic]

requires:
  - phase: 02-02
    provides: "CorpusRatingSnapshot y versiones gobernadas de datos externos."
  - phase: 02-08
    provides: "Protocolo de evaluación y exclusión any_library_entry."
  - phase: 02-10
    provides: "Vectores de contenido, perfil de usuario, coseno y caché WorkFeatureVector."
provides:
  - "Tres variantes versionadas de recomendación de contenido: weighted, multiplicative y twostage."
  - "Término de rating basado exclusivamente en CorpusRatingSnapshot, con mezcla por confianza y fallback por género."
  - "Ranking determinista, explicaciones numéricas por contribución de género, cold start y exclusión de obras ya presentes en la biblioteca."
  - "ContentRecsView autenticado, owner-scoped, con allowlist de algorithm_id y DTO versionado."
affects: [02-13, 02-12]

actuals:
  tokens: 9300
  tasks: 3
  commits: 0

tech-stack:
  added: []
  patterns:
    - "Registro explícito de variantes mediante VariantSpec inmutable."
    - "Proyección allowlist-echo en endpoints de recomendaciones."
    - "Explicaciones reproducibles construidas únicamente desde features persistidas."

key-files:
  created:
    - apps/api/recommendations/content/variants.py
    - apps/api/recommendations/content/combine.py
    - apps/api/recommendations/content/explain.py
    - apps/api/recommendations/content/rank.py
    - apps/api/recommendations/tests/test_content.py
  modified:
    - apps/api/recommendations/views.py
    - apps/api/recommendations/urls.py

key-decisions:
  - "El rating externo se lee siempre del snapshot de la versión solicitada; GameWork.total_rating no participa en el cálculo."
  - "El endpoint solo usa request.user y valida algorithm_id por pertenencia estricta al registro, sin importación dinámica."
  - "El arranque en frío devuelve una lista fallback no vacía y la marca explícitamente en el DTO."

patterns-established:
  - "Orden final estable por score descendente y canonical_slug ascendente."
  - "Cada resultado incluye rating_term, indicador de fallback y tabla de contribuciones; la interfaz aporta la prosa localizada."

requirements-completed: [REC-03, REC-06, REC-07, REC-08, REC-09]

coverage:
  - id: D1
    description: "El registro contiene exactamente las tres variantes versionadas y sus modos de combinación producen rankings diferenciados."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content.py#test_algorithm_registry_has_exactly_the_three_versioned_variants / test_combination_modes_have_distinct_ordering_semantics"
        status: pass
    human_judgment: false
  - id: D2
    description: "El término de rating combina snapshots con confianza y usa la mediana de géneros como fallback, sin leer el rating vivo de la obra."
    requirement: "REC-03"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content.py#test_rating_term_uses_corpus_snapshot_and_confidence_blend / test_rating_term_falls_back_to_median_genre_profile"
        status: pass
    human_judgment: false
  - id: D3
    description: "El ranking aplica cold start, exclusión de LibraryEntry, desempate determinista y DTO con hashes y versiones."
    requirement: "REC-06"
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content.py#test_rank_is_deterministic_and_breaks_equal_scores_by_slug / test_cold_start_returns_fallback_and_keeps_seen_work_out / test_versioned_dto_and_item_evidence"
        status: pass
    human_judgment: false
  - id: D4
    description: "El endpoint autenticado de contenido valida límites y algoritmo, ignora user y proyecta solo claves permitidas."
    requirement: "REC-07"
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_content.py#test_content_view_requires_authentication / test_content_view_validates_algorithm_and_clamps_limit"
        status: pass
    human_judgment: false

duration: ~25min
completed: 2026-09-07
status: complete
---

# Fase 2, plan 11: laboratorio de recomendación basado en contenido

**El primer recomendador de contenido queda versionado, reproducible y owner-scoped, con ratings externos congelados, explicaciones numéricas y fallback de arranque en frío.**

## Accomplishments

- Se implementaron `content-cbf-weighted-v1`, `content-cbf-multiplicative-v1` y `content-cbf-twostage-v1`.
- El ranking combina similitud de contenido y rating externo del corpus, excluye cualquier obra ya presente en la biblioteca y garantiza el desempate determinista.
- Se añadieron explicaciones estructuradas por género, hashes de entrada y snapshot, versión de features y limitaciones explícitas para la evaluación simulada.
- Se expuso `/api/recommendations/content/` con autenticación, límites acotados, allowlist de algoritmos y respuesta limitada a claves del contrato.

## Verification

| Comprobación | Resultado |
|---|---|
| `docker compose -f infra/compose.yaml run --rm api pytest apps/api/recommendations/tests/test_content.py -q` | 10 passed |
| `docker compose -f infra/compose.yaml run --rm api pytest apps/api/recommendations -q` | 61 passed |

## Issues Encountered

El commit atómico previsto por el executor no pudo realizarse desde el subagente por las restricciones de escritura de `.git`; la integración y el commit de ambos planes quedan a cargo del hilo principal.

## Next Phase Readiness

El plan 02-13 puede consumir ya el ranking de contenido y sus metadatos de reproducibilidad. El plan 02-12 puede integrar el DTO en la página de recomendaciones después de la Wave 5.
