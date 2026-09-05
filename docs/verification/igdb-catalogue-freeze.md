# IGDB catalogue import — aggregate freeze evidence

**Estado:** PENDING — awaiting the full-scale fresh-database run (Plan 01.1-02 Task 3).
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

_The block below is filled by `scripts/verify-igdb-fresh-import.ps1` on a
genuinely empty, disposable PostgreSQL instance. All command output is
redacted: no connection string, OAuth token, or `Client-ID` /
`Authorization` header value appears here._

| Field | Value |
|---|---|
| Run timestamp (UTC) | _pending_ |
| Repo commit | _pending_ |
| Query boundary | _pending_ |
| Live eligible count (`game_type = 0`, re-measured) | _pending_ |
| Acceptance floor `max(100000, 0.90 × eligible)` | _pending_ |
| Primary works imported | _pending_ |
| Distinct `source_id` == imported total | _pending_ |
| Covers present / first-party fallback | _pending_ / _pending_ |
| Genres seen | _pending_ |
| Content checksum (`sha256`) | _pending_ |
| `IgdbImportRun.status` / `last_committed_igdb_id` | _pending_ / _pending_ |

### Interrupt / resume observations

_pending_

### Rerun convergence

_pending_

### Redacted command outcomes

_pending_

### Sampled-review manifest

_Attached as `docs/verification/igdb-catalogue-freeze.sample.json` (deterministic, ≤ 300 records)._
