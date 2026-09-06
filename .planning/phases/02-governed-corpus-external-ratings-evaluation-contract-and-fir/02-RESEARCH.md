# Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender - Research

**Researched:** 2026-09-06
**Domain:** Corpus governance over a 312k-work IGDB import; external user-ratings ingestion with experiment isolation; tolerant search + multi-select filters; a parameterised content-based recommender ("laboratory"); a frozen simulation-aware offline evaluation protocol with synthetic users.
**Confidence:** MEDIUM-HIGH. In-repo findings (schema, importer, search, heuristic, serializers) are `[VERIFIED]` from files read this session. IGDB rating-field semantics are `[VERIFIED]` against IGDB's own generated type docs. IGDB rating *coverage* over the corpus and modern platform IDs are `[ASSUMED]` and must be measured/probed in Wave 0. RAWG terms are `[CITED]` from rawg.io.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Copied verbatim from `02-CONTEXT.md` `## Implementation Decisions`. The planner MUST honour every one of these and must NOT research or plan alternatives to them.

**A — Corpus governance**

- **D-01:** Allowlist de plataformas **curada** (≈30-40 plataformas mainstream). El research/planner propone la lista concreta y el autor la revisa antes de aplicarla. Lista tentativa de partida: PC (Windows / Mac / Linux); PlayStation 1-5 + PSP + Vita; Xbox (original / 360 / One / Series X\|S); Nintendo (NES, SNES, N64, GameCube, Wii, Wii U, Switch, Game Boy, GBC, GBA, DS, 3DS); Sega (Master System, Mega Drive/Genesis, Game Gear, Saturn, Dreamcast); Atari (2600, 5200, 7800, Lynx, Jaguar); iOS; Android; navegador web. Una obra "tiene plataforma válida" si posee ≥1 `GameRelease` en una plataforma de la allowlist.
- **D-02:** "Steam debería aparecer" se resuelve como **PC / Windows**: en IGDB no existe una plataforma "Steam" (es una tienda). No se añade filtro por tienda en esta fase. Los chips / enlaces de tienda quedan como idea diferida.
- **D-03:** Una obra queda **fuera del corpus gobernado** si se cumple cualquiera de: nombre vacío / con menos de 2 caracteres alfanuméricos / compuesto solo de símbolos o puntuación; O sin ninguna release en plataforma de la allowlist (D-01); O `is_dlc == True`; O sin ningún `Genre` asignado; O sin `first_release_date`. Las obras **sin rating** SÍ se conservan (la política de rating es aparte, ver D-07).
- **D-04:** **Marca reversible, no borrado.** Se añade `GameWork.in_corpus` (`BooleanField`, migración aditiva con backfill). El corpus gobernado es el subconjunto `in_corpus == True`. El checksum inmutable, el diccionario de datos y el informe de calidad/missing-fields (DATA-03) se calculan sobre esa vista. Se conservan las ≈312k filas para fases posteriores (CAT-05, descubrimiento). Sin tope de tamaño: se reporta el tamaño resultante. — Reversible: migración aditiva de un booleano; recomputar `in_corpus` es re-ejecutar el comando de gobernanza.
- **D-04b:** El corpus gobernado lleva una **versión** (`corpus_version`, string o entero monotónico) a la que se anclan los snapshots de rating (D-08) y toda la evidencia de experimentos. Regenerar el corpus con reglas distintas produce una `corpus_version` nueva; los snapshots viejos no se tocan.

**B — Ratings externos e inmutabilidad**

- **D-05:** Fuente primaria = **IGDB**, importado correctamente (hoy el importador no puebla ningún rating: causa a investigar). **Preferencia explícita del autor por ratings de usuarios sobre ratings de crítica.** Usar el campo de valoración de usuarios de IGDB (`rating` / `rating_count`), no `aggregated_rating` (crítica); `total_rating` solo si el research confirma que es la señal de usuario más completa y documenta su composición. Si la cobertura de rating de usuario sobre el corpus gobernado queda baja, añadir **RAWG** como segunda fuente para los juegos de la allowlist (su `rating` de usuarios; `metacritic`, que es de crítica, solo como último recurso), con su **propio ADR** de licencia / atribución / cuotas / estabilidad / coste (patrón de ADR-006). — Costly: añadir RAWG implica una segunda cadena de procedencia citada en la tesis y un ADR.
- **D-06:** **Sin suelo de cobertura duro.** Se mide el porcentaje de obras del corpus gobernado con rating de usuario y se documenta en el informe de calidad de datos (DATA-03). Las reglas estrictas de D-03 ya elevan la cobertura esperada.
- **D-07:** Juego **sin rating** → se muestra "sin valoración" en catálogo y ficha; queda **excluido** del sort por rating y del filtro `min_rating`. El recomendador, cuando necesita el rating agregado de un juego sin dato, usa la **mediana declarada de su(s) género(s)** como señal explícita (nunca un valor imputado silencioso y nunca mostrado como si fuera real).
- **D-08:** **Inmutabilidad para experimentos.** Nueva tabla `CorpusRatingSnapshot(work, rating, rating_count, source, retrieved_at, corpus_version)`. El protocolo de evaluación y el recomendador leen **siempre** del snapshot de una `corpus_version` dada. Un re-import posterior actualiza el valor vivo del catálogo (`GameWork.total_rating` o un `display_rating` derivado) **sin tocar snapshots**. Cumple DATA-06. — Costly: una vez que una comparación citada en la tesis referencia una `corpus_version`, el esquema y la semántica del snapshot son un contrato de evidencia.
- **D-09:** **Ratings locales acumulativos.** El rating "general" que ve el usuario en vivo mezcla el rating externo con las valoraciones de los propios usuarios de SavePoint (`LibraryEntry.rating_half_steps`) según se acumulan. La composición exacta (peso relativo externo vs local, si cuentan solo usuarios auto-registrados o también cuentas demo, cómo se refleja en el snapshot) la fija el research/planner y se documenta. Para experimentos manda el snapshot de la `corpus_version`, congelado con la regla vigente en el momento del freeze. **Riesgo a vigilar:** separar el rating de producto (vivo, mezclado) del rating de investigación (snapshot), igual que `rank_popularity_v1` ya restringe su cálculo a cuentas demo.

**C — Primer recomendador: laboratorio de contenido**

- **D-10:** Modelo **basado en contenido completo** ya en la Fase 2, construido como **laboratorio paramétrico**: el **modo de combinación** (`weighted_sum`, `multiplicative`, `two_stage`) y el **conjunto de features** son parámetros. Cada configuración concreta es un **algoritmo con nombre y versión** (`algorithm_id` legible, patrón de `rank_genre_taste_v1`). El contrato de evaluación de la Fase 2 **compara las variantes entre sí y contra los baselines** aleatorio (REC-01) y popularidad (REC-02). — Costly: los `algorithm_id` se graban en artefactos de evaluación y tablas de la tesis.
- **D-11:** Vector de features del contenido: **géneros + plataformas + franquicia/saga + desarrollador + señal de rating**. El planner confirma qué campos ofrece IGDB de forma fiable sobre el corpus gobernado; se empieza por géneros + rating (garantizados) y se añaden plataforma / franquicia / desarrollador según cobertura.
- **D-12:** Perfil de usuario = media ponderada de los vectores de los juegos de su biblioteca, ponderada por `_entry_weight` (estado + `rating_half_steps`, ya implementado en `genre_heuristic.py`). Similitud usuario ↔ candidato por **coseno** (0..1).
- **D-13:** Término de rating del candidato = **perfil de rating por género** (media, tomada del snapshot D-08, del rating de usuario de los juegos gobernados de cada género) combinado con el **rating propio del candidato** cuando exista, mezclados según confianza (`rating_count`). Normalizado a 0..1.
- **D-14:** Score final según el modo de combinación (todas se comparan):
  - `weighted_sum` = `w1·similitud + w2·rating_esperado (+ w3·rating_propio_si_existe)`, con `w1/w2/w3` como **parámetros congelados en el protocolo**, ajustables dentro del presupuesto de tuning (D-21).
  - `multiplicative` = `similitud · rating_esperado`.
  - `two_stage` = bandas de similitud, desempate por rating dentro de cada banda.
- **D-15:** **DLC de juegos que ya tienes** → estante propio **"Para tus juegos"**: si el usuario posee el juego base, sus DLC (vía `is_dlc` + `RelatedContent`) aparecen en una sección aparte y claramente etiquetada. Los DLC siguen **fuera** del catálogo gobernado normal (D-03) pero quedan consultables para este estante. Además "posee el juego base" es una **feature** que sube esos candidatos en el modelo.
- **D-16:** Explicación = **frase corta determinista + detalle desplegable** (tabla de contribución por género + término de rating), **sin prosa generada**, derivada solo de features persistidas, y **marcando qué variante/algoritmo la produjo**.

**D — Protocolo de evaluación y usuarios sintéticos**

- **D-17:** Relevancia (acierto) para un usuario sintético en el test = `current_status == "completed"` **O** `rating_half_steps >= 7` (≥ 3.5/5). — One-way: parte del protocolo congelado EVAL-03.
- **D-18:** Split = **leave-one-out por usuario**: se retira un juego que le gustó (semilla fija), el modelo debe recuperarlo en su top-K sobre el corpus gobernado menos su biblioteca; el ítem retirado se reincorpora al conjunto de candidatos. — One-way: parte de EVAL-03.
- **D-19:** K del top-N: report a **5, 10, 20**; métrica titular **`nDCG@10`**. — One-way.
- **D-20:** Usuarios sintéticos = **≈8 arquetipos documentados × ≈25 usuarios ≈ 200**, generados variando parámetros (nº de géneros preferidos, tamaño de biblioteca, generosidad al puntuar, ...) con semillas independientes; **regenerables** con un informe de validación (EVAL-09). **Cohorte cold-start explícita** de usuarios con 1-3 juegos. Los arquetipos concretos los propone el research a partir de literatura de simulación de usuarios de RecSys y los revisa el autor en el PLAN.
- **D-21:** Tuning = split **train / validación / test** disjunto entre los ≈200 usuarios. Rejilla de **≤ 24 combinaciones** de hiperparámetros **declarada antes de correr**; se bloquea la mejor por el titular (`nDCG@10`) medido en **validación**; el **test se corre una sola vez**. Cumple EVAL-02 y EVAL-03. — One-way.
- **D-22:** Lista de **métricas congelada**: Ranking/acierto: Precision@K, Recall@K, nDCG@K, MAP. Más allá del acierto: cobertura de catálogo, novedad, diversidad intra-lista. La Fase 2 **calcula al menos las de ranking**; la Fase 3 calcula el conjunto completo + cohortes + tests. — One-way: ampliar está previsto; quitar/cambiar una métrica no.
- **D-23:** Baselines = **aleatorio** (REC-01, nuevo) + **popularidad** (REC-02, `rank_popularity_v1`). Aislamiento del test = EVAL-02.

**E — Home y pase de UI**

- **D-24:** En la home entra un estante **"Novedades"** derivado de `first_release_date` (juegos del corpus gobernado lanzados en los últimos N meses; N a fijar por el planner — **UI-SPEC P5 lo fija en 6 meses, máx 20, orden `first_release_date` desc, desempate `canonical_slug`, se oculta el estante si 0**). No requiere datos nuevos. La señal de **tendencia real** queda fuera de esta fase → Fase 6. `rank_popularity_v1` se mantiene en la home.

### Claude's Discretion

The research/planner decides (author reviews in the PLAN):

- **Búsqueda tolerante sobre el corpus gobernado:** backfill de `GameAlias` para las obras IGDB (hoy solo las puebla el importador de Wikidata) y añadir creación de alias al importador IGDB. Arquitectura del backfill (comando de management, en el import, ambos), normalización, y si el alias primario es `normalize_title(original_title)` más `title_en` y alias alternativos. → **See "Pattern 4" below — recommendation: BOTH a one-off command now AND importer changes.**
- **Forma de los parámetros de URL de los filtros multi-selección.** Semántica propuesta: varios géneros = AND ("contiene todos"); varias plataformas = OR ("disponible en alguna"). → **UI-SPEC P1 already resolved this: repeated params `?genre=rpg&genre=strategy`, `getAll`, genres AND / platforms OR. See "Pattern 3".**
- **Alcance concreto del pase de UI:** densidad del catálogo, panel de filtros como desplegables / chips reales, y la ficha de juego "escasa" (añadir `summary` de IGDB, secciones, enlaces). Pulido dirigido a las referencias de producto, no rediseño. → **UI-SPEC Screen Contracts 1-4 are the authoritative surface list. `summary` is NOT currently imported — see "Runtime State Inventory".**
- **Lista concreta de plataformas de la allowlist (D-01), arquetipos concretos de usuario sintético (D-20), y el conjunto exacto de features fiables (D-11).** → **Proposed below in Patterns 1, 6, 5. Author confirms in PLAN.**

### Deferred Ideas (OUT OF SCOPE — do not plan)

- Filtro / chips por tienda (Steam / GOG / Epic) y enlaces de tienda en la ficha — Fase 6+.
- Estante "Tendencia" / juegos de moda a partir de señal externa de popularidad (endpoint *Popularity Primitives* de IGDB, `hypes`, picos de jugadores) — Fase 6. La parte "Novedades" (por `first_release_date`) SÍ entra (D-24).
- Segunda/más fuentes de rating más allá de IGDB/RAWG (p. ej. OpenCritic dedicado) — solo si la cobertura lo exige.
- Modelo de features CAT-05 completo (modos de juego, tags, publishers como entidades) — Fase 6.
- Recomendador colaborativo / híbrido — Fase 4.
- Conjunto completo de métricas más-allá-del-acierto + cohortes + tests estadísticos + recálculo desde artefactos inmutables — Fase 3 (EVAL-04/05/07/08/11/12).
- Cobertura total de portadas — heredado de 01.1 D-06, incremental.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-03 | Data dictionary + quality/missing-fields report for the fixed corpus. | Pattern 7 (corpus governance): extend the `igdb-catalogue-freeze.md` checksum+aggregates+sampled pattern with per-field null/coverage table over the `in_corpus=True` view, incl. rating coverage. |
| DATA-05 | Each enriched value retains source + retrieval date. | Pattern 2: `CorpusRatingSnapshot(source, retrieved_at, corpus_version)` per (work, corpus_version, source); importer already writes `SourceRecord.retrieved_at`. |
| DATA-06 | Mutable API data cannot retrospectively alter completed experiments. | Pattern 2: snapshot table is append-only; re-import writes live `GameWork` fields only; harness reads snapshot for a fixed `corpus_version`. |
| DATA-07 | Deterministic identifier reconciliation + conflict rules. | Pattern 2 (RAWG↔IGDB reconciliation on IGDB id / canonical_slug); IGDB is authoritative, RAWG fills gaps only, documented tie-break. |
| DATA-08 | Thesis evidence: dataset/API choices, limitations, redistribution rights. | ADR-006 pattern; new ratings ADR (IGDB rating fields + optional RAWG). Verbatim terms in `## State of the Art` / `## Sources`. |
| EVAL-01 | All algorithms compared with same users, candidates, exclusions, split manifests. | Pattern 6 harness: one frozen split manifest + candidate-set builder shared by random / popularity / every content variant. |
| EVAL-02 | Transformations fit training data only; test isolated from tuning. | Pattern 6: train/val/test disjoint user split (D-21); genre-median rating profile (D-13) computed from training users' governed works only; single test run. |
| EVAL-03 | Protocol fixes relevance, K, splits, metrics, tuning budget before comparison. | Pattern 6 + a checked-in frozen `evaluation-protocol.md` + `protocol.json` (relevance D-17, K D-19, LOO D-18, ≤24-grid D-21, metric list D-22, seeds). |
| EVAL-09 | Synthetic users from contrasting, parameterised, reproducible scenarios. | Pattern 5: ~8 archetypes × ~25, seeded `numpy`/`random` parameter draws, `generate_synthetic_users` command, validation report. |
| EVAL-10 | Conclusions distinguish synthetic simulation from real-user evidence. | DOC-04 deliverable; every artifact + DTO carries a `simulation: true` / `limitation` string (ADR-007 precedent). |
| REC-01 | Random recommendation baseline. | Pattern 6: `rank_random_v1(user, seed)` — seeded shuffle of governed candidates minus library, DTO mirrors `rank_popularity_v1`. |
| REC-03 | Content-based recommender. | Pattern 5: feature-vector + cosine + 3 combination modes as named variants. |
| REC-06 | Cold-start strategy for sparse-history users. | Pattern 5: explicit fallback to popular-genres view + `coldStartBadge`; never an empty list (UI-SPEC §4a). Threshold = <N genre-bearing entries; N proposed = 3 (matches D-20 cold-start cohort). |
| REC-07 | Exclude already-consumed games per configured rules. | Pattern 5: exclude every work with any `LibraryEntry` for the user (same as `rank_genre_taste_v1` `seen_ids`); rule is a protocol parameter. |
| REC-08 | Deterministic explanation grounded in model evidence. | Pattern 5: per-genre contribution table + rating term, from persisted features; no generated prose (D-16). |
| REC-09 | Published results retain model, feature, input-data versions. | Pattern 5 DTO: `algorithm_id` + `feature_set_version` + `corpus_version` + `snapshot_sha256` (extends ADR-007 DTO). |
| DOC-02 | Dataset, API, data-model, normalisation documented. | `docs/verification/` corpus-governance doc + updated `igdb-catalogue-freeze.md` + ratings ADR. |
| DOC-04 | Experimental protocol, metrics, results, threats to validity documented. | `docs/methodology/evaluation-protocol.md` (frozen) + threats section (synthetic-user external validity, LOO bias, single-critic-source bias). |
| AGENT-04 | Methodology controls against hallucination, bias, error, information exposure. | Deterministic explanations (no LLM) = anti-hallucination; synthetic-user validation report + genre-balanced archetypes = anti-bias; frozen seeds + immutable snapshots = anti-error; allowlist serializers + demo/synthetic-account restriction on live blended rating = anti-exposure. `docs/methodology/`. |

**Also refines (IDs owned elsewhere, extended here):** CAT-02 (multi-select genre+platform — Pattern 3), QUAL-05 (product-grade UI pass — UI-SPEC), AUTH-02 (simulated accounts gain seed-reproducible scenario histories — Pattern 5 persists synthetic users as `DemoAccountIdentity` rows).
</phase_requirements>

## Summary

This phase has five loosely-coupled tracks over the already-imported 312k-work IGDB catalogue. **Track 1 (governance):** an additive `GameWork.in_corpus` boolean + `corpus_version`, set by a new idempotent `govern_corpus` management command that applies the D-03 exclusion rules and the D-01 platform allowlist, then emits a checksum + data dictionary + quality/missing-fields report over the `in_corpus=True` view (extending the existing non-enumerative freeze pattern). **Track 2 (ratings):** the current importer already requests and maps IGDB `total_rating` — the "no ratings" symptom is a combination of (a) the importer requesting only the *blended* `total_rating` and never the user-specific `rating`/`rating_count` the author wants (D-05), and (b) genuine IGDB sparsity of any rating over the long tail of 312k primary works. The fix is to add `rating,rating_count,total_rating_count` (and `summary`, `alternative_names`, `franchises`, `involved_companies` for later tracks) to the Apicalypse field list, re-run the import (or a targeted enrichment pass), and snapshot user ratings into a new immutable `CorpusRatingSnapshot` table keyed by `corpus_version`. RAWG is a *conditional* second source: its terms are materially harsher than IGDB's (20k requests/month hard cap, mandatory backlink on every page, explicit no-redistribution), so it should be gated on measured IGDB coverage and scoped only to allowlist games, with its own ADR. **Track 3 (search + filters):** `catalogue/search.py` is 100% `GameAlias`-driven and the IGDB importer never creates aliases, so search finds ~a few hundred of 312k works — fix with a one-off `backfill_game_aliases` command *and* alias creation inside the importer's `_upsert`. Multi-select filters (UI-SPEC P1: repeated params, genres AND / platforms OR) are an additive change to `parse_catalogue_query` / `_apply_filters` / `catalogue-filters.ts`. **Track 4 (recommender laboratory):** a new `recommendations/content/` module building item feature vectors (one-hot genres + allowlist platforms + franchise/developer buckets + a genre-rating term, D-11/D-13), a `_entry_weight`-weighted user profile vector (reuse `genre_heuristic._entry_weight`), cosine similarity, and the three combination modes (`weighted_sum` / `multiplicative` / `two_stage`) each shipped as a named, versioned `algorithm_id` with a deterministic contribution-table explanation. **Track 5 (evaluation contract):** a frozen, checked-in protocol document + `protocol.json`; a seeded `generate_synthetic_users` command producing ~8 archetypes × ~25 users (~200) persisted as `DemoAccountIdentity` rows plus an explicit cold-start cohort, with a validation report; and a `run_evaluation` command doing leave-one-out-per-user top-N evaluation with a train/val/test user split, a ≤24-config tuning grid selected on validation nDCG@10, one test run, and Precision/Recall/nDCG/MAP at K∈{5,10,20}.

**Primary recommendation:** Sequence the work as governance → ratings (importer field fix + re-import + snapshot) → search/alias backfill → multi-select filters → UI pass → evaluation protocol freeze → synthetic users → content recommender → harness run. Keep the whole recommender + harness in **pure Python + stdlib** (no `numpy`) for Phase 2 to preserve the project's 5-dependency posture and match the `genre_heuristic.py` precedent — the feature vectors are tiny and sparse and 24×200 leave-one-out passes over ~tens of thousands of governed works run in minutes. Flag to the author that Phase 3's fuller metric suite + statistical tests (EVAL-08) will likely justify bringing `numpy`/`scipy` in then; decide now whether to adopt `numpy` early to avoid a re-write.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Corpus governance (`in_corpus`, `corpus_version`, checksum/dictionary/quality report) | API / Backend (offline management command) | Database / Storage | Same tier and shape as `import_igdb_catalogue` — never a request path (CAT-06/OPS-03). Additive migration + recomputable command (D-04). |
| IGDB rating ingestion + `CorpusRatingSnapshot` | API / Backend (offline command) | Database / Storage | Extends the existing importer; snapshot rows are an evidence contract, written once per `corpus_version`. |
| RAWG fallback ratings (if in scope) | API / Backend (offline command) | Database / Storage | Mirror the IGDB client's redaction + pacing + resumable-cursor discipline; new `catalogue/rawg.py`. Never request-time. |
| Live blended "display" rating (external + SavePoint users, D-09) | API / Backend (read-time or denormalised-on-write) | Frontend Server | A *product* number, not research data — computed from `LibraryEntry` + external, restricted to a documented account set (mirror `rank_popularity_v1`'s demo-account restriction). Experiments never read it. |
| `GameAlias` backfill + importer alias creation | API / Backend (offline command + importer change) | Database / Storage | Search is a pure local query over `GameAlias`; aliases are import-time data, not request-time. |
| Multi-select filter parsing + query | API / Backend (`catalogue/search.py`) | Frontend Server (`catalogue/page.tsx`, `FilterBar`, `catalogue-filters.ts`) | Server-validated allowlist + `order_by`; the page stays a searchParams-driven server component (no client state) per UI-SPEC. |
| "Novedades" shelf (D-24) | API / Backend (new list endpoint or home payload) | Frontend Server (`NewReleasesShelf`) | Deterministic `order_by` over `in_corpus` + `first_release_date`; no new data. |
| Content recommender variants (feature vectors, cosine, combination modes, explanations) | API / Backend (request-time compute over committed data + snapshot) | Frontend Server (`/recommendations` page) | Same tier as `rank_genre_taste_v1` — computed live from PostgreSQL + the rating snapshot, never trained/persisted as a model artifact in Phase 2 (a persisted feature cache is allowed; a trained model is Phase 3+). |
| Synthetic user generation | API / Backend (offline command, seeded) | Database / Storage (persisted as `DemoAccountIdentity` + `LibraryEntry` rows) | Reproducible seed contract, same discipline as `bootstrap_demo_accounts`. Clearly-labelled simulated accounts (AUTH-02). |
| Evaluation harness (`run_evaluation`) | API / Backend (offline command) | Database / Storage (artifact JSON) | Offline job that publishes versioned artifacts (STACK rule: "no training/tuning inside web requests"). |
| Frozen protocol document + `protocol.json` | Docs / Static (checked-in) | — | The evidence contract; must exist before any variant runs (EVAL-03). |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`dataclasses`, `hashlib`, `json`, `random`, `math`, `statistics`, `collections`) | 3.13.x (`requires-python = "==3.13.*"` `[VERIFIED: pyproject.toml:5]`) | Feature vectors, cosine, seeded synthetic-user draws, ranking metrics, fingerprints | The existing `recommendations/genre_heuristic.py` and `library/popularity.py` are pure stdlib + Django ORM `[VERIFIED: apps/api/recommendations/genre_heuristic.py, apps/api/library/popularity.py — read this session]`. The Phase 2 laboratory is deliberately simpler than Phase 3's rigorous comparison; stdlib keeps zero new dependency surface and matches the house pattern. `random.Random(seed)` gives reproducible draws; `math.fsum` gives exact cosine numerators. |
| Django ORM (`Django==5.2.17`, `djangorestframework==3.18.0`) | already pinned `[VERIFIED: pyproject.toml:7-8]` | Governed-view querysets, snapshot writes, candidate-set builders, aggregation (`Count`, `Avg`, `Case/When`) | Every existing catalogue/recommendation query is ORM-only; the governance/snapshot/recommender queries are additive `.filter()`/`.annotate()` on top. |

**No new required core dependency is recommended for Phase 2.**

### Supporting (considered; adopt only with author sign-off + full dependency gate)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `numpy` | 2.5.2 is the STACK-blessed pin (`AGENTS.md` STACK table: "NumPy 2.5.2 … Shared foundation for feature vectors, rankings, metrics, and seeded synthetic generation") `[CITED: AGENTS.md Technology Stack section]` — **verify the current patch with `pip index versions numpy` before pinning** | Vectorised cosine over the governed feature matrix; `numpy.random.default_rng(seed)` for synthetic users; array maths for metrics | Adopt **only if** the pure-Python harness runtime proves unacceptable (unlikely at this scale) or if the author chooses to bring it in early because Phase 3 needs it anyway. Triggers the project dependency gate: human approval + `docs/verification/dependency-legitimacy.md` row + `scripts/check-dependencies.ps1` row + `agent-ledger.jsonl` entry `[CITED: CONVENTIONS.md §3]`, and its own line in the ratings/recommender ADR. |
| `scikit-learn` | 1.9.0 STACK pin `[CITED: AGENTS.md]` | `cosine_similarity`, `OneHotEncoder`, `ndcg_score`, `train_test_split` | **Not recommended for Phase 2.** STACK itself notes it "does not supply a complete recommender evaluation protocol; implement project metrics explicitly." The ranking metrics (D-22) must be hand-written and unit-tested regardless; adding sklearn now buys little and enlarges the security-review surface. Revisit in Phase 3. |
| `scipy` | 1.18.1 STACK pin `[CITED: AGENTS.md]` | Sparse matrices, statistical tests | Phase 3 (EVAL-08 statistical tests). Not this phase. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure-Python content recommender | `numpy` vectorised implementation | numpy is faster and more idiomatic for feature matrices, and Phase 3 will want it — but it is a new dependency behind the project's approval gate, and the Phase 2 scale (≤~150k governed works × ~60 sparse features × 200 users × 24 configs, offline) does not need it. Recommend deferring the decision to the author with a clear "adopt early or rewrite later" framing. |
| Persisted synthetic users as `DemoAccountIdentity` rows | Ephemeral in-memory synthetic users regenerated per harness run | Persisting them makes the histories inspectable in the product UI (AUTH-02 "clearly identified as simulated"), lets `rank_popularity_v1`'s demo-account restriction naturally include/exclude them, and makes the validation report a query rather than a log. Ephemeral would avoid ~200 account rows but loses all of that. Recommend persisted, with a distinct `seed_key` prefix (`synthetic-<archetype>-<n>`) and the existing `SIMULATED_ACCOUNT_MARKER`. `[VERIFIED: apps/api/accounts/models.py:26,43-71 — DemoAccountIdentity, marker, seed_key]` |
| Re-run the full 312k IGDB import to backfill ratings + aliases + new fields | A targeted enrichment pass over `in_corpus=True` works only | A full re-run is ~50 min of IGDB pull `[VERIFIED: docs/verification/igdb-catalogue-freeze.md:89]` and already idempotent via `update_or_create` on `SourceRecord`. A governed-subset enrichment pass is faster and lighter but needs a second code path. Recommend: expand `GAME_FIELDS`, run one full re-import to converge every field (it also rebuilds the snapshot dump), then snapshot ratings for the governed subset. |
| RAWG as a committed second ratings source | IGDB only, accept measured coverage | RAWG's terms (below) are a real thesis-narrative cost (second provenance chain, second ADR, mandatory backlink). Recommend: **measure IGDB governed-corpus user-rating coverage first** (`total_rating IS NOT NULL` and `rating IS NOT NULL` counts over `in_corpus=True`), then let the author decide with a number in hand (D-05/D-06). |

**Installation:** none for the recommended (pure-Python) path. If `numpy` is adopted: `uv add numpy==<verified>` from repo root, then the four dependency-gate artifacts.

**Version verification:** `numpy` / `scikit-learn` / `scipy` pins above are `[CITED: AGENTS.md STACK table]`, not re-verified against PyPI this session — the executor MUST run `pip index versions numpy` (etc.) and confirm the current patch + publish date before writing any pin, per the STACK's own "Open Validation Items".

## Package Legitimacy Audit

No external package is required for the recommended Phase 2 plan. If the author opts to adopt `numpy` (or later `scikit-learn`/`scipy`), run the gate before the install task:

```bash
gsd_run query package-legitimacy check --ecosystem pypi numpy
pip index versions numpy
```

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| numpy | PyPI | ~20 yrs, continuous releases | very high (top-10 PyPI) | github.com/numpy/numpy | not run this session — no install planned | If adopted: expected OK; still requires the project's human dependency sign-off (`checkpoint:human-verify`) + `dependency-legitimacy.md` + `check-dependencies.ps1` + ledger entry per `CONVENTIONS.md §3`. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

*If `numpy`/`scikit-learn`/`scipy` enter scope during planning, the planner MUST add a `checkpoint:human-verify` task before the `uv add`, and a task to update all four dependency-gate artifacts in the same commit.*

## Architecture Patterns

### System Architecture Diagram

```
  OFFLINE MANAGEMENT COMMANDS (never a request path — CAT-06/OPS-03)
  ┌────────────────────────────────────────────────────────────────────────┐
  │ import_igdb_catalogue  (EXTEND: +rating,rating_count,total_rating_count,│
  │   summary,alternative_names,franchises,involved_companies in GAME_FIELDS;│
  │   +GameAlias creation in _upsert)                                        │
  │         │ writes GameWork / Genre / Platform / GameRelease /            │
  │         │ SourceRecord / AssetAttribution  (+GameAlias, +summary, ...)   │
  │         ▼                                                                │
  │ backfill_game_aliases  (one-off: normalize_title(name) + title_en +     │
  │   alternative_names → GameAlias, bulk_create ignore_conflicts)          │
  │         ▼                                                                │
  │ govern_corpus  (apply D-03 rules + D-01 allowlist → set in_corpus,      │
  │   bump corpus_version; emit checksum + data dictionary +               │
  │   quality/missing-fields report incl. rating coverage)  ── DATA-03      │
  │         ▼                                                                │
  │ snapshot_corpus_ratings  (write CorpusRatingSnapshot(work,rating,       │
  │   rating_count,source,retrieved_at,corpus_version) for in_corpus works) │
  │         │                             ▲                                  │
  │         │            (optional) enrich_rawg_ratings ──┘ if IGDB         │
  │         │            coverage low — allowlist games only, own ADR      │
  │         ▼                                                                │
  │ generate_synthetic_users  (seeded: ~8 archetypes × ~25 + cold-start;    │
  │   persist DemoAccountIdentity + LibraryEntry; validation report) EVAL-09 │
  │         ▼                                                                │
  │ run_evaluation  (frozen protocol.json → LOO split → candidate sets →    │
  │   {random, popularity, content-*} → Precision/Recall/nDCG/MAP@{5,10,20} │
  │   → per-run artifact JSON)  EVAL-01/02/03                               │
  └────────────────────────────────────────────────────────────────────────┘

  REQUEST-TIME (all local, zero external calls)
   GameListView ──► search_games / parse_catalogue_query  (EXTEND: getlist,
     genres AND, platforms OR; sort unchanged)                    CAT-02
   RecommendationsView (genre-taste-v1, unchanged)  +  NEW ContentRecsView
     (variant selected by algorithm_id; reads CorpusRatingSnapshot for the
      active corpus_version + persisted feature vectors)          REC-03..09
   NEW NewReleasesView  (in_corpus + first_release_date window)   D-24
   NEW OwnedGamesDlcView  (RelatedContent where parent ∈ user library) D-15
        │
        ▼
   apps/web  catalogue/page.tsx (multi FacetMenu) · games/[id] (Synopsis,
     RatingBreakdownLine, ScorePill relabel, DLC shelf) · recommendations/
     page.tsx (3 labelled sections) · page.tsx (NewReleasesShelf)
```

### Recommended Project Structure

```
apps/api/
├── catalogue/
│   ├── models.py            # ADD: GameWork.in_corpus (bool), GameWork.corpus_version,
│   │                        #      GameWork.summary (TextField); NEW CorpusRatingSnapshot;
│   │                        #      (optional) Franchise / Developer minimal entities OR
│   │                        #      denormalised franchise_slug / developer_slug fields
│   ├── igdb.py              # EXTEND: GAME_FIELDS += rating,rating_count,total_rating_count,
│   │                        #         summary,alternative_names.name,franchises.name,
│   │                        #         involved_companies.company.name,involved_companies.developer
│   ├── rawg.py              # NEW (only if RAWG in scope): redaction + pacing + id-cursor client
│   ├── management/commands/
│   │   ├── import_igdb_catalogue.py   # EXTEND: map new fields; create GameAlias in _upsert
│   │   ├── backfill_game_aliases.py   # NEW: one-off alias backfill for existing works
│   │   ├── govern_corpus.py           # NEW: D-01/D-03 rules → in_corpus + corpus_version + reports
│   │   ├── snapshot_corpus_ratings.py # NEW: write CorpusRatingSnapshot for a corpus_version
│   │   └── enrich_rawg_ratings.py     # NEW (conditional): RAWG user ratings for allowlist works
│   ├── search.py            # EXTEND: getlist for genre/platform; genres AND, platforms OR
│   ├── corpus.py            # NEW: governed_works() queryset + allowlist constants (single source)
│   └── views.py             # EXTEND GameListView; ADD NewReleasesView, OwnedGamesDlcView
├── recommendations/
│   ├── genre_heuristic.py   # unchanged (REC-10, kept)
│   ├── content/             # NEW
│   │   ├── features.py      # item feature vectors (genres+platforms+franchise+developer+rating term)
│   │   ├── profile.py       # user profile vector (reuse genre_heuristic._entry_weight)
│   │   ├── similarity.py    # cosine (stdlib)
│   │   ├── combine.py       # weighted_sum / multiplicative / two_stage
│   │   ├── explain.py       # deterministic contribution table (D-16)
│   │   └── variants.py      # ALGORITHM registry: id → (feature_set, combine_mode, params, version)
│   ├── baselines.py         # NEW: rank_random_v1(user, seed)  (REC-01)
│   └── views.py             # EXTEND: ContentRecsView
├── evaluation/              # NEW app (add to INSTALLED_APPS)
│   ├── protocol.py          # load + validate protocol.json; freeze checks
│   ├── synthetic.py         # archetype definitions + seeded generator
│   ├── splits.py            # leave-one-out per user; train/val/test user split
│   ├── metrics.py           # precision@k, recall@k, ndcg@k, map@k  (hand-written, unit-tested)
│   ├── runner.py            # orchestrate variants over the frozen split
│   └── management/commands/
│       ├── generate_synthetic_users.py
│       └── run_evaluation.py
docs/
├── adr/ADR-008-external-ratings.md          # NEW (IGDB rating fields; optional RAWG)
├── methodology/evaluation-protocol.md       # NEW (frozen; DOC-04)
├── methodology/protocol.json                # NEW (machine-readable frozen protocol)
├── methodology/agent-methodology-controls.md# NEW or extend (AGENT-04)
└── verification/
    ├── corpus-governance-freeze.md          # NEW (DATA-03: checksum + dictionary + quality)
    ├── igdb-catalogue-freeze.md             # UPDATE (new fields, rating coverage row)
    └── synthetic-users-validation.md        # NEW (EVAL-09 validation report)
apps/web/
├── lib/catalogue-filters.ts   # genre/platform → string[]; getAll; per-value chips
├── app/[locale]/catalogue/page.tsx  # first() → getAll; FacetMenu
├── app/[locale]/games/[id]/page.tsx # Synopsis, RatingBreakdownLine, DLC shelf
├── app/[locale]/recommendations/page.tsx # 3 labelled sections
└── components/ …            # FacetMenu, Synopsis, ContentRecommendationList, WhyDisclosure,
                             # ContributionTable, OwnedGamesDlcShelf, NewReleasesShelf (UI-SPEC)
```

### Pattern 1: Platform allowlist as a curated constant set keyed on IGDB slug (D-01)

**What:** Define the allowlist once in `catalogue/corpus.py` as an ordered list of `(igdb_id, slug, display_name)` and resolve it to a set of `Platform.slug` values at command time. A `GameWork` "has a valid platform" iff `work.releases.filter(platform__slug__in=ALLOWLIST_SLUGS).exists()`.

**Why slug not `category`:** IGDB's `Platform.category` enum is **deprecated** — the generated docs say *"@deprecated Use platform_type instead"* `[VERIFIED: DmitryScaletta/igdb-api-types index.ts:1983-1984 (generated from IGDB api-docs.html), fetched via gh this session]`. The 01.1 probe already found the analogous game `category` field returns 0 (unpopulated) `[VERIFIED: docs/verification/igdb-api-probe.md:28]`. So `category` is a weak signal; a curated list is what D-01 asks for anyway. For reference, `PlatformCategoryEnum` values are: `console = 1, arcade = 2, platform = 3, operating_system = 4, portable_console = 5, computer = 6` `[VERIFIED: igdb-api-types index.ts:2030-2037]` — usable only as a loose sanity check.

**Proposed concrete allowlist (~40 platforms).** IGDB IDs ≤ 166 are `[CITED: gist ahmed-abdelazim/b533b443388baaafab3fc377e71e0109 — community "IGDB all platforms by ID", ~2020]`; PS5 / Xbox Series are `[ASSUMED]` from training memory and MUST be confirmed by a live `POST /v4/platforms` probe (credentials already available) before `govern_corpus` runs:

| Family | Platform (IGDB name) | IGDB id | Note |
|---|---|---|---|
| PC | PC (Microsoft Windows) | 6 | D-02: "Steam" resolves here |
| PC | Mac | 14 | |
| PC | Linux | 3 | |
| PlayStation | PlayStation | 7 | |
| PlayStation | PlayStation 2 | 8 | |
| PlayStation | PlayStation 3 | 9 | |
| PlayStation | PlayStation 4 | 48 | |
| PlayStation | PlayStation 5 | 167 `[ASSUMED]` | confirm via probe |
| PlayStation | PlayStation Portable | 38 | |
| PlayStation | PlayStation Vita | 46 | |
| Xbox | Xbox | 11 | |
| Xbox | Xbox 360 | 12 | |
| Xbox | Xbox One | 49 | |
| Xbox | Xbox Series X\|S | 169 `[ASSUMED]` | confirm via probe |
| Nintendo | Nintendo Entertainment System (NES) | 18 | |
| Nintendo | Super Nintendo Entertainment System (SNES) | 19 | |
| Nintendo | Nintendo 64 | 4 | |
| Nintendo | Nintendo GameCube | 21 | |
| Nintendo | Wii | 5 | |
| Nintendo | Wii U | 41 | |
| Nintendo | Nintendo Switch | 130 | |
| Nintendo | Game Boy | 33 | |
| Nintendo | Game Boy Color | 22 | |
| Nintendo | Game Boy Advance | 24 | |
| Nintendo | Nintendo DS | 20 | |
| Nintendo | Nintendo 3DS | 37 | |
| Sega | Sega Master System | 64 | |
| Sega | Sega Mega Drive/Genesis | 29 | |
| Sega | Sega Game Gear | 35 | |
| Sega | Sega Saturn | 32 | |
| Sega | Dreamcast | 23 | |
| Atari | Atari 2600 | 59 | |
| Atari | Atari 5200 | 66 | |
| Atari | Atari 7800 | 60 | |
| Atari | Atari Lynx | 61 | |
| Atari | Atari Jaguar | 62 | |
| Mobile | iOS | 39 | |
| Mobile | Android | 34 | |
| Web | Web browser | 82 | |

**Reconciliation caveat:** the importer created `Platform` rows keyed on `slug` reconciled against the pre-existing Wikidata rows (`Platform.objects.filter(slug=slug).first() or filter(name=pname).first()`) `[VERIFIED: apps/api/catalogue/management/commands/import_igdb_catalogue.py:191-223]`. So the allowlist must be matched on **slug** (e.g. `slugify("PC (Microsoft Windows)") = "pc-microsoft-windows"`), and `govern_corpus` should print any allowlist slug that resolves to **zero** `Platform` rows so the author can catch a spelling drift before governance runs.

### Pattern 2: Immutable rating snapshot + reconciliation (D-05/D-07/D-08/D-09, DATA-05/06/07)

**IGDB rating fields — verbatim definitions** `[VERIFIED: igdb-api-types index.ts:1181-1334, generated from IGDB api-docs.html, fetched via gh this session]`:

| Field | IGDB doc comment (verbatim) | Kind | Use in this phase |
|---|---|---|---|
| `rating` | "Average IGDB user rating" | **user**, 0–100 float | **Primary user-rating signal (D-05).** Add to `GAME_FIELDS`. |
| `rating_count` | "Total number of IGDB user ratings" | user | Confidence weight (D-13). Add to `GAME_FIELDS`. |
| `aggregated_rating` | "Rating based on external critic scores" | **critic** | Do NOT use as the primary signal (D-05). Last resort only. |
| `aggregated_rating_count` | "Number of external critic scores" | critic | — |
| `total_rating` | "Average rating based on both IGDB user and external critic scores" | **blend of user + critic** | Currently the ONLY rating field imported. It is a mean of `rating` and `aggregated_rating` — **not** a pure user signal, so it does not satisfy D-05's "prefiere ratings de usuarios". Keep importing it for the live product number, but the snapshot must store `rating`/`rating_count`. |
| `total_rating_count` | "Total number of user and external critic scores" | blend | Add to `GAME_FIELDS` for display ("N usuarios" needs the user split; use `rating_count` for the IGDB-user count in `detail.ratingBreakdown`). |
| `hypes` | "Number of follows a game gets before release" | pre-release interest | Deferred to Phase 6 (trending). Not a rating. |
| `follows` | "@deprecated - To be removed" | — | Do not use. |

**Why `GameWork.total_rating` looks empty (the D-05 "causa a investigar"):** Three checks, in order of likelihood — the plan needs a Wave-0 measurement task, not a guess:

1. **The importer only ever requested the blended field.** `GAME_FIELDS` is `"id,name,slug,url,first_release_date,total_rating,genres.id,genres.name,platforms.id,platforms.name,cover.image_id"` `[VERIFIED: apps/api/catalogue/igdb.py:36-39]` — no `rating`, no `rating_count`. So even a perfect import gives you only `total_rating`, never the user rating the author wants.
2. **`total_rating` IS mapped when present.** `_normalize` does `rating = row.get("total_rating"); if isinstance(rating, (int, float)): total_rating = round(float(rating), 4)` and `_upsert` writes `work.total_rating = norm["total_rating"]` `[VERIFIED: apps/api/catalogue/management/commands/import_igdb_catalogue.py:127-130, 258-266, 275]`. The serializers expose it (`total_rating = serializers.FloatField(allow_null=True)` on both card and detail) `[VERIFIED: apps/api/catalogue/serializers.py:63, 128]`. So "not requested" is refuted for `total_rating`, and "not mapped" / "not surfaced" are refuted. The remaining explanation is data.
3. **Genuine IGDB sparsity.** IGDB omits null fields from responses entirely, so `total_rating` is absent for any game with zero IGDB user ratings **and** zero tracked critic scores — which is the overwhelming majority of the 312k `game_type = 0` long tail (obscure, old, regional, shovelware). The `igdb-catalogue-freeze.md` evidence measured covers/genres/platforms/year histogram but **never measured rating coverage** `[VERIFIED: docs/verification/igdb-catalogue-freeze.md:45-58, 83-95 — no rating row]`. **Wave-0 task:** against `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (already on disk, 93 MB, gitignored `[VERIFIED: igdb-catalogue-freeze.md:95]`), run `SELECT count(*) FILTER (WHERE total_rating IS NOT NULL) AS rated, count(*) AS total FROM catalogue_gamework WHERE id IN (SELECT work_id FROM catalogue_sourcerecord WHERE source='igdb')`, and repeat scoped to a trial `in_corpus` set. `[ASSUMED]` expectation: full-catalogue `total_rating` coverage is low (order of 5–20 %); governed-subset coverage is materially higher because D-03 already removes the untitled/genre-less/date-less/DLC noise — but the number, not the guess, drives the D-05/D-06 RAWG decision.

**Snapshot table (D-08):**

```python
class CorpusRatingSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey("catalogue.GameWork", on_delete=models.CASCADE, related_name="rating_snapshots")
    corpus_version = models.CharField(max_length=32)          # matches GameWork.corpus_version
    source = models.CharField(max_length=16)                  # "igdb" | "rawg"
    rating = models.FloatField(null=True)                     # user rating, normalised 0..100
    rating_count = models.PositiveIntegerField(default=0)
    retrieved_at = models.DateTimeField()
    class Meta:
        constraints = [models.UniqueConstraint(
            fields=("work", "corpus_version", "source"),
            name="catalogue_unique_rating_snapshot")]
```

Rules: `snapshot_corpus_ratings` **only inserts** (never updates) for a given `corpus_version`; a re-import updates `GameWork.rating`/`total_rating` (live) but never a snapshot row. The harness and recommender read `CorpusRatingSnapshot.objects.filter(corpus_version=ACTIVE_VERSION, source="igdb")` — never `GameWork.total_rating`. This is exactly the DATA-06 guarantee.

**DATA-07 reconciliation (IGDB ↔ RAWG, if RAWG adopted):** IGDB `id` is authoritative and already the canonical identity (`SourceRecord(source="igdb", source_id=<igdb id>)`, and `canonical_slug` derived from the IGDB slug) `[VERIFIED: import_igdb_catalogue.py:112-113, 240-289]`. RAWG rows attach via a new `SourceRecord(source="rawg", source_id=<rawg id>)` on the same `GameWork`, matched by exact IGDB-slug ↔ RAWG-slug equality first, then normalised-title + release-year equality, with any unmatched RAWG row **dropped and counted** (never fuzzy-guessed). Conflict rule when both sources have a user rating for a work: keep both snapshot rows (`source` distinguishes them); the recommender's rating term (D-13) uses IGDB when `rating_count` ≥ a documented floor, else the higher-`rating_count` source, else the genre median. Document the exact rule in ADR-008.

**Live blended "display" rating (D-09):** compute a `display_rating` (0–100) at read time (or denormalise on `LibraryEntry` save) = confidence-weighted blend of the external value and the mean of SavePoint `LibraryEntry.rating_half_steps` (×10 to reach the 0–100 scale) for that work. **Restrict which SavePoint ratings count** the same way `rank_popularity_v1` restricts to `Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)` `[VERIFIED: apps/api/library/popularity.py:44-49]` — the planner/author fixes whether the live number counts (a) demo + synthetic + self-registered, or (b) self-registered only. Whatever the choice: the **research snapshot never includes any SavePoint rating** — it is external-only, frozen at `corpus_version` freeze time. `detail.ratingBreakdown` ("Basada en la valoración de N usuarios de IGDB y M de SavePoint") uses `rating_count` (IGDB) and the counted-SavePoint-entry count.

### Pattern 3: Multi-select filters — repeated params, genres AND / platforms OR (CAT-02, UI-SPEC P1)

**What (already resolved in UI-SPEC P1, this is the backend contract):**
- URL: repeated keys, `?genre=rpg&genre=strategy&platform=switch`. `parseFilters` / `parse_catalogue_query` read **all** values (`request.query_params.getlist("genre")`), normalise, de-dupe, drop empties.
- `CatalogueFilters.genre` / `.platform` change from `string?` to `string[]` in `apps/web/lib/catalogue-filters.ts` `[VERIFIED: apps/web/lib/catalogue-filters.ts:42-50, 55-83 — currently single-value via `sp.genre?.trim()`]`. `countActiveFilters` counts **each** selected value; `buildQuery` emits one repeated pair per value; one `FilterChip` per value with a `removeHref` that drops only that value.
- Semantics: **genres = AND** ("contiene todos"), **platforms = OR** ("disponible en alguna").

**Backend change to `catalogue/search.py`** `[VERIFIED: apps/api/catalogue/search.py:73-153 (CatalogueQuery + parse_catalogue_query), 161-182 (_apply_filters)]`:

```python
@dataclass
class CatalogueQuery:
    q: str | None = None
    genres: tuple[str, ...] = ()      # was: genre: str | None
    platforms: tuple[str, ...] = ()   # was: platform: str | None
    year_from: int | None = None
    year_to: int | None = None
    min_rating: float | None = None
    sort: str = "relevance"

def _apply_filters(qs, cq):
    joined = False
    # platforms: OR — one IN clause
    valid_platforms = list(Platform.objects.filter(slug__in=cq.platforms).values_list("slug", flat=True))
    if valid_platforms:
        qs = qs.filter(releases__platform__slug__in=valid_platforms); joined = True
    # genres: AND — chained filter per genre (each adds a join)
    for g in cq.genres:
        if Genre.objects.filter(slug=g).exists():
            qs = qs.filter(genres__slug=g); joined = True
    if cq.year_from is not None: qs = qs.filter(first_release_date__gte=date(cq.year_from, 1, 1))
    if cq.year_to   is not None: qs = qs.filter(first_release_date__lte=date(cq.year_to, 12, 31))
    if cq.min_rating is not None: qs = qs.filter(total_rating__gte=cq.min_rating)
    if joined: qs = qs.distinct()
    return qs
```

Keep the existing behaviours: unknown slug → silently dropped (not an empty result); unknown `sort` / out-of-range year/rating → bounded 400 via `FilterValidationError` `[VERIFIED: search.py:62-70, 110-140]`. `min_rating` stays single-value. Governed-catalogue scoping: `_base_works()` should become `governed_works()` (= `GameWork.objects.filter(is_dlc=False, in_corpus=True)`) once governance lands — the catalogue's public list, search, and facets all operate on the governed view; the ~312k non-governed rows remain for later phases. `[VERIFIED: search.py:156-159 `_base_works` filters only `is_dlc=False`]`

**Facet counts** (`_facets`, three aggregate queries, no N+1 `[VERIFIED: search.py:233-261]`) need no structural change — they already `Count(..., distinct=True)` over the scoped set.

### Pattern 4: `GameAlias` backfill — the search-bug root cause (Claude's discretion)

**Root cause (confirmed):** `_ordered_matching_work_ids` queries `GameAlias` **exclusively** (exact `normalized_value` → `startswith` → `trigram_similar`, capped at 200) `[VERIFIED: apps/api/catalogue/search.py:189-230]`. The IGDB importer's `_upsert` writes `GameWork`, `SourceRecord`, `Genre`, `GameRelease`, `AssetAttribution` — **never `GameAlias`** `[VERIFIED: apps/api/catalogue/management/commands/import_igdb_catalogue.py:240-337 — no GameAlias reference anywhere in the file]`. Only the Wikidata importer creates aliases. Net: search can match ~the 150 Wikidata works' aliases and essentially nothing from the 312k IGDB import.

**`GameAlias` shape** `[VERIFIED: apps/api/catalogue/models.py:128-154]`: `(work FK, locale ∈ {"en","es"}, value, normalized_value db_index)`; unique on `(work, locale, normalized_value)`; a GIN trigram index `catalogue_alias_trgm_gin` on `normalized_value` with `gin_trgm_ops`. `normalize_title(value)` = NFKD + strip combining marks + casefold `[VERIFIED: apps/api/catalogue/normalization.py:8-12]`.

**Recommendation — do BOTH:**

1. **One-off `backfill_game_aliases` management command (immediate fix).** For every `GameWork` with no `GameAlias` (or every work, idempotent via the unique constraint), create: primary alias `(locale="en", value=original_title, normalized_value=normalize_title(original_title))`; plus `title_en` if non-empty and different; plus each IGDB `alternative_names.name` (once the importer fetches them — see step 2). Use `GameAlias.objects.bulk_create(objs, ignore_conflicts=True, batch_size=5000)` inside batched transactions (mirror the importer's batch discipline). At ~312k works × ~1–3 aliases ≈ 0.4–1M rows. Runs offline in minutes; no IGDB calls.
2. **Add alias creation to `import_igdb_catalogue._upsert`** so future imports / re-runs stay correct. Also add `alternative_names.name` to `GAME_FIELDS` (`apps/api/catalogue/igdb.py:36-39`) and map it in `_normalize`. On update, `set`-style reconcile: delete the work's stale auto-aliases not in the new set (guard like the importer already does for stale releases), then `bulk_create(ignore_conflicts=True)`.

**pg_trgm index health at this scale:** the existing GIN + the `%`-operator prefilter + `TRIGRAM_CANDIDATE_CAP = 200` already bound fan-out `[VERIFIED: search.py:31-32, 210-222]`. After the bulk backfill: run `VACUUM ANALYZE catalogue_gamealias` (GIN pending-list flush + planner stats); optionally raise `maintenance_work_mem` for the session and consider `REINDEX INDEX CONCURRENTLY catalogue_alias_trgm_gin` if insert order fragmented it. Do the bulk insert with the GIN index **already present** (Postgres batches pending-list updates) rather than dropping/recreating — at <1M rows the drop/recreate saving is not worth the operational risk on the shared dev DB. Keep `pg_trgm.similarity_threshold` at its default; the code uses an explicit `TRIGRAM_SIMILARITY_THRESHOLD = 0.3` and `similarity__gte` filter, so the GUC is irrelevant.

### Pattern 5: Content recommender laboratory (REC-03/06/07/08/09, D-10..D-16)

**Feature vectors (`content/features.py`, D-11).** Per governed `GameWork`, a sparse dict `{feature_key: weight}`:
- **genres** (guaranteed — 23 total `[VERIFIED: igdb-catalogue-freeze.md:56]`): `f"genre:{slug}"` → 1.0 (or 1/√k for k genres, to stop many-genre works dominating — a tuning parameter).
- **platforms** (allowlist only, ~40): `f"platform:{slug}"` → 1.0.
- **franchise / series**: `f"franchise:{slug}"` → 1.0. Requires importer to fetch `franchises.name` / `collections.name` (not currently fetched). Start absent; add once coverage measured (D-11).
- **developer**: `f"developer:{slug}"` → 1.0. Requires `involved_companies.company.name` + `involved_companies.developer` (boolean) in `GAME_FIELDS`. Start absent; add by coverage.
- **owns-base-game** (D-15): a per-user boolean feature that boosts DLC of owned base games — applied at scoring time, not stored on the item.
- **rating term** is NOT a vector dimension — it is the separate D-13 term combined per D-14.

Persist feature vectors in a `WorkFeatureVector(work, feature_set_version, vector_json)` table (a cache, not a trained model — allowed) so `run_evaluation` and the live endpoint don't recompute 100k vectors per call. Rebuild is a command; `feature_set_version` is part of the DTO (REC-09).

**User profile (`content/profile.py`, D-12).** `profile = Σ _entry_weight(status, rating_half_steps) · normalize(vector(work)) / Σ weights` over the user's `LibraryEntry` rows. **Reuse `genre_heuristic._entry_weight`** verbatim: `_STATUS_WEIGHTS = {"completed": 3.0, "playing": 2.0, "pending": 1.0, "abandoned": 0.0}` + `(rating_half_steps or 0)/10` `[VERIFIED: apps/api/recommendations/genre_heuristic.py:44-49, 94-95]`.

**Similarity (`content/similarity.py`, D-12).** Cosine, 0..1 (all feature weights ≥ 0 so cosine ∈ [0,1] naturally). Pure stdlib: `num = math.fsum(p[k]*v[k] for k in p.keys() & v.keys()); den = math.sqrt(sumsq(p))*math.sqrt(sumsq(v)); return num/den if den else 0.0`.

**Rating term (`combine.py`, D-13).** `genre_rating_profile[genre] = mean(snapshot.rating for governed works in that genre with a snapshot rating)` — computed from **training-split users' governed works only** for EVAL-02 cleanliness? No: the genre median is a *corpus* statistic from `CorpusRatingSnapshot`, not user data, so it is leakage-safe as long as it is computed from the frozen snapshot for the active `corpus_version`. Candidate rating term = confidence-blend of the candidate's own snapshot `rating` (weight ∝ `rating_count`, capped) and the mean of its genres' `genre_rating_profile` (D-13), normalised to 0..1. If the candidate has no snapshot rating: use the genre median and mark it (`why.ratingTermFallback`, D-07 — "se usó la mediana de sus géneros").

**Combination modes (`combine.py`, D-14) — three named variants:**

| `algorithm_id` (proposed) | mode | score |
|---|---|---|
| `content-cbf-weighted-v1` | `weighted_sum` | `w1·cos + w2·rating_term (+ w3·own_rating_if_present)`; `w1,w2,w3` frozen in `protocol.json`, tunable within the ≤24 grid |
| `content-cbf-multiplicative-v1` | `multiplicative` | `cos · rating_term` |
| `content-cbf-twostage-v1` | `two_stage` | bucket by `cos` bands (e.g. 5 bands), order within band by `rating_term` |

`variants.py` holds an `ALGORITHM_REGISTRY: dict[str, VariantSpec]` where `VariantSpec` = `(feature_set_version, combine_mode, param_dict, version_string)`. The DTO mirrors ADR-007 exactly plus versioning: `algorithm_id`, `generated_at`, `input_snapshot_sha256`, `feature_set_version`, `corpus_version`, `snapshot_sha256`, `insufficient_history`, `limitation`, `results[]` (each with `work_id, slug, title, score, contributions[], rating_term, rating_term_is_fallback`) `[VERIFIED: apps/api/recommendations/genre_heuristic.py:245-254 for the DTO shape to extend; apps/api/recommendations/views.py:21-29 for the allowlist-echo view pattern to copy]`.

**Explanation (`explain.py`, D-16 / REC-08).** Purely from persisted features: `contributions = [{genre, contribution_pct}]` where `contribution_pct` = that genre dimension's share of the cosine numerator, sorted desc; plus the rating term value and its fallback flag; plus `variant: {algorithm_id}`. No generated prose. The UI-SPEC `recommendations.forYou.explanationSentence` is a fixed template filled with the top genres — the backend supplies the slot values, not a sentence.

**Cold start (REC-06).** `insufficient_history = True` when the user has `< 3` genre-bearing `LibraryEntry` rows (matches the D-20 cold-start cohort of 1–3 items). Response then carries the explicit fallback (popular-genres view) — never an empty `results` list (UI-SPEC §4a). Reuse the `genre_heuristic._insufficient_history` shape `[VERIFIED: genre_heuristic.py:112-120]` extended with the fallback list.

**Exclusions (REC-07).** Exclude every work the user has any `LibraryEntry` for (`seen_ids`, exactly as `rank_genre_taste_v1` `[VERIFIED: genre_heuristic.py:141-146]`). The rule is a `protocol.json` parameter (`exclude: "any_library_entry"`) so the harness and the live endpoint share it.

**Random baseline (REC-01, `baselines.py`).** `rank_random_v1(user, seed, limit)` = `random.Random(seed).sample(governed_candidates_minus_library, k=limit)`; DTO identical grammar to `rank_popularity_v1` with `limitation` = "Uniform random draw from the governed corpus; comparison floor only."

### Pattern 6: Frozen evaluation harness (EVAL-01/02/03, DOC-04)

**Freeze artifact.** `docs/methodology/protocol.json` checked in **before any variant runs**, containing: `relevance` (`{"completed": true, "rating_half_steps_gte": 7}`, D-17), `k_values` `[5,10,20]`, `headline` `"ndcg@10"` (D-19), `split` `{"strategy":"leave_one_out_per_user","seed":<int>}` (D-18), `candidate_set` (`"governed_corpus_minus_user_library_plus_heldout"`), `exclusions` (`"any_library_entry"`), `metrics` `["precision@k","recall@k","ndcg@k","map@k"]` (D-22 ranking subset), `tuning` `{"grid": [...≤24 configs...], "select_on":"ndcg@10","select_split":"validation","test_runs":1}` (D-21), `user_split` `{"train":N,"validation":M,"test":P,"seed":<int>}`, `corpus_version`, `snapshot_sha256`. A `protocol.py` loader validates the file and refuses to run if `len(grid) > 24` or if `test` has already been consumed (a run marker).

**Split (`splits.py`, D-18).** Per user: pick one "liked" work (relevance-positive, D-17) by a per-user deterministic seed, hold it out; candidate set = governed corpus − user's remaining library + the held-out item; the model must rank the held-out item. LOO with a single relevant item makes Recall@K ∈ {0, 1} and nDCG@K = `1/log2(rank+1)` if hit — implement metrics for the general case anyway (D-22, and Phase 3 will have multi-positive).

**User split (D-21).** Disjoint train/validation/test partition of the ~200 synthetic users by a fixed seed (e.g. 120/40/40). The tuning grid is scored on **validation** only; the winning config by `ndcg@10` is locked; **test is run exactly once** and its consumption is recorded so a re-run is refused without an explicit `--force-new-protocol` that bumps a protocol version. The genre-rating profile (D-13) is a corpus statistic (snapshot-derived), so it is leakage-safe across splits; any statistic that *were* user-derived would have to be train-only (EVAL-02).

**Metrics (`metrics.py`, D-22).** Hand-write and unit-test against tiny fixtures with known answers: `precision_at_k`, `recall_at_k`, `dcg_at_k` / `ndcg_at_k` (binary gains, `2^rel - 1` = `rel` for binary; discount `1/log2(i+2)` for 0-indexed rank `i`), `average_precision_at_k` / `map_at_k`. STACK explicitly says implement these explicitly rather than lean on a library `[CITED: AGENTS.md — "It does not supply a complete recommender evaluation protocol; implement project metrics explicitly"]`.

**Runner + artifacts (`runner.py`, `run_evaluation.py`).** For each of `{rank_random_v1, rank_popularity_v1, content-cbf-weighted-v1, content-cbf-multiplicative-v1, content-cbf-twostage-v1}` (+ grid configs on validation), produce one artifact JSON: `code_commit`, `protocol_sha256`, `corpus_version`, `snapshot_sha256`, `feature_set_version`, `seeds`, `split_manifest_sha256`, per-user held-out rank, per-K metrics, aggregate metrics, `simulation: true`, `limitation`. This is the data shape EVAL-11/12 formalise in Phase 3 — start it right here.

### Pattern 7: Corpus governance mechanics (DATA-03/06, D-04/D-08)

**Migration (additive, D-04):** `GameWork.in_corpus = BooleanField(default=False)`, `GameWork.corpus_version = CharField(max_length=32, blank=True)`, `GameWork.summary = TextField(blank=True)` (for the ficha synopsis, UI-SPEC §3). No data migration in the migration file itself — `govern_corpus` does the backfill so re-governing = re-run (D-04b).

**`govern_corpus` command:** one pass over `GameWork.objects.filter(source_records__source="igdb")`:
- compute `in_corpus = not (empty/<2-alnum/symbols-only name) and has ≥1 release on an allowlist platform (Pattern 1) and not is_dlc and has ≥1 genre and first_release_date is not null` (D-03). "sin rating" is NOT an exclusion (D-03/D-07).
- set `corpus_version` on every `in_corpus=True` row (monotonic string, e.g. `"2026.09.1"` or an int; store the rule-set hash alongside in a `CorpusVersion` metadata row for provenance).
- emit `docs/verification/corpus-governance-freeze.md` + a machine-readable JSON: **(1) checksum** — `sha256` over sorted `(source_id, snapshot_sha256)` for `in_corpus=True` works (reuse `_catalogue_checksum` shape `[VERIFIED: import_igdb_catalogue.py:341-353]`); **(2) data dictionary** — every field name, type, source, nullability; **(3) quality / missing-fields report** — governed count, per-field null counts and % coverage (genres, platforms, first_release_date, summary, cover, **`total_rating`**, **`rating`/`rating_count`** once imported), genre distribution, allowlist-platform distribution, year histogram, exclusion-reason histogram (how many works failed on each D-03 clause); **(4) deterministic sampled manifest** — every `step = floor(N/300)`-th governed work, ≤300 rows, for a human spot-check (reuse `_build_evidence` shape `[VERIFIED: import_igdb_catalogue.py:355-418]`). This is DATA-03. Do **not** enumerate every row.

**Immutability wiring (D-08):** experiments and the recommender read `CorpusRatingSnapshot` for a fixed `corpus_version` and `governed_works()` filtered by that `corpus_version`. A later re-import updates live `GameWork` fields and can produce a **new** `corpus_version` (new `govern_corpus` run) + new snapshot; old snapshots and old `corpus_version` rows are never mutated. Anything a thesis table cites is pinned to a `corpus_version` string.

### Anti-Patterns to Avoid

- **Reading `GameWork.total_rating` in the harness or recommender.** Always read `CorpusRatingSnapshot` for the active `corpus_version` (D-08). `GameWork.total_rating` is the mutable product number.
- **Enumerating every governed work in the freeze doc.** Checksum + aggregates + 300-row sample, per the established pattern (Pitfall in 01.1-RESEARCH, and `igdb-catalogue-freeze.md`'s own preamble).
- **Tuning on the test split, or computing any user-derived statistic across the whole user set.** D-21/EVAL-02: grid → validation only; test → one run.
- **Letting SavePoint user ratings leak into research data.** The snapshot is external-only; the blended `display_rating` is product-only and account-restricted (mirror `rank_popularity_v1`).
- **Generated prose in explanations.** D-16/REC-08/AGENT-04: contribution table + rating term from persisted features only.
- **Fuzzy-matching RAWG rows to IGDB works.** DATA-07: exact slug, then normalised-title+year; unmatched → dropped and counted.
- **`get_or_create(name=...)` for platforms/genres in any new command.** The importer learned this the hard way — match on `slug` first (IGDB vs Wikidata casing) `[VERIFIED: import_igdb_catalogue.py:191-223, 225-238]`.
- **A giant transaction for the alias backfill or snapshot write.** Batch it (importer precedent, 01.1-RESEARCH Pattern 2).
- **Adding `numpy`/`sklearn` without the four-artifact dependency gate + `checkpoint:human-verify`.** `[CITED: CONVENTIONS.md §3]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Activity weighting for the user profile vector | A new status/rating weighting scheme | `genre_heuristic._entry_weight` / `_STATUS_WEIGHTS` verbatim | The heuristic and the popularity baseline already share this "how much does this interaction count" language (ADR-007); the content profile is the third consumer. `[VERIFIED: genre_heuristic.py:44-49,94-95]` |
| Recommendation DTO / reproducibility fingerprint | A bespoke response shape | Extend the ADR-007 DTO (`algorithm_id` + `generated_at` + `input_snapshot_sha256` + `limitation`) + the view's allowlist-echo | Two ranking endpoints already use it; a third must be visibly the same grammar. `[VERIFIED: genre_heuristic.py:98-109,245-254; views.py:19-65]` |
| Idempotent upsert on external ids | A new keying scheme for RAWG / re-import | `update_or_create` on `SourceRecord(source, source_id)` | Already the house pattern for Wikidata and IGDB; RAWG is `source="rawg"`. `[VERIFIED: import_igdb_catalogue.py:279-289]` |
| Freeze evidence at scale | A per-row enumerated table | checksum + aggregate stats + 300-row deterministic sample | `igdb-catalogue-freeze.md` + `_build_evidence` already do exactly this. `[VERIFIED: igdb-catalogue-freeze.md; import_igdb_catalogue.py:341-418]` |
| Anti-contamination for a public/live aggregate | A new "is this a real user" flag | `Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)` | `rank_popularity_v1` already restricts its computation this way; the D-09 blended rating reuses it. `[VERIFIED: library/popularity.py:44-49]` |
| Seeded, all-or-nothing bulk account creation | A custom synthetic-user persister | Extend `bootstrap_demo_accounts`' advisory-lock + validate-then-write + redacted-output discipline | AUTH-02 accounts already have a seed contract, a marker, and a deterministic anchor UUID. `[VERIFIED: apps/api/accounts/management/commands/bootstrap_demo_accounts.py; accounts/models.py:29-71]` |
| Ranking metrics (P@K, R@K, nDCG@K, MAP) | Pulling in scikit-learn for `ndcg_score` | Hand-written functions in `evaluation/metrics.py` + unit tests with known-answer fixtures | STACK: "implement project metrics explicitly"; keeps the thesis's central contribution auditable and dependency-free. `[CITED: AGENTS.md]` |
| Trigram / fuzzy search | Any new matcher | The existing `_ordered_matching_work_ids` (exact→prefix→trigram, capped) — just feed it aliases | It is correct and bounded; the only bug is missing alias rows (Pattern 4). `[VERIFIED: search.py:189-230]` |
| LLM-based user simulation | An LLM synthetic-user generator (RecUserSim / SimUSER style) | Seeded parametric archetype draws (`random.Random(seed)`) | An LLM dependency would break reproducibility, add cost and an external service, contradict AGENT-04, and is not what D-20 describes. The classical parametric approach is the thesis-defensible one. `[CITED: WebSearch — recent RecSys user-sim literature is LLM-heavy; the classical parametric method is the reproducible baseline]` |

**Key insight:** every recommender/evaluation building block either already exists in `recommendations/` + `library/` + `accounts/` or is a small stdlib function — the phase is composition over invention. The only genuinely new external surface is the *optional* RAWG client, and it should copy `catalogue/igdb.py`'s redaction/pacing/cursor design line for line.

## Runtime State Inventory

> This phase adds columns, a table, and re-runs the importer, and it backfills two kinds of derived data — so runtime state matters.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | Dev DB `savepoint_test` on container `savepoint-db-1`: 312,483 IGDB `GameWork` + 150 Wikidata works + demo accounts + seeded `LibraryEntry` `[VERIFIED: igdb-catalogue-freeze.md:89-90]`. `GameAlias`: only Wikidata-sourced rows exist (~hundreds) — IGDB works have none `[VERIFIED: import_igdb_catalogue.py — no GameAlias write]`. `GameWork.total_rating`: populated only where IGDB returned it; coverage **unmeasured** `[VERIFIED: igdb-catalogue-freeze.md — no rating row]`. `GameWork.summary`, `rating`, `rating_count`, franchise, developer: **not imported at all** (`GAME_FIELDS` `[VERIFIED: igdb.py:36-39]`). `in_corpus` / `corpus_version` columns: do not exist yet. | Wave 0: measure rating coverage against the snapshot dump. Then: migration (add columns) → re-import with expanded `GAME_FIELDS` (data refresh across all rows, ~50 min IGDB pull) → `backfill_game_aliases` (data backfill, ~minutes, offline) → `govern_corpus` (compute `in_corpus`) → `snapshot_corpus_ratings` (populate `CorpusRatingSnapshot`). Each is a distinct task. |
| **Live service config** | IGDB app (Twitch OAuth `client_credentials`) — `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET`, env-only, ~57-day token `[VERIFIED: igdb-api-probe.md:14-20; igdb.py:82-87]`. No other external service holds phase-relevant state (no n8n, no Datadog, no scheduler). If RAWG adopted: a RAWG API key, env-only, `RAWG_API_KEY`. | No migration of external config. Confirm IGDB credentials are still valid before the re-import task (a token probe). If RAWG: add `RAWG_API_KEY` to the env contract + `.env.example` + deployment docs, never committed. |
| **OS-registered state** | None. The IGDB import is a manual `python manage.py import_igdb_catalogue` invocation — no cron, no Task Scheduler, no pm2. The 01.1 "background load" was a one-time manual run `[VERIFIED: STATE.md:140-141, igdb-catalogue-freeze.md:79-95]`. | None — state explicitly clear. New commands are also manual/offline; do not register any scheduler. |
| **Secrets / env vars** | `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET` (unchanged). `DEMO_ACCOUNTS` JSON seed contract for `bootstrap_demo_accounts` `[VERIFIED: bootstrap_demo_accounts.py:55, 80-137]`. `DATABASE_URL`. | Synthetic users (Pattern 5) should NOT go through `DEMO_ACCOUNTS` env (200 entries is unmanageable) — `generate_synthetic_users` takes a `--seed` and archetype config file, writes `DemoAccountIdentity` rows with `seed_key="synthetic-<archetype>-<n>"` directly. If RAWG: `RAWG_API_KEY` added to the env contract. No secret value is ever logged (importer redaction precedent). |
| **Build artifacts / snapshots** | `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (93 MB, gitignored, `pg_restore`-able) `[VERIFIED: igdb-catalogue-freeze.md:95; CONVENTIONS.md §3 "Sin datos en bloque de IGDB en Git"]`. `docs/verification/igdb-catalogue-freeze.sample.json` (sampled manifest). | The `.dump` goes **stale** the moment the re-import adds `rating`/`summary`/aliases/`in_corpus`. Regenerate it (`pg_dump -Fc`, keep gitignored) after governance + snapshot, and update `igdb-catalogue-freeze.md`'s "Carga en la BD de desarrollo persistente" section + add a rating-coverage row. `deferred-items.md` from 01.1 (nav <430px, ficha escasa) is addressed by UI-SPEC P6 / §3. |

**Nothing found in category "OS-registered state":** confirmed — no scheduled job, service registration, or saved process name references any phase artifact; all import/governance/evaluation entry points are manual offline management commands (verified by reading every `management/commands/*.py` under catalogue/accounts/recommendations and by `STATE.md`'s description of the 01.1 load as a one-time manual background run).

## Common Pitfalls

### Pitfall 1: Assuming the importer never populated ratings

**What goes wrong:** A plan task titled "make the importer populate ratings" that only adds a mapping — when `total_rating` is *already* requested and mapped `[VERIFIED: igdb.py:38; import_igdb_catalogue.py:127-130,275]`.
**Why it happens:** D-05 phrases it as "el importador no puebla ningún rating"; the author saw empty pills.
**How to avoid:** First measure (`total_rating IS NOT NULL` count over the IGDB works and over a trial governed set) against the on-disk dump. The real gaps are (a) the *user* field `rating`/`rating_count` is never requested, and (b) genuine sparsity. Frame tasks as "add `rating,rating_count,total_rating_count` to `GAME_FIELDS` + map + snapshot" and "measure and report coverage (DATA-03)".
**Warning signs:** A task that changes `_upsert` mapping but not `GAME_FIELDS`.

### Pitfall 2: RAWG scoped like IGDB

**What goes wrong:** Planning a full 300k RAWG pass. RAWG's free tier is **20,000 requests/month** with an explicit **no-redistribution** clause and a mandatory **backlink on every page** using RAWG data `[CITED: rawg.io/tos_api, rawg.io/apidocs — "up to 20,000 requests per month"; "attribute RAWG as the source … add an active hyperlink from every page where the data of RAWG is used"; "No data redistribution"]`. A full catalogue pass would take ~16 months of quota or a paid plan; it also adds a UI obligation (backlink) IGDB does not require.
**Why it happens:** IGDB's terms are unusually permissive (no monthly cap, store-and-serve encouraged) so RAWG feels equivalent.
**How to avoid:** Gate RAWG on measured IGDB governed-corpus coverage (D-05/D-06). If adopted: allowlist games only (~tens of thousands, still multi-month at 20k/mo — so a bounded top-N-by-`rating_count` subset, or accept a slow multi-month enrichment), its own ADR-008 section, and a persistent RAWG backlink in the footer/sources page. Prefer "document the IGDB coverage number and accept it" unless the author explicitly wants RAWG.
**Warning signs:** A RAWG task with no request-budget arithmetic; a UI task list with no RAWG backlink.

### Pitfall 3: Multi-select AND joins without `distinct()`

**What goes wrong:** `qs.filter(genres__slug="rpg").filter(genres__slug="strategy")` without `.distinct()` returns duplicate `GameWork` rows (one per matching join row), inflating counts and pagination.
**Why it happens:** The current single-value `_apply_filters` sets `joined` and calls `.distinct()` once `[VERIFIED: search.py:180-181]`; it is easy to miss that each chained genre filter adds a join.
**How to avoid:** Keep the `joined` flag; always `.distinct()` when any facet joined. Test with a work that has 3 genres and a 2-genre AND query — expect it once.
**Warning signs:** Facet count != number of cards rendered.

### Pitfall 4: `corpus_version` drift between snapshot and governed view

**What goes wrong:** The recommender reads `CorpusRatingSnapshot` for `corpus_version="2026.09.1"` but `governed_works()` for whatever `GameWork.corpus_version` currently is, after a second `govern_corpus` run bumped it — silent mismatch, some works have no snapshot.
**Why it happens:** Two places store the version.
**How to avoid:** A single `ACTIVE_CORPUS_VERSION` resolved from one place (a `CorpusVersion` metadata row with an `is_active` flag, or a settings constant bumped deliberately). The harness takes `--corpus-version` explicitly and refuses if snapshot coverage over the governed set is < 100%.
**Warning signs:** Recommender results that silently shrink after a re-governance.

### Pitfall 5: Synthetic users contaminating the popularity baseline

**What goes wrong:** `generate_synthetic_users` writes `DemoAccountIdentity` rows → `rank_popularity_v1` counts their ~200 libraries → the "Populares en la demo" shelf on the public home is now driven by synthetic archetypes, not the hand-seeded demo accounts.
**Why it happens:** `rank_popularity_v1` includes any `user__demo_identity__isnull=False` `[VERIFIED: library/popularity.py:44-49]`, and synthetic users get a `DemoAccountIdentity`.
**How to avoid:** Either give synthetic users a distinct marker (`marker="synthetic-eval-user"` instead of `SIMULATED_ACCOUNT_MARKER`) and exclude that marker from `rank_popularity_v1`, or add an `is_evaluation_fixture` boolean and exclude it. Decide before generating. Document in ADR-007's sibling / the protocol doc.
**Warning signs:** The home popularity shelf changes after running the synthetic-user command.

### Pitfall 6: Leave-one-out with the wrong candidate set

**What goes wrong:** Ranking the held-out item against a candidate set that still contains the user's *other* library items, or against the ungoverned 312k catalogue — either inflates or destroys the metrics and breaks EVAL-01's "same candidates".
**Why it happens:** D-18's "el ítem retirado se reincorpora al conjunto de candidatos" is easy to implement as "add it back to the full catalogue".
**How to avoid:** Candidate set = `governed_works(corpus_version)` − `{user's remaining library}` + `{held-out item}`, identical for every algorithm. Freeze the per-user candidate id list in the split manifest and hash it.
**Warning signs:** Different algorithms seeing different candidate counts for the same user.

## Code Examples

### Existing DTO grammar to extend (do not diverge)

```python
# Source: apps/api/recommendations/genre_heuristic.py:245-254 (read verbatim this session)
return {
    "algorithm_id": ALGORITHM_ID,
    "generated_at": generated_at.isoformat(),
    "input_snapshot_sha256": _fingerprint(taste_weights, [(i["slug"], i["score"]) for i in results]),
    "insufficient_history": False,
    "limitation": _LIMITATION,
    "results": results,
}
# Content variant ADDS: "feature_set_version", "corpus_version", "snapshot_sha256",
# and per-item "contributions", "rating_term", "rating_term_is_fallback".
```

### Anti-contamination filter to reuse for the D-09 blended rating

```python
# Source: apps/api/library/popularity.py:44-49 (read verbatim this session)
entries = list(
    LibraryEntry.objects.filter(
        Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False),
        updated_at__lte=cutoff,
    ).values("work_id", "current_status", "rating_half_steps")
)
# The live display_rating uses a filter like this (author fixes whether self-registered
# users are also included). The research snapshot uses NONE of it — external only.
```

### Multi-select parse (backend)

```python
# Extends apps/api/catalogue/search.py:98-153 (parse_catalogue_query, read this session)
genres = tuple(dict.fromkeys(s.strip() for s in params.getlist("genre") if s.strip()))
platforms = tuple(dict.fromkeys(s.strip() for s in params.getlist("platform") if s.strip()))
# DRF: request.query_params.getlist("genre"); Django QueryDict also supports .getlist
```

### Cosine (stdlib, no numpy)

```python
import math
def cosine(p: dict[str, float], v: dict[str, float]) -> float:
    if not p or not v:
        return 0.0
    num = math.fsum(p[k] * v[k] for k in p.keys() & v.keys())
    dp = math.sqrt(math.fsum(x * x for x in p.values()))
    dv = math.sqrt(math.fsum(x * x for x in v.values()))
    return num / (dp * dv) if dp and dv else 0.0
```

### nDCG@k (binary relevance, hand-written — unit-test this)

```python
import math
def ndcg_at_k(ranked_ids: list, relevant: set, k: int) -> float:
    dcg = sum(1.0 / math.log2(i + 2) for i, wid in enumerate(ranked_ids[:k]) if wid in relevant)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0
```

### IGDB Apicalypse field list after this phase's change

```
# apps/api/catalogue/igdb.py GAME_FIELDS  (current + additions)
id,name,slug,url,first_release_date,
total_rating,total_rating_count,rating,rating_count,
summary,
genres.id,genres.name,
platforms.id,platforms.name,
alternative_names.name,
franchises.name,collections.name,
involved_companies.company.name,involved_companies.developer,
cover.image_id
# Still ONE request per page via dot-expansion (no N+1). Confirm every path
# resolves against a live call before committing (01.1 pattern).
```

## State of the Art

| Old approach (in this repo / common) | Current approach for this phase | Why |
|---|---|---|
| Search over `GameAlias` only, aliases created solely by the Wikidata importer | Aliases created by every importer + a one-off backfill | 312k works had ~0 aliases → search near-dead. `[VERIFIED]` |
| Single-value `?genre=`/`?platform=` (`sp.get`) | Repeated params + `getlist`, genres AND / platforms OR | UI-SPEC P1; standard on Backloggd/OpenCritic/Steam (01.1 State-of-the-Art). |
| `GameWork.total_rating` (blended user+critic) as *the* rating | `rating`/`rating_count` (IGDB **user** rating) snapshotted per `corpus_version`; `total_rating` kept only as the live product number | D-05 prefers user ratings; `total_rating` = "Average rating based on both IGDB user and external critic scores" `[VERIFIED: IGDB type docs]`. |
| `IgdbImportRun` freeze = covers/genres/platforms/year | + per-field coverage incl. rating, + exclusion-reason histogram over the governed view | DATA-03 requires a quality/missing-fields report. |
| `rank_genre_taste_v1` = frequency count (product feature) | `content-cbf-*` = feature-vector cosine + rating term + 3 combination modes, evaluated under a frozen protocol | REC-03; this IS the thesis's first algorithmic contribution, unlike the 01.1 heuristic (ADR-007 "Frontera"). |
| LLM user simulators (2024–2026 RecSys papers) | Seeded parametric archetype draws | Reproducibility (EVAL-09), no external service, AGENT-04. `[CITED: WebSearch]` |
| IGDB/Platform `category` enum | `platform_type` (category deprecated); curated slug allowlist regardless | `[VERIFIED: IGDB type docs — "@deprecated Use platform_type instead"]` + D-01. |

**Deprecated / outdated:**
- IGDB `Game.category` and `Platform.category` enums — both marked `@deprecated` in IGDB's own docs (use `game_type` / `platform_type`); `game_type` already used by the importer `[VERIFIED: igdb-api-probe.md:28; import_igdb_catalogue.py:84]`.
- IGDB `Game.follows` — "@deprecated - To be removed" `[VERIFIED: IGDB type docs]`.
- RAWG for bulk catalogue use — 20k/mo cap makes it a *targeted* enrichment source at best `[CITED: rawg.io/tos_api]`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Full-catalogue IGDB `total_rating` coverage is low (~5–20 %); governed-subset coverage is materially higher. | Pattern 2 | Drives the D-05/D-06 RAWG decision. **Mitigated:** Wave-0 measurement task against the on-disk dump makes this a number, not an assumption, before the RAWG decision. |
| A2 | IGDB platform ids: PlayStation 5 = 167, Xbox Series X\|S = 169. | Pattern 1 | `govern_corpus` would silently exclude PS5/Series games. **Mitigated:** live `POST /v4/platforms` probe (credentials on hand) resolves the full allowlist id/slug set before governance; ids ≤166 are `[CITED]` from a community gist and also need a probe confirm. |
| A3 | IGDB exposes `franchises.name` / `collections.name` and `involved_companies.company.name` + `involved_companies.developer` with usable coverage over the governed corpus. | Pattern 5 (D-11) | Franchise/developer features would be mostly empty. **Mitigated:** D-11 says start with genres+rating (guaranteed) and add the rest by measured coverage; a Wave-1 probe + coverage count gates their inclusion. |
| A4 | Pure-Python (no numpy) is fast enough for 24 grid configs × ~200 users × LOO over ≤~150k governed works, as an offline command. | Standard Stack | If the harness run takes hours, adopt `numpy` (behind the dependency gate). Low risk: sparse vectors, ~10 nonzeros each; a full user-vs-corpus cosine pass is ~150k cheap dict ops. |
| A5 | The D-09 live blended rating counts demo + synthetic + self-registered users (or a documented subset); the research snapshot counts none of them. | Pattern 2 | Wrong split → either contaminated research data or a "dead" product number. **Needs author confirmation in discuss/plan** — D-09 explicitly leaves the composition to research/planner + author. |
| A6 | Persisting ~200 synthetic users as `DemoAccountIdentity` rows with a distinct non-`SIMULATED_ACCOUNT_MARKER` marker keeps them out of `rank_popularity_v1`. | Pattern 5 / Pitfall 5 | Home popularity shelf contamination. **Mitigated:** explicit marker choice + a `rank_popularity_v1` exclusion, decided before generation. |
| A7 | The persistent dev DB (`savepoint_test`) still holds the 2026-09-06 import and the `.dump` is restorable. | Runtime State Inventory | Re-import from IGDB (~50 min) if not. Low risk — documented in `igdb-catalogue-freeze.md`. |
| A8 | RAWG `rating` is 0–5 user average, `ratings_count` the count, `metacritic` the critic score. | D-05 / Pattern 2 | Field-mapping rework. `[CITED: rawg.io/apidocs mentions "average ratings" and "Metacritic ratings"; the exact `rating`/`rating_top`/`ratings`/`ratings_count` shape is from RAWG API training knowledge, not re-read from the schema this session]` — confirm against `api.rawg.io/docs` before writing `rawg.py`. |

## Open Questions (RESOLVED)

1. **RAWG in or out this phase?**
   - Known: IGDB `rating`/`rating_count` will be imported; RAWG terms are harsh (20k/mo, backlink, no redistribution).
   - Unclear: whether measured IGDB governed-corpus user-rating coverage is low enough to justify RAWG's cost (second provenance chain, ADR-008 section, persistent backlink).
   - RESOLVED: closed by the blocking-human `checkpoint:decision` in **02-02 Task 3** — IGDB coverage is measured in 02-02 Task 2, the number is put to the author, and the author picks `igdb-only` (document the coverage per D-06) or `add-rawg` (bounded top-N-by-`rating_count` RAWG subset, its own ADR-008 section, footer backlink, planned as 02-02b). In the `igdb-only` branch DATA-07 is satisfied by a forward-looking tie-break rule written into ADR-008 by 02-13 Task 3 — no reconciliation code or `test_rawg_reconcile.py` this phase.

2. **`numpy` now or in Phase 3?**
   - Known: STACK blesses `numpy 2.5.2` for exactly this; the project has kept to 5 deps and pure-Python recommenders.
   - RESOLVED: closed by the blocking `checkpoint:decision` in **02-10 Task 1** — default is pure-Python for Phase 2 (RESEARCH-recommended); the author may pick `adopt-numpy`, which triggers the full dependency gate (legitimacy `checkpoint:human-verify` + `uv add numpy==<pinned>` + `dependency-legitimacy.md` row + `check-dependencies.ps1` row + `agent-ledger.jsonl` entry + ADR-008 line) carved out as its own commit before 02-10 Tasks 2–3.

3. **D-09 live-rating composition (weights + which accounts count).**
   - Unclear by design (D-09 delegates it). Needs an author decision: external-vs-local weight, and self-registered-only vs including demo/synthetic.
   - RESOLVED: fixed in **02-05 `<flagged_assumptions>`** and its `must_haves` — `display_rating` is a read-time confidence-weighted blend of the external value and the mean `LibraryEntry.rating_half_steps` (×10) restricted to the same account set as `rank_popularity_v1`; the `CorpusRatingSnapshot` does not participate (external-only, frozen). The executor surfaces the assumption for author confirmation during 02-05.

4. **Franchise / developer as first-class entities or denormalised slugs?**
   - `CAT-05` (franchises/developers/publishers as entities) is Phase 6. This phase needs only a feature key.
   - RESOLVED: fixed in **02-10 Task 3** — denormalised `franchise:{slug}` / `developer:{slug}` feature keys inside the `WorkFeatureVector` cache, emitted only when measured coverage over the governed view clears a documented threshold (D-11). No `Franchise` / `Developer` models this phase (stays inside CAT-05's Phase 6 boundary).

5. **Number of tuning-grid configs and the exact ≤24 grid.**
   - D-21 caps it at 24, declared before running. The grid must be in `protocol.json` before any run.
   - RESOLVED: ratified in the **02-08 Task 1 `checkpoint:decision`** and frozen into `protocol.json` by 02-08 Task 2 — proposed grid is ~18 configs (`weighted_sum` (w1,w2) ∈ {(0.7,0.3),(0.5,0.5),(0.3,0.7)} × {genres+rating, +platform, +franchise/dev} = 9; `multiplicative` × 3 feature sets = 3; `two_stage` band counts {3,5} × 3 feature sets = 6), `len(grid) > 24` → `ProtocolError`.

6. **Cold-start threshold N.**
   - RESOLVED: fixed at `< 3` genre-bearing library entries in **02-11** (`must_haves` truth + `rank_content_v1` cold-start wrapper + `test_content.py` cases), aligned with the D-20 cold-start cohort of 1–3 items.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| IGDB app credentials (`IGDB_CLIENT_ID`/`SECRET`) | Re-import with new fields; platform-id probe; rating fields | ✓ (used in 01.1) `[VERIFIED: igdb-api-probe.md]` | Twitch OAuth `client_credentials`, ~57-day token | None — blocks the ratings + platform-allowlist tracks. Re-verify token before the re-import task. |
| Persistent dev DB `savepoint_test` + `data/snapshots/…-20260906.dump` | Coverage measurement; governance; harness | ✓ (assumed present) `[VERIFIED: igdb-catalogue-freeze.md:81-95]` | Re-import from IGDB (~50 min) |
| PostgreSQL 18 + `pg_trgm` + GIN trigram index | Search backfill, alias index health | ✓ (`catalogue_alias_trgm_gin` exists) `[VERIFIED: catalogue/models.py:149-151]` | — |
| `requests==2.34.2` | IGDB (and optional RAWG) HTTP | ✓ `[VERIFIED: pyproject.toml:10]` | — |
| `numpy` / `scikit-learn` / `scipy` | Only if the vectorised harness path is chosen | ✗ (not in `pyproject.toml`) `[VERIFIED: pyproject.toml:6-12]` | Pure-Python stdlib implementation (recommended) |
| RAWG API key | Only if RAWG adopted | ✗ (not registered) | Skip RAWG; document IGDB coverage (D-06 "sin suelo de cobertura duro") |
| Node/pnpm + Playwright + axe-core | UI pass verification (QUAL-05) | ✓ (01.1 e2e suite exists: `e2e/a11y.spec.ts`) `[VERIFIED: repo listing this session]` | — |

**Missing with no fallback:** none that block the core phase — IGDB credentials exist; the only hard external need (IGDB) is available.
**Missing with fallback:** `numpy` (→ pure Python), RAWG key (→ IGDB-only + documented coverage).

## Validation Architecture

> `workflow.nyquist_validation = true` `[VERIFIED: .planning/config.json:24]` — this section is in scope.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-django 4.14.0 (backend) `[VERIFIED: pyproject.toml:16-18]`; Vitest (frontend, `apps/web/vitest.config.ts`); Playwright 1.62.x (e2e, `playwright.config.ts`) `[VERIFIED: repo listing]` |
| Config file | `apps/api/pytest.ini` (`DJANGO_SETTINGS_MODULE=config.settings`, `testpaths=.`, `python_files=test_*.py`) `[VERIFIED: apps/api/pytest.ini]`; `apps/web/vitest.config.ts`; `playwright.config.ts` |
| Quick run command | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue apps/api/recommendations apps/api/evaluation -x` |
| Full suite command | `docker compose -f infra/compose.yaml run --rm api pytest` + `pnpm --dir apps/web run test` + `pnpm exec playwright test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-03 | `govern_corpus` applies D-03 rules; emits checksum + dictionary + coverage report; idempotent (re-run → same checksum) | integration | `pytest apps/api/catalogue/tests/test_govern_corpus.py -x` | ❌ Wave 0 |
| DATA-05/06 | `CorpusRatingSnapshot` insert-only; re-import updates live `GameWork` not snapshot | integration | `pytest apps/api/catalogue/tests/test_rating_snapshot.py -x` | ❌ Wave 0 |
| DATA-07 | IGDB↔RAWG reconciliation: exact slug then title+year; unmatched dropped+counted | unit | `pytest apps/api/catalogue/tests/test_rawg_reconcile.py -x` | ❌ Wave 0 (only if RAWG in scope) |
| CAT-02 | Multi-select: genres AND, platforms OR, per-value chips, unknown slug ignored, `distinct()` | integration | `pytest apps/api/catalogue/tests/test_search.py -x` (extend) | ✅ extend `apps/api/catalogue/tests/test_search.py` |
| CAT-02 (web) | `parseFilters` reads `getAll`; `buildQuery` repeats; `countActiveFilters` counts each value | unit | `pnpm --dir apps/web run test` (extend catalogue-filters tests) | ✅ likely (`apps/web/lib/catalogue-filters.ts` has tests referenced) — confirm |
| (search bug) | `backfill_game_aliases` creates primary+title_en+alt-name aliases; idempotent; search then finds IGDB works | integration | `pytest apps/api/catalogue/tests/test_alias_backfill.py -x` | ❌ Wave 0 |
| REC-01 | `rank_random_v1` seeded, deterministic, excludes library, governed candidates only | unit | `pytest apps/api/recommendations/tests/test_baselines.py -x` | ❌ Wave 0 |
| REC-03/08/09 | Each `content-cbf-*` variant: cosine, combination mode, contribution table, DTO carries feature/corpus/snapshot versions | integration | `pytest apps/api/recommendations/tests/test_content.py -x` | ❌ Wave 0 |
| REC-06 | `< 3` genre-bearing entries → `insufficient_history` + non-empty cold-start fallback | integration | `pytest apps/api/recommendations/tests/test_content.py -k cold_start -x` | ❌ Wave 0 |
| REC-07 | Every consumed work excluded from every variant | unit | `pytest apps/api/recommendations/tests/test_content.py -k exclude -x` | ❌ Wave 0 |
| EVAL-09 | `generate_synthetic_users`: ~8 archetypes × ~25 + cold-start cohort; same seed → identical histories; validation report | integration | `pytest apps/api/evaluation/tests/test_synthetic.py -x` | ❌ Wave 0 |
| EVAL-01/02/03 | Frozen `protocol.json` (grid ≤24, K, relevance, LOO); same candidate set across algorithms; test runs once; refuses tuning-on-test | integration | `pytest apps/api/evaluation/tests/test_protocol.py apps/api/evaluation/tests/test_runner.py -x` | ❌ Wave 0 |
| EVAL (metrics) | P@K, R@K, nDCG@K, MAP@K match known-answer fixtures at K∈{5,10,20} | unit | `pytest apps/api/evaluation/tests/test_metrics.py -x` | ❌ Wave 0 |
| D-24 | "Novedades": `in_corpus` + `first_release_date` in last 6 months, desc, `canonical_slug` tie, ≤20, hidden if 0 | integration | `pytest apps/api/catalogue/tests/test_new_releases.py -x` | ❌ Wave 0 |
| D-15 | "Para tus juegos": DLC of owned base games; DLC excluded from governed catalogue but queryable here | integration | `pytest apps/api/catalogue/tests/test_owned_dlc.py -x` | ❌ Wave 0 |
| QUAL-05 | Catalogue/detail/recommendations/home pass axe (dark+light), 44px targets, focus ring, 400%/320px reflow, EN/ES parity | e2e | `pnpm exec playwright test e2e/a11y.spec.ts` (extend) | ✅ extend `e2e/a11y.spec.ts` |

### Sampling Rate

- **Per task commit:** scoped quick pytest/vitest for the touched app.
- **Per wave merge:** full backend + frontend suite.
- **Phase gate:** full suite + Playwright green before `/gsd-verify-work`, **plus** a manual review of: (a) `govern_corpus` re-run producing an identical checksum, (b) an interrupt-and-resume of the re-import against a throwaway DB, (c) the synthetic-user validation report against its archetype spec, (d) one full `run_evaluation` producing a complete artifact JSON with content variants beating random on nDCG@10.

### Wave 0 Gaps

- [ ] `apps/api/catalogue/tests/test_govern_corpus.py` — DATA-03
- [ ] `apps/api/catalogue/tests/test_rating_snapshot.py` — DATA-05/06
- [ ] `apps/api/catalogue/tests/test_alias_backfill.py` — search bug
- [ ] `apps/api/catalogue/tests/test_new_releases.py`, `test_owned_dlc.py` — D-24, D-15
- [ ] `apps/api/catalogue/tests/test_rawg_reconcile.py` — DATA-07 (only if RAWG)
- [ ] `apps/api/recommendations/tests/test_baselines.py` — REC-01
- [ ] `apps/api/recommendations/tests/test_content.py` — REC-03/06/07/08/09
- [ ] `apps/api/evaluation/` app + `tests/{test_protocol,test_synthetic,test_splits,test_metrics,test_runner}.py` — EVAL-01/02/03/09
- [ ] `docs/methodology/protocol.json` + a `test_protocol.py` schema/consistency check
- [ ] Extend `apps/api/catalogue/tests/test_search.py` (multi-select), `e2e/a11y.spec.ts` (new surfaces), `apps/web` catalogue-filters unit tests (array params)
- [ ] Add `evaluation` to `INSTALLED_APPS`; confirm `pytest.ini` `testpaths=.` picks up `apps/api/evaluation/tests/`

## Security Domain

> `security_enforcement = true`, `security_asvs_level = 1`, `security_block_on = "high"` `[VERIFIED: .planning/config.json:47-49]`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (no new auth surface) | Content recs endpoint reuses `IsAuthenticated` like `RecommendationsView` `[VERIFIED: apps/api/recommendations/views.py:42]`. |
| V3 Session Management | no | Unchanged. |
| V4 Access Control | **yes** | `ContentRecsView` MUST be `IsAuthenticated` and `request.user`-only (no target-user param) — mirror ADR-007 §7 and the allowlist-echo response projection `[VERIFIED: views.py:19-65]`. `OwnedGamesDlcView` similarly owner-scoped. The live blended rating must not expose which specific SavePoint users rated a work (aggregate count only). |
| V5 Input Validation | **yes** | Multi-select `genre`/`platform` values: allowlist-resolve against `Genre`/`Platform` slugs, unknown → dropped (never interpolated) — the existing `parse_catalogue_query` discipline extended to lists `[VERIFIED: search.py:98-153]`. `algorithm_id` on the content-recs endpoint: strict membership in `ALGORITHM_REGISTRY`, unknown → bounded 400 (never used to build a query or import a module). `limit` clamped (existing pattern). Cap the number of repeated `genre`/`platform` params (e.g. ≤ 20) to bound join fan-out (T-01.1-06 aggregate-filter DoS precedent). |
| V6 Cryptography | no | `sha256` fingerprints only, no secrets. |
| V11 / API (SSRF, outbound) | **yes** | IGDB re-import and optional RAWG client: outbound only, fixed hosts (`api.igdb.com`, `id.twitch.tv`, `api.rawg.io`), offline management commands, never a request path. Reuse `catalogue/igdb.py`'s `redact()` for every log line / exception / evidence string; `raise ... from None` to drop chained context `[VERIFIED: apps/api/catalogue/igdb.py:14-19, 55-60, 96-101]`. RAWG API key env-only, never logged. |
| V7 Errors & Logging | **yes** | New commands must not print credentials or connection strings (importer redaction precedent). Evidence JSON is non-sensitive aggregates + a 300-row sample only. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Multi-select filter join fan-out (many repeated `genre`/`platform`) → DoS | Denial of Service | Cap repeated params; keep `ScopedRateThrottle` on `GameListView` `[VERIFIED: apps/api/catalogue/views.py:43-44]`; `.distinct()` + bounded page size unchanged. |
| `algorithm_id` used to select a code path | Tampering / RCE-adjacent | Registry membership check only; never `importlib`/`getattr` on the value. |
| Content-recs endpoint leaking another user's taste | Information Disclosure | `request.user`-only, allowlist-echo response (ADR-007 §7 pattern). |
| Synthetic users polluting the public popularity baseline / public profiles | Information Disclosure / integrity of the demo | Distinct marker + `rank_popularity_v1` exclusion (Pitfall 5); synthetic accounts are `is_simulated=True` and clearly labelled (AUTH-02). |
| Live blended rating revealing individual SavePoint ratings | Information Disclosure / Privacy | Expose only the aggregate blended number + counts; never per-user rows; account-set restricted like `rank_popularity_v1`. |
| IGDB/RAWG secret in logs, evidence, or Git | Information Disclosure | `redact()` on every outbound string; env-only keys; `check-secrets.ps1` gate; no bulk data dump committed (`CONVENTIONS.md §3`). |
| Mutable API data silently rewriting a cited experiment | Tampering | `CorpusRatingSnapshot` insert-only per `corpus_version`; harness reads snapshot, never live `GameWork` (DATA-06). |

## Sources

### Primary (HIGH confidence) — in-repo, read verbatim this session

- `apps/api/catalogue/models.py` — `GameWork` (incl. `total_rating`, `first_release_date`, indexes), `Genre` (`igdb_id`), `Platform`, `GameRelease`, `GameAlias` (GIN trigram), `RelatedContent`, `SourceRecord`, `IgdbImportRun`, `AssetAttribution`.
- `apps/api/catalogue/igdb.py` — `GAME_FIELDS` (line 36-39), redaction, pacing, id-cursor client.
- `apps/api/catalogue/management/commands/import_igdb_catalogue.py` — `_normalize` maps `total_rating` (127-130), `_upsert` (240-337, no `GameAlias`), `_catalogue_checksum` (341-353), `_build_evidence` (355-418), platform/genre reconciliation on slug.
- `apps/api/catalogue/search.py` — `parse_catalogue_query`, `_apply_filters` (single-value), `_ordered_matching_work_ids` (alias-only), `SORT_ORDERS`, `_facets`, `_base_works`.
- `apps/api/catalogue/serializers.py` — `total_rating` exposed on card + detail.
- `apps/api/catalogue/normalization.py` — `normalize_title`.
- `apps/api/recommendations/genre_heuristic.py` — `_entry_weight`, `_STATUS_WEIGHTS`, `_fingerprint`, `_insufficient_history`, DTO shape, `ALGORITHM_ID`.
- `apps/api/recommendations/views.py` — `IsAuthenticated`, allowlist-echo projection.
- `apps/api/library/popularity.py` — demo-account restriction `Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)`.
- `apps/api/library/models.py` — `LibraryEntry.rating_half_steps` (1–10, null=unrated), `BacklogStatus`, `OwnedCopy`.
- `apps/api/accounts/models.py` — `DemoAccountIdentity`, `SIMULATED_ACCOUNT_MARKER`, `demo_identity_anchor_id`.
- `apps/api/accounts/management/commands/bootstrap_demo_accounts.py` — seed contract, advisory lock, validate-then-write.
- `apps/web/lib/catalogue-filters.ts` — current single-value `genre`/`platform`, `parseFilters`/`buildQuery`/`countActiveFilters`.
- `pyproject.toml` — deps (Django/DRF/gunicorn/psycopg/requests only; no numpy/scipy/sklearn); `requires-python = "==3.13.*"`.
- `.planning/config.json` — `nyquist_validation`, `security_enforcement`, ASVS L1.
- `docs/adr/ADR-006-igdb-source.md`, `docs/adr/ADR-007-genre-taste-heuristic.md`, `docs/verification/igdb-api-probe.md`, `docs/verification/igdb-catalogue-freeze.md` — read this session.

### Primary (HIGH confidence) — external, tool-verified

- IGDB API type definitions — `github.com/DmitryScaletta/igdb-api-types` `index.ts` (auto-generated from IGDB's own `api-docs.html`), fetched via `gh api` this session: verbatim `Game` rating-field doc comments (`rating` = "Average IGDB user rating", `rating_count`, `aggregated_rating` = "Rating based on external critic scores", `total_rating` = "Average rating based on both IGDB user and external critic scores", `total_rating_count`, `hypes` = "Number of follows a game gets before release", `follows` deprecated); `GameCategoryEnum` (main_game=0 … update=14); `PlatformCategoryEnum` (console=1, arcade=2, platform=3, operating_system=4, portable_console=5, computer=6) with `category` marked `@deprecated Use platform_type instead`.

### Secondary (MEDIUM confidence)

- `rawg.io/tos_api` + `rawg.io/apidocs` (WebFetch this session) — "up to 20,000 requests per month"; "attribute RAWG as the source of the data and/or images and add an active hyperlink from every page where the data of RAWG is used"; "No data redistribution"; free for commercial under 100K MAU / 500K pageviews.
- WebSearch synthesis — RecSys offline evaluation (leave-one-out, HR/nDCG for top-N; P@K/R@K/MAP/nDCG the standard accuracy+ranking set); content-based filtering pipeline (one-hot features → weighted-average user profile → cosine → rank); recent user-simulation literature is LLM-centric (RecUserSim, SimUSER, RecoWorld) — the classical seeded parametric persona method is the reproducible baseline.

### Tertiary (LOW confidence — must verify before use)

- IGDB platform ids ≤ 166 — community gist `ahmed-abdelazim/b533b443388baaafab3fc377e71e0109` (~2020). PS5=167 / Xbox Series=169 — training memory. **Confirm all via a live `POST /v4/platforms` probe.**
- IGDB `total_rating` / `rating` coverage over the catalogue — no public number found; **measure against the on-disk dump in Wave 0.**
- RAWG games-endpoint field shape (`rating` 0–5, `rating_top`, `ratings`, `ratings_count`, `metacritic`) — training knowledge; confirm against `api.rawg.io/docs` before writing `rawg.py`.

## Metadata

**Confidence breakdown:**
- Standard stack / "no new dep" recommendation: HIGH — grounded in `[VERIFIED]` reads of `pyproject.toml` + the existing pure-Python recommenders; the `numpy` alternative is `[CITED: AGENTS.md]` and flagged for author decision.
- Architecture patterns (governance, snapshot, multi-select, alias backfill, recommender, harness): HIGH for the in-repo integration points (every one `[VERIFIED: path:lines]`); MEDIUM for IGDB-field behaviour (verified against generated type docs, not a live call this session) and for platform ids (must probe).
- Ratings "causa a investigar": HIGH that `total_rating` is already requested/mapped/surfaced (`[VERIFIED]` three files); MEDIUM-LOW on the *coverage* explanation — needs the Wave-0 measurement.
- Pitfalls: HIGH for in-repo ones; MEDIUM for RAWG terms (`[CITED]` from rawg.io, not legal advice).
- Synthetic users / evaluation protocol: MEDIUM — the classical parametric method is well-established but the concrete archetype set + grid need author ratification in the PLAN.

**Research date:** 2026-09-06
**Valid until:** 14 days for IGDB/RAWG specifics (re-probe platform ids + rating coverage + RAWG schema before implementing those tracks regardless); 30 days for the in-repo architecture findings (stable unless the codebase changes before planning).
