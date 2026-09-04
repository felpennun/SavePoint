# Testing Patterns

**Analysis Date:** 2026-09-04

## Test Framework

**Runners:**
- **Backend (Python):** `pytest==9.1.1` with `pytest-django==4.14.0`
  - Config: `apps/api/pytest.ini` and `pyproject.toml:tool.pytest.ini_options`
- **Frontend (TypeScript):** `vitest==5.0.0`
  - Config: `apps/web/vitest.config.ts`
- **End-to-End / Browser:** `@playwright/test==1.62.1` with `axe-core==4.13.0`
  - Config: `playwright.config.ts`
- **Supply Chain / Allowlist:** PowerShell test script
  - Script: `scripts/check-dependencies.ps1`

**Assertion Libraries:**
- Python: native `assert` in pytest
- Vitest: Vitest `expect`
- Playwright: Playwright `expect`

**Run Commands:**
```bash
# Run backend tests inside PostgreSQL-connected container
docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests -q

# Run frontend Vitest tests (from apps/web directory)
corepack pnpm --dir apps/web test --run

# Run Playwright E2E tests (from root)
npx playwright test

# Verify dependency allowlist, lockfiles, and negative controls
powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1
```

## Test File Organization

**Location:**
- Backend tests: `apps/api/tests/`
- Frontend tests: `apps/web/tests/`
- E2E browser tests: `e2e/`
- Synthetic security fixtures: `e2e/fixtures/`

**Naming:**
- Backend: `test_<feature>.py` (e.g., `test_postgres_sentinel.py`)
- Frontend: `<feature>.test.ts` (e.g., `sentinel.test.ts`)
- E2E: `<feature>.spec.ts` (e.g., `sentinel.spec.ts`)

**Structure:**
```text
apps/
├── api/
│   ├── conftest.py
│   └── tests/
│       └── test_postgres_sentinel.py
└── web/
    └── tests/
        └── sentinel.test.ts
e2e/
├── fixtures/
│   └── hostile.json
└── sentinel.spec.ts
```

## Test Structure

**Suite Organization (Frontend - Vitest):**
```typescript
// apps/web/tests/sentinel.test.ts
import { describe, expect, it } from "vitest";

describe("SavePoint frontend test runner", () => {
  it("executes a real assertion before the application scaffold exists", () => {
    const supportedLocales = ["es", "en"] as const;
    const halfStarValues = Array.from({ length: 10 }, (_, index) => (index + 1) / 2);

    expect(supportedLocales).toEqual(["es", "en"]);
    expect(halfStarValues).toHaveLength(10);
    expect(halfStarValues.at(-1)).toBe(5);
  });
});
```

**Integration Test Pattern (Backend - Pytest):**
```python
# apps/api/tests/test_postgres_sentinel.py
import psycopg

def test_integration_database_is_postgresql(
    postgres_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT version(), current_setting('server_version_num')")
        version, numeric_version = cursor.fetchone()

    assert version.startswith("PostgreSQL 18.6")
    assert int(numeric_version) >= 180000
```

## Mocking

**Framework:** None currently required.

**Guidelines:**
- **No SQLite Mocking:** The primary database is never mocked with SQLite or SQLite in-memory databases. All relational integration tests run against a real PostgreSQL 18.6 instance.
- **External Network Isolation:** Live external network calls to Wikidata or Wikimedia Commons are forbidden in application and integration tests; tests consume local static fixtures or pre-acquired canonical JSON snapshots.

## Fixtures and Factories

**Database Fixtures (`apps/api/conftest.py`):**
- `postgres_connection`: Yields an active `psycopg.Connection` configured via `POSTGRES_*` environment variables. Fails cleanly without printing connection DSNs on error.

**Security Fixtures (`e2e/fixtures/hostile.json`):**
- Synthetic users (`ownerA`, `visitorB` with fixed UUIDs).
- Untrusted script strings for XSS testing:
  ```json
  "<script>globalThis.__savepoint_xss = true</script>",
  "<img src=x onerror=alert('synthetic-xss')>"
  ```
- Malicious and unexpected URL schemes:
  ```json
  "javascript:alert('synthetic-url')",
  "file:///etc/passwd",
  "http://127.0.0.1:5432/"
  ```
- Tampered dataset hashes to test checksum verification logic.

## Coverage

**Requirements:**
- Wave 0 gate requires non-empty test execution across all runners (`passWithNoTests: false`).
- Zero unhandled exceptions or floating versions permitted.

## Test Types

**Unit Tests:**
- Validate discrete TypeScript logic, data structures, calculation utilities, and isolated React components (`apps/web/tests/`).

**Integration Tests:**
- Validate database queries, migrations, transactions, and ORM behaviors against live PostgreSQL 18.6 (`apps/api/tests/`).

**End-to-End Tests:**
- Full browser runs under Chromium (and multi-browser in CI) verifying user journeys, accessible navigation, and hostile payload sanitization (`e2e/`).

**Integrity / Compliance Checks:**
- Static and runtime validation of dependency allowlists, lockfile specs, and OCI image digests (`scripts/check-dependencies.ps1`).

## Common Patterns

**Fail-on-Empty Sentinel Enforcement:**
- `apps/web/vitest.config.ts` enforces `passWithNoTests: false` to ensure test suites cannot pass vacuously.

**Fail-First Negative Controls:**
- `scripts/check-dependencies.ps1` explicitly verifies that invalid floating versions (`latest`, `^`, `~`) fail validation before checking valid dependencies.

**Secret-Safe Error Reporting:**
- Test setup asserts presence of required configuration variables and raises `pytest.fail(..., pytrace=False)` to prevent connection strings with passwords from leaking into CI output.

---

*Testing analysis: 2026-09-04*
