# Project Research Summary

**Project:** SavePoint
**Domain:** Video-game backlog and copy-level collection inventory with an academic recommender-system laboratory
**Researched:** 2026-09-04
**Confidence:** MEDIUM-HIGH

## Executive Summary

SavePoint is two deliberately separated products sharing one domain model: an accessible catalogue, backlog, inventory, and public-profile application for controlled users; and a reproducible laboratory comparing content-based, collaborative, and hybrid recommenders. Experts build this class of system around stable item identity, relational constraints, immutable experimental inputs, common evaluation contracts, and offline model jobs. The decisive architectural rule is to keep live catalogue enrichment and interactive product writes out of the fixed research data plane.

The recommended implementation is a modular monolith: Next.js 16.2/React 19.2/strict TypeScript 6 for the browser, Django 5.2 LTS/DRF 3.18 on Python 3.13 for the API and domain services, and PostgreSQL 18 as the source of truth. A separate offline Python worker uses NumPy/SciPy/pandas/scikit-learn, focused classical recommender implementations, and MLflow to create versioned datasets, synthetic cohorts, splits, models, metrics, and evidence bundles. Docker Compose, lockfiles, immutable artifacts, checksums, and one-command runs make the local and deployed demonstrations defensible. PostgreSQL 17 is the approved fallback if the selected host has not validated 18; exact package patches must be resolved together in the target Linux container before the stack is frozen.

The largest risks are legal ambiguity around datasets and assets, contamination by mutable API data, leakage or unfair comparisons, synthetic users that favor the tested model, and claims that exceed what offline evaluation establishes. Mitigate these before algorithm work: approve a source/licence register and publication decision; freeze a checksummed research corpus; preregister split, candidates, metrics, cohorts, tuning budgets, and uncertainty reporting; run contrasting synthetic scenarios over predefined seeds; and generate all thesis tables from immutable run artifacts. Scope is also a research risk: preserve the vertical academic spine and defer social networking, open registration, continuous retraining, storefront synchronization, neural recommenders, and other operationally expensive features.

## Key Findings

### Recommended Stack

Use one repository and one Python-centered research environment, with a typed web boundary and a separate worker lifecycle. The detailed rationale and version evidence are in [STACK.md](./STACK.md). Exact fast-moving patches are recommendations to validate in lockfiles, not permanent thesis facts.

**Core technologies:**

- **Python 3.13 + Django 5.2.17 LTS + DRF 3.18:** relational domain, authentication, admin, migrations, API, ingestion, and research code in a maintainable ecosystem.
- **PostgreSQL 18.6:** canonical store for users, games, provenance, inventory, experiment references, and published recommendations; use PostgreSQL 17 consistently if hosting support requires it.
- **Next.js 16.2 + React 19.2 + strict TypeScript 6 + Node 24 LTS:** responsive public pages, authenticated workflows, and an accessible research dashboard with a generated API contract.
- **NumPy 2.5, SciPy 1.18, pandas 3.0, scikit-learn 1.9:** sparse feature pipelines, classical baselines, deterministic preprocessing, ranking, and explicit metric implementations.
- **MLflow 3.15 + immutable artifact storage:** experiment ledger and storage for configurations, manifests, models, per-case outputs, tables, and plots; thesis semantics remain first-class project records.
- **uv, pnpm, Docker Compose v2, and GitHub Actions:** locked dependencies, reproducible containers, PostgreSQL integration tests, schema diffing, browser tests, and clean-environment verification.
- **pytest/Hypothesis, Vitest/Testing Library, Playwright/axe:** domain invariants, metric and generator properties, user workflows, cross-browser behavior, and WCAG-oriented regression checks.

Do not introduce microservices, Kubernetes, MongoDB, a vector database, online training, or neural recommendation by default. Precompute collaborative/hybrid results; add a broker, cache, or separate serving service only after measured pressure demonstrates a need.

### Expected Features

SavePoint's feature boundary is intentionally narrower than Goodreads or Letterboxd and broader than a flat backlog because it represents owned artifacts and thesis evidence. See [FEATURES.md](./FEATURES.md) for atomic boundaries and dependencies.

**Must have — product table stakes:**

- Controlled sign-in; searchable attributable catalogue; stable canonical game/platform/edition identifiers.
- Backlog statuses, ratings, plain-text comments, ordered custom lists, and useful sorting/filtering.
- Separate user-game state from multiple physical/digital owned-copy records, with the agreed fixed inventory fields.
- Public profile and shareable public lists through an explicit allowlist; never expose purchase, storage, account, or private-note fields.
- Versioned CSV/JSON export, then staged import with preview, row errors, deterministic matching, duplicate/conflict rules, and formula-injection defenses.
- Ranked unseen recommendations, faithful deterministic explanations, and disclosed zero-history/sparse-user fallback behavior.
- Responsive WCAG 2.2 AA-oriented workflows, including keyboard/focus/reflow checks and text/table equivalents for charts.

**Must have — academic table stakes and primary differentiators:**

- A licensed, citable, immutable dataset snapshot with provenance, checksum, data dictionary, quality report, and publication decision.
- Parameterized synthetic cohorts with scenario labels, independent seeds, manifests, invariant checks, and sensitivity analysis.
- Content-based, collaborative, and hybrid recommenders sharing candidates, exclusions, split manifests, output schema, tuning budget, and evaluation protocol.
- Popularity and random baselines; fixed-K relevance/ranking metrics plus coverage, diversity, novelty, runtime, per-cohort results, uncertainty, and paired comparisons.
- Reproducible experiment runs recording code/environment/data/split/model/metric identities and preserving per-user results sufficient to recompute aggregates.
- Accessible comparison dashboard and machine-readable evidence bundle generated from immutable artifacts, including failed runs and threats to validity.

**Should have after validation (v1.x):** bulk editing, richer/saved filters, extra cold-start elicitation, optional inventory photos, or one storefront adapter only when observed workflow needs and rights/security constraints justify them.

**Defer to v2+ or exclude:** social graph/feed/reactions, open registration, community catalogue editing, fine-grained privacy, gameplay diary, native clients, automatic multi-store sync, market valuation/trading, sensitive keys/receipts, real-time retraining, generative explanations, and deep models without a justified research question and adequate data.

### Architecture Approach

Use a modular Django product monolith plus a separately invoked offline worker, connected through durable idempotent job records and immutable artifact references. The API owns transactions and read projections; the worker owns ingestion, normalization, synthesis, splitting, training, evaluation, and publication. PostgreSQL contains normalized application data and metadata references, while content-addressed/run-scoped storage holds large datasets, sparse matrices, models, and reports. Research snapshots are immutable; live enrichment is a replaceable backend-only cache mapped through source assertions and an explicit precedence policy. Full boundaries and flows are in [ARCHITECTURE.md](./ARCHITECTURE.md).

**Major components:**

1. **Web client** — accessible collection, inventory, profile, recommendation, and researcher views; no business rules or training.
2. **Product API modules** — controlled identity, catalogue, library/copies, public projections, import/export, recommendation serving, and experiment read APIs.
3. **Provenance and enrichment boundary** — source/licence/retrieval registry, raw snapshots, external-ID crosswalk, deterministic merges, caching, rate limits, and offline fallback.
4. **Offline research worker** — dataset freezing, seeded synthetic generation, split-first preprocessing, baselines/models, evaluation, statistics, and evidence generation.
5. **PostgreSQL job/metadata store** — transactional state, retryable job lifecycle, model activation pointer, immutable snapshot/run identities, and published ranked outputs.
6. **Artifact and model registry** — checksummed dataset/model/result bundles linked to MLflow runs; publication occurs only after complete verified writes.

Follow explicit candidate-generation, scoring, re-ranking, and explanation interfaces. Route cold start from popularity-with-diversity to content and then hybrid as evidence accumulates. A recommendation snapshot must retain model/feature versions, constituent evidence, ranks, exclusions, and reason codes so later metadata changes cannot rewrite history.

### Critical Pitfalls

1. **Accessible data is not necessarily licensed research data** — approve source, asset, caching, attribution, and redistribution terms before ingestion; publish acquisition scripts/checksums or lawful fixtures when redistribution is disallowed.
2. **Live enrichment contaminates experimental evidence** — isolate immutable research snapshots from replaceable product enrichment and prove experiments reproduce with the API disabled.
3. **Leakage and unfair comparison invalidate model rankings** — freeze temporal or justified split manifests first; fit transformations on training only; tune on validation; keep test untouched; use identical users, candidates, exclusions, and budgets.
4. **Synthetic volume is mistaken for external validity** — use multiple contrasting generators and independent seeds, avoid reusing the evaluated scoring assumptions, report sensitivity, and state that conclusions are simulation-bound.
5. **A narrow leaderboard becomes an overclaim** — preregister task-aligned metrics/K, baselines, cold cohorts, uncertainty, and paired comparisons; report trade-offs rather than a universal winner.
6. **A seed is mistaken for reproducibility** — bind every run to code, dirty-state flag, image and dependency digests, dataset/split/feature versions, all derived seeds, hardware/timing context, and artifact hashes; rehearse from a clean checkout.
7. **Third-party API and accessibility work is postponed** — use a server-side adapter with rate-limit/auth/failure contract tests and an offline demo path; enforce WCAG criteria in shared components from the first UI slice.
8. **The TFG grows into several products** — phase-gate the academic spine and treat excluded social, marketplace, synchronization, and operational features as future work.

## Implications for Roadmap

Based on the combined dependencies, use eight outcome-oriented phases. Each phase must emit thesis-ready rationale, tests, manifests, and limitations rather than deferring documentation to the end.

### Phase 1: Reproducible Foundation and Data Governance

**Rationale:** Every feature and result depends on stable identity, legal data use, repeatable environments, and an immutable/mutable boundary.

**Delivers:** repository/module skeleton; pinned toolchains and Compose topology; PostgreSQL migrations; CI; clock/seed/job/artifact contracts; canonical catalogue/source schema; source and asset register; dataset/API selection decision; licence/attribution/redistribution record; fixed corpus acquisition, normalization, checksum, data dictionary, and quality report.

**Addresses:** stable catalogue, provenance registry, citable dataset, deployment foundation.

**Avoids:** rights failure, provider-ID-as-identity, fixed/live contamination, unpinned environments, and scope drift.

### Phase 2: Evaluation and Synthetic-Data Contract

**Rationale:** The measuring instrument must be specified before algorithms can optimize against it or accidentally leak information.

**Delivers:** interaction semantics; hypotheses/estimands; candidate/exclusion and split manifests; fixed K; metric formulas and tests; baseline/tuning/statistical protocol; zero-history, onboarding, sparse-user, new-item, and warm cohorts; parameterized contrasting synthetic scenarios with independent seeds, validation reports, and threats-to-validity template.

**Addresses:** deterministic synthetic users, comparable algorithms, cold-start evaluation, multi-objective metrics, limitations record.

**Avoids:** leakage, unequal comparisons, post-hoc metric choices, hidden cold entities, and self-fulfilling synthetic evidence.

### Phase 3: Core Collection Product

**Rationale:** Stable catalogue and interaction semantics now support the user-facing domain and the records later consumed by recommendation workflows.

**Delivers:** controlled authentication; catalogue browse/detail/search; backlog states; ratings/comments; lists; separate physical/digital copy inventory; public-field policy; accessible shared primitives; versioned export followed by staged import/preview and round-trip tests.

**Addresses:** the full core product table stakes except public presentation and recommendations.

**Avoids:** ownership/status conflation, one-copy schema rewrites, unsafe public exposure, destructive imports, CSV injection, and late accessibility retrofit.

### Phase 4: Public Profiles and Resilient Enrichment

**Rationale:** Live/current presentation is safe only after canonical identity, provenance, and public projection boundaries exist.

**Delivers:** public profile/list read models; backend provider adapter; authentication refresh, batching, permitted caching, attribution, timeout/429/schema tests, deterministic merge policy, refresh jobs, stale state, placeholders, and prewarmed or lawful fixed offline fallback.

**Addresses:** public profiles and broad/current attributable metadata.

**Avoids:** secret leakage, N+1 provider calls, provider lock-in, mutable research features, missing attribution, and a presentation dependent on internet availability.

### Phase 5: Experiment Harness and Baselines

**Rationale:** Run storage, trivial baselines, and metric recomputation must validate the evaluation apparatus before sophisticated recommenders are credited.

**Delivers:** durable idempotent run jobs; MLflow/project run linkage; immutable manifests/artifacts; random and popularity baselines; shared candidate/scoring/evaluation interfaces; per-user outputs; aggregate metrics, runtime context, dispersion/paired comparison support; failed-run handling; one-command clean-environment reproduction.

**Addresses:** reproducible experiment runner, evidence bundle foundation, evaluation metric suite.

**Avoids:** notebook-only logic, metrics-only storage, mutable `latest` models, single-run evidence, and hand-copied thesis results.

### Phase 6: Content Recommendations, Cold Start, and Explanations

**Rationale:** Content recommendation validates the fixed feature pipeline and is the first personalized path available without dense interactions.

**Delivers:** immutable content-feature snapshot; sparse TF-IDF/encoded metadata pipeline; content candidates/scores; onboarding preferences; popularity/content cold-start router; exclusions and diversity re-ranking; persisted top-N results; deterministic reason codes and evidence; accessible product recommendation flow.

**Addresses:** content-based comparison, personalized list, cold-start behavior, traceable explanations.

**Avoids:** all-data preprocessing, generic or unfaithful explanations, full pairwise memory growth, and empty new-user experiences.

### Phase 7: Collaborative and Hybrid Comparison

**Rationale:** Collaborative work requires frozen interactions and harness; hybridization is meaningful only after both constituent paths share the same contract.

**Delivers:** validated collaborative baseline(s), then explicit hybrid fusion/weighting and common re-ranking; predefined hyperparameter searches on validation only; identical test/candidate protocol; multi-scenario and multi-seed evaluation; cohort metrics, uncertainty, sensitivity analysis, and bounded conclusions.

**Addresses:** collaborative and hybrid recommenders, side-by-side algorithm comparison, cold-start transition policy, multi-objective evaluation.

**Avoids:** incompatible algorithm pipelines, synthetic-generator favoritism, test-set tuning, incomparable raw scores, and unsupported superiority claims.

### Phase 8: Research Panel, Promotion, and Evidence Freeze

**Rationale:** The panel must consume complete immutable runs, and final deployment follows only after model publication, accessibility, resilience, and reproduction are proven.

**Delivers:** accessible chart/table comparison by run/configuration/cohort; provenance and limitation drill-down; CSV/JSON and thesis-ready table/figure exports; atomic model promotion and precomputed serving snapshots; backup/recovery; managed deployment; offline demo rehearsal; manual keyboard/screen-reader/zoom/mobile checks; clean-checkout reproduction and final experiment matrix.

**Addresses:** researcher panel, result export, deployed/local delivery, final recommendation serving, complete thesis evidence.

**Avoids:** dashboards recomputing raw events, charts as the only academic record, partial model activation, tracker/admin exposure, inaccessible visualizations, and an unreproducible final submission.

### Phase Ordering Rationale

- Canonical IDs, rights, provenance, and environment locks precede both product mutation and research snapshots.
- The evaluation and synthetic-data protocol precedes model implementation so algorithm choices cannot redefine the test.
- Product interaction and copy semantics precede generated histories; public/enrichment work follows the fixed/live separation.
- The experiment harness and trivial baselines precede content, collaborative, and hybrid claims; content precedes hybrid and supports cold start.
- Immutable runs precede the comparison panel and atomic promotion; hardening and evidence freeze consume only generated, traceable outputs.
- Accessibility, reproducibility, security, and thesis evidence are acceptance criteria in every phase, with final end-to-end gates in Phase 8.

### Research Flags

**Phases requiring deeper research during planning:**

- **Phase 1:** mandatory — choose the actual fixed dataset and enrichment provider only after case-specific licence/terms, asset rights, redistribution, identifier coverage, rate limits, host compatibility, and current cost/region review.
- **Phase 2:** mandatory — finalize task/estimand, temporal split, formulas, K, candidate universe, negative sampling, statistical tests, synthetic generator design, and external-validity language from recommender-methodology literature.
- **Phase 4:** targeted — research the selected provider's current authentication, schema, caching, attribution, quota, and failure behavior; patterns are standard but provider terms are not.
- **Phase 7:** mandatory — validate collaborative library/platform compatibility and select defensible collaborative/hybrid formulations and calibration methods under the frozen protocol.
- **Phase 8:** targeted — validate current PaaS/database/object-storage pricing, regional availability, backups, sleeping limits, and data-export terms before deployment.

**Phases with established patterns (skip broad research-phase):**

- **Phase 3:** Django relational CRUD, generated OpenAPI types, import preview, and accessible form/list patterns are mature; use focused design decisions for rating scale, inventory enums, visibility, and conflict policy.
- **Phase 5:** MLflow/artifact manifests, PostgreSQL job rows, baselines, and CI reproducibility are well documented once Phase 2 fixes the protocol.
- **Phase 6:** sparse classical content recommendation, deterministic explanations, and routing fallbacks are established; only the exact feature vocabulary and onboarding burden need validation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Architecture-level selections and support lines use official documentation. Exact 2026 patch compatibility, Linux wheels, hosting support, and prices must be proven in locks and containers. |
| Features | MEDIUM | Table stakes are corroborated across consumer and collector products; no user interviews exist, and several enum/visibility/import decisions are product choices. Academic table stakes are stronger than competitor evidence. |
| Architecture | HIGH | Modular monolith, offline worker, immutable artifacts, explicit source boundaries, and shared recommender contracts are strongly supported and fit thesis scale. Deployment sizing remains contextual. |
| Pitfalls | MEDIUM-HIGH | Legal/API/accessibility findings use primary sources and evaluation risks use peer-reviewed work; applying licences to a selected corpus and synthetic realism remain case-specific. |

**Overall confidence:** MEDIUM-HIGH. The system shape, build dependencies, and methodological safeguards are established. The unresolved items are concentrated in provider/corpus selection, precise experimental protocol, and product-policy details.

### Gaps to Address

- **Dataset and assets:** select the corpus, save the exact terms/version, document field- and asset-level rights, decide what may be cached and redistributed, and obtain university/legal review for ambiguity.
- **Enrichment provider:** choose only after current terms, attribution, identifiers, field completeness, quota, token lifecycle, downtime fallback, and replacement cost are verified.
- **Stack resolution:** generate `uv.lock` and `pnpm-lock.yaml` in the target Linux image; confirm scientific wheels and numerical smoke tests; use the same PostgreSQL major locally, in CI, and in production.
- **Experimental protocol:** freeze the user task, relevance definition, K, temporal/non-temporal rationale, candidates, negative sampling, tuning budget, metric formulas, repeated seeds, confidence intervals, and paired tests before recommender implementation.
- **Synthetic validity:** specify contrasting archetypes/scenarios mathematically, separate generator and model representations, compare lawful real-data marginals when possible, and keep all conclusions explicitly simulation-bound.
- **Product policy:** decide rating scale, list/profile visibility, public-field allowlist, exact physical/digital enums, canonical edition/duplicate handling, deletion semantics, and import conflict rules.
- **Explainability and cold start:** validate explanation faithfulness and accessibility, onboarding burden, transition thresholds, and cohort-specific acceptance criteria with a small structured lab/user assessment if feasible.
- **Deployment:** benchmark precomputed serving latency and artifact size before adding Redis/queues/object storage; select a platform only from current cost, region, backup, sleep, and export evidence.

## Sources

### Primary (HIGH confidence)

- [Django supported versions](https://www.djangoproject.com/download/), [DRF release notes](https://www.django-rest-framework.org/community/release-notes/), [PostgreSQL releases](https://www.postgresql.org/docs/release/), [Next.js 16.2](https://nextjs.org/blog/next-16-2), and [React versions](https://react.dev/versions) — framework and database support/version constraints.
- [NumPy news](https://numpy.org/news/), [SciPy news](https://scipy.org/news/), [pandas 3.0 notes](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html), [scikit-learn releases](https://scikit-learn.org/stable/whats_new.html), and [MLflow tracking](https://mlflow.org/docs/latest/tracking) — scientific stack behavior and experiment tracking.
- [Docker Compose](https://docs.docker.com/compose/) and [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — reproducible topology and accessibility requirements.
- [IGDB API documentation](https://api-docs.igdb.com/) and [RAWG API terms](https://rawg.io/tos_api) — authentication, quotas, caching/attribution, and operational/legal constraints to re-check at selection.
- [Directive 96/9/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31996L0009) and [European Commission database protection overview](https://digital-strategy.ec.europa.eu/en/policies/protection-databases) — EU database-rights context; not a project-specific legal determination.
- [Time to Split (RecSys 2025)](https://doi.org/10.1145/3705328.3748164), [Evaluating Recommender Systems](https://doi.org/10.1145/3556536), and [Improving Methodological Standards](https://doi.org/10.1145/3800587) — split sensitivity, multi-faceted evaluation, and limits of offline claims.

### Secondary (MEDIUM confidence)

- [Backloggd](https://backloggd.com/), [PLAYBACK](https://playback-archive.com/video-game-collection), [GameVentory](https://gameventory.app/), and [Game Collector](https://gamecollector.online/) — consumer backlog, collection, profile, inventory, and portability expectations.
- [Linux Foundation Recommenders evaluation](https://recommenders-team.github.io/recommenders/evaluation.html) — relevance and beyond-accuracy metric landscape.
- [Critical Study on Data Leakage](https://arxiv.org/abs/2010.11060) — corroborating analysis of timeline leakage in offline evaluation.
- [Implicit documentation](https://benfred.github.io/implicit/) — algorithm/library capabilities and packaging; exact compatibility must be tested.
- [Towards Understanding Bias in Synthetic Data for Evaluation](https://arxiv.org/abs/2506.10301) — recent threat-to-validity signal requiring cautious interpretation.

### Tertiary (LOW confidence)

- No low-confidence claim is adopted as a roadmap commitment. Hosting vendor, final dataset/provider, inventory-policy, and experimental-protocol choices remain explicitly open for phase-specific validation.

---
*Research completed: 2026-09-04*
*Ready for roadmap: yes*
