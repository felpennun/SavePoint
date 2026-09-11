---
tags: [fase/3, fase/4, tema/evaluacion, tema/recomendadores, resultado]
---

# Evaluación offline final — protocolo 12, 400 usuarios, split test

Cálculo final del harness congelado ejecutado con éxito el 2026-09-10/11, consumiendo el
split `test` de protocolo v12 (`protocol_sha256 02af71222f...`) una sola vez. Fuente
canónica y completa: [[../../docs/verification/evaluation-results-400-test-2026-09-10.md|evaluation-results-400-test-2026-09-10.md]].
Corrige los conteos de usuarios evaluables del checkpoint previo
([[../../docs/verification/evaluation-checkpoint-400-users-2026-09-10.md]]).

## Resultado, en una frase

Bajo este protocolo y este split, **ningún algoritmo es declarable superior a otro**
(0 de 120 comparaciones por pares sobreviven Holm, pese a un Friedman ómnibus
significativo, χ²=30,00, p=0,0119, n=73); `cf-user-knn-v1` tiene el nDCG@10 medio más
alto (0,0155) pero solo por 2 aciertos de 73 usuarios.

## Hallazgo que sí es accionable

**El 74 % de los 73 usuarios evaluables de test (54/73) cae en el modo
`insufficient_history` del ranker de contenido** en cuanto el leave-one-out retira su
único positivo elegible (`_COLD_START_ENTRIES = 3` en `recommendations/content/rank.py`).
En ese modo las diez variantes de contenido —y sus derivadas MMR/híbridas— dejan de usar
similitud de tags y colapsan a la misma clasificación por rating/PopScore/recencia que ya
usan los baselines. Eso explica que 15 de los 16 algoritmos anoten
`precision = recall = nDCG = MAP = 0,000000` exactos en K = 5/10/20.

No es un fallo del pipeline: se verificó que los vectores de contenido son correctos
(byte a byte contra la caché `WorkFeatureVector`), que el conjunto de candidatas es
idéntico para los 16 algoritmos, y que los dos algoritmos que sí puntúan lo hacen por una
señal ajena al contenido (colaborativa). Es una interacción entre dos piezas congeladas
por separado: el generador de población sintética (Plan `02-09`) y el umbral de arranque
en frío del ranker de contenido.

## Decisión pendiente del autor

Antes de citar este resultado como hallazgo central del capítulo de evaluación del TFG,
decidir entre:

1. Reportarlo tal cual, con la prevalencia de `insufficient_history` como hallazgo
   metodológico explícito (no exige tocar nada congelado).
2. Regenerar la población sintética garantizando ≥3 positivos tras el LOO para los
   usuarios no-`no_history`, lo que exige re-congelar protocolo (nuevo
   `manifest_sha256`, ratificación del autor, nuevo checkpoint) — fuera del alcance de
   la tarea que produjo este resultado.

## Efectos colaterales de la ejecución (documentados en el resultado canónico)

- Se descartaron (rating → `NULL`, reversible) 3 obras del corpus contaminadas por una
  importación IGDB posterior al freeze del snapshot `2026.09.2`; no afectó a ningún
  usuario sintético ni a `snapshot_sha256`.
- Se corrigió un bug latente (`.filter(curated_labels__isnull=False)` sin `.distinct()`
  iteraba ~96.055 filas en vez de 13.618) leyendo los vectores desde la caché
  `WorkFeatureVector` ya poblada para `fs-v12-curated-tags-idf` — de ~2 h por intento
  fallido a minutos por algoritmo.
- El cálculo final corrió en un solo proceso (`run_evaluation`, no el comando paralelo)
  por límite de memoria de la VM de Docker local (8 GiB); es una condición de ejecución,
  no cambia ningún valor puntuado.

Commits relevantes en `main`: `b956256`, `3fba4bb`, `895a689`, `64efe32`, `c8877c0`.
