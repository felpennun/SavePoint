# Phase 3: Explainable Content Recommenders and Baseline Comparison - Context

**Gathered:** 2026-09-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Completar el **arnés de evaluación como evidencia de tesis** sobre los cinco
algoritmos que ya define la Fase 2 (`random-v1`, `popularity-v1`,
`content-cbf-weighted-v1`, `content-cbf-multiplicative-v1`,
`content-cbf-twostage-v1`), corriéndolos bajo el protocolo congelado y dejándolo
todo **recalculable desde artefactos inmutables sin re-ejecutar ningún modelo**.

En concreto la Fase 3 entrega:

- El **conjunto completo de métricas** más allá del acierto — cobertura de
  catálogo, diversidad intra-lista y novedad — además de las métricas de ranking
  ya congeladas, todas con su justificación escrita (EVAL-04, EVAL-05).
- El **desglose de cada métrica por cohorte de usuario** (tamaño de biblioteca y
  arquetipo), incluyendo el grupo sin historial y el de historial escaso
  (EVAL-07).
- **Multi-semilla** con estimaciones de incertidumbre (bootstrap sobre usuarios +
  dispersión entre semillas) y **tests estadísticos justificados** (Friedman +
  Wilcoxon pareado + corrección Holm) (EVAL-08).
- **Registro completo de la identidad de cada run** — commit de código, entorno,
  dataset, split, semillas, parámetros, modelo, identidad de métricas — sin alias
  mutables (EVAL-11), y grabación de tiempo de cómputo y consumo de recursos
  (EVAL-06).
- **Artefactos inmutables por run** desde los que se recalculan todos los
  agregados, cohortes, intervalos y tests offline (EVAL-12).
- **Visibilidad de runs fallidos**: estado explícito `complete | partial |
  failed`, con el recálculo y el volcado a las tablas del TFG rechazando todo lo
  que no sea `complete` (criterio de éxito 4).
- Un **camino de reproducción desde instalación limpia** para los experimentos y
  su evidencia (QUAL-02), y un **documento de informe con tablas en español**
  generado de forma reproducible desde los artefactos, para uso directo en la
  memoria (criterio de éxito 5).

**Fuera de esta fase:** recomendadores colaborativos e híbridos (Fase 4); el
panel de investigación interactivo y accesible con gráficas y exportación de
figuras/datos (EVAL-13, EVAL-14, QUAL-04 → Fase 7); cualquier señal de tendencia
o popularidad de mercado en vivo desde datos externos (Fase 6); rediseño de
producto o pulido de páginas de usuario final.

</domain>

<decisions>
## Implementation Decisions

### A — Métricas más allá del acierto (EVAL-04, EVAL-05)

- **D-01:** La **diversidad intra-lista** se mide con **distancia coseno sobre el
  `WorkFeatureVector`** ya cacheado por el recomendador de contenido (géneros +
  plataformas + saga + desarrollador + señal de rating). No se añade código de
  features nuevo. Se documenta explícitamente en la memoria que, al compartir
  espacio con el criterio del `content-cbf`, ese algoritmo tenderá a puntuar bajo
  en diversidad y el baseline aleatorio alto: es un hallazgo esperable de
  simulación, no un fallo de ejecución.
- **D-02:** La **novedad** se mide como **self-information promediada sobre la
  lista top-N**: `novelty(ítem) = -log2(fracción de usuarios sintéticos que
  tienen el ítem en su biblioteca)`. Es la definición estándar de RecSys (Vargas
  & Castells 2011; Zhou et al. 2010) y usa la misma señal de popularidad que
  `rank_popularity_v1`, calculable offline y de forma determinista desde el
  snapshot inmutable. En la memoria se etiqueta como **"novedad respecto a la
  población simulada"**, nunca como tendencia de mercado real. Se **descarta**
  `rating_count` externo de IGDB como señal de novedad (decisión del autor: el
  recuento histórico de valoraciones no indica que un juego sea novedad ni
  tendencia ahora, y su cobertura sobre el corpus gobernado es baja, ~13,9 %).
  El research fija la variante exacta de la fórmula (normalización, base del
  logaritmo) siempre que sea 100 % reproducible offline desde el artefacto.
- **D-03:** La **cobertura de catálogo** se reporta como la **fracción única del
  corpus gobernado que aparece en el top-N de algún usuario del split**, a
  **N ∈ {10, 20}**, más un **índice de concentración de la exposición** (Gini o
  entropía de cuántas veces se recomienda cada ítem) como cifra secundaria. Se
  documenta que el baseline aleatorio satura la cobertura por construcción
  (hallazgo legítimo).
- **D-04:** El conjunto de métricas de la Fase 3 se **cierra en esas tres**
  (cobertura, diversidad, novedad) además de las de ranking ya congeladas
  (Precision@K, Recall@K, nDCG@K, MAP@K). **No** se añaden serendipia,
  `APLT`/`ARP` (sesgo de popularidad) ni otras métricas: menos superficie que
  justificar y mantener estable en la tesis. — **Reversibility:** costly —
  ampliar la lista de métricas de `protocol.json` está previsto por el freeze
  (`evaluation-protocol.md` §"Lista de métricas congelada"); reducirla o cambiar
  una definición tras una comparación citada no lo está.
- **D-05:** Las tres métricas beyond-accuracy se **implementan y se testean desde
  su definición** contra fixtures de respuesta conocida, siguiendo el patrón de
  `apps/api/evaluation/metrics.py` y la convención del STACK "implement project
  metrics explicitly". `numpy`/`scipy` (ver D-11) **no** las sustituyen.
- **D-06:** Las tres métricas nuevas las **añade la Fase 3 al contrato de
  evaluación** (`docs/methodology/protocol.json`, clave `metrics`) y a la prosa de
  `evaluation-protocol.md`, versionándolo a **`protocol_version: 2`** (ver D-13).
  Es **evolución prevista del freeze** — `evaluation-protocol.md` §"Lista de
  métricas congelada" declara que ampliar el conjunto de métricas es trabajo de
  la Fase 3 — **no una modificación retroactiva de la Fase 2**: la comparación v1
  y su hash siguen intactos y citados como primer resultado. — **Reversibility:**
  one-way — una vez que una comparación del TFG referencia `protocol.json` v2 por
  su hash, cambiar la definición de una métrica invalida esa comparación.

### B — Multi-semilla, incertidumbre y tests estadísticos (EVAL-06, EVAL-08)

- **D-07:** La evaluación multi-semilla de EVAL-08 son **8-10 repeticiones
  "baratas"** (se re-sortea únicamente qué juego relevante-positivo se esconde
  por usuario; los mismos usuarios sintéticos) para formar la banda de robustez,
  **más 1 repetición con la población sintética entera regenerada** como
  comprobación de que la ordenación de algoritmos sobrevive a otra población.
  La run con la **semilla titular fijada en `protocol.json` v2** es la
  **comparación citada como principal de la tesis**; las semillas adicionales se
  declaran en una **sección `robustness` del `protocol.json` v2** (lista explícita
  de semillas) **antes** de correr nada, sin tocar la semilla titular.
  — **Reversibility:** costly — la lista de semillas de robustez pasa a formar
  parte del contrato de evidencia en cuanto una banda de incertidumbre se cita en
  la memoria.
- **D-08:** El **runner graba, en cada artefacto, el tiempo de cómputo y el
  consumo de recursos** por algoritmo y de forma agregada (EVAL-06): al menos
  tiempo de pared por algoritmo y por usuario, y pico de memoria del proceso.
- **D-09:** La **banda de incertidumbre** de cada métrica se estima con **dos
  mecanismos combinados**: (a) **bootstrap sobre usuarios** — IC 95 % percentil
  re-muestreando con reemplazo los usuarios del split de test dentro de cada
  repetición; (b) **dispersión entre semillas** — media ± desviación de la
  métrica titular sobre las 8-10 repeticiones. Cubren, respectivamente, el ruido
  por muestra de usuarios y el ruido por la tirada de azar.
- **D-10:** El **contraste de hipótesis** es **Friedman omnibus** sobre los cinco
  algoritmos y, si hay diferencia global, **Wilcoxon signed-rank pareado por
  usuario** sobre `nDCG@10` en los pares de interés (cada algoritmo frente al
  baseline de popularidad; contenido frente a aleatorio), con **corrección de
  Holm** por comparaciones múltiples. No paramétrico. Se descarta la **t de
  Student pareada** porque las diferencias de `nDCG` bajo leave-one-out con un
  único positivo no son normales. La justificación de la elección se escribe en
  el documento de metodología.
- **D-11:** Se **aprueba `scipy`** (con `numpy` como dependencia transitiva)
  **para toda la parte estadística**: tests de hipótesis (`scipy.stats.wilcoxon`,
  `friedmanchisquare`), bootstrap e intervalos de confianza. Es una **dependencia
  nueva** y pasa por el **gate de aprobación del proyecto en el PLAN**: pin exacto
  de versión + evidencia de release en PyPI + aprobación humana, siguiendo el
  patrón de `01-01-PLAN.md`. Esta decisión **revierte la ratificación
  pure-Python del checkpoint del Plan 02-10 solo para la parte estadística**; el
  propio checkpoint dejó "numpy ahora vs Fase 3" abierto para esta fase. Las
  métricas de ranking y beyond-accuracy siguen escritas a mano y verificadas
  (D-05). — **Reversibility:** costly — quitar `scipy` después obliga a
  reimplementar Wilcoxon/Friedman/bootstrap a mano y re-verificar toda la
  evidencia estadística citada.

### C — Población sintética enriquecida y protocol_version 2, todo dentro de la Fase 3 (EVAL-07, EVAL-08, EVAL-09)

> **Encaje con la Fase 2 (instrucción del autor 2026-09-07):** la Fase 3 se
> ejecuta **después de una Fase 2 terminada y sin modificar**. No hay puente de
> re-freeze previo. La población de 200 usuarios de la Fase 2, su manifiesto de
> generación, el `protocol.json` v1 y su primera comparación (Plan 02-13) quedan
> **intactos y se citan como primer resultado** (ranking, 200 usuarios). Todo lo
> de abajo es **trabajo propio de la Fase 3**, montado encima de ese v1
> congelado.

- **D-12:** La Fase 3 **genera una población sintética nueva y enriquecida de
  ≥ 400 usuarios** (adicional a la de 200 de la Fase 2, con su **propia semilla y
  su propio manifiesto**), con esta composición pedida por el autor:
  - **10 usuarios con 0 juegos** (cohorte sin historial),
  - **100 usuarios con 1-4 juegos** (cohorte de historial escaso / cold-start),
  - **50 usuarios con más de 10 juegos** (cohorte de usuario intensivo),
  - **el resto (~240) con 5-10 juegos** (cohorte normal).

  Por usuario: **notas propias variadas** (distintas puntuaciones), **algunas
  cuentas con `OwnedCopy`** registradas y **otras sin ninguna**. Los juegos que
  entran en las bibliotecas se eligen del corpus gobernado con
  **`rating_count` ≥ 10**, **salvo 1-2 usuarios sembrados por semilla** que tienen
  a propósito un juego **sin ninguna valoración**, para ejercitar en evaluación
  el camino "sin valoración" (D-07 de la Fase 2) y la mediana de género. El
  research fija el umbral exacto de `rating_count` y la proporción de excepciones
  contra la distribución real del corpus. Se **extiende** el generador de la
  Fase 2 (`apps/api/evaluation/synthetic.py`, `archetypes.py`,
  `generate_synthetic_users.py`) de forma **aditiva**, sin cambiar el
  comportamiento con el que se generó la población de 200.
- **D-13:** La Fase 3 **versiona el contrato de evaluación a `protocol_version: 2`**
  como entregable propio (no es una modificación retroactiva de la Fase 2; el
  freeze ya prevé esta evolución). El `protocol.json` v2:
  1. **re-dimensiona `user_split`** para la población ≥ 400 — el research propone
     las proporciones train/validación/test (orientativo ~60/20/20) de forma que
     **cada cohorte tenga un tamaño usable en el split de test**;
  2. define la **cohorte cold-start como "1-4" juegos** (la de la Fase 2 era
     "1-3"; la v1 no se toca);
  3. **añade la clave `metrics`** ampliada (D-06) y la sección `robustness`
     (D-07);
  4. **fija su propia `corpus_version` y `snapshot_sha256`** (los del corpus
     gobernado vigente al ejecutar la Fase 3, que puede ser el mismo `2026.09.1`
     de la Fase 2 si no ha cambiado).

  El `protocol.json` v1, su hash y el artefacto de la comparación 02-13 **no se
  tocan**; la Fase 3 corre los cinco algoritmos bajo v2 con **su propio marcador
  de test consumido** (mecanismo `--force-new-protocol` / `record_test_run`, que
  es exactamente para esto). — **Reversibility:** one-way — `protocol_version: 2`
  y su `user_split` pasan a ser el contrato de evidencia de las comparaciones
  principales de las Fases 3 y 4; cambiarlos después invalida esas comparaciones
  y obliga a re-narrar el capítulo de evaluación.
- **D-14:** El **tamaño total exacto** (≥ 400 es el piso; el research puede
  proponer un número redondo mayor, p. ej. 400-500, para que las proporciones
  train/val/test y de cohortes salgan limpias), las **proporciones del
  `user_split` v2** y si `protocol.json` v2 se escribe **en el mismo fichero
  versionado** o en un `protocol.v2.json` aparte, los fija el research en el PLAN
  y los **ratifica el autor** en un `checkpoint:decision`, dado que D-13 es
  `one-way`.

### D — Cohortes y usuarios sin historial (EVAL-07)

- **D-15:** Cada métrica (acierto, ranking y las tres beyond-accuracy) se
  reporta **desglosada por dos ejes de cohorte**: (a) **tamaño de biblioteca**
  (0 / 1-4 / 5-10 / >10) y (b) **arquetipo** (~8 perfiles de comportamiento
  documentados). El desglose titular por cohorte se calcula sobre los usuarios
  del **split de test**; se reportan **intervalos anchos y honestos** donde el
  `n` por cohorte sea pequeño.
- **D-16:** El **grupo "0 juegos"** no es evaluable en acierto/ranking bajo
  leave-one-out (no tiene juego que esconder). En las tablas del TFG ese grupo
  lleva **acierto/ranking = "no definido bajo leave-one-out"**. En su lugar se le
  mide: (a) un **chequeo de cold-start** — que el fallback (REC-06) devuelve una
  lista **válida, no vacía y determinista** que no excluye nada indebidamente; y
  (b) **cobertura / diversidad / novedad de lo que se le recomienda** (esas no
  necesitan un ítem escondido). Es coherente con el criterio de éxito 4 (estados
  ausentes visibles, nunca evidencia parcial silenciosa).
- **D-17:** La **etiqueta de cohorte de cada usuario sintético** (arquetipo +
  banda de tamaño) se **graba en el manifiesto de generación** reproducible por
  semilla (EVAL-09). La evaluación **lee la etiqueta**, no la re-infiere al
  vuelo, para que las tablas sigan siendo comparables entre runs aunque cambien
  los cortes.

### E — Artefactos inmutables, identidad de run y runs fallidos (EVAL-06, EVAL-11, EVAL-12, criterio 4, QUAL-02)

- **D-18:** Por cada run se persiste, **por usuario y por algoritmo**: la **lista
  top-N rankeada de candidatos** (N ≈ 100; el planner fija el valor exacto,
  siempre ≥ max(K)=20 y ≥ lo que necesiten cobertura y novedad), el id del juego
  escondido, el conjunto de relevantes, la **etiqueta de cohorte** y el **tiempo
  de cómputo** (D-08). Desde ese artefacto se **recalculan offline todas las
  métricas a K ≤ N, todos los cortes por cohorte, todos los intervalos bootstrap
  y todos los tests, sin re-ejecutar ningún recomendador** (EVAL-12).
- **D-19:** Formato y ubicación de los artefactos: **JSON commiteado bajo
  `docs/verification/evaluation/`**, un fichero por run
  (`protocol_version` × población × semilla × split), más un **`MANIFEST`** que
  indexa todos los runs por su hash. Compresión gzip si el tamaño lo exige. Sin
  git-LFS ni almacenamiento externo.
- **D-20:** **Identidad de entorno completa y automática** en cada artefacto,
  grabada por el runner (EVAL-11, "sin alias mutables"): SHA de commit de git,
  **versión exacta de Python**, **hash de los lockfiles** (API y web si aplica),
  **lista hasheada de paquetes instalados** (`pip freeze`), string de
  SO/plataforma, y **digest de la imagen de contenedor** si el run corre en
  Docker. Es la base sobre la que QUAL-02 detecta que un entorno limpio ha
  derivado.
- **D-21:** **Runs fallidos visibles.** Cada artefacto lleva
  `status: complete | partial | failed` y un **bloque de completitud** (usuarios
  intentados / logrados por algoritmo). Un artefacto `partial`/`failed` **sí se
  escribe** (para depuración), pero el **comando de recálculo** y el paso de
  **volcado a las tablas del TFG se niegan a consumir nada que no sea
  `complete`**, y el documento de verificación pinta un **banner "RUN
  INCOMPLETO"** en lugar de números. — **Reversibility:** reversible.
- **D-22:** **Salida de la fase = artefactos JSON + un documento de informe con
  tablas, en español**, generado de forma **reproducible desde los artefactos**
  (algoritmos × métricas × cohortes × IC × p-valores). **Sin interfaz
  interactiva**: el panel de investigación accesible con gráficas y exportación
  de figuras/datos es EVAL-13 / EVAL-14 / QUAL-04 = Fase 7. El planner decide el
  formato exacto del informe (Markdown en `docs/`, tablas LaTeX para `thesis/`, o
  ambos) según cómo se integre con la memoria.
- **D-23:** El **camino de reproducción de QUAL-02** es un **comando o secuencia
  documentada única** que, desde una instalación limpia, regenera la población
  sintética por semilla, corre el/los run(s) y **produce los mismos artefactos y
  el mismo informe** (salvo la identidad de entorno de D-20, que se compara para
  detectar deriva). Se acompaña de un documento de verificación en español. El
  planner dimensiona el **presupuesto de tiempo** aceptable de esa ejecución
  (400+ usuarios × 5 algoritmos × ~190k candidatos × multi-semilla en Python
  puro más `scipy` para stats) y, si hace falta, acota N o el número de semillas
  de la ejecución de reproducción por defecto.

### Dependencias y conflictos entre fases (CRÍTICO — leer antes de planificar)

**Premisa fijada por el autor (2026-09-07):** la Fase 3 se ejecuta **después de
que la Fase 2 esté terminada, y la Fase 2 no se modifica**. No hay puente de
re-freeze previo; toda la ampliación (población ≥ 400, `protocol_version: 2`,
métricas beyond-accuracy, `robustness`) es trabajo interno de la Fase 3.

1. **Precondición: la Fase 2 debe estar cerrada.** Hoy están hechas las olas 1-4
   (planes 02-01..02-05, 02-07..02-11); quedan **02-06, 02-12 y 02-13** (la
   primera comparación completa), con código aún sin commitear en el árbol de
   trabajo (`apps/api/evaluation/runner.py`, `candidates.py`,
   `management/commands/run_evaluation.py`, `tests/test_runner.py`). La Fase 3
   **no arranca hasta que la Fase 2 entregue ese arnés base y su comparación v1**.

2. **`protocol_version: 2` es un entregable de la Fase 3, no una re-apertura de
   la Fase 2.** El `protocol.json` v1, su hash y el artefacto de la comparación
   02-13 quedan **intactos** y se citan como primer resultado (ranking, 200
   usuarios). La Fase 3 escribe v2 (D-13), genera su propia población ≥ 400
   (D-12, semilla y manifiesto propios), extiende de forma **aditiva** el
   generador y `apps/api/evaluation/protocol.py`, y corre los cinco algoritmos
   bajo v2 con **su propio marcador de test consumido**. Nada de esto edita
   planes, artefactos ni el alcance entregado de la Fase 2.

3. **Lo que NO cambia del freeze v1 → v2:** la regla de relevancia (D-17 Fase 2),
   la estrategia de split **leave-one-out** (D-18 Fase 2), K ∈ {5,10,20}, la
   métrica titular `nDCG@10`, la rejilla de tuning de 18 configuraciones (tope
   24) y el aislamiento del test (una sola ejecución por versión, marcador de
   consumo). v2 solo **re-dimensiona `user_split`**, **amplía `metrics`**,
   **añade `robustness`** y **redefine la banda cold-start a 1-4**.

4. **La memoria del TFG cita dos comparaciones:** v1 (Fase 2, 200 usuarios,
   solo ranking) como primer resultado, y **v2 (Fase 3, ≥ 400 usuarios, suite
   completa + cohortes + estadística) como comparación principal**. El capítulo
   de evaluación debe distinguirlas explícitamente.

5. **Nueva dependencia:** `scipy` + `numpy` (D-11) requieren aprobación humana con
   pin exacto y evidencia PyPI en el PLAN, y revierten parcialmente una
   ratificación previa (checkpoint 02-10).

6. **Idea abierta que puede ampliar el alcance:** la variante de señal negativa
   (Claude's Discretion, abajo) podría añadir un sexto algoritmo con nombre al
   `ALGORITHM_REGISTRY` y a la comparación v2.

### Claude's Discretion

- **Variante de contenido con señal negativa (`content-cbf-neg-v1` u otro
  nombre).** El autor planteó que una **nota propia baja** debería **restar
  afinidad al género correspondiente**, con una **salvaguarda** para el caso "es
  el único juego de ese género en la biblioteca y simplemente es un mal juego"
  (no penalizar el género entero por una sola señal). El research evalúa si es
  barata de implementar sobre el laboratorio de contenido existente y si aporta
  frente a las tres variantes actuales; el planner propone en el PLAN si entra
  como **variante nueva con nombre comparada bajo el mismo protocolo** (encaja
  con "additional content-based variants" del goal de la fase en el ROADMAP) o si
  se **difiere**. El autor lo ratifica en el PLAN.
- **Fórmula exacta de novedad** (D-02): variante concreta (Vargas & Castells,
  normalización, tratamiento de ítems con frecuencia cero), con la restricción de
  reproducibilidad offline.
- **Elección Gini vs entropía** para el índice de concentración de cobertura
  (D-03).
- **Valor exacto de N** en la persistencia top-N (D-18) y **formato del informe**
  (D-22).
- **Presupuesto de tiempo y posibles recortes** de la ejecución de reproducción
  por defecto (D-23).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap y requisitos
- `.planning/ROADMAP.md` §"Phase 3: Explainable Content Recommenders and Baseline
  Comparison" — goal, requisitos, 5 criterios de éxito.
- `.planning/REQUIREMENTS.md` — EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08,
  EVAL-11, EVAL-12, QUAL-02 (y el contexto de EVAL-01/02/03/09/10 ya cerrados en
  la Fase 2).
- `.planning/PROJECT.md` — Core Value, Constraints (reproducibilidad académica,
  legalidad/procedencia, doble entrega), convención de idioma.

### Protocolo de evaluación v1 congelado (base que la Fase 3 versiona a `protocol_version: 2`)
- `docs/methodology/protocol.json` — contrato v1 legible por máquina: relevancia,
  K, split, candidate set, exclusiones, lista de métricas, rejilla de tuning
  (tope 24), `user_split` (120/40/40), `corpus_version`, `snapshot_sha256`. La
  Fase 3 escribe **v2** (en este fichero versionado o en `protocol.v2.json`, D-14)
  re-dimensionando `user_split` para ≥ 400 + ampliando `metrics` + añadiendo
  `robustness`; **el v1 y su hash no se tocan** (D-13).
- `docs/methodology/evaluation-protocol.md` — lectura en prosa del protocolo v1;
  §"Lista de métricas congelada" declara que ampliar el conjunto de métricas es
  trabajo de la Fase 3; §"Amenazas a la validez" declara que la Fase 3 introduce
  escenarios multi-positivo y métricas beyond-accuracy. La Fase 3 añade la prosa
  de v2 (documento nuevo o sección nueva), sin reescribir la de v1.
- `apps/api/evaluation/protocol.py` — cargador fail-closed (`ProtocolError`,
  `load()`, `frozen_hash()`, `record_test_run`, `_check_not_consumed`,
  `MAX_GRID = 24`, `REQUIRED_KEYS`, `_bump_protocol` / `--force-new-protocol`).
  Se **extiende de forma aditiva** para `metrics` ampliado, `robustness` y
  `user_split` de ≥ 400, sin romper la carga de v1.

### Arnés de evaluación existente (a extender, no reescribir)
- `apps/api/evaluation/runner.py` — `run(protocol, corpus_version, algorithms,
  split)`, `default_algorithms()` (los cinco), `snapshot_sha256`,
  `validate_snapshot_coverage`, `_code_commit`, forma del artefacto JSON (12
  campos). Base para D-08, D-18, D-20, D-21.
- `apps/api/evaluation/candidates.py` — `build(user, protocol, corpus_version)`:
  candidate set único y compartido por todos los algoritmos + hash de manifiesto.
- `apps/api/evaluation/metrics.py` — Precision/Recall/nDCG/MAP escritas a mano,
  caso general multi-positivo; patrón para las tres métricas beyond-accuracy
  (D-05).
- `apps/api/evaluation/splits.py` — `relevant_positive_ids`, `leave_one_out`,
  `user_split` (sizes desde `protocol.user_split`). `user_split` exige
  exactamente `train + validation + test` usuarios distintos — hay que
  re-dimensionar para ≥ 400 (D-13).
- `apps/api/evaluation/synthetic.py`, `apps/api/evaluation/archetypes.py`,
  `apps/api/evaluation/management/commands/generate_synthetic_users.py` —
  generación de usuarios sintéticos por arquetipo/semilla (EVAL-09). Base para
  D-12 (≥ 400, composición de cohortes, notas variadas, `OwnedCopy`, filtro
  `rating_count ≥ 10`, excepciones sembradas) y D-17 (etiqueta de cohorte en el
  manifiesto).
- `apps/api/evaluation/management/commands/run_evaluation.py` — comando de run
  único (`--corpus-version`, `--split`, `--evidence-json`, marcador de test
  consumido, `--force-new-protocol`). Base para D-19, D-23.

### Recomendadores bajo evaluación
- `apps/api/recommendations/content/variants.py` — `ALGORITHM_REGISTRY` y
  `VariantSpec` (`content-cbf-weighted-v1`, `-multiplicative-v1`,
  `-twostage-v1`). Punto de extensión para la variante de señal negativa
  (Claude's Discretion).
- `apps/api/recommendations/content/rank.py` — `rank_content_v1(user,
  algorithm_id, limit, corpus_version, candidate_ids)`.
- `apps/api/recommendations/content/features.py` — `FEATURE_SET_VERSION` y el
  `WorkFeatureVector`; espacio de features para la distancia coseno de
  diversidad (D-01).
- `apps/api/recommendations/content/explain.py` — explicación determinista por
  variante (patrón de trazabilidad, relevante para el informe D-22).
- `apps/api/recommendations/baselines.py` — `rank_random_v1` (REC-01).
- `apps/api/library/popularity.py` — `rank_popularity_v1` (REC-02), restringido a
  cuentas demo; misma señal de popularidad que usa la novedad (D-02).

### ADRs y convenciones
- `docs/adr/ADR-007-genre-taste-heuristic.md` — patrón `algorithm_id` +
  `input_snapshot_sha256` + estado distinto para historia insuficiente.
- `docs/adr/ADR-008-external-ratings.md` — procedencia RAWG/IGDB, sesgo de fuente
  única de la señal de rating (amenaza a la validez que hereda la Fase 3).
- `.planning/phases/01-three-day-public-demo-slice/01-01-PLAN.md` — patrón del
  gate de aprobación de dependencias nuevas (pin exacto + evidencia PyPI +
  aprobación humana), aplicable a `scipy`/`numpy` (D-11).
- `CONVENTIONS.md` — idioma: prosa nueva de `.planning/**` y documentación de
  tesis en español; código en inglés; tokens neutrales y citas legales se
  conservan. `scripts/check-evidence.ps1` exige encabezados de ADR en español si
  se crea un ADR para `scipy`.

### Contexto de fase previa
- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-CONTEXT.md`
  — D-08 (inmutabilidad del snapshot), D-10/D-14 (laboratorio de contenido),
  D-13 (perfil de rating por género), D-17..D-23 (protocolo congelado).
- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-13-PLAN.md`
  — la primera comparación completa (`protocol_version: 1`, 200 usuarios, solo
  ranking); **intacta**, se cita como primer resultado frente a la comparación
  principal v2 de la Fase 3.
- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-RESEARCH.md`
  §"Pattern 6: Frozen evaluation harness" — campos del artefacto, Pitfall 4
  (drift de `corpus_version`), Pitfall 6 (candidate set correcto).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/api/evaluation/metrics.py`: las cuatro métricas de ranking ya están
  escritas para el caso general multi-positivo y verificadas contra fixtures —
  las tres beyond-accuracy siguen el mismo patrón y el mismo fichero de tests.
- `apps/api/evaluation/runner.py`: el artefacto JSON ya lleva `code_commit`,
  `protocol_sha256`, `corpus_version`, `snapshot_sha256`, `feature_set_version`,
  `seeds`, `split_manifest_sha256`, `per_user` con `heldout_rank` y métricas por
  K, `simulation: true` y `limitation`. La Fase 3 añade campos (identidad de
  entorno D-20, top-N por usuario D-18, tiempos D-08, `status` D-21) sin cambiar
  la forma base.
- `apps/api/recommendations/content/features.py` + `models.py`
  (`WorkFeatureVector`): cache de vectores de features idempotente con
  `feature_set_version` en el DTO — reutilizable tal cual para la distancia
  coseno de diversidad.
- `apps/api/evaluation/{synthetic,archetypes}.py` + `generate_synthetic_users`:
  generación por arquetipo/semilla ya existe; la Fase 3 la **extiende de forma
  aditiva** para generar una población nueva de ≥ 400 usuarios con la composición
  de cohortes de D-12, sin cambiar cómo se generó la población de 200 de la
  Fase 2.
- `accounts/` (`bootstrap_demo_accounts`, `DemoAccountIdentity` con marcador
  `synthetic-eval-user`): patrón anti-contaminación (cálculo restringido a
  cuentas demo) reutilizado por la señal de novedad.

### Established Patterns
- **Fail-closed antes de puntuar**: `protocol.py` valida todo el contrato y
  lanza `ProtocolError` antes de que ningún algoritmo corra. Las extensiones de
  la Fase 3 (`metrics` ampliado, `robustness`, `user_split` grande, `status`)
  mantienen ese estilo.
- **Candidate set único y compartido**: `candidates.build()` es el único punto de
  verdad; el runner hace `assert` de que cada algoritmo ve el mismo conjunto.
- **`algorithm_id` legible y versionado** grabado en los artefactos y en las
  tablas del TFG: renombrar rompe la cadena de evidencia. Cualquier variante
  nueva (señal negativa) sigue el patrón `VariantSpec`.
- **Congelación por hash**: `protocol.frozen_hash()` sobre el JSON canónico;
  cualquier cambio semántico mueve el hash. La Fase 3 produce un hash nuevo bajo
  `protocol_version: 2`; el hash de v1 permanece citado por la comparación 02-13.
- **Marcador de test consumido**: `record_test_run` / `_check_not_consumed` — un
  `protocol_version` nuevo limpia el marcador; el test se corre una sola vez por
  versión.
- **Métricas explícitas** (STACK): implementadas a mano y verificadas contra
  valores conocidos; `scipy` se admite solo para lo estadístico (D-11).

### Integration Points
- `docs/methodology/protocol.json` + `evaluation-protocol.md` + `protocol.py`:
  la Fase 3 escribe `protocol_version: 2` (D-13) — entregable propio, aditivo
  sobre v1 (que no se toca). Es la primera ola natural de la fase.
- `apps/api/evaluation/runner.py` + `run_evaluation.py`: nuevos campos de
  artefacto, multi-semilla (`robustness`), tiempos/recursos, `status`,
  persistencia top-N, identidad de entorno.
- Nuevo módulo de métricas beyond-accuracy en `apps/api/evaluation/` (cobertura,
  diversidad coseno, novedad) + tests contra fixtures.
- Nuevo módulo estadístico en `apps/api/evaluation/` (bootstrap, IC, Friedman,
  Wilcoxon, Holm) apoyado en `scipy.stats`.
- Nuevo comando de **recálculo** que lee solo artefactos + `MANIFEST` y regenera
  agregados, cohortes, IC, tests y el informe, rechazando artefactos no
  `complete`.
- Nuevo comando/secuencia de **reproducción desde instalación limpia** (QUAL-02)
  + documento de verificación en español.
- `generate_synthetic_users`: parametrización para ≥ 400 usuarios, composición de
  cohortes, `OwnedCopy`, filtro `rating_count ≥ 10`, excepciones sembradas,
  etiqueta de cohorte en el manifiesto.
- Posible ADR nuevo para `scipy`/`numpy` (encabezados en español,
  `check-evidence.ps1`) y enmienda al agente-ledger si algún doc con SHA pineado
  cambia.
- `thesis/` (memoria LaTeX): destino del informe con tablas (D-22); el autor
  regenera el zip de Overleaf tras planificar y entregar la fase.

</code_context>

<specifics>
## Specific Ideas

- El autor insiste en que **las cuentas sintéticas mejoren**: 5-10 juegos de
  base, notas propias variadas, unas con copias registradas y otras sin ninguna,
  y que los juegos de sus bibliotecas tengan **al menos 10 valoraciones totales**
  — con **algún usuario suelto, elegido al azar, con un juego sin valoraciones**
  para forzar ese camino.
- El autor quiere **≥ 400 usuarios sintéticos** en total, con **10 sin juegos**,
  **100 con 1-4 juegos** y **50 con más de 10**.
- El autor razona sobre la señal de rating en el algoritmo de contenido: una
  **nota propia baja debería bajar puntos de ese género**, salvo que sea el único
  juego del género (entonces "es que el juego es malo", no que el género no
  guste) → posible variante nueva.
- El autor distingue con claridad la **métrica de novedad de evaluación** (interna,
  reproducible, para las tablas del TFG) del **estante de "novedades y
  tendencias" de producto** (datos externos en vivo, Fase 6): no quiere una
  novedad "de mercado" fabricada en la Fase 3.
- El autor quiere el enfoque de **laboratorio "bien marcado"**: comparar
  variantes con nombre bajo un protocolo explícito, "es un entorno de estudio".
- Todas las decisiones de la fase (métricas, algoritmos, explicaciones,
  interpretación) se **escriben en el TFG después de planificar y entregar la
  fase**, regenerando entonces el zip de Overleaf. No se pre-escriben capítulos
  de trabajo no construido.

</specifics>

<deferred>
## Deferred Ideas

- **Estante "Tendencia / Novedades reales"** a partir de datos externos de
  visitas/popularidad (endpoint *Popularity* de IGDB, picos de jugadores de
  Steam) → **Fase 6**. Ya diferido en `02-CONTEXT.md` D-24 y su sección
  *Deferred Ideas*. Es una función de producto en vivo, distinta de la métrica
  de novedad de evaluación; la Fase 6 no toca `protocol.json` ni el arnés.
- **Pulido de la página `/recomendaciones` para el usuario sin juegos** (mensaje
  "aún no tienes juegos" + CTA "descubrir juegos" al catálogo). El estado
  `insufficient_history` ya existe desde la Fase 01.1; el pulido de esa página
  cae en la **Fase 5** (Complete Collection Workflows). "Novedades" en el
  catálogo es Fase 2 D-24; "Tendencias", Fase 6.
- **Panel de investigación interactivo y accesible** con gráficas y exportación
  de figuras/datos para el TFG → **Fase 7** (EVAL-13, EVAL-14, QUAL-04). La
  Fase 3 solo genera el informe con tablas.
- **Serendipia, `APLT`/`ARP` y otras métricas beyond-accuracy adicionales** — no
  entran (D-04); quedan como posible ampliación futura si el capítulo de
  evaluación lo pidiera.
- **Escenarios de split alternativos al leave-one-out** (leave-N-out, split
  temporal) para explotar de verdad el multi-positivo de la población
  enriquecida — no se abre en la Fase 3 (el split leave-one-out sigue congelado
  en v1 y v2); posible línea para la Fase 4 o trabajo futuro.

</deferred>

---

*Phase: 3-Explainable Content Recommenders and Baseline Comparison*
*Context gathered: 2026-09-07*
