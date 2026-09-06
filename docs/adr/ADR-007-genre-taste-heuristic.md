# ADR-007: A deterministic genre-taste heuristic for the recommendations page

- **Status:** Accepted
- **Date:** 2026-09-06
- **Decision author:** Felipe (author-requested recommendations page, D-04 / REC-10; heuristic-over-model boundary set in `01.1-CONTEXT.md` D-09 and `01.1-RESEARCH.md`)
- **Drafting / evidence:** execution agent; the ranking rules below are enforced by `apps/api/recommendations/tests/test_genre_heuristic.py` (21 tests, run under `docker compose -f infra/compose.yaml run --rm api pytest`).
- **Phase / Plan:** 01.1 / 01.1-05 · **Requirement:** REC-10 · **GitHub issue:** #13
- **Sibling baseline:** [`apps/api/library/popularity.py`](../../apps/api/library/popularity.py) (`rank_popularity_v1`, REC-02) — the non-personalized aggregate this page must be visibly distinct from.
- **Superseded by (future):** Phase 6 content-based recommender (REC-03, `ROADMAP.md`) — see *Boundary*.

## Context

`REC-10` asks for "a dedicated recommendations page [that] exposes genre-oriented suggestions reflecting the signed-in user's own recorded tastes, distinct from the public popularity baseline." The author prioritised this page as a **product** deliverable for Phase 01.1 (D-04).

The rigorous recommender work — a documented comparison of content-based, collaborative, and hybrid approaches with versioned artifacts, explanations, and cold-start handling — is **Phase 6 (`REC-03`)**, and sits behind the Phase 2 comparative-evaluation freeze. Building anything resembling that here would duplicate future work and blur the two systems' thesis narrative. `01.1-RESEARCH.md` ("Don't Hand-Roll" table) is explicit: the Phase 01.1 page should be *"a stateless, request-time aggregation over `LibraryEntry` rows … mirroring `library/popularity.py`'s shape"*, **not** a trained model or a persisted feature store.

The existing `rank_popularity_v1` already establishes the house pattern for a defensible, non-ML ranking: a single resolved queryset, an explicit weight table, a deterministic tie-break, and a DTO that always declares `algorithm_id` + `generated_at` + `input_snapshot_sha256` + an explicit `limitation` string so it can never be mistaken for more than it is.

## Decision

Ship **`rank_genre_taste_v1(user, limit)`** in a new `apps/api/recommendations/` app: a stateless, request-time, deterministic genre-frequency heuristic scoped strictly to one user, exposed at `GET /api/recommendations/genre-taste/` behind `IsAuthenticated`. `ALGORITHM_ID = "genre-taste-v1"`.

### 1. Taste vector — weights

Each of the user's own `LibraryEntry` rows contributes an **activity weight** to *every* `Genre` attached to that entry's `GameWork`:

```
activity_weight(entry) = STATUS_WEIGHT[entry.current_status] + (entry.rating_half_steps or 0) / 10

STATUS_WEIGHT = { completed: 3.0, playing: 2.0, pending: 1.0, abandoned: 0.0, <unset>: 0.0 }
rating contribution  = rating_half_steps / 10   ->  0.1 .. 1.0   (null rating = 0.0)

taste_weight[genre] = Σ  activity_weight(entry)   for every entry whose work carries `genre`
```

The status table is a deliberate copy of `library/popularity.py`'s `_STATUS_WEIGHTS`, and the rating term is the same `rating_half_steps / 10` the popularity baseline uses — the personal heuristic and the public baseline speak the same "how much does this interaction count" language. `abandoned` and status-less entries contribute nothing: a bounced-off or untracked title is not evidence of taste.

### 2. Candidate ranking

Rank catalogue `GameWork` rows by summed genre overlap with the taste vector:

- **Exclude** every work the user already has *any* `LibraryEntry` for (status set or not).
- **Exclude** `is_dlc = True`.
- **Require** at least one genre in common with the taste vector (`taste_weight > 0`).
- `score(work) = Σ taste_weight[g]` for `g` in `work.genres ∩ taste_genres`.
- **Tie-break:** `canonical_slug` ascending. Identical inputs therefore produce an identical ordering.
  - The database orders on `Sum(CASE …)` in IEEE-754 `double precision`, but rating contributions are multiples of `0.1` (not exactly representable), so two works with the same *rational* score can carry different float sums and land either side of a naive `LIMIT`. The service therefore over-fetches a fixed multiple of `limit` (`_CANDIDATE_OVERFETCH = 4`, so at most `50 × 4 = 200` candidate rows — still bounded per threat T-01.1-11), then performs the **authoritative** exact-arithmetic re-score and `canonical_slug` tie-break in Python before truncating to `limit`. The DB ordering is only a candidate pre-filter; the documented cut-line semantics are decided in Python (repo-review 2026-09-06, finding L-03).
- Each result item carries its **genre-overlap explanation evidence**: `matched_genres = [{slug, name, weight}, …]` sorted by weight desc then slug, plus `work_id`, `slug`, `title`, `score`.

### 3. Bounded query (threat T-01.1-11)

The dev database holds 312,483 works / 23 genres, so a naive genre-overlap scan is a DoS surface. The ranking query is driven by the **`GameWork.genres` M2M through table**, filtered by `genre_id__in=<taste genres>` (the through table's auto-created `genre_id` index), grouped by work, aggregated with a `CASE`-sum of the per-genre weights, ordered, and **`LIMIT`-capped in SQL** at `limit × _CANDIDATE_OVERFETCH` (≤ 200; see the tie-break note above). Postgres never scans the full catalogue and the working set is never larger than that bounded candidate pool. No new index migration is required — the auto `genre_id` index on the through table plus the SQL `LIMIT` bound the scan; the unique `canonical_slug` index serves the tie-break sort.

### 4. `limit` bound

`limit` is clamped to **`[1, 50]`, default `20`**. The endpoint rejects a non-integer `limit` with `400`; an out-of-range integer is clamped (not rejected) to that bound. The service clamps defensively too, so a direct caller cannot pass an unbounded value.

### 5. Reproducibility — `input_snapshot_sha256`

The DTO carries a SHA-256 over a canonical JSON of **(the sorted taste vector) + (the ordered `(slug, score)` result list)**. Two calls that hash the same are provably the same ranking over the same taste snapshot; any change to the user's activity or to the produced order is always visible as a hash change. `generated_at` is a snapshot cutoff — only activity with `updated_at <= generated_at` feeds the taste vector — mirroring `rank_popularity_v1`'s `cutoff` argument, so a ranking can be recomputed identically after the fact.

### 6. Insufficient history — never a fall-back

When the user has no genre-bearing rated/status-tracked activity, the result is an **explicit distinct shape**: `insufficient_history: True`, `results: []`, and a `limitation` string stating that the page must show an empty/onboarding state. It **never** falls back to `rank_popularity_v1` or any aggregate — D-09 requires the page to reflect the signed-in user's *own* activity, so a public list dressed up as "your recommendations" would be a correctness bug.

### 7. Security (threat T-01.1-10)

`RecommendationsView` is `IsAuthenticated` and calls the service with `request.user` only. It accepts no target-user parameter. The response is re-projected through an explicit key allowlist (`algorithm_id`, `generated_at`, `input_snapshot_sha256`, `insufficient_history`, `limitation`, `results`; items: `work_id`, `slug`, `title`, `score`, `matched_genres`) so a future change to the service DTO cannot silently widen the wire contract. Anonymous requests get `403` with no taste data in the body.

## Boundary — this is a product feature, not the thesis's algorithmic contribution

`genre-taste-v1` is **deliberately simpler** than Phase 6's recommender and is not part of the Phase 2 comparative evaluation:

- It is a **frequency count over one table**, not a learned model. There is no training step, no embedding, no similarity matrix, no persisted feature store, no artifact to version beyond the code itself.
- It has **no cold-start strategy** beyond "say so" (§6). Phase 6 owns cold-start.
- It does **not** claim predictive quality and must not be benchmarked against, or reported alongside, the Phase 6 content-based / collaborative / hybrid comparison. The `limitation` string in every response says this in words so the frontend and any later reader cannot conflate the two.
- Its role in the thesis is to make the Phase 01.1 product read like a real cataloguing site (D-01, D-04) and to give Phase 6 a concrete, already-wired page and endpoint contract to replace.

## Consequences

**Positive**
- `REC-10` ships now as a real, personalised, explainable page without pre-empting Phase 6.
- Deterministic + fingerprinted: reproducible for the thesis write-up and cheap to test (21 unit/integration tests, no fixtures beyond a handful of rows).
- Same DTO grammar as `rank_popularity_v1`, so the two ranking endpoints are visibly siblings with an explicit distinction, satisfying D-09.
- Bounded, index-driven query — safe against the 312k-row catalogue (T-01.1-11); owner-scoped (T-01.1-10).

**Negative / limits**
- Genre frequency is a coarse taste signal: a user with one completed RPG gets an all-RPG page. This is acceptable for a product shelf and is exactly the kind of limitation Phase 6 exists to address.
- No diversity/novelty control, no recency decay beyond the `generated_at` cutoff, no per-genre normalisation (a work in many taste genres always outranks a work in one). Documented, not fixed.
- Depends on catalogue genre coverage from the IGDB import (ADR-006). Works with no genres are unrankable and simply never appear.
- A second ranking endpoint with its own DTO to keep in step with `popularity.py` if the shared contract changes.

## Reversibility

Self-contained: the `recommendations` app has no models and no migrations. Deleting the app directory, its `INSTALLED_APPS` line, and its `config/urls.py` include removes the feature with no schema impact. Phase 6 is expected to replace `rank_genre_taste_v1`'s internals (or swap the view's service call) while keeping the `GET /api/recommendations/genre-taste/` URL and the DTO shape.

## Approval and review

**Accepted.** Any change to the weight table, the exclusion rules, the `[1, 50]` limit bound, the tie-break, or the `input_snapshot_sha256` construction supersedes this decision and requires a new ADR entry and a re-run of `test_genre_heuristic.py`.
