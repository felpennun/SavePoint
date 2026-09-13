---
phase: 06-public-discovery-and-resilient-enrichment
plan: 05
subsystem: ui
tags: [nextjs, typescript, catalogue, filters, facets, accessibility, ssr]

# Dependency graph
requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: "Contrato CAT-05 local con filtros, facets y ordenación determinista en Django/DRF"
provides:
  - "Integración Next.js de todas las dimensiones CAT-05 mediante GET reproducible"
  - "Facets allowlisted con checkboxes nativos, acciones Aplicar/Limpiar y degradación sin JavaScript"
  - "Sincronización SSR de cookies, filtros, ordenación y paginación con el API local"
affects: [06-06, 06-08, 06-09, catalogue-discovery]

# Actuals (#2632)
actuals:
  tokens: 9325
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "El contrato backend es la fuente de verdad de los nombres de query params y facets"
    - "Los valores repetibles se serializan con URLSearchParams.append en orden determinista"
    - "El estado de discovery permanece en la URL y se carga por Server Component"
    - "Las opciones seleccionables se restringen a facets devueltas por el API local"

key-files:
  created:
    - .planning/phases/06-public-discovery-and-resilient-enrichment/deferred-items.md
  modified:
    - apps/web/lib/api.ts
    - apps/web/lib/catalogue-filters.ts
    - apps/web/components/FilterBar.tsx
    - apps/web/components/FacetMenu.tsx
    - apps/web/components/FilterDropdown.tsx
    - apps/web/app/[locale]/catalogue/page.tsx
    - apps/web/tests/catalogue-filters.test.ts

key-decisions:
  - "La UI adopta los nombres exactos del contrato local (`edition`, `genre`, `franchise`, `developer`, `publisher`, `mode`, `year_from`, `year_to`, `date_from`, `date_to`) y no crea filtros paralelos."
  - "La página SSR reenvía la cookie disponible al endpoint de catálogo, manteniendo la frontera de sesión sin llamadas directas a proveedores externos."
  - "Las facets CAT-05 se muestran con una única gramática first-party; los slugs desconocidos se descartan de los controles y no pueden ampliar resultados."

requirements-completed: [CAT-05]

coverage:
  - id: D1
    description: "El catálogo Next.js conserva todos los filtros CAT-05, orden y paginación en URLs GET reproducibles."
    requirement: CAT-05
    verification:
      - kind: unit
        ref: "apps/web/lib/__tests__/catalogue-filters.test.ts — 11 tests de repetición, orden, límites, eliminación y facets desconocidas"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Las facets visibles usan controles nativos, acciones Aplicar/Limpiar, paneles nombrados y enhancement Escape/foco de retorno, con layout responsive existente."
    requirement: CAT-05
    verification:
      - kind: other
        ref: "git diff --check; revisión de FilterBar, FacetMenu, FilterDropdown y FilterDropdownScript"
        status: pass
    human_judgment: true
    rationale: "La imagen web no contiene Chromium para ejecutar la suite visual existente; la comprobación responsive/teclado final requiere UAT en navegador."

# Metrics
duration: 25min
completed: 2026-09-13
status: complete
---

# Phase 06 Plan 05: Public catalogue discovery in Next.js Summary

**CAT-05 queda conectado a Next.js con facets completas, URLs GET reproducibles y controles first-party accesibles sin estado de browse exclusivo del cliente.**

## Performance

- **Duration:** 25 min.
- **Tasks:** 2/2.
- **Files del write-set:** 8 modificados/creados; además se registró la verificación diferida exigida por el workflow.

## Accomplishments

- `fetchCatalogueList` y sus DTOs representan las facets `platforms`, `editions`, `genres`, `franchises`, `developers`, `publishers`, `modes`, `tags`, `dates` y `year_range`, y reenvían la cookie SSR sin invocar proveedores.
- `catalogue-filters.ts` normaliza los parámetros exactos del backend, repite cada facet con `append`, valida fechas/años y conserva orden, filtros y paginación al construir enlaces.
- El catálogo presenta todas las facets locales con `FilterBar`/`FacetMenu`, chips eliminables, checkboxes nativos y acciones explícitas de aplicar/limpiar; `FilterDropdown` mantiene nombre accesible y el enhancement existente para Escape y foco.

## Task Commits

Cada tarea se comprometió atómicamente:

1. **Task 1: Tracer: filtro GET → fetch SSR → catálogo reproducible** — `96888d1` (test), `681df16` (feat).
2. **Task 2: Facets accesibles y estados extremos de filtro** — `4a357e0` (feat).

El commit documental final se generará después de verificar este resumen, estado, roadmap y requisitos.

## Files Created/Modified

- `apps/web/lib/api.ts` — DTOs de facets CAT-05, parámetros repetibles y fetch SSR con Cookie opcional.
- `apps/web/lib/catalogue-filters.ts` — allowlist de parámetros, parseo, serialización, eliminación individual y restricción a facets locales.
- `apps/web/components/FilterBar.tsx` — toolbar responsive que presenta las dimensiones del contrato y rangos de año.
- `apps/web/components/FacetMenu.tsx` — checkboxes repetibles con Aplicar/Limpiar y estado accesible.
- `apps/web/components/FilterDropdown.tsx` — panel de facet con nombre accesible y degradación nativa.
- `apps/web/app/[locale]/catalogue/page.tsx` — carga SSR de todas las facets, cookie forwarding y paginación completa.
- `apps/web/lib/__tests__/catalogue-filters.test.ts` — pruebas unitarias de contrato y seguridad de controles.
- `apps/web/tests/catalogue-filters.test.ts` — actualización de la allowlist de sort soportada por el backend.

## Decisions Made

Se aplicaron D-01 y D-02: el backend sigue siendo completo y la URL GET es la fuente de verdad. La UI no añade un endpoint ni una llamada de red al proveedor; solo convierte el DTO local en controles y conserva la consulta al paginar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Mantener compatibilidad de consumidores con filtros parciales.**

- **Encontrado durante:** Task 1.
- **Problema:** añadir nuevas arrays obligatorias a `CatalogueFilters` rompía un test existente que construye un objeto parcial para contar filtros.
- **Corrección:** las nuevas arrays son opcionales en el tipo público y las utilidades las tratan como vacías cuando faltan; `parseFilters` sigue devolviendo siempre la forma completa.
- **Verificación:** TypeScript y los 11 tests focalizados pasan.
- **Commit:** `681df16`.

**2. [Rule 2 - Missing critical] Evitar controles con slugs que no proceden de facets locales.**

- **Encontrado durante:** Task 1.
- **Problema:** los parámetros de URL son entrada no confiable y no deben convertirse directamente en opciones visuales.
- **Corrección:** `restrictSelectedFilters` cruza cada selección con la facet recibida del API antes de renderizar controles/chips.
- **Verificación:** test de slug desconocido y TypeScript pasan.
- **Commit:** `681df16`.

**3. [Rule 1 - Bug] Eliminar el atributo `disabled` inválido de `<details>`.**

- **Encontrado durante:** Task 2.
- **Problema:** `<details>` no admite el atributo nativo `disabled`; mantenerlo produciría una semántica HTML inconsistente.
- **Corrección:** se conserva `aria-disabled` y el comportamiento visual existente, dejando el control nativo válido.
- **Verificación:** test focalizado, TypeScript y diff check pasan.
- **Commit:** `4a357e0`.

### Verificación diferida fuera de alcance

La invocación exacta del plan ejecuta también `components/__tests__/nav-overflow.test.tsx`, que no puede iniciar porque Chromium no está instalado en la imagen web. No se instaló ninguna dependencia ni se modificó esa suite; la incidencia está registrada en `deferred-items.md` y en `.planning/WINDOWS.md`. La suite focalizada CAT-05 (11/11) y TypeScript sí pasan.

## Issues Encountered

- El fichero no rastreado `apps/api/tests/test_public_profile.py` ya estaba presente y se conservó intacto por pertenecer a trabajo ajeno.
- La ejecución agregada de Vitest queda pendiente de un runtime Chromium disponible; no afecta a la validación unitaria ni al typecheck del write-set.

## User Setup Required

None - no se requieren servicios externos ni nuevas dependencias.

## Next Phase Readiness

El frontend ya puede consumir el contrato CAT-05 completo en SSR y está listo para que los planes posteriores reutilicen la misma allowlist, los DTOs de facets y la semántica GET. Queda pendiente ejecutar la matriz visual/teclado en un contenedor con Chromium instalado.

---
*Phase: 06-public-discovery-and-resilient-enrichment*
*Completed: 2026-09-13*

## Self-Check: PASSED

- `06-05-SUMMARY.md` existe en la ruta canónica.
- Existen los commits `96888d1`, `681df16` y `4a357e0`.
- TypeScript, los 11 tests focalizados de CAT-05 y `git diff --check` pasan.
- La suite agregada con `pnpm test -- --run catalogue-filters` queda registrada como diferida únicamente por Chromium ausente en un test Playwright preexistente.
