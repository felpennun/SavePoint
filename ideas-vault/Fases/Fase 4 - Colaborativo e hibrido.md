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

## Implementación posterior autorizada — 2026-09-10

La orden posterior del autor incorpora `hybrid-mmr-v1` a la fase. Ya cuenta
con worker y estantería independientes en web, entrada en el runner offline y
la misma implementación de MMR: relevancia `0,60` Weighted + `0,40`
User-kNN, fallback Weighted, pool `max(100, 5 * K)`, `lambda = 0,80`, coseno
`fs-v9` y 20 resultados. La rejilla y el protocolo v10 lo identifican como
una configuración adicional.

También queda adoptada la señal global
`rating_final = rating_quality * rating_confidence`, con calidad bayesiana al
cuadrado, confianza `n / (n + 25)` y `n = total_rating_count`. Los ratings
personales y la señal colaborativa conservan su semántica propia. Todavía no
hay resultados de la evaluación de los 400 usuarios.

Fuente canónica: [`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md).

## Decision concretada — 2026-09-09

La fase queda implementada con `cf-user-knn-v1` y
`hybrid-weighted-cf-v1`. El primero usa vecinos de usuario sobre valoraciones
explicitas centradas, minimo de dos obras comunes y K=20 vecinos positivos; el
segundo combina Weighted y CF con pesos 0,60/0,40. Cada uno tiene worker y
estanteria web propios. La evaluacion offline se prepara con un proceso por
algoritmo y tiempos individuales y globales. La fuente canonica es
`docs/verification/recommendation-architecture-2026-09-09.md` y el plan de
ejecucion es `.planning/phases/04-collaborative-and-hybrid-comparison/`.

## Frontera de alcance y propuesta — decisión histórica previa — 2026-09-09

La comparación inicial de esta fase se limitaba a las dos variantes implementadas y
mantiene intactas las variantes MMR de contenido. Item-KNN, los modelos
neuronales y otros modelos complejos quedan fuera por el corpus controlado y
sintético, el uso de valoraciones explícitas, el protocolo congelado, la
necesidad de interpretación y el control del espacio de tuning. Es una
decisión de alcance y validez de la fase, no una afirmación de inferioridad
algorítmica, y no produce resultados comparables adicionales.

En ese estado previo, `hybrid-mmr-v1` quedaba registrado como **Propuesta — no implementada**. Su
definición futura combinaría primero la relevancia
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`, con fallback Weighted
cuando falte señal colaborativa, y después aplicaría MMR sobre 100 candidatas o
`5 * K`, con `lambda = 0,80`, coseno de `fs-v9` y 20 resultados presentados.
Se distinguía de `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`, que aplican
MMR a relevancias de contenido, y de `hybrid-weighted-cf-v1`, que no incorpora
esa segunda etapa. En ese estado no tenía worker, estantería, registro,
snapshot ni resultados. La fuente canónica es
[`recommendation-architecture-2026-09-09`](../../docs/verification/recommendation-architecture-2026-09-09.md).

## Enlaces relacionados

- [[Recomendador hibrido]] · [[Recomendador colaborativo]]
- [[Recomendador basado en contenido]] · [[Arranque en frio]]
- [[Requisitos - Recomendaciones]] · [[Requisitos - Tesis y metodologia con agentes]]
