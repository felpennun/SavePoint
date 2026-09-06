# Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender - Pattern Map

**Mapped:** 2026-09-06
**Files analyzed:** 41 (nuevos + modificados)
**Analogs found:** 36 con análogo directo / 41

> Prosa en español (`CONVENTIONS.md` §1). Rutas, identificadores, nombres de símbolo y
> excerpts de código en inglés. Todos los análogos citados son ficheros **git-tracked**
> (verificado con `git ls-files`). No hay rutas de mirror (`.gsd/capabilities/...`) en este
> documento.

RESEARCH.md ya nombró los análogos in-repo con `[VERIFIED: path:lines]` en sus Patterns 1-7;
este documento los concreta con excerpts leídos verbatim esta sesión y asigna un análogo por
fichero a crear/modificar.

---

## File Classification

### Backend — `apps/api/catalogue/`

| Nuevo/Modificado | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `catalogue/models.py` (ADD `GameWork.in_corpus`, `corpus_version`, `summary`; NEW `CorpusRatingSnapshot`; NEW `CorpusVersion` metadata) | model | schema/transform | `catalogue/models.py` `GameWork`, `SourceRecord`, `IgdbImportRun` | exact |
| `catalogue/migrations/000X_governed_corpus.py` | migration | schema | `catalogue/migrations/0004_catalogue_filter_sort_fields.py`, `0005_igdbimportrun_pass_cursor.py` | exact |
| `catalogue/corpus.py` (NEW — `governed_works()` queryset + allowlist constants) | utility | request/transform | `catalogue/search.py` `_base_works()` + module-level constants | role-match |
| `catalogue/igdb.py` (EXTEND `GAME_FIELDS`) | config/client | request-response (outbound) | `catalogue/igdb.py` `GAME_FIELDS` (lines 36-39) | exact (self-edit) |
| `catalogue/rawg.py` (NEW, conditional) | service/client | request-response (outbound), batch | `catalogue/igdb.py` (`IgdbClient`, `redact`, pacing, id-cursor) | exact |
| `catalogue/management/commands/import_igdb_catalogue.py` (EXTEND: map new fields, create `GameAlias` in `_upsert`) | command | batch / file-I-O | `import_igdb_catalogue.py` itself (`_normalize`, `_upsert`, `_platform_for`) | exact (self-edit) |
| `catalogue/management/commands/backfill_game_aliases.py` (NEW) | command | batch | `import_igdb_catalogue.py` (batched `transaction.atomic` + advisory lock + evidence emit) | role-match |
| `catalogue/management/commands/govern_corpus.py` (NEW) | command | batch / transform | `import_igdb_catalogue.py` (`_catalogue_checksum`, `_build_evidence`, `_emit_evidence`) | role-match |
| `catalogue/management/commands/snapshot_corpus_ratings.py` (NEW) | command | batch | `import_igdb_catalogue.py` (`_upsert` `update_or_create` discipline, batched) | role-match |
| `catalogue/management/commands/enrich_rawg_ratings.py` (NEW, conditional) | command | batch / request-response | `import_igdb_catalogue.py` + `catalogue/rawg.py` | role-match |
| `catalogue/search.py` (EXTEND: `getlist`, genres AND / platforms OR, governed scoping) | utility | request-response / CRUD-read | `catalogue/search.py` `CatalogueQuery`, `parse_catalogue_query`, `_apply_filters` | exact (self-edit) |
| `catalogue/views.py` (EXTEND `GameListView`; ADD `NewReleasesView`, `OwnedGamesDlcView`) | controller | request-response | `catalogue/views.py` `GameListView`, `GameDetailView` | exact (self-edit) |
| `catalogue/serializers.py` (ADD `summary`, `rating`/`rating_count` breakdown, relabel) | serializer | transform | `catalogue/serializers.py` (`total_rating` on card + detail) | exact (self-edit) |
| `catalogue/tests/test_govern_corpus.py`, `test_rating_snapshot.py`, `test_alias_backfill.py`, `test_new_releases.py`, `test_owned_dlc.py` (NEW) | test | — | `catalogue/tests/test_igdb_import.py`, `test_search.py` | role-match |
| `catalogue/tests/test_search.py` (EXTEND multi-select) | test | — | `catalogue/tests/test_search.py` itself | exact (self-edit) |

### Backend — `apps/api/recommendations/`

| Nuevo/Modificado | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `recommendations/baselines.py` (NEW — `rank_random_v1(user, seed, limit)`, REC-01) | service | transform / request-time compute | `library/popularity.py` `rank_popularity_v1` + `recommendations/genre_heuristic.py` DTO | exact |
| `recommendations/content/features.py` (NEW — item feature vectors) | service | transform | `recommendations/genre_heuristic.py` (genre through-table walk, lines 154-165) | role-match |
| `recommendations/content/profile.py` (NEW — user profile vector) | service | transform | `recommendations/genre_heuristic.py` `_entry_weight`, `_STATUS_WEIGHTS` (lines 44-49, 94-95) | exact (reuse) |
| `recommendations/content/similarity.py` (NEW — cosine, stdlib) | utility | transform | RESEARCH Code Examples "Cosine (stdlib)" (no in-repo analog — stdlib `math.fsum`) | no analog |
| `recommendations/content/combine.py` (NEW — weighted_sum / multiplicative / two_stage + rating term D-13) | service | transform | `recommendations/genre_heuristic.py` (score `Case/When`, exact Python re-score, lines 183-232) | role-match |
| `recommendations/content/explain.py` (NEW — deterministic contribution table, D-16) | service | transform | `recommendations/genre_heuristic.py` `matched_genres` build (lines 213-243) | role-match |
| `recommendations/content/variants.py` (NEW — `ALGORITHM_REGISTRY` id → VariantSpec) | config | — | `recommendations/genre_heuristic.py` `ALGORITHM_ID` + `_LIMITATION` module constants | role-match |
| `recommendations/genre_heuristic.py` (EXTEND: no cambia — se conserva REC-10) | service | — | itself | n/a (unchanged) |
| `recommendations/views.py` (EXTEND: ADD `ContentRecsView`) | controller | request-response | `recommendations/views.py` `RecommendationsView` (allowlist-echo, `IsAuthenticated`) | exact (self-edit) |
| `recommendations/urls.py` (ADD route) | route | — | `recommendations/urls.py` | exact (self-edit) |
| `recommendations/tests/test_baselines.py`, `test_content.py` (NEW) | test | — | `recommendations/tests/test_genre_heuristic.py` | role-match |

### Backend — `apps/api/evaluation/` (NEW app; add to `INSTALLED_APPS`)

| Nuevo | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `evaluation/apps.py`, `__init__.py` | config | — | `recommendations/apps.py` | exact |
| `evaluation/protocol.py` (load + validate `protocol.json`; freeze/consumed checks) | service | file-I-O / transform | `accounts/.../bootstrap_demo_accounts.py` `parse_seed_contract` + `validate_seed_passwords` | role-match |
| `evaluation/synthetic.py` (archetype defs + seeded generator) | service | transform (seeded) | `accounts/.../bootstrap_demo_accounts.py` (`_bootstrap_identities`, advisory lock, all-or-nothing) | role-match |
| `evaluation/splits.py` (leave-one-out per user; train/val/test user split) | utility | transform (seeded) | `library/popularity.py` (single resolved queryset snapshot) — weak; mostly new | partial |
| `evaluation/metrics.py` (precision@k, recall@k, ndcg@k, map@k — hand-written) | utility | transform | RESEARCH Code Examples "nDCG@k" (no in-repo analog — hand-write + unit-test) | no analog |
| `evaluation/runner.py` (orchestrate variants over frozen split; artifact JSON) | service | batch / file-I-O | `import_igdb_catalogue.py` `_build_evidence` + `_emit_evidence` (aggregate JSON artifact) | role-match |
| `evaluation/management/commands/generate_synthetic_users.py` (NEW) | command | batch (seeded) | `accounts/.../bootstrap_demo_accounts.py` `Command` + `apply_seed_contract` | exact |
| `evaluation/management/commands/run_evaluation.py` (NEW) | command | batch / file-I-O | `import_igdb_catalogue.py` `Command.handle` (+ `--evidence-json`) | role-match |
| `evaluation/tests/test_protocol.py`, `test_synthetic.py`, `test_splits.py`, `test_metrics.py`, `test_runner.py` (NEW) | test | — | `recommendations/tests/test_genre_heuristic.py`, `catalogue/tests/test_igdb_import.py` | role-match |

### Frontend — `apps/web/`

| Nuevo/Modificado | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `lib/catalogue-filters.ts` (`genre`/`platform` → `string[]`, `getAll`, per-value chips) | utility | transform | `lib/catalogue-filters.ts` itself (`parseFilters`, `buildQuery`, `countActiveFilters`) | exact (self-edit) |
| `components/FacetMenu.tsx` (NEW) | component | request-response (GET form) | `components/FilterBar.tsx` (`<details>` + `<form method="get">` + `sp-field` + disabled degrade) | role-match |
| `components/FilterBar.tsx` (MOD: two `<select>` → two `<FacetMenu>`) | component | request-response | `components/FilterBar.tsx` itself | exact (self-edit) |
| `components/FilterChip.tsx` (MOD: one chip per value) | component | — | `components/FilterChip.tsx` itself | exact (self-edit) |
| `components/ScorePill.tsx` (MOD: relabel "Valoración", revised aria) | component | — | `components/ScorePill.tsx` itself | exact (self-edit) |
| `components/RatingBreakdownLine.tsx` (NEW) | component | — | inline plain `<p className="sp-muted">` pattern in `FilterBar.tsx` line 134 | partial |
| `components/Synopsis.tsx` (NEW — client, clamp + toggle) | component | — | `components/ThemeToggle.tsx` (`"use client"`, `useState`, `aria-pressed`/`aria-expanded` idiom) | role-match |
| `components/ContentRecommendationList.tsx` (NEW) | component | — | `components/RecommendationShelf.tsx` (`<section>` + `<h2>` + track + per-card evidence) | role-match |
| `components/WhyDisclosure.tsx` (NEW — `<details>` closed) | component | — | `components/FilterBar.tsx` `<details>` + UI-SPEC "disclosure único" (native `<details>/<summary>`) | role-match |
| `components/ContributionTable.tsx` (NEW — `<table>` key→value + decorative bar) | component | — | RESEARCH/UI-SPEC `.sp-kv` / `KeyValueTable` (no dedicated `.tsx` yet — new, follows `.sp-*` class idiom) | partial |
| `components/OwnedGamesDlcShelf.tsx` (NEW) | component | — | `components/RecommendationShelf.tsx` | role-match |
| `components/NewReleasesShelf.tsx` (NEW) | component | — | `components/RecommendationShelf.tsx` / `RecommendationStrip.tsx` | exact |
| `components/AppShell.tsx` (MOD: `hidden md:inline` on text spans) | component | — | `components/AppShell.tsx` itself | exact (self-edit) |
| `components/ThemeToggle.tsx` (MOD: wrap `<span>` in `hidden md:inline`) | component | — | `components/ThemeToggle.tsx` itself | exact (self-edit) |
| `components/AccountSwitcher.tsx` (MOD: wrap trigger text in `hidden md:inline`) | component | — | `components/AccountSwitcher.tsx` itself | exact (self-edit) |
| `app/[locale]/catalogue/page.tsx` (MOD: `first()` → `getAll`, mount `FacetMenu`) | route/page | request-response | `app/[locale]/catalogue/page.tsx` itself | exact (self-edit) |
| `app/[locale]/games/[id]/page.tsx` (MOD: Synopsis, RatingBreakdownLine, DLC shelf) | route/page | request-response | itself | exact (self-edit) |
| `app/[locale]/recommendations/page.tsx` (MOD: 3 labelled sections) | route/page | request-response | itself | exact (self-edit) |
| `app/[locale]/page.tsx` (MOD: mount `NewReleasesShelf`) | route/page | request-response | itself | exact (self-edit) |
| `i18n/en.ts`, `i18n/es.ts` (ADD new keys, EN/ES parity) | config | — | existing `i18n/*.ts` (parity enforced by `apps/web/tests/i18n.test.ts`) | exact (self-edit) |

---

## Pattern Assignments

### `recommendations/baselines.py` — `rank_random_v1` (service, transform) — REC-01

**Analog:** `apps/api/library/popularity.py` (DTO grammar + demo-account restriction) and
`apps/api/recommendations/genre_heuristic.py` (limit clamp, fingerprint, `insufficient_history`).

**DTO shape to mirror** (`library/popularity.py:86-96`):
```python
return {
    "algorithm_id": ALGORITHM_ID,               # e.g. "random-v1"
    "generated_at": cutoff.isoformat(),
    "input_snapshot_sha256": input_snapshot_sha256,
    "results": results,                          # [{work_id, slug, title, score}]
    "limitation": (
        "Uniform random draw from the governed corpus; comparison floor only."
    ),
}
```

**Seeded determinism + fingerprint** (adapt `popularity.py:62-69`):
```python
ranked_ids = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
input_snapshot_sha256 = hashlib.sha256(
    json.dumps(ranked_ids, sort_keys=False).encode("utf-8")
).hexdigest()
```
For `rank_random_v1` use `random.Random(seed).sample(governed_candidates_minus_library, k=limit)`;
hash `(seed, sorted(candidate_ids), ranked_ids)` so the draw is reproducible and visible.

**Candidate set:** `catalogue/corpus.py::governed_works(corpus_version)` minus every work with any
`LibraryEntry` for the user — the `seen_ids` idiom from `genre_heuristic.py:141-146`:
```python
entries = list(
    LibraryEntry.objects.filter(user=user, updated_at__lte=generated_at)
    .values("work_id", "current_status", "rating_half_steps")
)
seen_ids = {entry["work_id"] for entry in entries}
```

---

### `recommendations/content/profile.py` — user profile vector (service, transform) — D-12

**Analog:** `apps/api/recommendations/genre_heuristic.py`.

**Reuse `_entry_weight` verbatim** — do NOT invent a new weighting scheme (`genre_heuristic.py:44-49, 94-95`):
```python
_STATUS_WEIGHTS: dict[str, float] = {
    "completed": 3.0, "playing": 2.0, "pending": 1.0, "abandoned": 0.0,
}
_RATING_DIVISOR = 10

def _entry_weight(status: str | None, rating_half_steps: int | None) -> float:
    return _STATUS_WEIGHTS.get(status or "", 0.0) + (rating_half_steps or 0) / _RATING_DIVISOR
```
Import it: `from recommendations.genre_heuristic import _entry_weight` (or promote to a shared
`recommendations/_weights.py` if the private-name import is undesirable — planner decides).

**Profile = weighted mean of normalised item vectors** over the user's `LibraryEntry` rows,
same one-resolved-read discipline as `genre_heuristic.py:141-152`.

---

### `recommendations/content/combine.py` + `variants.py` — combination modes (service) — D-10/D-14

**Analog:** `apps/api/recommendations/genre_heuristic.py` (exact-rescore + tie-break) and its
module-constant `ALGORITHM_ID` / `_LIMITATION` idiom.

**Named-variant registry** (new, follows the `ALGORITHM_ID = "genre-taste-v1"` precedent at
`genre_heuristic.py:38`):
```python
# recommendations/content/variants.py
@dataclass(frozen=True)
class VariantSpec:
    algorithm_id: str
    feature_set_version: str
    combine_mode: str          # "weighted_sum" | "multiplicative" | "two_stage"
    params: dict
    version: str

ALGORITHM_REGISTRY: dict[str, VariantSpec] = {
    "content-cbf-weighted-v1": VariantSpec(...),
    "content-cbf-multiplicative-v1": VariantSpec(...),
    "content-cbf-twostage-v1": VariantSpec(...),
}
```
Security (V5, RESEARCH Security Domain): `algorithm_id` from the request → strict
`in ALGORITHM_REGISTRY` membership check, unknown → bounded 400. NEVER `getattr`/`importlib`
on the value.

**Exact Python re-score + deterministic tie-break** (copy the shape of `genre_heuristic.py:205-232`):
```python
scored.sort(key=lambda row: (-row[0], row[1]))   # score desc, canonical_slug asc
scored = scored[:limit]
```

**Full content DTO** = ADR-007 grammar + versioning (extends `genre_heuristic.py:245-254`):
```python
return {
    "algorithm_id": spec.algorithm_id,
    "generated_at": generated_at.isoformat(),
    "input_snapshot_sha256": _fingerprint(...),
    "feature_set_version": spec.feature_set_version,   # ADDED
    "corpus_version": corpus_version,                  # ADDED
    "snapshot_sha256": snapshot_sha256,                # ADDED
    "insufficient_history": False,
    "limitation": _LIMITATION,
    "results": results,   # each: work_id, slug, title, score, contributions[],
                          #       rating_term, rating_term_is_fallback
}
```

---

### `recommendations/content/explain.py` — deterministic explanation (service) — D-16/REC-08

**Analog:** `genre_heuristic.py:213-243` (`matched_genres` list of `{slug, name, weight}`,
sorted, rounded). Same idea: `contributions = [{genre, contribution_pct}]` where
`contribution_pct` is that genre dimension's share of the cosine numerator, sorted desc,
`round(..., 3)`. No generated prose — the UI fills a fixed i18n template with the top genres.

---

### `recommendations/views.py` — `ContentRecsView` (controller, request-response) — REC-03/09, V4

**Analog:** `apps/api/recommendations/views.py::RecommendationsView` — copy line for line.

```python
permission_classes = [IsAuthenticated]           # owner-scoped, no target-user param

_DTO_KEYS = ("algorithm_id", "generated_at", "input_snapshot_sha256",
            "feature_set_version", "corpus_version", "snapshot_sha256",
            "insufficient_history", "limitation", "results")
_ITEM_KEYS = ("work_id", "slug", "title", "score", "contributions",
             "rating_term", "rating_term_is_fallback")

def get(self, request):
    raw_limit = request.query_params.get("limit")
    # ...strict int parse, bounded 400 on failure (views.py:45-55)...
    algorithm_id = request.query_params.get("algorithm_id", "content-cbf-weighted-v1")
    if algorithm_id not in ALGORITHM_REGISTRY:
        return Response({"detail": "unknown algorithm_id"}, status=400)
    payload = rank_content_v1(request.user, algorithm_id, limit=limit)
    return Response({
        **{k: payload[k] for k in _DTO_KEYS},
        "results": [{k: it[k] for k in _ITEM_KEYS} for it in payload["results"]],
    })
```
The allowlist-echo projection (`views.py:58-65`) is mandatory — a future DTO widening must be a
deliberate edit here.

---

### `catalogue/igdb.py` + `import_igdb_catalogue.py` — field expansion + `GameAlias` creation

**Analog:** the files themselves.

**`GAME_FIELDS` change** (`catalogue/igdb.py:36-39`), per RESEARCH Code Examples:
```python
GAME_FIELDS = (
    "id,name,slug,url,first_release_date,"
    "total_rating,total_rating_count,rating,rating_count,"
    "summary,"
    "genres.id,genres.name,platforms.id,platforms.name,"
    "alternative_names.name,franchises.name,collections.name,"
    "involved_companies.company.name,involved_companies.developer,"
    "cover.image_id"
)
```

**Map new fields in `_normalize`** — mirror the existing `total_rating` guard (`import_igdb_catalogue.py:127-130`):
```python
total_rating = None
rating = row.get("total_rating")
if isinstance(rating, (int, float)):
    total_rating = round(float(rating), 4)
```
Add the same shape for `rating`, `rating_count`, `total_rating_count`, and
`summary = str(row.get("summary") or "").strip()`.

**Create `GameAlias` in `_upsert`** (currently absent — root cause of the search bug). The
`GameAlias` model constraint is `unique(work, locale, normalized_value)` with a GIN trigram
index (`catalogue/models.py:128-151`). Use `normalize_title` from `catalogue/normalization.py`.
Follow the "reconcile-then-set, drop stale" idiom the file already uses for releases
(`import_igdb_catalogue.py:312-322`):
```python
# build desired alias set: normalize_title(name) [locale en],
#   title_en if distinct, each alternative_names.name
GameAlias.objects.bulk_create(objs, ignore_conflicts=True, batch_size=5000)
# then delete this work's stale auto-aliases not in the new set
```

**Platform/genre reconciliation — copy `_platform_for` (`import_igdb_catalogue.py:191-223`)**:
match on `slug` first, then `name`, INSERT inside `transaction.atomic()` catching
`IntegrityError`. NEVER `get_or_create(name=...)`. The allowlist in `catalogue/corpus.py` must
resolve on **slug** (`slugify("PC (Microsoft Windows)") == "pc-microsoft-windows"`).

---

### `catalogue/management/commands/backfill_game_aliases.py` (NEW command, batch)

**Analog:** `import_igdb_catalogue.py` — batched `transaction.atomic()` + one
`pg_advisory_xact_lock` per batch (lines 61, 511-513), distinct lock key. `stealth_options`,
`requires_system_checks = []` idiom (lines 77-81). For every `GameWork` (idempotent via the
unique constraint): primary alias `(locale="en", value=original_title,
normalized_value=normalize_title(original_title))` + `title_en` if distinct + each
`alternative_names.name`. `GameAlias.objects.bulk_create(objs, ignore_conflicts=True,
batch_size=5000)`. After: `VACUUM ANALYZE catalogue_gamealias`.

---

### `catalogue/management/commands/govern_corpus.py` (NEW command, batch/transform) — DATA-03

**Analog:** `import_igdb_catalogue.py` — `_catalogue_checksum` (lines 341-353), `_build_evidence`
(355-418), `_emit_evidence` (420-428).

**Checksum shape to reuse** (`import_igdb_catalogue.py:341-353`), scoped to `in_corpus=True`:
```python
rows = sorted(
    SourceRecord.objects.filter(source="igdb", work__in_corpus=True)
        .values_list("source_id", "snapshot_sha256"),
    key=lambda pair: int(pair[0]),
)
digest = hashlib.sha256()
for source_id, record_hash in rows:
    digest.update(source_id.encode("utf-8")); digest.update(b"\0")
    digest.update(record_hash.encode("utf-8")); digest.update(b"\n")
```

**Sampled manifest** — reuse `_build_evidence`'s `step = max(1, len(ids) // 300)` /
`ids[::step][:300]` deterministic decimation (lines 374-395). Do NOT enumerate every governed
row.

**Exclusion logic (D-03):** `in_corpus = not(empty / <2-alnum / symbols-only name) and has ≥1
release on an allowlist platform and not is_dlc and genres.exists() and first_release_date is
not None`. Emit an exclusion-reason histogram (how many works failed each clause). Print any
allowlist slug that resolves to zero `Platform` rows (RESEARCH Pattern 1 reconciliation caveat).

**`--evidence-json` flag + `_emit_evidence`** idiom verbatim (lines 94-98, 420-428): `'-'` →
stdout, else write file + `mkdir parents`.

---

### `catalogue/models.py` — additive migration + `CorpusRatingSnapshot` (model, schema) — D-04/D-08

**Analog:** `GameWork` denormalised-scalar fields (`models.py:44-61`), `SourceRecord` (187-210),
`IgdbImportRun` unique-constraint + check-constraint idiom (255-266).

```python
# GameWork ADD:
in_corpus = models.BooleanField(default=False)
corpus_version = models.CharField(max_length=32, blank=True)
summary = models.TextField(blank=True)
# index in Meta.indexes, mirroring catalogue_work_release_idx style:
models.Index(fields=["in_corpus", "first_release_date"], name="catalogue_work_corpus_idx")

class CorpusRatingSnapshot(models.Model):        # NEW — insert-only per corpus_version
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey("catalogue.GameWork", on_delete=models.CASCADE,
                             related_name="rating_snapshots")
    corpus_version = models.CharField(max_length=32)
    source = models.CharField(max_length=16)     # "igdb" | "rawg"
    rating = models.FloatField(null=True)
    rating_count = models.PositiveIntegerField(default=0)
    retrieved_at = models.DateTimeField()
    class Meta:
        constraints = [models.UniqueConstraint(
            fields=("work", "corpus_version", "source"),
            name="catalogue_unique_rating_snapshot")]
```
Migration file itself carries **no data migration** — `govern_corpus` does the backfill (D-04b).
Analog: `0004_catalogue_filter_sort_fields.py`, `0005_igdbimportrun_pass_cursor.py`.

---

### `catalogue/search.py` — multi-select (utility, request-response) — CAT-02

**Analog:** the file itself. RESEARCH already gives the target diff (Pattern 3).

**`CatalogueQuery`:** `genre: str | None` → `genres: tuple[str, ...] = ()`; `platform` →
`platforms`. In `parse_catalogue_query` (currently `search.py:142-143`):
```python
genres = tuple(dict.fromkeys(s.strip() for s in params.getlist("genre") if s.strip()))
platforms = tuple(dict.fromkeys(s.strip() for s in params.getlist("platform") if s.strip()))
```
(DRF `request.query_params.getlist`; Django `QueryDict.getlist`.) Cap repeated params at ≤20
(V5 DoS).

**`_apply_filters` (currently `search.py:161-182`):** platforms OR = one
`releases__platform__slug__in=[...]`; genres AND = chained `qs.filter(genres__slug=g)` per genre;
keep the `joined` flag → `.distinct()` once (Pitfall 3 — each chained genre filter adds a join).
Unknown slug still silently dropped.

**Governed scoping:** `_base_works()` (`search.py:156-158`) becomes
`GameWork.objects.filter(is_dlc=False, in_corpus=True)` — move to `catalogue/corpus.py::governed_works()`.
`_facets` (233-261) needs no structural change (already `Count(distinct=True)`).

**`SORT_ORDERS` (search.py:48-54)** unchanged; `rating_desc` still on `total_rating` (live number).

---

### `catalogue/views.py` — `NewReleasesView`, `OwnedGamesDlcView` (controller) — D-24, D-15

**Analog:** `GameListView` (`views.py:29-63`) — `ScopedRateThrottle`, `try/except
FilterValidationError → 400`, serializer projection. `GameDetailView` (66-81) for the
`prefetch_related` + generic-404 idiom.

- `NewReleasesView`: `governed_works().filter(first_release_date__gte=<today-6mo>).order_by(
  F("first_release_date").desc(nulls_last=True), "canonical_slug")[:20]`, serialize with
  `GameCardSerializer`. Empty → `[]` (frontend hides the shelf).
- `OwnedGamesDlcView`: `IsAuthenticated`; `RelatedContent.objects.filter(
  parent_work__in=<user library work ids>, relation__in=["dlc","expansion"])` →
  `child_work`. Owner-scoped, no target-user param (V4). DLC stays out of `governed_works()`
  but is queryable here.

---

### `evaluation/management/commands/generate_synthetic_users.py` (command, seeded batch) — EVAL-09

**Analog:** `apps/api/accounts/management/commands/bootstrap_demo_accounts.py` — copy the
structure: `parse_*` (pure validation, no DB) → `validate_*` → `apply_*` inside
`transaction.atomic()` + `pg_advisory_xact_lock` (distinct key; existing keys 725_01_15 /
725_01_16 / 725_0101_02 are taken). All-or-nothing, redacted output (counts + anchor UUIDs
only).

**Persist synthetic users as `DemoAccountIdentity`** with a **distinct marker** (NOT
`SIMULATED_ACCOUNT_MARKER`) so `rank_popularity_v1` can exclude them (Pitfall 5). Analog for the
anchor-UUID derivation (`accounts/models.py:29-32`):
```python
def demo_identity_anchor_id(seed_key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_ACCOUNT_NAMESPACE, seed_key)
```
Use `seed_key = f"synthetic-{archetype}-{n}"`. Seeded draws via `random.Random(seed)` /
per-archetype independent seeds. ~8 archetypes × ~25 + explicit cold-start cohort (1-3 games).

**`rank_popularity_v1` change:** `library/popularity.py:44-49` currently includes any
`user__demo_identity__isnull=False` — add `.exclude(user__demo_identity__marker="synthetic-eval-user")`
(or an `is_evaluation_fixture` flag). Decide before generating.

---

### `evaluation/protocol.py` + `run_evaluation.py` — frozen protocol (service/command) — EVAL-01/02/03

**Analog:** `bootstrap_demo_accounts.py::parse_seed_contract` (fail-closed structural validation,
`SeedContractError(CommandError)` subclass) for the `protocol.json` loader; `import_igdb_catalogue.py`
`_build_evidence` + `_emit_evidence` for the per-run artifact JSON.

`protocol.py` refuses to run if `len(grid) > 24` (D-21) or if the `test` split was already
consumed (a run marker). `run_evaluation.py` `handle()` mirrors `import_igdb_catalogue.py::handle`
shape: resolve `--corpus-version` explicitly, refuse if snapshot coverage over the governed set
< 100% (Pitfall 4), write artifact JSON via the `_emit_evidence` idiom.

---

### `evaluation/metrics.py` — ranking metrics (utility) — D-22 — NO ANALOG

Hand-write `precision_at_k`, `recall_at_k`, `dcg_at_k` / `ndcg_at_k`, `average_precision_at_k` /
`map_at_k`; unit-test against known-answer fixtures. RESEARCH Code Example:
```python
def ndcg_at_k(ranked_ids, relevant, k):
    dcg = sum(1.0/math.log2(i+2) for i, wid in enumerate(ranked_ids[:k]) if wid in relevant)
    ideal = sum(1.0/math.log2(i+2) for i in range(min(len(relevant), k)))
    return dcg/ideal if ideal else 0.0
```
STACK: "implement project metrics explicitly" — do not pull in scikit-learn.

---

### Frontend: `lib/catalogue-filters.ts` (utility, transform) — CAT-02

**Analog:** the file itself.

- `CatalogueFilters.genre` / `.platform`: `string?` → `string[]` (currently
  `catalogue-filters.ts:42-50`).
- `parseFilters` (55-83): `sp.genre?.trim()` → read all values. Because Next.js
  `searchParams` gives `string | string[]`, the page passes `URLSearchParams`/`getAll`; parse
  helper normalises, de-dupes (`[...new Set(...)]`), drops empties. Unknown slug passes through
  (server drops it).
- `countActiveFilters` (87-96): `if (f.genre) n += 1` → `n += f.genre.length` (each value counts).
- `buildQuery` (100-112): `params.set("genre", ...)` → `for (const g of f.genre)
  params.append("genre", g)`. `removeHref` for a chip = current query minus that one value.

---

### Frontend: `components/FacetMenu.tsx` (NEW, server component) — UI-SPEC P1 / E1

**Analog:** `components/FilterBar.tsx` — server component, `<details>` + `<form method="get">`,
`sp-field` rows, `disabled` degrade when an option list is empty (`FilterBar.tsx:49-50, 67,
133-137`). No client state, no auto-submit.

```tsx
<details className="sp-facet">
  <summary>{label} · {selectedCountLabel} <ChevronSvg/></summary>
  <div className="sp-surface">           {/* --shadow-overlay when floating (≥md) */}
    <p className="sp-muted">{semanticsText}</p>
    <ul>{options.map(o => (
      <li key={o.value}><label>
        <input type="checkbox" name={name} value={o.value}
               defaultChecked={selected.includes(o.value)} />
        {o.label}
      </label></li>
    ))}</ul>
    <a href={hrefWithoutThisFacet} className="sp-link">{clearLabel}</a>
  </div>
</details>
```
Repeated `name` → browser submits `?genre=a&genre=b`. Degrades to full list without JS.

---

### Frontend: shelves — `NewReleasesShelf`, `OwnedGamesDlcShelf`, `ContentRecommendationList`

**Analog:** `components/RecommendationShelf.tsx` — `<section className="sp-shelf"
aria-label={heading}>` + `<h2 className="sp-h2">` + `<p className="sp-muted">` explainer +
`<ul className="sp-shelf-track">` of `<GameCard coverVariant="shelf" evidence={...}>`
(`RecommendationShelf.tsx:26-56`). `GameCard` shelf variant = 120×160 cover
(`GameCard.tsx:41`). For a flat `<ol>` (content list positions) see `RecommendationStrip.tsx:36-43`.
Empty → `return null` (`RecommendationStrip.tsx:30`) — shelf disappears entirely (E3/E8 backstop).

---

### Frontend: `ScorePill.tsx` (MOD) — P2

**Analog:** itself (`ScorePill.tsx`). Keep tier ramp (`value < 40 ? "weak" : value < 75 ?
"fair" : "strong"`, line 25), `role="img"`, `rating == null → return null` (line 23). Change:
visible label uses `card.score.label` ("Valoración"/"Rating"), drop the `labelPrefix="IGDB"`
default; `ariaLabelTemplate` = revised `card.score.aria` ("Valoración {n} de 100"). Never
`--color-accent` (unchanged).

---

### Frontend: `Synopsis.tsx` (NEW, client) — P3 / E5

**Analog:** `components/ThemeToggle.tsx` — `"use client"`, `useState`, `useEffect` for
post-mount refinement, `aria-pressed`/`aria-label` idiom (`ThemeToggle.tsx:1-3, 25-32, 46-53`).
`Synopsis` uses `aria-expanded` + a measured `scrollHeight > clientHeight` check to decide
whether to show the toggle; `-webkit-line-clamp: 6`; no-JS fallback = full text + CSS clamp +
`<details>` backstop; `text` empty → whole `<section>` not rendered.

---

## Shared Patterns

### Recommendation/algorithm DTO grammar (ADR-007)
**Source:** `apps/api/recommendations/genre_heuristic.py:245-254`, `apps/api/library/popularity.py:86-96`
**Apply to:** `recommendations/baselines.py`, `recommendations/content/*`, every `run_evaluation` artifact
Every ranking result carries `algorithm_id` + `generated_at` + `input_snapshot_sha256` +
explicit `limitation` string + deterministic `canonical_slug` (or UUID) tie-break. Content
variants ADD `feature_set_version`, `corpus_version`, `snapshot_sha256`; per-item ADD
`contributions`, `rating_term`, `rating_term_is_fallback`. Every artifact/DTO also carries a
`simulation: true` / limitation string (EVAL-10).

### Allowlist-echo response projection (V4 information disclosure)
**Source:** `apps/api/recommendations/views.py:19-65`
**Apply to:** `ContentRecsView`, `NewReleasesView`, `OwnedGamesDlcView`
`_DTO_KEYS` / `_ITEM_KEYS` tuples projected verbatim; `IsAuthenticated` + `request.user`-only,
no target-user param; `algorithm_id`/`limit` strictly validated → bounded 400.

### Anti-contamination account restriction
**Source:** `apps/api/library/popularity.py:44-49`
```python
LibraryEntry.objects.filter(
    Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False),
    updated_at__lte=cutoff,
)
```
**Apply to:** the D-09 live blended `display_rating` (external + SavePoint users, product-only,
account-restricted); and its inverse — `rank_popularity_v1` must **exclude** the synthetic
eval-user marker (Pitfall 5). The research snapshot (`CorpusRatingSnapshot`) uses **none** of
this — external-only.

### Offline management command skeleton
**Source:** `apps/api/catalogue/management/commands/import_igdb_catalogue.py` (`stealth_options`,
`requires_system_checks = []`, per-batch `transaction.atomic()` + `pg_advisory_xact_lock(KEY)`,
`--evidence-json` + `_emit_evidence`, redacted error summary, fail-closed `except → status=FAILED`);
`apps/api/accounts/management/commands/bootstrap_demo_accounts.py` (parse→validate→apply,
all-or-nothing, redacted counts-only output).
**Apply to:** `backfill_game_aliases`, `govern_corpus`, `snapshot_corpus_ratings`,
`enrich_rawg_ratings`, `generate_synthetic_users`, `run_evaluation`. Each needs a **distinct**
advisory-lock key.

### Non-enumerative freeze evidence
**Source:** `import_igdb_catalogue.py::_catalogue_checksum` (341-353), `_build_evidence`
(355-418: sorted checksum + genre/platform/year aggregates + `step = max(1, len(ids)//300)`
sampled manifest ≤300 rows)
**Apply to:** `govern_corpus` (`corpus-governance-freeze.md` + JSON), the updated
`igdb-catalogue-freeze.md` (add rating-coverage row). Never a per-row table.

### Provider client (redaction + pacing + id-cursor)
**Source:** `apps/api/catalogue/igdb.py` (`redact`, `_SECRET_PATTERNS`, `_scrub`, `_throttle` /
`_backoff`, `_post` 401/429/5xx handling, `iter_pages` id-cursor, `raise ... from None`)
**Apply to:** `catalogue/rawg.py` if RAWG enters scope — copy line for line, fixed host
`api.rawg.io`, `RAWG_API_KEY` env-only, plus RAWG's 20k/mo budget arithmetic and a persistent
footer backlink (Pitfall 2).

### Platform/genre reconciliation on slug (never `get_or_create(name=)`)
**Source:** `import_igdb_catalogue.py::_platform_for` (191-223), `_genre_for` (225-238)
**Apply to:** `catalogue/corpus.py` allowlist resolution, `snapshot_corpus_ratings`,
`enrich_rawg_ratings`, any new command touching `Platform`/`Genre`.

### Idempotent upsert on external id
**Source:** `import_igdb_catalogue.py:279-289` — `SourceRecord.objects.update_or_create(
source=..., source_id=..., defaults={...})`
**Apply to:** RAWG rows (`source="rawg"`), snapshot writes (insert-only via the unique
constraint), re-import convergence.

### Frontend GET-form / URL-shareable filter idiom
**Source:** `components/FilterBar.tsx` (`<form method="get">`, `defaultValue`, `disabled` degrade),
`lib/catalogue-filters.ts` (`parseFilters`/`buildQuery`/`countActiveFilters`)
**Apply to:** `FacetMenu`, `FilterChip` per-value, `catalogue/page.tsx`. No client state.

### `<details>/<summary>` single disclosure pattern
**Source:** `components/FilterBar.tsx` `<details className="sp-filterbar sp-surface">`; UI-SPEC
"Patrón de disclosure único" (native `<details>`, `::-webkit-details-marker{display:none}`,
inline chevron SVG, 44px, no focus-trap for filters)
**Apply to:** `FacetMenu`, `WhyDisclosure`, `Synopsis` no-JS fallback.

### i18n EN/ES parity
**Source:** `apps/web/i18n/{en,es}.ts` + `apps/web/tests/i18n.test.ts`
**Apply to:** every new key in UI-SPEC "Copywriting Contract" — add to both files in the same
commit.

### Backend test idiom
**Source:** `apps/api/recommendations/tests/test_genre_heuristic.py` (pytest fixtures `user_a`,
`genres`, `_work`/`_own` helpers, `APIClient`), `apps/api/catalogue/tests/test_igdb_import.py`
(fake client injection via `call_command(..., client=fake)`)
**Apply to:** all Wave-0 test files listed in the classification tables.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `recommendations/content/similarity.py` | utility | transform | No cosine/vector-math code exists in-repo; pure stdlib `math.fsum` per RESEARCH Code Example. |
| `evaluation/metrics.py` | utility | transform | No ranking-metric code exists; STACK mandates hand-written + unit-tested P@K/R@K/nDCG@K/MAP. |
| `evaluation/splits.py` | utility | transform | Leave-one-out / train-val-test user partitioning has no in-repo precedent (only the single-resolved-queryset snapshot idea from `popularity.py`). |
| `docs/methodology/protocol.json` | config | file | New machine-readable freeze artifact; `evaluation-protocol.md` prose follows ADR-006/007 doc pattern but the JSON schema is new. |
| `components/ContributionTable.tsx` | component | — | No `KeyValueTable` component file exists yet; follows the `.sp-kv` CSS-class idiom and semantic `<table><th scope="row">` from the Accessibility Contract. |
| `components/RatingBreakdownLine.tsx` | component | — | Trivial `<p className="sp-muted">` with 3-way i18n key selection; nearest is the inline muted `<p>` in `FilterBar.tsx:134`. |

---

## Metadata

**Analog search scope:** `apps/api/{catalogue,recommendations,library,accounts}/` (models,
commands, search, views, serializers, tests), `apps/web/components/`, `apps/web/lib/`.
**Files scanned (read verbatim this session):** `genre_heuristic.py`, `popularity.py`,
`recommendations/views.py`, `catalogue/search.py`, `catalogue/igdb.py`,
`import_igdb_catalogue.py`, `catalogue/models.py`, `catalogue/views.py`, `accounts/models.py`,
`bootstrap_demo_accounts.py`, `lib/catalogue-filters.ts`, `FilterBar.tsx`, `ScorePill.tsx`,
`RecommendationShelf.tsx`, `RecommendationStrip.tsx`, `FilterChip.tsx`, `ThemeToggle.tsx`,
`GameCard.tsx`, `tests/test_genre_heuristic.py`.
**Tracked-source gate:** every analog path confirmed via `git ls-files`. No mirror
(`.gsd/capabilities/**`) paths emitted.
**Pattern extraction date:** 2026-09-06
