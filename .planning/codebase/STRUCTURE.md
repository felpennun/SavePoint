# Codebase Structure

**Analysis Date:** 2026-09-04

## Directory Layout

```text
SavePoint/
├── .planning/                  # Project roadmap, state, research, and codebase maps
│   ├── codebase/               # Architectural and codebase reference documents
│   ├── phases/                 # Phase definitions, plans, and execution summaries
│   └── PROJECT.md              # Project goals, scope, and core value definition
├── apps/                       # Monorepo applications
│   ├── api/                    # Django 5.2 backend REST application
│   │   ├── catalogue/          # Canonical video game works and releases
│   │   │   ├── migrations/     # Database migration files
│   │   │   ├── apps.py         # Django app configuration
│   │   │   └── models.py       # GameWork and GameRelease models
│   │   ├── config/             # Root Django configuration
│   │   │   ├── asgi.py         # ASGI entry point
│   │   │   ├── settings.py     # Django settings with strict PostgreSQL parser
│   │   │   ├── urls.py         # Root URL router
│   │   │   └── wsgi.py         # WSGI entry point
│   │   ├── library/            # Personal backlog tracking and state transitions
│   │   │   ├── migrations/     # Database migration files
│   │   │   ├── apps.py         # Django app configuration
│   │   │   └── models.py       # LibraryEntry and StatusTransition models
│   │   ├── tests/              # Backend integration tests
│   │   │   └── test_postgres_sentinel.py  # Fail-fast PostgreSQL 18.6 verification
│   │   ├── conftest.py         # Shared pytest fixtures (psycopg connection)
│   │   ├── Dockerfile          # Non-root multi-stage Python 3.13 image
│   │   ├── manage.py           # Django administrative command CLI
│   │   └── pytest.ini          # Pytest configuration
│   └── web/                    # Next.js 16 frontend application
│       ├── tests/              # Frontend unit and component tests
│       │   └── sentinel.test.ts # Vitest verification sentinel
│       ├── Dockerfile          # Non-root multi-stage Node 24 image
│       ├── package.json        # Web package manifest (@savepoint/web)
│       └── vitest.config.ts    # Vitest runner configuration
├── data/                       # Acquired datasets and manifests (generated offline)
│   ├── manifests/              # Immutable provenance and asset manifests
│   └── raw/                    # Raw JSON data snapshots (e.g., wikidata-games.json)
├── docs/                       # Verification and academic audit documentation
│   └── verification/           # Legitimacy logs and manual testing protocols
│       ├── dependency-legitimacy.md  # Approved dependencies and OCI digests
│       └── phase-01-manual.md        # Manual accessibility and security protocols
├── e2e/                        # End-to-end browser tests
│   ├── fixtures/               # Synthetic security and hostile test inputs
│   │   └── hostile.json        # Untrusted strings, malicious URLs, tampered hashes
│   └── sentinel.spec.ts        # Playwright test discovering Chromium runner
├── infra/                      # Local and deployment infrastructure
│   └── compose.yaml            # Docker Compose definition for db, api, web
├── scripts/                    # Maintenance, acquisition, and validation scripts
│   ├── acquire_catalogue.py    # SPARQL & Commons offline candidate fetcher
│   └── check-dependencies.ps1  # Enforceable dependency allowlist gate
├── package.json                # Root package manifest with workspace dependencies
├── playwright.config.ts        # Root Playwright test configuration
├── pnpm-lock.yaml              # Frozen lockfile for npm packages
├── pnpm-workspace.yaml         # pnpm workspace configuration
├── pyproject.toml              # Python project dependencies and pytest configuration
├── README.md                   # Project overview
└── uv.lock                     # Frozen lockfile for Python packages
```

## Directory Purposes

**`apps/api/`:**
- Purpose: Backend REST services, domain models, database migrations, and administrative interfaces.
- Contains: Django apps (`catalogue`, `library`), configuration modules, tests, and Docker runtime files.
- Key files: `apps/api/config/settings.py`, `apps/api/catalogue/models.py`, `apps/api/library/models.py`.

**`apps/web/`:**
- Purpose: Frontend web client, server-rendered profile pages, and accessible interactive collection tools.
- Contains: Next.js pages/components, frontend tests, and package configurations.
- Key files: `apps/web/package.json`, `apps/web/vitest.config.ts`, `apps/web/tests/sentinel.test.ts`.

**`infra/`:**
- Purpose: Infrastructure orchestration for local reproduction and evaluation environments.
- Contains: Docker Compose services configuring PostgreSQL 18.6, API, and Web containers.
- Key files: `infra/compose.yaml`.

**`scripts/`:**
- Purpose: Developer tooling, data preparation pipelines, and integrity checkers.
- Contains: Standalone Python and PowerShell scripts.
- Key files: `scripts/acquire_catalogue.py`, `scripts/check-dependencies.ps1`.

**`docs/`:**
- Purpose: Academic evidence, manual testing protocols, and dependency justification records.
- Contains: Markdown protocols and verifiable audit logs.
- Key files: `docs/verification/dependency-legitimacy.md`, `docs/verification/phase-01-manual.md`.

**`e2e/`:**
- Purpose: Full end-to-end browser integration tests across Chromium, Firefox, and WebKit.
- Contains: Test specs and hostile input fixtures.
- Key files: `e2e/sentinel.spec.ts`, `e2e/fixtures/hostile.json`.

## Key File Locations

**Entry Points:**
- `apps/api/manage.py`: Backend management CLI entry point.
- `apps/api/config/wsgi.py`: WSGI entry point for production application servers.
- `apps/api/config/asgi.py`: ASGI entry point for asynchronous interfaces.
- `apps/web/package.json`: Web application scripts (`dev`, `build`, `start`, `test`).
- `scripts/acquire_catalogue.py`: CLI entry point for candidate dataset acquisition.

**Configuration:**
- `apps/api/config/settings.py`: Authoritative Django backend configuration.
- `infra/compose.yaml`: Multi-container topology and local environment variables.
- `pyproject.toml`: Python dependencies and pytest configuration.
- `package.json`: Root Node dependencies, pnpm packageManager, and engine requirements.
- `playwright.config.ts`: End-to-end browser configuration.
- `apps/web/vitest.config.ts`: Frontend test runner configuration.

**Core Logic:**
- `apps/api/catalogue/models.py`: Definitions for `GameWork` and `GameRelease`.
- `apps/api/library/models.py`: Definitions for `LibraryEntry`, `BacklogStatus`, and `StatusTransition`.

**Testing:**
- `apps/api/tests/test_postgres_sentinel.py`: Fail-fast PostgreSQL integration test.
- `apps/web/tests/sentinel.test.ts`: Frontend runner assertion.
- `e2e/sentinel.spec.ts`: Playwright Chromium test sentinel.
- `scripts/check-dependencies.ps1`: Negative control dependency validation.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `acquire_catalogue.py`, `test_postgres_sentinel.py`).
- TypeScript test files: `kebab-case.test.ts` or `kebab-case.spec.ts` (e.g., `sentinel.test.ts`, `sentinel.spec.ts`).
- Documentation: `kebab-case.md` (e.g., `dependency-legitimacy.md`, `phase-01-manual.md`) or `UPPERCASE.md` for planning artifacts (`PROJECT.md`, `STACK.md`).
- Configuration files: standard tooling filenames (`package.json`, `pyproject.toml`, `compose.yaml`).

**Directories:**
- Application directories: lowercase alphanumeric (`apps/api`, `apps/web`, `e2e`, `infra`, `scripts`).
- Django app directories: lowercase singular noun (`catalogue`, `library`).

## Where to Add New Code

**New Feature (Backend):**
- Domain models: `apps/api/<app_name>/models.py`
- Serializers & views: `apps/api/<app_name>/serializers.py`, `apps/api/<app_name>/views.py`
- URLs: `apps/api/<app_name>/urls.py`, registered in `apps/api/config/urls.py`
- Tests: `apps/api/tests/test_<feature>.py` or `apps/api/<app_name>/tests/test_<feature>.py`

**New Feature (Frontend):**
- App Router pages: `apps/web/app/<route>/page.tsx`
- Reusable UI components: `apps/web/components/<component>.tsx`
- Client state/hooks: `apps/web/hooks/use-<hook>.ts`
- Tests: `apps/web/tests/<feature>.test.ts`

**Utilities & Data Scripts:**
- Standalone CLI utilities: `scripts/<tool_name>.py`
- Integration checks: `scripts/<check_name>.ps1`

## Special Directories

**`.planning/`:**
- Purpose: Project planning state, roadmaps, requirement logs, phase plans, and codebase maps.
- Generated: Managed by GSD tooling.
- Committed: Yes.

**`data/`:**
- Purpose: Storage for raw acquired JSON dumps and cryptographic manifests.
- Generated: Yes (via `scripts/acquire_catalogue.py`).
- Committed: Manifests and canonical snapshots are committed; temporary scratch files are ignored.

**`infra/`:**
- Purpose: Local container orchestration and reproducible deployment configuration.
- Generated: No.
- Committed: Yes.

---

*Structure analysis: 2026-09-04*
