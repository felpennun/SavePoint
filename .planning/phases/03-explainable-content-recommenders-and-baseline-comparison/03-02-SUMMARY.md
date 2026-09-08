---
phase: 03-explainable-content-recommenders-and-baseline-comparison
plan: 02
subsystem: recommendations-api-ui-testing
tags: [django, nextjs, content-based, explainability, reproducibility]

requires:
  - phase: 03-explainable-content-recommenders-and-baseline-comparison
    provides: "Servicio v2, manifiesto común de candidatos y trazador de ranking real"
provides:
  - "Perfil positivo con ratings propios y variante negativa aislada"
  - "Señales escalares normalizadas y ausencia explícita de datos no gobernados"
  - "Razones estructuradas, deterministas y localizables de hasta dos señales"
affects: [03-03, 03-04, recommendations, evaluation]

actuals:
  tokens: 11000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "ProfileInputs separa afinidad positiva y evidencia negativa protegida"
    - "Los campos no persistidos se publican como ausentes, nunca como ceros o valores inventados"

key-files:
  created:
    - apps/api/recommendations/tests/test_content_v2.py
    - apps/api/recommendations/tests/test_explanations_v2.py
  modified:
    - apps/api/recommendations/content/features.py
    - apps/api/recommendations/content/profile.py
    - apps/api/recommendations/content/rank.py
    - apps/api/recommendations/content/variants.py
    - apps/api/recommendations/content/explain.py
    - apps/api/recommendations/service.py
    - apps/web/components/ContentRecommendationShelf.tsx
    - apps/web/lib/api.ts

key-decisions:
  - "Solo completed y playing con rating propio >= 3,5 aportan afinidad positiva; pending y ausencia de rating no se interpretan como gusto."
  - "La variante content-cbf-neg-v1 exige tres ratings bajos del mismo género y mantiene una penalización visible y reversible."
  - "Franquicia, desarrollador y PopScore permanecen ausentes hasta que haya persistencia y snapshot gobernado; el ranker declara esa disponibilidad en vez de fingir la señal."

patterns-established:
  - "El DTO interno del ranker serializa parámetros, umbrales de perfil, disponibilidad de señales y evidencia por resultado."
  - "La API pública transforma únicamente tokens con nombres canónicos disponibles y devuelve reason: null si no puede justificarlos."

requirements-completed: [EVAL-05, EVAL-06, EVAL-07]

coverage:
  - id: D1
    description: "Perfil positivo de juegos completed/playing valorados y señal negativa protegida por tres observaciones"
    requirement: EVAL-05
    verification:
      - kind: unit
        ref: "apps/api/recommendations/tests/test_content_v2.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Variantes con parámetros serializados, señales normalizadas y ausencia honesta de PopScore"
    requirement: EVAL-06
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_content.py y test_content_v2.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Razones locales, deterministas y de dos señales como máximo en el contrato de producto"
    requirement: EVAL-07
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_explanations_v2.py y test_service.py"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit -p tsconfig.json"
        status: pass
    human_judgment: false

duration: 98min
completed: 2026-09-09
status: complete
---

# Fase 3 Plan 02: señales de contenido y explicaciones deterministas

**El recomendador separa gusto positivo, aversión protegida y señales de catálogo gobernadas, con razones breves que no inventan atributos ausentes.**

## Rendimiento

- **Duración:** aproximadamente 98 min
- **Inicio:** 2026-09-08T23:45:00+02:00
- **Fin:** 2026-09-09T01:23:00+02:00
- **Tareas:** 2
- **Ficheros modificados o creados:** 16

## Logros

- Se versionó el espacio de features como `fs-v2`, se normalizan rating externo y `log1p(rating_count)` dentro del snapshot y se registra la disponibilidad de cada familia de señal.
- `ProfileInputs` separa la afinidad positiva de `completed`/`playing` valorados al menos 3,5 de una señal negativa de género, activada solo con tres experiencias bajas.
- Se añadió `content-cbf-neg-v1`, con parámetros visibles, orden estable y penalización independiente de las tres variantes positivas.
- Las explicaciones producen tokens ordenados de género o plataforma y la API los convierte a nombres localizados; cuando no hay evidencia disponible devuelve `null`.

## Commits de tareas

1. **Features y variantes explicables de contenido** — `3addc55` (`feat(03-02): add governed content signal variants`)
2. **Razones deterministas para el ranking** — `3addc55` (incluida atómicamente con la implementación y sus pruebas)

**Metadatos del plan:** este resumen se registra en el commit de cierre.

## Ficheros creados o modificados

- `apps/api/recommendations/content/{features,profile,rank,variants,explain,combine}.py` — señales v2, perfiles, variante negativa y trazas de explicación.
- `apps/api/recommendations/service.py` — traducción segura de tokens de género/plataforma al DTO público.
- `apps/web/components/ContentRecommendationShelf.tsx` y `apps/web/lib/api.ts` — contrato de razón de señales localizado.
- `apps/api/recommendations/tests/test_content_v2.py` y `test_explanations_v2.py` — cobertura nueva de perfiles, ausencias, estabilidad y razones.

## Decisiones tomadas

- Se reutilizan los pesos de actividad ya publicados para el perfil positivo; no se afirman pesos finales nuevos. La penalización negativa se identifica como variante experimental reversible y se serializa con sus parámetros.
- Un `rating_count` sin snapshot de rating se conserva como ausente. De igual forma, PopScore es `null` y `popscore_available: false` hasta contar con un snapshot fechado y gobernado.
- Saga/franquicia y desarrollador se mantienen como seams con cobertura medida, porque el modelo actual no los persiste. Esta restricción proviene del contexto canónico y evita contaminar el experimento con llamadas en vivo.

## Desviaciones del plan

### 1. Integración necesaria con el contrato público

- **Motivo:** el plan enumera los módulos de ranking, pero las razones de plataforma no podían llegar a la interfaz con el DTO anterior, limitado a géneros.
- **Corrección:** se adaptaron `service.py`, el tipo TypeScript y `ContentRecommendationShelf` para transportar tokens `genre`/`platform` sin cambiar el copy ES/EN ya aprobado.
- **Verificación:** 43 pruebas de recomendaciones/evaluación y TypeScript pasan.

### 2. Señales sin fuente persistida

- **Motivo:** franquicia, desarrollador y PopScore no existen en el corpus gobernado actual; el contexto de la Fase 3 prohíbe usar llamadas externas vivas para suplirlos.
- **Corrección:** se implementó un manifiesto de disponibilidad y valores ausentes explícitos, dejando las funciones de cobertura como punto de extensión.
- **Verificación:** tests v2 comprueban que la ausencia no se convierte en cero; la suite completa pasa.

**Impacto:** no se incorpora ningún dato ficticio ni dependencia nueva. La ingestión versionada de esas tres fuentes sigue siendo una precondición explícita para activarlas en una variante futura.

## Problemas encontrados

- El contenedor web no tiene un navegador Playwright, pero el chequeo TypeScript pasó. No se descargó un navegador ni se modificó el entorno para este plan.
- La ejecución completa con un contenedor efímero retiró sus logs al terminar; se repitió en un contenedor temporal identificado y se obtuvo el resultado completo antes de eliminarlo.

## Configuración requerida al usuario

Ninguna.

## Preparación para el siguiente plan

El plan 03-03 puede consumir la nueva familia de variantes y sus parámetros serializados en sus artefactos, manteniendo explícita la ausencia de PopScore y facets aún no persistidos. Antes de activar esas señales se necesita un importador con procedencia, cobertura y snapshot versionado.

## Autoverificación

- `docker compose -f infra/compose.yaml run --rm api sh -c "cd /workspace/apps/api && pytest recommendations/tests/test_content.py recommendations/tests/test_content_features.py recommendations/tests/test_content_v2.py recommendations/tests/test_explanations_v2.py recommendations/tests/test_service.py evaluation/tests/test_runner.py -q"` → 43 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit -p tsconfig.json` → passed.
- Suite backend completa desde `/workspace/apps/api` → 409 passed en 74,82 s.

---
*Fase: 03-explainable-content-recommenders-and-baseline-comparison*
*Completado: 2026-09-09*
