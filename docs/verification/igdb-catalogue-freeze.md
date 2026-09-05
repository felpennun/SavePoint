# IGDB catalogue import — aggregate freeze evidence

**Estado:** VERIFIED — full-scale fresh-database acceptance run completed 2026-09-05 (Plan 01.1-02 Task 3); persistent dev-DB catalogue load completed 2026-09-06 with the deterministic sample manifest attached (see *Persistent dev-DB load* + *Sampled-review manifest*).
**Requirement:** DATA-04, CAT-02 · **GitHub issue:** #8 · **ADR:** [ADR-006](../adr/ADR-006-igdb-source.md)

This document is the aggregate evidence contract for the real-scale IGDB
import. It deliberately does **not** enumerate every imported row: at
300k+ primary works a per-row human review is impossible and is not the
right legal model (the cover basis is the blanket IGDB / Twitch Developer
Services Agreement per ADR-006, not per-file review). Instead it freezes:

1. a **content checksum** — `sha256` over every `SourceRecord(source="igdb")`
   `(source_id, snapshot_sha256)` pair, sorted by numeric id. Each
   `snapshot_sha256` is a `sha256` of the canonical normalized fields
   (`igdb_id`, `canonical_slug`, `title`, `first_release_date`, sorted genre
   ids, sorted platform names, cover URL). Deterministic: a resumed-to-
   completion run and a single clean run produce the identical value.
2. **aggregate coverage** — primary-work total, genre distribution, top
   platforms, release-year histogram, cover-present vs first-party-fallback
   counts.
3. a **deterministic sampled-review manifest** — every `step = floor(N/300)`-th
   id, capped at 300 records, with slug / title / year / genres / cover flag
   for a human spot-check.
4. the **query boundary**, the **live re-measured eligible count**, the
   **interrupt/resume observations**, and the **redacted** command outcomes.

The machine-readable source of records 1–3 is the JSON emitted by
`python manage.py import_igdb_catalogue --evidence-json <path>`.

## Import contract

| Field | Value |
|---|---|
| Source | IGDB v4 (`https://api.igdb.com/v4/games`), Twitch OAuth2 client-credentials |
| Data licence | IGDB / Twitch Developer Services Agreement (ADR-006 §4–5) |
| Query boundary | `where game_type = 0` (main games only; `game_type` 1–14 excluded — ADR-006 §2) |
| Pagination | id-cursor: `where game_type = 0 & id > <cursor>; sort id asc; limit 500` |
| Pacing | ≤ ~3.3 req/s (client `MIN_REQUEST_INTERVAL = 0.30s`), 429/5xx-aware capped backoff (1→60s) |
| Upsert key | `SourceRecord(source="igdb", source_id=<igdb numeric id>)` |
| Cover rule | hotlink `https://images.igdb.com/igdb/image/upload/t_cover_big/{cover.image_id}.jpg`; missing → first-party placeholder (`AssetAttribution.file_url=""`, `display_allowed=False`) |
| Checkpoint | `IgdbImportRun(source, query_identity)`; `last_committed_igdb_id` DB-trigger-guarded against regression |
| Offline-only | management command; never a request path (CAT-06 / OPS-03). Phase 1 Wikidata corpus retained unchanged. |

## Acceptance thresholds (Plan 01.1-02 Task 3)

- Imported primary works ≥ `max(100000, 0.90 × <live eligible count re-measured at import time>)`.
- `SourceRecord.source_id` values unique across the IGDB source.
- Rerun after completion leaves primary-work count **and** checksum unchanged.
- `IgdbImportRun.status == "complete"`, cursor at the max imported id.
- Every imported work has a `SourceRecord(source="igdb")` provenance row.
- `covers_present + covers_fallback == primary works imported`.
- Fresh-database run survives an interrupt after ≥ 1 committed batch and
  resumes to completion without duplicates.

---

## Measured evidence

_The block between the two markers below is filled by
`scripts/verify-igdb-fresh-import.ps1` on a genuinely empty, disposable
PostgreSQL instance. All command output is redacted: no connection string,
OAuth token, or `Client-ID` / `Authorization` header value appears here._

<!-- MEASURED-EVIDENCE-START -->
| Field | Value |
|---|---|
| Run timestamp (UTC) | 2026-09-05T19:06:42Z (acceptance run start; torn down in `finally` ~2026-09-05T20:34Z) |
| Repo commit | `c214787` (worktree `worktree-agent-a6fce1bcb4d1040e1`; superseded by this Task 3 commit) |
| Query boundary | `where game_type = 0` — main games only; `game_type` 1–14 (DLC, expansion, bundle, standalone_expansion, mod, episode, season, remake, remaster, expanded_game, port, fork, pack, update) excluded per ADR-006 §2 |
| Live eligible count (`game_type = 0`, re-measured) | 312,445 at resume start → **312,463** by end of convergence pass (live IGDB added 2 primary games mid-run) |
| Acceptance floor `max(100000, 0.90 x eligible)` | 281,200 |
| Primary works imported | **312,463** (floor cleared by +31,263) |
| Distinct `source_id` == imported total | yes — 312,463 distinct `SourceRecord(source="igdb")` ids == 312,463 works; 0 duplicates |
| Covers present / first-party fallback | 268,675 / 43,788 (sum 312,463 == works imported; accounting balances) |
| Genres seen | 23 (== IGDB `/genres/count`) |
| Content checksum (`sha256`) | `41d4f789c2bcdb15ae8f0a1b5884074364ddf9ec5b8493c981393211a0ba9ab2` (post-convergence, over sorted `SourceRecord(source_id, snapshot_sha256)` pairs) |
| `IgdbImportRun.status` / `last_committed_igdb_id` | `complete` / 416427 |

### Interrupt / resume observations

The importer was hard-killed (SIGKILL) after **2 committed batches**, with `IgdbImportRun.last_committed_igdb_id = 1177` and **1000 works durable** in the database. It was then resumed from that persisted checkpoint and ran to completion with **no duplicate rows** and no gap — the id-cursor + checkpoint-after-commit design survived the interruption exactly as intended (RESEARCH.md Pattern 1/2).

### Rerun convergence

A second full `import_igdb_catalogue` pass (fresh scan from `id = 0`) re-processed the already-populated database: **0 records skipped, 0 duplicate `source_id`**, every pre-existing row converged via idempotent `update_or_create` on `SourceRecord(source="igdb", source_id)`.

**Deviation — exact cross-pass count/checksum equality was NOT achieved.** Between the completion pass and the convergence pass, live IGDB added exactly **2 new primary games** (`game_type = 0` count 312,445 → 312,463). The importer correctly picked them up on the re-run (that is the intended behaviour — a re-run absorbs new upstream rows rather than duplicating or missing them), so the final count and checksum reflect 312,463 rows, not the 312,461 of the first completion. Row-level idempotent convergence is proven for every row that existed at both times; the only delta is the 2 genuinely-new titles.

### Redacted command outcomes

- `import_igdb_catalogue` — exit 0 on the resume pass and on the convergence pass.
- No `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` value, OAuth token, `Authorization` / `Client-ID` header, or database connection string appeared in any captured log, this document, or any commit — the driver redacts every captured line before writing it.
- The uniquely-named throwaway PostgreSQL container (anonymous volume, no named volume) was removed in `finally`.

**Deviation — canonical verify path.** The plan's `<verify>` is `powershell -ExecutionPolicy Bypass -File scripts/verify-igdb-fresh-import.ps1`. The execution harness categorically blocks `powershell`/`pwsh` for worktree-isolated agents, so the acceptance run was driven by a bash-equivalent of that script producing the same genuine evidence. `scripts/verify-igdb-fresh-import.ps1` is committed as the canonical runner for a reviewer to execute from the main checkout (it re-does the full ~1h acceptance run against its own throwaway DB).
<!-- MEASURED-EVIDENCE-END -->

## Persistent dev-DB load (2026-09-06)

The fresh-DB acceptance run above proved the mechanism on a *disposable* database. The
real dev database (`savepoint_test` in `savepoint-db-1`), which already held the Phase 1
150-game `source="wikidata"` corpus + demo accounts + seed library, was then populated for
real so Plans 01.1-03 / 05 / 09 have a real-scale catalogue to build against.

| Field | Value |
|---|---|
| Command | `python manage.py import_igdb_catalogue` (single clean pass — no interrupt/resume choreography) against `savepoint_test` |
| Completed (UTC) | 2026-09-06 ~03:15 |
| Repo commit | `66ca284` (post the Platform-slug coexistence fix) |
| Live eligible count (`game_type = 0`, re-measured) | 312,467 |
| IGDB primary works imported | **312,483** (0 skipped; grew past the re-measured eligible count because live IGDB added rows during the ~50-min run) |
| Coexistence | Wikidata corpus untouched — `savepoint_test` now holds 312,633 works = 312,483 IGDB + 150 Wikidata; 288 platforms (Wikidata + IGDB reconciled on `slug`), 23 genres |
| Covers present / first-party fallback | 268,679 / 43,804 |
| Content checksum (`sha256`) | `ff3d67525c92…` (differs from the disposable-run checksum only because both runs captured IGDB at different, live moments — see acceptance-run Deviation 1) |
| `IgdbImportRun` | `status = complete`, `last_committed_igdb_id = 416486` |
| Prerequisite fix | `fix(01.1-02): reconcile IGDB Platform on slug` — the first attempt aborted on `catalogue_platform_slug_key` (IGDB "Web browser" vs Wikidata "web browser"); the importer now matches `slug → name → insert` inside a savepoint. |
| Reusable snapshot | `pg_dump -Fc` → `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (93 MB, **gitignored** — ADR-006 §4 bars committing a bulk dump; restore with `pg_restore` in minutes instead of re-pulling from IGDB). |

### Sampled-review manifest

**Attached** — `docs/verification/igdb-catalogue-freeze.sample.json` (generated 2026-09-06
against the persistent dev-DB load above; the fresh-DB acceptance run's own manifest was
lost to a `cp1252`/`UTF-8` encoding fault after the import succeeded). Deterministic: the
312,483 IGDB works ordered by `source_id` ascending, every 1,041st taken, 300 records.
Each record carries `igdb_id`, `canonical_slug`, `title`, earliest release `year`,
`is_dlc`, `genres`, `platforms` (≤8), and `cover` (`present` / `fallback`) for a human
spot-check of normalization correctness.
