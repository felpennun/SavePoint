# Protocolo de evaluación congelado (Fase 2)

- **Estado:** Congelado el 2026-09-07.
- **Ratificado por:** Felipe — Tarea 1 (`checkpoint:decision`, `blocking-human`) del Plan
  `02-08`, opción `ratify-as-proposed`, 2026-09-07. Registro en
  `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-08-CHECKPOINT.md`.
- **Contrato legible por máquina:** [`protocol.json`](./protocol.json). El cargador
  `apps/api/evaluation/protocol.py` valida ese fichero y se niega a correr si la rejilla de
  tuning excede las 24 combinaciones o si el split de test de ese protocolo ya fue consumido.
- **Requisitos que cumple:** EVAL-01, EVAL-02, EVAL-03, EVAL-10, DOC-04. Decisiones de
  `02-CONTEXT.md`: D-17..D-22.
- **Reversibilidad:** one-way. En cuanto una comparación citada en el TFG referencia
  `protocol.json` por su hash SHA-256, cambiar la relevancia, K, el split, la lista de
  métricas o el presupuesto de tuning invalida esa comparación y obliga a re-narrar el
  capítulo de evaluación. Ampliar la rejilla o el conjunto de métricas está previsto para la
  Fase 3; reducirlos o cambiar una definición no.

## Contexto

La Fase 2 introduce el primer recomendador basado en contenido de la tesis (REC-03), un
laboratorio paramétrico con tres modos de combinación (`weighted_sum`, `multiplicative`,
`two_stage`) y varios conjuntos de features. Antes de que corra **cualquier** variante
avanzada hay que congelar el protocolo de comparación: qué cuenta como acierto, sobre qué
candidatos, con qué métricas, con qué presupuesto de tuning y con qué aislamiento del
conjunto de test. Ese contrato es `protocol.json`; este documento es su lectura en prosa.

Todos los usuarios del harness son **sintéticos** (arquetipos parametrizados y regenerables
por semilla, Plan `02-09`). Cualquier resultado producido bajo este protocolo es evidencia
de simulación, no evidencia sobre usuarios reales de SavePoint (EVAL-10). Por eso
`protocol.json` y todo artefacto derivado llevan la marca `simulation: true` y una cadena
`limitation` explícita.

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
Está congelada en **24 configuraciones** (tope duro: 24; `protocol.load()` lanza
`ProtocolError` si `len(grid) > 24`):
- `weighted_sum`: 5 perfiles de señales × 3 conjuntos de features = 15. Los
  perfiles incorporan de forma progresiva similitud de contenido, rating de
  usuarios IGDB, `total_rating_count` como volumen y PopScore; los dos últimos
  añaden `recency_score` con peso explícito.
- `multiplicative`: × 3 conjuntos de features = 3.
- `two_stage`: bandas ∈ {3, 5} × 3 conjuntos de features = 6.
- Los conjuntos de features son `genres_platform`,
  `genres_platform_developer` y `genres_platform_developer_franchise`; la
  franquicia queda identificada como ablación exploratoria por su cobertura
  baja.
- La rejilla se puntúa **solo sobre `validation`**, con la métrica titular `ndcg@10`. Se
  bloquea la configuración ganadora.
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

Desde `protocol_version: 2`, el universo que puntuan los algoritmos se limita
a las obras gobernadas con `total_rating_count >= 1` o con un `rating` de
usuarios IGDB externo válido
en el intervalo `[0, 100]`, aunque su recuento sea cero o nulo. Las obras sin
ninguna de esas señales siguen disponibles para busqueda y coleccion, pero no
se devuelven como recomendaciones ni participan en las metricas. El item
retirado del leave-one-out tambien debe cumplir esta regla; de lo contrario,
el usuario no participa en ese split.
