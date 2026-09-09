# Comparacion fs-v9 para Felipe — 2026-09-09

## Contrato aplicado

La comparacion usa `fs-v9` / `facet-similarity-v5`, la misma configuracion
publicada por web, workers y evaluacion offline:

- nucleo de genero y plataforma con pesos 0,50 y 0,25;
- afinidad del nucleo mediante F0,5 (`beta = 0,5`), priorizando precision del
  candidato frente a cobertura del perfil;
- bonus de saga/franquicia de 0,02 y de desarrollador de 0,015, solo si hay
  coincidencia con la coleccion ponderada;
- bonus opcional maximo combinado de 0,035;
- rating-confidence, PopScore y recency-score segun la rejilla versionada.

Para esta reevaluacion, las variantes que usan PopScore aplican el refuerzo
moderado publicado en el protocolo 7: PopScore pasa a 0,20 en las sumas y
desempates, `swing = 0,20` en la variante multiplicativa y 0,20 en Recency.

## Senales de los candidatos

| Juego | Nucleo | Bonus desarrollador | Bonus saga | Similitud contenido | Rating confidence | Rating IGDB normalizado | PopScore | Recency-score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Hollow Knight: Silksong | 0,903333 | 0,015000 | 0 | 0,918333 | 0,806762 | 0,924795 | 0,996857 | 0,350000 |
| Terraria | 0,920746 | 0 | 0 | 0,920746 | 0,651111 | 0,823387 | 0,996087 | 0,000000 |

El bonus de desarrollador de Silksong es exactamente 0,015 porque coincide con
un desarrollador del perfil de Felipe. No se aplica bonus de saga en esta
comparacion. Terraria no coincide en saga ni desarrollador.

## Puntuaciones por algoritmo

| Algoritmo | Silksong | Terraria |
|---|---:|---:|
| `content-cbf-weighted-v1` | 0,884862 | 0,839856 |
| `content-cbf-multiplicative-v1` | 0,740876 | 0,599508 |
| `content-cbf-twostage-v1` | 4,134460 | 4,108518 |
| `content-cbf-neg-v1` | 0,884862 | 0,839856 |
| `content-cbf-weighted-pop-v1` | 0,906145 | 0,868406 |
| `content-cbf-multiplicative-pop-v1` | 0,888120 | 0,718471 |
| `content-cbf-twostage-pop-v1` | 4,140797 | 4,120018 |
| `content-cbf-neg-pop-v1` | 0,906145 | 0,868406 |
| `recency-v1` | 0,684390 | 0,513589 |

`genre-taste-v1` no incluyo ninguno de los dos juegos en sus 20 resultados
publicados. Las puntuaciones `two_stage` estan expresadas en la escala de
bandas del algoritmo y no son directamente comparables con las variantes
normalizadas entre 0 y 1.

Estos valores son una reevaluacion de Felipe con los valores publicados en el
snapshot activo, no una ejecucion de la evaluacion offline de los 400 usuarios.
