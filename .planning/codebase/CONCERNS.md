# Codebase Concerns

**Analysis Date:** 2026-09-04

## Tech Debt

**Root Test Script Collision:**
- Issue: In `package.json:10`, the root test script `"test": "vitest run"` runs Vitest from the workspace root without excluding `e2e/`. Because Vitest discovers `e2e/sentinel.spec.ts` (which imports `@playwright/test`), executing `vitest run` from the root fails with `Playwright Test did not expect test() to be called here`.
- Files: `package.json`, `apps/web/vitest.config.ts`, `e2e/sentinel.spec.ts`
- Impact: Developers running `pnpm test` at the root receive an unexpected failure.
- Fix approach: Either configure a root `vitest.config.ts` that ignores `e2e/**`, update root script to `vitest run --project apps/web`, or update script to `pnpm --dir apps/web test --run`.

**Uncommitted Initial Database Migrations:**
- Issue: Django models `GameWork`, `GameRelease` (`apps/api/catalogue/models.py`) and `LibraryEntry`, `StatusTransition` (`apps/api/library/models.py`) are defined, but no initial migration files have been generated (`catalogue/migrations/` and `library/migrations/` only contain `__init__.py`).
- Files: `apps/api/catalogue/migrations/`, `apps/api/library/migrations/`
- Impact: Running `migrate` against PostgreSQL will not create tables for the domain models until migrations are created.
- Fix approach: Run `python manage.py makemigrations catalogue library` inside the containerized Python 3.13 runtime.

## Known Bugs

**Host Python Version Incompatibility:**
- Symptoms: Local environment commands that rely on Python directly on the host fail or risk compatibility issues if run with the host's Python 3.14 (`Python 3.14.2`), whereas `pyproject.toml` strictly requires `==3.13.*`.
- Files: `pyproject.toml`, `apps/api/Dockerfile`
- Trigger: Running `python` or `pytest` directly in the host shell without the container or a Python 3.13 virtual environment.
- Workaround: Execute backend tasks and tests through Docker Compose (`docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests -q`).

## Security Considerations

**Fail-Closed Environment Credentials:**
- Risk: Missing `DJANGO_SECRET_KEY` or PostgreSQL variables causes runtime crashes.
- Files: `apps/api/config/settings.py:10`
- Current mitigation: Compose provides isolated local dummy credentials (`local-development-only-not-a-secret`, `local_test_only`); `_postgres_database()` verifies presence and valid PostgreSQL schemes.
- Recommendations: Production deployment configuration must ensure high-entropy secret injection and fail closed on defaults.

**Hostile Fixture Injection Defense:**
- Risk: Cross-site scripting (XSS), open redirect via untrusted URLs, or IDOR between users (ownerA vs visitorB).
- Files: `e2e/fixtures/hostile.json`, `docs/verification/phase-01-manual.md`
- Current mitigation: Fixture defines synthetic attack vectors (`<script>`, `javascript:alert()`, private UUIDs) ready for validation; manual testing protocol mandates that `untrustedText` renders as inert text and `untrustedUrls` are rejected.
- Recommendations: Implement strict input sanitization and automated Playwright assertions asserting inert rendering when UI components are built.

## Performance Bottlenecks

**Wikidata SPARQL Batch Retrieval:**
- Problem: `scripts/acquire_catalogue.py` relies on `https://query.wikidata.org/sparql` and `https://commons.wikimedia.org/w/api.php`. SPARQL queries with aggregations and sitelinks can encounter public gateway timeouts (HTTP 429/504) if limits or filters are expanded.
- Files: `scripts/acquire_catalogue.py:43-69`
- Cause: Public shared SPARQL endpoint constraints.
- Improvement path: Acquisition is strictly offline and writes immutable versioned files to `data/raw/` with SHA-256 checks; application runtime is insulated and does not query external APIs.

## Fragile Areas

**Strict Dependency Allowlist:**
- Files: `scripts/check-dependencies.ps1`, `package.json`, `pyproject.toml`, `docs/verification/dependency-legitimacy.md`
- Why fragile: Adding or updating any package (or changing patch versions) immediately fails the verification script unless updated across package manifests, lockfiles, the script allowlist, and the academic justification document.
- Safe modification: Follow the human-authorized dependency workflow: verify official registry integrity, update allowlist, update lockfile, and document justification.
- Test coverage: Validated by `scripts/check-dependencies.ps1` with negative controls for floating versions and unapproved canary packages.

**Immutable OCI Digests:**
- Files: `infra/compose.yaml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, `scripts/check-dependencies.ps1`
- Why fragile: Container images are pinned to multi-arch SHA-256 digests. If upstream image tags change, builds will fail or diverge unless digests are updated synchronously.
- Safe modification: Check multi-arch manifests with `docker buildx imagetools inspect` before updating digests.

## Scaling Limits

**Offline Ingestion Memory Footprint:**
- Current capacity: Handles target size of 150 games (with bounds 100-300).
- Limit: Memory dictionary aggregation (`_aggregate()` in `scripts/acquire_catalogue.py:174-219`) operates entirely in memory.
- Scaling path: If scaling to thousands of games in later research phases, transition to streaming JSON parser (e.g., `ijson`) and direct PostgreSQL staging tables.

## Dependencies at Risk

**Next.js 16 Supply Chain Baseline:**
- Risk: Next.js 16 is an active major line. Early 16.2.x releases had transitive vulnerabilities in `sharp` and `postcss`; `next@16.3.4` resolved these to zero vulnerabilities.
- Impact: New zero-day advisories could emerge in newer patches.
- Migration plan: Maintain strict `pnpm audit` gate; update only with exact patch pins and human authorization.

## Missing Critical Features

**Frontend UI Scaffold:**
- Problem: `apps/web` contains package configuration and test sentinels, but no App Router pages (`app/layout.tsx`, `app/page.tsx`), navigation components, or styling yet.
- Blocks: End-user browsing, login journeys, and browser visual manual verification.

**API Viewsets & Serializers:**
- Problem: `apps/api` has models and health endpoint (`/health/`), but no REST endpoints for catalogue querying, backlog entry updates, or authentication.
- Blocks: Frontend client integration.

## Test Coverage Gaps

**Catalogue and Library Domain Model Tests:**
- What's not tested: Model fields, uniqueness constraints (`catalogue_unique_release_name_per_work`, `library_unique_entry_per_user_work`), and `StatusTransition` ordering.
- Files: `apps/api/catalogue/models.py`, `apps/api/library/models.py`
- Risk: Regressions in relational constraints could occur unnoticed until integration phase.
- Priority: High.

**End-to-End Functional Flows:**
- What's not tested: Real browser interaction with forms, ratings, search, and locale switching (currently only sentinel runner discovery exists).
- Files: `e2e/sentinel.spec.ts`
- Risk: User experience and accessibility defects.
- Priority: High.

---

*Concerns audit: 2026-09-04*
