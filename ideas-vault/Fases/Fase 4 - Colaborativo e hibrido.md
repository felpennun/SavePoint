---
tags: [fase/4, roadmap, tema/recomendadores]
---

# Fase 4 - Colaborativo e hibrido

Meta: comparar metodos colaborativos e hibridos bajo el protocolo ya congelado y
documentar conclusiones acotadas por la simulacion, con los mismos candidatos,
exclusiones, particiones, metricas y presupuesto de tuning que los metodos
previos.

## Enlaces

- [[Recomendador colaborativo]] · [[Recomendador hibrido]]
- [[Protocolo de evaluacion congelado]] · [[Arranque en frio]]
- [[Requisitos - Recomendaciones]] · [[Requisitos - Tesis y metodologia con agentes]]

## Decision concretada — 2026-09-09

La fase queda implementada con `cf-user-knn-v1` y
`hybrid-weighted-cf-v1`. El primero usa vecinos de usuario sobre valoraciones
explicitas centradas, minimo de dos obras comunes y K=20 vecinos positivos; el
segundo combina Weighted y CF con pesos 0,60/0,40. Cada uno tiene worker y
estanteria web propios. La evaluacion offline se prepara con un proceso por
algoritmo y tiempos individuales y globales. La fuente canonica es
`docs/verification/recommendation-architecture-2026-09-09.md` y el plan de
ejecucion es `.planning/phases/04-collaborative-and-hybrid-comparison/`.

## Frontera de alcance y propuesta — 2026-09-09

La comparación de esta fase se limita a las dos variantes implementadas y
mantiene intactas las variantes MMR de contenido. Item-KNN, los modelos
neuronales y otros modelos complejos quedan fuera por el corpus controlado y
sintético, el uso de valoraciones explícitas, el protocolo congelado, la
necesidad de interpretación y el control del espacio de tuning. Es una
decisión de alcance y validez de la fase, no una afirmación de inferioridad
algorítmica, y no produce resultados comparables adicionales.

`hybrid-mmr-v1` queda registrado como **Propuesta — no implementado**. Su
definición futura combinaría primero la relevancia
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`, con fallback Weighted
cuando falte señal colaborativa, y después aplicaría MMR sobre 100 candidatas o
`5 * K`, con `lambda = 0,80`, coseno de `fs-v9` y 20 resultados presentados.
Se distinguiría de `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`, que aplican
MMR a relevancias de contenido, y de `hybrid-weighted-cf-v1`, que no incorpora
esa segunda etapa. No tiene worker, estantería, registro, snapshot ni
resultados. La fuente canónica es
[`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md).

## Enlaces relacionados

- [[Recomendador hibrido]] · [[Recomendador colaborativo]]
- [[Recomendador basado en contenido]] · [[Arranque en frio]]
- [[Requisitos - Recomendaciones]] · [[Requisitos - Tesis y metodologia con agentes]]
