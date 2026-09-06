# Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Convertir el catálogo real (≈312k obras IGDB importadas en la Fase 01.1) en un
**corpus gobernado, citable y versionado** con **ratings externos** (preferentemente
de usuarios), arreglar la **búsqueda tolerante** y añadir **filtros multi-selección**
sobre él, dar un **pase de UI de producto** a catálogo / filtros / ficha /
recomendaciones, **congelar el protocolo de evaluación** consciente de la simulación
(usuarios sintéticos, splits, métricas, presupuesto de tuning, aislamiento del test),
y entregar el **primer recomendador basado en contenido** construido como un
**laboratorio paramétrico** de variantes con nombre, evaluado bajo ese protocolo
frente a los baselines aleatorio y de popularidad.

Fuera de esta fase: el conjunto completo de métricas más-allá-del-acierto, el
desglose por cohorte y los tests estadísticos (Fase 3); recomendadores colaborativos
e híbridos (Fase 4); flujos completos de colección y portabilidad (Fase 5);
descubrimiento público y enriquecimiento en vivo con degradación resiliente (Fase 6);
panel de investigación, hardening y congelación final de evidencia (Fase 7).

</domain>

<decisions>
## Implementation Decisions

### A — Gobernanza del corpus

- **D-01:** Allowlist de plataformas **curada** (≈30-40 plataformas mainstream). El
  research/planner propone la lista concreta y el autor la revisa antes de aplicarla.
  Lista tentativa de partida: PC (Windows / Mac / Linux); PlayStation 1-5 + PSP + Vita;
  Xbox (original / 360 / One / Series X\|S); Nintendo (NES, SNES, N64, GameCube, Wii,
  Wii U, Switch, Game Boy, GBC, GBA, DS, 3DS); Sega (Master System, Mega Drive/Genesis,
  Game Gear, Saturn, Dreamcast); Atari (2600, 5200, 7800, Lynx, Jaguar); iOS; Android;
  navegador web. Una obra "tiene plataforma válida" si posee ≥1 `GameRelease` en una
  plataforma de la allowlist.
- **D-02:** "Steam debería aparecer" se resuelve como **PC / Windows**: en IGDB no
  existe una plataforma "Steam" (es una tienda). No se añade filtro por tienda en esta
  fase. Los chips / enlaces de tienda quedan como idea diferida.
- **D-03:** Una obra queda **fuera del corpus gobernado** si se cumple cualquiera de:
  nombre vacío / con menos de 2 caracteres alfanuméricos / compuesto solo de símbolos
  o puntuación; O sin ninguna release en plataforma de la allowlist (D-01); O
  `is_dlc == True`; O sin ningún `Genre` asignado; O sin `first_release_date`. Las
  obras **sin rating** SÍ se conservan (la política de rating es aparte, ver D-07).
- **D-04:** **Marca reversible, no borrado.** Se añade `GameWork.in_corpus`
  (`BooleanField`, migración aditiva con backfill). El corpus gobernado es el
  subconjunto `in_corpus == True`. El checksum inmutable, el diccionario de datos y el
  informe de calidad/missing-fields (DATA-03) se calculan sobre esa vista. Se
  conservan las ≈312k filas para fases posteriores (CAT-05, descubrimiento). Sin tope
  de tamaño: se reporta el tamaño resultante. — **Reversibility:** reversible — es una
  migración aditiva de un campo booleano; recomputar `in_corpus` es re-ejecutar el
  comando de gobernanza.
- **D-04b:** El corpus gobernado lleva una **versión** (`corpus_version`, string o
  entero monotónico) a la que se anclan los snapshots de rating (D-08) y toda la
  evidencia de experimentos. Regenerar el corpus con reglas distintas produce una
  `corpus_version` nueva; los snapshots viejos no se tocan.

### B — Ratings externos e inmutabilidad

- **D-05:** Fuente primaria = **IGDB**, importado correctamente (hoy el importador no
  puebla ningún rating: causa a investigar). **Preferencia explícita del autor por
  ratings de usuarios sobre ratings de crítica.** Usar el campo de valoración de
  usuarios de IGDB (`rating` / `rating_count`), no `aggregated_rating` (crítica);
  `total_rating` solo si el research confirma que es la señal de usuario más completa y
  documenta su composición. Si la cobertura de rating de usuario sobre el corpus
  gobernado queda baja, añadir **RAWG** como segunda fuente para los juegos de la
  allowlist (su `rating` de usuarios; `metacritic`, que es de crítica, solo como
  último recurso), con su **propio ADR** de licencia / atribución / cuotas / estabilidad
  / coste (patrón de ADR-006). — **Reversibility:** costly — añadir RAWG implica una
  segunda cadena de procedencia citada en la tesis y un ADR; quitarla después obliga a
  re-narrar la sección de datos.
- **D-06:** **Sin suelo de cobertura duro.** Se mide el porcentaje de obras del corpus
  gobernado con rating de usuario y se documenta en el informe de calidad de datos
  (DATA-03). Las reglas estrictas de D-03 ya elevan la cobertura esperada.
- **D-07:** Juego **sin rating** → se muestra "sin valoración" en catálogo y ficha;
  queda **excluido** del sort por rating y del filtro `min_rating`. El recomendador,
  cuando necesita el rating agregado de un juego sin dato, usa la **mediana declarada
  de su(s) género(s)** como señal explícita (nunca un valor imputado silencioso y
  nunca mostrado como si fuera real).
- **D-08:** **Inmutabilidad para experimentos.** Nueva tabla
  `CorpusRatingSnapshot(work, rating, rating_count, source, retrieved_at, corpus_version)`.
  El protocolo de evaluación y el recomendador leen **siempre** del snapshot de una
  `corpus_version` dada. Un re-import posterior actualiza el valor vivo del catálogo
  (`GameWork.total_rating` o un `display_rating` derivado) **sin tocar snapshots**.
  Cumple DATA-06. — **Reversibility:** costly — una vez que una comparación citada en
  la tesis referencia una `corpus_version`, el esquema y la semántica del snapshot son
  un contrato de evidencia; cambiarlo invalida resultados registrados.
- **D-09:** **Ratings locales acumulativos.** El rating "general" que ve el usuario en
  vivo mezcla el rating externo con las valoraciones de los propios usuarios de
  SavePoint (`LibraryEntry.rating_half_steps`) según se acumulan. La composición exacta
  (peso relativo externo vs local, si cuentan solo usuarios auto-registrados o también
  cuentas demo, cómo se refleja en el snapshot) la fija el research/planner y se
  documenta. Para experimentos manda el snapshot de la `corpus_version`, congelado con
  la regla vigente en el momento del freeze. **Riesgo a vigilar:** separar el rating de
  producto (vivo, mezclado) del rating de investigación (snapshot), igual que
  `rank_popularity_v1` ya restringe su cálculo a cuentas demo para no contaminarse.

### C — Primer recomendador: laboratorio de contenido

- **D-10:** Modelo **basado en contenido completo** ya en la Fase 2, construido como
  **laboratorio paramétrico**: el **modo de combinación** (`weighted_sum`,
  `multiplicative`, `two_stage`) y el **conjunto de features** son parámetros. Cada
  configuración concreta es un **algoritmo con nombre y versión** (`algorithm_id`
  legible, patrón de `rank_genre_taste_v1`). El contrato de evaluación de la Fase 2
  **compara las variantes entre sí y contra los baselines** aleatorio (REC-01) y
  popularidad (REC-02). — **Reversibility:** costly — los valores de `algorithm_id` se
  graban en los artefactos de evaluación y en las tablas de la tesis; renombrarlos
  después rompe la cadena de evidencia.
- **D-11:** Vector de features del contenido: **géneros + plataformas + franquicia/saga
  + desarrollador + señal de rating**. El planner confirma qué campos ofrece IGDB de
  forma fiable sobre el corpus gobernado; se empieza por géneros + rating (garantizados)
  y se añaden plataforma / franquicia / desarrollador según cobertura.
- **D-12:** Perfil de usuario = media ponderada de los vectores de los juegos de su
  biblioteca, ponderada por `_entry_weight` (estado + `rating_half_steps`, ya
  implementado en `genre_heuristic.py`). Similitud usuario ↔ candidato por **coseno**
  (0..1).
- **D-13:** Término de rating del candidato = **perfil de rating por género** (media,
  tomada del snapshot D-08, del rating de usuario de los juegos gobernados de cada
  género) combinado con el **rating propio del candidato** cuando exista, mezclados
  según confianza (`rating_count`). Normalizado a 0..1.
- **D-14:** Score final según el modo de combinación (todas se comparan):
  - `weighted_sum` = `w1·similitud + w2·rating_esperado (+ w3·rating_propio_si_existe)`,
    con `w1/w2/w3` como **parámetros congelados en el protocolo**, ajustables dentro del
    presupuesto de tuning (D-21).
  - `multiplicative` = `similitud · rating_esperado`.
  - `two_stage` = bandas de similitud, desempate por rating dentro de cada banda.
- **D-15:** **DLC de juegos que ya tienes** → estante propio **"Para tus juegos"**: si
  el usuario posee el juego base, sus DLC (vía `is_dlc` + `RelatedContent`) aparecen en
  una sección aparte y claramente etiquetada. Los DLC siguen **fuera** del catálogo
  gobernado normal (D-03) pero quedan consultables para este estante. Además "posee el
  juego base" es una **feature** que sube esos candidatos en el modelo.
- **D-16:** Explicación = **frase corta determinista + detalle desplegable** (tabla de
  contribución por género + término de rating), **sin prosa generada**, derivada solo
  de features persistidas, y **marcando qué variante/algoritmo la produjo** ("bien
  marcado el tipo de recomendación").

### D — Protocolo de evaluación y usuarios sintéticos

- **D-17:** Relevancia (acierto) para un usuario sintético en el test =
  `current_status == "completed"` **O** `rating_half_steps >= 7` (≥ 3.5/5).
  — **Reversibility:** one-way — parte del protocolo congelado EVAL-03; redefinirla
  tras una comparación citada en la tesis invalida esa comparación.
- **D-18:** Split = **leave-one-out por usuario**: se retira un juego que le gustó
  (semilla fija), el modelo debe recuperarlo en su top-K sobre el corpus gobernado
  menos su biblioteca; el ítem retirado se reincorpora al conjunto de candidatos.
  — **Reversibility:** one-way — parte de EVAL-03.
- **D-19:** K del top-N: report a **5, 10, 20**; métrica titular **`nDCG@10`**.
  — **Reversibility:** one-way — parte de EVAL-03.
- **D-20:** Usuarios sintéticos = **≈8 arquetipos documentados × ≈25 usuarios ≈ 200**,
  generados variando parámetros (nº de géneros preferidos, tamaño de biblioteca,
  generosidad al puntuar, ...) con semillas independientes; **regenerables** con un
  informe de validación (EVAL-09). **Cohorte cold-start explícita** de usuarios con 1-3
  juegos. Los arquetipos concretos los propone el research a partir de literatura de
  simulación de usuarios de RecSys y los revisa el autor en el PLAN.
- **D-21:** Tuning = split **train / validación / test** disjunto entre los ≈200
  usuarios. Rejilla de **≤ 24 combinaciones** de hiperparámetros **declarada antes de
  correr**; se bloquea la mejor por el titular (`nDCG@10`) medido en **validación**; el
  **test se corre una sola vez**. Cumple EVAL-02 y EVAL-03. — **Reversibility:**
  one-way — el presupuesto de tuning es parte de EVAL-03.
- **D-22:** Lista de **métricas congelada** en el protocolo:
  - Ranking / acierto: Precision@K, Recall@K, nDCG@K, MAP.
  - Más allá del acierto: cobertura de catálogo, novedad, diversidad intra-lista.
  La Fase 2 **calcula al menos las de ranking** para la primera comparación; la Fase 3
  calcula el conjunto completo + desglose por cohorte + tests estadísticos
  (EVAL-04/05/07/08). — **Reversibility:** one-way — la lista de métricas es parte de
  EVAL-03; ampliarla está previsto, quitar o cambiar una métrica no.
- **D-23:** Baselines de comparación = **aleatorio** (REC-01, nuevo en esta fase) +
  **popularidad** (REC-02, ya existe `rank_popularity_v1`). Aislamiento del test =
  EVAL-02.

### E — Home y pase de UI

- **D-24:** En la home entra un estante **"Novedades"** derivado de `first_release_date`
  (juegos del corpus gobernado lanzados en los últimos N meses; N a fijar por el
  planner, orden por fecha descendente con desempate `canonical_slug`). No requiere
  datos nuevos. La señal de **tendencia real** (popularidad externa, picos de
  jugadores) queda **fuera de esta fase** → Fase 6. El baseline de popularidad
  existente (`rank_popularity_v1`) se mantiene en la home como hasta ahora.

### Claude's Discretion

El research/planner decide (y el autor revisa en el PLAN):

- **Búsqueda tolerante sobre el corpus gobernado:** hay que hacer **backfill de
  `GameAlias`** para las obras IGDB (hoy solo las puebla el importador de Wikidata, por
  eso `catalogue/search.py` no encuentra nada) y añadir la creación de alias al
  importador IGDB. Arquitectura del backfill (comando de management, en el import,
  ambos), normalización, y si el alias primario es `normalize_title(original_title)`
  más `title_en` y alias alternativos.
- **Forma de los parámetros de URL de los filtros multi-selección.** Semántica
  propuesta: varios géneros = AND ("contiene todos"); varias plataformas = OR
  ("disponible en alguna"). Confirmar con el autor si surge duda en el PLAN.
- **Alcance concreto del pase de UI:** densidad del catálogo, panel de filtros como
  desplegables / chips reales, y la ficha de juego que el autor llamó "escasa" (añadir
  el `summary` de IGDB, secciones, enlaces). Es pulido dirigido a las referencias de
  producto, no un rediseño.
- **Lista concreta de plataformas de la allowlist** (D-01), **arquetipos concretos de
  usuario sintético** (D-20), y el **conjunto exacto de features fiables** (D-11).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap y requisitos
- `.planning/ROADMAP.md` §"Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender" — goal, requisitos, 6 criterios de éxito.
- `.planning/REQUIREMENTS.md` — DATA-03, DATA-05, DATA-06, DATA-07, DATA-08, EVAL-01, EVAL-02, EVAL-03, EVAL-09, EVAL-10, REC-01, REC-03, REC-06, REC-07, REC-08, REC-09, DOC-02, DOC-04, AGENT-04 (y la nota de refinamiento de CAT-02 / QUAL-05 / AUTH-02).
- `.planning/PROJECT.md` — Core Value, Constraints (reproducibilidad académica, legalidad/procedencia, doble entrega), convención de idioma.

### Datos y fuente
- `docs/adr/ADR-006-igdb-source.md` — decisión de fuente IGDB y términos de licencia/atribución (base y patrón para el ADR de ratings externos).
- `docs/verification/igdb-api-probe.md` §5 — términos IGDB / Twitch verbatim (relevante para almacenamiento y redistribución de valores de rating).
- `docs/verification/igdb-catalogue-freeze.md` — evidencia de congelación del import IGDB (patrón checksum + agregados + muestreo a extender para el corpus gobernado, DATA-01/DATA-02 equivalente).

### Recomendación y evaluación
- `docs/adr/ADR-007-genre-taste-heuristic.md` — patrón del heurístico de género vigente (`rank_genre_taste_v1`): `algorithm_id`, `input_snapshot_sha256`, estado `insufficient_history` distinto (D-09 de 01.1).
- `apps/api/recommendations/genre_heuristic.py` — `_entry_weight`, `_fingerprint`, `_insufficient_history`, `rank_genre_taste_v1`; base del perfil de usuario (D-12).
- `apps/api/library/popularity.py` — `rank_popularity_v1` (baseline REC-02), ya restringido a cuentas demo vía `demo_anchor` / `demo_identity` (patrón anti-contaminación para D-09).

### Contexto de fase previa
- `.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-CONTEXT.md` — D-05 (IGDB elegido), D-06/D-07 (placeholder de portada de primera parte), patrón de freeze no-enumerativo, AUTH-02 movido a territorio de cuentas simuladas.
- `.planning/phases/01.1-real-scale-catalogue-and-product-experience/deferred-items.md` — ítems de pulido de UI diferidos (D-01.1-10-a nav <430px, ficha escasa) relevantes para el pase de UI.

### Convenciones
- `CONVENTIONS.md` — idioma (docs de tesis y prosa nueva de `.planning/**` en español; código en inglés; tokens neutrales y citas legales se conservan).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `catalogue/models.py`: `GameWork` (ya tiene `total_rating`, `first_release_date`, `is_dlc`, índices), `Genre` (con `igdb_id`), `Platform`, `GameRelease`, `Edition`, `GameAlias`, `RelatedContent` (para DLC ↔ juego base), `SourceRecord`, `IgdbImportRun` (import reanudable, `pass_cursor`, trigger anti-retroceso).
- `recommendations/genre_heuristic.py`: `rank_genre_taste_v1` con `_entry_weight(status, rating_half_steps)`, `_fingerprint`, `_insufficient_history`, `_clamp_limit`; DTO con `algorithm_id`.
- `library/popularity.py`: `rank_popularity_v1(cutoff)` — baseline de popularidad, restricción a cuentas demo ya resuelta.
- `library/models.py`: `LibraryEntry.rating_half_steps` (entero 1-10, constraint de rango), `BacklogStatus`, `OwnedCopy`, `RelatedContent`.
- `accounts/`: `bootstrap_demo_accounts` + `DemoAccountIdentity` / `DemoAccountAnchor` — base para generar los usuarios sintéticos de escenario con historiales reproducibles por semilla.
- `catalogue/search.py`: `parse_catalogue_query` (allowlist de filtros `platform`/`genre`/`year_from`/`year_to`/`min_rating` + set de sort con desempate `canonical_slug`, 400 acotado), `search_games`, `_facets` sin N+1.

### Established Patterns
- **Búsqueda = 100% por `GameAlias.normalized_value`** (`_ordered_matching_work_ids`): exacto → prefijo → trigram. El importador IGDB **no crea `GameAlias`** → causa raíz del bug "búsqueda no encuentra nada" (solo ~239 alias sobre 312k obras). El backfill de alias es prerequisito de la búsqueda utilizable.
- DTO de recomendación: `algorithm_id` + `input_snapshot_sha256` + estado `insufficient_history` con forma distinta (ADR-007). El laboratorio de contenido (D-10) sigue el mismo patrón por variante.
- Congelación de datos: checksum + estadísticas agregadas + revisión muestreada (no enumeración fila a fila — no escala a cientos de miles).
- D-11 de la Fase 1: DLC/expansiones nunca aparecen como resultados independientes de búsqueda/listado (`is_dlc=False` en `_base_works`). El estante "Para tus juegos" (D-15) es la excepción controlada.
- Filtros: valor de faceta desconocido → se ignora, no fuerza resultado vacío.

### Integration Points
- Migración aditiva: `GameWork.in_corpus` (bool) + backfill; nueva tabla `CorpusRatingSnapshot`.
- `catalogue/management/commands/import_igdb_catalogue.py`: poblar rating de usuario + **crear `GameAlias`** por obra.
- Nuevo comando de gobernanza del corpus (aplica D-01/D-03, calcula `in_corpus`, emite checksum + diccionario de datos + informe de calidad, fija `corpus_version`).
- Nuevo módulo de recomendador de contenido en `apps/api/recommendations/` (vectorización, similitud coseno, modos de combinación, explicación).
- Nuevo comando + harness: generación de usuarios sintéticos por arquetipo/semilla; ejecución del protocolo (splits, tuning en validación, test único, métricas de ranking).
- `catalogue/search.py` + `FilterBar` (frontend): filtros multi-selección (AND géneros / OR plataformas).
- `MyLibraryView` / detalle de juego: estante "Para tus juegos" (DLC de juegos poseídos).
- Nuevo ADR de ratings externos (si entra RAWG) siguiendo ADR-006; extensión de la evidencia de congelación para el corpus gobernado (DATA-01/02/03).

</code_context>

<specifics>
## Specific Ideas

- Referencias de producto del autor (heredadas de 01.1): **Goodreads, OpenCritic,
  Letterboxd** para densidad, tipografía y tratamiento de imagen.
- Ratings **preferentemente de usuarios**, no de crítica.
- Enfoque de **laboratorio**: comparar variantes con nombre bajo un protocolo "bien
  marcado", porque "es un entorno de estudio".
- El autor quiere que **todas las decisiones de esta fase** (algoritmos,
  explicaciones, toma de decisiones) se escriban en el **TFG** después de planificar y
  entregar la fase, **regenerando el zip de Overleaf** entonces. No se pre-escriben
  capítulos de trabajo no construido.
- El campo `GameWork.total_rating` "no mostraba nada" en la revisión del autor: el
  importador IGDB actual no lo puebla — a investigar y arreglar.

</specifics>

<deferred>
## Deferred Ideas

- **Filtro / chips por tienda (Steam / GOG / Epic)** y enlaces de tienda en la ficha —
  Fase 6 (descubrimiento público) o posterior.
- **Estante "Tendencia" / juegos de moda en la home** a partir de una señal externa
  de popularidad (endpoint *Popularity* de IGDB: visitas, "quiero jugar", "jugando
  ahora"; `hypes`; o Steam / picos de jugadores). Es una integración de datos nueva
  con su propia procedencia — Fase 6. La parte de "Novedades" (por `first_release_date`)
  sí entra en esta fase (D-24).
- **Segunda o más fuentes de ratings más allá de IGDB/RAWG** (p.ej. OpenCritic
  dedicado) — solo si la cobertura lo exige; en otro caso, futura.
- **Modelo de features CAT-05 completo** (modos de juego, tags, publishers como
  entidades) — Fase 6.
- **Recomendador colaborativo / híbrido** — Fase 4.
- **Conjunto completo de métricas más-allá-del-acierto + cohortes + tests estadísticos
  + recálculo desde artefactos inmutables** — Fase 3.
- **Cobertura total de portadas** across el corpus gobernado — heredado de 01.1 D-06,
  puede seguir siendo incremental.

</deferred>

---

*Phase: 2-Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender*
*Context gathered: 2026-09-06*
