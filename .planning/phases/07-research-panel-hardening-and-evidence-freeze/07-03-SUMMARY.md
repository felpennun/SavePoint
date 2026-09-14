---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 03
subsystem: ui
tags: [nextjs, react, typescript, research-panel, accessibility, playwright, i18n]

# Dependency graph
requires:
  - phase: 07-research-panel-hardening-and-evidence-freeze
    provides: "API de evaluación protegida, DTO allowlisted y capability can_view_research de 07-01/07-02"
provides:
  - "Ruta SSR localizada /[locale]/research con login seguro y 404 neutro"
  - "Panel de evidencia read-only con filtros GET, SVG, tabla equivalente, detalles y exportaciones same-origin"
  - "Estados loading, empty, error, partial y populated con cobertura frontend"
  - "Imagen web reproducible para Chromium/Playwright en Debian Bookworm"
affects: [07-05, frontend, accessibility, evaluation-evidence]

# Actuals (#2632) - pairs with the plan estimate to calibrate future estimates.
actuals:
  tokens: 16448
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "La UI consume DTOs de evaluación ya preparados y delega autorización y cálculos al backend."
    - "Los filtros de investigación se propagan como GET con una allowlist cerrada y sin valores duplicados."
    - "El SVG y la tabla semántica renderizan el mismo array y orden de filas."
    - "La imagen de pruebas instala Chromium fijado por Playwright junto con sus bibliotecas runtime Debian."

key-files:
  created:
    - apps/web/app/[locale]/research/page.tsx
    - apps/web/app/[locale]/research/loading.tsx
    - apps/web/app/[locale]/research/error.tsx
    - apps/web/components/ResearchPanel.tsx
    - apps/web/components/ResearchFilters.tsx
    - apps/web/components/ResearchComparisonChart.tsx
    - apps/web/components/ResearchComparisonTable.tsx
    - apps/web/components/ResearchEvidenceDetails.tsx
    - apps/web/components/ResearchExports.tsx
    - apps/web/tests/research-panel.test.tsx
    - ideas-vault/Fases/2026-09-14 - Panel de investigacion y Chromium reproducible.md
  modified:
    - apps/web/lib/api.ts
    - apps/web/components/AppShell.tsx
    - apps/web/app/[locale]/layout.tsx
    - apps/web/middleware.ts
    - apps/web/i18n/dictionary.ts
    - apps/web/i18n/es.ts
    - apps/web/i18n/en.ts
    - apps/web/app/globals.css
    - apps/web/Dockerfile

key-decisions:
  - "La capability can_view_research se obtiene server-side desde Django; el enlace de navegación y la ruta nunca autorizan por cookie de presencia."
  - "Las exportaciones son anchors same-origin a rutas entregadas por el backend; React no serializa ni transforma resultados."
  - "El runner web incluye las librerías Debian y Chromium de Playwright en /ms-playwright para que la verificación del plan sea limpia y reproducible."

patterns-established:
  - "ResearchPanelStatus expresa explícitamente empty, error, partial y populated en el árbol accesible."
  - "Las columnas de tabla usan caption y scope; el contenedor ancho tiene foco y scroll interno."

requirements-completed: [EVAL-13, EVAL-14, SEC-01, QUAL-01, QUAL-04]

coverage:
  - id: D1
    description: "Ruta SSR localizada con capability visibility, login seguro para 401 y 404 neutro para 403/404."
    requirement: SEC-01
    verification:
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#sends one request with only known, single-value query filters"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Panel de comparación con filtros GET, SVG inline, tabla semántica equivalente, evidencia y descargas same-origin."
    requirement: EVAL-13
    verification:
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#keeps the SVG and semantic table equivalent in source order"
        status: pass
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#preserves selected filters in same-origin export links"
        status: pass
    human_judgment: false
  - id: D3
    description: "Estados explícitos y accesibilidad estructural para loading, empty, error, partial y populated, con nulls, foco de tabla y copy ES/EN."
    requirement: QUAL-01
    verification:
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#renders loading with a polite status and skeletons"
        status: pass
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#renders an alert error state and a partial state with one notice"
        status: pass
    human_judgment: true
    rationale: "La suite demuestra semántica y contratos estáticos; la inspección visual/axe en 320px, 400% y ambos temas está asignada al plan 07-05."
  - id: D4
    description: "La presentación no importa runners/métricas ni ofrece re-run, delete o serialización client-side."
    requirement: EVAL-14
    verification:
      - kind: unit
        ref: "apps/web/tests/research-panel.test.tsx#keeps presentation components free of runner imports and DTO serialization"
        status: pass
    human_judgment: false
  - id: D5
    description: "Chromium/Playwright funciona en la imagen web fijada sin dependencias nativas ausentes ni instalación global."
    requirement: QUAL-04
    verification:
      - kind: other
        ref: "docker compose -f infra/compose.yaml build web"
        status: pass
      - kind: automated_ui
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test -- --run research-panel (12 suites, 70 tests)"
        status: pass
    human_judgment: false

# Metrics
duration: 2h 00m
completed: 2026-09-14
status: complete
---

# Phase 7 Plan 3: Panel de investigación localizado y endurecido

**Panel SSR de evidencia congelada con comparación SVG/tabla equivalente, filtros allowlisted, estados accesibles y Chromium reproducible en Docker.**

## Performance

- **Duration:** 2h 00m (incluye diagnóstico y reconstrucción de la imagen web)
- **Started:** 2026-09-13T23:07:39Z
- **Completed:** 2026-09-14T01:07:30Z
- **Tasks:** 3
- **Files modified or created:** 20

## Accomplishments

- Ruta `/es/research` y `/en/research` con fetch SSR, capability server-side, redirect de login con `next` seguro y 404 neutro.
- Panel read-only con filtros GET explícitos, tabla semántica equivalente al SVG, detalles de procedencia, limitaciones y descargas same-origin.
- Estados loading/empty/error/partial/populated, copy bilingüe, CSS responsive con scroll interno de tabla, foco visible y reduced motion.
- Suite frontend ampliada a 70 tests y TypeScript validado en el contenedor fijado.

## Task Commits

Cada tarea fue comprometida atómicamente:

1. **Task 1: Tracer de ruta localizada SSR a comparación visible** - `9a13987` (`feat`)
2. **Task 2: Completar filtros, estados, evidencia, descargas y responsive** - `bda11ad` (`feat`)
3. **Task 3: Pruebas frontend de equivalencia y accesibilidad estructural** - `2c10946` (`test`)

Commit adicional de sincronización obligatoria del vault: `2c58028` (`docs`).

El commit de cierre de metadatos se crea después de este SUMMARY e incluye `Closes #68`.

## Files Created/Modified

- `apps/web/app/[locale]/research/page.tsx` - Server Component de la ruta, filtros, fetch y mapeo de 401/403/404.
- `apps/web/components/ResearchPanel.tsx` - Orquestación read-only de estados, comparación, evidencia y descargas.
- `apps/web/components/ResearchComparisonChart.tsx` - SVG inline con viewBox visible y valores recibidos.
- `apps/web/components/ResearchComparisonTable.tsx` - Tabla semántica con caption, scope y scroll enfocable.
- `apps/web/components/ResearchEvidenceDetails.tsx` - `dl` de run, hashes, procedencia y limitaciones.
- `apps/web/components/ResearchExports.tsx` - Enlaces same-origin a exportaciones del backend.
- `apps/web/lib/api.ts` - DTOs y fetch helpers server-side con allowlist de filtros.
- `apps/web/components/AppShell.tsx` y `apps/web/app/[locale]/layout.tsx` - Visibilidad de Research Viewer por capability.
- `apps/web/middleware.ts` - Inclusión de research en la UX de rutas autenticadas.
- `apps/web/i18n/dictionary.ts`, `apps/web/i18n/es.ts`, `apps/web/i18n/en.ts` - Contrato de copy bilingüe.
- `apps/web/app/globals.css` - Tokens y reglas responsive del panel.
- `apps/web/tests/research-panel.test.tsx` - Cobertura de estados, equivalencia, seguridad de query, exports y paridad.
- `apps/web/Dockerfile` - Bibliotecas runtime y Chromium Playwright fijado para el runner de pruebas.
- `ideas-vault/Fases/2026-09-14 - Panel de investigacion y Chromium reproducible.md` - Nota viva de la decisión y su fuente canónica.

## Decisions Made

- Se mantuvo el backend como única autoridad para autorización, métricas, orden y serialización.
- Se usó una allowlist explícita (`run`, `algorithm`, `cohort`, `metric`) y se ignoraron arrays/keys desconocidas en runtime.
- Se añadió Chromium a la imagen `web` de pruebas porque la verificación literal también ejecuta la suite existente de Playwright; no se instaló nada global ni se cambió el compose.
- Se consolidó el aviso partial para evitar duplicar la misma advertencia en el panel y el detalle de evidencia.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Añadida compatibilidad reproducible de Chromium a la imagen web**

- **Found during:** Task 2 (verificación del plan).
- **Issue:** La imagen `node:24.20.0-slim` no tenía `libglib-2.0.so.0`; después, el runner limpio tampoco tenía el navegador `chromium_headless_shell-1234` de Playwright.
- **Fix:** Se instalaron bibliotecas runtime Debian Bookworm y se descargó el Chromium fijado por el paquete en `/ms-playwright`, con `PLAYWRIGHT_BROWSERS_PATH` explícito. No hubo instalación global ni modificación de `infra/compose.yaml`.
- **Files modified:** `apps/web/Dockerfile`.
- **Verification:** `docker compose -f infra/compose.yaml build web` y la orden exacta de Vitest pasan; el fallo original queda reproducido y resuelto.
- **Committed in:** `bda11ad` (parte del commit de Task 2).

**2. [Rule 2 - Missing Critical] Cerrada la allowlist de filtros en runtime**

- **Found during:** Task 2 (revisión de contrato y amenaza T-07-03-03).
- **Issue:** Iterar todas las keys de un objeto permitía propagar una key desconocida si llegaba fuera del tipado TypeScript.
- **Fix:** Se recorren sólo `run`, `algorithm`, `cohort` y `metric`, y se ignoran valores que no sean strings únicos no vacíos.
- **Files modified:** `apps/web/lib/api.ts`, `apps/web/tests/research-panel.test.tsx`.
- **Verification:** La prueba de solicitud única y filtros allowlisted pasa dentro de las 12 suites.
- **Committed in:** `bda11ad`.

**3. [Rule 1 - Bug] Eliminada la duplicación del aviso partial**

- **Found during:** Task 2 (revisión de estados).
- **Issue:** El estado partial mostraba el mismo aviso en el panel y dentro de detalles.
- **Fix:** El aviso vive una sola vez en `ResearchPanel`; los detalles siguen mostrando procedencia y limitaciones.
- **Files modified:** `apps/web/components/ResearchPanel.tsx`, `apps/web/components/ResearchEvidenceDetails.tsx`, `apps/web/tests/research-panel.test.tsx`.
- **Verification:** La prueba comprueba una sola aparición del copy partial.
- **Committed in:** `bda11ad`.

---

**Total deviations:** 3 auto-fixed (Rule 1: 1, Rule 2: 1, Rule 3: 1).
**Impact on plan:** Cambios mínimos y directamente necesarios para seguridad del contrato y para que la verificación Docker del plan sea reproducible; no se amplió la responsabilidad UI ni se invadieron 07-04/07-05.

## Issues Encountered

- La primera ejecución de la suite pasó los tests estáticos pero falló al lanzar Chromium por la biblioteca nativa ausente; la segunda, tras instalar el navegador sólo en un contenedor efímero, evidenció la falta de cache del browser. Ambos fallos están resueltos en la imagen.
- Una aserción inicial dependía del orden de atributos HTML y otra no consideraba la opción de filtro repetida en el markup; se ajustaron las pruebas para comprobar semántica, no serialización incidental.
- No se detectaron stubs funcionales, tests omitidos ni comandos `<verify>` pendientes dentro de este plan. La validación visual/axe completa queda explícitamente en 07-05.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 07-05 puede ejecutar Playwright/axe sobre la ruta ya integrada, con Chromium y sus dependencias disponibles dentro de la imagen `web`.
- La comprobación visual de 320px, 400%, ambos temas, teclado y reduced motion debe permanecer en 07-05; no se modifica aquí su plan ni sus artefactos.

## Self-Check: PASSED

- SUMMARY presente en la ruta canónica.
- Commits `9a13987`, `bda11ad`, `2c10946` y `2c58028` encontrados en el historial.
- No se mezclaron cambios concurrentes de 07-04/07-05.

---
*Phase: 07-research-panel-hardening-and-evidence-freeze*
*Completed: 2026-09-14*
