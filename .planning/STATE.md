---
gsd_state_version: 1.0
current_phase: 7
status: completed
stopped_at: Phase 7 complete — all phases complete
last_updated: "2026-09-14T09:27:36.873Z"
last_activity: 2026-09-14
last_activity_desc: Phase 7 complete
state_head: ddb7eaf435dc78968d656971dee6d5f5bcc24eb3
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 66
  completed_plans: 66
  percent: 50
total_plans_in_phase: 6
next_phase: 07
next_phase_name: Research Panel, Hardening, and Evidence Freeze
next_action: Ejecutar 07-04-PLAN.md
current_plan: 03
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-08)

Living project mirror: `ideas-vault/` (see `CONVENTIONS.md` and its README for the update
rule that applies to every LLM and collaborator).

**Core value:** Users receive useful and explainable video-game recommendations from a well-organised collection, while every algorithmic result remains reproducible and defensible in the thesis.
**Current focus:** Phase 07 — Research Panel, Hardening, and Evidence Freeze

## Current Position

**Phase:** 7
**Plan:** Not started
**Plans in Phase:** 6
**Status:** All phases complete

### Snapshot de ejecucion vigente (2026-09-07)

**Fase 2, ola 3 CERRADA.** 02-01 y 02-07 (ola 1), 02-02 y 02-08 (ola 2), y 02-03,
02-05, 02-09 y 02-10 (ola 3) tienen SUMMARY, commits y verificaciones verdes. El plan
02-09 se cerró en `0b90de7`.

- **02-08** congeló el contrato de evaluación EVAL-03: `docs/methodology/protocol.json`
  (12 claves + `simulation:true`, rejilla de 18 configs, tope 24),
  `docs/methodology/evaluation-protocol.md` (`## Amenazas a la validez`, DOC-04), app
  `apps/api/evaluation/` en `INSTALLED_APPS` con `protocol.py`, `metrics.py`
  (precision/recall/nDCG/MAP a mano) y `splits.py` (leave-one-out por usuario + partición
  train/val/test). `pytest apps/api` 280/280. Tarea 1 ratificada `ratify-as-proposed`.
- **02-02** verificó por consulta directa a BD que el import IGDB está **completo**
  (312.560 obras, cursor 416.648; 193.885 gobernadas; 27.014 con `rating` = **13,933 %**;
  no se reimportó nada). RAWG acotado N=10.000 sobre el top por `rating_count` →
  **8.575 emparejadas / 8.575 `CorpusRatingSnapshot(source="rawg")` / 1.425 descartadas**,
  `GameWork.rating` sin mutar (huella idéntica), 70 tests catalogue. **Cobertura nueva por
  RAWG: 0 obras** — el corte por `rating_count` ya tenía rating IGDB, así que RAWG aquí es
  contraste de fuente, no relleno. `shm_size:256mb` añadido al `db` de Compose. 3
  desviaciones documentadas en el SUMMARY (contenedor `db` recreado por el worktree
  concurrente; conversión de rutas MSYS; bug pre-existente de FK de `SourceRecord` en 22
  filas, 0,26 %, diferido).

Requisitos completados en la ola 3: EVAL-09, EVAL-10 y AUTH-02, además de REC-01 y REC-03.
Siguen pendientes EVAL-01, DATA-05, DATA-07 y los planes restantes de la Fase 2.

**Pendiente inmediato — RAWG pasada 2** (ratificado por el autor 2026-09-07, ver
`02-02-RATINGS-FOLLOWUP.md`): juegos con `rating IS NULL` y `first_release_date` 2022-2026,
ordenados por popularidad (`total_rating_count` → `rating_count` → recientes), `--limit 20000`
hasta agotar cuota. Necesita flags nuevos en `enrich_rawg_ratings` + enmienda a ADR-008.

Fase 01.1 CERRADA. D-01 ratificada por el autor el 2026-09-07 (39 plataformas). La
preferencia de consolas actuales primero está registrada en 02-04.

Hecho y commiteado esta sesión (2026-09-06):

- Corrección post-cierre de la 01.1 (tanda 1): login fuera de la home, motivos reales de contraseña, login case-insensitive, `GET /api/accounts/me/` — `2bfbfe2`.
- Borrador LaTeX del TFG (10 capítulos + portada + biblio + figuras) fusionado — `4f10914`. Tag `demo-estable` = versión demostrable congelada. Zip de Overleaf enviado (queda OBSOLETO tras la Fase 2).
- Roadmap reestructurado (Fase 2 ampliada; antiguas 5+6 fundidas; 3/4/7/8 → 5/6/4/7; trazabilidad 91/91) — `85e98ba`.
- Planificación completa de la Fase 2: `02-CONTEXT.md` `f5d65e7`, `02-UI-SPEC.md` verificado 7/7 `e548a2e`, `02-RESEARCH.md` `a78510f`, `02-VALIDATION.md` `53b173f`, `02-PATTERNS.md` `df45a33`, `02-COVERAGE.md` `15006b3`.
- **13 PLAN.md en 6 olas** `8429926`/`86f4a68`; `gsd-plan-checker` iteración 1 (1 blocker + 5 warnings) → revisión `15c1d4e`/`54d9cca` → iteración 2 **0 blockers**; 2 warnings advisory cerrados (`254f999`, `9ad347b`).

**Siguiente:** `/gsd-execute-phase 2`. Ejecuta las 6 olas por subagentes y **se detiene en 5 checkpoints de ratificación del autor**: allowlist de plataformas (02-01), RAWG sí/no con cobertura medida (02-02), parámetros del protocolo congelado + rejilla de tuning (02-08, one-way), arquetipos de usuario sintético (02-09), numpy ahora vs Fase 3 (02-10). Detalle completo en `.planning/phases/02-.../.continue-here.md`.

Progreso global: 2/8 fases (25%).

## Performance Metrics

**Velocity:**

- Total plans completed: 46
- Average duration: 25 min
- Total execution time: 25 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 16 | - | - |
| 2 | 13 | - | - |
| 06 | 10 | - | - |
| 7 | 7 | - | - |

**Recent Trend:**

- Last 5 plans: 01-01 (25 min)
- Trend: baseline established

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 25 min | 2 tasks | 7 files |
| Phase 01 P05 | 45min | 2 tasks | 5 files |
| Phase 01 P06 | 17min | 2 tasks | 15 files |
| Phase 01 P15 | 25min | 2 tasks | 12 files |
| Phase 01 P04 | 44min | 2 tasks | 30 files |
| Phase 01 P07 | 20min | 3 tasks | 16 files |
| Phase 01 P08 | 15min | 1 tasks | 10 files |
| Phase 01 P16 | 8min | 2 tasks | 3 files |
| Phase 01 P09 | 20min | 2 tasks | 22 files |
| Phase 01 P10 | 10min | 1 tasks | 2 files |
| Phase 01 P11 | 55min | 2 tasks | 6 files |
| Phase 01 P12 | 2 sessions | 2 tasks | 9 files |
| Phase 01 P14 | 1 session | 1 tasks | 4 files |
| Phase 02 P08 | 18 min | 3 tasks | 12 files |
| Phase 02 P02 | ~80 min | 3 tasks | 7 files |
| Phase 06 P00 | 10min | 2 tasks | 4 files |
| Phase 06 P02 | 35min | 3 tasks | 10 files |
| Phase 06 P05 | 25min | 2 tasks | 8 files |
| Phase 06 P04 | 1h+ | 3 tasks | 11 files |
| Phase 06 P06 | 45min | 2 tasks | 12 files |
| Phase 06 P07 | 12min | 2 tasks | 8 files |
| Phase 06 P09 | 30m | 3 tasks | 6 files |
| Phase 07 P00 | 18 min | 3 tasks | 4 files |
| Phase 07 P01 | 26 min | 3 tasks | 12 files |
| Phase 07 P02 | 35min | 3 tasks | 32 files |
| Phase 07-research-panel-hardening-and-evidence-freeze P03 | 2h 00m | 3 tasks | 20 files |
| Phase 07 P04 | 75 | 3 tasks | 17 files |

## Accumulated Context

### Estado actualizado — 2026-09-09

La importación IGDB y la sincronización DLC/expansiones terminaron con política
aditiva. El corpus activo `2026.09.2` contiene `190479` obras visibles y `13618`
candidatas derivadas; ratings y PopScore están congelados y el PopScore compuesto
está materializado para `9929` obras. No se han ejecutado rankings ni evaluaciones.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- [Phase 1]: Ship a controlled, lawful, public vertical demo within three days; explicitly treat it as demo-grade.
- [Phases 2-8]: Harden data, evaluation, product, security, accessibility, operations, and evidence incrementally.
- [All phases]: Thesis and agent-methodology evidence is a continuous acceptance criterion.
- [Phase 01]: Next.js fijado a 16.3.4 tras rechazar el lock vulnerable de 16.2.12.
- [Phase 01]: Toda dependencia directa requiere pin exacto, evidencia oficial y aprobación humana.
- [Phase 01]: Replaced the fabricated Wikidata QID list in scripts/acquire_catalogue.py with a class-filtered live query (wdt:P31 wd:Q7889) plus dynamically-resolved platform sub-queries; fixed a URL-decoding bug that silently defaulted every cover image to placeholder. — The pre-existing hand-typed QID list contained non-video-game entities (a commune, an organ, a war); any hardcoded Wikidata QID must be verified live before use, never trusted from memory or a prior commit.
- [Phase 01]: Added dev-only Docker bind mounts (infra/compose.yaml) and fixed apps/api/pytest.ini's missing DJANGO_SETTINGS_MODULE -- both were silently breaking every future plan's docker compose run/pytest verification, not just plan 01-06's. — Without a bind mount, docker compose run always tested whatever code existed at the last image build, never the current working tree; without DJANGO_SETTINGS_MODULE actually loaded inside the container, any Django-DB test would fail to configure Django at all. Fixing both now prevents every subsequent plan in the phase from hitting the same wall.
- [Phase 01]: Scoped e2e/demo-journey.spec.ts (Plan 01-15 Task 2) to only what is verifiable without a login UI: the credential-contract (env-only, redacted-on-missing). The real browser login journey is an explicit test.describe.skip deferred to Plan 01-04, which also declares this file and will add the login page/endpoint. — Neither the Next.js login page nor the Django accounts login endpoint exist yet at Wave 4 -- both are Plan 01-04 deliverables (Wave 5). Fabricating a login test against non-existent infrastructure would be dishonest; the file is explicitly built incrementally across the two plans instead.
- [Phase 01]: Ran the plan 01-04 vertical tracer against the real stack (not just unit tests) and found/fixed 8 real infrastructure bugs: missing Docker port mappings, a Next.js rewrite trailing-slash redirect loop, a Django CSRF Origin mismatch through the same-origin proxy, dev-mode HMR hydration failure that let the login form leak credentials via URL query string, a locale-blind post-login redirect, and an incomplete middleware public-path list. Switched infra/compose.yaml's web service from `next dev` to a production build+start as the fix for the HMR issue. — None of these were found by unit tests alone -- they only surfaced when the full login->catalogue->status journey was actually driven through a real browser via Playwright, which is exactly what a type="tracer" plan exists to catch before six more waves build on top of a broken foundation. The production-build switch also better matches the project's own stated reproducibility principle (same commit/lockfiles build local and deployed).
- [Phase 01]: Resolved PROF-02's flagged assumption for Phase 1: every account is public by design (small controlled demo, no privacy toggle yet). The public profile serializer is a hand-built allowlist (never DRF ModelSerializer auto-introspection), verified by a recursive denylist scan plus hostile-fixture XSS tests. — Building the allowlist by hand means a new private model field requires an explicit decision to expose it, not an accidental one to hide it -- the opposite failure mode of auto-serialization. Phase 1's no-privacy-toggle choice keeps the "unauthorized vs nonexistent" indistinguishability requirement trivially satisfied (both cases collapse to the same 404 today) while leaving the response shape ready for a future toggle without a rewrite.
- [Phase 01]: Found Tailwind CSS had been a devDependency since Plan 01-03 but was never actually wired up (no postcss.config.mjs anywhere) -- added it as part of building the design token system. Also found and fixed a completely unconfigured Vitest path alias. — Both were genuine blocking gaps for this plan's own deliverables (globals.css's first @import line, and the i18n parity test's own @/ imports), not scope creep -- discovered only because this plan was the first to actually exercise either piece of tooling.
- [Phase 01]: Wired every UI-SPEC page (homepage, catalogue, detail, collection, profile, sources) to real backend data via GameCard/LibraryControls/RecommendationStrip, adding two new backend endpoints (MyLibraryView, SourcesView) the plan's file list didn't explicitly name but the pages genuinely needed to function. — Ten requirements (AUTH-01, PROF-02, CAT-01, CAT-03, CAT-06, LIB-01, LIB-02, INV-01, INV-02, REC-02) reached their last declaring plan here and are now marked complete -- the E2E suite proves rating and multi-copy persistence across a reload, not just the status field the earlier tracer plan covered, which is what closes out LIB-01/LIB-02/INV-01/INV-02 for real rather than by inference.
- [Phase 01]: Injected axe-core's already-approved local bundle directly via page.addScriptTag instead of adding the @axe-core/playwright wrapper package — Avoids a new-dependency approval round for what is functionally one line of glue code around an already-approved devDependency
- [Phase 01]: Introduced DJANGO_DEPLOY_ENV (local|production) to make check --deploy genuinely clean in each context via SILENCED_SYSTEM_CHECKS, instead of always showing expected-but-scary HTTP-only warnings — An explicit, required switch is auditable in a way that inferring the security profile from DEBUG or DATABASE_URL is not
- [Phase 01]: check-secrets.ps1 exempts only e2e/fixtures/hostile.json (holds the self-test canaries) and test files (assigned-secret-value/bearer-token patterns only) by path, never any file by content — Synthetic, reviewed fixture credentials are a normal testing pattern; a narrow, documented path exemption keeps every other file -- including README.md and .env.example -- genuinely scanned
- [Phase 01]: Pivoted the deployment topology mid-plan from a single-PaaS assumption to Vercel Hobby (web) + Render Free (api) + Neon Free (db), no card — Render Free's Docker-only model does not host two independently-scaled services plus a managed Postgres for free; the pivot keeps the same same-origin-proxy security architecture across two separately-hosted services
- [Phase 01]: Found and fixed three real deploy-path bugs (missing docs/ in the API image, non-portable random GameWork.id in the demo seed, /health/ redirected by Next.js middleware) plus a Vercel Hobby private-repo commit-author gotcha, each only visible against genuinely fresh infrastructure — The long-lived local dev Postgres volume masked two of these for the whole session; testing against a throwaway fresh container before every push is now the standing verification pattern for any fresh-database code path
- [Phase 01]: Deliberately left QUAL-03 open despite the tool reporting it structurally ready to mark complete -- the sign-off document explicitly states 400% zoom reflow and a screen-reader pass are still unverified manual checklist items — Marking a requirement complete when its own sign-off evidence names an open gap would misrepresent the actual state; readiness-to-mark-complete is structural (all declaring plans have summaries), not a substitute for checking the requirement's real acceptance criteria
- [Phase 01]: Phase 1 (Three-Day Public Demo Slice) ACCEPTED by the author, 2026-09-05, against commit 1af981e at https://save-point-orpin.vercel.app — All five ROADMAP success criteria linked to evidence in docs/verification/phase-01-signoff.md; two named open limitations (400% zoom, screen reader) stated rather than hidden
- [Phase 01.1]: IGDB v4 chosen as the real-scale catalogue source (ADR-006, DATA-04), over RAWG and scaled Wikidata, from a live authenticated probe (2026-09-05): 374,555 total games, 312,418 primary (game_type = 0), no monthly quota, 4 req/s + 8 concurrent. Import boundary is game_type = 0 only; covers are hotlinked to images.igdb.com (not mirrored) with the Phase 1 first-party placeholder as fallback; Phase 1's Wikidata offline corpus and the no-runtime-provider rule are retained. `requests==2.34.2` pinned (author-approved, PyPI-verified real release); django-allauth/dj-rest-auth explicitly rejected. The Twitch DSA (24h cache, no redistribution) is reconciled against IGDB's own API FAQ (store + serve permitted, keep after termination) treated as the "written authorization otherwise" the DSA contemplates — a reasoned position recorded verbatim for the thesis, not legal advice.
- [Phase 05]: Phase 6 confirma SOCIAL-03/04/05 como alcance social controlado y conserva SOCIAL-01/02 con su semántica v2.
- [Phase 05]: PROF-03 fija una allowlist exacta y D-07 como única excepción del perfil básico no-amigo; PROF-04 exige autorización server-side y 404 genérico.
- [Phase 05]: CAT-05 mantiene juegos, plataformas, ediciones, géneros, franquicias, desarrolladores, editoriales, fechas, modos y tags en el contrato backend aunque la selección visual quede abierta.
- [Phase 05]: CAT-05 usa filtros GET allowlisted y facets calculados antes de paginar, con orden determinista y slugs desconocidos ignorados.
- [Phase 05]: Publisher solo se enriquece desde snapshots locales APPROVED con SHA-256 y procedencia; Edition permanece anidada bajo GameRelease.
- [Phase 06]: La UI de catálogo usa los nombres exactos del contrato CAT-05 y mantiene filtros, orden y paginación en GET SSR.
- [Phase 06]: Los controles de facets solo presentan opciones procedentes del API local y no invocan proveedores externos.
- [Phase 06]: Las recomendaciones solo se crean entre amistades aceptadas y el receptor se deriva por alias único sin IDs de identidad alternativos.
- [Phase 06]: El cooldown direccional usa una ventana exacta de siete días y responde 429 con Retry-After de forma fail-closed.
- [Phase 06]: Remove/block convierten mensajes en tombstones mínimos y los comentarios aplican la policy antes del queryset.
- [Phase 06]: El frontend normaliza proyecciones basic/protected y mantiene al backend como autoridad de privacidad.
- [Phase 06]: Las acciones sociales usan rutas separadas, CSRF, busy por fila y confirmaciones accesibles.
- [Phase 06]: La bandeja social usa DTOs allowlisted, Cookie/no-store en SSR y CSRF same-origin en mutaciones; el backend conserva la autoridad de privacidad y cooldown.
- [Phase 06]: AccountSwitcher refleja el aggregate autenticado de pendientes con texto accesible y punto rojo, y se sincroniza tras mark_read.
- [Phase 06]: Se cierra el gate de backend y evidencia con PostgreSQL 18.6, snapshots inmutables y sin relanzar evaluación offline.
- [Phase 06]: Los journeys browser quedan diferidos de forma explícita cuando el entorno Compose no aporta e2e/configuración y el journey social no dispone de variables runtime.
- [Phase 07]: La identidad histórica v15 declarada por el artefacto es la autoridad de publicación; el protocol.json posterior solo aporta anclajes compartidos y nunca recalcula cifras.
- [Phase 07]: Las métricas catalogue_coverage, concentration_hhi y prediction_coverage se exponen como null por cohorte con explicación porque el snapshot las declara run-level-only.
- [Phase 07]: El entorno histórico ausente permanece como null y las exportaciones backend usan únicamente proyecciones allowlisted.
- [Phase 07]: Research Viewer se resuelve en cada endpoint con evaluation.view_research_panel mediante has_perm; Platform Admin conserva una capability separada.
- [Phase 07]: La API consume únicamente la publicación v15 inmutable y sus exportaciones saneadas; no recalcula rankings ni expone per_user, logs, dumps o secretos.
- [Phase 07]: El parámetro export format queda bajo la allowlist de Django y URL_FORMAT_OVERRIDE de DRF permanece desactivado para evitar negociación no controlada.
- [Phase 07]: [Phase 07 Plan 02]: Platform Admin usa exclusivamente evaluation.access_platform_admin; no se autoriza por is_staff, auth.change_user, cookies, nombres o frontend.
- [Phase 07]: [Phase 07 Plan 02]: La privacidad normal es desactivar y anonimizar; el borrado irreversible exige superusuario, confirmación exacta y auditoría previa.
- [Phase 07]: [Phase 07 Plan 02]: AuditEvent es allowlisted y append-only mediante trigger PostgreSQL, sin payload libre ni PII.
- [Phase 07]: La UI del panel delega autorización, métricas, orden y serialización al backend y expone filtros GET allowlisted.
- [Phase 07]: La imagen web fija las bibliotecas Debian y Chromium de Playwright para ejecutar la suite sin dependencias globales.
- [Phase 07]: Phase 07-04: imports use preview SHA-256 digests and atomic idempotent apply
- [Phase 07]: Phase 07-04: PostgreSQL backups use private manifests, 7 daily/4 weekly retention, and disposable restore only

### Pending Todos

- **RAWG pasada 2** (ratificado por el autor, 2026-09-07) — segunda pasada de
  `enrich_rawg_ratings` sobre juegos con `rating IS NULL` y `first_release_date` en
  2022-2026, ordenados por popularidad (`total_rating_count` → `rating_count` →
  recientes), `--limit 20000` hasta agotar cuota. Necesita flags nuevos
  (`--only-unrated`, `--release-year-min/max`, `--order-by popularity`) + tests +
  enmienda a ADR-008. Motivo del autor: "máxima cantidad de datos ahora; el resto se
  rellena con otras APIs al final". Spec completa en
  `.planning/phases/02-.../02-02-RATINGS-FOLLOWUP.md`.
- **Verificación del import IGDB** (petición del autor, 2026-09-07) — RESUELTA en 02-02:
  consulta directa a BD confirma el import `complete` (312.560 obras, cursor 416.648),
  sin franjas sin campos ampliados. El 13,933 % es la densidad real de rating de usuario
  de IGDB, no un hueco del import. No hay nada que reimportar.

### Blockers/Concerns

- Phase 1 must fit the three-day demo constraint; keep seeded accounts/catalogue and popularity logic intentionally thin.
- Phase 2 must freeze the evaluation protocol before sophisticated recommender comparisons. — DONE (Plan 02-08, 2026-09-07): `docs/methodology/protocol.json` is checked in and `evaluation/protocol.py` refuses to run on a >24 grid or a consumed test split. 02-09/02-10/02-11/02-13 build on it.
- Dataset and enrichment-provider legal terms require case-specific confirmation before adoption. — IGDB terms captured verbatim and reconciled in ADR-006 / docs/verification/igdb-api-probe.md §5 (2026-09-05). RAWG Free API terms (non-commercial, attribution + backlink, 20k req/month, no redistribution) recorded in ADR-008; the authenticated N=10.000 run (2026-09-07) stayed well under quota with no 429s. The FAQ-vs-DSA reading is a reasoned position for the author to accept, not legal advice; Wikidata terms remain as previously recorded.
- RAWG rating coverage is low: the top-10.000-by-`rating_count` slice added 0 net new coverage (those works already had IGDB ratings). Net coverage stays 13,933 %. RAWG pasada 2 (unrated + 2022-2026, by popularity) is the queued mechanism to raise it; other APIs will fill the remainder later.
- Pre-existing defect (logged, deferred): 22 RAWG game ids reconcile to 2 governed works each; `SourceRecord.update_or_create(source, source_id)` overwrites the shared row's `work` FK. Ratings data is correct (each work keeps its own immutable snapshot); only RAWG provenance for those 22 rows (0,26 %) is imprecise. Fix is a provenance-schema change — see `.planning/WINDOWS.md`.
- Plan 01-04 (Wave 5) is mid-execution and paused on a real blocker: the frontend (apps/web) was scaffolded in Plan 01-03 WITHOUT @types/react or @types/react-dom in devDependencies. Re-enabling TypeScript build-error checking (next.config.ts's ignoreBuildErrors:true was itself a bug, now removed) surfaces this immediately -- every .tsx file in apps/web fails to type-check (useState/FormEvent not found on 'react', JSX.IntrinsicElements missing, react/jsx-runtime has no types).

Per project policy (01-01's package-legitimacy gate; deviation Rule 3's explicit exclusion for package-manager installs), a new dependency install requires human sign-off, not an agent's unilateral pnpm add -- even though @types/react and @types/react-dom are about as standard/low-risk as a package gets.

WHAT'S DONE (committed, tested, working): apps/api/accounts/{views,urls}.py + test_auth.py (7/7 passing), apps/api/library/{views,urls}.py + test_entry.py (8/8 passing), config/urls.py wiring, infra/compose.yaml port mappings (web:3000, api:8000) and demo env vars. Full backend suite: 62/62 passing.

WHAT'S UNCOMMITTED (working tree, not yet type-checked clean): apps/web/app/[locale]/** (layout, homepage, login page, catalogue page, game detail page + StatusControl), apps/web/lib/api.ts, apps/web/middleware.ts, apps/web/next.config.ts (rewrite proxy to Django + ignoreBuildErrors removed), and the deletion of the old flat apps/web/app/layout.tsx + page.tsx (replaced by the [locale] structure).

TO RESUME: get the user's explicit approval, then `pnpm add -D @types/react@<version matching react 19.2.7> @types/react-dom@<matching>` at the repo root (deps are hoisted there, see package.json), run `pnpm exec tsc --noEmit` in apps/web to confirm the errors clear, then continue: verify the dev server actually renders each page, write/run the e2e/demo-journey.spec.ts real login journey (replacing the 01-15 skip block), run the plan's two <verify> commands, then close out Plan 01-04 (SUMMARY.md, STATE/ROADMAP/REQUIREMENTS updates) exactly like 01-05/01-06/01-15 before it.

- 07-04 restore mensual desechable no verificable: el dump copia y checksum pasan, pero accounts.0004_phase7_anonymization falla con UniqueViolation por admin_uuid duplicado; requiere corregir dump/fixture o migracion propietaria.

## Tareas rápidas completadas

| Fecha | Tarea | Resultado |
|---|---|---|
| 2026-09-07 | Incorporación de la documentación de la Fase 2 en la memoria LaTeX | Protocolo, ratings, corpus gobernado, algoritmos y decisiones previas al laboratorio documentados; compilación pendiente de entorno TeX |
| 2026-09-07 | Revisión académica y corrección de la memoria LaTeX | Tablas adaptables, prosa y referencias revisadas; compilación pendiente de entorno TeX |
| 2026-09-09 | Actualización de rejillas y contrato de señales de la Fase 3 | Rejilla de 24 configuraciones; `recency-v1` combina las señales base y recencia; snapshot, hashes, protocolo y documentación actualizados; sin ejecutar algoritmos |
| 2026-09-09 | Corrección y regeneración de población sintética de Fase 3 | Los 400 usuarios nuevos sustituyen a los 200 heredados como población activa; split 240/80/80, cohortes 10/100/240/50 y sesgo escalonado por `rating_count >= 1` verificados en BD; sin ejecutar algoritmos |

| 2026-09-09 | Manifiesto, aislamiento y auditoría de señales de Fase 3 | Manifiesto hash-pinned de 400 usuarios; 200 históricos preservados sin solapamiento; split 240/80/80 verificado; cobertura y política de nulos de todas las señales documentadas; sin ejecutar algoritmos |

| 2026-09-09 | Inclusión de franquicia IGDB como saga | `franchise` se incluye como dimensión de `fs-v4` aunque su cobertura sea 6,07 %; se omite solo por obra cuando falta; auditoría y pruebas actualizadas; sin ejecutar algoritmos |

| 2026-09-09 | Validación y archivo previos a algoritmos | PASS: corpus/candidatos, población 400/200, split 240/80/80, rejilla 24, rating de usuario y recencia validados; resultados archivados; sin ejecutar algoritmos |

| 2026-09-09 | Integración del runner y métricas pendientes | Runner con métricas beyond-accuracy, hash de PopScore, valores por usuario y evidencias del corpus integrados; 120 tests pasados; caché fs-v4 documentada; sin ejecutar algoritmos |

| 2026-09-09 | Reconstrucción de caché fs-v4 | 190.479/190.479 vectores materializados; 186.211 creados, 4.268 actualizados, 0 ausentes; evidencia archivada; sin ejecutar algoritmos |

| 2026-09-09 | Enmienda del contrato visual de recomendaciones | Página definida con cinco variantes de contenido, heurística por género y DLC; cada variante tendrá explicación breve y señales visibles; sin ejecutar algoritmos |

| 2026-09-09 | Separación del rating visible y los algoritmos | `display_rating` mantiene la fórmula combinada IGDB+SavePoint solo para la presentación; tarjetas y ficha coinciden; 60 pruebas backend y 16 frontend correctas |

| 2026-09-09 | Umbral común de candidatos para web y offline | El corpus conserva 190.479 obras y los algoritmos comparten 13.618 candidatas con `rating IS NOT NULL AND total_rating_count >= 5`; snapshot hash actualizado, protocolo v6 y preflight PASS; sin ejecutar rankings ni evaluación |

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| Hardening | Production-strength controls beyond the Phase 1 demo boundary | Planned | Roadmap creation | v1 |
| Evaluation | Real-user study (20 users, own libraries, survey-based quality evaluation) after the synthetic-population offline study closes; own frozen corpus snapshot, not comparative with the synthetic-population metrics. Not yet a numbered/scheduled phase. | Noted, not planned | 2026-09-11 (author decision) | v1 |

## Tarea rápida completada — 2026-09-09

Se añadieron cuatro variantes PopScore con suelo mínimo explícito, preservando
los baselines. Web y offline comparten la misma arquitectura y pesos; se
incorporaron cuatro workers y cuatro estanterías, y `recency-v1` adoptó también
la imputación mínima. El protocolo pasó a v4 con rejilla de 28 configuraciones.
Ver `.planning/quick/260909-nej-a-adir-cuatro-variantes-popscore-con-imp/`.

## Registro histórico de sesiones (prevalece el checkpoint de ejecución actual)

**Stopped at:** Completed 07-04-PLAN.md

**Resume (after the rate-limit reset):** `/gsd-plan-phase 2` re-spawns the planner from scratch. All inputs are committed: `02-CONTEXT.md`, `02-UI-SPEC.md` (verified 7/7), `02-RESEARCH.md`, `02-VALIDATION.md`, `02-PATTERNS.md`, `02-COVERAGE.md`. Then `gsd-plan-checker` → revision loop → present → `/gsd-execute-phase 2`. Full detail in `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/.continue-here.md`.

Last session: 2026-09-14T01:29:13.515Z

### Done this session (2026-09-06, all committed on `main`)

- **01.1 post-close correction (batch 1)** — `2bfbfe2`: login CTA removed from the home hero; registration returns the concrete `password_errors` list; login username matching made case-insensitive; new `GET /api/accounts/me/` (`MeView`). 80 accounts tests + 16 web tests + tsc green. `deferred-items.md` updated, D-01.1-13-b resolved.
- **TFG LaTeX draft** — `4f10914`: 10 chapters + front matter + bibliography + 18 app screenshots + code listings, merged from a worktree agent. Follows the author/supervisor rules and the professor style rules. Pending author items marked with `\todo` and listed in `thesis/README.md`. Overleaf zip sent (now OBSOLETE — regenerate after Phase 2 with its algorithms + decisions folded in). Tag `demo-estable` = frozen demoable version.
- **Roadmap restructure** — `85e98ba`: Phase 2 enlarged (governed corpus + external ratings + evaluation contract + first advanced recommender + search/filters + UI pass); former phases 5+6 merged; 3/4/7/8 renumbered to 5/6/4/7. Requirement coverage 91/91.
- **Phase 2 planning inputs** — `02-CONTEXT.md` `f5d65e7` (discuss-phase, D-01..D-24), `02-UI-SPEC.md` `e548a2e` (ui-phase, checker 7/7, `## UI Considerations` 45 explicit + 10 backstop), `02-RESEARCH.md` `a78510f`, `02-VALIDATION.md` `53b173f`, `02-PATTERNS.md` `df45a33`, `02-COVERAGE.md` `15006b3` (rescued from the rate-limited planner).

Resume file: None

## Session Continuity

Last session: 2026-09-07

Stopped at: Phase 7 complete — all phases complete
blocking-human checkpoint: IGDB final governed-corpus user-rating coverage measured at
13,933 % (27.014/193.885); awaiting author decision to run the bounded RAWG enrichment
(N=10000) or record IGDB-only in ADR-008. RAWG code + ADR committed in wip commit a718e8d.

Resume file: .planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/.continue-here.md
Handoff: eliminado tras la reanudación; el checkpoint de Fase 3 sigue en `.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/.continue-here.md`

## Continuidad de esta sesión

Último estado comprobado: **Fase 3 preparada para ejecución** (2026-09-08). Los cuatro
planes están creados, validados y enlazados a sus issues: `03-01` → #42, `03-02` → #41,
`03-03` → #39 y `03-04` → #40. Los cuatro elementos están en el board SavePoint con estado
`Todo`.

La autenticación de GitHub CLI funciona desde el contexto elevado necesario para el keyring y
el scope `project` está concedido. No se han publicado credenciales ni logs sensibles.

Siguiente acción: ejecutar `/gsd-execute-phase 3`, empezando por la Ola 1 (`03-01`).

## Tarea rápida completada — 2026-09-09

Se adoptó el diseño de caché personal stale-while-revalidate en
`.planning/quick/260909-asynchronous-recommendation-cache/`: snapshots y cola durable en
PostgreSQL, worker independiente, endpoint no bloqueante y cinco secciones de recomendaciones
con explicación localizada. Redis queda pospuesto hasta disponer de una medición de latencia o
concurrencia que justifique añadirlo. No se ejecutaron algoritmos experimentales.

## Tarea rápida completada — 2026-09-09

La colección y la continuación de la portada muestran `display_rating` mediante
la respuesta owner-scoped de biblioteca, manteniendo separadas las estrellas
personales. Ver resumen en `.planning/quick/260909-mdo-a-adir-display-rating-a-las-tarjetas-de-/`.

## Tarea rápida completada — 2026-09-09

Web y offline comparten la señal compuesta `rating_confidence`: rating IGDB con
potencia 2 y volumen `total_rating_count` normalizado como refuerzo acotado del
20 %. La rejilla y el contrato offline se actualizaron a protocolo v3. Ver
resumen en `.planning/quick/260909-msb-reforzar-rating-igdb-y-volumen-de-valora/`.

## Tarea rápida completada — 2026-09-09

Se reforzó la intensidad de las valoraciones personales de los juegos semilla con una potencia
cuadrática y se sustituyó la semivida diaria de `recency-v1` por una decaída explícita por año
natural. Web, workers y offline comparten el cambio; el protocolo reproducible pasó a v5. No se
ejecutaron algoritmos experimentales. Ver `.planning/quick/260909-o1u-reforzar-peso-de-valoraciones-personales/`.

## Tarea rápida completada — 2026-09-09

Se implementó `fs-v6`: similitud de género/plataforma como núcleo y bonus
personalizado de saga/desarrollador solo por coincidencia con el perfil. La
lógica es compartida por web, workers y offline; se materializaron 190.479
vectores, se reiniciaron los workers para cargar la nueva versión y los diez
jobs de `felipe` publicaron correctamente el snapshot `fs-v6`. 191 pruebas y
TypeScript pasan; no se ejecutó la evaluación de los 400 usuarios. Ver
`.planning/quick/260909-ptx-implement-fs-v6-facet-aware-content-simi/`.

## Tarea rápida completada — 2026-09-09

Se documentaron las decisiones de la jornada y se aplicó `fs-v7`: la similitud
de género/plataforma usa media armónica entre cobertura del perfil y precisión
del candidato; saga/franquicia y desarrollador pasan a pesos `0,18` y `0,12`,
con bonus opcional máximo `0,30`. La señal de rating observado es
`rating-confidence-v3`, sin dilución por el perfil medio del género. La caché
fs-v7 contiene 190.479 vectores y los diez workers de `felipe` publicaron la
revisión 14. Ver `docs/verification/jornada-decisiones-recomendacion-2026-09-09.md`
y `docs/verification/recommendation-fs-v7-felipe-2026-09-09.md`.

## Tarea rapida completada — 2026-09-09

Se publico `fs-v8` / `facet-similarity-v4`: saga/franquicia tiene bonus maximo
`0,20`, desarrollador `0,15`, y el nucleo genero/plataforma usa F0,5 para dar
mas peso a la precision del candidato frente a listas amplias de metadatos.
La cache contiene 190.479 vectores y los diez workers de `felipe` publicaron la
revision 14. Backend: 194 pruebas; TypeScript correcto. Se archivo la
comparacion fs-v8 entre Silksong y Terraria; no se ejecuto la evaluacion de los
400 usuarios. Ver `.planning/quick/260909-rnf-raise-saga-and-developer-optional-bonuse/`
y `docs/verification/recommendation-fs-v8-comparison-felipe-2026-09-09.md`.

## Tarea rapida completada — 2026-09-09

Se completo `fs-v9` / `facet-similarity-v5`: F0,5 queda congelado, saga usa
bonus maximo 0,02 y desarrollador 0,015. Ademas, PopScore se reforzo de forma
moderada: 0,20 en las variantes lineales y desempates, `swing = 0,20` en la
variante multiplicativa y 0,20 en Recency. El protocolo offline se versiono a
7 y web/offline comparten los pesos. Los diez workers de Felipe publicaron la
revision 14; la cache mantiene 190.479 vectores. Backend: 194 pruebas; web:
TypeScript correcto. Reevaluacion archivada en
`docs/verification/recommendation-fs-v9-comparison-felipe-2026-09-09.md`. No se
ejecuto la evaluacion offline de los 400 usuarios.

## Tarea rapida completada — 2026-09-09

La señal de calidad IGDB pasa a `rating-confidence-v4-bayesian`: media previa
del corpus congelado ponderada por `total_rating_count`, con 25
pseudo-observaciones y posterior potencia cuadrática. Sustituye el
multiplicador de volumen, sin cambiar candidatas, fs-v9 ni los pesos de los
algoritmos. El protocolo se elevó a v8; los diez workers paralelos de Felipe
terminaron y publicaron atómicamente la revisión 14. Backend: 195 pruebas;
TypeScript correcto. Ver
`.planning/quick/260909-tub-implement-a-reproducible-bayesian-rating/` y
`docs/verification/recommendation-bayesian-rating-felipe-2026-09-09.md`.

## Tarea rápida completada — 2026-09-09

Se añadieron exactamente dos variantes nuevas de reordenación MMR, sin cambiar
las nueve variantes publicables anteriores: `content-cbf-mmr-v1` parte de
Weighted y `content-cbf-mmr-pop-v1` parte de Weighted-Pop. Ambas comparten el
ranker entre web y offline, usan `lambda = 0,80` y coseno sobre fs-v9, tienen
worker y estantería propios, y publican 20 resultados. La rejilla queda en 30
configuraciones. Los 12 workers de Felipe terminaron en paralelo y publicaron
el snapshot `ddef6ae3-6795-4049-b105-5d389e53d1e2`, revisión 14. Ver
`.planning/quick/260909-udz-implement-two-shared-mmr-recommendation-/` y
`docs/verification/recommendation-mmr-felipe-2026-09-09.md`.

## Fase 4 — implementación preparada — 2026-09-09

Se incorporaron `cf-user-knn-v1` y `hybrid-weighted-cf-v1` a la arquitectura
web y offline, con workers y estanterías independientes. El protocolo pasa a
v9 y declara la ejecución paralela por algoritmo. La revisión 14 de Felipe
publicó 14 trabajos correctos y 13 estanterías personales con 20 resultados.
La evaluación de los 400 usuarios aún no se ha ejecutado; el comando
`run_evaluation_parallel` queda listo para hacerlo con tiempos individuales y
totales. Ver `.planning/phases/04-collaborative-and-hybrid-comparison/`.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260914-h0g | Construir inventario académico verificable para rehacer la memoria del TFG | 2026-09-14 | 2ad6e06 | [260914-h0g-construir-la-fase-a-de-la-nueva-memoria-](./quick/260914-h0g-construir-la-fase-a-de-la-nueva-memoria-/) |
| 260914-gdk | Sincronizar el vault de Obsidian y cerrar issues completadas | 2026-09-14 | c24784e | [260914-gdk-sync-obsidian-vault-and-close-completed-](./quick/260914-gdk-sync-obsidian-vault-and-close-completed-/) |
| 260909-wgm | Documentar la decisión de no implementar Item-KNN ni modelos complejos y definir hybrid-mmr-v1 como propuesta | 2026-09-09 | 1004ed9 | [260909-wgm-documentar-la-decision-de-no-implementar](./quick/260909-wgm-documentar-la-decision-de-no-implementar/) |
| 260909-ws8 | Implementar hybrid-mmr-v1 y adoptar rating_final compartido en web y offline | 2026-09-10 | 2c12838 | [260909-ws8-implementar-hybrid-mmr-v1-en-web-y-offli](./quick/260909-ws8-implementar-hybrid-mmr-v1-en-web-y-offli/) |
| 260910-0u7 | Verificar la importación de facetas IGDB y dejar checkpoint para la interfaz | 2026-09-10 | a3f3a14 | [260910-0u7-verificar-importacion-de-facetas-igdb-y-](./quick/260910-0u7-verificar-importacion-de-facetas-igdb-y-/) |

Last activity: 2026-09-14 — Quick task 260914-h0g completado: inventario de fuentes y matrices verificados antes de reescribir la memoria

## Reconciliación de continuidad — 2026-09-12

La reanudación detectó que el `HANDOFF.json` anterior era histórico: indicaba que la
evaluación offline aún no había comenzado, pero la rama `main` ya contiene la ejecución
final del protocolo v15 y su documentación.

- `main` está limpio y sincronizado con `origin/main` en `1a00474`.
- La evaluación final del test v15 terminó con estado `succeeded`, 16/16 algoritmos,
  79 usuarios evaluables y el marcador de test consumido una sola vez.
- La evidencia canónica es
  `docs/verification/evaluation-results-400-test-2026-09-12-v15.md` y el checkpoint
  `docs/verification/evaluation-checkpoint-400-users-2026-09-12-v15.md`.
- El protocolo vigente es v15 (`docs/methodology/protocol.json`); no se debe relanzar
  el test ni modificar el marcador para continuar el trabajo documental.
- Fase 4 tiene `04-01-SUMMARY.md`, `04-02-SUMMARY.md` y `04-03-SUMMARY.md`. Fase 3
  ya tiene `03-03-SUMMARY.md` y `03-04-SUMMARY.md`, con el cierre backend/documental
  y las limitaciones de semillas/UI reconciliadas contra la evidencia v15. No se
  reejecutan cálculos.

**Siguiente acción:** comenzar la planificación de la Fase 5; las Fases 3 y 4 quedan
cerradas con sus firmas y la limitación multi-semilla documentada.

## Cierre Fase 3 — 2026-09-12

Se ejecutó el cierre backend/documental de la Fase 3 sin repetir el cálculo v15. Se
añadieron los resúmenes `03-03-SUMMARY.md` y `03-04-SUMMARY.md`, el comando de análisis
por cohortes y la captura futura de entorno/recursos del runner paralelo. El informe
derivado confirma 79 usuarios evaluables del test dentro de la cohorte
`active_history_10_to_20`; los 10 usuarios `no_history` quedan correctamente fuera de
un ranking personalizado.

El punto 6 (múltiples semillas) queda registrado como limitación metodológica: el test
v15 es de un solo consumo y repetirlo exigiría un nuevo protocolo versionado, población,
split y artefacto. El bootstrap y los contrastes pareados describen incertidumbre
interna del run, pero no sustituyen un estudio de sensibilidad entre semillas.

El punto 7 (UI/E2E) queda cubierto por `e2e/recommendations.spec.ts` y su evidencia
registrada en el vault. Esta sesión no modificó `apps/web/**` ni `design/**`; la
implementación y sus pruebas pertenecen a la otra sesión, pero `QUAL-02` ya queda
integrado en el cierre documental.

La firma formal queda en `docs/verification/phase-03-signoff-2026-09-12.md`.

## Cierre Fase 4 — 2026-09-12

La Fase 4 queda completada con limitación metodológica explícita. Sus tres planes
están resumidos, verificados y enlazados a las issues #44, #45 y #46.

- `cf-user-knn-v1` y `hybrid-weighted-cf-v1` comparten candidatos, exclusiones,
  DTOs, fallbacks y protocolo con los algoritmos anteriores.
- La web dispone de workers y estanterías independientes; la verificación de
  Felipe confirmó 14 trabajos correctos y 20 resultados por sección nueva.
- El runner offline registra procesos, hashes, estados, tiempos individuales y
  tiempo de pared. El artefacto v15 contiene 16/16 algoritmos y 79/80 usuarios
  evaluables.
- REC-04, REC-05 y DOC-03 pasan a estado completo en la trazabilidad.

La evidencia canónica está en `04-VERIFICATION.md`,
`docs/verification/phase-04-signoff-2026-09-12.md` y los resultados v15. No se
relanza el split `test`: la ejecución fue única y la ausencia de multi-semilla
se registra como limitación, no como un resultado no observado.
