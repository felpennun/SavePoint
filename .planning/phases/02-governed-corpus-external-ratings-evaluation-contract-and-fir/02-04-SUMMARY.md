---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 04
subsystem: ui
tags: [catalogue, filters, facets, accessibility, nextjs, i18n]

requires:
  - phase: 02-03
    provides: "Contrato de parámetros repetidos para filtros de catálogo en la API."
  - phase: 02-07
    provides: "Base visual y responsive para el catálogo y los controles de filtrado."
provides:
  - "Filtros de género y plataforma como facetas multi-selección con checkboxes y URLs GET compartibles."
  - "Parseo, serialización, recuento y eliminación individual de valores repetidos en catalogue-filters.ts."
  - "Claves de interfaz EN/ES, orden estable de plataformas y cobertura unitaria del contrato."
affects: [02-06, 02-12]

actuals:
  tokens: 7600
  tasks: 3
  commits: 0

tech-stack:
  added: []
  patterns:
    - "Facetas server-rendered basadas en <details> y formularios GET, sin estado cliente."
    - "Normalización y deduplicación de parámetros repetidos antes de construir la consulta."

key-files:
  created:
    - apps/web/components/FacetMenu.tsx
    - apps/web/lib/__tests__/catalogue-filters.test.ts
  modified:
    - apps/web/lib/catalogue-filters.ts
    - apps/web/components/FilterBar.tsx
    - apps/web/app/[locale]/catalogue/page.tsx
    - apps/web/i18n/dictionary.ts
    - apps/web/i18n/en.ts
    - apps/web/i18n/es.ts
    - apps/web/lib/api.ts
    - apps/web/app/globals.css
    - apps/web/vitest.config.ts
    - e2e/a11y.spec.ts

key-decisions:
  - "Las facetas se mantienen como componentes de servidor y usan checkboxes nativos para conservar la degradación sin JavaScript."
  - "La lista de plataformas usa un orden explícito que prioriza consolas actuales y conserva después las generaciones anteriores."
  - "Los valores desconocidos se eliminan de la representación visible, pero la consulta sigue siendo tolerante y compartible."

patterns-established:
  - "Cada selección repetida genera su propio FilterChip y removeHref elimina únicamente esa ocurrencia."
  - "Los paneles de faceta flotan en escritorio y fluyen en móvil, con objetivos táctiles y anillo de foco visibles."

requirements-completed: [CAT-02, QUAL-05]

coverage:
  - id: D1
    description: "El catálogo admite varios géneros y plataformas mediante parámetros repetidos, con parseo, serialización y eliminación individual deterministas."
    requirement: "CAT-02"
    verification:
      - kind: unit
        ref: "apps/web/lib/__tests__/catalogue-filters.test.ts (5 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Las facetas, chips, textos semánticos y límites de foco están implementados con paridad EN/ES y layout responsive."
    requirement: "QUAL-05"
    verification:
      - kind: unit
        ref: "apps/web/tests/i18n.test.ts (5 tests)"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml exec -T web pnpm --dir apps/web exec next build"
        status: pass
    human_judgment: false
  - id: D3
    description: "El pase E2E de accesibilidad, teclado y viewport del catálogo queda preparado para ejecutarse con Chromium."
    requirement: "QUAL-05"
    verification:
      - kind: e2e
        ref: "docker compose -f infra/compose.yaml exec -T web pnpm exec playwright test e2e/a11y.spec.ts --project=chromium"
        status: unknown
    human_judgment: true
    rationale: "El contenedor actual no declara el proyecto Playwright chromium; requiere configuración o ejecución manual en un entorno con el navegador instalado."

duration: ~20min
completed: 2026-09-07
status: complete
---

# Fase 2, plan 04: facetas multi-selección del catálogo

**El catálogo ofrece filtros de género y plataforma multi-selección, accesibles y compartibles mediante URLs GET, con interfaz localizada y orden estable de plataformas.**

## Accomplishments

- Se transformaron género y plataforma en arrays normalizados, deduplicados y serializados como parámetros repetidos.
- Se añadió `FacetMenu` con checkboxes nativos, semántica visible, limpieza por faceta, chips individuales y comportamiento responsive.
- Se actualizó la página del catálogo y la API frontend para conservar todos los valores seleccionados, incluyendo la paginación.
- Se amplió la prueba E2E para cubrir la selección combinada de dos géneros y una plataforma, sin mantener el contador de resultados eliminado por decisión del autor.

## Issues Encountered

- La prueba E2E no pudo arrancar porque la configuración disponible no declara el proyecto `chromium`. El build y las pruebas unitarias sí pasan; queda pendiente ejecutar el pase de navegador cuando se configure el runner.

## Next Phase Readiness

El frontend ya expone el contrato multi-filtro que necesitan los planes 02-06 y 02-12. La única verificación pendiente es el pase de navegador real de `e2e/a11y.spec.ts`.
