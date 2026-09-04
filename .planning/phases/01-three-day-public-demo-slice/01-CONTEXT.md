# Phase 1: Three-Day Public Demo Slice - Context

**Gathered:** 2026-09-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a lawful, secure, publicly deployed and locally reproducible vertical demo within three days. The slice covers a realistic homepage and controlled login, a curated searchable catalogue, core backlog/rating/copy actions, a public profile, and simple popularity recommendations. Full-scale ingestion, advanced inventory fields, resilient live enrichment, sophisticated recommenders, and production hardening remain assigned to later roadmap phases.

</domain>

<decisions>
## Implementation Decisions

### Demo Journey
- **D-01:** The public URL opens a realistic product homepage with SavePoint branding, value proposition, representative content, and a visible login entry.
- **D-02:** Controlled access uses a conventional username/password form with demo credentials displayed separately; demo passwords are never infrastructure secrets.
- **D-03:** Successful login opens the catalogue rather than a dashboard or collection page.
- **D-04:** The product contains no guided tour. Actions and empty states must be self-explanatory; a separate presentation script will support the tribunal demo.

### Initial Catalogue
- **D-05:** Phase 1 uses a curated, reviewed sample of 100-300 games, while identifiers, schemas, and import boundaries must support thousands later.
- **D-06:** The sample represents multiple eras, genres, PC, current consoles, and historical platforms rather than favouring one ecosystem.
- **D-07:** Maximise cover availability only where source terms permit display/caching. Retain attribution and use a coherent first-party placeholder when rights or data are unavailable.
- **D-08:** Each game page shows concise provenance and links to a detailed global sources/methodology page.
- **D-09:** Catalogue identity is hierarchical: work → releases/platforms/editions → user-owned copies. Distinct remakes are separate linked works. — **Reversibility:** costly — flattening or changing this hierarchy later would require catalogue and ownership-data migration.
- **D-10:** Interface and catalogue presentation support Spanish and English per user preference, with explicit fallback to English or the original value and alternative titles searchable in both languages.
- **D-11:** DLC and expansions are related child content inside the base-game page, not independent catalogue results or backlog entries.
- **D-12:** Initial search tolerates case, accents, bilingual alternative titles, and small typographical errors. Advanced faceted filters and autocomplete remain Phase 4.

### Backlog and Inventory
- **D-13:** Ratings use five stars with half-star increments. Store them in an exact normalized representation suitable for later recommendation/evaluation calculations.
- **D-14:** A game exposes one current state—pending, playing, completed, or abandoned—while retaining a dated transition history. — **Reversibility:** costly — removing history after launch would discard chronological evidence used by later statistics and experiments.
- **D-15:** Phase 1 copy creation requires only physical/digital format, platform, and edition. Purchase, conservation, location, and private-note fields arrive in Phase 3.
- **D-16:** Status and rating belong to the game/work; multiple platform copies remain separate ownership records. Preserve a clean model boundary for optional version-level ratings in a later release.

### Visual Direction
- **D-17:** Use a modern hybrid visual style: dark, cover-led catalogue presentation with clean, highly legible inventory and data panels.
- **D-18:** The initial dark palette is provisional, accessible, and implemented through replaceable design tokens. Future screenshots, links, sketches, and palettes can become canonical visual references through `$gsd-ui-phase 1`.
- **D-19:** Catalogue uses an adaptive cover grid. Essential information is visible; richer information may appear on large screens or keyboard focus, but no action may depend only on hover.
- **D-20:** Navigation uses a top bar on desktop and a compact menu on mobile, covering home, catalogue, collection, profile, and session actions.

### Agent's Discretion
- Exact demo-game selection within the agreed representative 100-300 boundary, subject to documented lawful provenance.
- Exact provisional colour values, typography, spacing, placeholder artwork, and responsive breakpoints, subject to accessible contrast and replaceable tokens.
- Exact copy and micro-interaction wording in Spanish and English, provided both locales remain complete and consistent.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope and Requirements
- `.planning/PROJECT.md` — Product vision, TFG purpose, constraints, and locked project-level decisions.
- `.planning/REQUIREMENTS.md` — Phase 1 requirement definitions and full v1 boundaries.
- `.planning/ROADMAP.md` — Phase 1 goal, deadline, dependencies, success criteria, and later-phase boundaries.
- `.planning/STATE.md` — Current position, three-day constraint, and project concerns.

### Research
- `.planning/research/SUMMARY.md` — Recommended architecture, data-governance boundary, security/reproducibility risks, and phase implications.

No user-supplied external theses, university templates, lecturer notes, visual examples, specifications, or ADRs have been provided yet. When supplied, register their full project-relative paths as canonical references before relying on them.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None: the repository is greenfield and currently contains planning artifacts only.

### Established Patterns
- No application patterns exist yet. Project research recommends a modular web application with strict separation between immutable research data and mutable enrichment data.
- Planning artifacts require continuous thesis evidence, agent-methodology traceability, and server-side secret handling.

### Integration Points
- New application skeleton, catalogue seed pipeline, authentication, public profile projection, recommendation baseline, local runtime, and deployment must all be established in this phase.

</code_context>

<specifics>
## Specific Ideas

- Product inspiration is Goodreads and Letterboxd, adapted to video games without copying their visual identity.
- The first impression should resemble a real public service, not an internal experiment dashboard.
- The catalogue should eventually hold thousands of games and as many legally usable covers as practical.
- A later UI discussion may incorporate screenshots, links, sketches, or palettes supplied by the user.

</specifics>

<deferred>
## Deferred Ideas

- Advanced catalogue filters, autocomplete, and resilient live enrichment — Phase 4.
- Purchase details, conservation state, storage location, private notes, lists, comments, and import/export — Phase 3.
- Content, collaborative, and hybrid recommenders plus academic comparison — Phases 5-7.
- Research comparison panel and full security/operations hardening — Phase 8.
- Optional rating per release/platform — future release; Phase 1 stores only game-level ratings.

</deferred>

---

*Phase: 01-three-day-public-demo-slice*
*Context gathered: 2026-09-04*
