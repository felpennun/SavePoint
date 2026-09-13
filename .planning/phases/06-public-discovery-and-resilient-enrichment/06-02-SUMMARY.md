---
phase: 06-public-discovery-and-resilient-enrichment
plan: 02
subsystem: api
tags: [django, drf, postgresql, catalogue, facets, provenance]

# Dependency graph
requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: "Modelo de catálogo y contrato de fuentes aprobado de 06-01"
provides:
  - "CAT-05: filtros GET reproducibles y facets para todas las dimensiones declaradas"
  - "Publisher con identidad estable y procedencia de snapshot local aprobado"
  - "Importador local idempotente y fail-closed sin proveedor externo en requests"
affects: [06-03, 06-04, 06-05, public-discovery]

# Actuals (#2632)
actuals:
  tokens: 13372
  tasks: 3
  commits: 6

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Allowlist de parámetros GET, límites acotados y orden total determinista"
    - "Facets calculados sobre el conjunto gobernado antes de paginar"
    - "Enriquecimiento Publisher exclusivamente desde snapshot local APPROVED"
    - "Edition reutiliza la relación existente GameRelease -> Edition"

key-files:
  created:
    - apps/api/catalogue/migrations/0019_phase6_catalogue_publishers.py
    - apps/api/catalogue/tests/test_schema.py
  modified:
    - apps/api/catalogue/models.py
    - apps/api/catalogue/search.py
    - apps/api/catalogue/serializers.py
    - apps/api/catalogue/views.py
    - apps/api/catalogue/igdb.py
    - apps/api/catalogue/management/commands/import_igdb_catalogue.py
    - apps/api/catalogue/tests/test_search.py
    - apps/api/catalogue/tests/test_igdb_import.py

key-decisions:
  - "Publisher es una entidad aditiva con igdb_id, slug y campos de procedencia; el payload vivo del proveedor no puede crearla."
  - "Las dimensiones CAT-05 se filtran con slugs desconocidos ignorados, intersección entre dimensiones y unión dentro de cada dimensión."
  - "GameCard conserva su proyección compacta para mantener el presupuesto de queries; las dimensiones completas viven en facets y detalle."
  - "El snapshot aprobado valida estado, fuente, IDs únicos y SHA-256 antes de importar; cada Publisher conserva el hash del snapshot."

patterns-established:
  - "Las views solo consultan el catálogo local y nunca instancian ni llaman a IgdbClient."
  - "Los filtros inválidos se rechazan antes del ORM con respuesta 400 acotada."

requirements-completed: [CAT-05]

coverage:
  - id: D1
    description: "Filtros GET y facets deterministas para juegos, plataformas, ediciones, géneros, franquicias, desarrolladores, publishers, fechas, modos y tags."
    requirement: CAT-05
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py::test_cat05_filters_and_facets_cover_all_declared_dimensions"
        status: pass
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue/tests/test_search.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Publisher enriquecido solo desde snapshot local aprobado, con procedencia, idempotencia y preservación de Edition."
    requirement: CAT-05
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_igdb_import.py::test_approved_snapshot_imports_publisher_with_provenance_and_keeps_edition"
        status: pass
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue/tests/test_igdb_import.py -q"
        status: pass
    human_judgment: false
  - id: D3
    description: "Cadena de migración PostgreSQL y límite fail-closed contra llamadas externas durante requests."
    requirement: CAT-05
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_schema.py"
        status: pass
      - kind: integration
        ref: "apps/api/catalogue/tests/test_search.py::test_cat05_view_fails_closed_if_igdb_client_is_invoked"
        status: pass
      - kind: other
        ref: "manage.py check; migrate --plan; makemigrations --check --dry-run"
        status: pass
    human_judgment: false

# Metrics
duration: 35min
completed: 2026-09-13
status: complete
---

# Phase 06 Plan 02: Backend CAT-05 catalogue discovery and approved local enrichment Summary

**CAT-05 queda implementado en backend con búsqueda GET determinista, facets completos y Publisher procedente únicamente de snapshots locales aprobados.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-13T16:05:04+02:00
- **Completed:** 2026-09-13T16:39:30+02:00
- **Tasks:** 3/3
- **Files modified:** 10 del write-set del plan

## Accomplishments

- Se añadieron todos los filtros/facets CAT-05, con validación previa al ORM, límites, ignorancia de slugs desconocidos y orden total estable.
- Se añadió `Publisher` con migración PostgreSQL, DTOs completos en detalle y procedencia `source_url`, licencia, fecha y SHA-256 del snapshot.
- El importador acepta solo snapshots locales `APPROVED`, es idempotente, no crea Publisher desde el cliente vivo y preserva Edition bajo `GameRelease`.
- Se verificó explícitamente que una view no puede invocar IGDB y que no hay deriva de esquema.

## Task Commits

1. **Task 1: filtros GET y facets CAT-05** - `12b3852` (test), `0ccf463` (feat)
2. **Task 2: enriquecimiento Publisher desde snapshot aprobado** - `0019daf` (feat)
3. **Task 3: esquema, fail-closed y contratos de importación** - `ca20768` (test), `5b005fd` (fix)

**Plan metadata:** commit final de documentación generado después de actualizar SUMMARY, STATE, ROADMAP y REQUIREMENTS.

## Files Created/Modified

- `apps/api/catalogue/models.py` - Publisher y relación many-to-many desde GameWork.
- `apps/api/catalogue/migrations/0019_phase6_catalogue_publishers.py` - migración aditiva y encadenada sobre 0018.
- `apps/api/catalogue/search.py` - parser, filtros, facets, caps y orden determinista.
- `apps/api/catalogue/serializers.py` - dimensiones completas para el detalle de juego.
- `apps/api/catalogue/views.py` - rechazo 400 de parámetros de paginación inválidos.
- `apps/api/catalogue/igdb.py` - cliente local de snapshots aprobados y hash SHA-256.
- `apps/api/catalogue/management/commands/import_igdb_catalogue.py` - importación Publisher condicionada al snapshot.
- `apps/api/catalogue/tests/test_search.py` - contrato CAT-05 y fail-closed.
- `apps/api/catalogue/tests/test_igdb_import.py` - procedencia, idempotencia y frontera proveedor/snapshot.
- `apps/api/catalogue/tests/test_schema.py` - constraints, columnas y relación Edition.

## Decisions Made

Se mantuvieron las decisiones documentadas: Edition no se duplica; Publisher se identifica por `igdb_id`; los facets se calculan antes de paginar; y no existe enriquecimiento externo dentro de requests/SSR.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corregido import faltante de `Max`.**
- **Encontrado durante:** Task 1.
- **Problema:** la nueva agregación de facets referenciaba `Max` sin importarlo.
- **Corrección:** se añadió el import y se repitió la suite de búsqueda.
- **Verificación:** `46 passed`.
- **Commit:** `0ccf463`.

**2. [Rule 1 - Bug/performance] Preservado el presupuesto de queries de GameCard.**
- **Encontrado durante:** Task 1.
- **Problema:** prefetchear todas las dimensiones en la tarjeta elevó el presupuesto existente.
- **Corrección:** se dejó la tarjeta compacta y se sirvieron dimensiones completas mediante facets y detalle.
- **Verificación:** `46 passed` y el test de presupuesto existente pasa.
- **Commit:** `0ccf463`.

**3. [Rule 3 - Secuenciación TDD] Publisher fue adelantado al slice tracer.**
- **Encontrado durante:** Task 1/2.
- **Problema:** los tests tracer de facets necesitaban la entidad Publisher y su migración antes de completar la implementación del importador.
- **Corrección:** se incluyeron modelo/migración en el GREEN de Task 1; el test de Task 2 no pudo observar una fase RED independiente.
- **Verificación:** suite de importación y suite combinada pasan.
- **Impacto:** solo cambia el orden de commits; no amplía el write-set.

### Verificación auxiliar no ejecutable

Ruff no está instalado en la imagen `api` (`exec ruff failed: No such file or directory`). No es una verificación declarada por el plan; las verificaciones principales de Django, migración, esquema, búsqueda e importación sí pasaron.

**Total de desviaciones:** 3 auto-fijadas y 1 verificación auxiliar no ejecutable.
**Impacto:** sin bloqueo para CAT-05; no se instalaron dependencias ni se alteró el entorno.

## Issues Encountered

Ninguno bloqueante. Las pruebas de PostgreSQL se ejecutaron contra el servicio `db` de Compose.

## Known Stubs

- `apps/api/catalogue/serializers.py`: los fallbacks existentes `Not available`/placeholder de plataforma y portada representan ausencia legítima de datos locales y no una fuente externa ni un stub de CAT-05.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

El backend queda listo para que los siguientes planes conecten la selección multi-filtro y la presentación de facets en UI; las requests públicas pueden consumir resultados locales reproducibles sin llamadas al proveedor.

---
*Phase: 06-public-discovery-and-resilient-enrichment*
*Completed: 2026-09-13*

## Self-Check: PASSED

- SUMMARY existe en la ruta canónica.
- Los commits de tareas `12b3852`, `0ccf463`, `0019daf`, `ca20768` y `5b005fd` existen en el historial.
- Las verificaciones principales registradas pasan: `86 passed`, `manage.py check`, `migrate --plan` y `makemigrations --check --dry-run`.
