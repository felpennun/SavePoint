# Reevaluación v8: rating bayesiano de Felipe

Fecha: 2026-09-09

## Contrato verificado

La señal compartida por la web, los diez workers y la evaluación offline es
`rating-confidence-v4-bayesian`. Con `m = 25` y media previa congelada
`78,4724015695`, se calcula:

`rating_bayes = (n * rating_igdb + 25 * media_previa) / (n + 25)`

`rating_confidence = (rating_bayes / 100)^2`.

`n` es `total_rating_count`. La señal `rating_volume` sigue en el payload como
evidencia explicable, pero no modifica otra vez la puntuación.

## Contraste reproducible

| Señal | Hollow Knight: Silksong | Terraria |
|---|---:|---:|
| Similitud de contenido fs-v9 | 0,918333 | 0,920746 |
| Rating IGDB normalizado | 0,924795 | 0,823387 |
| Rating bayesiano | 91,820032 | 82,249942 |
| `rating_confidence` | 0,843092 | 0,676505 |
| PopScore | 0,996857 | 0,996087 |
| Recencia | 0,350000 | 0,000000 |

| Algoritmo | Silksong | Terraria |
|---|---:|---:|
| Weighted | 0,895760 | 0,847474 |
| Multiplicative | 0,774239 | 0,622890 |
| Two-Stage | 4,140515 | 4,112751 |
| Negative | 0,895760 | 0,847474 |
| Weighted-Pop | 0,915227 | 0,874754 |
| Multiplicative-Pop | 0,928113 | 0,746493 |
| Two-Stage-Pop | 4,145641 | 4,123404 |
| Negative-Pop | 0,915227 | 0,874754 |
| Recency | 0,691656 | 0,518668 |

La similitud de Terraria continúa siendo ligeramente superior, pero la
calidad IGDB ajustada y la recencia de Silksong prevalecen en todas las
variantes publicadas. Esto es una comprobación de producto, no una métrica de
efectividad del estudio sintético.

## Evidencia de ejecución

- Prior y huella de configuración: `78,4724015695` y
  `81f295e2a1018163e2aca18d444149b468600652cbbaf16b85a258b68735c303`.
- Workers para la revisión 14 de `felipe`: 10/10 `succeeded` y publicación
  atómica del snapshot activo.
- `pytest apps/api/recommendations/tests apps/api/evaluation/tests -q`: 195
  passed.
- `pnpm --dir apps/web exec tsc --noEmit`: correcto.

