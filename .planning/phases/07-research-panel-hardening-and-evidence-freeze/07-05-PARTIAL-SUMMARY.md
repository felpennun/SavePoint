---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 05
subsystem: browser-verification
tags: [playwright, chromium, axe, accessibility, research-panel, admin]
requires:
  - 07-03
  - 07-04
provides:
  - Task 1 browser-visible verification evidence
affects:
  - QUAL-01
  - QUAL-04
  - SEC-07
tech-stack:
  added: []
  patterns:
    - Process-only demo credentials with trace disabled
    - Focused real axe context for the large catalogue surface
key-files:
  created:
    - e2e/admin-security.spec.ts
    - e2e/research-panel.spec.ts
    - .planning/phases/07-research-panel-hardening-and-evidence-freeze/07-05-PARTIAL-SUMMARY.md
  modified:
    - e2e/a11y.spec.ts
    - e2e/deployed-smoke.spec.ts
decisions:
  - Task 1 se detiene tras su verificación; Tasks 2 y 3 no se han iniciado.
  - Las credenciales demo se obtuvieron en memoria desde Compose y solo se expusieron al proceso Playwright.
metrics:
  attempts: 2
  first_run: "55 passed, 1 failed"
  final_run: "56 passed, 0 failed"
  skipped: 0
  completed: 2026-09-14
status: partial
---

# Fase 07 Plan 05: resumen parcial de Task 1

Task 1 queda verificada en el árbol actual con una segunda corrida completa en Chromium: **56/56 PASS**, código de salida 0. La suite ejecutada fue exactamente:

```text
corepack pnpm exec playwright test e2e/a11y.spec.ts e2e/research-panel.spec.ts e2e/admin-security.spec.ts e2e/deployed-smoke.spec.ts --project=chromium
```

La primera corrida terminó completa, sin cancelación, con 55 PASS y un fallo real en el journey de teclado: `/es/collection` renderiza la región accesible `Colección`, no un heading con ese nombre. Se corrigió únicamente el locator del test para consultar `getByRole("region", { name: "Colección" })` y se repitió la suite una sola vez.

La segunda corrida confirmó:

- Research Viewer y Platform Admin con roles separados, 404 neutro y ausencia de controles destructivos.
- Panel localizado en español e inglés, filtros, comparación, equivalencia tabla/SVG y exportaciones.
- axe real focalizado en la tarjeta representativa de catálogo, con `runOnly` explícito y timeout documentado de 15 s; el panel se escaneó de forma real sin sustituir axe por un stub.
- Responsive y teclado en 320/375/820 px, ambos temas y zoom 400 %, además de smoke de health/login/catálogo/detalle.
- Variables de credenciales solo de proceso, trazas desactivadas y limpieza de variables al terminar; no se persistieron valores sensibles.
- Ningún test omitido activo: 56 PASS, 0 FAIL, 0 skipped.

## Estado de ejecución

- **Task 1:** completada y verificada; pendiente de integración posterior del plan.
- **Task 2:** no iniciada; no se generó ni modificó el paquete de evidencia.
- **Task 3:** no iniciada; no se ejecutó la gate de lanzamiento ni se creó signoff.

## Limitaciones

Este artefacto es parcial y no declara el plan ni la fase completos. No sustituye la verificación de generación de evidencia, secretos, dependencias, backups, restore, health/headers y signoff prevista en Tasks 2/3.

## Commits

Se registrarán commits parciales con `Refs #70`. La issue no se cierra en este punto.
