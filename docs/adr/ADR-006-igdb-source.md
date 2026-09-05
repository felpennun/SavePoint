# ADR-006: IGDB as the real-scale catalogue source, and cover delivery

- **Status:** Accepted
- **Date:** 2026-09-05
- **Decision author:** Felipe (`requests 2.34.2 aprobado` — explicit approval of the dependency and the source decision gate)
- **Drafting / evidence:** execution agent; automated verification (`scripts/verify-igdb-adr.ps1`, `scripts/verify-igdb-probe.ps1`, `scripts/check-dependencies.ps1`) and the human decision are kept separate.
- **Phase / Plan:** 01.1 / 01.1-01 Task 3 · **Requirement:** DATA-04 (also unblocks CAT-02, REC-10 catalogue work) · **GitHub issue:** #7
- **Supersedes for the real-scale catalogue:** the "no runtime provider, Wikidata-only" position of [ADR-003](ADR-003-data-sources.md) — see *Consequences › Relationship to ADR-003*.

## Context

Phase 1 shipped a 150-game curated Wikidata snapshot ([ADR-003](ADR-003-data-sources.md)). Phase 01.1 grows the catalogue to real product scale (D-01, D-05). DATA-04 requires the enrichment source to be selected through a **documented comparison of coverage, platforms, licence, attribution, quotas, stability, and cost**, and the author asked for that comparison to be recorded for the thesis.

The comparison below is grounded in a live, authenticated probe of the IGDB v4 API — [`docs/verification/igdb-api-probe.md`](../verification/igdb-api-probe.md), probe run **2026-09-05T14:56:27Z**. RAWG and scaled-Wikidata rows are from secondary sources and Phase 1's own direct experience, and are labelled as such.

## Candidates considered

Three candidates: **IGDB** (Twitch/Amazon), **RAWG** (rawg.io), and **scaled Wikidata** (extending the Phase 1 SPARQL pipeline).

## DATA-04 comparison

| Axis | IGDB (chosen) | RAWG | Scaled Wikidata |
|---|---|---|---|
| **Coverage** | 374,555 total game entries; **312,418** primary games (`game_type = 0`). 336,568 covers, 23 genres, 220 platforms. Measured live, 2026-09-05. | ~350,000–500,000 games claimed (secondary source, not probed). Broad, includes storefront metadata. | Sparse and uneven for games: no reliable genre/platform modelling, cover art only via per-file Wikimedia Commons entries. Phase 1 needed hand-curation to reach 150 usable rows. |
| **Platforms** | First-class `platforms` entity (220 rows), dot-expandable as `platforms.name`; confirmed live. | First-class platform metadata (secondary source). | Platform data present but inconsistent; requires bespoke sub-queries and normalisation (Phase 1 experience). |
| **Licence** | API "free for both non-commercial and commercial projects", governed by the **Twitch Developer Services Agreement**; code samples are "Program Materials". Verbatim sources in the probe evidence §5. | Free tier for non-commercial use under RAWG API ToS; commercial use requires a paid plan and a revenue-share/attribution arrangement (secondary source). | Structured data is **CC0** (public domain) — the cleanest licence of the three. Commons media is per-file (CC-BY / CC-BY-SA / PD), needing individual review — see ADR-003. |
| **Attribution** | IGDB expects "fair attribution … visible to your users and located in a static location". SavePoint adds visible static IGDB.com attribution (sources page + footer) despite being non-commercial. | Mandatory attribution **and a backlink to rawg.io** on every page using the data (secondary source) — heavier and more prescriptive than IGDB's. | CC0 structured data needs no attribution; Commons media requires per-file author + licence credit (ADR-003 model). |
| **Quotas** | **No monthly request quota.** Documented limit: **4 requests/second, 8 concurrent open requests**; `429` on breach; multiquery capped at 10 sub-queries (all observed live). No rate-limit headers returned. | **20,000 requests/month** on the free tier (secondary source) — a hard monthly ceiling that would constrain a multi-hundred-thousand-row import. | No quota, no auth (public SPARQL endpoint), but subject to endpoint timeouts and fair-use throttling on large queries. |
| **Stability** | Backed by Twitch/Amazon; stable v4 API since the 2020 Twitch migration; OAuth token lifetime ~57 days observed. Dataset mutates under long pulls → id-cursor pagination required (RESEARCH.md Pattern 1). | Independent operator (rawg.io); smaller organisation, higher discontinuation/pricing-change risk (secondary source). | Wikidata/Wikimedia is very stable institutionally, but the *game* data depends on volunteer editing — coverage and modelling change unpredictably and are not import-stable. |
| **Cost** | **€0.** Free for this use; new Python dependency is `requests==2.34.2` only. | €0 within 20k req/month; a full-catalogue import would likely exceed the free tier and require a paid plan. | €0. |

## Decision

1. **Adopt IGDB v4 as the real-scale catalogue source** (D-05). It is the only candidate that combines real coverage, first-class genre/platform/cover modelling, **no monthly quota**, zero cost, and an operator-published permission to store and serve the data — at the price of a heavier attribution obligation than CC0 Wikidata and a licence that is an agreement rather than a public-domain dedication.
2. **Eligible-category boundary (D-06):** the SavePoint catalogue imports IGDB **`game_type = 0` (main games) — 312,418 rows at probe time**. `game_type` 1–14 (DLC, expansion, bundle, standalone_expansion, mod, episode, season, remake, remaster, expanded_game, port, fork, pack, update) are non-primary and are **excluded** from the primary catalogue, consistent with the existing `RelatedContent` / `is_dlc` precedent in `apps/api/catalogue/models.py`. Plan 01.1-02 re-measures the eligible count immediately before import and must import ≥ 90% of that fresh measurement and **> 100,000 primary works**.
3. **Cover delivery / storage rule (D-06):** covers are **hotlinked**, not mirrored, in Phase 01.1. Build URLs as `https://images.igdb.com/igdb/image/upload/t_{size}/{hash}.jpg` where `{hash}` is `cover.image_id` (e.g. `t_cover_big`, `t_cover_small`, append `_2x` for retina). IGDB documents a 30-day retention window for removed/replaced images — acceptable for hotlinking, and the reason local mirroring is deferred (it would inherit that reconciliation burden and lean hardest on the storage permission for image "Twitch Content"). A missing or failing cover falls back to the **Phase 1 first-party placeholder** (D-06, and D-07 of `01-CONTEXT.md`). Local mirroring of covers is revisited only if hotlink reliability proves inadequate.
4. **Caching / redistribution rule:** SavePoint stores IGDB structured metadata (games, genres, platforms) in its own PostgreSQL database and serves it to its own end users. It does **not** re-syndicate or bulk-redistribute the dataset — no public data dump, no third-party data sharing, no API that re-serves IGDB rows in bulk. The operative written permission of record is the IGDB API documentation FAQ (Q3 "we prefer if you store and serve the data to your end users", Q5 "you are allowed to keep all data you retrieve"), which stands as the "prior written authorization … otherwise" contemplated by the Twitch Developer Services Agreement's storage carve-out. Verbatim sources: [`igdb-api-probe.md`](../verification/igdb-api-probe.md) §5.
5. **Attribution:** a visible, static "Data from IGDB.com" attribution is shown on the sources page and the site footer.
6. **Preserve the Phase 1 offline corpus:** the Wikidata snapshot, its manifests, `docs/verification/catalogue-freeze.md`, and the ADR-003 freeze are **retained unchanged**. The 150-game CC0 corpus and its per-asset Commons review stay valid, citable evidence; the IGDB import is additive and keyed on `SourceRecord(source="igdb", source_id=<igdb id>)` alongside the existing `source="wikidata"` rows. `CAT-06` / `OPS-03` still hold: no provider is called at request time — IGDB access is confined to the offline, resumable management command.
7. **HTTP client dependency:** add exactly **`requests==2.34.2`** (Apache-2.0, `requires-python >=3.10`, PyPI-verified — real `psf/requests` release uploaded 2026-05-14, not yanked) via `uv add`, pinned in `pyproject.toml` and `uv.lock`. Its approved-dependency row is added to `scripts/check-dependencies.ps1` and `docs/verification/dependency-legitimacy.md`. **Do not** add `django-allauth` or `dj-rest-auth` — the hand-rolled `accounts` app is extended instead (RESEARCH.md *Alternatives Considered*).

## Evidence and sources

- **Authenticated probe:** [`docs/verification/igdb-api-probe.md`](../verification/igdb-api-probe.md) — probe run 2026-09-05T14:56:27Z; counts, field-name confirmation, rate-limit behaviour, and verbatim terms quotations.
- **Primary terms sources:** `https://api-docs.igdb.com/` (Getting Started, License, Business FAQ, Images); `https://legal.twitch.com/legal/developer-agreement/` (Program Materials — storage/redistribution).
- **Dependency:** `https://pypi.org/project/requests/2.34.2/` — Apache-2.0, `requires-python >=3.10`, wheel + sdist uploaded 2026-05-14, `yanked: false`; source repo `github.com/psf/requests`.
- **Research:** [`.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md`](../../.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md) — assumptions A1 (no monthly quota) and A3 (field names) are now **confirmed** by the probe; A5 (catalogue size) is measured at 374,555 total / 312,418 primary.
- RAWG and scaled-Wikidata rows are secondary-source / Phase 1 direct experience, explicitly not independently probed this plan.

## Consequences

**Positive**
- Real-scale catalogue (100k+ primary works) becomes reachable at zero cost with no monthly ceiling.
- First-class genre and platform data unblocks CAT-02 filtering/sorting and REC-10's genre heuristic.
- Storage + serve permission is explicit in the operator's own documentation, recorded verbatim for thesis defensibility (DATA-08).

**Negative / limits**
- The licence is an **agreement** (Twitch DSA), not a public-domain dedication; it can change, and the FAQ-vs-DSA reconciliation in point 4 is a reasoned reading, not legal advice.
- Attribution is now an ongoing obligation on the UI.
- Import must respect 4 req/s + 8 concurrent and be resumable over a long run (RESEARCH.md Patterns 1–2).
- Hotlinked covers move image availability to a third-party CDN outside SavePoint's control; the 30-day removal window means some covers will 404 over time and fall back to the placeholder.
- One new runtime dependency (`requests`) plus its transitive tree (`certifi`, `charset-normalizer`, `idna`, `urllib3`).

**Relationship to ADR-003**
ADR-003's Wikidata freeze and its "no runtime provider" rule remain in force for the Phase 1 corpus and for request-time behaviour. ADR-006 narrows ADR-003's alternative-2 rejection of "RAWG/IGDB … credentials, quotas, terms and drift": those risks are now measured and mitigated (no quota, terms recorded, id-cursor import, offline-only access) rather than avoided, specifically for the real-scale catalogue Phase 01.1 requires.

## Reversibility

The IGDB corpus is keyed on `SourceRecord(source="igdb", …)` and can be dropped without touching the Wikidata rows. Switching sources later means a new fetch, a new freeze, and a new human decision. The `requests` pin is reversible via `uv remove`.

## Approval and review

**Accepted.** Any change to the source, the eligible-category boundary, the cover delivery rule, or the `requests` pin invalidates this decision and requires a new human decision gate and a re-run of the verification scripts.
