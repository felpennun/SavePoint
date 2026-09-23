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

## 2026-09-14: integración LaTeX condensada

La memoria activa en `thesis/TFG.tex` carga capítulos condensados con el núcleo en
`06_algoritmos.tex` y `07_experimentos_resultados.tex`. Estos documentos remiten a las
matrices verificadas y mantienen la frontera v15/v16. Las tablas de resultados usan
`tabularx` con ancho acotado; la comprobación visual final y cualquier captura no existente
continúan pendientes de compilación en Prism y de confirmación del autor.

## 2026-09-14: inventario de la Fase A de la memoria

La Fase B quedó bloqueada hasta superar el gate integral de la Fase A. El gate integral
se superó el 2026-09-14 tras validar las seis matrices y el manifiesto de fuentes vivas.

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

## 2026-09-22: corrección de la trazabilidad de requisitos (81/94 → 92/94)

`.planning/REQUIREMENTS.md` se quedó desactualizado tras las Fases 01.1, 3 y 7: su checklist y
su tabla de trazabilidad seguían marcando como `Pending` once requisitos (CAT-02, REC-10,
QUAL-05, EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-12, QUAL-02, PORT-02, PORT-03) que esas
fases ya habían cerrado con evidencia firmada en sus `SUMMARY.md`. La memoria (capítulo
`05_diseno_actualizado.tex`) heredó la cifra errónea de 81/94 completos y 13 pendientes. Se
reconciliaron ambos ficheros contra la evidencia real de fase: quedan 92/94 completos y solo
dos pendientes genuinos, ambos parciales dentro del mismo contrato de evaluación — EVAL-08
(repetir la comparación con varias semillas; los contrastes estadísticos sobre la semilla
única ya están hechos) y EVAL-11 (retroproyectar sobre la ejecución histórica v15 la captura
de entorno/recursos que el ejecutor paralelo ya sabe registrar para ejecuciones futuras). Los
capítulos `05_diseno_actualizado.tex` y `09_conclusiones_actualizadas.tex` se corrigieron en
consecuencia.
