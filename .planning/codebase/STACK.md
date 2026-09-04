# Technology Stack

**Analysis Date:** 2026-09-04

## Languages

**Primary:**
- **Python 3.13.x** - Backend services, Django models, data acquisition scripts (`pyproject.toml`, `apps/api/`, `scripts/acquire_catalogue.py`). Pin policy strictly restricts runtime to `==3.13.*`.
- **TypeScript 6.0.3** - Web application and tests (`apps/web/`, `playwright.config.ts`, `e2e/`). Strict mode contract across frontend and test suites.

**Secondary:**
- **PowerShell 7+ / 5.1** - Dependency integrity and validation scripting (`scripts/check-dependencies.ps1`).
- **SQL (PostgreSQL 18 dialect)** - Database migrations, schema integrity, and query execution in PostgreSQL 18.6.

## Runtime

**Environment:**
- **Node.js 24.13.0** (`package.json:engines.node`, Docker image `node:24.13.0-slim@sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f`)
- **Python 3.13.7** (Docker image `python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689`)

**Package Manager:**
- **pnpm 11.25.0** (Node package manager managed via Corepack, declared in `package.json:packageManager`)
  - Lockfile: `pnpm-lock.yaml` (present, strictly pinned, frozen in CI/Docker)
- **uv 0.12.9** (Python package installer and virtual environment resolver, declared in `pyproject.toml:tool.uv.required-version`)
  - Lockfile: `uv.lock` (present, strictly pinned, frozen in CI/Docker)

## Frameworks

**Core:**
- **Next.js 16.3.4** - Server-side rendering, routing, and metadata for public profiles and collection interfaces (`package.json`, `apps/web/package.json`).
- **React / React DOM 19.2.7** - Accessible declarative component model for Next.js App Router (`package.json`).
- **Django 5.2.17 LTS** - Core domain logic, authentication, ORM, sessions, CSRF, and administration (`pyproject.toml`, `apps/api/config/settings.py`).
- **Django REST Framework 3.18.0** - RESTful API serialization, endpoints, and permissions (`pyproject.toml`, `apps/api/config/settings.py`).

**Testing:**
- **pytest 9.1.1** - Python test runner for backend logic and integration (`pyproject.toml`, `apps/api/pytest.ini`).
- **pytest-django 4.14.0** - Pytest integration for Django database transactions and settings (`pyproject.toml`).
- **Vitest 5.0.0** - Unit and component test runner for web frontend (`package.json`, `apps/web/vitest.config.ts`).
- **@testing-library/react 16.3.3** - Accessible user-centric component testing (`package.json`).
- **Playwright 1.62.1** (`@playwright/test`) - End-to-end browser automation for Chromium, Firefox, WebKit (`package.json`, `playwright.config.ts`).
- **axe-core 4.13.0** - Automated accessibility engine for WCAG audits (`package.json`).

**Build/Dev:**
- **Tailwind CSS 4.3.3** with `@tailwindcss/postcss 4.3.3` - CSS tokens and responsive layout styling (`package.json`).
- **Docker Compose v2** (tested v5.0.2) - Multi-container service orchestration (`infra/compose.yaml`).

## Key Dependencies

**Critical:**
- `psycopg[binary]==3.3.5` - PostgreSQL 3.x driver connecting Django ORM to PostgreSQL 18.6 (`pyproject.toml`, `apps/api/conftest.py`).
- `next==16.3.4` - Web application server and UI runtime (`package.json`).
- `django==5.2.17` - Enterprise relational framework providing auth, ORM, security middleware (`pyproject.toml`).

**Infrastructure:**
- `postgres:18.6@sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280` - Primary relational store (`infra/compose.yaml`).
- `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e` - Official container image for browser testing (`docs/verification/dependency-legitimacy.md`).

## Configuration

**Environment:**
- Environment variables are consumed by Django in `apps/api/config/settings.py`:
  - `DJANGO_SECRET_KEY`: Mandatory secret key for cryptographic signing.
  - `DJANGO_DEBUG`: Boolean debug flag (defaults to `False`).
  - `DJANGO_ALLOWED_HOSTS`: Comma-separated allowed host headers (defaults to `localhost,127.0.0.1,testserver`).
  - `DATABASE_URL`: PostgreSQL connection string (`postgresql://user:pass@host:port/dbname`).
  - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`: Discrete connection variables parsed by `_postgres_database()` if `DATABASE_URL` is unset.
  - `DJANGO_SECURE_COOKIES`: Boolean enforcing Secure cookie flags.
  - `DJANGO_CSRF_TRUSTED_ORIGINS`: Comma-separated trusted origins for CSRF protection.
- Frontend environment variables:
  - `PLAYWRIGHT_BASE_URL`: Base URL for E2E tests in `playwright.config.ts` (defaults to `http://127.0.0.1:3000`).

**Build:**
- `pnpm-workspace.yaml`: Configures `apps/*` monorepo packages with `strict` catalog mode and shared lockfile.
- `apps/web/vitest.config.ts`: Configures Vitest test inclusion (`tests/**/*.test.ts`).
- `apps/api/pytest.ini`: Configures pytest paths (`testpaths = tests`, `python_files = test_*.py`).
- `pyproject.toml`: Pytest options and tool configs.

## Platform Requirements

**Development:**
- Windows / Linux / macOS with Node.js 24 LTS and Corepack enabled.
- Python 3.13 (or Docker Desktop to run services inside official Linux containers).
- Docker Engine & Docker Compose v2.
- Local dependency check: `powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1`.

**Production:**
- Containerized Linux execution (multi-stage Docker builds: `apps/api/Dockerfile`, `apps/web/Dockerfile`).
- Managed PostgreSQL 18.6 instance.
- Non-root container runtime (`UID 10001` for API, `node` user `UID 1000` for Web).

---

*Stack analysis: 2026-09-04*
