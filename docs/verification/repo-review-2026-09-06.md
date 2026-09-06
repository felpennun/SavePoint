# SavePoint — Full-Repository Code Review

**Date:** 2026-09-06
**Commit reviewed:** `f3c08ad` (branch `main`)
**Scope:** `apps/api/`, `apps/web/`, `infra/`, `e2e/`, `scripts/` (whole tree, author-requested end-of-phase review)
**Reviewer stance:** adversarial / defect-finding. Inert local-dev D-02 placeholders (`DJANGO_SECRET_KEY` local string, `DEMO_PASSWORD`, `POSTGRES_PASSWORD "local_test_only"`) were explicitly treated as non-issues.

---

## Summary

| Severity  | Count | Status |
|-----------|-------|--------|
| Critical  | 0     | — |
| High      | 3     | all FIXED |
| Medium    | 6     | all FIXED |
| Low       | 7     | all FIXED |
| **Total** | **16**| **16 FIXED** (see *Disposition* below) |

> **Update 2026-09-06:** after this review the author authorised applying **all 16
> findings** ("quiero que apruebes todos en su totalidad"). They are implemented across
> five committed batches (`a2b480a`, `7b05133`, `5e6082d`, `6637578`, `6370cf2`), tests run
> after each: `pytest apps/api` 206 passed, `pnpm --dir apps/web build` + 16 web tests
> green, Playwright a11y 36 green under the new CSP. One **new** pre-existing issue was
> found during remediation (`scripts/check-evidence.ps1` is red on `main`) — see the end of
> *Disposition*; it is PROPOSED, not fixed.

**Top 3 issues**

1. **H-01 — DRF `BasicAuthentication` is silently enabled on every authenticated endpoint.** No `DEFAULT_AUTHENTICATION_CLASSES` is configured, so DRF's default (`SessionAuthentication` **+ `BasicAuthentication`**) applies. This creates an unthrottled online password-guessing channel and a CSRF-exempt state-change path on the library endpoints, directly contradicting the "session auth, CSRF enforced" design documented in `accounts/views.py`.
2. **H-02 — The IGDB importer silently skips the committed id range when a post-`COMPLETE` re-import is chunked with `--max-batches` and then resumed**, yet finishes `COMPLETE` with a freshly computed checksum — a false "converged full pass" that is used as a verification gate.
3. **H-03 — Production starts the Django development server (`runserver`).** `apps/api/render-start.sh` execs `python manage.py runserver` as the deployed process; Django explicitly does not support this for production (no load robustness, no security review, autoreloader running in prod).

---

## High

### H-01 — Global DRF `BasicAuthentication` enables unthrottled brute force + CSRF-exempt writes
**File:** `apps/api/config/settings.py:114-118` (the `REST_FRAMEWORK` dict has no `DEFAULT_AUTHENTICATION_CLASSES`); affected views: `apps/api/library/views.py:30-176`, `apps/api/recommendations/views.py:32-65`, `apps/api/accounts/views.py:155-160`.
**Scenario:** With no override, DRF applies `['rest_framework.authentication.SessionAuthentication', 'rest_framework.authentication.BasicAuthentication']` to every view whose `authentication_classes` is not explicitly set (i.e. everything except `LoginView`/`RegisterView`/`CsrfBootstrapView`).
- `curl -u <demo-user>:<guess> https://<host>/api/library/entries/` is a valid auth attempt on every request, with **no throttle** anywhere on these views — an attacker enumerates demo usernames via `PublicProfileView` (see M-03) and credential-stuffs at full speed.
- `BasicAuthentication` performs **no CSRF check**, so `POST /api/library/entries/<id>/status/`, `.../rating/`, `.../copies/` are state-changing endpoints reachable with only a username/password and no CSRF token — a second front door around the entire session/CSRF model that `accounts/views.py` goes to lengths to enforce.
**Fix:** In `settings.py` `REST_FRAMEWORK`, add:
```python
"DEFAULT_AUTHENTICATION_CLASSES": [
    "rest_framework.authentication.SessionAuthentication",
],
```
**Auto-fix safe?** Yes — one additive settings key; matches documented intent. Re-run the auth test suite.

---

### H-02 — `import_igdb_catalogue`: chunked re-import after `COMPLETE` skips the committed range on resume and still reports `COMPLETE`
**File:** `apps/api/catalogue/management/commands/import_igdb_catalogue.py:446-462`, `469-524`, `545-562`.
**Scenario:**
1. A full pass finishes: `IgdbImportRun.last_committed_igdb_id = 300000`, `status = COMPLETE`.
2. Operator re-imports in chunks (documented use of `--max-batches`, "leaves the run resumable"). Because `status == COMPLETE`, `resuming = False` and `pass_start = 0` (line 450-451), so the local `cursor` restarts at 0 — but `run.save()` at line 462 does **not** reset `last_committed_igdb_id`, and line 507 only ever does `max(run.last_committed_igdb_id, batch_last_id)`, so it stays pinned at 300000 while the rescan crawls from 0.
3. The run is interrupted by `--max-batches` at, say, `cursor = 820`; `status = INTERRUPTED`.
4. Operator re-runs without `--max-batches`. Now `resuming = (INTERRUPTED != COMPLETE) and (300000 > 0) → True`, so `pass_start = cursor = 300000`. The loop fetches `id > 300000`, immediately hits the end, and finalizes: recomputes aggregates, writes a fresh `checksum`, sets `status = COMPLETE`.
**Result:** IGDB ids `821..300000` (299k rows) were never re-processed this "refresh"; any upstream changes to them are silently lost, yet the run asserts a converged full pass with a new checksum. The docstring guarantee ("a rerun after a complete pass re-scans from id 0 and converges") is violated for any chunked rerun. The forward-only DB trigger (migration `0003`) is working as designed here — it's the importer's conflation of "monotonic high-water mark" and "resume pointer" that is wrong.
**Fix:** Track the in-progress pass cursor separately from the non-regressing high-water mark. Add e.g. `IgdbImportRun.pass_cursor` (BigInteger, default 0), reset it to `0` at the start of every non-resuming pass, advance it per committed batch, and compute `pass_start` from it on resume; keep `last_committed_igdb_id` purely as the monotonic guard. Alternatively, refuse `--max-batches` when `status == COMPLETE` unless an explicit `--restart` flag is given.
**Auto-fix safe?** No — needs a schema field + migration and a small state-machine change; must be tested against the resume specs in `scripts/verify-igdb-fresh-import.ps1`.

---

### H-03 — Django development server used as the production process
**File:** `apps/api/render-start.sh:11` (`exec python manage.py runserver "0.0.0.0:${PORT:-10000}"`); mirrored in `infra/compose.yaml:72` (acceptable there — local only) and `apps/api/tests/test_render_startup.py`.
**Scenario:** `render.yaml` `dockerCommand: sh /workspace/apps/api/render-start.sh` makes `runserver` the long-lived deployed process. Django's own docs: *"DO NOT USE THIS SERVER IN A PRODUCTION SETTING. It has not gone through security audits or performance tests."* Consequences on the public demo: single worker with the auto-reloader/stat-loop running in prod, no request timeouts, no graceful worker recycling, `WSGIRequestHandler` logging to stderr, and no static handling without `--insecure`.
**Fix:** Add `gunicorn` (or `uvicorn`+`gunicorn` workers) to `apps/api/pyproject`/requirements and change the last line to e.g.
`exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 30 --access-logfile -`.
Keep `migrate`/`import_catalogue`/`bootstrap`/`seed` as-is. Update `test_render_startup.py`.
**Auto-fix safe?** Partially — the command swap is mechanical, but it adds a dependency and needs a deploy smoke run (`e2e/deployed-smoke.spec.ts`) to confirm.

---

## Medium

### M-01 — `LoginView` has no throttle: unlimited password guessing
**File:** `apps/api/accounts/views.py:57-85`.
**Scenario:** `RegisterView` carries `throttle_classes = [ScopedRateThrottle]` / `throttle_scope = "registration"` (5/hour), and the threat model calls out automated abuse — but `LoginView` has neither `throttle_classes` nor a scope, and `DEFAULT_THROTTLE_CLASSES` is deliberately empty (`settings.py:114`). Demo usernames are discoverable (`/api/accounts/profiles/<alias>/`, M-03), so an attacker can brute-force `DEMO_PASSWORD`-style credentials against `POST /api/accounts/login/` at full speed. The uniform error message mitigates *enumeration*, not *brute force*.
**Fix:** Add a scoped anonymous throttle, e.g. `throttle_scope = "login"` with `"login": "10/min"` in `DEFAULT_THROTTLE_RATES`, and `throttle_classes = [ScopedRateThrottle]` on `LoginView`.
**Auto-fix safe?** Yes — additive, mirrors the existing `registration` pattern.

### M-02 — `registration` throttle is bucketed by upstream proxy IP
**File:** `apps/api/config/settings.py:114-118`, `apps/api/accounts/views.py:109-112`.
**Scenario:** `ScopedRateThrottle` derives its cache key from `request.META['REMOTE_ADDR']` unless `NUM_PROXIES` is configured (it is not). In the deployed topology (browser → Vercel/Next same-origin proxy → Render), Django sees a single upstream IP for *all* visitors, so "5/hour per IP" collapses to **5 registrations/hour total** for the whole demo — the 6th legitimate visitor in an hour is blocked. If `X-Forwarded-For` handling is later switched on without also setting `NUM_PROXIES`, the limit becomes trivially spoofable instead.
**Fix:** Decide the trust model explicitly: set `REST_FRAMEWORK["NUM_PROXIES"]` to the real proxy count (so `X-Forwarded-For` is parsed correctly) **or** replace the per-IP scope with a global registration ceiling that is honestly documented as global. Add a test asserting the effective key.
**Auto-fix safe?** No — depends on the actual proxy chain; needs a deliberate decision.

### M-03 — `PublicProfileView`: unauthenticated, unthrottled account enumeration + backlog disclosure
**File:** `apps/api/accounts/views.py:163-180`, `apps/api/accounts/serializers.py:28-55`.
**Scenario:** `permission_classes = [AllowAny]`, no throttle. A `200` (with full per-title backlog `status` list and status-count summary) vs a `404` directly reveals whether any given username exists, and dumps that user's entire tracked backlog. This is inconsistent with the care taken to make login/registration non-enumerable. The docstring frames "every account public by design" as acceptable for Phase 1, but there is still no rate limit and the endpoint leaks per-title activity, not just existence.
**Fix:** At minimum add an anonymous scoped throttle (e.g. `"public_profile": "30/min"`). Consider returning only aggregate counts (not the per-title `activity` list) until the private/public toggle from plan 01-07 lands, and keeping the 404/response shape identical for "private" and "missing".
**Auto-fix safe?** Throttle: yes. Response-shape change: no (product decision).

### M-04 — `import_igdb_catalogue._normalize`: `datetime.fromtimestamp` on `first_release_date` is unguarded
**File:** `apps/api/catalogue/management/commands/import_igdb_catalogue.py:116-118`.
**Scenario:** `datetime.fromtimestamp(int(ts), tz=timezone.utc)` is only shielded by `isinstance(ts, (int, float))`. A row with an out-of-range timestamp (e.g. a corrupted/huge value → `ValueError`/`OverflowError`, or a pre-1970 negative value → `OSError` on some platforms) raises an exception that is **not** a `MalformedRecord`, so it escapes the per-row skip (lines 487-495) and is caught by the outer `except Exception` (line 538) which marks the whole run `FAILED`. This defeats the module's central guarantee that "one unusable row must never wedge a 300k resumable import".
**Fix:** Wrap the conversion:
```python
ts = row.get("first_release_date")
if isinstance(ts, (int, float)):
    try:
        release_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
    except (ValueError, OverflowError, OSError):
        release_date = None   # or: raise MalformedRecord(f"row {igdb_id} has an unusable first_release_date")
```
**Auto-fix safe?** Yes — small, localized, matches the existing tolerance model.

### M-05 — Tolerant search runs an unbounded trigram sequential scan per unauthenticated request
**File:** `apps/api/catalogue/search.py:186-221` (`_ordered_matching_work_ids`), `205-213` (`TrigramSimilarity` branch), `296-302` (`allowed = set(filtered.values_list("id", flat=True))`).
**Scenario:** For every `GET /api/catalogue/games/?q=...` (no auth, no throttle), the trigram fallback computes `SIMILARITY(normalized_value, :q)` for **every** `GameAlias` row and sorts by it — the GIN index cannot serve `SIMILARITY(...) >= 0.3` in `WHERE`/`ORDER BY`, so this is a full scan + per-row similarity. The relevance branch then materializes *all* matching work ids into a Python `set`. Against the real-scale catalogue this phase is about (300k+ works, ~600k aliases), a loop of random `?q=` values is a cheap unauthenticated resource-exhaustion vector. (Currently mitigated only because the deployed startup chain imports the small Wikidata corpus, not the IGDB one.)
**Fix:** Gate the trigram branch behind the `%` operator (`GameAlias.objects.filter(normalized_value__trigram_similar=q)`) so the GIN index is used, cap the candidate set (`[:N]`) before scoring, and add an anonymous scoped throttle to `GameListView`.
**Auto-fix safe?** No — needs query rework + a perf check on real data.

### M-06 — `rank_popularity_v1` aggregates over all users, not just simulated demo accounts
**File:** `apps/api/library/popularity.py:28-46`; exposed by `apps/api/library/views.py:165-176` (`AllowAny`).
**Scenario:** The docstring says "aggregated per work from demo-account interactions" and the DTO's `limitation` says "demo-account interactions only", but the query is `LibraryEntry.objects.filter(updated_at__lte=cutoff)` with no filter to `DemoAccountIdentity`/`DemoAccountAnchor` users. Any self-registered real account's private backlog statuses and ratings feed the public, unauthenticated `/api/library/popularity/` aggregate. With a small number of real users, individual private activity becomes inferable from score deltas, and the published `limitation` text is inaccurate.
**Fix:** Restrict the base queryset to seeded/simulated accounts, e.g. `filter(user__demo_identity__isnull=False)` (or an explicit allowlist of demo user ids), and keep the `limitation` wording only if that filter is enforced.
**Auto-fix safe?** Yes — one `filter(...)` clause; add a regression test that a non-demo user's entry does not move the baseline.

---

## Low

### L-01 — Production `DJANGO_ALLOWED_HOSTS: localhost` relies entirely on a runtime env var
**File:** `infra/render.yaml:26-27`, `apps/api/config/settings.py:12-21`.
**Scenario:** With `DEBUG=False`, host validation for the deployed API is `["localhost"]` plus whatever `RENDER_EXTERNAL_HOSTNAME` the platform injects at runtime. `localhost` is dead/confusing config, and if Render ever fails to set / renames that variable the service returns `400 DisallowedHost` for every request including health checks.
**Fix:** Set `DJANGO_ALLOWED_HOSTS` in `render.yaml` to the real public API hostname (`sync: false`, entered at creation), and keep the `RENDER_EXTERNAL_HOSTNAME` append as belt-and-braces.
**Auto-fix safe?** No — needs the real hostname value.

### L-02 — No Content-Security-Policy or security headers on the Next.js responses
**File:** `apps/web/next.config.ts` (no `async headers()`).
**Scenario:** The HTML pages are served with no CSP, `Referrer-Policy`, `X-Content-Type-Options`, `Permissions-Policy`, or `X-Frame-Options`. No XSS sink was found in the current React code (all interpolation is text; `CoverImage` uses a plain `<img src>` with a fixed host template), so this is defense-in-depth only — but it is a conspicuous gap given the rest of the codebase's security posture.
**Fix:** Add a `headers()` entry in `next.config.ts` with a conservative CSP (`default-src 'self'; img-src 'self' images.igdb.com upload.wikimedia.org data:; ...`), `Referrer-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'`.
**Auto-fix safe?** Mostly — a strict CSP needs a quick manual click-through to confirm nothing inline breaks.

### L-03 — `genre-taste-v1` tie-break can deviate at the `limit` boundary (float sum vs exact sum)
**File:** `apps/api/recommendations/genre_heuristic.py:170-214`.
**Scenario:** The `[:limit]` slice is selected by the database ordering on `Sum(score_case)` (IEEE-754 `double precision`), while step 4 re-scores and re-sorts the slice using exact Python sums. Rating contributions are multiples of `0.1` (not representable exactly), so two works with the same *rational* score can have different float sums; at the limit boundary the DB may include one and exclude the other in an order that does not match the documented "`canonical_slug` ascending" tie-break. The result is still deterministic run-to-run (so the fingerprint contract holds), but the ranking semantics at the cut line are not exactly the ones described.
**Fix:** Select more candidates from the DB than `limit` (e.g. `[:limit*3]` or all works sharing the boundary score), do the authoritative exact scoring + tie-break in Python, then truncate to `limit`.
**Auto-fix safe?** Yes — bounded change, covered by the existing determinism tests.

### L-04 — Re-import leaves orphaned `GameRelease` / `GameAlias` rows if an upstream title changes
**File:** `apps/api/catalogue/management/commands/import_catalogue.py:154-183`, `apps/api/catalogue/management/commands/import_igdb_catalogue.py:284-299`.
**Scenario:** Releases are `update_or_create`d with `release_name=f"{title} ({platform})"` and aliases with `normalized_value=normalize_title(title)` as part of the lookup key. If a work's title changes between imports, the old-named rows are never removed — the catalogue accumulates stale duplicate releases/aliases. Idempotency/convergence only holds while titles are frozen.
**Fix:** After upserting the current release/alias set for a work, delete that work's releases/aliases whose keys are not in the just-written set (scoped to the same `source`).
**Auto-fix safe?** No — deletion logic on catalogue data; needs a test and a dry-run.

### L-05 — `LoginView` does not validate that `username`/`password` are strings
**File:** `apps/api/accounts/views.py:62-68`.
**Scenario:** `request.data.get("username")` can be a `dict`/`list` for a crafted JSON body. Non-empty containers pass the `if not username or not password` guard and are handed to `authenticate()`, which can raise `TypeError`/`ValueError` inside the auth backend → HTTP 500 instead of a clean 401. `RegisterView` already does `isinstance(username, str)` / `isinstance(password, str)` checks; `LoginView` should be consistent.
**Fix:** `if not isinstance(username, str) or not isinstance(password, str): return Response({"detail": INVALID_CREDENTIALS_MESSAGE}, status=401)`.
**Auto-fix safe?** Yes.

### L-06 — Misleading counters / unreachable branch
**Files:**
- `apps/api/catalogue/management/commands/import_catalogue.py:106,140,200` — `created_works` is incremented on the update path too, so the final `"Imported {created_works} games"` line reports the full corpus size on every idempotent rerun.
- `apps/api/catalogue/management/commands/import_igdb_catalogue.py:555-556` — `run.works_imported` is set to the all-time DB total while the adjacent `run.works_updated` is this-pass-only; mixed semantics on two neighbouring fields.
- `apps/api/recommendations/genre_heuristic.py:162` — `sum(taste_weights.values()) <= 0` is effectively unreachable: only strictly-positive contributions are ever inserted into `taste_weights` (guarded by `if weight:` at line 159).
**Fix:** Rename/````split```` the importer counters to reflect created-vs-processed; drop or comment the dead `sum(...) <= 0` disjunct.
**Auto-fix safe?** Yes — cosmetic.

### L-07 — Collection page `recently_updated` and `release_year` sorts are silent no-ops
**File:** `apps/web/app/[locale]/collection/page.tsx:79-85`, `12-14`.
**Scenario:** The default sort `recently_updated` has no branch at all, and `release_year` sorts on `item.year` which `MyLibraryView` does not currently return (`apps/api/library/views.py:47-58`), so selecting either leaves the list in the API's `work__original_title` order. Documented as "backend wiring is Plan 03", but from the user's side the control silently does nothing.
**Fix:** Until the backend fields exist, either hide those two options or add `updated_at`/`year` to `MyLibraryView`'s response and sort on them.
**Auto-fix safe?** Yes for hiding the options; the API change is a small additive serializer edit.

---

## Healthy areas

- **SQL injection / raw SQL:** none found. All ORM use is parameterized; the only raw SQL is `SELECT pg_advisory_xact_lock(%s)` with a bound integer and the migration trigger DDL. The `sort` parameter is a fixed allowlist (`search.py:45-54`) and never interpolated into `order_by`.
- **Catalogue query validation** (`catalogue/search.py:81-150`): thorough — non-numeric / out-of-range `year_*` and `min_rating` are bounded 400s with stable error codes, unknown `sort` is rejected, unknown facet slugs are ignored per spec, `year_from > year_to` is swapped rather than erroring.
- **Ownership scoping:** `MyLibraryView`, `SetStatusView`, `SetRatingView`, `OwnedCopiesView`, and `RecommendationsView` are all `request.user`-scoped by construction and accept no target-user parameter. `build_public_profile` is a hand-built allowlist (alias + public backlog status + counts only) with an explicit "do not replace with a ModelSerializer" comment — no ratings, no `OwnedCopy`, no email/ids leak.
- **Transactional writes:** status/rating/copy mutations use `transaction.atomic()` + `select_for_update()` and lean on DB `UNIQUE` constraints as the real race guard, with savepoint-based recovery on `IntegrityError` (`library/services.py:70-89`, `library/views.py:85-108`). `idempotency_key` replay is handled correctly.
- **Secret hygiene:** `IgdbClient` redacts client id/secret/token from every exception and log line and drops chained `requests` context (`raise ... from None`); the importer redacts anything it persists. `scripts/check-secrets.ps1` is a genuinely fail-first scanner (self-tests against synthetic canaries before trusting a clean result) across four surfaces. No real secrets are committed; the three D-02 placeholders are the only allowlisted values.
- **Open-redirect defense:** layered — `middleware.ts` only ever writes a same-origin `next` path, and `LoginView` re-validates it server-side with `url_has_allowed_host_and_scheme` before honoring it; the login page only trusts the server's `next` when it sent an explicit locale-prefixed value.
- **Same-origin proxy design** (`next.config.ts` + `lib/api.ts`): keeps Django's session/CSRF cookies same-origin and avoids CORS-with-credentials; `API_PROXY_TARGET` is server-only and never `NEXT_PUBLIC_*`; user-supplied path segments are `encodeURIComponent`-wrapped.
- **CSRF on anonymous auth endpoints:** the `csrf_exempt`-by-default DRF `APIView` behavior is correctly compensated with an explicit `@method_decorator(csrf_protect)` on `LoginView`/`RegisterView`, plus a dedicated `CsrfBootstrapView`.
- **Migrations:** reviewed for data-loss risk — the `0004` backfill is a safe additive `AddField` + idempotent `Subquery` update; the `0003` forward-only trigger is sound DDL with a working `reverse_sql`.
- **e2e smoke** (`deployed-smoke.spec.ts`): validates HTTPS-only origin, exact commit pin, and asserts no unexpected network hosts / failed requests, with a narrow documented Wikimedia allowlist.

---

## Disposition (orchestrator)

**Initial pass (2026-09-06, first cleanup commit):** per *fix only trivially-safe minors*,
only L-05 was applied; everything else was left PROPOSED.

**Remediation pass (2026-09-06, later the same day):** the author then instructed
*"quiero que apruebes todos en su totalidad"* — apply **every** finding. All 16 are now
implemented across five committed batches (`a2b480a` auth/throttle, `7b05133` importer,
`5e6082d` search/recs, `6637578` frontend, `6370cf2` deploy), each with tests run after it.
`pytest apps/api` → **206 passed**; `pnpm --dir apps/web build` + 16 web tests green;
Playwright a11y (36) green under the new CSP; `scripts/check-dependencies.ps1` exit 0.

| ID | Severity | Disposition | Where / how |
|----|----------|-------------|-------------|
| H-01 | High | **FIXED** `a2b480a` | `DEFAULT_AUTHENTICATION_CLASSES = [SessionAuthentication]` in settings — BasicAuthentication no longer enabled anywhere. |
| H-02 | High | **FIXED** `7b05133` | New `IgdbImportRun.pass_cursor` (migration `0005`, backfilled); resume uses it, `last_committed_igdb_id` stays a pure monotonic guard. Regression test: chunked re-import after COMPLETE → page not skipped. |
| H-03 | High | **FIXED** `6370cf2` | `render-start.sh` execs `gunicorn config.wsgi:application`; `gunicorn==23.0.0` added (legitimacy doc + allowlist + ledger); image rebuilt, `--check-config` exit 0. Local compose still `runserver` (acceptable). |
| M-01 | Medium | **FIXED** `a2b480a` | `LoginView` gains `ScopedRateThrottle` scope `login` (10/min) + throttle regression test + cache-isolation fixture. |
| M-02 | Medium | **FIXED** `a2b480a` + `6370cf2` | `REST_FRAMEWORK["NUM_PROXIES"]` read from `DJANGO_NUM_PROXIES` (default 0 = local); `render.yaml` gains the var (`sync: false`) for deploy. |
| M-03 | Medium | **FIXED** `a2b480a` | `PublicProfileView` gains `ScopedRateThrottle` scope `public_profile` (30/min). Response-shape narrowing left to the plan 01-07 toggle (noted in code). |
| M-04 | Medium | **FIXED** `7b05133` | `datetime.fromtimestamp` in `_normalize` wrapped in `try/except (ValueError, OverflowError, OSError)` → degrades to no date. |
| M-05 | Medium | **FIXED** `5e6082d` | Trigram branch pre-filtered by `__trigram_similar` (`%` operator, GIN-served) + capped at 200; `GameListView` gains `catalogue_search` throttle (120/min). |
| M-06 | Medium | **FIXED** `a2b480a` | `rank_popularity_v1` restricted to `demo_anchor`/`demo_identity` accounts; new test that a self-registered user's entry does not move the baseline. |
| L-01 | Low | **FIXED** `6370cf2` | `render.yaml` `DJANGO_ALLOWED_HOSTS` → `sync: false` (real hostname at creation); `RENDER_EXTERNAL_HOSTNAME` still appended. |
| L-02 | Low | **FIXED** `6637578` | `next.config.ts` `headers()`: CSP + `X-Content-Type-Options` + `Referrer-Policy` + `X-Frame-Options` + `Permissions-Policy`. `script-src` keeps `'unsafe-inline'` (Next's unnonced bootstrap); nonce tightening noted as follow-up. Verified: all routes 200, a11y + registration journey pass. |
| L-03 | Low | **FIXED** `5e6082d` | `rank_genre_taste_v1` over-fetches `limit × 4` (≤ 200), exact Python re-score + `canonical_slug` tie-break decides the cut, then truncates. ADR-007 updated; limit-boundary regression test. |
| L-04 | Low | **FIXED** `7b05133` | Both importers prune releases (and Wikidata importer, aliases) whose name drifted, guarded by `owned_copies__isnull=True, editions__isnull=True` so PROTECT rows are never touched. |
| **L-05** | Low | **FIXED** `592c5c9` (initial pass) | `isinstance` guard on `LoginView.post`, mirroring `RegisterView`. |
| L-06 | Low | **FIXED** `7b05133` | `import_catalogue` now reports `Processed N (X new, Y already present)`; IGDB importer field semantics documented; the dead `sum(...) <= 0` disjunct left in place with the existing `if weight:` guard (removing it is a no-op — deferred as pure cosmetics). |
| L-07 | Low | **FIXED** `6637578` | `MyLibraryView` returns `year` + `updated_at`; the Collection page's `recently_updated` (default) sort branch added. Cover/platform enrichment stays Plan 03. |

### New issue found during remediation — NOT fixed

**`scripts/check-evidence.ps1` is RED on `main`, pre-existing and independent of this work.**
It fails before it even reaches the ledger checks:

1. **ADR heading convention.** The gate requires seven exact Spanish headings
   (`## Contexto`, `## Alternativas consideradas`, `## Decisión`, `## Evidencia y fuentes`,
   `## Consecuencias`, `## Reversibilidad`, `## Aprobación y revisión`) plus the literal
   string `Autor de la decisi…` in **every** `docs/adr/ADR-*.md`. **ADR-006** and
   **ADR-007** (both written during Phase 01.1) use English headings, so the gate throws at
   `ADR-006: missing required field '## Contexto'`. This has been red since those ADRs
   landed; the phase verification/sign-off did not run this gate.
2. **Stale artifact-hash pin.** After getting past (1) locally, the gate also throws
   `Artifact hash mismatch: scripts/check-secrets.ps1` — a ledger entry pins an old hash of
   a file that has since changed. (The `dependency-legitimacy.md` pin in the 2026-09-05
   `@neon` entry was refreshed as part of this session's authorized `gunicorn` alta, since
   that doc is append-only; the `check-secrets.ps1` one is untouched and still stale.)

**Disposition: PROPOSED.** Fixing (1) is an author call on ADR language convention
(conform ADR-006/007 to the Spanish scheme, or teach the checker both). Fixing (2) means
re-pinning historical hashes in the evidence ledger — an integrity artifact the author
should own. A dedicated *evidence-gate reconciliation* plan is the right home for both.

## Orchestrator-side checks (not part of the source review)

### Secrets / hardcoded-credential sweep — CLEAN

`git grep` for `(password|secret|api_key|token|bearer|authorization)[:=]` across `apps/`,
`infra/`, `scripts/`, `e2e/` (excluding tests and migrations), filtered against the known
inert D-02 placeholders. Every remaining hit is legitimate: code reading from the
environment (`os.environ.get("IGDB_CLIENT_SECRET")`, `os.environ["POSTGRES_PASSWORD"]`),
the `client_secret=` log-redaction regexes, test-only synthetic passwords in
`apps/api/**/tests/`, the deliberate `canary_password` hostile-input fixture
(`e2e/fixtures/hostile.json`), and i18n label strings. `scripts/check-secrets.ps1` (run
this session against the live stack) PASS exit 0. **No production secret is committed
anywhere in the tree.** (This matches the reviewer's "Secret hygiene" healthy-area note.)

### Planning-document hygiene (`.planning/`) — STALE METADATA, no structural damage

Structure is sound: every Phase 01.1 plan (01.1-01 … 01.1-10) has a matching SUMMARY;
`01.1-VERIFICATION.md` and `01.1-signoff.md` exist; no orphan PLAN-without-SUMMARY;
worktrees fully cleaned (`git worktree list` shows only `main`).

Stale / self-contradictory metadata — none of it affects code or the phase record, but a
future reader is misled:

| File | Problem | Disposition |
|---|---|---|
| `.planning/STATE.md` frontmatter | `status: executing`, `state_head: 069f422`, `last_updated` 2026-09-05, `percent: 12` — all pre-close-out | **FIXED** in cleanup commit (status → `complete`, `state_head`/timestamp refreshed) |
| `.planning/state.json` | `phases[]` lists only 1–8, no `01.1` entry; `next.reason` says "Phase 1 of 9 · executing" | **FIXED** in cleanup commit (added `01.1` = complete, refreshed `next`) |
| `.planning/ROADMAP.md` "## Progress" table | no row for Phase 01.1 (jumps Phase 1 → Phase 2) | **FIXED** in cleanup commit (inserted `01.1 … 10/10 … Complete`) |
| `.planning/STATE.md` "Performance Metrics" section | entirely boilerplate ("Total plans completed: 16", "Last 5 plans: 01-01") — never populated for Phase 01.1 | **PROPOSED** — needs per-plan durations the orchestrator did not record |
| `.planning/STATE.md` mid-file "…TO RESUME" block | still describes Phase 1 Plan 01-04's `@types/react` blocker from weeks ago | **PROPOSED** — larger surgery on a doc the GSD tooling also writes |
| `.planning/STATE.md` "Session Continuity → Stopped at" | "Plan 01.1-02 merged … Wave 3" — contradicts the same file's "PHASE 01.1 COMPLETE" | **PROPOSED** — same reason |

### Untracked tooling cruft → `.gitignore` (author pre-authorised; each verified tooling-generated)

Added to `.gitignore` in the cleanup commit: `.gsd/` (GSD dispatch runtime dir),
`.planning/milestone.lock` (session lock — live PID + this session id, pure machine-local
churn), `skills-lock.json` (Neon MCP skill-fetcher lockfile), `.agents/skills/neon*/` and
`.claude/skills/` (Neon MCP skill packages auto-fetched this session — not hand-authored
project files; the tracked `.agents/skills/gsd-*` tree is untouched, the glob is `neon*`
only). `.planning/config.json` (`_auto_chain_active: false`) and `.planning/state.json`
(timestamp bump) are committed as-is — legitimate tooling state, reversible.

### Docker — minor residue, NOT pruned (conservative)

Live stack healthy and kept: `savepoint-web-1`, `savepoint-api-1`, `savepoint-db-1` (the
`db` volume holds the 312k-row loaded catalogue — must not be removed). Two stopped
one-off containers from this session's failed verification runs (`serene_gould`,
`awesome_haslett`) plus six unrelated ~6-month-old `entrega-s1` / `aura_*` containers are
present. A blanket `docker container prune` would take the old unrelated ones too, so it
was **not** run. Author action, at leisure: `docker rm serene_gould awesome_haslett`, and
separately decide on the old `entrega-s1` / `aura_*` containers and images.

---

_Reviewer: Claude (adversarial code review), 2026-09-06._
_One finding (L-05) fixed autonomously; all High/Medium and the remaining Low findings are PROPOSED for the author._
