# Requirements: SavePoint

**Defined:** 2026-09-04
**Core Value:** Users receive useful and explainable video-game recommendations from a well-organised collection, while every algorithmic result remains reproducible and defensible in the thesis.

## v1 Requirements

### Accounts and Profiles

- [x] **AUTH-01**: User can sign in to and sign out of a controlled account.
- [x] **AUTH-02**: System can load synthetic users that are clearly identified as simulated accounts.
- [x] **PROF-01**: User can edit their biography and optional HTTPS avatar while the login alias remains immutable.
- [x] **PROF-02**: An authorised visitor can view a public profile.
- [x] **PROF-03**: Public projections expose only the exact allowlist `alias`, `avatar_url`, `bio`, `game`, `cover`, `year`, `platform`, `backlog_status`, `personal_rating`, `author_alias`, `text`, and `date`; the only non-friend exception is the basic profile in D-07, with no collection, lists, comments, activity, statistics, copies, purchases, prices, stores, locations, private notes, or internal identifiers.
- [x] **PROF-04**: Owner and accepted friends can use shareable profile and public-list URLs; every direct URL is authorised server-side and unauthorised, blocked, anonymous-protected, and nonexistent resources return an indistinguishable generic `404`.
- [x] **SOCIAL-03**: Authenticated users can find exact aliases and manage friendship requests, accepted friendships, rejection, removal, blocking, and unblocking; these controlled relationship workflows do not replace v2 `SOCIAL-01` or `SOCIAL-02`. `[ASSUMED]` for Phase 6 planning.
- [x] **SOCIAL-04**: Owners and accepted friends can access allowlisted profile, collection, list, and comment projections through protected URLs, while a non-friend receives only the D-07 basic profile. `[ASSUMED]` for Phase 6 planning.
- [x] **SOCIAL-05**: Friends can send private game recommendations with optional text to an inbox with unread state, accessible pending badge, and a directional seven-day rolling cooldown. `[ASSUMED]` for Phase 6 planning.

### Catalogue

- [x] **CAT-01**: User can search video games by title.
- [ ] **CAT-02**: User can filter and sort the catalogue using available metadata. Phase 01.1 owns the requirement; Phase 6 extends its backend/query traceability under D-01/D-02 without changing the ownership or research snapshots.
- [x] **CAT-03**: Each game has a detail page showing available data and its provenance.
- [x] **CAT-04**: Catalogue uses canonical game identifiers that do not depend on the enrichment API.
- [x] **CAT-05**: Catalogue can represent games, platforms, editions, genres, franchises, developers, publishers, dates, modes, and tags available from approved sources.
- [x] **CAT-06**: Catalogue remains usable with local data when the enrichment API is unavailable.

### Backlog, Lists, and Inventory

- [x] **LIB-01**: User can mark a game as pending, playing, completed, or abandoned.
- [x] **LIB-02**: User can rate a game using a consistent rating scale.
- [x] **LIB-03**: User can create, edit, and delete their own comments.
- [x] **LIB-04**: User can create and order custom game lists.
- [x] **INV-01**: User can register multiple owned copies of the same game.
- [x] **INV-02**: Each copy can record physical or digital format, platform, and edition.
- [x] **INV-03**: Each copy can record purchase date, price, currency, and store.
- [x] **INV-04**: A physical copy can record conservation state and storage location.
- [x] **INV-05**: Private notes and purchase details never appear in public projections.
- [x] **PORT-01**: User can export their collection, ratings, and lists as versioned CSV; JSON is not part of the Phase 5 closure.
- [ ] **PORT-02**: User can preview and validate an import before applying it (assigned to Phase 7; no Phase 5 endpoint or feature test).
- [ ] **PORT-03**: Import reports row-level errors and applies deterministic duplicate and conflict rules (assigned to Phase 7; no Phase 5 endpoint or feature test).
- [x] **PORT-04**: CSV exports neutralise potentially malicious spreadsheet formulas.

### Data and Provenance

- [x] **DATA-01**: Project uses a stable, citable dataset that is legally suitable for its experiments.
- [x] **DATA-02**: Dataset records its version, licence, source URL, retrieval date, and checksum.
- [x] **DATA-03**: Project generates a data dictionary and a quality/missing-fields report for the fixed corpus.
- [x] **DATA-04**: Enrichment API is selected through a documented comparison of coverage, platforms, licence, attribution, quotas, stability, and cost.
- [x] **DATA-05**: Each enriched value retains its source and retrieval date.
- [x] **DATA-06**: Mutable API data cannot retrospectively alter completed experiments.
- [x] **DATA-07**: System uses deterministic rules to reconcile source identifiers and conflicting values.
- [x] **DATA-08**: Thesis evidence explains the dataset and API choices, limitations, and redistribution rights.

### Recommendations

- [x] **REC-01**: System produces a random recommendation baseline.
- [x] **REC-02**: System produces a popularity recommendation baseline.
- [x] **REC-03**: System implements a content-based recommender.
- [x] **REC-04**: System implements at least one collaborative-filtering method.
- [x] **REC-05**: System implements a hybrid recommender.
- [x] **REC-06**: User without sufficient history receives recommendations through an explicit cold-start strategy.
- [x] **REC-07**: Recommendations exclude already-consumed games according to configured rules.
- [x] **REC-08**: Each recommendation presents a deterministic explanation grounded in actual model evidence.
- [x] **REC-09**: Published recommendation results retain the model, feature, and input-data versions used.
- [ ] **REC-10**: A dedicated recommendations page exposes genre-oriented suggestions reflecting the signed-in user's own recorded tastes, distinct from the public popularity baseline.

### Experimentation and Evaluation

- [x] **EVAL-01**: All algorithms are compared with the same users, candidates, exclusions, and split manifests.
- [x] **EVAL-02**: Transformations fit training data only and the test set remains isolated from tuning.
- [x] **EVAL-03**: Protocol fixes relevance, K, splits, metrics, and tuning budget before algorithm comparison.
- [ ] **EVAL-04**: Evaluation calculates justified accuracy and ranking metrics.
- [ ] **EVAL-05**: Evaluation calculates coverage, diversity, and novelty metrics.
- [ ] **EVAL-06**: Evaluation records execution time and resource consumption.
- [ ] **EVAL-07**: Results are reported by user cohort, including zero-history and sparse-history users.
- [ ] **EVAL-08**: Comparisons use multiple seeds, uncertainty estimates, and justified statistical tests.
- [x] **EVAL-09**: Synthetic users are generated from contrasting, parameterised, and reproducible scenarios.
- [x] **EVAL-10**: Conclusions distinguish synthetic simulation results from evidence about real users.
- [ ] **EVAL-11**: Every run records code, environment, dataset, split, seeds, parameters, model, and metric identities.
- [ ] **EVAL-12**: Stored artifacts allow aggregate results to be recalculated without rerunning an experiment.
- [x] **EVAL-13**: Research panel compares algorithms, configurations, metrics, cohorts, and runs.
- [x] **EVAL-14**: Research panel provides accessible tables and exports thesis-ready results and figures.

### Administration, Privacy, and Security

- [x] **ADMIN-01**: Authorised administrator can manage demo users and catalogue data.
- [x] **ADMIN-02**: Authorised administrator can supervise imports, jobs, and experiments without directly editing the database.
- [x] **SEC-01**: Server validates every permission and tests access by role and ownership.
- [x] **SEC-02**: No secret or API key is present in Git, browser bundles, logs, public images, or public artifacts.
- [x] **SEC-03**: Database access uses an ORM or parameterised queries and is tested against SQL injection.
- [x] **SEC-04**: Inputs and outputs are validated and protected against XSS, CSRF, and malicious content.
- [x] **SEC-05**: External URLs and requests are constrained against SSRF, unsafe redirects, and URL manipulation.
- [x] **SEC-06**: Application applies rate limits, secure headers, and non-sensitive production error handling.
- [x] **SEC-07**: Delivery pipeline scans secrets, vulnerable dependencies, and insecure code.
- [x] **SEC-08**: Sensitive actions create audit events without recording credentials or secrets.
- [x] **PRIV-01**: Public projections use an explicit allowlist of fields.
- [x] **PRIV-02**: A controlled account can be deleted or anonymised.

### Operations, Quality, and Delivery

- [x] **OPS-01**: Application can be deployed to the Internet using documented configuration.
- [x] **OPS-02**: Project can be run locally through a reproducible documented process.
- [x] **OPS-03**: A lawful offline demo mode works without the external API or Internet access.
- [ ] **OPS-04**: PostgreSQL and experimental artifacts have tested backup and recovery procedures.
- [x] **OPS-05**: System emits structured logs and observable job states without sensitive data.
- [x] **QUAL-01**: Project has unit, integration, and browser tests for critical workflows.
- [ ] **QUAL-02**: A clean installation can reproduce experiments and their evidence.
- [x] **QUAL-03**: Core workflows are responsive and verifiable against WCAG 2.2 AA.
- [x] **QUAL-04**: Charts and visualisations provide accessible textual or tabular alternatives.
- [ ] **QUAL-05**: Interface presents a professional, product-grade visual design comparable to established cataloguing applications (density, typography, imagery treatment), not a minimal utilitarian layout.

### Thesis and Agent-Assisted Methodology

- [x] **DOC-01**: Architecture and technology decisions record alternatives and rationale.
- [x] **DOC-02**: Dataset, API, data model, and normalisation processes are documented.
- [x] **DOC-03**: Each algorithm documents its theory, formulation, parameters, and limitations.
- [x] **DOC-04**: Experimental protocol, metrics, results, and threats to validity are documented.
- [ ] **DOC-05**: Thesis tables and figures are generated from immutable experiment artifacts.
- [ ] **DOC-06**: Future example theses, formatting rules, and lecturer annotations are registered as canonical project references.
- [x] **AGENT-01**: Project records the roles and responsibilities of agents used.
- [x] **AGENT-02**: Project retains relevant protocols or prompts, configuration, models, tools, and generated artifacts.
- [x] **AGENT-03**: Evidence distinguishes agent proposals, automated verification, and author decisions.
- [x] **AGENT-04**: Methodology documents controls against hallucination, bias, error, and information exposure.
- [ ] **AGENT-05**: Methodology analyses reproducibility, costs, limitations, and threats to validity of agent-assisted work.
- [ ] **AGENT-06**: AI use is disclosed according to future university rules and lecturer guidance.

## v2 Requirements

### Extended Collection

- **DIARY-01**: User can record play sessions, dates, and time played.
- **REVIEW-01**: User can mark and reveal spoiler-containing review content.
- **PRIV-03**: User can configure visibility for individual lists and collection items.

### Social and Integrations

`SOCIAL-01` and `SOCIAL-02` remain v2 requirements with their original meaning.
Phase 6 adds the controlled, relationship-gated workflows in `SOCIAL-03`,
`SOCIAL-04`, and `SOCIAL-05`; these are not an open community feed or reaction
system.

- **SOCIAL-01**: User can follow other profiles and view a social activity feed.
- **SOCIAL-02**: User can react to or interact with community content.
- **AUTH-03**: Visitor can register an unrestricted production account.
- **STORE-01**: User can synchronise owned games automatically with storefront accounts.

### Advanced Clients and Models

- **MOBILE-01**: User can access SavePoint through native mobile applications.
- **REC-10**: System can compare neural recommenders when a justified research question and adequate dataset exist.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Unrestricted open community social network in v1 | Phase 6 includes only controlled, relationship-gated friendship, protected projections, and private recommendations; it does not include an unrestricted moderation-heavy feed or reaction network. |
| Open production registration in v1 | Initial release is a controlled academic demonstration. |
| Real-time or continuous model training | Offline, versioned training is safer and more reproducible for the thesis. |
| Generative recommendation explanations | Deterministic evidence-based explanations are more faithful and auditable. |
| Microservices or Kubernetes by default | They add operational complexity without evidence of a scaling need. |
| Marketplace, valuation, or trading | These do not support the collection-and-recommendation core value. |
| Storage of storefront credentials, keys, or receipts | Avoids unnecessary sensitive-data and security risk. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| PROF-02 | Phase 1 | Complete |
| CAT-01 | Phase 1 | Complete |
| CAT-03 | Phase 1 | Complete |
| CAT-04 | Phase 1 | Complete |
| CAT-06 | Phase 1 | Complete |
| LIB-01 | Phase 1 | Complete |
| LIB-02 | Phase 1 | Complete |
| INV-01 | Phase 1 | Complete |
| INV-02 | Phase 1 | Complete |
| INV-05 | Phase 1 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| REC-02 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| OPS-01 | Phase 1 | Complete |
| OPS-02 | Phase 1 | Complete |
| OPS-03 | Phase 1 | Complete |
| QUAL-03 | Phase 1 | Complete |
| DOC-01 | Phase 1 | Complete |
| AGENT-01 | Phase 1 | Complete |
| AGENT-02 | Phase 1 | Complete |
| AGENT-03 | Phase 1 | Complete |
| CAT-02 | Phase 01.1 (extended by Phase 6) | Pending |
| AUTH-02 | Phase 2 | Complete (Plan 02-09) |
| DATA-04 | Phase 01.1 | Complete (ADR-006, Plan 01.1-01) |
| REC-10 | Phase 01.1 | Pending |
| QUAL-05 | Phase 01.1 | Pending |
| DATA-03 | Phase 2 | Complete |
| DATA-05 | Phase 2 | Complete |
| DATA-06 | Phase 2 | Complete |
| DATA-07 | Phase 2 | Complete |
| DATA-08 | Phase 2 | Complete |
| EVAL-01 | Phase 2 | Complete |
| EVAL-02 | Phase 2 | Complete |
| EVAL-03 | Phase 2 | Complete |
| EVAL-09 | Phase 2 | Complete (Plan 02-09) |
| EVAL-10 | Phase 2 | Complete (Plan 02-09) |
| REC-01 | Phase 2 | Complete |
| REC-03 | Phase 2 | Complete |
| REC-06 | Phase 2 | Complete |
| REC-07 | Phase 2 | Complete |
| REC-08 | Phase 2 | Complete |
| REC-09 | Phase 2 | Complete |
| DOC-02 | Phase 2 | Complete |
| DOC-04 | Phase 2 | Complete |
| AGENT-04 | Phase 2 | Complete |
| EVAL-04 | Phase 3 | Pending |
| EVAL-05 | Phase 3 | Pending |
| EVAL-06 | Phase 3 | Pending |
| EVAL-07 | Phase 3 | Pending |
| EVAL-08 | Phase 3 | Pending |
| EVAL-11 | Phase 3 | Pending |
| EVAL-12 | Phase 3 | Pending |
| QUAL-02 | Phase 3 | Pending |
| REC-04 | Phase 4 | Complete (`04-01-SUMMARY.md`, v15 artifact) |
| REC-05 | Phase 4 | Complete (`04-01-SUMMARY.md`, v15 artifact) |
| DOC-03 | Phase 4 | Complete (`docs/methodology/recommendation-algorithms.md`, phase signoff) |
| PROF-01 | Phase 5 | Complete (Plan 05-01) |
| LIB-03 | Phase 5 | Complete |
| LIB-04 | Phase 5 | Complete |
| INV-03 | Phase 5 | Complete |
| INV-04 | Phase 5 | Complete |
| PORT-01 | Phase 5 | Complete (Plan 05-04, CSV only — JSON out of scope) |
| PORT-02 | Phase 7 | Pending — deferred; no Phase 5 endpoint or feature test |
| PORT-03 | Phase 7 | Pending — deferred; no Phase 5 endpoint or feature test |
| PORT-04 | Phase 5 | Complete |
| PRIV-01 | Phase 5 | Complete |
| PROF-03 | Phase 6 | Complete |
| PROF-04 | Phase 6 | Complete |
| CAT-05 | Phase 6 | Complete |
| SOCIAL-03 | Phase 6 | Complete |
| SOCIAL-04 | Phase 6 | Complete |
| SOCIAL-05 | Phase 6 | Complete |
| EVAL-13 | Phase 7 | Complete |
| EVAL-14 | Phase 7 | Complete |
| ADMIN-01 | Phase 7 | Complete |
| ADMIN-02 | Phase 7 | Complete |
| SEC-01 | Phase 7 | Complete |
| SEC-03 | Phase 7 | Complete |
| SEC-04 | Phase 7 | Complete |
| SEC-05 | Phase 7 | Complete |
| SEC-06 | Phase 7 | Complete |
| SEC-07 | Phase 7 | Complete |
| SEC-08 | Phase 7 | Complete |
| PRIV-02 | Phase 7 | Complete |
| OPS-04 | Phase 7 | Pending |
| OPS-05 | Phase 7 | Complete |
| QUAL-01 | Phase 7 | Complete |
| QUAL-04 | Phase 7 | Complete |
| DOC-05 | Phase 7 | Pending |
| DOC-06 | Phase 7 | Pending |
| AGENT-05 | Phase 7 | Pending |
| AGENT-06 | Phase 7 | Pending |

**Coverage:**

- v1 requirements: 91 total
- Mapped to phases: 91
- Unmapped: 0
- Roadmap revised 2026-09-06: DATA-05..08 moved from the former Phase 4 into the enlarged Phase 2; REC-01 moved from the former Phase 5; REC-03/06/07/08/09 moved from the former Phase 6; DOC-02 moved from the former Phase 8. Former phases 5 and 6 merged into the new Phase 3; former 3, 4, 7, 8 renumbered to 5, 6, 4, 7 respectively.

---
*Requirements defined: 2026-09-04*
*Last updated: 2026-09-04 after initial definition*
