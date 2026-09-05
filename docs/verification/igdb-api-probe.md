# IGDB v4 API — authenticated probe evidence

**Plan:** 01.1-01 Task 2 · **Requirement:** DATA-04 · **GitHub issue:** #7
**Probe run (ISO-8601 UTC):** 2026-09-05T14:56:27Z
**Operator:** execution agent, against the real `https://api.igdb.com/v4` API using the author-provided Twitch application credentials.
**Credential handling:** `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` were read from the process environment only. No credential value, OAuth token, or `Authorization` header was printed, logged, committed, or written to this file. Presence was confirmed by variable name only.

This document records **redacted, reproducible, non-secret** observations. It is the primary-source input for `docs/adr/ADR-006-igdb-source.md`.

---

## 1. Authentication

| Property | Observation |
|---|---|
| Flow | Twitch OAuth2 `client_credentials` — `POST https://id.twitch.tv/oauth2/token` |
| Authenticated response status | **HTTP 200** — access token obtained |
| Token type | `bearer` |
| Token lifetime | `expires_in` = **4,959,769 s** (~57.4 days) |
| IGDB request auth | `Client-ID: <client id>` + `Authorization: Bearer <token>` headers on every `https://api.igdb.com/v4/*` call |

## 2. Catalogue size (authenticated counts)

| Endpoint / query | UTC time | Status | Count |
|---|---|---|---|
| `POST /v4/games/count` (no filter) | 2026-09-05T14:56:28Z | 200 | **Total games: 374555** |
| `POST /v4/games/count` — `where game_type = 0;` | 2026-09-05T14:56:29Z | 200 | **Eligible primary games (game_type = 0): 312418** |
| `POST /v4/games/count` — `where category = 0;` | 2026-09-05T14:56:28Z | 200 | 0 — legacy `category` field is deprecated / no longer populated; the live API uses `game_type` |
| `POST /v4/covers/count` | 2026-09-05T14:56:30Z | 200 | 336568 |
| `POST /v4/genres/count` | 2026-09-05T14:56:30Z | 200 | 23 |
| `POST /v4/platforms/count` | 2026-09-05T14:56:31Z | 200 | 220 |

### 2.1 Full `game_type` breakdown (sums to the unfiltered total)

| game_type | label | count |
|---:|---|---:|
| 0 | main_game | 312418 |
| 1 | dlc_addon | 17615 |
| 2 | expansion | 1736 |
| 3 | bundle | 7134 |
| 4 | standalone_expansion | 504 |
| 5 | mod | 9779 |
| 6 | episode | 976 |
| 7 | season | 866 |
| 8 | remake | 1472 |
| 9 | remaster | 1381 |
| 10 | expanded_game | 2143 |
| 11 | port | 8227 |
| 12 | fork | 135 |
| 13 | pack | 8952 |
| 14 | update | 1217 |
| — | **sum** | **374555** (matches unfiltered `/games/count`) |

**Eligible-category boundary for the SavePoint catalogue:** `game_type = 0` (main games) — **312418** rows. game_type 1–14 are non-primary entries (DLC, bundles, packs, ports, updates, mods, episodes, seasons, remakes/remasters, expansions, forks) and are excluded from the primary catalogue, consistent with the existing `RelatedContent` / `is_dlc` precedent in `apps/api/catalogue/models.py`.

## 3. Apicalypse field names (confirmed live)

Query: `fields id,name,slug,genres.name,platforms.name,cover.image_id,cover.url,first_release_date,total_rating,url; where id = 1942;` → HTTP 200, 1 row (`The Witcher 3: Wild Hunt`).

All of these current field paths resolved without error:

- `id`, `name`, `slug`, `first_release_date` (unix seconds), `total_rating` (0–100 float), `url`
- `genres.name` (dot expansion) — returned `Role-playing (RPG)`, `Adventure`
- `platforms.name` (dot expansion) — returned 6 platforms
- `cover.image_id` — returned `coaarl`
- `cover.url` — returned `//images.igdb.com/igdb/image/upload/t_thumb/coaarl.jpg`

Assumption A3 (RESEARCH.md) is **confirmed**: `genres.name`, `platforms.name`, `cover.image_id`, `first_release_date`, `total_rating` are current.

## 4. Rate limiting and quota (probe-derived + primary-source)

**Quota conclusion: there is NO monthly request quota on the current Twitch-OAuth v4 API.**

- Primary source — `https://api-docs.igdb.com/` › *Rate Limits* (verbatim): "There is a rate limit of 4 requests per second. If you go over this limit you will receive a response with status code 429 Too Many Requests. You are able to have up to 8 open requests at any moment in time."
- No monthly cap is stated anywhere in the primary documentation. The historical "50,000 requests/month" figure applied to the deprecated pre-Twitch (RapidAPI) tier and does not apply. Assumption A1 (RESEARCH.md) is **confirmed**.
- Rate-limit headers: the IGDB API returned **no `X-RateLimit-*` / `RateLimit-*` headers** on any response — only `Content-Type` and `Date`. Rate-limit state is not observable from headers; a `429` body is the only signal.
- Observed behaviour: 12 back-to-back sequential `POST /v4/games/count` calls with no client-side pacing all returned **HTTP 200** (no 429). Sequential round-trips did not exceed 4 req/s.
- Multiquery concurrency cap (observed): a `POST /v4/multiquery` with 15 sub-queries returned **HTTP 400** — body `{"title":"Too Many Concurrent queries","details":"The maximum amount of concurrent request is at 10 queries"}`. Split into two multiqueries of ≤10 sub-queries, both returned HTTP 200.

**Importer pacing rule for Plan 01.1-02:** pace at ≤4 requests/second, ≤8 concurrent open requests, ≤10 sub-queries per multiquery, with 429-aware backoff. No days-to-complete budget is forced by a monthly cap.

## 5. Terms: caching / storage / redistribution / attribution / covers

Two primary sources govern, and they are recorded here verbatim because they are not perfectly aligned.

### 5.1 Twitch Developer Services Agreement (umbrella legal agreement)

Source: `https://legal.twitch.com/legal/developer-agreement/` (fetched 2026-09-05), section II ("Program Materials"), verbatim:

> "Do not store copies of Twitch Content or Program Materials, unless you: (a) obtain prior written authorization from Twitch (through these terms or otherwise); (b) control the rights associated with such content; or (c) cache such information for only a twenty-four hour time period without further sharing it with third parties. **Re-syndication and re-distribution of Program Materials or data as available from a Twitch API is prohibited.**"

> "You must delete all Twitch Data collected upon termination of this Agreement, revocation, or reduction in scope of end user authorization, or upon Twitch's or the end user's request…"

### 5.2 IGDB API documentation FAQ (the operator's own written guidance)

Source: `https://api-docs.igdb.com/` › *Getting Started* / *License* / *Business related FAQ* (fetched 2026-09-05), verbatim:

- "The IGDB.com API is free for non-commercial usage under the terms of the Twitch Developer Service Agreement."
- "One of the principles behind IGDB.com is accessibility of data. We wish to share the data with anyone who wants to build cool video game oriented websites, apps and services."
- FAQ Q2: "What is the price of the API? The API is free for both non-commercial and commercial projects."
- FAQ Q3: "**Am I allowed to store/cache the data locally? Yes. In fact, we prefer if you store and serve the data to your end users.** You remain in control over your user experience, while alleviating pressure on the API itself."
- FAQ Q4: "We expect fair attribution, i.e. attribution that is visible to your users and located in a static location (e.g. not in a change log)."
- FAQ Q5: "**You are allowed to keep all data you retrieve from the API and we will not ask you to remove the data in case of partnership termination.**"
- Images section: "Images that are removed or replaced from IGDB.com exist for 30 days before they are removed. Keep that in mind when designing cache logic."

### 5.3 Reconciliation (the conclusion the ADR encodes)

- **Caching conclusion:** the DSA's blanket 24-hour cache limit is subject to its own carve-out (a) — "prior written authorization from Twitch (**through these terms or otherwise**)". IGDB's official published API documentation, from the Twitch/Amazon subsidiary that operates the API, is that written authorization "otherwise": it explicitly grants indefinite local storage and serving to end users (FAQ Q3) and post-termination retention (FAQ Q5). SavePoint stores IGDB structured metadata locally and serves it from its own database, and treats the FAQ as the operative permission of record.
- **Attribution / redistribution conclusion:** SavePoint shows **fair, visible, static attribution to IGDB.com** (sources page + footer) even though it is a non-commercial academic project, and does **not** re-syndicate or bulk-redistribute the dataset — no public data dump, no third-party sharing, no API of its own that re-serves IGDB rows in bulk. This satisfies both the DSA's redistribution prohibition and the FAQ's attribution expectation.
- **Hotlink-versus-mirror cover conclusion:** covers are **hotlinked** to `https://images.igdb.com/igdb/image/upload/t_{size}/{hash}.jpg` (where `{hash}` is `cover.image_id`), which IGDB documents as the intended mechanism. Covers are **not mirrored locally in Phase 01.1** — local mirroring of images leans hardest on the storage permission for "Twitch Content" and carries the documented 30-day image-removal reconciliation burden. A missing or failing cover falls back to the Phase 1 first-party placeholder (D-06 / D-07). Local mirroring is revisited only if hotlink reliability proves inadequate.

---

## Reproduction

```
# environment: IGDB_CLIENT_ID and IGDB_CLIENT_SECRET set (values never echoed)
# 1. token:   POST https://id.twitch.tv/oauth2/token?client_id=…&client_secret=…&grant_type=client_credentials
# 2. counts:  POST https://api.igdb.com/v4/games/count            (body: "" | "where game_type = 0;")
#             POST https://api.igdb.com/v4/{covers,genres,platforms}/count
# 3. fields:  POST https://api.igdb.com/v4/games  body: fields id,name,slug,genres.name,platforms.name,cover.image_id,cover.url,first_release_date,total_rating,url; where id = 1942;
# 4. limits:  12x POST /v4/games/count (observe 429s); POST /v4/multiquery with >10 sub-queries (observe HTTP 400 concurrency cap)
```

Counts drift over time as IGDB's dataset changes; the ISO-8601 UTC timestamps above fix this probe's point-in-time values. Plan 01.1-02 re-measures the eligible count immediately before import and targets ≥90% of that fresh measurement (and > 100,000 primary works).
