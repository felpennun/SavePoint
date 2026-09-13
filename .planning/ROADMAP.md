# Roadmap: SavePoint

## Overview

SavePoint begins with a three-day, publicly deployed vertical demonstration, then replaces demo shortcuts with governed data, a frozen evaluation contract, complete collection workflows, resilient enrichment, reproducible experiment infrastructure, and progressively stronger recommenders. The final phase exposes immutable evidence through an accessible research panel and hardens the demonstrator for thesis assessment. Every phase is an MVP vertical slice and must leave contemporaneous thesis and agent-methodology evidence; documentation is an acceptance condition throughout, not an end-only activity.

## Delivery Policy

- **Mode:** mvp for every initial phase.
- **Phase 1 deadline:** a visible public demonstration within three days.
- **Demo-grade boundary:** Phase 1 may use controlled seeded accounts, a small lawful local catalogue, a simple popularity recommender, and narrowly scoped administration. It may not use client-side secrets, unlawful data, mutable research inputs, or undocumented setup.
- **Hardening boundary:** Phases 2-7 expand data governance, evaluation validity, product depth, security, recovery, accessibility, and operational controls. Phase 1 is a coherent demonstrator, not evidence that these later guarantees are complete.
- **Roadmap revision (2026-09-06):** After the Phase 01.1 review the author folded the external-ratings enrichment, corpus governance, the frozen evaluation protocol, and a first ratings-aware recommender into a single larger Phase 2, and compressed the former experiment-harness and content-recommendation phases into one. Former phases 3 and 4 (collection workflows, public discovery) shift to 5 and 6; the former hardening phase becomes 7. Rationale and the requirement re-mapping are recorded in this file's git history and in `.planning/phases/`.
- **Continuous evidence:** each phase records decisions, alternatives, tests, provenance, limitations, agent roles/prompts/configuration, automated verification, and explicit author decisions relevant to its scope.

## Phases

- [x] **Phase 1: Three-Day Public Demo Slice** - Deploy a lawful, locally reproducible controlled demo with catalogue, backlog, rating, inventory, public profile, and popularity recommendations. (completed 2026-09-05)
- [x] **Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender** - Prune the corpus to a governed platform/quality allowlist (Steam included), ingest external ratings with provenance and experiment isolation, fix tolerant search over the real corpus, add multi-select filters and a product-grade UI pass, freeze the simulation-aware evaluation protocol, and ship a first ratings-aware content recommender evaluated under it. Accepted by the author on 2026-09-08; simulated limitations retained explicitly.
- [x] **Phase 3: Explainable Content Recommenders and Baseline Comparison** - Run the frozen harness over random/popularity baselines and content recommenders with cold-start routing, exclusions, deterministic explanations, the full metric suite, cohort reporting, and independently recalculable artifacts. Completed 2026-09-12 with the multi-seed limitation documented.
- [x] **Phase 4: Collaborative and Hybrid Comparison** - Compare collaborative and hybrid methods under the already-frozen protocol and document bounded conclusions. Completed 2026-09-12 with the multi-seed limitation documented.
- [x] **Phase 5: Complete Collection Workflows and Portability** - Complete profiles, comments, lists, copy details, and safe deterministic versioned CSV export. (completed 2026-09-13)
- [x] **Phase 6: Public Discovery and Resilient Enrichment** - Add public projections, catalogue discovery, and shareable public views without contaminating research data. (completed 2026-09-13)
- [ ] **Phase 7: Research Panel, Hardening, and Evidence Freeze** - Present thesis-ready comparisons and finish administration, security, recovery, accessibility, and reproducibility gates.

## Phase Details

### Phase 1: Three-Day Public Demo Slice

**Mode:** mvp
**Goal**: A tribunal visitor can use a visible, lawful SavePoint vertical slice online within three days, while the same controlled demo starts reproducibly offline.
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, PROF-02, CAT-01, CAT-03, CAT-04, CAT-06, LIB-01, LIB-02, INV-01, INV-02, INV-05, DATA-01, DATA-02, REC-02, SEC-02, OPS-01, OPS-02, OPS-03, QUAL-03, DOC-01, AGENT-01, AGENT-02, AGENT-03
**Success Criteria** (what must be TRUE):

  1. A visitor can open the public deployment, sign into a controlled account, search a small lawful local catalogue, and inspect a game with source information even when external enrichment is unavailable.
  2. A signed-in user can change backlog status, rate a game, and register multiple physical or digital copies while private ownership details remain absent from the public profile.
  3. An authorised visitor can open a public profile and see a simple popularity recommendation produced from the demo data.
  4. A clean machine can start the same demo from documented, pinned instructions without Internet/API dependency, and no secret appears in Git, browser assets, logs, images, or public artifacts.
  5. The demo is keyboard-usable and responsive at desktop/mobile widths, and its source/legal record, architecture rationale, agent inputs/outputs, verification, limitations, and author decisions are captured as thesis evidence.

**Plans**: 16/16 plans executed

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Aprobar dependencias y resolver locks

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Crear Compose inicial y runners no vacíos

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Verificar scaffold Django/Next/PostgreSQL
- [x] 01-05-PLAN.md — Adquirir y congelar corpus/assets

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-15-PLAN.md — Crear cuenta demo rotatoria antes del E2E de login

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-04-PLAN.md — Probar sesión→estado como trazador vertical
- [x] 01-06-PLAN.md — Importar y exponer catálogo lawful offline

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 01-07-PLAN.md — Persistir rating/copias, perfil y popularidad
- [x] 01-08-PLAN.md — Crear shell, tokens e i18n

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 01-16-PLAN.md — Cargar interacciones deterministas después del esquema

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 01-09-PLAN.md — Integrar superficies y detalle

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 01-10-PLAN.md — Verificar accesibilidad y responsive

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 01-11-PLAN.md — Cerrar runtime y gate de secretos con ciclo de seed ordenado

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 01-12-PLAN.md — Elegir/provisionar PaaS y validar URL pública
- [x] 01-13-PLAN.md — Documentar arquitectura, datos y agentes

**Wave 12** *(blocked on Wave 11 completion)*

- [x] 01-14-PLAN.md — Firmar aceptación humana

**Cross-cutting constraints:**

- empty — explicit: Every collection surface has explicit zero/empty behavior and references localized Copywriting Contract rows where applicable.
- loading — explicit: Geometry-matched skeletons reserve layout; one polite status announces loading and skeletons are hidden from accessibility APIs.
- error — explicit: Scoped retry, value preservation, safe localized messages, and focus behavior are defined in the state matrices.
- populated — explicit: Required information hierarchy, result counts, ordering, provenance, and action placement are specified screen by screen.
- partial — explicit: Core local data remains visible; missing assets use lawful placeholders and failed secondary panels cannot blank the page.
- overflow — explicit: Adaptive grid, wrapping, bounded content width, mobile menu, and vertical copy rows prevent page-level horizontal overflow.
- zero-one-many — explicit: Zero copy/results language, singular/plural localized count handling, multiple owned copies, and paginated catalogue behavior are explicit.
- long-text — explicit: Titles wrap, prose reflows, cards clamp only redundant title previews, and acceptance includes 30% expansion plus 400% zoom.

**UI hint**: yes

### Phase 01.1: Real-Scale Catalogue and Product Experience (INSERTED)

**Goal:** The demo grows from a small curated 150-game corpus into a real-scale catalogue (hundreds of thousands of titles via IGDB) with a product-grade visual redesign, catalogue sorting/filtering, multiple working preloaded accounts, and a dedicated genre-based recommendations page -- author-requested immediately after Phase 1's sign-off, prioritized ahead of Phase 2's evaluation-protocol work.

**Author's priority order for this phase** (recorded 2026-09-05, from `docs/verification/phase-01-signoff.md`):

1. Mass catalogue import (IGDB) + interface redesign
2. Real login system with multiple preloaded accounts
3. Catalogue sorting/filtering and search filters
4. An independent recommendations page (by genre / user taste)

**Author's data-source decision:** IGDB, chosen over RAWG and scaling the existing Wikidata pipeline. Complete cover-image coverage across the full catalogue matters to the author and may be delivered incrementally after the initial import, without blocking the rest of this phase. Rationale to be elaborated in this phase's own ADR once planned (DATA-04).

**Requirements**: CAT-02, AUTH-02, DATA-04, REC-10, QUAL-05
**Depends on:** Phase 01
**Plans:** 10 plans

**Success Criteria** (what must be TRUE):

  1. A visitor can browse a real-scale IGDB-sourced catalogue (not the 150-game demo corpus), with its licence/attribution terms and dataset provenance documented the same way the Phase 1 corpus was.
  2. A visitor can sort and filter the catalogue by platform, genre, and other available metadata.
  3. Multiple distinct preloaded accounts can each sign in and out independently (not just the single Phase 1 demo account).
  4. The interface's visual density, typography, and imagery treatment read as a professional cataloguing product (author's reference points: Goodreads, OpenCritic), not a minimal utilitarian layout.
  5. A signed-in user can open a dedicated recommendations page showing genre-oriented suggestions reflecting their own recorded activity, distinct from the existing public popularity baseline.

Plans (execution order follows the author's locked D-01 -> D-02 -> D-03 -> D-04 priority):

- [x] 01.1-01-PLAN.md (Wave 1) — Approve and probe IGDB, then freeze the provider ADR and dependency pin — ADR-006, IGDB probe evidence, `requests==2.34.2` pinned (2026-09-05)
- [x] 01.1-02-PLAN.md (Wave 2) — Build resumable ingestion and prove a full-scale import on fresh PostgreSQL — merged 2026-09-05 (`507f876`); 312,463 primary works imported on a disposable DB, SIGKILL interrupt + resume + idempotent convergence proven, aggregate freeze evidence recorded. Persistent dev/Neon DB load is a follow-on.
- [x] 01.1-06-PLAN.md (Wave 3) — Approve and implement the product redesign milestone before account work — merged 2026-09-05 (`069f422`); UI-SPEC implemented across apps/web (tokens light+dark, ThemeToggle, Cristal brand, FilterBar catalogue, detail, recommendations + registration pages, collection/home/login), pnpm build + i18n parity green. Known stubs deferred to Plans 03/04/05/08.
- [x] 01.1-04-PLAN.md (Wave 4) — Add plural, clearly labeled simulated accounts — merged 2026-09-06; DemoAccountIdentity + bootstrap_demo_accounts (env-only DEMO_ACCOUNTS contract, idempotent, credential-redacted), 147 api tests pass.
- [x] 01.1-08-PLAN.md (Wave 5) — Add controlled functional registration without opening AUTH-03 — merged 2026-09-06; csrf_protect RegisterView, validate_password, ScopedRateThrottle 5/hour, session login; 163 api tests + web build green. AUTH-03 language absence test-enforced.
- [x] 01.1-03-PLAN.md (Wave 6) — Add validated catalogue filters, sorting, facets, and shareable controls — merged 2026-09-06; parse_catalogue_query allowlists platform/genre/year/min_rating + a 6-key sort set (canonical_slug tie-break, bounded 400), facet DTO no N+1, migration 0004 adds first_release_date/total_rating scalars + 4 indexes + backfill. FilterBar wired to live facets. 181 backend tests + web build green.
- [x] 01.1-05-PLAN.md (Wave 7) — Deliver deterministic personal genre recommendation service and API — merged 2026-09-06; rank_genre_taste_v1 (stateless heuristic, popularity.py weights + rating/10, canonical_slug tie-break, input_snapshot_sha256, distinct insufficient_history shape per D-09), RecommendationsView IsAuthenticated at /api/recommendations/genre-taste/ (limit [1,50]), ADR-007. 21 rec tests + 202 api regression pass.
- [x] 01.1-09-PLAN.md (Wave 8) — Wire the personalized page and authenticated navigation — merged 2026-09-06; getPersonalRecommendations -> /api/recommendations/genre-taste/, genre shelves + explanation + algorithm/limitation disclosure + signed-out/insufficient-history states, /recommendations nav link authenticated-only. Build + 16 web tests green.
- [x] 01.1-10-PLAN.md (Wave 9) — Produce complete Playwright, axe, viewport, and screenshot evidence — merged 2026-09-06; 41 Playwright tests + axe (zero critical/serious) across catalogue/detail/registration/recommendations desktop+mobile, 8 screenshot artifacts, phase-01.1-product-review.md. Rule 1 reflow fixes (.sp-field min-width:0 + AppShell header).
- [x] 01.1-07-PLAN.md (Wave 10) — Record the author's separate post-evidence product-quality verdict — 2026-09-06; conditional advance author approval (APPROVED all four D-07 surfaces desktop+mobile) recorded in phase-01.1-product-review.md against passing evidence; full live walkthrough + 3 cosmetic polish items deferred.

### Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender

**Mode:** mvp
**Goal**: A researcher can trust the governed corpus and its external ratings, a visitor gets working search and multi-select filtering over a product-grade catalogue, and a signed-in user receives a first ratings-aware recommendation produced under a frozen, simulation-aware evaluation protocol.
**Depends on**: Phase 01.1
**Requirements**: DATA-03, DATA-05, DATA-06, DATA-07, DATA-08, EVAL-01, EVAL-02, EVAL-03, EVAL-09, EVAL-10, REC-01, REC-03, REC-06, REC-07, REC-08, REC-09, DOC-02, DOC-04, AGENT-04
**Also refines** (owned by Phase 01.1, extended here without reassigning the ID): CAT-02 (multi-select genre and platform filtering), QUAL-05 (a further product-grade UI pass over catalogue, filters, and recommendations), AUTH-02 (the simulated accounts gain the parameterised, seed-reproducible scenario histories the evaluation protocol needs).
**Success Criteria** (what must be TRUE):

  1. A researcher can verify the governed corpus by its fixed checksum, data dictionary, and missing-data/quality report, produced by a documented platform and quality allowlist (Steam included) that excludes junk titles, independently of mutable enrichment.
  2. Every game that has one carries an external rating whose source and retrieval date are shown, stored so that a completed experiment can never be altered by later provider data, with deterministic identifier reconciliation and conflict rules.
  3. A visitor can find any governed game by an approximate title match and can narrow the catalogue by several genres and several platforms at once, over a catalogue whose density, typography, and imagery read as a product-grade cataloguing interface.
  4. The comparison protocol freezes relevance, K, users, candidate sets, exclusions, split manifests, metrics, seeds, tuning budget, and test isolation before any advanced recommender runs, and clearly labelled synthetic accounts regenerate from contrasting parameterised scenarios and independent seeds with identical histories and a validation report.
  5. A signed-in user receives a ranked recommendation from a first ratings-aware recommender that combines their own recorded genre affinity with the aggregate external ratings of comparable games, excludes already-consumed titles, shows a deterministic explanation grounded in persisted features, records the model, feature, and input-data versions of every published result, and gives a sparse-history user an explicit cold-start fallback instead of an empty list; a random baseline is available as the comparison floor.
  6. The phase records the dataset, API, data-model, and normalisation documentation, the protocol, metrics, and threats to validity, and the controls against leakage, hallucination, bias, error, and information exposure, plus the author decisions behind them.

**Plans**: 13/13 plans integrated (6 waves); accepted by the author on 2026-09-08
**UI hint**: yes

Plans:

**Wave 1**

- [x] 02-01-PLAN.md — Esquema de corpus gobernado + comando `govern_corpus` (checksum, diccionario, informe de calidad — DATA-03)
- [x] 02-07-PLAN.md — Tokens de pulido compartidos en `globals.css` + fix de overflow de la nav autenticada <430px

**Wave 2** *(blocked on Wave 1)*

- [x] 02-02-PLAN.md — Campos de rating de usuario de IGDB, re-import + alias, snapshot inmutable `CorpusRatingSnapshot`, ADR-008 — `fb2dafe` (2026-09-07); import IGDB verificado completo (312.560 obras, 27.014 con `rating` = 13,933 %), RAWG acotado N=10.000 top-`rating_count` → 8.575 emparejadas / 8.575 snapshots `source="rawg"` / 0 cobertura nueva (el corte ya tenía rating IGDB), `GameWork.rating` sin mutar, 70 tests catalogue
- [x] 02-08-PLAN.md — Protocolo de evaluación congelado (`protocol.json`) + métricas de ranking + split leave-one-out — `2f51d16`/`2696c54` (2026-09-07); app `evaluation` en `INSTALLED_APPS`, 12 claves congeladas + `simulation:true`, rejilla de 18 configs (tope 24), `## Amenazas a la validez` (DOC-04), 54 tests; suite `pytest apps/api` 280/280

**Wave 3** *(blocked on Wave 2)*

- [x] 02-03-PLAN.md — Búsqueda tolerante (backfill de `GameAlias`) + filtros multi-selección backend — completado; resumen y pruebas disponibles
- [x] 02-05-PLAN.md — API de catálogo para el pase de UI: serializer, `NewReleasesView` (D-24), `OwnedGamesDlcView` (D-15), `display_rating` (D-09) — completado; resumen y pruebas disponibles
- [x] 02-09-PLAN.md — Usuarios sintéticos reproducibles por semilla + aislamiento del baseline de popularidad + informe de validación — completado; 200 usuarios, 25 cold-start, 17 tests específicos y 352 tests de backend
- [x] 02-10-PLAN.md — Baseline aleatorio `rank_random_v1` (REC-01) + modelo de features de contenido + caché `WorkFeatureVector` — completado; resumen y pruebas disponibles

**Wave 4** *(blocked on Wave 3)*

- [x] 02-04-PLAN.md — UI de filtros multi-selección (`FacetMenu`) + densidad product-grade del catálogo
- [x] 02-11-PLAN.md — Variantes con nombre del recomendador de contenido, explicación determinista, arranque en frío, `ContentRecsView`

**Wave 5** *(blocked on Wave 4)*

- [x] 02-06-PLAN.md — Ficha de juego product-grade (sinopsis, rating relabelado) + estantes "Novedades" y "Para tus juegos"
- [x] 02-13-PLAN.md — Primera comparación completa `run_evaluation` (EVAL-01) + controles metodológicos (AGENT-04) + reconciliación (DATA-07)

**Wave 6** *(blocked on Wave 5)*

- [x] 02-12-PLAN.md — Página de recomendaciones: 3 secciones etiquetadas que coexisten (contenido / género / DLC)

### Phase 3: Explainable Content Recommenders and Baseline Comparison

**Mode:** mvp
**Goal**: Researchers can run the frozen harness over random and popularity baselines plus the Phase 2 recommender and additional content-based variants, and independently recalculate every accuracy, ranking, coverage, diversity, novelty, cohort, timing, and uncertainty result from immutable artifacts.
**Depends on**: Phase 2
**Requirements**: EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08, EVAL-11, EVAL-12, QUAL-02
**Success Criteria** (what must be TRUE):

  1. A clean installation runs the random and popularity baselines and every content recommender against the frozen protocol and reproduces versioned outputs.
  2. Every run records code, environment, dataset, split, seed, parameter, model, and metric identities, per-user outputs, timing, and resource consumption without mutable aliases.
  3. Stored artifacts recalculate accuracy and ranking, coverage, diversity, and novelty, reported by user cohort including zero-history and sparse-history users, without rerunning any model.
  4. Comparisons use multiple seeds, uncertainty estimates, and justified statistical tests, and failed-run states are visible and cannot silently yield partial published evidence.
  5. Metric rationale, limitations, agent work, verification, and author interpretation are captured for direct thesis use.

**Plans**: 4 plans in 3 waves; completed 2026-09-12 with the multi-seed limitation documented

**Plan files**:

- [x] 03-01-PLAN.md (Wave 1) — Tracer de ranking real, candidatos comunes y contrato v2 — completado 2026-09-08; `03-01-SUMMARY.md`, servicio v2, manifiesto común hashado y 403 pruebas backend.
- [x] 03-02-PLAN.md (Wave 2) — Señales de contenido, variantes y explicaciones deterministas — completado 2026-09-09; `03-02-SUMMARY.md`, perfiles positivo/negativo, `fs-v2` y razones estructuradas.
- [x] 03-03-PLAN.md (Wave 2) — Métricas beyond-accuracy, incertidumbre, contrastes estadísticos y desglose por cohortes; resumen `03-03-SUMMARY.md`. La repetición multi-semilla del punto 6 queda documentada como limitación.
- [x] 03-04-PLAN.md (Wave 3) — Runner, captura futura de entorno/recursos, evidencia UI/E2E y vault; resumen `03-04-SUMMARY.md`. `QUAL-02` verificado mediante tres pruebas Playwright; la limitación multi-semilla queda documentada.

**UI hint**: yes

### Phase 4: Collaborative and Hybrid Comparison

**Mode:** mvp
**Goal**: Researchers can fairly compare collaborative and hybrid recommenders with the prior baselines and content results and make simulation-bounded conclusions.
**Depends on**: Phase 3
**Requirements**: REC-04, REC-05, DOC-03
**Success Criteria** (what must be TRUE):

  1. The frozen harness produces collaborative recommendations for eligible cohorts using the same candidates, exclusions, splits, metrics, and tuning budget as earlier methods.
  2. A documented hybrid combines content and collaborative evidence and transitions predictably for cold and sparse users.
  3. Multi-seed results expose uncertainty, cohort trade-offs, diversity/novelty effects, timing, and sensitivity without tuning on the test set.
  4. Each algorithm's theory, formulation, parameters, limitations, implementation evidence, agent contribution, and author interpretation are thesis-ready.

**Plans**: 3 plans in 2 waves; completed 2026-09-12 with the multi-seed limitation documented

**Plan files**:

- [x] 04-01-PLAN.md — Rankers colaborativo e híbrido compartidos, con pruebas y fallbacks.
- [x] 04-02-PLAN.md — Workers independientes y estanterías web para ambos algoritmos.
- [x] 04-03-PLAN.md — Evaluación offline paralela por proceso, tiempos y fallo explícito.

**Cierre:** REC-04, REC-05 y DOC-03 quedan verificados. La comparación v15
está congelada y es reproducible, pero procede de una sola semilla; la
sensibilidad multi-semilla queda como limitación metodológica y trabajo futuro.

### Phase 5: Complete Collection Workflows and Portability

**Mode:** mvp
**Goal**: Controlled users can fully curate their profile, collection, commentary, lists, and copy inventory, and can safely export the visible data as versioned CSV.
**Depends on**: Phase 4
**Requirements**: PROF-01, LIB-03, LIB-04, INV-03, INV-04, PORT-01, PORT-04, PRIV-01
**Success Criteria** (what must be TRUE):

  1. A user can edit profile details, create/edit/delete comments, and create and reorder custom lists.
  2. A user can record purchase information for any copy and conservation/storage details for physical copies, while public responses expose only allowlisted fields.
  3. A user can export a deterministic, versioned CSV containing the visible collection, ratings, lists, commentary, and favorites.
  4. Exported spreadsheet cells cannot execute formulas; JSON export and import preview/conflict handling are explicitly assigned to Phase 7 and are not part of this closure.
  5. The workflows have accessible UI verification and contemporaneous design, test, limitation, agent, and author-decision evidence.

**Plans**: 4/4 plans executed (backend only — no `apps/web/**` plan in this phase, see `05-01`..`05-04` `<handoff>` blocks)
Plans:

- [x] 05-01-PLAN.md — autenticación real, perfil, favoritos y privacidad
- [x] 05-02-PLAN.md — comentarios únicos y listas personalizadas ordenables
- [x] 05-03-PLAN.md — metadatos avanzados de copias e inventario
- [x] 05-04-PLAN.md — exportación CSV, reconciliación de requisitos y evidencia

**Estado (2026-09-13, cerrada):** las 4 plans de backend están completas y verificadas (619/619 tests). La integración en `apps/web/**` (perfil/favoritos, comentarios, listas, copias, export CSV) está hecha y verificada con evidencia Playwright/axe real (`e2e/collection-workflows.spec.ts`, 2/2 reproducible en tres ejecuciones separadas). Dos bugs de integración encontrados durante esa verificación (404 del export CSV a través del proxy de Next.js; colisión de clases CSS entre botones de borrar comentario/lista/copia) quedaron corregidos en la misma sesión. Evidencia completa en `docs/verification/phase-05-signoff.md` §9-10.

**UI hint**: yes

### Phase 6: Public Discovery and Resilient Enrichment

**Mode:** mvp
**Goal**: Visitors can discover and share rich local catalogue and profile views that expose only permitted activity, while controlled authenticated users can build friendships and exchange private game recommendations without contaminating research data.
**Depends on**: Phase 5
**Requirements**: PROF-03, PROF-04, CAT-05, SOCIAL-03, SOCIAL-04, SOCIAL-05
**Note**: CAT-02 and DATA-04 were reprioritized by the author into Phase 01.1 and are owned there. DATA-05, DATA-06, DATA-07, and DATA-08 (live enrichment provenance and experiment isolation) moved into the enlarged Phase 2 in the 2026-09-06 roadmap revision.
**Success Criteria** (what must be TRUE):

  1. A visitor can filter and sort broad catalogue metadata (games, platforms, editions, genres, franchises, developers, publishers, dates, modes, tags) drawn from approved sources.
  2. A visitor can open the basic profile allowed by D-07, while an owner or accepted friend can open shareable profile and list URLs that expose only permitted games, lists, ratings, comments, and no private ownership data.
  3. Public projections use an explicit allowlist of fields; direct protected URLs re-authorise server-side and return a generic indistinguishable `404` when access is not allowed.
  4. Authenticated users can manage exact-alias friendship requests, accepted friendships, rejection/removal/block transitions, and private game recommendations in an inbox with unread state and a seven-day directional rolling cooldown.
  5. Accessibility, security, thesis rationale, agent contribution, automated checks, and author decisions are recorded with the phase evidence.

**Plans**: 10/10 plans executed
Plans:
**Wave 1**

- [x] 06-00-PLAN.md — Reconciliación semántica de requisitos, decisiones y trazabilidad
- [x] 06-01-PLAN.md — Núcleo transaccional de relaciones sociales

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06-02-PLAN.md — Contrato CAT-05 y enriquecimiento local resiliente

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 06-03-PLAN.md — Perfil básico, proyecciones autorizadas y listas compartibles
- [x] 06-05-PLAN.md — Descubrimiento de catálogo en Next.js

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 06-04-PLAN.md — Comentarios autorizados, recomendaciones e inbox backend
- [x] 06-06-PLAN.md — Perfiles, amistades y acciones sociales en Next.js

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 06-07-PLAN.md — Inbox privado, navegación y badge de pendientes
- [x] 06-08-PLAN.md — Comentarios en ficha, traducciones y estados visuales

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 06-09-PLAN.md — E2E, gates PostgreSQL y evidencia final

**UI hint**: yes

### Phase 7: Research Panel, Hardening, and Evidence Freeze

**Mode:** mvp
**Goal**: The deployed and offline demonstrator is securely operable and presents an accessible, immutable, thesis-ready comparison of the completed research.
**Depends on**: Phase 6
**Portability carry-over**: PORT-02 and PORT-03 are deferred from Phase 5 to this identifiable later phase; their endpoints, parsers, preview, row-level validation, and conflict rules are not part of the Phase 5 plans.
**Requirements**: EVAL-13, EVAL-14, ADMIN-01, ADMIN-02, SEC-01, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08, PRIV-02, OPS-04, OPS-05, QUAL-01, QUAL-04, DOC-05, DOC-06, AGENT-05, AGENT-06, PORT-02, PORT-03
**Success Criteria** (what must be TRUE):

  1. A researcher can compare immutable runs, configurations, algorithms, cohorts, metrics, timings, provenance, and limitations through accessible tables/charts and export thesis-ready figures/data.
  2. An authorised administrator can manage demo users/catalogue and supervise imports, jobs, and experiments without direct database edits; account deletion/anonymisation and non-secret audit events work.
  3. Role/ownership, injection, XSS/CSRF, malicious-content, SSRF/redirect, rate-limit, header, error-handling, secret, dependency, and pipeline checks protect the deployed system and are evidenced by tests.
  4. Structured non-sensitive logs expose job state, and tested PostgreSQL/artifact backup and recovery restore the demonstrator and immutable evidence.
  5. A clean checkout reproduces the final evidence and accessible deployed/offline workflows; canonical thesis references, generated tables/figures, AI-use disclosure, costs, limitations, threats to validity, agent records, and author decisions are frozen together.

**Plans**: TBD
**UI hint**: yes

### Candidate phase (not yet numbered or scheduled): Real-User Study and Survey-Based Quality Evaluation

Noted by the author 2026-09-11, after the synthetic-population offline study (protocol v14,
400 users) closes: recruit 20 real users who build their own library in SavePoint, collect
that library data, then run a **survey-based quality evaluation** (subjective satisfaction,
not the ranking metrics used for the synthetic study) plus the same 16-algorithm offline
harness over their real libraries. The corpus at that point will be newer than the
`2026.09.2` snapshot frozen for the current study, but must itself be frozen to one
consistent snapshot shared across all 20 collections for that round. This is explicitly a
**quality** evaluation, not a comparative benchmark against the synthetic-population
metrics — two separate thesis chapters with separate methodologies. Full rationale:
`ideas-vault/Fases/2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad.md`.
Not planned (no requirement IDs, success criteria, or wave breakdown yet) — evaluate and
schedule properly in a later phase-planning pass.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Three-Day Public Demo Slice | 16/16 | Complete    | 2026-09-05 |
| 01.1. Real-Scale Catalogue and Product Experience (inserted) | 10/10 | Complete    | 2026-09-06 |
| 2. Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender | 13/13 | Complete    | 2026-09-08 |
| 3. Explainable Content Recommenders and Baseline Comparison | 4/4 | Complete with limitation | 2026-09-12 |
| 4. Collaborative and Hybrid Comparison | 3/3 | Complete with limitation | 2026-09-12 |
| 5. Complete Collection Workflows and Portability | 4/4 | Complete | 2026-09-13 |
| 6. Public Discovery and Resilient Enrichment | 10/10 | Complete    | 2026-09-13 |
| 7. Research Panel, Hardening, and Evidence Freeze | 0/TBD | Not started | - |
