---
tags: [concepto, tema/evaluacion, fase/7]
---

# Panel de investigacion

Panel que compara ejecuciones inmutables, configuraciones, algoritmos, cohortes,
metricas, tiempos, procedencia y limitaciones mediante tablas y graficos
accesibles, y exporta figuras y datos listos para la tesis (EVAL-13, EVAL-14).
Los graficos no son el registro academico: se exportan los datos subyacentes en
CSV/JSON.

## Contrato de evidencia v15 — 2026-09-14

El contrato ejecutable de la Fase 7 queda en
`apps/api/evaluation/panel_contract.py` y su evidencia en
`docs/verification/phase-07-evidence-contract.md`. El panel consume el artefacto v15
y el snapshot de cohortes mediante rutas relativas allowlisted, SHA-256 e identidad
de protocolo; no importa el runner ni recalcula rankings.

La publicacion conserva metricas exactas y marca como `null` las metricas globales que
no pueden desagregarse por cohorte. El `protocol.json` vigente puede ser posterior al
v15: solo se usan sus anclajes compartidos y nunca se presenta como origen historico
de las cifras publicadas.

Fuente canonica: [[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-00-PLAN.md]]

## Enlaces

- [[Artefacto de evaluacion reproducible]] · [[Accesibilidad WCAG 2.2 AA]]
- [[Fase 7 - Panel de investigacion y hardening]]
