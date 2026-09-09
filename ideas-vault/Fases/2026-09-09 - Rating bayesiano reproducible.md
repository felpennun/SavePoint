# Rating bayesiano reproducible

Fecha: 2026-09-09

## Decisión

La señal de rating IGDB cambia a `rating-confidence-v4-bayesian`. La nota de
cada candidata se contrae hacia la media IGDB ponderada del corpus congelado
mediante 25 pseudo-observaciones. Después conserva la transformación
cuadrática que separa las notas altas.

## Motivo

El multiplicador de volumen anterior podía dejar demasiado cerca una nota alta
con pocas valoraciones y otra sostenida por evidencia abundante. La media
bayesiana incorpora `total_rating_count` una sola vez, de una forma estándar,
continua y explicable.

## Alcance

La fórmula es común a `rank_content_v1`, web, workers y evaluación offline;
no modifica el corpus candidato, los vectores fs-v9 ni los pesos de las
variantes. El protocolo pasa a v8 para que los resultados previos no se
comparen como si procedieran de la misma señal.

## Enlaces

- Contrato: [`protocol.json`](../../docs/methodology/protocol.json).
- Verificación: [`recommendation-bayesian-rating-felipe-2026-09-09.md`](../../docs/verification/recommendation-bayesian-rating-felipe-2026-09-09.md).
- Decisión de facetas relacionada: [`Decision fs-v9 F0,5 y bonus calibrados`](2026-09-09%20-%20Decision%20fs-v9%20F0,5%20y%20bonus%20calibrados.md).

