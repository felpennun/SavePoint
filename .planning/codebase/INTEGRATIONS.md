# External Integrations

**Analysis Date:** 2026-09-04

## APIs & External Services

**Knowledge Graph & Catalogue Source:**
- **Wikidata Query Service (SPARQL):** Used for batch acquisition of video-game entities, release dates, sitelinks, platform data, and Wikimedia Commons image links.
  - Endpoint: `https://query.wikidata.org/sparql`
  - Integration Script: `scripts/acquire_catalogue.py`
  - Auth: None (public CC0 endpoint). Requires descriptive User-Agent (`SavePoint-TFG/0.1`).
  - Runtime boundary: Strictly offline. Never called during HTTP requests, live UI browsing, or recommender evaluation. Writes canonical versioned artifacts to `data/raw/wikidata-games.json` with SHA-256 hashes.

**Media & Licensing Metadata:**
- **Wikimedia Commons API:** Used for querying licensing terms, authorship, credit, and image URLs of candidate cover assets.
  - Endpoint: `https://commons.wikimedia.org/w/api.php`
  - Integration Script: `scripts/acquire_catalogue.py`
  - Auth: None (public Wikimedia API).
  - Runtime boundary: Strictly offline. Output is written to `data/manifests/assets.json` with all items flagged as `review_status: "pending-human-review"` and `display_allowed: false`. Unapproved assets fall back to first-party placeholders.

## Data Storage

**Databases:**
- **PostgreSQL 18.6:** Primary relational datastore for canonical game works, releases, user accounts, personal library entries, and backlog transitions.
  - Connection: `DATABASE_URL` (format: `postgresql://user:password@host:port/dbname`) or individual parameters `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.
  - Client / Driver: `psycopg[binary]==3.3.5` via Django ORM (`apps/api/config/settings.py:_postgres_database()`).
  - Enforcement: SQLite is strictly forbidden; connection parser raises `RuntimeError` if engine is not PostgreSQL or if required parameters are missing.

**File Storage:**
- **Local filesystem only:** Static files handled via Django `STATIC_URL` (`apps/api/config/settings.py:106`). Cover images are not mirrored locally; applications reference approved external URLs or render first-party vector placeholders.

**Caching:**
- **Database sessions / None:** Currently sessions are managed via `django.contrib.sessions` backed by PostgreSQL. No Redis or Memcached instances in current foundation.

## Authentication & Identity

**Auth Provider:**
- **Custom Django Authentication:**
  - Implementation: Built-in `django.contrib.auth` with session cookies (`SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`, configurable `SESSION_COOKIE_SECURE`).
  - Password Validators: Minimum length, numeric, common password, and user attribute similarity validators configured in `apps/api/config/settings.py`.
  - Permissions: DRF permission layers with Django authentication backend.

## Monitoring & Observability

**Error Tracking:**
- **None:** No external Sentry or Datadog agent integrated; error boundaries report fail-closed exceptions.

**Logs:**
- **Standard console logging:** Standard output streams in Docker containers (`PYTHONUNBUFFERED=1` in `apps/api/Dockerfile`). Pytest output strictly suppresses database credentials (`apps/api/conftest.py:22`).

## CI/CD & Deployment

**Hosting:**
- **Target Container PaaS (Render / Railway / Fly.io):** Target deployment hosts standard OCI images built from `apps/api/Dockerfile` and `apps/web/Dockerfile`.

**CI Pipeline:**
- **Local Docker Compose & Scripts:**
  - Orchestration: `infra/compose.yaml` coordinates `db`, `api`, and `web`.
  - Dependency Allowlist Verification: `powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1`.
  - Container healthchecks: `pg_isready -U savepoint_test -d savepoint_test` on `db` service.

## Environment Configuration

**Required env vars:**
- `DJANGO_SECRET_KEY`: Cryptographic signing secret (required in `apps/api/config/settings.py`).
- `DATABASE_URL` or (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`): PostgreSQL connection details.
- `DJANGO_DEBUG`: Set to `"true"` or `"false"` (default: `"false"`).
- `DJANGO_ALLOWED_HOSTS`: Host headers allowed by Django (default: `localhost,127.0.0.1,testserver`).
- `DJANGO_CSRF_TRUSTED_ORIGINS`: Origins allowed for CSRF-protected POST requests.
- `PLAYWRIGHT_BASE_URL`: Base target URL for Playwright tests (default: `http://127.0.0.1:3000`).

**Secrets location:**
- Local test values are isolated to `infra/compose.yaml` and ephemeral environment variables. `.env*` files are excluded by `.gitignore` and `.dockerignore`.
- Zero credentials or tokens in git repository or test fixtures (`e2e/fixtures/hostile.json`).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-09-04*
