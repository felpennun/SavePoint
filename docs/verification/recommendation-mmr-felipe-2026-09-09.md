# Verificación de variantes MMR en Felipe — 2026-09-09

## Alcance

Se añadieron exactamente dos variantes nuevas al catálogo publicable:

| Variante | Algoritmo base | Worker | Estantería |
|---|---|---|---|
| `content-cbf-mmr-v1` | `content-cbf-weighted-v1` | `recommendation-worker-mmr` | Afinidad diversa por contenido |
| `content-cbf-mmr-pop-v1` | `content-cbf-weighted-pop-v1` | `recommendation-worker-mmr-pop` | Afinidad diversa con popularidad |

Las nueve variantes anteriores no se sustituyen ni se reescriben. MMR es una
capa de selección posterior a la puntuación base: conserva la relevancia de
Weighted o Weighted-Pop y reduce la redundancia entre resultados.

## Contrato reproducible

- `lambda = 0,80`.
- El primer resultado es el de mayor relevancia base.
- Cada resultado posterior maximiza `0,80 * relevancia - 0,20 *
  similitud_máxima_con_los_seleccionados`.
- La redundancia usa el coseno de los vectores versionados `fs-v9`.
- La selección usa como máximo las 100 mejores candidatas o cinco veces el
  límite solicitado, lo que sea mayor, y publica 20 resultados.
- El contrato offline contiene 30 configuraciones; las dos nuevas declaran
  explícitamente `rating_confidence` y la similitud por pares.

## Verificación de ejecución

- `pytest apps/api/recommendations/tests apps/api/evaluation/tests/test_protocol.py -q`: **134 passed**.
- `tsc --noEmit`: correcto.
- `docker compose -f infra/compose.yaml config --quiet`: correcto.
- Los 12 workers (11 variantes de contenido y la heurística de género) están
  configurados y ejecutándose en paralelo.
- Para `felipe`, los 12 trabajos de la huella
  `2d79000f2de0083eb201fd65740f74b5d0ebd25ad1f84d33e681a8f0328d20d8` terminaron
  con estado `succeeded`.
- Snapshot publicado: `ddef6ae3-6795-4049-b105-5d389e53d1e2`, revisión de
  colección 14. Cada variante MMR contiene 20 resultados.

## Comparación Weighted solicitada

En el snapshot activo, antes de aplicar MMR a sus dos variantes nuevas,
`content-cbf-weighted-v1` mantiene estos valores para los dos juegos:

| Señal | Hollow Knight: Silksong | Monster Boy and the Cursed Kingdom |
|---|---:|---:|
| Puntuación Weighted | 0,895760 | 0,876945 |
| Similitud de contenido | 0,918333 | 0,955756 |
| Rating IGDB normalizado | 0,924795 | 0,867625 |
| Rating bayesiano | 91,820032 | 83,249746 |
| `rating_confidence` usado | 0,843092 | 0,693052 |
| `total_rating_count` normalizado | 0,716553 | 0,409022 |
| PopScore | 0,996857 | 0,911214 |
| `recency_score` | 0,350000 | 0,000225 |

La fórmula vigente es `0,70 * similitud + 0,30 * rating_confidence`. PopScore y
`recency_score` se conservan en el payload para trazabilidad, pero no intervienen
en Weighted; sí intervienen en sus variantes correspondientes.

