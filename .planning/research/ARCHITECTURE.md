# Architecture Research

**Domain:** Video-game collection web application and reproducible academic recommender-system laboratory
**Researched:** 2026-09-04
**Confidence:** HIGH for component boundaries and experiment isolation; MEDIUM for exact deployment sizing, which depends on the final stack and dataset volume

## Recommended Architecture

### System Overview

Use a **modular monolith for the product** and a **separate offline worker for data/ML workloads**. This keeps the thesis-sized system operable while enforcing the boundary that matters: interactive transactions must not share a process or lifecycle with ingestion, synthetic-data generation, training, or evaluation.

```text
+--------------------------- Web / Browser ----------------------------+
| Collection | Inventory | Public profile | Recommendations | Lab UI   |
+-------------------------------+--------------------------------------+
                                | HTTPS / JSON
+-------------------------------v--------------------------------------+
|                       Product API (modular monolith)                  |
| Auth | Catalogue | Library & inventory | Profiles | Recommendation   |
| orchestration | Experiment read API | Import/export                  |
+-----------+-------------------+-------------------------+------------+
            | transactional SQL | create job / read state | enrich
            v                   v                         v
+---------------------+  +---------------------+  +--------------------+
| PostgreSQL          |  | Durable job records |  | Legal live game   |
| app + provenance +  |  | (initially in DB)   |  | metadata API      |
| serving projections |  +----------+----------+  +---------+----------+
+----------+----------+             | worker claim/poll               |
           ^                        v                                  |
           |             +---------------------------+                 |
           |             | Offline research worker   |                 |
           |             | ingest -> normalize ->    |                 |
           |             | synthesize -> split ->    |                 |
           |             | train -> evaluate ->      |                 |
           |             | publish serving snapshot  |                 |
           |             +-------------+-------------+                 |
           |                           |                               |
           |                +----------v------------------+            |
           +----------------+ Versioned artifact store   |            |
                            | datasets, models, reports, |            |
                            | plots + MLflow run metadata|            |
                            +-----------------------------+            |
```

The database is the transactional source of truth. Large immutable inputs and outputs belong in an artifact store (local filesystem/volume in the reproducible profile, object storage in the deployed profile), referenced by digest and URI. The API never calls the live enrichment service on a normal catalogue read and never trains a model during a request.

### Component Responsibilities

| Component | Owns | Does not own |
|---|---|---|
| Web client | Accessible workflows, responsive views, lab visualizations, job progress | Business invariants, recommender training |
| Identity/access module | Controlled accounts, roles (`user`, `researcher/admin`), profile visibility | Social graph or public registration |
| Catalogue module | Canonical game identity, normalized titles/genres/platforms, source assertions, quality flags | User ownership or raw provider payloads |
| Library module | Status, ratings, comments, lists, copies, editions, purchase/conservation metadata | Global game metadata |
| Public-profile module | Read projection of opted-in/controlled public activity | Independent duplicate user or library records |
| Provenance/ingestion module | Source registry, licence/terms record, retrieval event, raw snapshot digest, mapping decisions, field-level assertions | Silent overwrite of canonical data |
| Enrichment adapter | Provider authentication, rate limiting, caching, retries, raw-response capture, mapping to source assertions | Choosing research ground truth |
| Recommendation serving module | Select active model/snapshot, gather candidates, score/re-rank, filter owned/disliked games, attach explanations | Training or evaluation |
| Synthetic-data generator | Seeded user archetypes, interaction histories, constraint checks, manifest | Mixing synthetic identities with real users without a cohort marker |
| Experiment runner | Snapshot selection, split policy, algorithm configuration, deterministic seeds, training, metrics, timings, statistical outputs | Mutating application ratings during evaluation |
| Model/artifact registry | Immutable model bundle, feature schema, code/data/config digests, run linkage, promotion status | Treating a mutable filename as a model version |
| Research panel/read API | Compare runs, metrics and artifacts; expose limitations and provenance | Recomputing results in the browser |

## Data Model and Storage Boundaries

Keep normalized relational tables for stable product concepts and use JSON only at uncertain external boundaries.

| Store / schema | Representative records | Rule |
|---|---|---|
| `app` | users, games, platforms, genres, library entries, ratings, comments, lists, owned copies | Transactional, constrained, mutable through application services |
| `source` | sources, licences, retrievals, raw-object references, external IDs, field assertions, merge decisions | Append-first audit trail; never lose which source supplied a value |
| `recsys` | algorithm definitions, model versions, active serving pointer, recommendation snapshots, explanations | Published outputs only; model activation is an explicit transaction |
| `research` | dataset snapshots, cohorts, generator manifests, split manifests, experiment/run references, aggregate metrics | Immutable identity by digest; corrections create a new version |
| artifact store | raw/normalized Parquet, fitted models, sparse matrices, plots, per-user result tables, reports | Content-addressed or run-scoped; checksum every artifact |
| MLflow backend/artifacts | run metadata, parameters, metrics, dataset inputs and artifacts | Research traceability and comparison, not product domain state |

External JSON payloads may be retained verbatim (compressed artifact plus checksum); queryable provider-specific extras may use `jsonb`. Promote fields into normalized columns only when the application or experiment semantics depend on them. PostgreSQL documents that `jsonb` supports containment and indexed searches, but that capability is not a reason to make the canonical catalogue schemaless.

## Online Recommendation Path

Google's reference architecture separates **candidate generation, scoring, and re-ranking**. Adopt those as explicit interfaces even if the MVP implementations are simple.

```text
GET /users/{id}/recommendations
  -> load user/library feature snapshot
  -> cold-start router (insufficient interactions?)
  -> candidate generators
       content model | collaborative model | popularity/editorial fallback
  -> scorer or hybrid score combiner
  -> re-ranker
       remove owned/disliked/unavailable; apply diversity constraint
  -> explanation builder
       reason codes + supporting features/source + model version
  -> persist/return recommendation snapshot
```

For the controlled demo, **precompute collaborative and hybrid outputs after a model is published**; permit lightweight content scoring on demand only if its feature matrix is already built and latency is bounded. Every response records `model_version_id`, `feature_snapshot_id`, generation time, constituent scores, rank, and explanation payload. This makes a screenshot or exported recommendation traceable to the exact model and data.

Cold start is a routing policy, not a special case hidden inside collaborative filtering: anonymous/no-history users receive popularity-with-diversity; a short onboarding preference set enables content-based results; sufficiently active users become eligible for collaborative/hybrid models.

## Offline Research and Synthetic-Data Flow

```text
Stable cited dataset + captured enrichment snapshot
  -> validate licence, schema, identifiers, checksums
  -> canonical mapping (source assertions remain intact)
  -> immutable dataset snapshot manifest
  -> seeded synthetic cohort specification
  -> generated users/interactions + validation report
  -> frozen experiment input snapshot
  -> deterministic train/validation/test split manifest
  -> fit content / collaborative / hybrid under common protocol
  -> candidate generation + scoring + re-ranking
  -> relevance + coverage + diversity + novelty + timing metrics
  -> per-user outputs, aggregate tables, plots, environment manifest
  -> immutable run + optional promotion to serving model
```

Synthetic generation must be a pure, parameterized pipeline: the manifest includes generator version, master seed and derived seeds, archetype distribution, sparsity/activity targets, rating/noise model, timestamps, catalogue snapshot digest, and validation statistics. Generate into a separate cohort namespace, then freeze a snapshot. Do not let later live enrichment alter the item features used by an already-defined experiment.

Use global temporal cutoffs whenever timestamps are meaningful. Recent RecSys research shows that ignoring the global timeline can leak future interactions and reorder model comparisons. Where a non-temporal split is intentionally used for a controlled synthetic question, record and justify it and run all compared algorithms against the same split manifest.

## Experiment and Provenance Contract

An experiment is reproducible only when its identity closes over all relevant inputs:

```text
run_id = reference to {
  git_commit,
  container/environment digest,
  dataset_snapshot_digest,
  source/licence/retrieval manifest,
  synthetic_generator_config + seeds,
  split_manifest_digest,
  feature_pipeline version,
  algorithm + hyperparameters,
  evaluation protocol + metric definitions
}
```

MLflow is appropriate for the run ledger because its official tracking model records code versions, parameters, metrics, dataset inputs, models, and arbitrary output artifacts. Keep thesis-specific semantic records (dataset licence, hypotheses, split rationale, threats to validity, model promotion decision) in first-class project/database records linked to the MLflow run; do not expect a generic tracker to infer them.

Persist both aggregate metrics and the per-user/per-item recommendation/evaluation table needed to recompute aggregates. Store timing context (hardware/CPU, concurrency, warm-up, repetitions) alongside durations. A promoted model is a copied/immutable model bundle plus a database pointer changed atomically; never serve “latest”.

## Internal Communication Boundaries

| Boundary | Communication | Contract |
|---|---|---|
| Web -> API | Versioned HTTP/JSON | DTOs; no database-shaped payloads |
| API module -> module | In-process application interfaces | Only owning module writes its tables |
| API -> worker | Durable job row with type, input snapshot IDs and idempotency key | Return `202`; UI polls job/read endpoints |
| Worker -> artifacts | Immutable writes followed by checksum verification | Publish DB references only after complete write |
| Worker -> serving | Transaction inserts model/snapshot then changes active pointer | Readers see old or new complete version, never partial state |
| Enrichment -> catalogue | Source assertions and an explicit deterministic merge policy | Raw response and retrieval metadata retained |
| Product -> MLflow | Read-only run links for panel, or tracker API through research service | Product transactions must not depend on tracker availability |

For a single-node demo, a PostgreSQL job table claimed with row locking is sufficient and removes Redis/RabbitMQ from the reproducibility burden. If concurrent users or retries outgrow it, replace only the job adapter with a broker-backed queue. FastAPI's own documentation advises separate multi-process tooling for heavy background computation and says background tasks should create their own resources, which supports the worker boundary.

## Recommended Repository Structure

```text
apps/
  web/                     # browser application
  api/                     # HTTP composition root; thin routes
  worker/                  # job runner and scheduled/one-off commands
packages/
  domain/                  # catalogue, library, profile entities/policies
  application/             # use cases and module ports
  infrastructure/          # PostgreSQL, artifact, API, queue adapters
  recommender/
    contracts/             # candidate/scorer/reranker protocols
    content/
    collaborative/
    hybrid/
    explain/
  research/
    ingest/                # source adapters and canonical mapping
    synthetic/             # seeded generators + validators
    datasets/              # snapshot/split builders
    evaluation/            # metrics, statistics, reports
db/
  migrations/              # schema-owned migrations
experiments/
  configs/                 # reviewed run specifications, not ad-hoc notebooks
  notebooks/               # exploration only; import production pipeline code
  reports/                 # generated summaries or pointers to artifacts
data/
  README.md                 # acquisition/licensing instructions; no unlicensed blobs
deploy/
  compose.yaml              # local reproducible topology
tests/
  unit/ integration/ contract/ experiment/
```

The language boundary may be one repository even if the web stack differs from Python. Crucially, algorithm implementations and metrics are importable, tested modules invoked by both CLI/worker and notebooks; notebooks must not contain the only copy of experiment logic.

## Deployment Topology

### Local reproducible profile

Docker Compose should define `web`, `api`, `worker`, `postgres`, and optionally `mlflow`, with named volumes for database and artifacts. Docker documents Compose as a single YAML model for services, networks and volumes and supports the same definition across development, CI, staging and production. Pin image and dependency versions; provide acquisition commands for redistributable datasets rather than committing questionable data.

### Deployed demo profile

Deploy the same web/API/worker images with managed PostgreSQL and durable object storage. Run MLflow privately or expose only a curated research panel; an academic demo does not need a public tracking/admin surface. Schedule enrichment and training explicitly, enforce API quotas/secrets server-side, back up database plus artifacts, and health-check API and worker separately.

Avoid Kubernetes and microservices for v1. They add operational variables without improving the thesis comparison. The product modular monolith and separately scalable worker are the useful seams.

## Dependency-Driven Build Order

1. **Reproducible skeleton and contracts** — repository boundaries, containers/Compose, migrations, configuration, CI, deterministic clock/seed helpers, job and artifact interfaces.
2. **Canonical catalogue plus provenance** — source/licence/retrieval model, canonical IDs, external-ID mapping, raw snapshot/checksum contract. Every downstream feature and experiment depends on stable item identity.
3. **Stable dataset ingestion snapshot** — acquire, validate, normalize, quality-report, freeze and cite one dataset before building recommendation logic.
4. **Core product vertical slice** — controlled auth; catalogue browse; statuses, ratings, comments, lists; copy inventory; import/export. These define real domain records and interaction semantics.
5. **Public read models and enrichment** — public profiles, cached enrichment adapter, deterministic merge policy and refresh jobs. Build only after canonical/source boundaries prevent live data from contaminating fixed research inputs.
6. **Synthetic cohort pipeline** — archetypes, seeded histories/timestamps, invariant checks and immutable manifests, using the now-stable catalogue and interaction schema.
7. **Experiment harness and simple baselines** — frozen splits, popularity/random baselines, common candidate/evaluation interface, MLflow/artifact logging, relevance and beyond-accuracy metric tests. Validate the measuring instrument before sophisticated models.
8. **Content-based path plus cold start/explanations** — feature snapshot, content candidates/scores, onboarding route, reason codes; first end-to-end online recommendation.
9. **Collaborative then hybrid path** — collaborative model consumes sufficient synthetic interactions; hybrid reuses the same contracts and common split, then candidate fusion/scoring/re-ranking.
10. **Research comparison panel and model promotion** — run comparisons, timings, plots, provenance drill-down, active-model transaction and precomputed serving snapshots.
11. **Hardening and evidence freeze** — accessibility/responsiveness, retries/idempotency, backups, deployment, fresh-machine reproduction, final fixed experiment matrix and thesis export bundle.

**Ordering rationale:** catalogue identity/provenance precedes all datasets; product interaction semantics precede synthetic generation; synthetic data and a frozen split precede collaborative work; the evaluation harness and trivial baselines precede claims about algorithms; individual recommenders precede hybridization; only complete immutable runs can feed the panel and promotion workflow.

## Scaling and Failure Considerations

| Scale | Adjustment |
|---|---|
| Controlled demo / <1k accounts | One API, one worker, PostgreSQL job table, local or single-bucket artifacts, precomputed recs |
| 1k-100k accounts | Add broker-backed queue, multiple workers, object storage/CDN, incremental feature builds and cached serving snapshots |
| 100k+ accounts | Separate recommendation serving, feature/event pipelines and online experimentation only after measured pressure; shard/partition by real access patterns |

The likely first bottleneck is repeated full-matrix training or scoring, not HTTP routing. Address it with sparse representations, offline materialization, incremental jobs and snapshot caching. The second is enrichment quota/latency; address it with durable caching, scheduled refresh, backoff and a stale-but-valid catalogue response.

Design every job for retry: explicit status transitions, heartbeat/lease, idempotency key, immutable inputs, attempt log, and publish-on-success. A failed run must leave a visible failed record and partial artifacts quarantined, never change the active model.

## Anti-Patterns to Avoid

### One mutable “games” row with no assertions

**Failure:** Dataset and API fields silently overwrite each other, destroying citation and reproducibility.  
**Instead:** Retain source assertions and retrievals; derive the canonical presentation through a versioned precedence policy.

### Training inside HTTP requests

**Failure:** Timeouts, resource contention, unrecoverable partial runs and untraceable parameters.  
**Instead:** Enqueue an immutable run specification, execute in a worker, return status and read stored outputs.

### Live enrichment in experiment features

**Failure:** The same code/config produces different input data tomorrow.  
**Instead:** Snapshot enrichments when legally permitted and reference a digest; otherwise exclude them from the fixed research feature set.

### Separate bespoke pipelines per algorithm

**Failure:** Different filtering/splits/candidate universes invalidate comparisons.  
**Instead:** Share snapshot, split, candidate-universe and evaluation contracts; vary only declared algorithm components.

### “Seeded” but environmentally nondeterministic experiments

**Failure:** One seed does not control library RNGs, input ordering, parallelism or dependency changes.  
**Instead:** Record derived seeds, sorted inputs, package/container digest and deterministic settings; repeat runs and report variance where exact determinism is unavailable.

### Metrics-only experiment storage

**Failure:** Aggregate values cannot be audited or recomputed, and thesis figures become disconnected from predictions.  
**Instead:** Store per-case rankings/scores, aggregate metrics, run config, logs, plots and environment manifest under the same run.

## Sources

- [Google for Developers — Recommendation systems overview](https://developers.google.com/machine-learning/recommendation/overview/types) (candidate generation, scoring, re-ranking; updated 2025-08-25; HIGH authority)
- [Google for Developers — Re-ranking](https://developers.google.com/machine-learning/recommendation/dnn/re-ranking) (filters, diversity and freshness; HIGH authority)
- [MLflow — Tracking](https://mlflow.org/docs/latest/tracking) (runs, code versions, parameters, metrics, datasets, models and artifact stores; official documentation; HIGH authority)
- [FastAPI — Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) (heavy computation should use separate multi-process tooling; official documentation; HIGH authority)
- [FastAPI — Advanced Dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies/) (background jobs should acquire their own resources; official documentation; HIGH authority)
- [PostgreSQL — JSON functions and operators](https://www.postgresql.org/docs/current/functions-json.html) (`jsonb` query/index capabilities; official documentation; HIGH authority)
- [Docker — Compose](https://docs.docker.com/compose/) (reproducible multi-container application model; official documentation; HIGH authority)
- [Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders](https://doi.org/10.1145/3705328.3748164) (RecSys 2025; temporal leakage and split selection; peer-reviewed; HIGH authority)
- [A Critical Study on Data Leakage in Recommender System Offline Evaluation](https://arxiv.org/abs/2010.11060) (timeline-aware offline evaluation; preprint/independent cross-check; MEDIUM authority)
- [Offline evaluation options for recommender systems](https://doi.org/10.1007/s10791-020-09371-3) (evaluation design choices materially affect conclusions; peer-reviewed; HIGH authority)

---
*Architecture research for: SavePoint*  
*Researched: 2026-09-04*
