# SavePoint

## What This Is

SavePoint is a web application for cataloguing a personal video-game backlog and collection, inspired by Goodreads and Letterboxd. Users can record played and pending games, rate them, publish comments, expose a public profile, and organise physical and digital copies with detailed inventory metadata.

The project is also an academic platform for a final degree thesis (TFG). It will implement and compare content-based, collaborative, and hybrid recommendation systems using reproducible experiments, synthetic users, explainable results, and documented data provenance.

## Core Value

Users receive useful and explainable video-game recommendations from a well-organised collection, while every algorithmic result remains reproducible and defensible in the thesis.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Users can maintain a backlog using statuses such as pending, playing, completed, and abandoned.
- [ ] Users can rate games, write comments, and expose their activity through public profiles.
- [ ] Users can organise games by catalogue metadata, custom lists, platform, and genre.
- [ ] Users can inventory physical and digital copies, including platform, edition, purchase details, and conservation state where applicable.
- [ ] The application combines a stable, citable dataset with a legal external API that enriches game records with broad and current metadata.
- [ ] The project implements content-based, collaborative-filtering, and hybrid recommendation algorithms.
- [ ] Recommendation algorithms can be evaluated and compared through reproducible experiments and appropriate metrics.
- [ ] Recommendations explain relevant reasons behind their results.
- [ ] New users can receive recommendations through an explicit cold-start strategy.
- [ ] A researcher-facing panel presents recommendation outputs, metrics, timings, and algorithm comparisons.
- [ ] Evaluation covers diversity and novelty as well as predictive relevance or accuracy.
- [ ] Catalogue records retain source, licence, retrieval date, and data-quality information.
- [ ] Collections, ratings, and lists can be imported and exported in CSV or JSON formats.
- [ ] Synthetic users, ratings, and histories support controlled and repeatable testing.
- [ ] The application is responsive, accessible, deployable on the web, and reproducible in a local environment.
- [ ] Architecture, language and framework choices, data models, algorithms, alternatives, experiments, metrics, and results are documented for later use in the written thesis.

### Out of Scope

- Full social network features such as follows, social feeds, and community interaction — public profiles are sufficient for v1.
- Open production registration and real-world community operation — v1 is a controlled academic demonstration.
- Gameplay diary and per-session tracking — deferred to v2 to keep v1 focused on inventory and recommendations.
- Spoiler-aware review controls — deferred to v2.
- Advanced per-list and per-item privacy controls — deferred to v2; the initial demo uses controlled accounts.

## Context

This is a greenfield TFG project with no prescribed programming language, framework, database, or deployment platform. Technology choices should therefore follow research and be justified against suitability, reproducibility, maintainability, data-processing needs, and the constraints of an academic demonstration.

The initial evaluation will not depend on organic adoption. Controlled synthetic users and interaction histories will exercise collaborative and hybrid recommenders, while a fixed dataset will make experiments repeatable. A separate external API may enrich the user-facing catalogue with current covers and metadata, but the research dataset must remain stable and citable.

The system should reach the public-profile scope associated with Goodreads or Letterboxd without implementing a complete social network. The inventory goes beyond a simple backlog by representing ownership details for physical and digital copies.

Every consequential implementation choice must leave usable evidence for the thesis: rationale, alternatives considered, architecture, algorithms and mathematical basis, dataset provenance and licensing, experiment design, metrics, limitations, results, and threats to validity.

## Constraints

- **Academic reproducibility**: Experiments, synthetic data generation, configurations, and results must be repeatable — the recommendation comparison is a central thesis contribution.
- **Data legality and provenance**: Dataset and API use must respect their licences and terms, and each source must be traceable — the thesis must cite defensible sources.
- **Dual delivery**: Provide both a deployed web application and a documented local environment — the tribunal needs a convenient demonstration and the work needs to be reproducible.
- **Controlled initial audience**: v1 uses a controlled academic demo with synthetic accounts rather than unrestricted public operation — this limits moderation and operational scope.
- **Accessibility and responsive design**: Core workflows must work across desktop and mobile layouts and follow accessible interaction practices — usability must be demonstrable.
- **No fixed stack**: Architecture and technologies remain open until researched — selections must be justified rather than inherited without evidence.
- **Language convention (since 2026-09-06)**: thesis documentation (`docs/**`), all conversation with the author, all prompts written for other AIs, and new prose in `.planning/**` are in **Spanish**; code (identifiers, code comments, commit messages, test names, log strings, branch names) stays in **English**. Verbatim legal quotations and language-neutral tokens (requirement IDs, paths, hashes, URLs, env-var names, commands) are kept as-is. Canonical doc: `CONVENTIONS.md`. No command needed — instruction files load per session; `/gsd-resume-work` reloads planning context.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Target public profiles without full social networking in v1 | Reaches the desired Goodreads/Letterboxd visibility while containing scope | — Pending |
| Use an advanced physical/digital inventory model | The collection must represent ownership, edition, purchase, and conservation details, not only play status | — Pending |
| Compare content-based, collaborative, and hybrid recommendation systems | Algorithm comparison and theory are central to the TFG | — Pending |
| Combine a stable dataset with a live enrichment API | Supports reproducible evaluation while retaining rich and current catalogue presentation | — Pending |
| Use controlled synthetic users and histories | Enables repeatable recommendation experiments before real usage data exists | — Pending |
| Include explainability, cold-start handling, an experiment panel, diversity, and novelty in v1 | Strengthens both the practical recommender and its academic evaluation | — Pending |
| Deliver deployed and locally reproducible versions | Supports presentation, assessment, and independent reproduction | — Pending |
| Preserve technical and experimental rationale as project artifacts | The implementation must directly support later thesis writing | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-04 after initialization*
