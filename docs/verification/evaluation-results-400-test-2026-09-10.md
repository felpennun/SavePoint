# Resultados de la evaluación offline final — 400 usuarios sintéticos, split test

**Fecha de ejecución:** 2026-09-10 23:04 UTC → 2026-09-11 02:47 UTC (3 h 42 min de pared).
**Protocolo:** v12, congelado el 2026-09-10. **Corpus:** `2026.09.2`. **Split:** `test`
(uso único, ahora consumido). **Estado:** `succeeded`, 16/16 algoritmos.

## 0. Resumen ejecutivo

- El split de test se ejecutó **una sola vez**, con éxito, y el marcador de consumo quedó
  escrito (`apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-11T02:47:06Z`). No
  se puede volver a correr este protocolo sobre `test` sin subir `protocol_version`.
- **Ningún algoritmo es declarable superior a otro** bajo este protocolo y este split: el
  test ómnibus de Friedman sobre nDCG@10 es significativo (χ² = 30,00; p = 0,0119; n = 73),
  pero **0 de las 120 comparaciones por pares sobreviven la corrección de Holm**. Cualquier
  lectura de "el algoritmo X gana" que no mencione esto es una simplificación indebida del
  resultado.
- **Hallazgo dominante, y el más importante de este documento:** 15 de los 16 algoritmos
  —los dos baselines, las diez variantes de contenido y el híbrido ponderado— obtienen
  `precision = recall = nDCG = MAP = 0,000000` exactos en K = 5, 10 y 20. Solo
  `cf-user-knn-v1` recupera el ítem retenido en el top-K para 2 de los 73 usuarios de test
  (posiciones 2 y 3) y `hybrid-mmr-v1` para 1 usuario en K = 20.
- **Causa principal identificada (no es un fallo del pipeline):** el 74 % de los usuarios
  evaluables de test (54 de 73) entran en el modo `insufficient_history` del ranker de
  contenido en cuanto se retira su único positivo elegible mediante leave-one-out. En ese
  modo, **las diez variantes de contenido colapsan a la misma clasificación no
  personalizada** (rating bayesiano + PopScore + recencia, sin similitud de tags), lo que
  explica que se comporten como los baselines. Ver §3.3 y §9.
- Incluso restringiendo el análisis a los 19 usuarios "calientes" (con perfil de contenido
  real), ninguna variante de contenido acertó el ítem retenido en el top-20 de 13.618
  candidatas. Con un único positivo por usuario esto es compatible con el azar (bajo poder
  estadístico, §5), pero es el punto que más necesita revisión del autor antes de citar
  este resultado como conclusión central del TFG — ver §11.

## 1. Estado congelado y trazabilidad

| Campo | Valor |
|---|---|
| `protocol_version` | 12 |
| `protocol_sha256` | `02af71222ffcc964ac940e7ebbe3c51c87fc70cf869f55248e4dce836f894a61` |
| `corpus_version` | `2026.09.2` |
| `snapshot_sha256` (ratings) | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| `popscore_snapshot_sha256` | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| `feature_set_version` | `fs-v12-curated-tags-idf` |
| Semilla leave-one-out | `20260907` |
| Semilla split de usuarios | `20260908` |
| `split` | `test` |
| `split_manifest_sha256` | `f049c83e7bb9af2db7cfc29adcbedf6b7adc4c249a92d3a5d7f95e17d8bf860b` |
| `code_commit` (artefacto) | `64efe32b5146862061c642410d0ff95bf9c2544e` |
| Marcador de consumo | `apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-11T02:47:06.371035+00:00` |
| Artefacto final | `apps/api/evaluation-400-test-2026-09-10.artifact.json` |
| SHA-256 del artefacto | `6cf05b9c53e595f5915c9b68538e44063e8e3bdd3b070520bbd88ed3f388be8b` |
| Preflight de entradas | `apps/api/evaluation-input-preflight-2026-09-10.json`, SHA-256 `b35f7158db8112b294f594665c2e058453114a5271e81fc49a4bab66cfcf1891` |

Todos los hashes de snapshot y protocolo son **idénticos** a los fijados en el checkpoint
del 2026-09-10 (`docs/verification/evaluation-checkpoint-400-users-2026-09-10.md`); nada
de lo congelado cambió durante esta tarea. Ambas fórmulas, semillas, exclusiones y pesos
son los del protocolo v12 sin modificación.

### 1.1 Mutación de datos aplicada antes de calcular (autorizada, documentada, reversible)

Tres obras del corpus (`night-runners-prologue-1`, `victory-run`, `bills-must-be-paid`)
recibieron un rating de IGDB **después** de que `snapshot_corpus_ratings` congelara el
snapshot `2026.09.2` (importación `IgdbImportRun 776f43cd`, lote de 2026-09-09 19:59:44
UTC, ~19 h después del freeze de las 00:57). Eso las metía en
`evaluation_candidate_works` sin fila de `CorpusRatingSnapshot`, y el runner abortaba con
`SnapshotCoverageError`. Con autorización expresa del autor, se revirtió
`rating`/`rating_count`/`total_rating_count` a `NULL` en esas 3 obras exactas, devolviendo
`evaluation_candidate_works('2026.09.2')` a las 13.618 candidatas originales sin mover
ningún hash congelado (`snapshot_sha256` verificado idéntico antes y después). Cero
entradas de biblioteca sintética apuntaban a esas 3 obras.

### 1.2 Cambios de código congelados en el camino (reproducibilidad, no fórmulas)

| Commit | Qué cambia | Por qué |
|---|---|---|
| `b956256` | Ordena `default_algorithms()` para que coincida con `protocol.tuning.evaluation_algorithms` | `hybrid-mmr-v1` quedaba en la posición 13 en vez de la 16; el guardián de `run_evaluation_parallel` comparaba listas y abortaba. Mismos 16 algoritmos, mismo orden que el protocolo; `frozen_hash` no cambia. Test de regresión añadido. |
| `3fba4bb` | `runner.run()` lee los vectores de candidata de la caché `WorkFeatureVector` en vez de recalcularlos | `evaluation_candidate_works(cv).filter(curated_labels__isnull=False)` sin `.distinct()` itera ~96.055 filas (13.618 obras × ~7 etiquetas); se llamaba a `feature_vector()` ~96.055 veces por algoritmo. Verificado byte a byte idéntico contra la caché para las 96.055 filas antes de aplicar. |
| `895a689` | `duration_seconds` por algoritmo + línea de progreso a stderr en `run()` | Sin esto, un cálculo de horas no daba ninguna señal hasta el final. Pura instrumentación. |
| `64efe32` | `--serial-tail N` en `run_evaluation_parallel` (no usado en el cálculo final, que corrió con el comando no paralelo) | Permite drenar la cola pesada (MMR/colaborativo/híbridos) a un proceso a la vez tras la cabeza en paralelo, sin perder el artefacto único ni la estadística conjunta. Documentado para reintentos futuros. |

Ninguno de estos cuatro commits toca `protocol.json`, una semilla, una fórmula, el
conjunto de candidatas o un peso. `pytest apps/api/evaluation` pasó (96/96) después de
cada uno.

### 1.3 Por qué se ejecutó en un solo proceso

`run_evaluation_parallel --max-workers 4` y `--max-workers 2` agotaron la memoria de la
VM de Docker (8 GiB) durante el *scoring* de las variantes de contenido/MMR/híbridas —
cada proceso mantiene en memoria los vectores de las 13.618 candidatas y el universo de
evaluación completo. Tres intentos fallaron por `SnapshotCoverageError` (§1.1) y
`BrokenProcessPool` (OOM); los artefactos de fallo se conservan íntegros:

| Artefacto de fallo | SHA-256 | Causa |
|---|---|---|
| `evaluation-400-test-2026-09-10.FAILED-snapshot-coverage.artifact.json` | `845bce2ba5c61b9ab49ed739db98205c50d735ca58b6890600bd71e147e358f9` | 3 obras contaminadas (§1.1), antes del descarte |
| `evaluation-400-test-2026-09-10.FAILED-brokenpool.artifact.json` | `35d8476ee6eb640dfb01e480d3bed30931e75555f7db8093f40b192e7278543e` | OOM con `--max-workers 4`, antes de la caché de vectores |
| `evaluation-400-test-2026-09-10.FAILED-brokenpool-w4-cache.artifact.json` | `384ae402be362e7eda2da123818733cc4b8ae1353c7b88b0fcdb32f8461939c8` | OOM con `--max-workers 4`, con caché de vectores (mucho más rápido, igual de sin memoria) |
| `evaluation-400-test-2026-09-10.FAILED-brokenpool-w2-cache.artifact.json` | `9fb493ff32544e83773a85325f539c4ad16d04c6080ac0a2831140c0cdc79651` | OOM con `--max-workers 2`, al entrar el primer par de algoritmos de contenido pesados |

Ninguno de los cuatro intentos fallidos escribió el marcador de consumo del test. El
cálculo que sí tuvo éxito usó `run_evaluation` (proceso único): pico de memoria ≈ 2,0 GiB
de 7,66 GiB disponibles, cero riesgo de OOM, a costa de perder el desglose
`parallel_execution`/`worker_timings` (compensado por `duration_seconds` por algoritmo,
§7). Es una condición de ejecución, no un cambio de resultado.

## 2. Protocolo que se aplicó (sin cambios)

- Relevancia: `completed` **o** `rating_half_steps >= 7`.
- Split leave-one-out por usuario, semilla `20260907`; el positivo retirado vuelve al
  conjunto de candidatas.
- `K ∈ {5, 10, 20}`; métrica titular `nDCG@10`.
- Candidatas: obras gobernadas con `rating IS NOT NULL AND total_rating_count >= 5`,
  menos la biblioteca restante del usuario, más el ítem retenido.
- 16 algoritmos declarados en `protocol.json`, ejecutados exactamente una vez sobre test.
- `train` (240) solo alimenta la referencia colaborativa y la frecuencia de novedad;
  `validation` (80) se reserva para selección; `test` (80 asignados) se usa una sola vez.

## 3. Población y cohortes evaluables del split test

### 3.1 Corrección de la cifra esperada

El checkpoint del 2026-09-10 esperaba **79 usuarios evaluables / 1 omitido** en test. Esa
cifra se calculó en `HEAD 8766b9d`, antes del freeze real (`b1ec0f7`), bajo una regla de
elegibilidad de candidatas más laxa (vigente hasta 2026-09-09 14:19, commit `b4f024b`) que
la que realmente aplica `protocol.json` (`total_rating_count >= 5`). La cifra
autoritativa, reproducida por este cálculo, es:

| Split | Asignados | Evaluables | Omitidos |
|---|---:|---:|---:|
| train | 240 | 227 | 13 |
| validation | 80 | 78 | 2 |
| **test** | **80** | **73** | **7** |

### 3.2 Motivo de las 7 omisiones de test

| Motivo | Usuarios | Cohorte |
|---|---:|---|
| Biblioteca vacía (`no_history`, cold start real) | 1 | `no_history` |
| Único positivo elegible con `total_rating_count` 1–4 (< umbral 5) | 6 | 5 `sparse_history_1_to_4`, 1 `normal_history_5_to_10` |

Ninguna de las tres obras descartadas en §1.1 pertenece a la biblioteca de ningún usuario
sintético: el descarte no cambió esta cifra (verificado reintroduciéndolas
hipotéticamente, ningún omitido pasa a evaluable).

### 3.3 Cohortes de los 73 usuarios evaluables de test

| Cohorte | n evaluable | ¿Perfil de contenido real? |
|---|---:|---|
| `sparse_history_1_to_4` | 14 | La mayoría cae en `insufficient_history` tras el LOO |
| `normal_history_5_to_10` | 47 | Mayoritariamente `insufficient_history` también (ver abajo) |
| `intensive_history_over_10` | 12 | La mayoría conserva perfil real |
| `no_history` | 0 | (excluida por diseño; no tiene positivo que retener) |

**Dimensión adicional, no prevista en el checkpoint:** de los 73 usuarios evaluables, **54
(74 %) entran en el modo `insufficient_history` del ranker de contenido** — su perfil
positivo, tras retirar el ítem de leave-one-out, tiene menos de 3 entradas
`completed`/`playing` con rating suficiente (`_COLD_START_ENTRIES = 3` en
`recommendations/content/rank.py`). Solo **19 usuarios (26 %)** conservan un perfil de
contenido real. Este corte no coincide con la cohorte de biblioteca (`sparse` vs
`normal`): varios usuarios `normal_history_5_to_10` también caen en `insufficient_history`
porque no todas sus entradas de biblioteca cualifican como evidencia positiva (solo
`completed`/`playing` con rating ≥ 3,5/5, §4.2 de `recommendation-algorithms.md`).

En modo `insufficient_history`, **las diez variantes de contenido (y sus derivadas MMR e
híbridas) no usan similitud de tags en absoluto**: ordenan candidatas solo por rating
bayesiano, PopScore y recencia — la misma familia de señales que ya usan `popularity-v1`
y `recency-v1`. Esto explica que 74 % de los usuarios reciban, de hecho, una
recomendación no personalizada bajo cualquier "algoritmo de contenido".

## 4. Resultados de acierto

### 4.1 nDCG@10 (métrica titular), ordenado descendente

| Algoritmo | nDCG@10 |
|---|---:|
| `cf-user-knn-v1` | 0,015492 |
| `content-cbf-weighted-v1` | 0,000000 |
| `content-cbf-multiplicative-v1` | 0,000000 |
| `content-cbf-twostage-v1` | 0,000000 |
| `content-cbf-neg-v1` | 0,000000 |
| `content-cbf-weighted-pop-v1` | 0,000000 |
| `content-cbf-multiplicative-pop-v1` | 0,000000 |
| `content-cbf-twostage-pop-v1` | 0,000000 |
| `content-cbf-neg-pop-v1` | 0,000000 |
| `content-cbf-mmr-v1` | 0,000000 |
| `content-cbf-mmr-pop-v1` | 0,000000 |
| `recency-v1` | 0,000000 |
| `hybrid-weighted-cf-v1` | 0,000000 |
| `hybrid-mmr-v1` | 0,000000 |
| `popularity-v1` | 0,000000 |
| `random-v1` | 0,000000 |

### 4.2 Valores no nulos de precision / recall / nDCG / MAP por K

Las 14 filas no mostradas (los dos baselines, las diez variantes de contenido y
`hybrid-weighted-cf-v1`) son **exactamente 0,000000** en precision, recall, nDCG y MAP,
en K = 5, 10 y 20. Solo estas dos filas tienen algún valor distinto de cero:

| Algoritmo | K | Precision | Recall | nDCG | MAP |
|---|---:|---:|---:|---:|---:|
| `cf-user-knn-v1` | 5 | 0,005479 | 0,027397 | 0,015492 | 0,011416 |
| `cf-user-knn-v1` | 10 | 0,002740 | 0,027397 | 0,015492 | 0,011416 |
| `cf-user-knn-v1` | 20 | 0,001370 | 0,027397 | 0,015492 | 0,011416 |
| `hybrid-mmr-v1` | 5 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| `hybrid-mmr-v1` | 10 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| `hybrid-mmr-v1` | 20 | 0,000684 | 0,013699 | 0,003351 | 0,000856 |

`cf-user-knn-v1` acertó el ítem retenido de 2 de los 73 usuarios (posiciones 2 y 3);
nDCG y MAP no varían con K porque ambos aciertos caen dentro del top-5, así que ampliar K
no cambia el rango descontado. `hybrid-mmr-v1` acertó 1 usuario, pero solo en la posición
11–20 (visible en K = 20, no en K ≤ 10).

## 5. Intervalos y pruebas pareadas de nDCG@10 (métrica titular)

Configuración: bootstrap BCa (2000 remuestreos, IC 95 %, semilla `20260907`), Wilcoxon
pareado (método `auto`, `zero_method="wilcox"`), corrección de Holm sobre las 120
comparaciones por pares (dieciséis algoritmos), Friedman como ómnibus.

- **Friedman:** χ² = 30,00 (`scipy.stats.friedmanchisquare`), n = 73, **p = 0,0119** →
  estimable y válido. Hay diferencia global en el orden de rangos entre los 16
  algoritmos.
- **Pares con `holm_reject = True`: 0 de 120.** Ninguna comparación por pares sobrevive
  la corrección por comparaciones múltiples.
- **105 de 120 pares tienen diferencia media exactamente 0** (ambos algoritmos anotan
  0,000000 para los 73 usuarios) — comparaciones sin información.
- Ejemplo representativo (`cf-user-knn-v1` frente a cualquier variante en 0,000000):
  diferencia media 0,015492; Wilcoxon `n = 73` pero `effective_n = 2` (71 empates,
  `zero_method="wilcox"` los descarta); p sin corregir 0,180; p tras Holm = 1,0.
  IC bootstrap de la diferencia: [0,000; 0,050].

**Lectura correcta:** el ómnibus de Friedman detecta que el orden de rangos no es
uniforme (esperable: dos algoritmos anotan por encima de cero y catorce empatan en
cero), pero con solo 2–3 observaciones no empatadas por comparación, el poder
estadístico de cualquier prueba pareada es insuficiente para declarar significación tras
corregir por 120 comparaciones. **No se puede afirmar que `cf-user-knn-v1` sea superior a
ningún otro algoritmo bajo este protocolo y este split de test**, pese a tener el nDCG@10
medio más alto.

## 6. Más allá del acierto: cobertura, concentración, diversidad, novedad (K = 10)

| Algoritmo | Cob. catálogo | Cob. predicción | HHI | Diversidad intra-lista | Novedad (n aplicable) |
|---|---:|---:|---:|---:|---:|
| `random-v1` | 5,20 % | 100 % | 0,0015 | 0,822 | — (0/73) |
| `content-cbf-mmr-v1` | 0,78 % | 100 % | 0,0613 | 0,687 | — (0/73) |
| `content-cbf-mmr-pop-v1` | 0,71 % | 100 % | 0,0636 | 0,699 | — (0/73) |
| `hybrid-mmr-v1` | 0,84 % | 100 % | 0,0597 | 0,700 | — (0/73) |
| `hybrid-weighted-cf-v1` | 0,51 % | 100 % | 0,0784 | 0,719 | — (0/73) |
| `cf-user-knn-v1` | 0,08 % | 100 % | 0,0997 | 0,795 | 9,09 (73/73) |
| `popularity-v1` | 0,08 % | 100 % | 0,0995 | 0,642 | — (0/73) |
| `content-cbf-multiplicative-v1` | 0,12 % | 100 % | 0,238 | 0,374 | 10,35 (7/73) |
| `content-cbf-multiplicative-pop-v1` | 0,12 % | 100 % | 0,239 | 0,372 | 10,35 (7/73) |
| `content-cbf-twostage-v1` | 0,15 % | 100 % | 0,552 | 0,0094 | 10,03 (8/73) |
| `content-cbf-twostage-pop-v1` | 0,15 % | 100 % | 0,552 | 0,0094 | 10,03 (8/73) |
| `content-cbf-neg-v1` | 0,12 % | 100 % | 0,593 | 0,0061 | 10,46 (6/73) |
| `content-cbf-neg-pop-v1` | 0,12 % | 100 % | 0,614 | 0,0070 | 10,46 (6/73) |
| `content-cbf-weighted-v1` | 0,12 % | 100 % | 0,593 | 0,0071 | 10,36 (7/73) |
| `content-cbf-weighted-pop-v1` | 0,12 % | 100 % | 0,614 | 0,0080 | 10,36 (7/73) |
| `recency-v1` | 0,04 % | 100 % | 0,715 | 0,118 | 10,78 (5/73) |

Lectura:

- **`random-v1` es, por construcción, el de mayor cobertura de catálogo** (5,2 % a K=10,
  10,1 % a K=20): al no tener criterio, distribuye sus recomendaciones sobre casi 1400
  obras distintas en 20 listas de usuario.
  `cf-user-knn-v1` y `popularity-v1` tienen la cobertura más baja (0,08 %, solo 11
  obras únicas en total) porque son casi la misma lista para todos los usuarios sin
  vecindad/popularidad diferenciada.
- Las variantes MMR (`content-cbf-mmr-*`, `hybrid-mmr-v1`) tienen HHI bajo (0,06) y
  diversidad intra-lista alta (~0,69–0,70): la reordenación por redundancia hace su
  trabajo incluso cuando la relevancia base viene del *fallback* no personalizado.
- Las variantes de contenido sin MMR tienen **HHI muy alto (0,55–0,71) y diversidad
  intra-lista casi nula (0,006–0,12)** a K=10: para el 74 % de usuarios en modo
  `insufficient_history`, la clasificación por rating/PopScore/recencia converge en un
  puñado de obras muy similares entre sí para todos ellos.
- La novedad (frecuencia inversa en las interacciones de `train`) solo es aplicable
  cuando el ítem recomendado aparece en alguna biblioteca de entrenamiento; para las
  variantes MMR e híbridas, 0 de 73 usuarios tienen un ítem recomendado con esa
  propiedad (`novelty: null` cuando `applicable_user_count = 0`), lo que en sí mismo es
  informativo: sus recomendaciones son sistemáticamente ítems ausentes de las 240
  bibliotecas de entrenamiento.

## 7. Tiempos por algoritmo

| Algoritmo | Duración |
|---|---:|
| `popularity-v1` | 3,9 s |
| `random-v1` | 17,9 s |
| `cf-user-knn-v1` | 22,2 s |
| `content-cbf-multiplicative-v1` | 993,4 s |
| `content-cbf-multiplicative-pop-v1` | 998,3 s |
| `content-cbf-twostage-v1` | 1000,1 s |
| `content-cbf-neg-v1` | 1001,1 s |
| `content-cbf-neg-pop-v1` | 1003,5 s |
| `content-cbf-twostage-pop-v1` | 1005,1 s |
| `content-cbf-weighted-v1` | 1013,8 s |
| `content-cbf-weighted-pop-v1` | 1015,8 s |
| `recency-v1` | 1028,5 s |
| `hybrid-weighted-cf-v1` | 1033,4 s |
| `hybrid-mmr-v1` | 1042,4 s |
| `content-cbf-mmr-v1` | 1052,3 s |
| `content-cbf-mmr-pop-v1` | 1053,5 s |
| **Suma de duraciones** | **13.285,2 s** |
| **Tiempo de pared (proceso único)** | **13.337 s ≈ 3 h 42 min** |

Los baselines y `cf-user-knn-v1` son rápidos (no calculan vectores de contenido); las diez
variantes de contenido y las dos híbridas rondan los 1000 s cada una, dominadas por la
similitud facetada sobre 13.618 candidatas × 73 usuarios. La diferencia entre la suma
(13.285 s) y la pared (13.337 s) es la sobrecarga fija de arranque de Django/consultas
por algoritmo (~52 s en total).

## 8. Documentación del leave-one-out para el TFG

### 8.1 Qué es y por qué se eligió

Leave-one-out (LOO) es el protocolo de partición estándar para evaluar sistemas de
recomendación de acierto (*top-K accuracy*) cuando cada usuario aporta un historial
limitado: se retira exactamente un ítem que el usuario considera relevante, se
reconstruye su perfil sin él, y se comprueba si el algoritmo lo recupera en su top-K
sobre un conjunto de candidatas común. Es la variante que usan Herlocker et al. (2004) en
su marco de evaluación de recomendadores y que asumen implícitamente las métricas de
ranking de Järvelin y Kekäläinen (2002) cuando se aplican a un único positivo por
consulta.

### 8.2 Mecánica exacta en SavePoint (D-17, D-18)

1. **Relevancia (D-17).** Un ítem de la biblioteca del usuario es positivo-relevante si
   `current_status == "completed"` o `rating_half_steps >= 7` (≥ 3,5/5).
2. **Selección determinista del retenido.** De los positivos-relevantes del usuario se
   elige exactamente uno con `random.Random(f"{seed}:{user.id}")`, semilla
   `20260907` fijada en `protocol.json`. Dos ejecuciones con la misma semilla retienen
   el mismo ítem para el mismo usuario.
3. **Reconstrucción del perfil.** El ítem retenido se retira de la biblioteca visible
   antes de construir el perfil de contenido o colaborativo del usuario. Si al
   usuario no le queda ningún positivo-relevante, se excluye de ese split (no se
   fuerza un cero artificial).
4. **Conjunto de candidatas común (EVAL-01).** Para cada usuario, el conjunto de
   candidatas es idéntico para los 16 algoritmos: obras gobernadas elegibles
   (`rating IS NOT NULL AND total_rating_count >= 5`) menos la biblioteca restante del
   usuario, más el ítem retenido reincorporado explícitamente aunque ya no sea parte de
   la vista habitual. El hash SHA-256 de esa lista ordenada se congela por usuario y se
   agrega en `split_manifest_sha256` del artefacto.
5. **Tarea de recuperación.** Cada algoritmo devuelve su top-K sobre ese conjunto de
   candidatas; se mide si el ítem retenido aparece y en qué posición
   (`heldout_rank`, solo dentro del top-20 solicitado — no se calcula el rango exacto
   más allá de eso).

### 8.3 Consecuencias matemáticas de un único positivo por usuario

Con exactamente un ítem relevante por usuario:

- `Recall@K ∈ {0, 1}` por usuario: o el ítem retenido está en el top-K (1) o no (0). No
  hay valores intermedios.
- `nDCG@K = 1 / log2(rango + 1)` si hay acierto, `0` en caso contrario — no hace falta
  el DCG ideal completo porque solo hay un ítem relevante.
- `Precision@K = acierto / K`; `MAP@K` coincide con `nDCG` reescalado para un único
  positivo bajo esta implementación.
- El agregado por algoritmo (§4) es la **media aritmética** de esos 0/1 (o
  1/log2(rango+1)) sobre los 73 usuarios evaluables — de ahí que valores tan bajos como
  0,0155 (`cf-user-knn-v1`) representen literalmente "acertó para 2 de 73 personas, en
  buena posición cuando acertó", no un "número pequeño de puntuación continua".

### 8.4 Por qué el poder estadístico es bajo con LOO de un único positivo

Cuando la mayoría de los usuarios anota exactamente 0 en un algoritmo, cualquier
comparación pareada frente a otro algoritmo que también anota mayormente 0 tiene muy
pocas observaciones no empatadas (`effective_n` bajo, aquí 2 de 73 en el mejor caso
observado). El test de Wilcoxon con `zero_method="wilcox"` descarta los empates
correctamente, pero eso reduce el tamaño muestral efectivo de la prueba, no solo su
señal — es una limitación estructural del diseño LOO de un único positivo, ya prevista en
`evaluation-protocol.md` ("Sesgo del leave-one-out con un único positivo") y confirmada
empíricamente en este cálculo (§5).

### 8.5 Qué mide y qué no mide este protocolo

LOO de un único positivo mide **si el sistema recupera exactamente el ítem que el
usuario retuvo**, no la calidad general de la lista de recomendación ni la satisfacción
del usuario con alternativas igualmente válidas. Un algoritmo puede producir una lista
de contenido excelente y aun así fallar el LOO si el ítem retenido no era, de entre todo
lo bueno que el usuario podría disfrutar, el que el algoritmo priorizó. Esta es la razón
por la que el protocolo también informa métricas más allá del acierto (§6): cobertura,
concentración, diversidad y novedad, que no dependen de acertar un ítem concreto y
permiten distinguir comportamientos (p. ej. MMR diversificando de verdad) incluso cuando
el acierto puntual es cero.

### 8.6 Interacción con la generación de usuarios sintéticos (amenaza ya documentada)

`evaluation-protocol.md` señala como amenaza a la validez que "los arquetipos de usuario
sintético" podrían introducir circularidad si se generan con las mismas features que
consume el recomendador. Este cálculo expone la cara opuesta de esa misma amenaza: la
generación de bibliotecas sintéticas (Plan `02-09`) no garantiza que, tras retirar
exactamente un positivo, el usuario conserve las ≥3 entradas de evidencia que exige el
perfil de contenido (`_COLD_START_ENTRIES`) — de ahí el 74 % de `insufficient_history`
en test (§3.3). Es una interacción entre dos componentes que se congelaron por separado
(el generador de población y el umbral de arranque en frío del ranker) y que no se había
cuantificado hasta esta ejecución.

## 9. Fallos, omisiones y limitaciones

1. **74 % de `insufficient_history` en test** (§3.3): la causa más probable del resultado
   casi nulo en acierto de las variantes de contenido; requiere decisión del autor antes
   de tratar §4–§5 como hallazgo central del TFG (ver §11).
2. **12 usuarios omitidos por corrección de elegibilidad** (§3.1): no es una regresión de
   datos ni una regeneración de la población — es la aplicación correcta de la regla
   `total_rating_count >= 5` ya vigente cuando se congeló el protocolo, frente a una
   estimación de checkpoint calculada con una regla anterior.
3. **3 obras descartadas del corpus** (§1.1): reversibles, documentadas, sin impacto en
   ningún usuario sintético ni en los hashes congelados.
4. **Ejecución en un solo proceso** (§1.3): el artefacto no lleva `parallel_execution`
   ni `worker_timings`; se compensa con `duration_seconds` por algoritmo (§7). No afecta
   ningún valor puntuado.
5. **Bajo poder estadístico estructural** (§5, §8.4): 0/120 pares significativos tras
   Holm pese a un Friedman significativo; es consecuencia matemática de LOO con un único
   positivo y una tasa de acierto casi nula, no un defecto de la implementación
   estadística (bootstrap BCa + Wilcoxon + Holm + Friedman, todos con semilla fija y
   verificados por `apps/api/evaluation/tests/test_statistics.py`).
6. **`tag-taste-v1` queda fuera de esta comparación** (como fija el protocolo): es una
   heurística de producto, no un algoritmo de la suite académica de 16.
7. Esta evaluación es **evidencia de simulación sobre arquetipos parametrizados**, nunca
   evidencia sobre usuarios reales de SavePoint (EVAL-10); las conclusiones se limitan al
   corpus `2026.09.2`, esta población de 400 usuarios y este protocolo v12.

## 10. Amenazas a la validez

Se heredan íntegras las de `evaluation-protocol.md` (validez externa de usuarios
sintéticos, sesgo de LOO de un único positivo, sesgo de fuente única de rating, riesgo de
circularidad de arquetipos, congelación de un solo uso) y se añade la confirmada
empíricamente en este cálculo:

- **Prevalencia de arranque en frío en el split de test (nueva, confirmada aquí).** El
  74 % de `insufficient_history` reduce de facto la comparación de las diez variantes de
  contenido, en la práctica, a una comparación de baselines de rating/PopScore/recencia
  para la mayoría de los usuarios de test. Cualquier conclusión sobre "qué señal de
  contenido funciona mejor" debería reportarse condicionada al 26 % de usuarios con
  perfil real, no al 100 % del split.

## 11. Interpretación prudente y siguiente paso recomendado

Bajo el protocolo `2026.09.2`/v12 y este split de test de un solo uso:

- **No hay un algoritmo superior de forma estadísticamente defendible.** `cf-user-knn-v1`
  tiene el nDCG@10 medio más alto (0,0155, 2/73 aciertos en buena posición), pero ninguna
  comparación por pares es significativa tras Holm (§5). Presentarlo como "el algoritmo
  ganador" sin esta salvedad sería una afirmación de superioridad universal que el propio
  protocolo prohíbe declarar.
- El resultado dominante —15 de 16 algoritmos en cero exacto— es **coherente con la
  arquitectura del sistema** (todas las variantes de contenido comparten el mismo umbral
  de arranque en frío) y **no muestra evidencia de un defecto de implementación**: los
  vectores de características se verificaron byte a byte contra la caché (§1.2), el
  conjunto de candidatas es idéntico para los 16 algoritmos (aserción en
  `runner.run()`), y los dos algoritmos que sí puntúan (`cf-user-knn-v1`,
  `hybrid-mmr-v1`) lo hacen exactamente donde cabía esperar (señal ajena al contenido).
- **Recomendación antes de citar esto en el capítulo de evaluación del TFG:** decidir si
  (a) se reporta el resultado tal cual, con el 74 % de `insufficient_history` como
  hallazgo metodológico explícito sobre la interacción población sintética × umbral de
  arranque en frío; o (b) se regenera la población sintética (fuera del alcance de esta
  tarea, exige re-congelar protocolo y checkpoint, ver la conversación de esta sesión)
  garantizando que cada usuario no-`no_history` conserve ≥3 positivos tras el LOO, y se
  repite la comparación con un nuevo protocolo versionado. Ambas son decisiones
  legítimas; ninguna de las dos se ha tomado en esta tarea.

## 12. Bibliografía citada (ya recogida en `recommendation-algorithms.md`, sin fuentes nuevas)

- Järvelin, K. y Kekäläinen, J. (2002). *Cumulated gain-based evaluation of IR
  techniques*. [DOI 10.1145/582415.582418](https://doi.org/10.1145/582415.582418) —
  fundamento de nDCG y de que la posición importa en la evaluación de ranking.
- Herlocker, J. L., Konstan, J. A., Terveen, L. G. y Riedl, J. T. (2004). *Evaluating
  collaborative filtering recommender systems*.
  [DOI 10.1145/963770.963772](https://doi.org/10.1145/963770.963772) — marco de
  evaluación de recomendadores, incluida la sensibilidad de la conclusión a la tarea, los
  datos, la partición y la métrica.
- Carbonell, J. y Goldstein, J. (1998). *The use of MMR, diversity-based reranking...*
  [DOI 10.1145/290941.291025](https://doi.org/10.1145/290941.291025) — fundamento de la
  reordenación MMR usada en `content-cbf-mmr-*` y `hybrid-mmr-v1`.
- McNee, S. M., Riedl, J. y Konstan, J. A. (2006). *Being accurate is not enough: how
  accuracy metrics have hurt recommender systems*.
  [DOI 10.1145/1125451.1125659](https://doi.org/10.1145/1125451.1125659) — justifica
  reportar cobertura, diversidad y novedad (§6) aparte del acierto, precisamente porque
  el acierto puntual puede ser engañoso o, como aquí, casi nulo, sin que el sistema
  carezca de comportamiento diferenciable.

## 13. Artefactos y reproducibilidad

| Artefacto | Ruta | SHA-256 |
|---|---|---|
| Artefacto final (éxito) | `apps/api/evaluation-400-test-2026-09-10.artifact.json` | `6cf05b9c53e595f5915c9b68538e44063e8e3bdd3b070520bbd88ed3f388be8b` |
| Preflight de entradas | `apps/api/evaluation-input-preflight-2026-09-10.json` | `b35f7158db8112b294f594665c2e058453114a5271e81fc49a4bab66cfcf1891` |
| Fallo: cobertura de snapshot | `apps/api/evaluation-400-test-2026-09-10.FAILED-snapshot-coverage.artifact.json` | `845bce2ba5c61b9ab49ed739db98205c50d735ca58b6890600bd71e147e358f9` |
| Fallo: OOM `-w4` (pre-caché) | `apps/api/evaluation-400-test-2026-09-10.FAILED-brokenpool.artifact.json` | `35d8476ee6eb640dfb01e480d3bed30931e75555f7db8093f40b192e7278543e` |
| Fallo: OOM `-w4` (con caché) | `apps/api/evaluation-400-test-2026-09-10.FAILED-brokenpool-w4-cache.artifact.json` | `384ae402be362e7eda2da123818733cc4b8ae1353c7b88b0fcdb32f8461939c8` |
| Fallo: OOM `-w2` (con caché) | `apps/api/evaluation-400-test-2026-09-10.FAILED-brokenpool-w2-cache.artifact.json` | `9fb493ff32544e83773a85325f539c4ad16d04c6080ac0a2831140c0cdc79651` |
| Marcador de consumo | `apps/api/.evaluation-test-run.json` | (contiene `protocol_sha256` y `consumed_at`, ver §1) |

Fuente normativa: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md),
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md) y el
checkpoint corregido
[`evaluation-checkpoint-400-users-2026-09-10.md`](./evaluation-checkpoint-400-users-2026-09-10.md).
