# Roadmap: SavePoint

## Overview

SavePoint begins with a three-day, publicly deployed vertical demonstration, then replaces demo shortcuts with governed data, a frozen evaluation contract, complete collection workflows, resilient enrichment, reproducible experiment infrastructure, and progressively stronger recommenders. The final phase exposes immutable evidence through an accessible research panel and hardens the demonstrator for thesis assessment. Every phase is an MVP vertical slice and must leave contemporaneous thesis and agent-methodology evidence; documentation is an acceptance condition throughout, not an end-only activity.

## Delivery Policy

- **Mode:** mvp for every initial phase.
- **Phase 1 deadline:** a visible public demonstration within three days.
- **Demo-grade boundary:** Phase 1 may use controlled seeded accounts, a small lawful local catalogue, a simple popularity recommender, and narrowly scoped administration. It may not use client-side secrets, unlawful data, mutable research inputs, or undocumented setup.
- **Hardening boundary:** Phases 2-8 expand data governance, evaluation validity, product depth, security, recovery, accessibility, and operational controls. Phase 1 is a coherent demonstrator, not evidence that these later guarantees are complete.
- **Continuous evidence:** each phase records decisions, alternatives, tests, provenance, limitations, agent roles/prompts/configuration, automated verification, and explicit author decisions relevant to its scope.

## Phases

- [x] **Phase 1: Three-Day Public Demo Slice** - Deploy a lawful, locally reproducible controlled demo with catalogue, backlog, rating, inventory, public profile, and popularity recommendations. (completed 2026-09-05)
- [ ] **Phase 2: Governed Corpus and Frozen Evaluation Contract** - Establish immutable research inputs, synthetic scenarios, and the protocol that later algorithm comparisons cannot redefine.
- [ ] **Phase 3: Complete Collection Workflows and Portability** - Complete profiles, comments, lists, copy details, and safe deterministic import/export.
- [ ] **Phase 4: Public Discovery and Resilient Enrichment** - Add public projections, catalogue discovery, and attributable live enrichment without contaminating research data.
- [ ] **Phase 5: Reproducible Experiment Harness and Baselines** - Execute immutable, comparable baseline runs whose metrics and evidence can be independently recalculated.
- [ ] **Phase 6: Explainable Content Recommendations** - Deliver personalized content recommendations, cold-start routing, exclusions, and faithful explanations.
- [ ] **Phase 7: Collaborative and Hybrid Comparison** - Compare collaborative and hybrid methods under the already-frozen protocol and document bounded conclusions.
- [ ] **Phase 8: Research Panel, Hardening, and Evidence Freeze** - Present thesis-ready comparisons and finish administration, security, recovery, accessibility, and reproducibility gates.

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

- [ ] 01.1-01-PLAN.md (Wave 1) — Approve and probe IGDB, then freeze the provider ADR and dependency pin
- [ ] 01.1-02-PLAN.md (Wave 2) — Build resumable ingestion and prove a full-scale import on fresh PostgreSQL
- [ ] 01.1-06-PLAN.md (Wave 3) — Approve and implement the product redesign milestone before account work
- [ ] 01.1-04-PLAN.md (Wave 4) — Add plural, clearly labeled simulated accounts
- [ ] 01.1-08-PLAN.md (Wave 5) — Add controlled functional registration without opening AUTH-03
- [ ] 01.1-03-PLAN.md (Wave 6) — Add validated catalogue filters, sorting, facets, and shareable controls
- [ ] 01.1-05-PLAN.md (Wave 7) — Deliver deterministic personal genre recommendation service and API
- [ ] 01.1-09-PLAN.md (Wave 8) — Wire the personalized page and authenticated navigation
- [ ] 01.1-10-PLAN.md (Wave 9) — Produce complete Playwright, axe, viewport, and screenshot evidence
- [ ] 01.1-07-PLAN.md (Wave 10) — Record the author's separate post-evidence product-quality verdict

### Phase 2: Governed Corpus and Frozen Evaluation Contract

**Mode:** mvp
**Goal**: Researchers can identify the immutable corpus and reproduce a predeclared, simulation-aware evaluation protocol before sophisticated recommenders are compared.
**Depends on**: Phase 1
**Requirements**: AUTH-02, DATA-03, EVAL-01, EVAL-02, EVAL-03, EVAL-09, EVAL-10, DOC-04, AGENT-04
**Success Criteria** (what must be TRUE):

  1. A researcher can verify the fixed corpus checksum, data dictionary, and missing-data/quality report independently of mutable enrichment.
  2. The comparison protocol freezes relevance, K, users, candidates, exclusions, split manifests, metrics, seeds, tuning budget, and test isolation before advanced algorithms run.
  3. Clearly labelled synthetic accounts can be regenerated from contrasting parameterized scenarios and independent seeds with the same histories and validation report.
  4. Research evidence explicitly limits conclusions to synthetic simulation and records leakage, hallucination, bias, error, and information-exposure controls plus author decisions.

**Plans**: TBD

### Phase 3: Complete Collection Workflows and Portability

**Mode:** mvp
**Goal**: Controlled users can fully curate and safely move their profile, collection, commentary, and lists.
**Depends on**: Phase 2
**Requirements**: PROF-01, LIB-03, LIB-04, INV-03, INV-04, PORT-01, PORT-02, PORT-03, PORT-04, PRIV-01
**Success Criteria** (what must be TRUE):

  1. A user can edit profile details, create/edit/delete comments, and create and reorder custom lists.
  2. A user can record purchase information for any copy and conservation/storage details for physical copies, while public responses expose only allowlisted fields.
  3. A user can export versioned CSV and JSON and preview an import before applying it.
  4. Invalid or duplicate import rows receive deterministic row-level outcomes, and exported spreadsheet cells cannot execute formulas.
  5. The workflows have accessible UI verification and contemporaneous design, test, limitation, agent, and author-decision evidence.

**Plans**: TBD
**UI hint**: yes

### Phase 4: Public Discovery and Resilient Enrichment

**Mode:** mvp
**Goal**: Visitors can discover and share rich public catalogue/profile views whose live metadata is attributable, resilient, and isolated from experiments.
**Depends on**: Phase 3
**Requirements**: PROF-03, PROF-04, CAT-02, CAT-05, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08
**Success Criteria** (what must be TRUE):

  1. A visitor can filter/sort broad catalogue metadata and open shareable profile/list URLs that expose only permitted activity and statistics.
  2. Enriched values display their source and retrieval date, degrade to lawful local placeholders on provider failure, and never change a completed experiment.
  3. A researcher can inspect the provider comparison, lawful-use/redistribution record, identifier reconciliation, conflict rules, and limitations behind any displayed value.
  4. Provider credentials remain server-side and refresh, quota, timeout, malformed-response, and stale-data behavior can be observed without breaking catalogue use.
  5. Accessibility, security, thesis rationale, agent contribution, automated checks, and author decisions are recorded with the phase evidence.

**Plans**: TBD
**UI hint**: yes

### Phase 5: Reproducible Experiment Harness and Baselines

**Mode:** mvp
**Goal**: Researchers can run fair random/popularity baselines and independently recalculate their immutable evaluation evidence.
**Depends on**: Phase 4
**Requirements**: REC-01, EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08, EVAL-11, EVAL-12, QUAL-02
**Success Criteria** (what must be TRUE):

  1. A clean installation can run random and popularity baselines against the frozen protocol and reproduce versioned outputs.
  2. Every run records code/environment/data/split/seed/parameter/model/metric identities, per-user outputs, timing, and resource consumption without mutable aliases.
  3. Stored artifacts can recalculate accuracy/ranking, coverage, diversity, novelty, cohort, uncertainty, and justified statistical comparisons without rerunning models.
  4. Multiple seeds and failed-run states are visible, comparable, and cannot silently yield partial published evidence.
  5. Metric rationale, limitations, agent work, verification, and author interpretation are captured for direct thesis use.

**Plans**: TBD

### Phase 6: Explainable Content Recommendations

**Mode:** mvp
**Goal**: Users, including newcomers, receive useful content-based recommendations with reproducible evidence and understandable faithful reasons.
**Depends on**: Phase 5
**Requirements**: REC-03, REC-06, REC-07, REC-08, REC-09
**Success Criteria** (what must be TRUE):

  1. A user with history can request ranked content-based recommendations that exclude configured already-consumed games.
  2. A zero- or sparse-history user receives an explicit popularity/onboarding/content fallback instead of an empty result.
  3. Each result shows a deterministic, accessible explanation grounded in persisted features or model evidence rather than generated prose.
  4. Published results retain model, feature, and input-data versions and reproduce from their immutable artifacts.
  5. The algorithm theory, parameters, tests, accessibility, limitations, agent contributions, and author decisions remain inspectable as phase evidence.

**Plans**: TBD
**UI hint**: yes

### Phase 7: Collaborative and Hybrid Comparison

**Mode:** mvp
**Goal**: Researchers can fairly compare collaborative and hybrid recommenders with prior baselines/content results and make simulation-bounded conclusions.
**Depends on**: Phase 6
**Requirements**: REC-04, REC-05, DOC-03
**Success Criteria** (what must be TRUE):

  1. The frozen harness produces collaborative recommendations for eligible cohorts using the same candidates, exclusions, splits, metrics, and tuning budget as earlier methods.
  2. A documented hybrid combines content and collaborative evidence and transitions predictably for cold and sparse users.
  3. Multi-seed results expose uncertainty, cohort trade-offs, diversity/novelty effects, timing, and sensitivity without tuning on the test set.
  4. Each algorithm's theory, formulation, parameters, limitations, implementation evidence, agent contribution, and author interpretation are thesis-ready.

**Plans**: TBD

### Phase 8: Research Panel, Hardening, and Evidence Freeze

**Mode:** mvp
**Goal**: The deployed and offline demonstrator is securely operable and presents an accessible, immutable, thesis-ready comparison of the completed research.
**Depends on**: Phase 7
**Requirements**: EVAL-13, EVAL-14, ADMIN-01, ADMIN-02, SEC-01, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08, PRIV-02, OPS-04, OPS-05, QUAL-01, QUAL-04, DOC-02, DOC-05, DOC-06, AGENT-05, AGENT-06
**Success Criteria** (what must be TRUE):

  1. A researcher can compare immutable runs, configurations, algorithms, cohorts, metrics, timings, provenance, and limitations through accessible tables/charts and export thesis-ready figures/data.
  2. An authorised administrator can manage demo users/catalogue and supervise imports, jobs, and experiments without direct database edits; account deletion/anonymisation and non-secret audit events work.
  3. Role/ownership, injection, XSS/CSRF, malicious-content, SSRF/redirect, rate-limit, header, error-handling, secret, dependency, and pipeline checks protect the deployed system and are evidenced by tests.
  4. Structured non-sensitive logs expose job state, and tested PostgreSQL/artifact backup and recovery restore the demonstrator and immutable evidence.
  5. A clean checkout reproduces the final evidence and accessible deployed/offline workflows; canonical thesis references, generated tables/figures, AI-use disclosure, costs, limitations, threats to validity, agent records, and author decisions are frozen together.

**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Three-Day Public Demo Slice | 16/16 | Complete    | 2026-09-05 |
| 2. Governed Corpus and Frozen Evaluation Contract | 0/TBD | Not started | - |
| 3. Complete Collection Workflows and Portability | 0/TBD | Not started | - |
| 4. Public Discovery and Resilient Enrichment | 0/TBD | Not started | - |
| 5. Reproducible Experiment Harness and Baselines | 0/TBD | Not started | - |
| 6. Explainable Content Recommendations | 0/TBD | Not started | - |
| 7. Collaborative and Hybrid Comparison | 0/TBD | Not started | - |
| 8. Research Panel, Hardening, and Evidence Freeze | 0/TBD | Not started | - |
