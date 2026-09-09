# Verificación fs-v7 con Felipe — 2026-09-09

## Cambios verificados

La configuración publicada usa `feature_set_version = fs-v7`,
`similarity_rule_version = facet-similarity-v3` y `rating-confidence-v3`.
Los vectores se reconstruyeron para las 190.479 obras del corpus
`2026.09.2`. La nueva huella de configuración es:

`4cb1d3b2c1fa241886d3df8a9d0bc09cbe2c242bcbb2412ee8a46a6231ddd9f0`

El snapshot activo de Felipe corresponde a la revisión de colección 14 y se
publicó después de que terminaran los diez workers.

## Auditoría de obras objetivo

| Obra | Rating IGDB | `total_rating_count` | Géneros | Franquicia | Desarrollador |
|---|---:|---:|---|---|---|
| Hollow Knight: Silksong | 92,4795 | 506 | Adventure, Indie, Platform | — | Team Cherry |
| Hades II | 88,9248 | 163 | Adventure, Hack and slash, Indie, RPG | — | Supergiant Games |
| Terraria | 82,3387 | 1.064 | Adventure, Indie, Platform, RPG, Simulator, Strategy | — | Re-Logic |

Silksong y Hades II cumplen el corpus algorítmico y comparten desarrollador
con una semilla de Felipe. No reciben bonus de franquicia porque esas obras no
tienen franquicia IGDB asociada en los datos importados.

## Similitud de contenido

| Obra | Núcleo género/plataforma | Bonus saga/desarrollador | Similitud final |
|---|---:|---:|---:|
| Silksong | 0,792569 | 0,120000 | 0,912569 |
| Hades II | 0,800001 | 0,114300 | 0,914301 |
| Terraria | 0,918396 | 0 | 0,918396 |

El bonus de Silksong alcanza `0,12` por la coincidencia exacta con Team Cherry.
Hades II recibe `0,1143` por la coincidencia ponderada con Supergiant Games.
Terraria obtiene una similitud de núcleo mayor porque comparte más géneros y
plataformas, pero no recibe bonus opcional.

## Puntuaciones publicadas

| Algoritmo | Silksong | Hades II | Terraria |
|---|---:|---:|---:|
| Weighted | 0,880827 | 0,857631 | 0,838211 |
| Negative | 0,880827 | 0,857631 | 0,838211 |
| Weighted + PopScore | 0,898760 | 0,878563 | 0,863229 |
| Negative + PopScore | 0,898760 | 0,878563 | 0,863229 |
| Two-stage | 4,134460 | 4,120900 | 4,108518 |
| Two-stage + PopScore | 4,139213 | 4,127537 | 4,117143 |
| Multiplicative | 0,736226 | 0,663233 | 0,597978 |
| Multiplicative + PopScore | 0,845966 | 0,760904 | 0,686972 |

Las dos obras relacionadas con la colección aparecen en las estanterías de
contenido publicadas. Terraria queda por encima en similitud, pero Silksong y
Hades II superan a Terraria en las variantes multiplicativas porque su rating
IGDB y su rating-confidence son mayores. En `recency-v1` no entraron en los 20
primeros resultados publicados en esta revisión.

## Estado de ejecución

- Workers completados: `10/10 succeeded`.
- Snapshot activo: revisión 14, `fs-v7`.
- Caché: `190.479/190.479` vectores.
- Pruebas backend dirigidas: `192 passed`.
- TypeScript web: `tsc --noEmit` correcto.
- Evaluación offline de los 400 usuarios: no ejecutada.

## Limitación de datos

La ausencia de franquicia en Hollow Knight, Silksong, Hades y Hades II limita
la evidencia del bonus de saga. Es una ausencia del dato IGDB importado, no una
penalización del algoritmo. La señal de desarrollador sí está disponible y se
ha verificado en las dos coincidencias esperadas.
