# Requirements: SavePoint

**Defined:** 2026-09-04
**Core Value:** Users receive useful and explainable video-game recommendations from a well-organised collection, while every algorithmic result remains reproducible and defensible in the thesis.

## v1 Requirements

### Accounts and Profiles

- [ ] **AUTH-01**: User can sign in to and sign out of a controlled account.
- [ ] **AUTH-02**: System can load synthetic users that are clearly identified as simulated accounts.
- [ ] **PROF-01**: User can edit their alias, avatar, and biography.
- [ ] **PROF-02**: An authorised visitor can view a public profile.
- [ ] **PROF-03**: Public profile shows only permitted games, lists, ratings, comments, and statistics.
- [ ] **PROF-04**: User can obtain a shareable URL for their public profile and public lists.

### Catalogue

- [ ] **CAT-01**: User can search video games by title.
- [ ] **CAT-02**: User can filter and sort the catalogue using available metadata.
- [ ] **CAT-03**: Each game has a detail page showing available data and its provenance.
- [x] **CAT-04**: Catalogue uses canonical game identifiers that do not depend on the enrichment API.
- [ ] **CAT-05**: Catalogue can represent games, platforms, editions, genres, franchises, developers, publishers, dates, modes, and tags available from approved sources.
- [ ] **CAT-06**: Catalogue remains usable with local data when the enrichment API is unavailable.

### Backlog, Lists, and Inventory

- [ ] **LIB-01**: User can mark a game as pending, playing, completed, or abandoned.
- [ ] **LIB-02**: User can rate a game using a consistent rating scale.
- [ ] **LIB-03**: User can create, edit, and delete their own comments.
- [ ] **LIB-04**: User can create and order custom game lists.
- [ ] **INV-01**: User can register multiple owned copies of the same game.
- [ ] **INV-02**: Each copy can record physical or digital format, platform, and edition.
- [ ] **INV-03**: Each copy can record purchase date, price, currency, and store.
- [ ] **INV-04**: A physical copy can record conservation state and storage location.
- [x] **INV-05**: Private notes and purchase details never appear in public projections.
- [ ] **PORT-01**: User can export their collection, ratings, and lists as versioned CSV and JSON.
- [ ] **PORT-02**: User can preview and validate an import before applying it.
- [ ] **PORT-03**: Import reports row-level errors and applies deterministic duplicate and conflict rules.
- [ ] **PORT-04**: CSV exports neutralise potentially malicious spreadsheet formulas.

### Data and Provenance

- [ ] **DATA-01**: Project uses a stable, citable dataset that is legally suitable for its experiments.
- [ ] **DATA-02**: Dataset records its version, licence, source URL, retrieval date, and checksum.
- [ ] **DATA-03**: Project generates a data dictionary and a quality/missing-fields report for the fixed corpus.
- [ ] **DATA-04**: Enrichment API is selected through a documented comparison of coverage, platforms, licence, attribution, quotas, stability, and cost.
- [ ] **DATA-05**: Each enriched value retains its source and retrieval date.
- [ ] **DATA-06**: Mutable API data cannot retrospectively alter completed experiments.
- [ ] **DATA-07**: System uses deterministic rules to reconcile source identifiers and conflicting values.
- [ ] **DATA-08**: Thesis evidence explains the dataset and API choices, limitations, and redistribution rights.

### Recommendations

- [ ] **REC-01**: System produces a random recommendation baseline.
- [ ] **REC-02**: System produces a popularity recommendation baseline.
- [ ] **REC-03**: System implements a content-based recommender.
- [ ] **REC-04**: System implements at least one collaborative-filtering method.
- [ ] **REC-05**: System implements a hybrid recommender.
- [ ] **REC-06**: User without sufficient history receives recommendations through an explicit cold-start strategy.
- [ ] **REC-07**: Recommendations exclude already-consumed games according to configured rules.
- [ ] **REC-08**: Each recommendation presents a deterministic explanation grounded in actual model evidence.
- [ ] **REC-09**: Published recommendation results retain the model, feature, and input-data versions used.

### Experimentation and Evaluation

- [ ] **EVAL-01**: All algorithms are compared with the same users, candidates, exclusions, and split manifests.
- [ ] **EVAL-02**: Transformations fit training data only and the test set remains isolated from tuning.
- [ ] **EVAL-03**: Protocol fixes relevance, K, splits, metrics, and tuning budget before algorithm comparison.
- [ ] **EVAL-04**: Evaluation calculates justified accuracy and ranking metrics.
- [ ] **EVAL-05**: Evaluation calculates coverage, diversity, and novelty metrics.
- [ ] **EVAL-06**: Evaluation records execution time and resource consumption.
- [ ] **EVAL-07**: Results are reported by user cohort, including zero-history and sparse-history users.
- [ ] **EVAL-08**: Comparisons use multiple seeds, uncertainty estimates, and justified statistical tests.
- [ ] **EVAL-09**: Synthetic users are generated from contrasting, parameterised, and reproducible scenarios.
- [ ] **EVAL-10**: Conclusions distinguish synthetic simulation results from evidence about real users.
- [ ] **EVAL-11**: Every run records code, environment, dataset, split, seeds, parameters, model, and metric identities.
- [ ] **EVAL-12**: Stored artifacts allow aggregate results to be recalculated without rerunning an experiment.
- [ ] **EVAL-13**: Research panel compares algorithms, configurations, metrics, cohorts, and runs.
- [ ] **EVAL-14**: Research panel provides accessible tables and exports thesis-ready results and figures.

### Administration, Privacy, and Security

- [ ] **ADMIN-01**: Authorised administrator can manage demo users and catalogue data.
- [ ] **ADMIN-02**: Authorised administrator can supervise imports, jobs, and experiments without directly editing the database.
- [ ] **SEC-01**: Server validates every permission and tests access by role and ownership.
- [ ] **SEC-02**: No secret or API key is present in Git, browser bundles, logs, public images, or public artifacts.
- [ ] **SEC-03**: Database access uses an ORM or parameterised queries and is tested against SQL injection.
- [ ] **SEC-04**: Inputs and outputs are validated and protected against XSS, CSRF, and malicious content.
- [ ] **SEC-05**: External URLs and requests are constrained against SSRF, unsafe redirects, and URL manipulation.
- [ ] **SEC-06**: Application applies rate limits, secure headers, and non-sensitive production error handling.
- [ ] **SEC-07**: Delivery pipeline scans secrets, vulnerable dependencies, and insecure code.
- [ ] **SEC-08**: Sensitive actions create audit events without recording credentials or secrets.
- [ ] **PRIV-01**: Public projections use an explicit allowlist of fields.
- [ ] **PRIV-02**: A controlled account can be deleted or anonymised.

### Operations, Quality, and Delivery

- [ ] **OPS-01**: Application can be deployed to the Internet using documented configuration.
- [ ] **OPS-02**: Project can be run locally through a reproducible documented process.
- [ ] **OPS-03**: A lawful offline demo mode works without the external API or Internet access.
- [ ] **OPS-04**: PostgreSQL and experimental artifacts have tested backup and recovery procedures.
- [ ] **OPS-05**: System emits structured logs and observable job states without sensitive data.
- [ ] **QUAL-01**: Project has unit, integration, and browser tests for critical workflows.
- [ ] **QUAL-02**: A clean installation can reproduce experiments and their evidence.
- [ ] **QUAL-03**: Core workflows are responsive and verifiable against WCAG 2.2 AA.
- [ ] **QUAL-04**: Charts and visualisations provide accessible textual or tabular alternatives.

### Thesis and Agent-Assisted Methodology

- [ ] **DOC-01**: Architecture and technology decisions record alternatives and rationale.
- [ ] **DOC-02**: Dataset, API, data model, and normalisation processes are documented.
- [ ] **DOC-03**: Each algorithm documents its theory, formulation, parameters, and limitations.
- [ ] **DOC-04**: Experimental protocol, metrics, results, and threats to validity are documented.
- [ ] **DOC-05**: Thesis tables and figures are generated from immutable experiment artifacts.
- [ ] **DOC-06**: Future example theses, formatting rules, and lecturer annotations are registered as canonical project references.
- [ ] **AGENT-01**: Project records the roles and responsibilities of agents used.
- [ ] **AGENT-02**: Project retains relevant protocols or prompts, configuration, models, tools, and generated artifacts.
- [ ] **AGENT-03**: Evidence distinguishes agent proposals, automated verification, and author decisions.
- [ ] **AGENT-04**: Methodology documents controls against hallucination, bias, error, and information exposure.
- [ ] **AGENT-05**: Methodology analyses reproducibility, costs, limitations, and threats to validity of agent-assisted work.
- [ ] **AGENT-06**: AI use is disclosed according to future university rules and lecturer guidance.

## v2 Requirements

### Extended Collection

- **DIARY-01**: User can record play sessions, dates, and time played.
- **REVIEW-01**: User can mark and reveal spoiler-containing review content.
- **PRIV-03**: User can configure visibility for individual lists and collection items.

### Social and Integrations

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
| Full social network in v1 | Public profiles meet the initial Letterboxd/Goodreads-inspired scope without moderation-heavy community features. |
| Open production registration in v1 | Initial release is a controlled academic demonstration. |
| Real-time or continuous model training | Offline, versioned training is safer and more reproducible for the thesis. |
| Generative recommendation explanations | Deterministic evidence-based explanations are more faithful and auditable. |
| Microservices or Kubernetes by default | They add operational complexity without evidence of a scaling need. |
| Marketplace, valuation, or trading | These do not support the collection-and-recommendation core value. |
| Storage of storefront credentials, keys, or receipts | Avoids unnecessary sensitive-data and security risk. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| PROF-02 | Phase 1 | Pending |
| CAT-01 | Phase 1 | Pending |
| CAT-03 | Phase 1 | Pending |
| CAT-04 | Phase 1 | Complete |
| CAT-06 | Phase 1 | Pending |
| LIB-01 | Phase 1 | Pending |
| LIB-02 | Phase 1 | Pending |
| INV-01 | Phase 1 | Pending |
| INV-02 | Phase 1 | Pending |
| INV-05 | Phase 1 | Complete |
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| REC-02 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| OPS-01 | Phase 1 | Pending |
| OPS-02 | Phase 1 | Pending |
| OPS-03 | Phase 1 | Pending |
| QUAL-03 | Phase 1 | Pending |
| DOC-01 | Phase 1 | Pending |
| AGENT-01 | Phase 1 | Pending |
| AGENT-02 | Phase 1 | Pending |
| AGENT-03 | Phase 1 | Pending |
| AUTH-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| EVAL-01 | Phase 2 | Pending |
| EVAL-02 | Phase 2 | Pending |
| EVAL-03 | Phase 2 | Pending |
| EVAL-09 | Phase 2 | Pending |
| EVAL-10 | Phase 2 | Pending |
| DOC-04 | Phase 2 | Pending |
| AGENT-04 | Phase 2 | Pending |
| PROF-01 | Phase 3 | Pending |
| LIB-03 | Phase 3 | Pending |
| LIB-04 | Phase 3 | Pending |
| INV-03 | Phase 3 | Pending |
| INV-04 | Phase 3 | Pending |
| PORT-01 | Phase 3 | Pending |
| PORT-02 | Phase 3 | Pending |
| PORT-03 | Phase 3 | Pending |
| PORT-04 | Phase 3 | Pending |
| PRIV-01 | Phase 3 | Pending |
| PROF-03 | Phase 4 | Pending |
| PROF-04 | Phase 4 | Pending |
| CAT-02 | Phase 4 | Pending |
| CAT-05 | Phase 4 | Pending |
| DATA-04 | Phase 4 | Pending |
| DATA-05 | Phase 4 | Pending |
| DATA-06 | Phase 4 | Pending |
| DATA-07 | Phase 4 | Pending |
| DATA-08 | Phase 4 | Pending |
| REC-01 | Phase 5 | Pending |
| EVAL-04 | Phase 5 | Pending |
| EVAL-05 | Phase 5 | Pending |
| EVAL-06 | Phase 5 | Pending |
| EVAL-07 | Phase 5 | Pending |
| EVAL-08 | Phase 5 | Pending |
| EVAL-11 | Phase 5 | Pending |
| EVAL-12 | Phase 5 | Pending |
| QUAL-02 | Phase 5 | Pending |
| REC-03 | Phase 6 | Pending |
| REC-06 | Phase 6 | Pending |
| REC-07 | Phase 6 | Pending |
| REC-08 | Phase 6 | Pending |
| REC-09 | Phase 6 | Pending |
| REC-04 | Phase 7 | Pending |
| REC-05 | Phase 7 | Pending |
| DOC-03 | Phase 7 | Pending |
| EVAL-13 | Phase 8 | Pending |
| EVAL-14 | Phase 8 | Pending |
| ADMIN-01 | Phase 8 | Pending |
| ADMIN-02 | Phase 8 | Pending |
| SEC-01 | Phase 8 | Pending |
| SEC-03 | Phase 8 | Pending |
| SEC-04 | Phase 8 | Pending |
| SEC-05 | Phase 8 | Pending |
| SEC-06 | Phase 8 | Pending |
| SEC-07 | Phase 8 | Pending |
| SEC-08 | Phase 8 | Pending |
| PRIV-02 | Phase 8 | Pending |
| OPS-04 | Phase 8 | Pending |
| OPS-05 | Phase 8 | Pending |
| QUAL-01 | Phase 8 | Pending |
| QUAL-04 | Phase 8 | Pending |
| DOC-02 | Phase 8 | Pending |
| DOC-05 | Phase 8 | Pending |
| DOC-06 | Phase 8 | Pending |
| AGENT-05 | Phase 8 | Pending |
| AGENT-06 | Phase 8 | Pending |

**Coverage:**

- v1 requirements: 89 total
- Mapped to phases: 89
- Unmapped: 0

---
*Requirements defined: 2026-09-04*
*Last updated: 2026-09-04 after initial definition*
