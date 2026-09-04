# Pitfalls Research

**Domain:** Video-game catalogue/inventory and academic recommender-system comparison platform
**Researched:** 2026-09-04
**Confidence:** MEDIUM-HIGH (official primary sources for legal/API/accessibility/tool behavior; peer-reviewed literature for evaluation threats; project-specific phase advice is reasoned synthesis)

## Critical Pitfalls

### Pitfall 1: Treating accessible metadata as licensed research data

**What goes wrong:**
The project downloads a convenient game catalogue, images, descriptions, or user ratings, then redistributes a snapshot or publishes derived artifacts without proving the rights to do so. Citation alone is mistaken for permission. In the EU, both copyright in an original database's selection/arrangement and a separate sui generis database right may apply; individual assets can have their own rights. The thesis and repository then become legally indefensible or the dataset must be replaced late.

**Why it happens:**
Metadata looks factual and APIs look public. Dataset pages, API terms, asset licences, and database rights are conflated into one vague “source”. Academic use is assumed to create a blanket exemption.

**How to avoid:**
Create a source register before ingestion. For every field/asset record source URL, owner, exact licence/terms version and retrieval date, permitted uses, attribution, redistribution/caching status, and transformation. Keep the immutable research snapshot separate from live enrichment. Publish only artifacts the licence permits; otherwise publish a reproducible acquisition script plus checksums and a small lawful fixture. Require a documented rights decision before selecting the fixed dataset. This is project governance, not legal advice; ambiguous cases need university/legal review.

**Warning signs:**
“Free API” is the only licence note; no saved terms/version; images and text inherit the dataset's licence without proof; provenance is stored only at dataset level; the repository contains a large data dump with no redistribution statement.

**Phase to address:**
Phase 1 — Data governance and dataset selection; re-check at deployment/publication.

---

### Pitfall 2: Letting the live API contaminate the fixed experimental corpus

**What goes wrong:**
Current API values silently alter item features, candidate sets, popularity, or ground truth between runs. Algorithm scores can no longer be reproduced, and missing/changed remote records affect models unequally.

**Why it happens:**
One convenient `games` table serves both research and product views, with upserts overwriting canonical fields. Enrichment jobs run during experiments.

**How to avoid:**
Define two explicit planes: (1) immutable, versioned research snapshot with checksum and stable IDs; (2) replaceable live enrichment cache with provider IDs, retrieval timestamps, raw payload/version, and stale status. Build model features only from an experiment manifest naming the snapshot. Use an explicit crosswalk and deterministic conflict rules; never overwrite source facts. Demo rendering must degrade to fixed metadata/placeholders when enrichment is unavailable.

**Warning signs:**
Repeated runs change item counts or metrics; model code calls an API; covers/genres disappear after refresh; a single `updated_at` hides which provider changed a value; experiment outputs lack dataset hashes.

**Phase to address:**
Phase 1 — Data model/provenance boundary, verified again in Phase 5 — Experiment harness.

---

### Pitfall 3: Leakage and unfair algorithm comparison

**What goes wrong:**
Future interactions or test-set statistics influence training, preprocessing, feature selection, popularity priors, negative sampling, hyperparameter tuning, or synthetic-profile construction. Alternatively, algorithms receive different candidate sets or tuning budgets. Scores become optimistically biased and rankings may reverse under a realistic split.

**Why it happens:**
Random interaction splits are easy; preprocessing is performed before splitting; one test set is repeatedly consulted; “the same dataset” is mistaken for the same protocol. Recent RecSys work shows split choice can materially change model rankings, and scikit-learn explicitly warns that fitting transformations on test data leaks information.

**How to avoid:**
Write an evaluation protocol before model implementation. Freeze train/validation/test partitions and preserve the global timeline where timestamps exist. Fit vocabulary, TF-IDF, normalization, imputers, popularity, user/item filters, and synthetic-generator calibration on training data only. Tune solely on validation, evaluate test once, use the same eligible users/items/candidates and comparable search budget, and include trivial baselines. Persist split IDs and assert no held-out interaction or future-derived feature enters training.

**Warning signs:**
All-data preprocessing; surprisingly large gains; test metrics guide implementation; no untouched validation set; different algorithms report different user counts; duplicate game editions cross partitions; the synthetic generator encodes which items will be held out.

**Phase to address:**
Phase 2 — Evaluation contract before Phase 3 — Recommender implementations.

---

### Pitfall 4: Claiming practical superiority from narrow offline metrics

**What goes wrong:**
The thesis declares a “best recommender” from RMSE or one top-N relevance metric, while the product task is ranked discovery and the requirements include diversity, novelty, explanations, latency, and cold start. Offline relevance is presented as user utility or causal evidence.

**Why it happens:**
A single leaderboard is easy to explain. Metric definitions, cutoffs, aggregation, uncertainty, and task alignment are left implicit. Multiple model/metric comparisons encourage cherry-picking.

**How to avoid:**
State the user task and estimand first. Predefine relevance metrics (for example Recall/NDCG@K), coverage, intra-list diversity, and a novelty definition tied to training-set popularity; report the accuracy–beyond-accuracy trade-off, per-user distributions, runtime, confidence intervals, and paired comparisons across identical users/seeds. Include popularity/random/content baselines. Phrase conclusions as applying to this dataset/protocol. If feasible, add a small structured user/lab assessment of recommendation usefulness and explanation clarity; current ACM methodological guidance recommends complementing offline results rather than equating them with user value.

**Warning signs:**
Only mean RMSE; K chosen after seeing results; “novelty” has no formula or reference population; no uncertainty; best model changes across metrics but the narrative ignores it; offline performance is called satisfaction.

**Phase to address:**
Phase 2 — Evaluation design, implemented in Phase 5 — Experiments and reporting.

---

### Pitfall 5: Synthetic users become self-fulfilling evidence

**What goes wrong:**
Algorithms are judged on preferences generated by assumptions that favor one algorithm (for example genre-cluster users favor content-based methods or latent-factor generation favors matrix factorization). Thousands of synthetic interactions create narrow confidence intervals around a biased simulation. Results do not establish behavior with real users.

**Why it happens:**
Synthetic data supplies convenient ground truth and volume, but generator assumptions are treated as observations. Generator and evaluator reuse the same representation. Recent research on synthetic evaluation finds bias can materially affect absolute system performance, even when relative comparison may sometimes be less affected.

**How to avoid:**
Use synthetic users primarily for controlled experiments, edge cases, and reproducibility—not as proof of external validity. Specify generator assumptions mathematically; create multiple contrasting scenarios (sparse/dense, niche/mainstream, noisy/consistent, popularity-biased/unbiased), independent seeds, and sensitivity analyses. Do not generate preferences with the exact scoring function being evaluated. Validate marginal distributions against any lawfully available real benchmark where possible, and label all conclusions as simulation-bound.

**Warning signs:**
One generator configuration; near-perfect results; more synthetic users are presented as more realism; algorithm ranking mirrors the generator equation; no sensitivity analysis; synthetic and real interactions are pooled without labels.

**Phase to address:**
Phase 2 — Synthetic-data specification; implement and validate in Phase 4 — Controlled scenarios.

---

### Pitfall 6: Cold start exists in the UI but not in the experiment

**What goes wrong:**
New users see empty, generic, or misleading recommendations, while reported aggregate metrics cover only warm users. New items are excluded by minimum-interaction filters, making collaborative filtering look stronger and hiding catalogue coverage failure.

**Why it happens:**
“Cold start” is treated as one condition rather than distinct new-user, new-item, and sparse-user cohorts. The onboarding preference capture is designed after the model.

**How to avoid:**
Define cohorts and acceptance criteria up front: zero-history user, user after N explicit onboarding selections, sparse user, and zero-interaction item. Use a deterministic fallback (editorial/popularity with disclosed scope), then content-based recommendations from explicit preferences, then hybrid weighting as evidence accumulates. Evaluate each cohort separately for relevance, coverage, diversity, and onboarding burden. Never silently drop cold entities from denominators.

**Warning signs:**
Eligibility requires several ratings; test users all appear in training; new games never surface; onboarding preferences are collected but unused; fallback recommendations have no explanation.

**Phase to address:**
Phase 2 — Evaluation cohorts and Phase 3 — Cold-start/hybrid strategy.

---

### Pitfall 7: The deployed demo depends on a fragile third-party API

**What goes wrong:**
The presentation fails because of rate limits, expired credentials, CORS, provider downtime, changed terms/schema, or exhausted quota. Secrets leak from browser calls. Catalogue pages become slow through per-card requests.

**Why it happens:**
The API is treated like a database with an SLA. For example, IGDB documents a 4-request/second limit, 8 concurrent requests, expiring tokens, and explicitly disallows direct browser requests because tokens would leak. RAWG disclaims uninterrupted service and may amend data/terms; its free plan requires visible linked attribution wherever its data/images appear.

**How to avoid:**
Call providers only from a backend adapter. Cache permitted responses, batch requests, enforce timeout/retry-with-jitter/circuit-breaker behavior, and distinguish not-found from temporarily unavailable. Ship a prewarmed demo cache or lawful fixed fallback, placeholder art, health indicator, and provider-attribution component. Keep secrets server-side and test token refresh. Pin an adapter contract so a provider can be replaced without changing research entities.

**Warning signs:**
API key in frontend/network logs; N requests for N cards; no 429 test; blank page offline; token manually refreshed; attribution absent; experiments fail without internet.

**Phase to address:**
Phase 1 — Provider decision/terms and Phase 4 — Resilient enrichment adapter; rehearse in deployment phase.

---

### Pitfall 8: “Seeded” is mistaken for reproducible

**What goes wrong:**
A run cannot be recreated because the dataset, split, dependencies, preprocessing, seed scope, hardware, or commands differ. Results are manually copied into the dashboard/thesis and diverge from generated artifacts.

**Why it happens:**
Only one library seed is fixed. Mutable API data and unpinned environments remain. scikit-learn documents that `None`, integer seeds, and shared RNG instances behave differently; deterministic reruns also require controlling every stochastic layer.

**How to avoid:**
Make an experiment manifest the unit of evidence: code revision, dataset/split hashes, generator version and seeds, full configuration, dependency lock, runtime/platform, start time, metrics and artifact hashes. Use one command to rebuild data and run experiments locally; run in a clean environment/CI. Generate tables/plots/dashboard data from immutable result files. Repeat stochastic experiments over predefined seeds and report dispersion; distinguish repeatability on the recorded platform from broader reproducibility.

**Warning signs:**
“Run the notebook cells in order”; unpinned dependencies; seed appears only once; results change after API refresh; plots are hand-edited; no clean-machine rehearsal.

**Phase to address:**
Phase 1 — Reproducible foundation, enforced in every algorithm/experiment phase.

---

### Pitfall 9: Accessibility is postponed until visual polish

**What goes wrong:**
Dense filters, status controls, modals, metric charts, and explanation tooltips cannot be used with keyboard/screen reader or at mobile/zoom widths. Retrofitting semantics and focus behavior late causes redesign.

**Why it happens:**
Responsive screenshots and automated audits are treated as accessibility proof. Card/grid UI favors clickable containers, color-only status, hover-only explanations, and custom controls.

**How to avoid:**
Target WCAG 2.2 AA in component contracts: semantic forms/tables/headings, visible labels and errors, keyboard operation and logical focus, non-color status cues, meaningful alternative text, text equivalents for charts, dismissible/hoverable/persistent popovers, adequate contrast/targets, and reflow at 320 CSS px. Test representative core flows with keyboard, 200–400% zoom, screen reader, mobile viewport, and automation from the first UI slice.

**Warning signs:**
`div` buttons; focus lost after modal close; horizontal page scrolling; covers have filename alt text; metrics exist only as charts; tooltip content is hover-only; status conveyed only by color.

**Phase to address:**
Phase 3 — Accessible design system and every feature phase; manual acceptance gate before demo.

---

### Pitfall 10: TFG scope becomes several products plus a research lab

**What goes wrong:**
Inventory edge cases, social features, three recommenders, explainability, experiment tooling, import/export, and deployment are all built broadly but none is defensible end-to-end. Thesis evidence is postponed until the final weeks.

**Why it happens:**
Goodreads/Letterboxd are used as parity targets rather than inspiration. Algorithm count is valued over controlled comparison. Research panel and documentation are treated as polish.

**How to avoid:**
Define one vertical academic spine: licensed fixed corpus → controlled accounts/interactions → three simple, well-specified baselines → frozen evaluation → generated comparison evidence → accessible deployed demo. Cap inventory fields to stated requirements and public profiles to read-only activity; keep follows/feeds/moderation/privacy granularity out. Prefer transparent classical models over extra sophistication. Each phase must emit thesis-ready decisions, formulas, configurations, tests, plots, and limitations.

**Warning signs:**
New social requirements; neural models before baselines; schema supports every edition/region nuance; experiment panel consumes bespoke live computations; thesis writing depends on reconstructing old decisions.

**Phase to address:**
Phase 0 — Roadmap/MVP contract; scope gate at every phase transition.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| One mutable table for fixed and live metadata | Simple queries | Irreproducible experiments and destructive merges | Never |
| Notebook-only experiment pipeline | Fast exploration | Hidden state, poor automation, weak audit trail | Exploration only; promote final pipeline to scripts/modules |
| One seed/one run | Fast leaderboard | No variance estimate; fragile ranking | Smoke tests only |
| Hard-coded provider fields in domain/UI | Faster first API screen | Provider lock-in and migration cost | Never beyond throwaway spike |
| Aggregate metrics only | Compact report | Hides cold/sparse cohorts and user-level failures | Early smoke test only |
| Client-side recommendation computation | Simple demo | Exposes logic/data, duplicates pipeline, inconsistent results | Only for a documented static visualization |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| IGDB | Browser calls expose bearer token; unthrottled concurrency causes 429s | Backend adapter, token refresh, ≤4 requests/s and ≤8 open requests, permitted caching |
| RAWG | Missing linked attribution or assuming service stability | Render required attribution on every relevant page; cache/fallback; record terms version |
| Fixed dataset import | Treating provider ID as universal identity | Internal stable ID plus source-ID crosswalk; deterministic duplicate/edition policy |
| Images | Hotlinking or assuming metadata licence covers art | Track asset-specific source/rights; use permitted URLs/cache and accessible fallback |
| CSV/JSON import | Trusting external IDs/enum values and overwriting records | Validate schema/version, report row errors, stage and reconcile before commit |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Per-card live API calls | Slow catalogue, 429s, layout churn | Backend batching/cache and pagination | Tens of cards per view under IGDB's 4 req/s limit |
| Recomputing all recommendations per page request | Timeouts and irreproducible timings | Offline/precomputed results keyed by model/data version | Even a controlled demo as catalogue/users grow |
| Full pairwise similarity matrices | Memory spikes | Sparse matrices, top-K neighbors, batched computation | Quadratic item/user growth; profile on target dataset |
| Dashboard queries raw experiment events | Slow filters and inconsistent aggregates | Materialized immutable run summaries | Dozens of runs × users × K recommendations |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| API credentials in frontend or repository | Credential theft/quota abuse | Server-side secret injection, secret scanning, rotation |
| Public profiles leak controlled-account inventory/purchase data | Unintended disclosure | Explicit public projection; exclude purchase price/location and private notes |
| Spreadsheet/CSV formula injection on export | Code/command execution when opened in office software | Escape cells beginning with formula control characters; treat imports as untrusted |
| Rendering provider descriptions/comments as HTML | Stored XSS | Sanitize or render as text; strict content policy |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Backlog status and ownership conflated | Cannot represent owned-but-unplayed or played-without-owned | Separate play-state from copy/ownership entities |
| Explanations are generic (“because you may like it”) | No trust or academic inspectability | Evidence-based reason using actual contributing features/history, with fallback disclosed |
| Cold-start questionnaire is long | Users abandon before value | Ask a few high-information preferences/games, show progress and immediate recommendations |
| Research controls dominate consumer UI | Demo feels like a lab tool | Separate user experience from researcher panel; share immutable result artifacts |
| Edition/platform duplicates flood results | Confusing catalogue and biased recommendations | Recommend canonical games; display owned editions/copies beneath them |

## "Looks Done But Isn't" Checklist

- [ ] **Dataset:** Licence URL exists — also archive terms/version, redistribution decision, field/asset provenance, retrieval date, and checksum.
- [ ] **Evaluation:** Metrics render — also verify frozen split, no leakage, shared candidates, baselines, uncertainty, and cold cohorts.
- [ ] **Synthetic users:** Generator runs — also document assumptions, scenario sensitivity, independent seeds, and external-validity limitation.
- [ ] **Cold start:** New user receives items — also test zero-history/new-item cohorts and disclose fallback logic.
- [ ] **Explainability:** Reason text appears — also verify it is faithful to the actual model evidence and accessible without hover.
- [ ] **API integration:** Happy path works — also test 429, timeout, expired token, malformed/missing fields, offline demo, and attribution.
- [ ] **Reproducibility:** README has commands — also reproduce from clean checkout and compare artifact hashes.
- [ ] **Accessibility:** Automated scan passes — also keyboard, focus, zoom/reflow, screen-reader, chart alternatives, and mobile manual tests pass.
- [ ] **Deployment:** Site loads — also ensure experiments do not depend on live API and secrets are absent from client bundles/logs.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Unclear dataset rights | HIGH | Freeze publication, replace corpus or remove restricted fields/assets, rebuild hashes/splits/results, document change |
| Leakage discovered | HIGH | Invalidate affected results, rebuild split-first pipeline, retune on validation, rerun every baseline/model |
| Synthetic generator favors a model | MEDIUM | Add contrasting generators/sensitivity study, narrow claims, seek a lawful real benchmark for triangulation |
| API failure near demo | LOW if designed early / HIGH otherwise | Switch to prewarmed permitted cache/fixed fallback, show stale state, disable refresh gracefully |
| Non-reproducible results | MEDIUM | Recover configs/logs, pin environment, create manifest and rerun; never backfill unverifiable numbers |
| Accessibility retrofit | MEDIUM-HIGH | Fix shared primitives first, then retest prioritized core flows manually and automatically |
| Scope overrun | MEDIUM | Preserve academic spine, cut social/edge-case breadth, freeze new features, convert omissions into documented future work |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Rights/provenance | Phase 1: Data governance | Complete source register; legal/terms review; snapshot checksum; publication decision |
| Fixed/live contamination | Phase 1: Data architecture | Repeat run with API disabled yields identical research features/metrics |
| Leakage/unfair comparison | Phase 2: Evaluation contract | Automated split/feature assertions; identical users/candidates; untouched test |
| Narrow metrics/overclaiming | Phase 2 + Phase 5 | Preregistered metric definitions; baselines; CIs/paired tests; bounded conclusions |
| Synthetic bias | Phase 2 + Phase 4 | Multiple generators/scenarios/seeds; sensitivity table; simulation limitation stated |
| Cold start hidden | Phase 2 + Phase 3 | Separate zero/sparse/new-item cohort metrics and UI acceptance tests |
| API fragility | Phase 4: Enrichment integration | Contract tests for timeout/429/auth/schema; offline demo rehearsal; attribution review |
| Reproducibility | Phase 1 + every experiment phase | Clean-checkout one-command rerun reproduces hashed artifacts within documented tolerance |
| Accessibility | Phase 3 + each UI phase | WCAG 2.2 AA checklist plus keyboard/screen-reader/zoom/mobile manual tests |
| Scope creep | Phase 0 + transitions | Academic vertical slice remains deliverable; out-of-scope list enforced |

## Sources

- [European Commission — EU copyright law: protection of databases](https://digital-strategy.ec.europa.eu/en/policies/protection-databases) — official; database copyright and sui generis right (HIGH for the general EU rule).
- [Directive 96/9/EC on the legal protection of databases](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31996L0009) — primary EU legislation (HIGH; application to a chosen corpus still needs case-specific review).
- [IGDB API documentation](https://api-docs.igdb.com/) — official; authentication, 4 requests/s, 8 open requests, caching, attribution/partnership FAQ, CORS/token warning (HIGH).
- [RAWG API Terms of Service](https://rawg.io/tos_api) — official; attribution, free-plan limits, service/terms-change disclaimers (HIGH; last-update date displayed as 2021, so re-check at provider selection and release).
- [Latifi & Jannach, “A Critical Study on Data Leakage in Recommender System Offline Evaluation”](https://arxiv.org/abs/2010.11060) — research preprint with published RecSys counterpart; global-timeline leakage analysis (MEDIUM-HIGH).
- [“Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders,” ACM RecSys](https://doi.org/10.1145/3705328.3748164) — peer-reviewed; split protocols can change realism and model rankings (HIGH).
- [Zangerle & Bauer, “Evaluating Recommender Systems: Survey and Framework,” ACM Computing Surveys](https://doi.org/10.1145/3556536) — peer-reviewed evaluation framework; multi-faceted task/data/metric design (HIGH).
- [Jannach & Chen, “Improving Methodological Standards in Recommender Systems Offline Evaluation,” ACM TORS](https://doi.org/10.1145/3800587) — peer-reviewed methodological guidance; limits of offline-only claims (HIGH).
- [“Towards Understanding Bias in Synthetic Data for Evaluation”](https://arxiv.org/abs/2506.10301) — recent research preprint; bias in synthetic test collections (MEDIUM; use as a threat-to-validity signal, not settled authority).
- [scikit-learn — Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html) — official documentation; preprocessing leakage and random-state subtleties (HIGH).
- [PyTorch — Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html) — official documentation; seeds/determinism limits (HIGH; consult if PyTorch is selected).
- [W3C — Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/) — normative W3C Recommendation; keyboard, contrast, reflow, focus, target and hover/focus requirements (HIGH).

---
*Pitfalls research for: SavePoint*
*Researched: 2026-09-04*
