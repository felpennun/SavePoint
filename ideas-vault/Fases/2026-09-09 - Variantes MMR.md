# Variantes MMR

Fecha: 2026-09-09
Estado: vigente

## Decisión

Se implementan dos algoritmos nuevos de diversidad: `content-cbf-mmr-v1`,
basado en Weighted, y `content-cbf-mmr-pop-v1`, basado en Weighted-Pop.

MMR no reemplaza la relevancia base. Primero puntúa las candidatas y conserva
el pool de las 100 mejores, o cinco veces K cuando sea mayor. Después selecciona
greedy con `0,80 * relevancia - 0,20 * similitud_maxima` frente a los juegos ya
seleccionados. La similitud usa el coseno de los vectores fs-v9.

Cada algoritmo tiene un worker y una estantería propios. El mismo ranker se
usa en web y offline, con `lambda = 0,80` congelado en el contrato v8.

## Enlaces

- Contrato: [`protocol.json`](../../docs/methodology/protocol.json).
- Arquitectura: [`recommendation-architecture-2026-09-09.md`](../../docs/verification/recommendation-architecture-2026-09-09.md).
- Protocolo: [`evaluation-protocol.md`](../../docs/methodology/evaluation-protocol.md).

## Ampliación híbrida — 2026-09-10

`hybrid-mmr-v1` está implementado como tercera variante MMR. Primero combina
Weighted y User-kNN con pesos `0,60/0,40`; después aplica la misma selección
MMR sobre `max(100, 5 * K)`, `lambda = 0,80` y coseno de `fs-v9`. Tiene worker,
estantería y entrada offline propios, y publica 20 resultados. La fórmula de
rating compartida es `rating_final = rating_quality * rating_confidence`, con
`rating_quality = rating_bayesian_normalized ^ 2`, `rating_confidence = n /
(n + 25)` y `n = total_rating_count`.

La implementación no implica que MMR híbrido sea superior: esa hipótesis solo
se podrá valorar tras la evaluación offline de los 400 usuarios.
