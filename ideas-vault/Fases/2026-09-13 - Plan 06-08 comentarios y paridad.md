---
fecha: 2026-09-13
estado: vigente
fuente: [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-08-PLAN]]
---

# Plan 06-08: comentarios en ficha y paridad social

## Qué ha cambiado

La ficha de juego conserva `GameComments` como única superficie de comentarios y la
ancla después de los metadatos. La UI mantiene la proyección de comentarios autorizada
por la API y no añade identificadores internos ni datos de propiedad.

Se incorporó el contrato de copy social paralelo para español e inglés, incluyendo
vacíos, errores, acciones, cooldown y 404 genérico. Las utilidades CSS añaden wrapping,
foco visible, objetivos de 44 px, reflow de 320 px/400 % y un badge textual sin animación.

## Impacto

El plan 06-08 deja protegidos por Vitest los contratos de ficha, allowlist, paridad
recursiva y estados responsive. La suite completa del frontend queda condicionada a un
runtime con Chromium; los tests no browser y TypeScript pasan.

## Enlaces relacionados

- [[Fase 6 - Descubrimiento publico]]
- [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-08-SUMMARY]]
