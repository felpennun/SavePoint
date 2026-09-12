---
tags: [fase/03, evaluacion, cohortes, reproducibilidad, limitacion]
estado: aceptado-con-limitaciones
fecha: 2026-09-12
---

# Cierre backend de Fase 3 y limitaciones metodológicas

## Decisión

Se cierra la parte backend, offline y documental de la Fase 3. El test v15 no se
repite: su marcador está consumido y el protocolo fija una única ejecución del test.
La ausencia de réplicas multi-semilla se registra como limitación metodológica
explícita, no se oculta ni se sustituye por una afirmación de robustez.

## Resultado

El análisis derivado de [[../../docs/verification/evaluation-cohorts-400-test-2026-09-12-v15|la evidencia por cohortes]]
usa solo el artefacto v15 y el manifiesto congelado. Los 79 usuarios evaluables
pertenecen a `active_history_10_to_20`; los 10 usuarios `no_history` se describen como
cold start y no se convierten artificialmente en puntuaciones cero.

El artefacto histórico permite desglosar por cohorte precisión, recall, nDCG, MAP,
diversidad intra-lista y novedad. Cobertura de catálogo, HHI y cobertura de predicción
se mantienen globales porque no se guardaron las listas completas por usuario.

## Reproducibilidad futura

El runner paralelo captura en nuevos runs versiones de Python/paquetes, plataforma,
CPU, tiempo de CPU y RSS máximo, sin secretos ni inventario sensible de la máquina.
Esa información se registra hacia adelante; no se finge que una medición actual
describe el entorno histórico de v15.

## Evidencia UI/E2E

El punto 7 (UI, Playwright y E2E) queda cubierto por la otra LLM mediante
`e2e/recommendations.spec.ts`. La evidencia registra tres pruebas Playwright pasadas
para orden API/DOM, ausencia de superficie metodológica y 320 px/temas/teclado. Esta
sesión no modificó `apps/web/**` ni `design/**`.

## Fuentes canónicas

- [[../../docs/verification/evaluation-results-400-test-2026-09-12-v15|Resultados v15]].
- [[../../docs/verification/evaluation-checkpoint-400-users-2026-09-12-v15|Checkpoint v15]].
- [[../../docs/methodology/evaluation-v15-appendix|Adenda metodológica v15]].
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-03-SUMMARY|Resumen 03-03]].
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-04-SUMMARY|Resumen 03-04]].
