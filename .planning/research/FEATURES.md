# Feature Research

**Domain:** Video-game backlog, physical/digital collection inventory, public profiles, and academic recommender comparison
**Researched:** 2026-09-04
**Confidence:** MEDIUM

## Feature Landscape

SavePoint serves two audiences with different definitions of completeness. A player needs a coherent catalogue, library, inventory, profile, and recommendation journey. A thesis evaluator needs reproducible evidence that the algorithms were compared fairly. The second category must be implemented, but it should not leak experimental controls into ordinary player workflows.

### Product Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Atomic v1 boundary |
|---------|--------------|------------|--------------------|
| Controlled sign-in and profile identity | Personal libraries, ratings, and recommendations need an owner | MEDIUM | Seeded/demo accounts; sign in/out; display name, avatar placeholder, bio; no public registration or account recovery |
| Searchable game catalogue and game detail | Every tracking action starts by locating the correct title | MEDIUM | Search plus platform/genre filters; cover, title, release data, genres, platforms, description, source attribution |
| Backlog lifecycle | A backlog product must distinguish intent and progress | MEDIUM | One current status per user/game: pending, playing, completed, abandoned; status can be changed and filtered |
| Ratings and comments | Users expect to record opinion, not only ownership | MEDIUM | Consistent documented rating scale; create/edit/delete own rating and plain-text comment; no replies, likes, or moderation workflow |
| Custom lists | Curated groupings are standard in media catalogues | MEDIUM | Create, rename, delete, order, and add/remove games; public list visibility only under controlled-account policy |
| Library browsing, sorting, and filtering | Collections quickly become unusable without retrieval tools | MEDIUM | Paginated or virtualized library; filter by status, ownership, platform, genre, and list; sort by title, rating, and date added |
| Separate ownership copies from play status | A user may play without owning, own multiple editions, or own both physical and digital copies | HIGH | Game-in-library and owned-copy records are separate; multiple copies per game are allowed |
| Physical copy inventory | Collector value depends on the exact artifact, not just the title | HIGH | Platform, region, edition/variant, condition, completeness/components, quantity, purchase date/place/price, storage location, notes |
| Digital copy inventory | Digital ownership has different semantics from physical condition | MEDIUM | Store/account label, platform, acquisition date/price, licence basis such as purchase/subscription, install/availability note; no secret keys |
| Public profile and shareable collection view | The requested Goodreads/Letterboxd-level visibility requires a stable public presentation | MEDIUM | Profile summary, selected library statistics, ratings/comments, and public lists; no follows or activity feed |
| Personalized recommendation list | Recommendation is part of the product's core value | HIGH | Ranked top-N unseen games, algorithm label, refresh/retrieve behavior, graceful empty state |
| Recommendation explanation | Users need understandable reasons and the thesis needs inspectable output | HIGH | Per-item reasons based on visible signals such as genres/platforms/similar rated games; never imply causal certainty |
| Cold-start onboarding | New/demo users otherwise receive empty or arbitrary collaborative results | HIGH | Explicit preference capture and/or popularity-with-filters fallback; UI states which strategy was used |
| CSV/JSON import with validation preview | Manual entry is a major adoption barrier for existing collections | HIGH | Supported schema, dry-run preview, row-level errors, deterministic matching, duplicate policy, and import report |
| CSV/JSON export | Portability and backup are expected for user-owned catalogue data | MEDIUM | Versioned schema covering statuses, ratings, lists, and owned copies; preserve stable identifiers and timestamps where relevant |
| Responsive, accessible core workflows | The demo must remain usable on mobile, keyboard, and assistive technology | HIGH | WCAG 2.2 AA target for catalogue, library, inventory, profile, recommendations, and dashboard; charts also have text/table equivalents |

### Academic Evaluation Table Stakes (Thesis Needs These)

| Feature | Why Required | Complexity | Atomic v1 boundary |
|---------|--------------|------------|--------------------|
| Stable, citable evaluation dataset | Algorithm results cannot be defended if live metadata changes the experiment input | HIGH | Immutable dataset version/snapshot, licence/citation, checksum, field dictionary, inclusion/exclusion rules |
| Provenance and data-quality registry | Every consequential field needs an auditable origin | HIGH | Source, licence, retrieval date, source identifier, transformation/version, missingness/quality indicators; live enrichment is kept out of benchmark features unless snapshotted |
| Deterministic synthetic-user generator | Collaborative and hybrid models need controlled interactions before real adoption | HIGH | Seeded generation configuration, reproducible users/ratings/histories, scenario labels, downloadable manifest |
| Comparable algorithm implementations | The thesis explicitly compares content-based, collaborative, and hybrid methods | HIGH | Shared candidate catalogue, interaction semantics, train/test protocol, top-K, exclusions, and output contract |
| Reproducible experiment runner | Manual notebook runs are too easy to change accidentally | HIGH | Persist dataset version, code/model version, seed, split, parameters, environment, start/end time, status, and artifact paths |
| Evaluation metric suite | Accuracy alone cannot support the stated research claims | HIGH | Ranking/relevance metrics such as precision/recall/nDCG at fixed K plus diversity, novelty, and catalogue coverage; metric definitions are versioned |
| Cold-start evaluation scenarios | Having a fallback is different from measuring it | HIGH | Explicit new-user and sparse-user cohorts; same scenarios across algorithms; segment-level metrics |
| Experiment comparison dashboard | The tribunal needs inspectable results, not raw logs | HIGH | Compare selected runs by metrics and timings; show configuration and cohort; accessible tables accompany charts |
| Result export and evidence bundle | Thesis figures and independent checking require durable outputs | MEDIUM | Export machine-readable results and presentation-ready tables; include configuration and provenance references |
| Limitations and threats-to-validity record | Synthetic and offline evaluation cannot be presented as production proof | LOW | Each run/report links assumptions, exclusions, metric caveats, synthetic-data limitations, and failed-run status |

### Differentiators (Aligned With Core Value)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Unified backlog plus copy-level inventory | Most backlog tools track a title while collector tools focus on artifacts; SavePoint can represent both without conflating them | HIGH | Make `user-game` and `owned-copy` separate concepts from the first schema version |
| Side-by-side recommendation comparison | Users/reviewers can see how content, collaborative, and hybrid methods differ for the same profile | HIGH | Researcher view first; avoid presenting raw scores as comparable until calibrated or normalized |
| Explanation tied to traceable evidence | Reasons can cite the user's visible preferences and source metadata | HIGH | Store explanation inputs with the recommendation result so later metadata changes do not rewrite history |
| Explicit cold-start strategy and disclosure | New users get useful results and can understand why personalization is limited | MEDIUM | Preference onboarding can double as a controlled academic scenario |
| Reproducibility-first evidence bundle | A single run can be reconstructed and cited in the thesis | HIGH | Strongest academic differentiator; prioritize over production-scale automation |
| Multi-objective evaluation | Diversity, novelty, and coverage reveal trade-offs hidden by relevance-only evaluation | HIGH | Present trade-offs, not a universal winner; metrics need precise definitions and fixed K |
| Import/export that preserves inventory semantics | Users can migrate detailed copies rather than a flat list of game names | HIGH | Version the interchange schema and provide canonical IDs plus human-readable fallback fields |

### Anti-Features (Deliberate v1 Exclusions)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Follows, friends, social feed, likes, notifications | Mimics Goodreads/Letterboxd engagement | Requires privacy, moderation, abuse handling, ranking, and notification infrastructure unrelated to the thesis | Public profiles and stable shareable list/profile URLs |
| Open registration and production community | Makes the demo feel launch-ready | Expands security, consent, account recovery, moderation, operational, and privacy obligations | Controlled seeded accounts with documented credentials and reset procedure |
| User-edited global catalogue | Fills missing metadata quickly | Creates conflicts, vandalism, moderation, and irreproducible experiment inputs | Curated fixed dataset plus attributable API enrichment and an admin-only correction process if essential |
| Automatic continuous synchronization with every storefront | Convenient library ingestion | OAuth/terms variance, brittle connectors, identity matching, secret handling, and nondeterministic data | CSV/JSON import; at most one separately scoped connector after v1 validation |
| Real-time model retraining after every action | Sounds highly personalized | Adds queues, invalidation, observability, and irreproducible run state without helping the controlled study | Explicit versioned batch training and recommendation generation |
| A single composite “best algorithm” score | Produces an easy winner | Arbitrary weights hide relevance/diversity/novelty trade-offs and can invalidate conclusions | Show a metric vector, Pareto-style trade-offs, and predeclared primary/secondary metrics |
| Generative-AI explanations | Produces fluent reasons | Risks hallucinated attributes, adds cost and evaluation burden, and weakens traceability | Deterministic explanation templates derived from stored features and neighbors |
| Price valuation, marketplace, lending, or trading | Appeals to collectors | Requires volatile pricing sources, transactions, disputes, and much more legal/operational scope | Store acquisition price and optional non-authoritative personal notes only |
| Serial numbers, activation keys, receipt images | Captures a complete inventory | Creates sensitive-data and access-control obligations that conflict with public profiles | Non-secret purchase/store notes; defer protected attachments and private fields |
| Arbitrary custom inventory fields in v1 | Handles every collector edge case | Complicates validation, filtering, imports, exports, and thesis data modeling | Fixed physical/digital schemas plus a plain notes field |
| Gameplay diary and session tracking | Enables richer activity and preference data | Creates a second product domain and event model | Status, rating, and date-updated signals only; revisit in v2 |
| Fine-grained privacy per item/list | Offers production-grade control | Easy to misconfigure and hard to test comprehensively | Controlled accounts with one documented public-profile policy in v1 |
| Native mobile applications | Better phone ergonomics | Duplicates UI and release work | Responsive progressive web experience |

## Feature Dependencies

```text
Stable catalogue + canonical IDs
    -> backlog statuses, ratings/comments, lists
    -> owned-copy inventory
    -> import/export matching
    -> content features and candidate generation

Controlled accounts
    -> personal library and inventory
    -> public profiles
    -> recommendation history

User-game interactions + deterministic synthetic users
    -> collaborative recommender
    -> hybrid recommender

Content feature pipeline
    -> content-based recommender
    -> hybrid recommender
    -> deterministic explanations

Versioned dataset + split protocol + metric definitions
    -> reproducible experiment runner
    -> comparable experiment results
    -> dashboard and evidence exports

Recommendation output contract
    -> product recommendation view
    -> explanations
    -> experiment comparison dashboard

Versioned interchange schema + canonical identifiers
    -> import preview/validation
    -> loss-aware export and round-trip tests
```

### Dependency and Ordering Notes

- **Catalogue identity precedes everything else:** recommendation features, imports, lists, and multiple owned copies all need stable game/platform/edition identifiers. Title-string matching alone will cause duplicates and corrupt evaluation joins.
- **Model copy inventory separately before building forms:** retrofitting multiple copies after assuming one row per user/game is a likely schema rewrite.
- **Freeze the experimental contract before implementing all three algorithms:** candidate exclusions, interaction meaning, data split, K, seeds, and metrics must be shared or comparisons are invalid.
- **Content-based comes before hybrid:** it validates the metadata feature pipeline and provides a cold-start-capable baseline. Collaborative follows once deterministic interaction data exists; hybrid depends on both.
- **Instrumentation precedes the dashboard:** persist structured run records and artifacts first. A dashboard built on ad-hoc logs will be brittle and non-reproducible.
- **Export schema should precede import:** define the canonical, versioned representation, then import into it with preview and errors. Round-trip export/import becomes a useful acceptance test.
- **Accessibility is cross-cutting:** semantic components, focus behavior, error/status messages, responsive tables, and non-visual chart alternatives must be acceptance criteria in every UI phase, not a final polish task.

## MVP Definition

### Launch With (v1 Product)

- [ ] Controlled demo accounts and public profiles
- [ ] Searchable, attributable catalogue with stable identifiers
- [ ] Backlog states, ratings/comments, lists, filters, and sorting
- [ ] Separate physical and digital copy inventory with multiple copies per game
- [ ] CSV/JSON import preview and versioned export
- [ ] Ranked recommendations with deterministic explanations and cold-start disclosure
- [ ] Responsive and WCAG 2.2 AA-oriented core workflows

### Launch With (v1 Academic Evaluation)

- [ ] Versioned benchmark dataset with provenance, licence, checksum, and quality report
- [ ] Seeded synthetic-user/scenario generator
- [ ] Content-based, collaborative, and hybrid recommenders using a shared output contract
- [ ] Reproducible runs with fixed splits, seeds, parameters, versions, timings, and artifacts
- [ ] Relevance/ranking, diversity, novelty, and coverage metrics at declared K
- [ ] New-user and sparse-user cold-start evaluation cohorts
- [ ] Accessible comparison dashboard plus CSV/JSON evidence export
- [ ] Explicit assumptions, failures, limitations, and threats to validity

### Add After Validation (v1.x)

- [ ] Bulk-edit library and inventory records — add if seeded demos or import correction expose repetitive editing
- [ ] Advanced multi-select filters and saved views — add when realistic collection size makes basic filtering insufficient
- [ ] Optional personal inventory photos — only after storage, privacy, and public-profile behavior are specified
- [ ] One storefront import adapter — only if CSV/JSON matching is stable and terms/authentication fit the thesis schedule
- [ ] Additional cold-start preference elicitation — if baseline onboarding produces insufficient catalogue coverage

### Future Consideration (v2+)

- [ ] Gameplay diary and per-session tracking
- [ ] Fine-grained list/item/profile privacy
- [ ] Social graph, feed, reactions, comments on reviews, and notifications
- [ ] Community catalogue edits and moderation
- [ ] Native mobile clients, barcode/photo recognition, marketplace valuation, lending, or trading

## Feature Prioritization Matrix

| Feature group | User Value | Academic Value | Implementation Cost | Priority |
|---------------|------------|----------------|---------------------|----------|
| Stable catalogue and provenance | HIGH | HIGH | HIGH | P1 |
| Backlog, ratings/comments, lists | HIGH | MEDIUM | MEDIUM | P1 |
| Copy-level physical/digital inventory | HIGH | MEDIUM | HIGH | P1 |
| Controlled accounts and public profiles | HIGH | LOW | MEDIUM | P1 |
| Versioned import/export | HIGH | HIGH | HIGH | P1 |
| Content-based recommender | HIGH | HIGH | HIGH | P1 |
| Synthetic users and collaborative recommender | MEDIUM | HIGH | HIGH | P1 |
| Hybrid recommender | HIGH | HIGH | HIGH | P1 |
| Explanations and cold-start handling | HIGH | HIGH | HIGH | P1 |
| Reproducible experiment runner and metrics | LOW | HIGH | HIGH | P1 |
| Comparison dashboard and evidence bundle | MEDIUM | HIGH | HIGH | P1 |
| Bulk edit and saved advanced filters | MEDIUM | LOW | MEDIUM | P2 |
| Photos, barcode/photo recognition, storefront sync | MEDIUM | LOW | HIGH | P3 |
| Full social layer | MEDIUM | LOW | HIGH | Excluded |

**Priority key:** P1 is necessary for the controlled v1 demonstration or thesis claims; P2 is conditional usability work; P3 is deferred; Excluded conflicts with the agreed scope.

## Competitor Feature Analysis

| Capability | Backloggd | Collector-oriented tools (PLAYBACK/GameVentory/Game Collector) | SavePoint v1 approach |
|------------|-----------|---------------------------------------------------------------|-----------------------|
| Backlog and progress | Collection/library states, plays, ratings, reviews, lists | Often owned/wanted/traded rather than play-centric | Explicit play status independent of ownership |
| Opinion and curation | Ratings, reviews, custom ordered lists | Usually secondary to inventory | Ratings, plain-text comments, and ordered custom lists |
| Public presence | Profiles, reviews/lists, and broader social features | Shareable collections or shelves | Public profile and lists only; no social graph/feed |
| Physical inventory | Some ownership/play-log fields | Edition/region, condition, completeness/components, purchase data, notes/photos/location | Structured copy-level physical schema, without protected media or market valuation |
| Digital inventory | Basic ownership in many products | Some tools cover digital purchases alongside physical | Separate digital schema with store/platform/licence basis |
| Portability | Export/import are prominent requested roadmap items | Varies by product | Versioned CSV/JSON import preview and export are v1 requirements |
| Recommendations | Requested or present as a user feature | Usually not central | Three explainable algorithms plus academic comparison |
| Experimental evidence | Not a consumer-platform concern | Not a consumer-platform concern | Versioned datasets, synthetic cohorts, runs, metrics, timings, and evidence export |

## Scope Traps and Requirement-Splitting Guidance

- Do not write one requirement called “manage collection.” Split catalogue lookup, user-game state, physical copy, digital copy, validation, filters, and deletion because they have different rules.
- Do not write “recommend games” as a single requirement. Separate candidate eligibility, each algorithm, cold-start policy, explanation contract, persisted output, and user presentation.
- Do not combine product recommendations with experiment comparison. The former optimizes understandable user delivery; the latter requires parameter visibility, comparable cohorts, metrics, timings, and reproducibility metadata.
- Do not combine external enrichment with the benchmark dataset. Live covers/descriptions may change; research inputs need a cited snapshot and checksum.
- Do not call a run reproducible merely because a seed exists. Dataset version, preprocessing, split membership, algorithm/version, dependency environment, configuration, and metric definitions are also inputs.
- Treat failed, partial, and empty experiments as first-class statuses. Silently dropping failed runs biases the comparison and makes the dashboard misleading.
- Avoid percentage claims such as “algorithm A is better” unless the dashboard identifies the metric, K, cohort, split, and run configuration.
- Define deletion and duplicate semantics for imports before implementing bulk mutation. Imported ratings, lists, statuses, and copies can conflict independently.
- Public-profile fields and inventory fields require an explicit allowlist. Even controlled accounts should never expose store account identifiers, serials, keys, receipts, storage location, or purchase notes by accident.

## Sources

- [Backloggd product](https://backloggd.com/?lang=en) and [feature roadmap](https://backloggd.com/roadmap/) — current product/roadmap evidence for ratings, reviews, lists, profiles, filters, import/export demand, recommendations, and broader social scope. **Confidence: MEDIUM**.
- [PLAYBACK video-game collection tracker](https://playback-archive.com/video-game-collection) — collector-oriented evidence for edition, region, condition, completeness, quantity, purchase history, notes, and photos. **Confidence: MEDIUM**.
- [GameVentory product](https://gameventory.app/) and [help](https://gameventory.app/help) — collector workflow and copy fields including edition, condition, contents, purchase data, notes, photos, shelves, barcode lookup, and sharing. **Confidence: MEDIUM**.
- [Game Collector](https://gamecollector.online/) — corroborating physical inventory fields such as purchase details, condition, region, boxes/manuals, photos, and notes. **Confidence: MEDIUM**.
- [Linux Foundation Recommenders evaluation documentation](https://recommenders-team.github.io/recommenders/evaluation.html) — ranking/relevance metrics and beyond-accuracy metrics including coverage, novelty, diversity, and serendipity. **Confidence: MEDIUM**.
- [W3C Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/wcag/) — primary accessibility standard supporting responsive reflow and accessible interaction requirements. **Confidence: MEDIUM**.
- [IGDB API documentation](https://api-docs.igdb.com/) — official evidence that user-facing attribution is required when integrating IGDB; the eventual chosen API must receive a separate licence/terms review. **Confidence: MEDIUM**.

## Confidence and Research Gaps

- **Overall MEDIUM:** competitor capabilities were cross-checked across several live product sources, and evaluation/accessibility claims use maintained technical or standards documentation. Product marketing pages may omit limitations, and no user interviews were available.
- The precise benchmark dataset and enrichment API are undecided; their licence, redistribution, attribution, identifiers, and field coverage require phase-specific verification before requirements freeze.
- Rating scale, public-profile allowlist, list visibility, exact inventory enumerations, and import conflict policy are product decisions rather than ecosystem facts.
- Metric formulas, split strategy, statistical comparison, synthetic-user realism, and threats-to-validity protocol require deeper recommender-methodology research during the AI/experiment design phase.

---
*Feature research for: SavePoint*
*Researched: 2026-09-04*
