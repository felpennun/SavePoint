<!-- refreshed: 2026-09-04 -->
# Architecture

**Analysis Date:** 2026-09-04

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      Presentation Layer (Next.js 16)                    │
│                      `apps/web/` (Node.js 24 LTS)                       │
├────────────────────────────────────┬────────────────────────────────────┤
│     Public Game Catalogue & UI     │     Personal Backlog & Library     │
│         (App Router & SSR)         │      (React 19.2 Components)       │
└──────────────────┬─────────────────┴──────────────────┬─────────────────┘
                   │                                    │
                   │ JSON / REST (Session Auth / CSRF)  │
                   ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Application & API Layer (Django 5.2 / DRF)              │
│                       `apps/api/` (Python 3.13)                         │
├────────────────────────────────────┬────────────────────────────────────┤
│         Catalogue Service          │          Library Service           │
│   `apps/api/catalogue/models.py`   │    `apps/api/library/models.py`    │
│    (GameWork, GameRelease)         │ (LibraryEntry, StatusTransition)   │
└──────────────────┬─────────────────┴──────────────────┬─────────────────┘
                   │                                    │
                   │ psycopg 3.3.5 / Django ORM         │
                   ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Persistence Layer (PostgreSQL 18.6)                     │
│                  `infra/compose.yaml` (Service `db`)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ Canonical JSON Batch Load (Offline)
┌──────────────────────────────────┴──────────────────────────────────────┐
│                    Offline Data Acquisition Pipeline                    │
│        `scripts/acquire_catalogue.py` -> `data/raw/wikidata-games.json` │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Core API Config** | Settings, fail-closed PostgreSQL connection resolution, security middleware, and URL routing | `apps/api/config/settings.py`, `apps/api/config/urls.py` |
| **Catalogue Domain** | Canonical video-game works and release variants | `apps/api/catalogue/models.py` |
| **Library Domain** | Personal backlog tracking, status states (`pending`, `playing`, `completed`, `abandoned`), and transition history | `apps/api/library/models.py` |
| **Web Client** | Accessible responsive user interface, SSR public profiles, client interaction | `apps/web/package.json`, `apps/web/vitest.config.ts` |
| **Offline Acquisition** | Deterministic SPARQL & Commons extraction, schema validation, and SHA-256 fingerprinting | `scripts/acquire_catalogue.py` |
| **Dependency Gate** | Verification of exact dependency pins and negative control enforcement | `scripts/check-dependencies.ps1` |
| **E2E & Security Fixtures** | Chromium test execution, accessibility checks, and hostile payload validation | `playwright.config.ts`, `e2e/sentinel.spec.ts`, `e2e/fixtures/hostile.json` |

## Pattern Overview

**Overall:** Modular Monolith Backend with Decoupled Next.js Frontend.

**Key Characteristics:**
- **Relational Domain Integrity:** Relational models strictly enforce uniqueness constraints (e.g., `UniqueConstraint(fields=("work", "release_name"))` and `UniqueConstraint(fields=("user", "work"))`).
- **Offline Acquisition Boundary:** External data sources (Wikidata/Wikimedia Commons) are fetched strictly offline via standalone batch scripts with content checksums; no external API calls occur within HTTP request lifecycles.
- **Fail-Closed Environmental Contract:** Configuration parsing throws immediate `RuntimeError` if PostgreSQL is not configured or if database scheme is invalid.
- **Fail-on-Empty Test Runners:** Test configurations forbid empty suites (`passWithNoTests: false`).

## Layers

**Presentation Layer:**
- Purpose: Delivers responsive, accessible HTML and interactive components.
- Location: `apps/web/`
- Contains: React components, Next.js routing, Vitest unit/component tests.
- Depends on: Django REST API via HTTP/JSON.
- Used by: End users, browsers, Playwright E2E suites.

**Domain & API Layer:**
- Purpose: Business logic, authentication, input validation, and REST API endpoints.
- Location: `apps/api/`
- Contains: Django apps (`catalogue`, `library`), configuration (`config/settings.py`), and test sentinels (`tests/test_postgres_sentinel.py`).
- Depends on: PostgreSQL database.
- Used by: Presentation layer and test runners.

**Persistence Layer:**
- Purpose: Authoritative relational storage for catalogue, accounts, library entries, and ratings.
- Location: `infra/compose.yaml` (`db` service)
- Contains: PostgreSQL 18.6 with persistent volume `postgres_data`.
- Depends on: None.
- Used by: Django ORM.

**Offline Ingestion Layer:**
- Purpose: Deterministic retrieval and verification of game metadata from Wikidata and Commons.
- Location: `scripts/acquire_catalogue.py`
- Contains: Bounded SPARQL fetcher, Wikimedia Commons license validator, and atomic manifest writers.
- Depends on: External HTTPS endpoints (`query.wikidata.org`, `commons.wikimedia.org`).
- Used by: Researchers/developers during dataset preparation.

## Data Flow

### Primary Request Path

1. **Browser Request**: User navigates to a catalogue or library view (`apps/web/`).
2. **API Endpoint**: Next.js sends authenticated JSON request to Django REST Framework (`apps/api/config/urls.py`).
3. **Domain Verification**: Django middleware evaluates session/CSRF (`apps/api/config/settings.py:29-37`).
4. **ORM Query**: Model query runs against PostgreSQL (`apps/api/catalogue/models.py`, `apps/api/library/models.py`).
5. **Database Response**: PostgreSQL executes SQL via `psycopg` connection pool.
6. **JSON Serialization**: DRF serializes model instances and returns structured JSON response.
7. **Render**: Web frontend updates UI state.

### Offline Ingestion Flow

1. **Acquisition Trigger**: Script `scripts/acquire_catalogue.py` executes query `QUERY` against Wikidata SPARQL.
2. **Batch Enrichment**: Bounded batch queries enrich sitelinks, genres, and platforms (`scripts/acquire_catalogue.py:57-69`).
3. **Media Verification**: Commons API checks license and attribution metadata (`scripts/acquire_catalogue.py:251-282`).
4. **Validation**: Candidate record count and era coverage validated (`scripts/acquire_catalogue.py:319-345`).
5. **Manifest Generation**: Atomic write outputs `data/raw/wikidata-games.json` and manifests with SHA-256 digests.

**State Management:**
- Server state in Next.js managed via HTTP requests/fetching.
- Session state in Django stored in PostgreSQL session tables via `django.contrib.sessions`.

## Key Abstractions

**GameWork (`apps/api/catalogue/models.py:8-19`):**
- Purpose: Canonical identity of a video-game title across all platforms and editions.
- Attributes: `id` (UUID), `canonical_slug` (unique), `original_title`, `is_dlc` (boolean).
- Pattern: Domain Entity.

**GameRelease (`apps/api/catalogue/models.py:21-40`):**
- Purpose: Specific release edition or platform distribution of a `GameWork`.
- Constraints: Unique constraint on `(work, release_name)`.
- Pattern: Child Entity.

**LibraryEntry (`apps/api/library/models.py:16-34`):**
- Purpose: Relationship representing a user's personal backlog state for a `GameWork`.
- Attributes: `user`, `work`, `current_status` (`BacklogStatus`), `updated_at`.
- Constraints: Unique constraint on `(user, work)`.
- Pattern: Association Entity with state machine.

**StatusTransition (`apps/api/library/models.py:36-49`):**
- Purpose: Immutable audit log tracking historical changes to a library entry status.
- Attributes: `entry`, `from_status`, `to_status`, `changed_at`.
- Pattern: Append-only Event Log.

## Entry Points

**Django WSGI/ASGI Server:**
- Location: `apps/api/config/wsgi.py`, `apps/api/config/asgi.py`
- Triggers: Web server (Gunicorn / Uvicorn) or Docker container startup.
- Responsibilities: Initializes Django application and handles HTTP/WebSocket requests.

**Django Management CLI:**
- Location: `apps/api/manage.py`
- Triggers: CLI invocations (`python manage.py <command>`).
- Responsibilities: Runs migrations, admin utilities, tests.

**Web Application Server:**
- Location: `apps/web/package.json`
- Triggers: `next dev` or `next start`.
- Responsibilities: Runs Next.js SSR server and static asset routing.

**Test Sentinels:**
- Backend: `apps/api/tests/test_postgres_sentinel.py` validates PostgreSQL 18.6 connectivity.
- Frontend: `apps/web/tests/sentinel.test.ts` validates Vitest test runner.
- E2E: `e2e/sentinel.spec.ts` validates Playwright Chromium runner discovery.

## Architectural Constraints

- **PostgreSQL Requirement:** SQLite is strictly rejected. `apps/api/config/settings.py:_postgres_database()` throws a `RuntimeError` if engine scheme is not PostgreSQL.
- **Fail-Closed Credentials:** Pytest fixtures connect using separated parameters rather than whole DSNs to prevent accidental credential leakage in test traces (`apps/api/conftest.py:20-23`).
- **Non-Privileged Containers:** Docker containers run as non-root users (`UID 10001` in `apps/api/Dockerfile`, `node` in `apps/web/Dockerfile`).
- **Deterministic Dependencies:** Direct dependencies in `package.json` and `pyproject.toml` must be pinned to exact versions with lockfiles frozen in builds.

## Anti-Patterns

### Using SQLite for Integration Tests or Local Development
**What happens:** Developers or CI switch to SQLite for quick in-memory testing.
**Why it's wrong:** SQLite has different column types, concurrency constraints, and lacks PostgreSQL 18 JSONB/trigram capabilities.
**Do this instead:** Use PostgreSQL 18.6 via Docker Compose (`infra/compose.yaml`) and verify using `apps/api/tests/test_postgres_sentinel.py`.

### Running Vitest across Root without Scoping
**What happens:** Running `vitest run` from the workspace root attempts to execute `e2e/sentinel.spec.ts`.
**Why it's wrong:** Playwright tests import `@playwright/test`, which throws `Error: Playwright Test did not expect test() to be called here` under Vitest.
**Do this instead:** Execute Vitest scoped to the web package (`apps/web/vitest.config.ts`) via `corepack pnpm --dir apps/web test --run`.

### Live Third-Party API Calls in Web Requests
**What happens:** Querying Wikidata or external cover art APIs during user page load.
**Why it's wrong:** Causes unbounded latency, rate-limiting failures, and undermines academic reproducibility.
**Do this instead:** Pre-acquire dataset snapshots offline using `scripts/acquire_catalogue.py` with versioned manifests.

## Error Handling

**Strategy:** Fail closed, validate strictly, sanitize untrusted inputs.

**Patterns:**
- `_postgres_database()` in `apps/api/config/settings.py`: Throws `RuntimeError` with a clear explanation if environment variables are missing.
- `_validate_url()` and `SafeRedirectHandler` in `scripts/acquire_catalogue.py`: Rejects URLs outside `query.wikidata.org` and `commons.wikimedia.org` and aborts on redirect counts > 2.
- Hostile fixture assertions: Verify untrusted strings render inert without script execution (`e2e/fixtures/hostile.json`).

## Cross-Cutting Concerns

**Logging:** Standard Python logging; sensitive variables (DB passwords, secret keys) are redacted and never printed in connection traces.
**Validation:** Strict typing with TypeScript 6.0 in frontend; Django model validation and unique constraints in backend.
**Authentication:** Cookie-based session authentication with `HttpOnly`, `SameSite=Lax`, and configurable `Secure` flags.
**Accessibility:** Built-in 44x44px touch targets, reflow at 320px, 400% zoom without horizontal scrolling, and screen-reader support verified via `docs/verification/phase-01-manual.md`.

---

*Architecture analysis: 2026-09-04*
