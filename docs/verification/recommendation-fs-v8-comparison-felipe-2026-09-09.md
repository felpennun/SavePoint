# Comparacion fs-v8: Silksong y Terraria — 2026-09-09

## Alcance

Comparacion aislada de `Hollow Knight: Silksong` y `Terraria` con el perfil de
`felipe`, usando el snapshot activo de la revision 14 y los mismos valores
normalizados publicados para las diez secciones. El cambio se identifica como
`feature_set_version = fs-v8` y `similarity_rule_version = facet-similarity-v4`.

## Puntuaciones

| Algoritmo | Silksong | Terraria | Diferencia Silksong - Terraria |
|---|---:|---:|---:|
| `content-cbf-weighted-v1` | 0,942029 | 0,839835 | +0,102194 |
| `content-cbf-multiplicative-v1` | 0,806762 | 0,599489 | +0,207273 |
| `content-cbf-twostage-v1` | 4,134460 | 4,108518 | +0,025942 |
| `content-cbf-neg-v1` | 0,942029 | 0,839835 | +0,102194 |
| `content-cbf-weighted-pop-v1` | 0,951219 | 0,864621 | +0,086598 |
| `content-cbf-multiplicative-pop-v1` | 0,927016 | 0,688709 | +0,238307 |
| `content-cbf-twostage-pop-v1` | 4,139213 | 4,117143 | +0,022070 |
| `content-cbf-neg-pop-v1` | 0,951219 | 0,864621 | +0,086598 |
| `recency-v1` | 0,701038 | 0,506046 | +0,194992 |
| `genre-taste-v1` | No aparece en las 20 publicadas | No aparece en las 20 publicadas | — |

Las puntuaciones de dos etapas se expresan en bandas de similitud más un
desempate de rating; no deben compararse directamente con las variantes
normalizadas de 0 a 1.

## Señales compartidas

| Señal | Silksong | Terraria |
|---|---:|---:|
| Similitud de contenido | 1,000000 (tope tras bonus) | 0,920718 |
| Núcleo género/plataforma | 0,903429 | 0,920718 |
| Bonus saga + desarrollador | 0,096571 efectivo por tope | 0,000000 |
| Rating IGDB normalizado | 0,924795 | 0,823387 |
| Rating confidence | 0,806762 | 0,651111 |
| PopScore | 0,996857 | 0,996087 |
| Recencia | 0,35 | 0,000000 |

El núcleo de Silksong más el bonus de desarrollador supera 1 y se limita a
1,0. El bonus bruto de desarrollador es `0,15` porque coincide con Team Cherry;
la diferencia visible en `optional_bonus` refleja el límite superior de la
similitud, no una reducción del peso configurado. Terraria tiene más núcleo por
géneros/plataformas, pero no recibe bonus opcional y tiene menor rating
confidence.

## Verificacion

- Caché reconstruida: `190.479` vectores en `fs-v8`.
- Workers de Felipe: `10/10 succeeded`.
- Snapshot activo: revision 14, `fs-v8`.
- Los scores se calcularon con el ranker compartido por web, workers y offline.
