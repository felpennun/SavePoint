# Coding Conventions

**Analysis Date:** 2026-09-04

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `apps/api/config/settings.py`, `scripts/acquire_catalogue.py`, `apps/api/tests/test_postgres_sentinel.py`).
- TypeScript test files: `kebab-case.test.ts` for unit/component tests (`apps/web/tests/sentinel.test.ts`) and `kebab-case.spec.ts` for Playwright E2E specs (`e2e/sentinel.spec.ts`).
- Documentation: `kebab-case.md` for records and guides (`docs/verification/dependency-legitimacy.md`), `UPPERCASE.md` for codebase map and root planning files (`STACK.md`, `ARCHITECTURE.md`, `PROJECT.md`).

**Functions:**
- Python: `snake_case` (e.g., `_postgres_database`, `_validate_url`, `test_integration_database_is_postgresql`).
- TypeScript: `camelCase` (e.g., `defineConfig`, test suite callbacks).

**Variables:**
- Local variables: `snake_case` in Python (`raw_url`, `game_uri`), `camelCase` in TypeScript (`supportedLocales`, `runnerContract`).
- Constants / Globals: `UPPER_SNAKE_CASE` in Python (`BASE_DIR`, `WIKIDATA_ENDPOINT`, `MAX_BYTES`).
- Private / Internal functions: Leading underscore in Python (`_binding_value`, `_qid`, `_sha256`).

**Types:**
- Classes and Type aliases: `PascalCase` in Python (`GameWork`, `GameRelease`, `LibraryEntry`, `BacklogStatus`) and TypeScript (`BacklogStatus`).
- Enums: `PascalCase` class name with `UPPER_SNAKE_CASE` members (`BacklogStatus.PENDING = "pending"`).

## Code Style

**Formatting:**
- Indentation: 4 spaces for Python (`apps/api/`, `scripts/`), 2 spaces for TypeScript, JSON, and YAML (`apps/web/`, `infra/compose.yaml`).
- Max line length: 120 characters for Python (observed in `settings.py` and `acquire_catalogue.py`).
- Quotes: Double quotes `""` for strings in both Python and TypeScript, unless escaping single quotes.

**Type Annotations:**
- Python: Mandatory type annotations on all function signatures (`-> None`, `-> dict[str, Any]`, `psycopg.Connection[tuple[object, ...]]`). Future annotations enabled via `from __future__ import annotations` in scripts.
- TypeScript: Strict typing enabled; literal types and constants enforced using `as const` assertions (e.g., `const supportedLocales = ["es", "en"] as const;` in `apps/web/tests/sentinel.test.ts`).

## Import Organization

**Order (Python):**
1. Future imports (`from __future__ import annotations`).
2. Standard library modules (`import os`, `import sys`, `from pathlib import Path`, `from urllib.parse import urlparse`).
3. Third-party dependencies (`import psycopg`, `import pytest`, `from django.db import models`).
4. Internal application / domain modules (`from catalogue.models import GameWork`).

**Order (TypeScript):**
1. External / framework imports (`import { expect, test } from "@playwright/test";`, `import { describe, it } from "vitest";`).
2. Internal application components and utilities.

**Path Aliases:**
- Backend: Relative application imports and Django root package imports (`catalogue.apps`, `config.settings`).
- Frontend: Direct module imports within `apps/web/` workspace.

## Error Handling

**Patterns:**
- **Fail Closed:** Incomplete configurations raise explicit exceptions immediately at startup rather than falling back to insecure defaults:
  ```python
  # apps/api/config/settings.py
  if missing:
      raise RuntimeError("Missing PostgreSQL configuration: " + ", ".join(missing))
  ```
- **Credential Protection:** Error messages and pytest traces must never format whole DSN strings containing passwords:
  ```python
  # apps/api/conftest.py
  pytest.fail("Missing PostgreSQL test configuration: " + ", ".join(missing), pytrace=False)
  ```
- **Safe Network Validation:** Network handlers check URLs against strict host allowlists before connection initiation:
  ```python
  # scripts/acquire_catalogue.py
  if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
      raise ValueError(f"Refusing non-allowlisted URL: {parsed.scheme}://{parsed.hostname}")
  ```

## Logging

**Framework:** Standard console logging and pytest test reporter.
**Patterns:**
- Clean stdout: Routine operations produce clean summary lines (`Candidate written: 150 games...`).
- Secret Redaction: Database passwords, session cookies, and private tokens must never be logged.

## Comments

**When to Comment:**
- File headers: Every Python module starts with a descriptive docstring defining its domain scope and operational boundary:
  ```python
  """Personal library state at canonical game-work level."""
  ```
- Non-obvious rationale: Inline comments explain why a particular constraint or negative control is enforced:
  ```powershell
  # Fail-first controls: values commonly used to bypass reproducible pins must
  # remain rejected even if a future manifest change accidentally introduces one.
  ```

## Function Design

**Size:**
- Single-purpose functions under 50 lines where practical.
- Complex multi-step pipelines broken down into distinct pure helper functions (`_aggregate`, `_enrich_bindings`, `_commons_metadata` in `scripts/acquire_catalogue.py`).

**Parameters:**
- Explicitly typed parameters with no generic catch-all `*args, **kwargs` unless required by framework hooks.

**Return Values:**
- Explicit return type hints on all public and helper functions.

## Module Design

**Exports:**
- Django apps declare public models in `models.py` and register configurations in `apps.py`.
- No wildcard imports (`from module import *` is strictly avoided).

**Barrel Files:**
- Avoid barrel files that re-export large dependency trees; import directly from the defining module.

---

*Convention analysis: 2026-09-04*
