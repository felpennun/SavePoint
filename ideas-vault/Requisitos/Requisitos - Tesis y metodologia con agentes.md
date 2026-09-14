---
tags: [requisitos, tema/metodologia]
---

# Requisitos - Tesis y metodologia con agentes

- **DOC-01** (Fase 1, hecho): decisiones de arquitectura y tecnologia con alternativas y rationale.
- **DOC-02** (Fase 2, hecho): dataset, API, modelo de datos y normalizacion documentados.
- **DOC-03** (Fase 4): cada algoritmo documenta teoria, formulacion, parametros y limitaciones.
- **DOC-04** (Fase 2): protocolo, metricas, resultados y amenazas a la validez.
- **DOC-05** (Fase 7): tablas y figuras de tesis generadas desde artefactos inmutables.
- **DOC-06** (Fase 7): tesis de ejemplo, reglas de formato y anotaciones del tutor como referencias.
- **AGENT-01/02/03** (Fase 1, hecho): roles de agentes; protocolos/prompts/config/modelos;
  separacion propuesta / verificacion / decision.
- **AGENT-04** (Fase 2): controles contra alucinacion, sesgo, error y exposicion.
- **AGENT-05/06** (Fase 7): reproducibilidad, costes, limitaciones y amenazas; disclosure de IA.

## Enlaces

- [[Metodo de trabajo asistido por agentes]] · [[Ledger de agentes]] · [[check-evidence]]
- [[Controles metodologicos AGENT-04]] · [[Separacion propuesta, verificacion y decision]]
- [[ADR (concepto)]]

## 2026-09-14: inventario de la Fase A de la memoria

El inventario canónico para la memoria está en el repositorio: `thesis/SOURCE-MANIFEST.json`,
`thesis/STRUCTURE-MAP.md`, `thesis/EVIDENCE-MATRIX.md`,
`thesis/ALGORITHM-MATRIX.md`, `thesis/SIGNAL-MATRIX.md`,
`thesis/REQUIREMENTS-TRACEABILITY.md` y `thesis/FIGURE-PLAN.md`. Este vault solo los
resume y enlaza: no sustituye las fuentes, el código, los planes ni los artefactos de
verificación versionados.

La evidencia publicada v15, basada en `fs-v12-curated-tags-idf`, permanece separada del
protocolo y del código v16, que usan `fs-v13-family-weighted-tags`. Cualquier redacción
posterior debe conservar esa separación, las limitaciones de población sintética y la
ausencia de generalización directa a usuarios reales.
