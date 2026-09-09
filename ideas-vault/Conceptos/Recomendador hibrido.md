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

## Propuesta MMR futura — 2026-09-09

`hybrid-mmr-v1` es una **Propuesta — no implementado**. Primero reutilizaría
la relevancia de `hybrid-weighted-cf-v1`, definida como
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`, y mantendría el
fallback Weighted cuando faltase señal colaborativa. Después aplicaría la regla
MMR vigente sobre las 100 mejores candidatas o `5 * K` cuando sea mayor: el
primer elemento sería el de mayor relevancia base y cada siguiente maximizaría
`0,80 * relevancia - 0,20 * similitud_maxima`, con `lambda = 0,80` y coseno de
`fs-v9`. La profundidad de presentación propuesta es de 20 resultados.

Se distingue de `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`, que aplican
MMR a relevancias de contenido, y de `hybrid-weighted-cf-v1`, que no tiene esa
segunda etapa. La propuesta no tiene worker, estantería, registro, snapshot ni
resultados de evaluación; no se ha ejecutado ningún algoritmo para ella. La
fuente canónica es
[`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md)
y debe conservar el corpus, las exclusiones, las semillas y el contrato de
evaluación si se retoma en el futuro.

## Enlaces

- [[Recomendador basado en contenido]] · [[Recomendador colaborativo]] · [[Arranque en frio]]
- [[Fase 4 - Colaborativo e hibrido]]
