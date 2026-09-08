---
phase: 03-explainable-content-recommenders-and-baseline-comparison
plan: 01
subsystem: api-ui-testing
tags: [django, drf, nextjs, recommendations, protocol-v2, reproducibility]

requires:
  - phase: 02-governed-corpus-external-ratings-evaluation-contract-and-first-advanced-recommender
    provides: "Corpus gobernado, ranker de contenido v1, contrato de evaluación y snapshots de rating"
provides:
  - "Servicio v2 autenticado con manifiesto común de candidatos y DTO estable"
  - "Exclusión de obras vistas, fechas futuras y obras sin señal de rating"
  - "Ranking de contenido real conectado a la página con evidencia determinista"
affects: [03-02, 03-03, 03-04, recommendations, evaluation]

actuals:
  tokens: 7200
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "CandidateManifest único en evaluation.candidates para producto y laboratorio"
    - "DTO allowlisted y validación fail-closed del protocolo y de los resultados del ranker"

key-files:
  created:
    - apps/api/recommendations/service.py
    - apps/api/evaluation/tests/test_protocol_v2.py
    - apps/api/recommendations/tests/test_service.py
  modified:
    - apps/api/evaluation/protocol.py
    - apps/api/evaluation/candidates.py
    - apps/api/evaluation/splits.py
    - apps/api/catalogue/corpus.py
    - apps/api/recommendations/views.py
    - apps/web/app/[locale]/recommendations/page.tsx
    - apps/web/components/ContentRecommendationShelf.tsx
    - apps/web/lib/api.ts

key-decisions:
  - "El ranker v1 queda intacto; el servicio v2 le pasa candidatos ya gobernados y desactiva solo su umbral histórico de 1000 ratings."
  - "El corte de producto es dinámico; las ejecuciones de laboratorio pueden aportar eligibility_cutoff_date explícita y el manifiesto siempre la registra."
  - "La razón es un objeto estructurado de solapamiento de hasta dos géneros reales; si no hay evidencia, se devuelve null y la UI no inventa texto."

patterns-established:
  - "Todos los algoritmos parten de la misma lista ordenada por identidad y del mismo candidate_manifest_sha256."
  - "La lista principal web es un <ol> que conserva literalmente el orden del backend."

requirements-completed: [EVAL-04, EVAL-06, EVAL-07, EVAL-12, QUAL-02]

coverage:
  - id: D1
    description: "Contrato v2, hash estable y rechazo de artefactos/versiones no soportados"
    requirement: EVAL-04
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_protocol_v2.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Manifiesto común: rating válido, exclusión de biblioteca y corte temporal"
    requirement: EVAL-06
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_service.py::test_manifest_excludes_seen_future_and_unrated_works"
        status: pass
    human_judgment: false
  - id: D3
    description: "Payload real score-desc con evidencia determinista y protección frente a resultados externos"
    requirement: EVAL-07
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_service.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Tracer API → página: lista semántica, orden backend y estados parciales"
    requirement: QUAL-02
    verification:
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit -p tsconfig.json"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test --run"
        status: unknown
    human_judgment: true
    rationale: "La suite de overflow requiere el ejecutable Chromium de Playwright, ausente en la imagen; la inspección visual de reflow queda pendiente."

duration: 53min
completed: 2026-09-08
status: complete
---

# Fase 3 Plan 01: tracer de ranking real, candidatos comunes y contrato v2

**El ranking de contenido gobernado llega a la web mediante un manifiesto común, un DTO v2 estable y razones deterministas sin datos ficticios.**

## Performance

- **Duración:** aproximadamente 53 min
- **Inicio:** 2026-09-08T22:45:00+02:00
- **Fin:** 2026-09-08T23:38:25+02:00
- **Tareas:** 2
- **Ficheros modificados o creados:** 18

## Accomplishments

- Se creó `recommendations.service.recommend_for_user`, con validación de protocolo v2, corpus activo, manifiestos hashados de universo explorable y candidatos, y comprobaciones de salida del ranker.
- Se centralizó en `evaluation.candidates` la elegibilidad por rating, la exclusión de cualquier entrada de biblioteca y el corte temporal; v1 conserva sus reglas históricas.
- La página de recomendaciones consume resultados reales, conserva el orden score-desc, usa `<ol>`, muestra razones localizadas solo cuando hay evidencia y conserva el estado de error parcial.
- Se añadieron pruebas de protocolo, candidatos, empates/orden, cold-start implícito y rechazo de payloads fuera del manifiesto.

## Task Commits

1. **Tracer y contrato de candidatos** — `4cebb86` (`feat(03-01): connect governed content recommendations`)
2. **Pruebas de invariantes y adaptación de contrato existente** — `4cebb86` (incluidas atómicamente en el commit de implementación)

**Plan metadata:** este SUMMARY se commitea inmediatamente después del commit de implementación.

## Files Created/Modified

- `apps/api/recommendations/service.py` — adaptador v2 entre candidatos, ranker y DTO autenticado.
- `apps/api/evaluation/candidates.py` — `CandidateManifest` único y construcción del universo común.
- `apps/api/evaluation/protocol.py` — parsing opcional del corte ISO y guard de versión esperada.
- `apps/api/evaluation/splits.py` y `apps/api/catalogue/corpus.py` — propagación del corte temporal.
- `apps/api/recommendations/views.py` — endpoint allowlisted conectado al servicio.
- `apps/web/components/ContentRecommendationShelf.tsx` y `apps/web/app/[locale]/recommendations/page.tsx` — `<ol>`, razones y errores parciales.
- `apps/web/lib/api.ts`, `apps/web/i18n/*`, `apps/web/app/globals.css` — tipos, copy localizada y geometría de tarjeta.
- `apps/api/evaluation/tests/test_protocol_v2.py`, `apps/api/recommendations/tests/test_service.py` — invariantes v2.
- `ideas-vault/Fases/2026-09-08 - Tracer v2 de recomendaciones.md` — decisión y evidencia resumidas en el vault vivo.

## Decisions Made

- El servicio no reimplementa el ranking: construye una sola frontera de candidatos y reutiliza `rank_content_v1` con `min_rating_count=None` para cubrir el nuevo contrato de rating.
- El backend devuelve `reason: null` cuando no puede justificar una tarjeta; la interfaz mantiene la geometría mediante CSS sin texto falso.
- La vista web no expone hashes, versiones ni metodología como copy visible, aunque conserva esos campos en el DTO para identidad y trazabilidad.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regla 2 — Corrección crítica] Unificar el constructor de candidatos**
- **Encontrado durante:** tracer del servicio.
- **Problema:** una primera implementación duplicaba en el servicio la lógica que el vault declara canónica en `evaluation.candidates`.
- **Corrección:** se trasladó `CandidateManifest` y `build_common` a `evaluation.candidates`; el servicio quedó como adaptador.
- **Verificación:** 403 pruebas backend completas y batería específica del plan pasando.
- **Commit:** `4cebb86`.

**2. [Regla 3 — Compatibilidad] Actualizar la aserción de contrato de la vista heredada**
- **Encontrado durante:** regresión de `test_content.py`.
- **Problema:** la prueba esperaba el DTO previo, incompatible con `protocol_version`, manifiesto y `reason` v2.
- **Corrección:** se adaptó la prueba y su fixture para representar una obra con rating elegible; el ranker v1 y sus pruebas no se modificaron semánticamente.
- **Verificación:** 403 pruebas backend completas.
- **Commit:** `4cebb86`.

---

**Total desviaciones:** 2 auto-corregidas.
**Impacto:** ambas fueron necesarias para evitar dos fuentes de verdad y mantener una regresión honesta del contrato público.

## Issues Encountered

- La suite frontend no pudo ejecutar la suite de overflow porque la imagen web no contiene el navegador Chromium requerido por Playwright. Vitest ejecutó 28 pruebas y 6 quedaron omitidas dentro de esa suite; TypeScript pasó. No se modificó el entorno ni se descargó un navegador durante este plan.
- La orden `pytest -q` desde la raíz del contenedor no cargó `apps/api/pytest.ini`; al repetirla desde `/workspace/apps/api` pasó correctamente.

## User Setup Required

Ninguno para el backend ni el flujo v2. Para completar la verificación visual de QUAL-02 será necesario disponer de la revisión de Chromium de Playwright dentro del entorno web.

## Next Phase Readiness

Plan 03-02 puede reutilizar `CandidateManifest`, el DTO v2 y las razones estructuradas para añadir señales de contenido sin crear otro camino de ranking. Plan 03-03 puede usar el mismo hash y corte en los artefactos experimentales.

## Self-Check: PASSED

- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_protocol_v2.py apps/api/recommendations/tests/test_service.py -q` → 9 passed.
- Batería ampliada de regresión → 66 passed.
- Suite backend completa desde `/workspace/apps/api` → 403 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit -p tsconfig.json` → passed.
- `git diff --check` → passed.

---
*Phase: 03-explainable-content-recommenders-and-baseline-comparison*
*Plan: 03-01*
*Completed: 2026-09-08*
