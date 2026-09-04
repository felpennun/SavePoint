# Stack Research

**Domain:** Video-game backlog, collection inventory, public profiles, and academic recommender-system web application
**Researched:** 2026-09-04
**Confidence:** MEDIUM overall; HIGH for architecture-level choices and officially documented release/support lines, MEDIUM for exact fast-moving package patches

## Recommendation in One Sentence

Build a modular monolith with a **Next.js 16.2 / React 19.2 / TypeScript 6 frontend**, a **Python 3.13 / Django 5.2 LTS / Django REST Framework 3.18 backend**, **PostgreSQL 18**, and an offline scientific-Python recommendation pipeline tracked by **MLflow 3.15**; run the complete system with Docker Compose locally and deploy the same container images to a managed container platform with managed PostgreSQL.

This deliberately keeps web/domain logic and research code in one Python repository and one relational source of truth, while retaining a separate, strongly typed UI. It is more defensible and reproducible than introducing microservices, a feature store, a vector database, Kubernetes, or a separate JVM recommender stack for a controlled TFG demonstration.

## Recommended Stack

### Core Technologies

| Technology | Version to pin | Purpose | Why Recommended |
|---|---:|---|---|
| Python | 3.13.x (exact patch in lock/toolchain file) | Backend and experiment language | One language spans Django, data preparation, baselines, evaluation, and reproducibility. Use 3.13 rather than the newest interpreter line to maximize binary-wheel compatibility across scientific and recommender packages. **Confidence: HIGH** |
| Django | 5.2.17 LTS | Domain model, authentication, admin, migrations, services | The inventory/catalogue domain is relational and CRUD-heavy; Django supplies mature auth, ORM, validation, migrations, and an admin UI. The 5.2 LTS security window runs to April 2028, making it preferable to shorter-lived 6.x for thesis maintenance. **Confidence: HIGH** |
| Django REST Framework | 3.18.0 | JSON API for the web client | Mature Django-native serializers, permissions, pagination, and test utilities. Keep business rules in Django services/models, not serializers. **Confidence: HIGH** |
| PostgreSQL | 18.6 | Canonical transactional and experiment-metadata database | Correct fit for normalized games, editions, ownership copies, lists, statuses, ratings, provenance, and constraints; also supports JSONB and full-text search when justified without adding another datastore. **Confidence: HIGH** |
| psycopg | 3.x, lock latest compatible patch | PostgreSQL driver | Current Django-recommended driver generation, with binary wheels for local/CI use and a production build option. **Confidence: HIGH** |
| Next.js | 16.2.x | Responsive web application and public profiles | App Router provides server rendering/metadata for public profiles while still supporting rich client interactions for collection and experiment dashboards. Next.js 16.2 is the active 16.x line and can run as an ordinary Node server in a container. **Confidence: HIGH** |
| React / React DOM | 19.2.7 | Component UI | Supported React generation used by Next.js 16, suitable for accessible reusable catalogue, forms, tables, and charts. **Confidence: HIGH** |
| TypeScript | 6.0.x, strict mode | Frontend type safety | Makes the API contract, inventory variants, recommendation explanations, and experiment result schemas explicit. Address TypeScript 6 deprecations rather than suppressing them in anticipation of TypeScript 7. **Confidence: HIGH** |
| Node.js | 24 LTS | Frontend build/runtime | Current LTS line and compatible with Next.js 16's Node >=20.9 requirement. Pin the exact image digest/version used by CI and deployment. **Confidence: HIGH** |
| Tailwind CSS | 4.3.x | Design tokens and responsive styling | CSS-first configuration and constrained utilities suit a one-developer accessible responsive UI without committing to a large component framework. **Confidence: HIGH** |

### Recommendation and Experiment Tooling

| Library | Version to pin | Purpose | When to Use |
|---|---:|---|---|
| NumPy | 2.5.2 | Arrays, deterministic numerical work | Shared foundation for feature vectors, rankings, metrics, and seeded synthetic generation. **Confidence: HIGH** |
| SciPy | 1.18.1 | Sparse matrices and scientific routines | Store user-item interactions sparsely; avoid dense matrices that scale with every user-game pair. **Confidence: HIGH** |
| pandas | 3.0.x (latest tested patch) | Dataset ingestion, cleaning, tabular results | Use at experiment/data boundaries, not as the application persistence layer. Explicitly normalize pandas 3 string and timezone semantics. **Confidence: HIGH** |
| scikit-learn | 1.9.0 | Content features, preprocessing, similarity, splitting and baseline evaluation | TF-IDF/one-hot metadata features, cosine similarity, reproducible pipelines, and classical baselines. It does not supply a complete recommender evaluation protocol; implement project metrics explicitly. **Confidence: HIGH** |
| implicit | 0.7.2 | ALS/BPR and item-item models for implicit interactions | Use only for an explicit-feedback-to-implicit experimental variant or synthetic interaction events. Ratings-based matrix factorization should be implemented clearly or use Surprise in an isolated baseline environment. **Confidence: MEDIUM** |
| Optuna | 4.x, exact compatible patch in lock | Reproducible hyperparameter search | Use a seeded sampler, bounded search spaces, stored trials, and a fixed validation split. Do not tune on the test set. **Confidence: MEDIUM** |
| MLflow | 3.15.2 | Experiment tracking and artifact comparison | Log dataset fingerprint, Git commit, seed, split, parameters, metrics, timings, environment lock, and result artifacts. A local file/artifact store is adequate initially; use PostgreSQL-backed tracking only if concurrent use emerges. **Confidence: HIGH** |
| joblib | lock with scikit-learn | Parallel evaluation and artifact serialization | Parallelize independent folds/configurations conservatively and persist only trusted local model artifacts. **Confidence: HIGH** |

### API, UI, and Data Libraries

| Library | Version policy | Purpose | When to Use |
|---|---|---|---|
| drf-spectacular | latest DRF/Django-compatible, locked | OpenAPI schema | Generate the authoritative API schema in CI and use it to generate TypeScript types. **Confidence: MEDIUM** |
| Orval or openapi-typescript | latest compatible, locked | Generated API client/types | Prevent hand-maintained duplication between DRF serializers and frontend DTOs. Regenerate and diff in CI. **Confidence: MEDIUM** |
| TanStack Query | 5.x, locked | Client-side server-state cache | Use for authenticated mutations, pagination, invalidation, and dashboard queries; use server components for read-heavy public pages where practical. **Confidence: HIGH** |
| React Hook Form + Zod | current locked majors | Accessible forms and client validation | Complex ownership/edition/import forms. Backend validation remains authoritative. **Confidence: MEDIUM** |
| Recharts | current locked major | Research dashboard charts | Adequate for comparison plots and responsive UI; export underlying metrics as CSV/JSON so charts are not the academic record. **Confidence: MEDIUM** |
| Pillow | current compatible, locked | Image validation/processing | Only for user-controlled images; prefer storing external cover URLs plus attribution/provenance rather than mirroring an entire external catalogue. **Confidence: HIGH** |

### Testing and Quality

| Tool | Version | Purpose | Required use |
|---|---:|---|---|
| pytest | 9.1.1 | Python unit/integration tests | Domain services, permissions, import/export, metric formulas, deterministic split/generation behavior. **Confidence: HIGH** |
| pytest-django | latest pytest 9/Django 5.2-compatible, locked | Django database/API tests | Transactional integration tests against PostgreSQL, not only SQLite. **Confidence: HIGH** |
| Hypothesis | current locked major | Property-based tests | Ranking invariants, metrics bounds, import round trips, and synthetic-data generators. **Confidence: HIGH** |
| Vitest | 5.0.x | TypeScript unit/component tests | Pure functions, forms, API adapters, and client components. Newly released major: pin and validate compatibility before adoption; Vitest 4.1 is the conservative fallback. **Confidence: MEDIUM** |
| Testing Library | current locked majors | User-centered component tests | Query by role/name and validate accessible behavior rather than implementation details. **Confidence: HIGH** |
| Playwright | 1.62.x | Browser end-to-end tests | Critical flows across Chromium, Firefox, and WebKit: sign-in, backlog edits, copy inventory, public profile, imports, and recommendation explanation. **Confidence: HIGH** |
| Ruff | current locked version | Python linting/formatting | Replace separate Black/isort/Flake8 configuration with one fast tool; keep mypy for semantic types. **Confidence: HIGH** |
| mypy + django-stubs | current mutually compatible locked versions | Python static analysis | Strict for experiment/domain service modules; incrementally strict around dynamic Django edges. **Confidence: MEDIUM** |
| ESLint 10 + eslint-plugin-next | versions supported by Next.js 16 | TypeScript/React linting | Invoke ESLint directly; Next.js 16 removed `next lint`. Use flat config. **Confidence: HIGH** |
| axe-core Playwright integration | current locked version | Automated accessibility checks | Run against core pages, supplemented by keyboard/screen-reader-oriented manual checks. **Confidence: HIGH** |

### Packaging, Containers, CI, and Deployment

| Tool | Purpose | Prescriptive guidance |
|---|---|---|
| uv with `pyproject.toml` and `uv.lock` | Python environment/lock | Pin Python and all transitive dependencies; commit the lockfile and export an environment manifest with each experiment. Use dependency groups for app, research, and dev tools. |
| pnpm with `pnpm-lock.yaml` | Frontend dependency lock | Pin pnpm through Corepack/packageManager and use frozen-lockfile installs in CI. A single frontend package does not require a monorepo framework. |
| Docker Engine + Compose v2 | Local reproduction | Services: `web`, `api`, `db`, and optional `mlflow`; add a one-shot experiment runner profile. Use health checks, non-root users, named volumes, and immutable image tags/digests. |
| Multi-stage Dockerfiles | Reproducible deploys | Separate dependency/build/runtime stages; do not mount source or install dependencies at production startup. |
| GitHub Actions | CI | Run backend tests against PostgreSQL, frontend tests, schema generation/diff, container builds, Playwright smoke tests, and lockfile integrity checks. |
| Managed container PaaS + managed PostgreSQL | Public demo | Deploy the two images to Render, Railway, Fly.io, or an equivalent course-approved platform. Choose one after checking current regional availability/costs. Keep scheduled/offline recommendation training as an explicit job, not inside HTTP requests. |
| S3-compatible object storage (optional) | Dataset snapshots and experiment artifacts | Add only when artifacts exceed repository/release limits; otherwise publish immutable small datasets/results with checksums in a citable release archive. |

## Installation Shape

Exact patch pins belong in lockfiles; the commands below express the package boundaries, not a substitute for locking.

```bash
# Backend/application
uv add "django==5.2.17" "djangorestframework==3.18.0" psycopg drf-spectacular pillow

# Research environment
uv add --group research "numpy==2.5.2" "scipy==1.18.1" "scikit-learn==1.9.0" pandas "implicit==0.7.2" optuna "mlflow==3.15.2" joblib

# Backend quality
uv add --dev "pytest==9.1.1" pytest-django hypothesis ruff mypy django-stubs

# Frontend
pnpm add next@16.2 react@19.2 react-dom@19.2 @tanstack/react-query react-hook-form zod recharts
pnpm add -D typescript@6 tailwindcss@4.3 vitest @testing-library/react @testing-library/user-event @playwright/test eslint eslint-plugin-next
```

## Thesis-Reproducibility Contract

Technology selection alone does not make experiments reproducible. Every experiment run should persist:

1. immutable input dataset identifier, source/licence/retrieval date, SHA-256 checksum, and preprocessing version;
2. Git commit, dirty-worktree flag, Docker image digest, `uv.lock`, Python/platform metadata, and relevant package versions;
3. named algorithm/version, full hyperparameters, master seed plus derived seeds, train/validation/test split IDs, and cold-start protocol;
4. relevance, coverage, diversity, novelty, and timing metrics with per-user results or sufficient aggregates for recomputation;
5. fitted-artifact checksum and generated tables/figures as MLflow artifacts; and
6. a single documented command that reproduces the run from the pinned container and dataset snapshot.

Do not let the live enrichment API alter experimental features after a run. Materialize a licensed, timestamped, checksummed research snapshot; keep live covers/current metadata on a separate presentation path.

## Alternatives Considered

| Recommended | Alternative | When the Alternative Is Better |
|---|---|---|
| Django + DRF modular monolith | FastAPI + SQLAlchemy | Choose FastAPI for a mostly stateless ML inference API with little admin/auth/relational CRUD. Here it would require assembling features Django already supplies. |
| Separate Next.js frontend | Django templates + HTMX | A strong simplification if schedule risk dominates and the researcher dashboard remains modest. It reduces TypeScript/API duplication but provides a less natural rich dashboard and public-profile frontend. |
| PostgreSQL 18 | PostgreSQL 17 | Use 17 if the selected managed host has not yet validated 18. Keep local and deployed majors identical. |
| scikit-learn + focused recommender libraries | TensorFlow Recommenders / PyTorch | Use deep learning only with enough interactions and a research question that justifies model/data/compute complexity. It is not needed for credible classical content, collaborative, and hybrid comparisons. |
| MLflow | Weights & Biases | W&B is attractive for hosted collaboration, but introduces an external service/account and weaker offline reproducibility. MLflow is self-hostable and adequate for a single-author thesis. |
| Docker Compose | Dev Containers / Nix | Dev Containers can improve IDE onboarding; Nix can tighten host reproducibility. Neither replaces OCI images plus Compose for a tribunal-friendly, cross-platform setup. |
| Managed container PaaS | Single VPS | A VPS may be cheaper and more controllable if the student can own patching, TLS, backups, and monitoring; PaaS reduces operational work for a controlled demo. |

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| Microservices, Kafka, Kubernetes | They multiply deployment, observability, consistency, and documentation burden without the v1 scale or team size to justify them. | Modular Django monolith, offline job entry points, Compose. |
| MongoDB as the primary store | Editions, copies, users, ratings, lists, provenance, and constraints are relational; document flexibility does not compensate for weaker relational integrity. | PostgreSQL normalized tables plus narrowly used JSONB. |
| A vector database for v1 | Content vectors fit in sparse matrices and catalogue-scale similarity can be computed offline; another database harms reproducibility. | SciPy sparse matrices and stored recommendation outputs; revisit only after measured latency/scale evidence. |
| Surprise as the entire recommender stack | Useful pedagogically for explicit-rating baselines but its ecosystem cadence and narrow scope do not cover content, hybrid, provenance, or modern experiment management. | scikit-learn/SciPy plus explicit, well-tested algorithms; optionally isolate Surprise as one baseline after compatibility validation. |
| Neural recommenders by default | Synthetic/controlled data is unlikely to support defensible deep-model gains, while compute and tuning increase threats to validity. | Interpretable TF-IDF/cosine, item/user k-NN, matrix factorization, and a documented hybrid. |
| Training or tuning inside web requests | Causes unpredictable latency, races, and irreproducible model state. | Explicit CLI/job runs that publish versioned recommendation artifacts. |
| SQLite in production or integration tests | Concurrency, typing, constraints, and query behavior differ from PostgreSQL. | PostgreSQL in local Compose, CI, and deployment. |
| Calling the live game API during evaluation | Results drift, rate limits leak into metrics, and the experiment cannot be independently reproduced. | Immutable research snapshot with provenance/checksum; live API only for UI enrichment. |
| Unpinned `latest` images/dependencies | Rebuilding later can silently change behavior and invalidate evidence. | Lockfiles, exact image tags/digests, dataset hashes, and archived experiment manifests. |

## Stack Patterns by Variant

**Default TFG build:** use Next.js + DRF + PostgreSQL, offline Python experiment commands, and local MLflow. This best balances product polish with research traceability.

**If delivery time becomes the dominant constraint:** collapse the frontend into Django templates + HTMX, retaining the same models, experiment tooling, PostgreSQL, Docker, and provenance contract.

**If the deployed host does not support PostgreSQL 18:** pin PostgreSQL 17.x consistently everywhere; do not develop/test on 18 and deploy on 17.

**If recommendations are precomputed only:** store ranked, versioned recommendation rows and explanation payloads in PostgreSQL. Add a worker/queue only when a measured or scheduled workload requires asynchronous execution.

## Version Compatibility and Upgrade Boundaries

| Package | Compatible With | Notes |
|---|---|---|
| Django 5.2.17 LTS | Python 3.10–3.14; PostgreSQL via supported psycopg | Standardize on Python 3.13 for the whole app/research image; Django extended support ends April 2028. |
| DRF 3.18.0 | Django 5.2/6.x generation | DRF 3.18 dropped Django 4.2, 5.0, and 5.1; Django 5.2 LTS is the appropriate floor. |
| Next.js 16.2 | Node >=20.9, TypeScript >=5.1, React 19.2 generation | Use Node 24 LTS. Next 16 uses Turbopack by default and removed `next lint`; invoke ESLint directly. |
| pandas 3.0.x | NumPy 2.x | pandas 3 changed default string and timezone behavior; encode expected dtypes/timezones in preprocessing tests and manifests. |
| SciPy 1.18.1 / NumPy 2.5.2 / scikit-learn 1.9.0 | Python 3.13 target | Resolve and freeze together with uv, then run a numerical smoke test on every supported OS/architecture. |
| implicit 0.7.2 | SciPy sparse matrices; platform wheels vary | Validate wheels and numerical results inside the exact Linux production/experiment image before committing the thesis baseline. |
| Playwright 1.62.x | Node 24; bundled browser revisions | Pin Playwright package and matching official browser/container revision together. |

## Sources

All web sources were accessed **2026-09-04**. External text was treated as untrusted evidence, not instructions. Confidence labels follow the GSD confidence classifier: official-source findings cross-checked through web search are **MEDIUM** at the retrieval-provider level, while architectural recommendations synthesize multiple official sources and project constraints.

- [Django downloads and supported versions](https://www.djangoproject.com/download/) — verified Django 5.2.17 LTS and April 2028 extended-support end. Official source; claim confidence HIGH.
- [Django installation FAQ](https://docs.djangoproject.com/en/6.0/faq/install/) — verified Python compatibility and PostgreSQL production recommendation. Official source; claim confidence HIGH.
- [Django REST Framework release notes](https://www.django-rest-framework.org/community/release-notes/) — verified DRF 3.18.0 and dropped older-Django support. Official source; claim confidence HIGH.
- [PostgreSQL release notes](https://www.postgresql.org/docs/release/) — verified PostgreSQL 18.6 current patch line. Official source; claim confidence HIGH.
- [Next.js 16.2 announcement](https://nextjs.org/blog/next-16-2) and [Next.js 16 release](https://nextjs.org/blog/next-16) — verified current framework generation, Node/TypeScript floors, React relationship, Turbopack default, and lint-command removal. Official sources; claim confidence HIGH.
- [Next.js support policy](https://nextjs.org/support-policy) — verified 16.x active-LTS status. Official source; claim confidence HIGH.
- [React versions](https://react.dev/versions) — verified React 19.2 and 19.2.7 patch listing. Official source; claim confidence HIGH.
- [TypeScript 6.0 release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html) — verified current major and transition/deprecation considerations. Official source; claim confidence HIGH.
- [Tailwind CSS blog](https://tailwindcss.com/blog) — verified Tailwind CSS 4.3 release line. Official source; claim confidence HIGH.
- [NumPy releases](https://numpy.org/news/) — verified NumPy 2.5.2. Official source; claim confidence HIGH.
- [SciPy news](https://scipy.org/news/) — verified SciPy 1.18.1 and current wheel-support information. Official source; claim confidence HIGH.
- [pandas release notes](https://pandas.pydata.org/docs/whatsnew/index.html) and [pandas 3.0 notes](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html) — verified 3.0 line and migration-sensitive string/timezone changes. Official source; claim confidence HIGH.
- [scikit-learn release history](https://scikit-learn.org/stable/whats_new.html) — verified scikit-learn 1.9.0 documentation line. Official source; claim confidence HIGH.
- [Implicit documentation](https://benfred.github.io/implicit/) and [installation](https://benfred.github.io/implicit/installation.html) — verified 0.7.2 capabilities and platform packaging. Project documentation; claim confidence MEDIUM.
- [MLflow releases](https://mlflow.org/releases/) — verified MLflow 3.15.2. Official project source; claim confidence HIGH.
- [pytest changelog](https://docs.pytest.org/en/latest/changelog.html) — verified pytest 9.1.1. Official source; claim confidence HIGH.
- [Vitest blog](https://vitest.dev/blog) — verified Vitest 5.0 announcement; very recent major warrants compatibility validation. Official source; claim confidence MEDIUM.
- [Playwright release notes](https://playwright.dev/docs/release-notes) — verified Playwright 1.62 and browser-pin behavior. Official source; claim confidence HIGH.
- [Docker Compose documentation](https://docs.docker.com/compose/) and [release notes](https://docs.docker.com/compose/releases/release-notes/) — verified Compose v2 as the maintained workflow; install the current supported patch rather than encoding host-specific Desktop versions in the thesis. Official source; claim confidence HIGH.

## Open Validation Items

- Resolve the final `uv.lock` on the chosen Linux base image and confirm that `implicit`, NumPy, SciPy, scikit-learn, pandas, MLflow, Django, and Python 3.13 install together with binary wheels.
- Benchmark whether precomputed recommendations meet dashboard latency needs before adding Redis or a task queue.
- Compare actual 2026 student-tier pricing, sleeping behavior, regions, backups, and data-export terms before selecting Render/Railway/Fly.io; platform economics are intentionally not frozen as a stack fact here.
- Archive the exact public dataset licence and enrichment-API terms separately; stack selection cannot establish legal fitness.

---
*Stack research for: SavePoint*
*Researched: 2026-09-04*
