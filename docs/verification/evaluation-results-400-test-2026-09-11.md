# Resultados de la evaluación offline final — protocolo v14, 400 usuarios sintéticos, split test

**Fecha de ejecución:** 2026-09-11 16:05:30 UTC → 17:16:57 UTC (1 h 11 min de pared).
**Protocolo:** v14, congelado el 2026-09-11. **Corpus:** `2026.09.2`. **Split:** `test`
(uso único, ahora consumido). **Estado:** `succeeded`, 16/16 algoritmos.

## 0. Resumen ejecutivo

- El split de test se ejecutó **una sola vez**, con éxito, y el marcador de consumo quedó
  escrito (`apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-11T17:16:57.612653Z`).
  No se puede volver a correr protocolo v14 sobre `test` sin subir `protocol_version`.
- **El hallazgo dominante del cálculo anterior (protocolo v12, 2026-09-10) queda resuelto.**
  El 74 % de `insufficient_history` que colapsaba las diez variantes de contenido a la
  misma clasificación no personalizada **ya no ocurre**: verificado directamente sobre los
  79 usuarios evaluables de test, **0 caen en `insufficient_history`** (todos conservan
  ≥ 3 positivos con perfil de contenido real tras el leave-one-out). Efecto combinado del
  rediseño de población v13 (biblioteca 10-20, franja PopScore 75 %, mínimo 5 positivos
  garantizados) y de no depender ya de la cohorte `sparse_history_1_to_4` que dominaba el
  split de test en v12.
- **Este cálculo sí encuentra diferencias estadísticamente significativas.** Friedman
  ómnibus sobre nDCG@10: χ² = 105,28, p = 1,29 × 10⁻¹⁵ (n = 79). **14 de las 120
  comparaciones por pares sobreviven la corrección de Holm** (frente a 0/120 en v12) — ver
  §5.
- **Los algoritmos de contenido y los híbridos superan claramente a los baselines.**
  `hybrid-weighted-cf-v1` (nDCG@10 = 0,1526) y `content-cbf-weighted-v1` (0,1452) tienen el
  mejor acierto y baten significativamente a `random-v1`, `popularity-v1` y `recency-v1`
  tras Holm. `content-cbf-weighted-pop-v1` y `hybrid-mmr-v1` también baten
  significativamente a ambos baselines. El modo `multiplicative` puntúa
  significativamente peor que `weighted_sum` en las comparaciones directas que sí
  sobreviven Holm.
- Este resultado, a diferencia del de v12, es citable como conclusión sustantiva del
  capítulo de evaluación del TFG sin la salvedad de "ningún algoritmo es declarable
  superior" — ver §11.

## 1. Estado congelado y trazabilidad

| Campo | Valor |
|---|---|
| `protocol_version` | 14 |
| `protocol_sha256` | `7b255fb2c00dc1c2675710595afd012f7528cf2ec02d27d80c9cf9c8c7f2bb6a` |
| `corpus_version` | `2026.09.2` |
| `snapshot_sha256` (ratings) | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| `popscore_snapshot_sha256` | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| `feature_set_version` | `fs-v12-curated-tags-idf` |
| Semilla leave-one-out | `20260907` |
| Semilla split de usuarios | `20260908` |
| `split` | `test` |
| `split_manifest_sha256` | `acb002f1a9cb52ead557e6e5324bc99405f94dc6ad0a78d47e0a9c0c42c1902c` |
| Marcador de consumo | `apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-11T17:16:57.612653+00:00` |
| Artefacto final | `apps/api/evaluation-400-test-2026-09-11.artifact.json` |
| SHA-256 del artefacto | `740eb354ec9f80be6dafe5d66af95ca4454d718876c72517060acb7ff3cf6781` |
| Preflight de entradas (v14) | `apps/api/evaluation-input-preflight-2026-09-11-v14-gate.json`, SHA-256 `f47cebb55f2137b26f5adfa3ae5db8bea81262b18ec849c906f0af3fc12de694` |

`corpus_version`, `snapshot_sha256` y `popscore_snapshot_sha256` son **idénticos** a los de
v12/v13 — nada del corpus ni de las fórmulas de contenido cambió. Lo que cambió entre v13 y
v14 es exclusivamente el mecanismo de selección del positivo retirado en el leave-one-out
(§1.1); entre v12 y v13 cambió exclusivamente el generador de población sintética (ver
`docs/verification/evaluation-results-400-test-2026-09-10.md` §11).

### 1.1 Protocolo v14: piso de rating externo en el positivo retirado (LOO)

`evaluation/splits.py::leave_one_out()` elegía el positivo retirado por gusto personal del
usuario únicamente (`completed` o `rating_half_steps >= 7`), sin considerar el rating
externo de IGDB de esa obra. La mayoría de las 16 variantes combinan similitud de
contenido con `rating_confidence` y/o PopScore, así que un positivo retirado con rating
externo bajo podía hundirse en el ranking pase lo que pase con la calidad del modelado de
contenido — un sesgo de popularidad ya documentado en la evaluación offline de sistemas de
recomendación top-N (Cremonesi, Koren y Turrin, 2010; Steck, 2011 — ver §12).

`protocol.relevance.heldout_min_external_rating = 70` (mediana del rating IGDB sobre las
13.618 candidatas elegibles de `2026.09.2`) exige que el positivo retirado también supere
ese piso. Verificado empíricamente antes de congelar: **0 de los 400 usuarios pierden
todos sus positivos elegibles** a ese umbral (§3). Detalle completo, alternativas
consideradas y justificación:
[[2026-09-11 - Piso de rating externo en LOO y paralelizacion offline]] (vault) y commit
`349f390`.

### 1.2 Optimizaciones de rendimiento de esta sesión

Ninguna de las dos cambia ningún valor puntuado — son exclusivamente condiciones de
ejecución, verificadas byte a byte contra la ruta sin optimizar antes de aplicarse.

| Pieza | Qué hace | Verificación |
|---|---|---|
| Cache de señales compartidas, offline (`134c6e0`) | `rank_content_v1` memoiza `profile_inputs`/`rating_term`/`facet_similarity` en el diccionario `prepared` de `run()`, reutilizado entre los 16 algoritmos de un mismo proceso | 12/12 combinaciones usuario×algoritmo, resultado idéntico con/sin cache |
| Job de señales dedicado, web (`9b1374c`) | Mismo principio para la cola de producción: un job `content-signals-v1` calcula la señal una vez por usuario y los 13 workers dependientes la leen, con dependencia por `Exists()` en la cola (no bloqueo) | Test de exclusión de reclamo + reproducción exacta con valor "envenenado" en la cache |
| Precómputo + fork, offline paralelo (`9b7ff13`) | `run_evaluation_parallel` construye el contexto compartido y precomputa la señal **una vez en el proceso padre**, antes de crear el `ProcessPoolExecutor`; cada worker forkeado la hereda por copy-on-write en vez de recalcularla | `run()` con contexto precomputado produce artefacto idéntico byte a byte (salvo `duration_seconds`) al de `run()` sin contexto |

Detalle completo de las tres piezas, con qué se descartó y por qué (cache oportunista para
la web, métrica secundaria de contenido puro para el LOO):
[[2026-09-11 - Cache de señales compartidas offline y web]] y
[[2026-09-11 - Piso de rating externo en LOO y paralelizacion offline]].

### 1.3 Por qué el cálculo final corrió con 2 workers + cola serial de 5 (no 4 workers)

Primer intento con `--max-workers 4` (sin cola serial, confiando en que el precómputo del
§1.2 bastaría): a los ~10 minutos, `docker stats` mostró el contenedor en 5,93 GiB de
7,66 GiB (77 %) con solo 3-4 algoritmos de contenido terminados, ninguno de los pesados
MMR/híbrido/colaborativo empezado. Diagnóstico con `/proc/<pid>/status`: el proceso padre
pesaba 365 MB, pero cada uno de los 4 workers forkeados pesaba **1,7-1,9 GiB cada uno** —
el copy-on-write del fork no estaba compartiendo memoria como se esperaba. CPython
incrementa el contador de referencias de cada objeto que se lee, aunque sea solo lectura,
lo que ensucia casi todas las páginas de memoria del contexto precomputado y anula gran
parte del ahorro de COW; con 4 workers a la vez eso iba camino de agotar la memoria del
contenedor antes de llegar a las variantes pesadas. Se detuvo el intento (sin escribir el
marcador de consumo, cero coste) y se relanzó con `--max-workers 2 --serial-tail 5` — el
mismo reparto probado en la corrida nocturna de protocolo v12 — que sí completó sin
incidentes: pico observado muy por debajo del límite, 16/16 algoritmos correctos.

Es una condición de ejecución, no un cambio de resultado: los valores puntuados de las dos
corridas (4 workers interrumpida a las 4/16, 2+1 completada) coinciden exactamente en los
algoritmos que sí llegaron a terminar en ambas.

## 2. Protocolo que se aplicó

- Relevancia: `completed` **o** `rating_half_steps >= 7`, para la selección de positivos
  del usuario (D-17, sin cambios).
- **Nuevo en v14:** el positivo retirado en el leave-one-out debe además tener
  `rating IGDB >= 70` (§1.1).
- Split leave-one-out por usuario, semilla `20260907`; el positivo retirado vuelve al
  conjunto de candidatas.
- `K ∈ {5, 10, 20}`; métrica titular `nDCG@10`.
- Candidatas: obras gobernadas con `rating IS NOT NULL AND total_rating_count >= 5`, menos
  la biblioteca restante del usuario, más el ítem retenido.
- 16 algoritmos declarados en `protocol.json`, ejecutados exactamente una vez sobre test.
- `train` (240) alimenta la referencia colaborativa y la frecuencia de novedad;
  `validation` (80) se reserva para selección; `test` (80 asignados) se usa una sola vez.

## 3. Población y cohortes evaluables del split test

| Split | Asignados | Evaluables | Omitidos | Motivo de los omitidos |
|---|---:|---:|---:|---|
| train | 240 | 232 | 8 | Arquetipo `no_history` (biblioteca vacía) |
| validation | 80 | 79 | 1 | Arquetipo `no_history` |
| **test** | **80** | **79** | **1** | Arquetipo `no_history` (usuario 223, `synthetic-sin-historial-omnivoro-2`, 0 entradas de biblioteca) |

Los 10 omitidos en total corresponden exactamente a los 10 usuarios del cohorte
`no_history` de la población v13 (`cohorts.no_history = 10` en `protocol.json`) — ningún
usuario adicional queda fuera por el piso de rating externo del §1.1: verificado
directamente, **el piso de 70 no cuesta ni un usuario** por encima de los 10 excluidos por
diseño (sin biblioteca, no tienen positivo que retener con o sin piso).

**Cero usuarios en `insufficient_history`.** Verificado directamente sobre los 79
evaluables de test: los 79 conservan ≥ 3 entradas positivas (`completed`/`playing`,
rating ≥ 3,5/5) tras retirar su positivo de LOO — el umbral de arranque en frío del
ranker de contenido (`_COLD_START_ENTRIES = 3` en `recommendations/content/rank.py`)
nunca se activa. Contraste directo con protocolo v12, donde el 74 % (54/73) sí caía en
ese modo. Las diez variantes de contenido usan similitud de tags real para el 100 % de
los usuarios de este split.

## 4. Resultados de acierto

### 4.1 nDCG@10 (métrica titular), ordenado descendente

| Algoritmo | nDCG@10 |
|---|---:|
| `hybrid-weighted-cf-v1` | 0,152631 |
| `content-cbf-weighted-v1` | 0,145199 |
| `content-cbf-weighted-pop-v1` | 0,130981 |
| `content-cbf-mmr-v1` | 0,121419 |
| `hybrid-mmr-v1` | 0,110073 |
| `content-cbf-mmr-pop-v1` | 0,107689 |
| `content-cbf-twostage-v1` | 0,096855 |
| `content-cbf-twostage-pop-v1` | 0,091190 |
| `content-cbf-neg-v1` | 0,084849 |
| `content-cbf-neg-pop-v1` | 0,070943 |
| `cf-user-knn-v1` | 0,052524 |
| `content-cbf-multiplicative-v1` | 0,049854 |
| `content-cbf-multiplicative-pop-v1` | 0,045193 |
| `recency-v1` | 0,004897 |
| `popularity-v1` | 0,000000 |
| `random-v1` | 0,000000 |

### 4.2 Precision / recall / nDCG / MAP a K = 10

| Algoritmo | Precision@10 | Recall@10 | nDCG@10 | MAP@10 |
|---|---:|---:|---:|---:|
| `hybrid-weighted-cf-v1` | 0,025316 | 0,253165 | 0,152631 | 0,121127 |
| `content-cbf-weighted-v1` | 0,024051 | 0,240506 | 0,145199 | 0,115431 |
| `content-cbf-weighted-pop-v1` | 0,021519 | 0,215190 | 0,130981 | 0,104375 |
| `content-cbf-mmr-v1` | 0,018987 | 0,189873 | 0,121419 | 0,100507 |
| `hybrid-mmr-v1` | 0,020253 | 0,202532 | 0,110073 | 0,081816 |
| `content-cbf-mmr-pop-v1` | 0,016456 | 0,164557 | 0,107689 | 0,089572 |
| `content-cbf-twostage-v1` | 0,017722 | 0,177215 | 0,096855 | 0,072835 |
| `content-cbf-twostage-pop-v1` | 0,015190 | 0,151899 | 0,091190 | 0,072308 |
| `content-cbf-neg-v1` | 0,013924 | 0,139241 | 0,084849 | 0,068194 |
| `content-cbf-neg-pop-v1` | 0,012658 | 0,126582 | 0,070943 | 0,053320 |
| `cf-user-knn-v1` | 0,011392 | 0,113924 | 0,052524 | 0,034333 |
| `content-cbf-multiplicative-v1` | 0,011392 | 0,113924 | 0,049854 | 0,031379 |
| `content-cbf-multiplicative-pop-v1` | 0,010127 | 0,101266 | 0,045193 | 0,029129 |
| `recency-v1` | 0,001266 | 0,012658 | 0,004897 | 0,002532 |
| `popularity-v1` | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| `random-v1` | 0,000000 | 0,000000 | 0,000000 | 0,000000 |

Recall@10 se lee directamente como "de cuántos de los 79 usuarios se recuperó el ítem
retenido en el top-10": `hybrid-weighted-cf-v1` lo consigue para 20 usuarios (25,3 %),
`content-cbf-weighted-v1` para 19 (24,1 %). Los dos baselines (`random-v1`,
`popularity-v1`) no aciertan ni un solo usuario en ningún K — la comparación frente a ellos
es la más limpia de este cálculo (§5).

## 5. Intervalos y pruebas pareadas de nDCG@10 (métrica titular)

Configuración: bootstrap BCa (2000 remuestreos, IC 95 %, semilla `20260907`), Wilcoxon
pareado (`zero_method="wilcox"`), corrección de Holm sobre las 120 comparaciones por pares,
Friedman como ómnibus.

- **Friedman:** χ² = 105,28 (`scipy.stats.friedmanchisquare`), n = 79, **p = 1,29 × 10⁻¹⁵**
  → estimable y válido, mucho más fuerte que el χ² = 30,00 (p = 0,0119) de v12.
- **14 de 120 pares tienen `holm_reject = True`.**

| Comparación | Δ nDCG@10 | IC 95 % (BCa) | p ajustado (Holm) |
|---|---:|---|---:|
| `hybrid-weighted-cf-v1` vs `popularity-v1` | +0,1526 | [0,0981; 0,2265] | 0,00987 |
| `hybrid-weighted-cf-v1` vs `random-v1` | +0,1526 | [0,0981; 0,2265] | 0,00987 |
| `content-cbf-weighted-v1` vs `popularity-v1` | +0,1452 | [0,0946; 0,2287] | 0,01462 |
| `content-cbf-weighted-v1` vs `random-v1` | +0,1452 | [0,0946; 0,2287] | 0,01462 |
| `hybrid-weighted-cf-v1` vs `recency-v1` | +0,1477 | [0,0914; 0,2237] | 0,01640 |
| `content-cbf-weighted-v1` vs `recency-v1` | +0,1403 | [0,0870; 0,2226] | 0,02382 |
| `content-cbf-weighted-pop-v1` vs `popularity-v1` | +0,1310 | [0,0822; 0,2105] | 0,03096 |
| `content-cbf-weighted-pop-v1` vs `random-v1` | +0,1310 | [0,0822; 0,2105] | 0,03096 |
| `content-cbf-multiplicative-pop-v1` vs `hybrid-weighted-cf-v1` | −0,1074 | [−0,1734; −0,0632] | 0,04342 |
| `hybrid-mmr-v1` vs `popularity-v1` | +0,1101 | [0,0651; 0,1744] | 0,04689 |
| `hybrid-mmr-v1` vs `random-v1` | +0,1101 | [0,0651; 0,1744] | 0,04689 |
| `content-cbf-multiplicative-pop-v1` vs `content-cbf-weighted-v1` | −0,1000 | [−0,1636; −0,0598] | 0,04886 |
| `content-cbf-multiplicative-v1` vs `hybrid-weighted-cf-v1` | −0,1028 | [−0,1655; −0,0579] | 0,04893 |
| `content-cbf-weighted-pop-v1` vs `recency-v1` | +0,1261 | [0,0750; 0,2047] | 0,04958 |

**Lectura correcta:**

- `hybrid-weighted-cf-v1`, `content-cbf-weighted-v1`, `content-cbf-weighted-pop-v1` y
  `hybrid-mmr-v1` son **estadísticamente superiores, tras corrección por comparaciones
  múltiples, a los dos baselines** (`random-v1`, `popularity-v1`). Los dos primeros
  también superan a `recency-v1`.
- El modo de combinación `multiplicative` (`content-cbf-multiplicative-v1` y su variante
  `-pop`) es **estadísticamente peor** que `weighted_sum` en las comparaciones directas
  frente a `hybrid-weighted-cf-v1` y `content-cbf-weighted-v1` — la única diferenciación
  entre variantes de contenido (no solo "contenido vs. baseline") que sobrevive Holm en
  este cálculo.
- Las 106 comparaciones restantes no sobreviven la corrección — con 120 comparaciones y
  n = 79, el poder estadístico para distinguir variantes de contenido *entre sí* (en vez
  de frente a los baselines) sigue siendo limitado, pero ya no es la limitación estructural
  casi total que era en v12 (§8.4 conserva la explicación del mecanismo).
- `cf-user-knn-v1` (colaborativo puro) no aparece en ninguna comparación significativa:
  su nDCG@10 (0,0525) queda por debajo de las variantes de contenido con `weighted_sum`,
  aunque por encima de `multiplicative` y de los baselines — ninguna de esas diferencias
  sobrevive Holm.

## 6. Más allá del acierto: cobertura, concentración, diversidad, novedad (K = 10)

| Algoritmo | Cob. catálogo | HHI | Diversidad intra-lista | Novedad (n aplicable) |
|---|---:|---:|---:|---:|
| `random-v1` | 5,62 % | 0,0013 | 0,817 | — (0/79) |
| `content-cbf-mmr-v1` | 1,73 % | 0,0124 | 0,668 | 10,79 (2/79) |
| `content-cbf-mmr-pop-v1` | 1,47 % | 0,0156 | 0,697 | 10,96 (1/79) |
| `hybrid-mmr-v1` | 1,97 % | 0,0103 | 0,637 | 9,56 (10/79) |
| `hybrid-weighted-cf-v1` | 1,87 % | 0,0094 | 0,523 | 9,53 (11/79) |
| `cf-user-knn-v1` | 1,40 % | 0,0407 | 0,696 | 8,88 (79/79) |
| `popularity-v1` | 0,08 % | 0,0988 | 0,641 | — (0/79) |
| `content-cbf-multiplicative-v1` | 0,95 % | 0,0287 | 0,611 | 9,41 (1/79) |
| `content-cbf-multiplicative-pop-v1` | 0,94 % | 0,0297 | 0,611 | 9,41 (1/79) |
| `content-cbf-twostage-v1` | 2,76 % | 0,0048 | 0,497 | 9,91 (6/79) |
| `content-cbf-twostage-pop-v1` | 2,78 % | 0,0046 | 0,495 | 9,92 (6/79) |
| `content-cbf-neg-v1` | 2,17 % | 0,0073 | 0,559 | 9,76 (2/79) |
| `content-cbf-neg-pop-v1` | 1,93 % | 0,0084 | 0,571 | 9,43 (1/79) |
| `content-cbf-weighted-v1` | 1,81 % | 0,0098 | 0,523 | 9,61 (5/79) |
| `content-cbf-weighted-pop-v1` | 1,52 % | 0,0130 | 0,561 | 10,21 (2/79) |
| `recency-v1` | 0,18 % | 0,0802 | 0,686 | — (0/79) |

Lectura:

- `random-v1` sigue teniendo, por construcción, la mayor cobertura de catálogo (5,6 %);
  `popularity-v1` la menor (0,08 %) — casi la misma lista para todos los usuarios.
- Frente a v12, la concentración (HHI) de las variantes de contenido baja drásticamente
  (0,55-0,71 en v12 → 0,005-0,03 aquí) y la diversidad intra-lista sube (0,006-0,12 en
  v12 → 0,50-0,61 aquí): consecuencia directa de que ahora sí usan similitud de tags real
  para el 100 % de los usuarios (§3), en vez de colapsar en el *fallback* de
  rating/PopScore/recencia compartido con los baselines.
- La novedad ahora es aplicable para muchos más usuarios que en v12 (donde las variantes
  MMR/híbridas tenían 0/73 aplicables): entre 1 y 11 usuarios según la variante reciben un
  ítem ausente de las bibliotecas de entrenamiento, coherente con perfiles de contenido
  reales explorando el catálogo más allá de lo popular.

## 7. Tiempos por algoritmo

| Algoritmo | Duración |
|---|---:|
| `popularity-v1` | 5,2 s |
| `random-v1` | 25,0 s |
| `cf-user-knn-v1` | 15,3 s |
| `content-cbf-weighted-v1` | 493,1 s |
| `content-cbf-multiplicative-v1` | 492,1 s |
| `content-cbf-twostage-v1` | 486,1 s |
| `content-cbf-neg-v1` | 485,1 s |
| `content-cbf-weighted-pop-v1` | 479,6 s |
| `content-cbf-multiplicative-pop-v1` | 477,1 s |
| `content-cbf-twostage-pop-v1` | 475,2 s |
| `content-cbf-neg-pop-v1` | 475,9 s |
| `recency-v1` | 424,2 s |
| `content-cbf-mmr-v1` | 488,2 s |
| `content-cbf-mmr-pop-v1` | 480,9 s |
| `hybrid-weighted-cf-v1` | 444,3 s |
| `hybrid-mmr-v1` | 492,1 s |
| Construcción del contexto compartido (una vez) | 36,7 s |
| Precómputo de señales compartidas (una vez) | 173,9 s |
| **Suma de duraciones por algoritmo** | **6.240,4 s** |
| **Tiempo de pared (2 workers + cola serial de 5)** | **4.285,2 s ≈ 1 h 11 min** |

Frente a v12 (proceso único, ~1000 s por variante de contenido, 3 h 42 min de pared total):
el precómputo compartido (§1.2, §1.3) reduce cada variante de contenido a ~475-493 s
(-50 % aprox.) y el tiempo de pared total a 1 h 11 min pese a evaluar el mismo número de
algoritmos sobre una población con perfiles de contenido reales (más trabajo por usuario
que el *fallback* de arranque en frío que dominaba v12). El coste residual por algoritmo
(sin la similitud/rating_term, ya en cache) es la combinación de señales (`combine()`),
la explicación (`explain()`) y la ordenación de 13.618 candidatas por usuario — no se
investigó a fondo si ese resto es optimizable más allá de lo ya hecho esta sesión.

## 8. Documentación del leave-one-out para el TFG

### 8.1 Qué es y por qué se eligió

Sin cambios respecto al protocolo v12 — leave-one-out (LOO) es el protocolo de partición
estándar para evaluar *top-K accuracy* con historial limitado por usuario: se retira
exactamente un ítem relevante, se reconstruye el perfil sin él, y se comprueba si el
algoritmo lo recupera en su top-K sobre un conjunto de candidatas común (Herlocker et al.,
2004; métricas de Järvelin y Kekäläinen, 2002, aplicadas a un único positivo por consulta).

### 8.2 Mecánica exacta en SavePoint (D-17, D-18, nuevo en v14: §1.1)

1. **Relevancia (D-17).** `current_status == "completed"` o `rating_half_steps >= 7`.
2. **Nuevo en v14: piso de rating externo en el retenido.** Antes de la elección
   aleatoria, se filtran los positivos del usuario a los que además tienen
   `rating IGDB >= 70` (§1.1) — si eso vacía el conjunto, el usuario se excluye del split
   (igual que "sin positivo elegible").
3. **Selección determinista del retenido.** `random.Random(f"{seed}:{user.id}")`, semilla
   `20260907`.
4. **Reconstrucción del perfil.** El ítem retenido se retira de la biblioteca visible
   antes de construir el perfil de contenido o colaborativo.
5. **Conjunto de candidatas común (EVAL-01).** Idéntico para los 16 algoritmos; hash por
   usuario agregado en `split_manifest_sha256`.
6. **Tarea de recuperación.** Top-K sobre ese conjunto; se mide si el ítem retenido
   aparece y en qué posición.

### 8.3 Consecuencias matemáticas de un único positivo por usuario

Sin cambios respecto a v12: con exactamente un ítem relevante por usuario,
`Recall@K ∈ {0, 1}` por usuario, `nDCG@K = 1 / log2(rango + 1)` si hay acierto. El agregado
por algoritmo (§4) es la media aritmética de esos valores sobre los 79 usuarios evaluables.

### 8.4 Por qué el poder estadístico sigue siendo limitado entre variantes de contenido

A diferencia de v12 (donde casi todos los pares comparaban "0 contra 0"), aquí la mayoría
de los algoritmos anotan un acierto no trivial (§4.2) — pero seguir comparando 16
algoritmos por pares (120 comparaciones) bajo Holm exige una diferencia grande para
sobrevivir. Las 14 comparaciones que sí sobreviven (§5) son, sin excepción, "contenido/
híbrido bueno contra baseline" o "weighted_sum contra multiplicative" — diferencias de
~0,10-0,15 en nDCG@10. Las diferencias más finas entre, por ejemplo, `content-cbf-weighted-v1`
y `content-cbf-weighted-pop-v1` (0,1452 vs 0,1310) no sobreviven Holm con n = 79.

### 8.5 Qué mide y qué no mide este protocolo

Sin cambios respecto a v12 (ver ese documento) — LOO de un único positivo mide si el
sistema recupera exactamente el ítem retenido, no la calidad general de la lista. Las
métricas del §6 (cobertura, concentración, diversidad, novedad) siguen siendo el
complemento necesario (McNee et al., 2006).

### 8.6 Interacción con la generación de usuarios sintéticos — ya resuelta

`evaluation-protocol.md` señalaba como amenaza a la validez que la generación de
bibliotecas sintéticas podría no garantizar, tras retirar un positivo, que el usuario
conservara las ≥ 3 entradas de evidencia que exige el perfil de contenido. El cálculo de
protocolo v12 confirmó esa interacción empíricamente (74 % `insufficient_history`). El
rediseño de población v13 (biblioteca 10-20, franja PopScore 75 %, mínimo 5 positivos
garantizados por `completed`/`playing` con rating ≥ 3,5/5) la resuelve por completo para
este split: **0 % `insufficient_history`** verificado directamente (§3). Sigue siendo una
interacción entre dos componentes congelados por separado (el generador de población y el
umbral de arranque en frío del ranker) — solo que ahora compatibles.

## 9. Fallos, omisiones y limitaciones

1. **10 usuarios omitidos por el arquetipo `no_history`** (§3): por diseño, no tienen
   biblioteca ni positivo que retener — no es una regresión ni un efecto del piso de
   rating v14 (verificado: 0 usuarios adicionales excluidos por el piso).
2. **Primer intento con `--max-workers 4` interrumpido por presión de memoria** (§1.3):
   sin escribir el marcador de consumo, sin coste; diagnóstico y causa raíz documentados.
3. **106 de 120 comparaciones por pares no sobreviven Holm** (§5, §8.4): sigue habiendo
   limitación de poder estadístico para diferenciar variantes de contenido *entre sí* con
   n = 79 y 120 comparaciones, aunque mucho menor que en v12.
4. **El coste residual por algoritmo de contenido (~480 s) no se investigó a fondo** (§7):
   se sabe que ya no es similitud/rating_term (en cache), pero no se perfiló qué fracción
   es `combine()`, `explain()` u ordenación.
5. **`tag-taste-v1` queda fuera de esta comparación** (como fija el protocolo): es una
   heurística de producto, no un algoritmo de la suite académica de 16.
6. Esta evaluación es **evidencia de simulación sobre arquetipos parametrizados**, nunca
   evidencia sobre usuarios reales de SavePoint (EVAL-10); las conclusiones se limitan al
   corpus `2026.09.2`, esta población de 400 usuarios y este protocolo v14. El siguiente
   estudio (20 usuarios reales, evaluación de calidad por encuestas) es un capítulo
   distinto, no comparativo con este — ver
   [[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]].

## 10. Amenazas a la validez

Se heredan las de `evaluation-protocol.md` (validez externa de usuarios sintéticos, sesgo
de LOO de un único positivo, sesgo de fuente única de rating, riesgo de circularidad de
arquetipos, congelación de un solo uso), con dos actualizaciones de esta ejecución:

- **Prevalencia de arranque en frío en el split de test (v12): RESUELTA.** Confirmada
  empíricamente en 0 % para este split bajo protocolo v14 (§3, §8.6). La amenaza registrada
  en el documento de v12 (§10) ya no aplica a este resultado.
- **Sesgo de rating externo en la selección del LOO (nueva amenaza, mitigada en v14).**
  Documentada y corregida en §1.1 — el piso de 70 reduce, sin eliminar del todo, el riesgo
  de que el acierto dependa parcialmente de la popularidad/calidad catalogada del ítem
  retenido en vez de solo del modelado de gusto. No se eliminó la dependencia de
  `rating_confidence`/PopScore en `combine()` en sí (eso cambiaría los algoritmos que se
  evalúan, no el protocolo de evaluación) — ver la opción descartada en
  [[2026-09-11 - Piso de rating externo en LOO y paralelizacion offline]].

## 11. Interpretación

Bajo el protocolo `2026.09.2`/v14 y este split de test de un solo uso:

- **`hybrid-weighted-cf-v1` y `content-cbf-weighted-v1` son estadísticamente superiores a
  `random-v1` y `popularity-v1`, y `hybrid-weighted-cf-v1` y `content-cbf-weighted-v1`
  también a `recency-v1`, tras corrección de Holm.** Esta es una conclusión sustantiva
  defendible del capítulo de evaluación del TFG, a diferencia del resultado de v12.
- **El modo de combinación importa:** `weighted_sum` supera significativamente a
  `multiplicative` en las comparaciones directas disponibles. No hay evidencia
  suficiente (tras Holm) para preferir una variante `weighted_sum` sobre otra entre sí
  (p. ej. con vs. sin PopScore, con vs. sin MMR) — esas diferencias existen en la media
  (§4.1) pero no sobreviven la corrección por 120 comparaciones con n = 79.
  Colaborativo puro (`cf-user-knn-v1`) no se diferencia significativamente de ningún otro
  algoritmo.
- El resultado es coherente con la arquitectura del sistema y con la resolución del
  hallazgo dominante de v12 (§8.6): una vez que las variantes de contenido usan similitud
  de tags real en vez de colapsar al mismo *fallback* que los baselines, se diferencian de
  ellos con claridad estadística.
- **Siguiente paso ya decidido por el autor** (no ejecutado en esta tarea): un estudio con
  20 usuarios reales, biblioteca propia, evaluación de calidad por encuestas — un capítulo
  de evaluación distinto y complementario, no una repetición comparativa de este. Ver
  [[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]] y
  `.planning/ROADMAP.md`.

## 12. Bibliografía citada

- Järvelin, K. y Kekäläinen, J. (2002). *Cumulated gain-based evaluation of IR
  techniques*. [DOI 10.1145/582415.582418](https://doi.org/10.1145/582415.582418).
- Herlocker, J. L., Konstan, J. A., Terveen, L. G. y Riedl, J. T. (2004). *Evaluating
  collaborative filtering recommender systems*.
  [DOI 10.1145/963770.963772](https://doi.org/10.1145/963770.963772).
- Carbonell, J. y Goldstein, J. (1998). *The use of MMR, diversity-based reranking...*
  [DOI 10.1145/290941.291025](https://doi.org/10.1145/290941.291025) — fundamento de la
  reordenación MMR usada en `content-cbf-mmr-*` y `hybrid-mmr-v1`.
- McNee, S. M., Riedl, J. y Konstan, J. A. (2006). *Being accurate is not enough: how
  accuracy metrics have hurt recommender systems*.
  [DOI 10.1145/1125451.1125659](https://doi.org/10.1145/1125451.1125659).
- Cremonesi, P., Koren, Y. y Turrin, R. (2010). *Performance of recommender algorithms on
  top-N recommendation tasks*. RecSys 2010.
  [DOI 10.1145/1864708.1864721](https://doi.org/10.1145/1864708.1864721) — fundamento del
  piso de rating externo del §1.1: el sesgo de popularidad en la evaluación offline top-N.
- Steck, H. (2011). *Item popularity and recommendation accuracy*. RecSys 2011.
  [DOI 10.1145/2043932.2043957](https://doi.org/10.1145/2043932.2043957) — idem, aplicado
  específicamente a cómo la popularidad del ítem de prueba sesga las métricas de acierto.

## 13. Artefactos y reproducibilidad

| Artefacto | Ruta | SHA-256 |
|---|---|---|
| Artefacto final (éxito) | `apps/api/evaluation-400-test-2026-09-11.artifact.json` | `740eb354ec9f80be6dafe5d66af95ca4454d718876c72517060acb7ff3cf6781` |
| Preflight de entradas (v14) | `apps/api/evaluation-input-preflight-2026-09-11-v14-gate.json` | `f47cebb55f2137b26f5adfa3ae5db8bea81262b18ec849c906f0af3fc12de694` |
| Preflight de entradas (v13, previo) | `apps/api/evaluation-input-preflight-2026-09-11-v13-gate.json` | `1ae0d3651f545f4542692291e94f9f244d94fb8b32d4739c17bf1b30c46e8ce1` |
| Marcador de consumo | `apps/api/.evaluation-test-run.json` | (contiene `protocol_sha256` y `consumed_at`, ver §1) |

Fuente normativa: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md),
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md), el
resultado previo
[`evaluation-results-400-test-2026-09-10.md`](./evaluation-results-400-test-2026-09-10.md)
(protocolo v12) y las notas de sesión en `ideas-vault/Fases/2026-09-11 - *.md`.
