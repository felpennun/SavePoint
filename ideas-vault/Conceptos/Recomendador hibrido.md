---
tags: [concepto, tema/recomendadores, fase/4]
---

# Recomendador hibrido

Combinacion documentada de evidencia de contenido y colaborativa (REC-05) que
transiciona de forma predecible para usuarios frios y con historial escaso. Su
teoria, formulacion, parametros y limitaciones se documentan para la tesis
(DOC-03).

## Implementacion aceptada — 2026-09-09

Se concreta como `hybrid-weighted-cf-v1`, con `0,60` para el algoritmo Weighted
de contenido y `0,40` para `cf-user-knn-v1`. Si no hay señal colaborativa,
mantiene Weighted como fallback. Tiene worker y estanteria propios tanto en la
web como en la suite offline. Fuente:
`docs/verification/recommendation-architecture-2026-09-09.md`.

## Propuesta MMR futura — decisión histórica previa — 2026-09-09

En ese momento, `hybrid-mmr-v1` era una **Propuesta — no implementada**. Primero reutilizaría
la relevancia de `hybrid-weighted-cf-v1`, definida como
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`, y mantendría el
fallback Weighted cuando faltase señal colaborativa. Después aplicaría la regla
MMR vigente sobre las 100 mejores candidatas o `5 * K` cuando sea mayor: el
primer elemento sería el de mayor relevancia base y cada siguiente maximizaría
`0,80 * relevancia - 0,20 * similitud_maxima`, con `lambda = 0,80` y coseno de
`fs-v9`. La profundidad de presentación propuesta es de 20 resultados.

Se distinguía de `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`, que aplican
MMR a relevancias de contenido, y de `hybrid-weighted-cf-v1`, que no tiene esa
segunda etapa. En ese estado no tenía worker, estantería, registro, snapshot ni
resultados de evaluación. La
fuente canónica es
[`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md)
y debe conservar el corpus, las exclusiones, las semillas y el contrato de
evaluación si se retoma en el futuro.

## Enlaces

- [[Recomendador basado en contenido]] · [[Recomendador colaborativo]] · [[Arranque en frio]]
- [[Fase 4 - Colaborativo e hibrido]]

## Implementación de MMR híbrido — 2026-09-10

Por decisión explícita del autor, `hybrid-mmr-v1` deja de ser una propuesta y
queda implementado. Reutiliza `hybrid-weighted-cf-v1` con pesos `0,60/0,40`,
mantiene el fallback Weighted y aplica MMR sobre `max(100, 5 * K)` con
`lambda = 0,80`, coseno `fs-v9` y publicación de 20 resultados. Tiene worker,
estantería, explicación y entrada offline independientes. La evaluación de
los 400 usuarios todavía no se ha ejecutado.

La señal global usada por el componente de contenido es
`rating_final = rating_quality * rating_confidence`, con
`rating_quality = rating_bayesian_normalized ^ 2`,
`rating_confidence = n / (n + m)`, `n = total_rating_count` y `m = 25`.
No reemplaza ratings personales ni la señal colaborativa.

Fuente canónica: [`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md).
