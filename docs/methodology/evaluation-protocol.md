# Protocolo de evaluación congelado (Fase 3)

- **Estado:** Congelado como protocolo v6 el 2026-09-09.
- **Ratificado por:** Felipe — Tarea 1 (`checkpoint:decision`, `blocking-human`) del Plan
  `02-08`, opción `ratify-as-proposed`, 2026-09-07. Registro en
  `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-08-CHECKPOINT.md`.
- **Contrato legible por máquina:** [`protocol.json`](./protocol.json). El cargador
  `apps/api/evaluation/protocol.py` valida ese fichero y se niega a correr si la rejilla de
  tuning excede las 28 combinaciones o si el split de test de ese protocolo ya fue consumido.
- **Requisitos que cumple:** EVAL-01, EVAL-02, EVAL-03, EVAL-10, DOC-04. Decisiones de
  `02-CONTEXT.md`: D-17..D-22.
- **Reversibilidad:** one-way. En cuanto una comparación citada en el TFG referencia
  `protocol.json` por su hash SHA-256, cambiar la relevancia, K, el split, la lista de
  métricas o el presupuesto de tuning invalida esa comparación y obliga a re-narrar el
  capítulo de evaluación. Ampliar la rejilla o el conjunto de métricas está previsto para la
  Fase 3; reducirlos o cambiar una definición no.

## Contexto

La Fase 2 introduce el primer recomendador basado en contenido de la tesis (REC-03), un
laboratorio paramétrico con modos de combinación (`weighted_sum`, `multiplicative`,
`two_stage`) y cuatro variantes que incorporan PopScore. Antes de que corra **cualquier** variante
avanzada hay que congelar el protocolo de comparación: qué cuenta como acierto, sobre qué
candidatos, con qué métricas, con qué presupuesto de tuning y con qué aislamiento del
conjunto de test. Ese contrato es `protocol.json`; este documento es su lectura en prosa.

Todos los usuarios del harness son **sintéticos** (arquetipos parametrizados y regenerables
por semilla, Plan `02-09`). Cualquier resultado producido bajo este protocolo es evidencia
de simulación, no evidencia sobre usuarios reales de SavePoint (EVAL-10). Por eso
`protocol.json` y todo artefacto derivado llevan la marca `simulation: true` y una cadena
`limitation` explícita.

## Señal compuesta de calidad y confianza

El protocolo v6 y la web comparten la señal `rating_confidence` v3. Cuando una obra candidata
tiene rating IGDB observado, se usa directamente su calidad transformada; el perfil medio por
género ya no reduce esa nota. El perfil por género queda reservado como fallback auditable para
obras sin rating observado. La calidad del rating IGDB se normaliza con potencia 2 para separar
mejor las notas altas. El volumen se calcula con
`log1p(total_rating_count)` respecto al máximo de la vista congelada y actúa como refuerzo
acotado:

`rating_confidence = rating_quality * (0,80 + 0,20 * rating_volume)`.

El catálogo gobernado completo permanece disponible para búsqueda. El universo que puede entrar
en cualquier algoritmo es un subconjunto explícito: `rating IS NOT NULL AND total_rating_count >= 5`.
La condición exige simultáneamente una nota de usuario IGDB y al menos cinco valoraciones totales
de IGDB; no es una alternativa `OR`.

El volumen no se suma como término independiente en `recency-v1`, evitando doble conteo.
`display_rating` y las valoraciones SavePoint son datos de presentación y quedan fuera de la
puntuación algorítmica. La versión `rating-confidence-v3` invalida los resultados publicados con
la mezcla anterior; el protocolo mantiene v6 porque no cambia el split, K, las métricas ni el
conjunto de candidatos.

La valoración personal de cada juego semilla sí forma parte del perfil de preferencias. Su
intensidad se calcula como `(rating_half_steps / 10)^2`, sumada al peso de actividad del estado:
`completed = 3`, `playing = 2`, `pending = 1`, `abandoned = 0`. El perfil solo usa como evidencia
positiva juegos `completed` o `playing` con una valoración de al menos 3,5/5; de este modo una
valoración 5/5 pesa más que una 4/5 y los géneros repetidos acumulan evidencia ponderada.

`recency-v1` usa años naturales: una obra del año del corte recibe `recency_score = 1,0` y cada
año anterior multiplica la señal por `0,35` (`1,0`, `0,35`, `0,1225`, ...). Su combinación oficial
es contenido `0,30`, rating-confidence `0,20`, PopScore `0,10` y recencia `0,40`; así la novedad
domina en esta estantería sin eliminar las señales de afinidad y calidad.

## Relevancia (D-17)

Para un usuario sintético, un juego de su biblioteca es **relevante-positivo** si se cumple
cualquiera de:

- `current_status == "completed"`, **o**
- `rating_half_steps >= 7` (es decir, ≥ 3,5 sobre 5).

`protocol.json` lo fija como `"relevance": {"completed": true, "rating_half_steps_gte": 7}`.
Un usuario sin ningún juego relevante-positivo se excluye del split (no participa en la
evaluación) en lugar de provocar un error.

## Split leave-one-out por usuario (D-18)

El split es **leave-one-out por usuario**:

1. De los juegos relevante-positivos del usuario se retira exactamente uno, elegido de forma
   determinista por `random.Random(f"{seed}:{user.id}")` con la semilla congelada
   (`split.seed` en `protocol.json`).
2. El **conjunto de candidatos** es
   `governed_works(corpus_version)` − (biblioteca restante del usuario) ∪ {ítem retirado}.
   El ítem retirado se reincorpora siempre, aunque ya no estuviera en la vista gobernada.
3. El modelo debe recuperar el ítem retirado en su top-K sobre ese conjunto de candidatos.
4. El conjunto de candidatos es **idéntico para todos los algoritmos** dados el mismo usuario
   y la misma semilla (EVAL-01). El `sha256` del listado ordenado de `candidate_ids` se
   congela como manifiesto por usuario.

Con un único positivo por usuario, `Recall@K ∈ {0, 1}` y `nDCG@K = 1 / log2(rango + 1)` si
hay acierto. Aun así las métricas se implementan para el caso general multi-positivo, porque
la Fase 3 lo necesitará.

## K y métrica titular (D-19)

- Se reporta en **K ∈ {5, 10, 20}**.
- La **métrica titular** es `ndcg@10`. Es el criterio único con el que se selecciona la
  mejor configuración de la rejilla de tuning y con el que se comparan las variantes contra
  los baselines aleatorio (REC-01) y de popularidad (REC-02).

## Lista de métricas congelada (D-22)

La Fase 2 calcula, como mínimo, las métricas de ranking/acierto, escritas a mano y
verificadas contra fixtures de respuesta conocida en `apps/api/evaluation/tests/test_metrics.py`
(sin `scikit-learn`, sin `numpy`):

| Métrica | Definición usada |
|---|---|
| `precision@k` | aciertos en el top-K dividido por `k` |
| `recall@k` | aciertos en el top-K dividido por el número total de relevantes |
| `ndcg@k` | DCG con ganancias binarias y descuento `1 / log2(i + 2)` (i indexado en 0), normalizado por el DCG ideal sobre `min(#relevantes, k)` |
| `map@k` | media de la precisión media por consulta sobre el top-K |

Las métricas más-allá-del-acierto (cobertura de catálogo, novedad, diversidad intra-lista) y
las cohortes y tests estadísticos son de la **Fase 3** y no forman parte de este freeze.

## Rejilla de tuning y aislamiento del test (D-21)

- La población prevista es de 400 usuarios sintéticos nuevos que sustituyen a la población de
  la Fase 2. Se parte en tres subconjuntos **disjuntos** por una semilla fija
  (`user_split.seed`): `train` = 240, `validation` = 80, `test` = 80.
  La población se regenera con la semilla titular `20260909` y su manifiesto de validación.
- Las bibliotecas solo contienen obras con `rating_count >= 1`. La selección sin reemplazo
  usa pesos escalonados `1/2/4/8/16/32` para los tramos `1–4`, `5–19`, `20–99`,
  `100–499`, `500–1999` y `>=2000`, respectivamente.
- La **rejilla de tuning** se declara entera en `protocol.json` **antes** de correr nada.
Está congelada en **30 configuraciones** (tope duro: 30; `protocol.load()` lanza
`ProtocolError` si `len(grid) > 30`):
- `weighted_sum`: 5 perfiles de señales × 3 conjuntos de features = 15, más una
  variante publicada con PopScore = 16. Los
  perfiles incorporan de forma progresiva similitud de contenido, rating de
  usuarios IGDB, `total_rating_count` como volumen y PopScore; los dos últimos
  añaden `recency_score` con peso explícito.
- `multiplicative`: × 3 conjuntos de features = 3.
- `two_stage`: bandas ∈ {3, 5} × 3 conjuntos de features = 6.
- Además, la rejilla reserva una configuración para cada nueva forma de combinar PopScore:
  `multiplicative_popscore`, `two_stage_popscore` y `negative_weighted_sum_popscore`.
  Estas variantes usan `popscore_missing_floor = 0.0`, de modo que una obra sin PopScore
  recibe una penalización explícita y no se beneficia de una renormalización.
- Los conjuntos de features son `genres_platform`,
  `genres_platform_developer` y `genres_platform_developer_franchise`; la
  franquicia queda identificada como ablación exploratoria por su cobertura
  baja.
- La rejilla se puntúa **solo sobre `validation`**, con la métrica titular `ndcg@10`. Se
  bloquea la configuración ganadora.

La versión vigente de la similitud de contenido es `fs-v9` con regla
`facet-similarity-v5`, común a web, workers y evaluación offline. Género y
plataforma forman el núcleo de similitud; sus pesos `0,50` y `0,25` se
normalizan entre las facetas disponibles y se combinan con una media F0,5
(`beta = 0,5`), que prioriza la precisión del candidato frente a la cobertura
del perfil. Saga/franquicia y desarrollador actúan como confirmaciones
positivas con pesos máximos `0,02` y `0,015`, respectivamente: solo aportan
cuando coinciden con valores presentes en el perfil ponderado del usuario.
El bonus opcional combinado no puede superar `0,035`; la mera presencia de
una saga o un desarrollador no concede puntos, y la ausencia no se imputa ni
penaliza.

Las variantes que incorporan PopScore usan el contrato de pesos publicado en
el protocolo 8: 0,20 para PopScore en las sumas y desempates, `swing = 0,20`
en la variante multiplicativa y 0,20 en Recency. La ausencia de PopScore se
imputa a 0,0, por lo que no se transforma en una señal neutra.
- El **conjunto de test se corre una sola vez** (`tuning.test_runs = 1`). Su consumo se
  registra en un marcador de run; `protocol.load()` se niega a volver a correr el test de un
  protocolo ya consumido salvo que se suba `protocol_version` (o se pase la bandera explícita
  `allow_consumed_test=True`).
- El perfil de rating por género (D-13) es un **estadístico de corpus** derivado del snapshot
  inmutable `CorpusRatingSnapshot` de la `corpus_version` activa, no de datos de usuarios, así
  que es leakage-safe entre splits. Cualquier estadístico que *sí* se derivara de usuarios
  tendría que calcularse solo sobre `train` (EVAL-02).

## `corpus_version` y hashes de snapshots

El protocolo apunta al corpus `2026.09.2`. `snapshot_sha256` identifica el
snapshot de ratings de usuarios y `popscore_snapshot_sha256` identifica las
primitivas normalizadas y el compuesto PopScore. El runner toma la versión y
ambos hashes de forma explícita y aborta si hay deriva respecto a los datos
locales congelados.

## Amenazas a la validez

- **Validez externa de los usuarios sintéticos.** Los ~200 usuarios son arquetipos
  parametrizados, no una muestra de usuarios reales. Sus bibliotecas y sus valoraciones se
  generan por semilla a partir de una plantilla de comportamiento. Los resultados describen
  cómo se ordenan los algoritmos **sobre esa población simulada**; no son una estimación de la
  satisfacción de usuarios reales de SavePoint. Todo artefacto del harness lleva
  `simulation: true` y una cadena `limitation`, y las conclusiones del TFG deben separar
  explícitamente la evidencia de simulación de cualquier evidencia sobre usuarios reales
  (EVAL-10).
- **Sesgo del leave-one-out con un único positivo.** Retirar un solo juego que le gustó al
  usuario reduce la evaluación a un problema de recuperación binaria: `Recall@K` solo puede
  valer 0 o 1 y `nDCG@K` colapsa a `1 / log2(rango + 1)`. Esto favorece a los algoritmos que
  aciertan el ítem popular u obvio y penaliza poco la diversidad o la cobertura. La Fase 3
  introduce escenarios multi-positivo y métricas más-allá-del-acierto para compensarlo.
- **Sesgo de fuente única para la señal de rating externa.** El término de rating (D-13) y la
  relevancia por `rating_half_steps` se apoyan en una única fuente de rating de usuarios
  (IGDB, y de forma condicional RAWG). Un sesgo sistemático de esa fuente —comunidades
  sobre-representadas, inflación de notas en juegos recientes, cobertura desigual por
  plataforma o región— se propaga a la señal de relevancia y al término de rating por igual.
  El informe de calidad de datos (DATA-03) documenta la cobertura de rating sobre el corpus
  gobernado; la limitación se recoge además en ADR-008.
- **Arquetipos como fuente de circularidad.** Si los arquetipos de usuario sintético se
  diseñan con las mismas features que consume el recomendador (géneros, plataformas,
  franquicia, desarrollador), la evaluación puede medir en parte la coincidencia entre el
  generador y el modelo en lugar de la calidad del modelo. El Plan `02-09` fija los
  arquetipos a partir de literatura de simulación de usuarios de RecSys y los somete a
  ratificación del autor; el informe de validación (EVAL-09) hace explícita esa relación.
- **Congelación una sola vez.** Un error en `protocol.json` descubierto después de una
  comparación citada no se puede corregir sin invalidar esa comparación. La mitigación es el
  cargador fail-closed (`apps/api/evaluation/protocol.py`) y su batería de tests
  (`apps/api/evaluation/tests/test_protocol.py`), que fijan la forma del contrato y sus
  invariantes de freeze antes de que corra ninguna variante.

## Actualizacion v8: rating bayesiano

La señal compartida pasa a `rating-confidence-v5-final`. Para cada
candidata con rating IGDB observado se calcula primero
`rating_bayes = (n * rating_igdb + 25 * media_corpus) / (n + 25)`, donde
`n = total_rating_count` y `media_corpus` es la media IGDB ponderada por ese
recuento en el snapshot congelado. La señal final es `(rating_bayes / 100)^2`.

El cambio contrae las notas de pocas valoraciones hacia la media del corpus y
conserva casi intactas las notas con evidencia abundante. El recuento no vuelve
a sumarse ni a multiplicarse: ya participa una sola vez en el ajuste. Este
cambio invalida resultados anteriores de la señal de rating y eleva el
protocolo a v8, sin cambiar split, K, metricas ni conjunto de candidatas.

## Variantes MMR

El protocolo incluye dos variantes nuevas de reordenacion diversificada. Ambas
puntuan primero el mismo pool que su algoritmo base y aplican MMR sobre las 100
mejores candidatas, o sobre cinco veces K si ese numero es mayor. La primera
usa `content-cbf-weighted-v1`; la segunda usa `content-cbf-weighted-pop-v1`.

Con `lambda = 0,80`, el primer resultado es el de mayor relevancia base y cada
siguiente maximiza `0,80 * relevancia - 0,20 * similitud_maxima_con_seleccionados`.
La similitud de redundancia es el coseno de los vectores fs-v9. MMR cambia el
orden de seleccion, no la puntuacion base ni los pesos de Weighted o
Weighted-Pop.

## Evidencia y fuentes

- Contrato: [`protocol.json`](./protocol.json).
- Cargador y guardas de freeze: `apps/api/evaluation/protocol.py`
  (`ProtocolError`, `load()`, `frozen_hash()`, marcador de test consumido).
- Métricas escritas a mano: `apps/api/evaluation/metrics.py`.
- Split leave-one-out y partición de usuarios: `apps/api/evaluation/splits.py`.
- Tests que fijan todo lo anterior: `apps/api/evaluation/tests/test_protocol.py`,
  `apps/api/evaluation/tests/test_metrics.py`, `apps/api/evaluation/tests/test_splits.py`.
- Decisiones de origen: `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-CONTEXT.md`
  (D-17..D-22) y `02-RESEARCH.md` "Pattern 6: Frozen evaluation harness".

## Regla de elegibilidad del evaluador

En el protocolo vigente (v9), el universo que puntúan los algoritmos se limita
a las obras gobernadas, con fecha no futura, `rating IS NOT NULL` y
`total_rating_count >= 5`. Las obras fuera de esta intersección siguen
disponibles para búsqueda y colección, pero no se devuelven como
recomendaciones ni participan en las métricas. El ítem retirado del
leave-one-out también debe cumplir esta regla; de lo contrario, el usuario no
participa en ese split.

## Ejecución paralela de la Fase 4

La suite incluye los baselines, las once variantes de contenido y los dos
algoritmos nuevos de Fase 4: `cf-user-knn-v1` y `hybrid-weighted-cf-v1`. El
comando `run_evaluation_parallel` ejecuta un proceso independiente por
algoritmo sobre el mismo protocolo y manifiestos. El artefacto registra el
tiempo de cada proceso, el tiempo total de pared y los fallos sin publicar
resultados parciales como si fueran una comparación completa.

## Regla vigente desde la Fase 4

La elegibilidad actual exige simultáneamente obra gobernada, fecha no futura,
`rating IS NOT NULL` y `total_rating_count >= 5`. Las obras que no cumplen la
intersección siguen en el catálogo, pero quedan fuera de todos los algoritmos
y de sus métricas.

## Protocolo v10: rating final y MMR híbrido

El protocolo v10 congela la señal global en tres componentes reproducibles:
`rating_quality = rating_bayesian_normalized ^ 2`, `rating_confidence = n /
(n + m)` y `rating_final = rating_quality * rating_confidence`, con `n =
total_rating_count` y `m = 25`. El rating bayesiano usa la media del corpus
ponderada por `total_rating_count` como prior. Esta señal se utiliza una sola
vez en cada variante que consume calidad IGDB; no se aplica a ratings
personales ni a la similitud colaborativa.

La rejilla pasa a 31 configuraciones al incorporar la entrada MMR híbrida.
`hybrid-mmr-v1` combina `0,60` de Weighted y `0,40` de User-kNN, usa fallback
Weighted sin vecindad suficiente y aplica MMR sobre `max(100, 5 * K)` con
`lambda = 0,80`, coseno de `fs-v9` y 20 resultados publicados. El runner
offline y el worker web comparten esta implementación y el mismo conjunto de
candidatas, exclusiones, snapshots y split. La evaluación de los 400 usuarios
queda pendiente y no se infieren resultados hasta ejecutarla.
