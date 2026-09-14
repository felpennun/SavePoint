---
fecha: 2026-09-14
estado: vigente
fuente: [[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-03-PLAN]]
tags: [fase-07, investigacion, frontend, reproducibilidad, accesibilidad]
---

# Panel de investigación y Chromium reproducible

## Que ha cambiado

El plan 07-03 entrega la ruta localizada de investigación como panel SSR de solo lectura:
filtros GET allowlisted, comparación SVG con tabla semántica equivalente, evidencia,
exportaciones same-origin y estados loading, empty, error, partial y populated. La visibilidad
del enlace depende de `can_view_research` comunicado por el backend.

La imagen `web` instala las bibliotecas runtime de Chromium para Debian Bookworm y el navegador
Chromium fijado por Playwright en `/ms-playwright`. Así, la suite exacta del plan funciona en un
contenedor limpio sin instalación global ni preparación manual del host.

## Impacto

La UI presenta los valores ya preparados por Django y no recalcula, ordena, agrega, redondea ni
autoriza resultados en React. La verificación local queda reproducible con la imagen fijada y
mantiene el contrato de accesibilidad estructural; la comprobación visual/axe de viewport queda
para 07-05 según el plan de fase.

## Enlaces relacionados

- [[Fase 7 - Panel de investigacion y hardening]]
- [[2026-09-14 - API protegida del panel de investigacion]]
- [[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-UI-SPEC]]
