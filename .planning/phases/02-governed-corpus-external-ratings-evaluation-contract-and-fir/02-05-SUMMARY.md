---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 05
subsystem: api
tags: [django, drf, serializers, catalogue, ratings, dlc, new-releases, d-09, d-15, d-24]

requires:
  - phase: 02-01
    provides: "governed_works() / GameWork.in_corpus / corpus_version / CorpusRatingSnapshot"
  - phase: 02-02
    provides: "GameWork.rating / rating_count / summary (campos de usuario de IGDB) + snapshots insert-only"
  - phase: 02-03
    provides: "governed scoping en catalogue/search.py; sort=rating_desc / min_rating sobre total_rating"
provides:
  - "GameDetailSerializer ampliado: summary (IGDB), rating / rating_count de usuario de IGDB, display_rating, rating_breakdown; la procedencia prefiere el SourceRecord source=igdb"
  - "GameCardSerializer: display_rating (numero de producto D-09, null = sin valoracion); total_rating se mantiene como clave de sort/min_rating (flagged assumption 2)"
  - "NewReleasesView + GET /api/catalogue/new-releases/ (D-24): obras gobernadas de los ultimos ~6 meses, first_release_date desc + canonical_slug, [:20], ventana vacia -> []"
  - "OwnedGamesDlcView + GET /api/catalogue/owned-dlc/ (D-15): IsAuthenticated, request.user-only, DLC/expansiones de juegos base en biblioteca agrupados por juego base, proyeccion allowlist-echo, DLC fuera del corpus gobernado se devuelven igual"
  - "catalogue/ratings.py::display_rating(work) (D-09) — mezcla ponderada por confianza de rating externo IGDB + media de LibraryEntry.rating_half_steps x10 restringida al mismo conjunto de cuentas que rank_popularity_v1; nunca lee CorpusRatingSnapshot"
  - "catalogue/ratings.py::rating_breakdown(work) -> {igdb_count, savepoint_count} (solo agregados) y savepoint_rating_stats() para render de listas query-bounded"
affects: [02-06, 02-12, thesis-data-chapter, recommender]

actuals:
  tokens: 8000
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Numero de rating de producto (vivo, mezclado, por request) separado del rating de investigacion (CorpusRatingSnapshot, externo-only, congelado por corpus_version): display_rating no toca ninguna fila de snapshot"
    - "Reutilizacion del filtro anti-contaminacion de rank_popularity_v1 (Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)) como contrato compartido para agregados publicos/vivos"
    - "Proyeccion allowlist-echo por tuplas de campos en vistas nuevas (patron de recommendations/views.py) — nunca ModelSerializer introspectivo"
    - "Stats agregadas en bloque (savepoint_rating_stats) pasadas por serializer context para que un listado de tarjetas no escale queries con las filas"

key-files:
  created:
    - "apps/api/catalogue/ratings.py (display_rating, rating_breakdown, savepoint_rating_stats)"
    - "apps/api/catalogue/tests/test_new_releases.py"
    - "apps/api/catalogue/tests/test_owned_dlc.py"
    - "apps/api/catalogue/tests/test_display_rating.py"
  modified:
    - "apps/api/catalogue/serializers.py (summary/rating/rating_count/display_rating/rating_breakdown; procedencia prefiere IGDB)"
    - "apps/api/catalogue/views.py (NewReleasesView + NewReleasesThrottle, OwnedGamesDlcView, contexto de stats en GameListView)"
    - "apps/api/catalogue/urls.py (rutas new-releases/, owned-dlc/)"

key-decisions:
  - "display_rating: mezcla = (ext*w_ext + local*w_local)/(w_ext+w_local), w = min(max(n,1), 50); un valor presente pesa >=1 aunque su n sea 0/None; techo de confianza 50 para que ninguna fuente ahogue a la otra sin limite. El autor debe confirmar el reparto exacto (flagged assumption D-09 / RESEARCH Open Question 3)."
  - "rating_breakdown.igdb_count = 0 cuando work.rating is None (aunque rating_count tuviera valor): la variante de copy de la ficha se elige por 'conteo > 0' y no debe anunciar usuarios de IGDB sin numero mostrable."
  - "NewReleasesView responde una lista JSON desnuda (no {results: [...]}) porque el plan fija 'ventana vacia -> []' en must_haves, behavior y acceptance_criteria."
  - "NewReleasesThrottle: subclase de SimpleRateThrottle con scope propio (catalogue_new_releases) y rate explicito 120/min en la clase, para no editar config/settings.py (fuera del limite de ficheros de este plan en modo worktree)."
  - "La procedencia de la ficha prefiere el SourceRecord source=igdb y cae al primero disponible; conserva el comportamiento del test heredado (source unico wikidata)."

patterns-established:
  - "catalogue/ratings.py como unico hogar del rating de producto D-09; el harness/recomendador siguen leyendo CorpusRatingSnapshot, nunca este modulo"
  - "Vistas de estante (NewReleasesView, OwnedGamesDlcView) con proyeccion allowlist-echo explicita y, para listas, contexto de stats en bloque"

requirements-completed: [DATA-05, QUAL-05, DATA-07]

coverage:
  - id: D1
    description: "GameDetailSerializer expone summary (IGDB), rating y rating_count de usuario de IGDB, y retrieved_at/source de la procedencia (que ahora prefiere el SourceRecord IGDB)"
    requirement: "DATA-05"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_new_releases.py::test_detail_exposes_summary_rating_and_provenance_fields (+ test_detail_summary_is_empty_string_when_igdb_has_none, test_detail_prefers_the_igdb_source_record_for_provenance)"
        status: pass
    human_judgment: false
  - id: D2
    description: "GET /api/catalogue/new-releases/ (D-24): <=20 obras de governed_works() con first_release_date en los ultimos ~6 meses, orden first_release_date desc + canonical_slug; ventana vacia -> [] con 200; obra in_corpus=False o is_dlc=True nunca aparece"
    requirement: "QUAL-05"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_new_releases.py::{test_new_releases_returns_recent_governed_works_only,test_new_releases_excludes_dlc_even_if_recent_and_in_corpus,test_new_releases_orders_by_release_date_desc_then_canonical_slug,test_new_releases_empty_window_returns_empty_list_with_200,test_new_releases_caps_at_twenty_items}"
        status: pass
    human_judgment: false
  - id: D3
    description: "GET /api/catalogue/owned-dlc/ (D-15): IsAuthenticated, request.user-only (ignora ?user=), DLC/expansiones de juegos base en biblioteca agrupados por juego base con proyeccion allowlist-echo; child_work fuera de governed_works() se devuelve igual; sin DLC -> {groups: []} con 200"
    requirement: "QUAL-05"
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_owned_dlc.py (6 tests: auth 403, agrupado por base, base no poseido ausente, child ungoverned devuelto, grupos vacios, ?user= ignorado)"
        status: pass
    human_judgment: false
  - id: D4
    description: "display_rating (D-09): solo externo -> valor externo; externo + SavePoint -> mezcla ponderada por confianza estrictamente entre ambos; solo SavePoint restringido -> media local x10; sin fuente -> None; una LibraryEntry de cuenta NO restringida no mueve el numero; nunca lee CorpusRatingSnapshot (un cambio en display_rating no altera la fila de snapshot)"
    requirement: "DATA-05"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_display_rating.py::{test_external_only_returns_the_external_value,test_savepoint_only_returns_the_local_mean_times_ten,test_external_plus_savepoint_is_a_confidence_weighted_blend,test_no_source_with_data_returns_none,test_rating_from_a_non_restricted_account_does_not_move_the_number,test_display_rating_never_reads_the_corpus_rating_snapshot}"
        status: pass
    human_judgment: false
  - id: D5
    description: "rating_breakdown(work) -> {igdb_count, savepoint_count} expone solo conteos agregados, nunca filas por usuario; igdb_count = 0 sin rating externo; savepoint_count solo cuenta cuentas restringidas; cableado en el serializer de ficha"
    requirement: "DATA-05"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_display_rating.py::{test_rating_breakdown_reports_aggregate_counts_only,test_igdb_count_is_zero_when_there_is_no_external_rating,test_detail_endpoint_exposes_display_rating_and_breakdown}"
        status: pass
    human_judgment: false
  - id: D6
    description: "Composicion determinista de la mezcla D-09 (reparto externo vs local, techo de confianza) fijada en codigo y documentada; el snapshot de investigacion no participa (DATA-07, faceta de contrato de datos; DATA-07 tambien es propiedad de 02-13)"
    requirement: "DATA-07"
    verification:
      - kind: unit
        ref: "apps/api/catalogue/tests/test_display_rating.py::test_external_plus_savepoint_is_a_confidence_weighted_blend"
        status: pass
    human_judgment: true
    rationale: "El plan (flagged_assumptions) y 02-RESEARCH Open Question 3 delegan explicitamente en el autor el reparto exacto de pesos externo/local y si cuentan cuentas auto-registradas. Se implemento el contrato de must_haves (restringido a demo_anchor|demo_identity, peso proporcional a n acotado a 50); el autor debe confirmar que ese reparto es el que quiere defender en la tesis antes de que 02-06/02-12 lo consuman y 02-13 cierre DATA-07."

duration: 45min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 05: API de catalogo para el pase de UI Summary

**Serializer de ficha con sinopsis IGDB y desglose de rating de usuario, dos estantes nuevos (`new-releases` D-24 y `owned-dlc` D-15 owner-scoped) y un `display_rating` mezclado en vivo (D-09) que reutiliza la restriccion anti-contaminacion de `rank_popularity_v1` y nunca toca el snapshot de investigacion.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-09-07T (aprox., primer arranque del harness)
- **Completed:** 2026-09-07
- **Tasks:** 3 (tracer + 2 auto, todas TDD)
- **Files modified:** 7 (3 nuevos + 3 modificados + 1 SUMMARY)

## Accomplishments

- **Tarea 1 (tracer, `ee76b86` test / `a9b796c` feat):** `GameDetailSerializer` expone `summary`, `rating`, `rating_count` (usuario de IGDB) y la procedencia ahora prefiere el `SourceRecord` `source=igdb`. `GameCardSerializer` y la ficha exponen `display_rating` (null explicito = "sin valoracion"). `NewReleasesView` + `/api/catalogue/new-releases/`: `governed_works()` con `first_release_date >= hoy-183d`, orden `first_release_date` desc (`nulls_last`) + `canonical_slug`, `[:20]`, ventana vacia -> `[]`. `NewReleasesThrottle` con scope propio y rate en la clase (sin tocar `settings.py`). Gate de feedback del tracer: `<verify>` re-ejecutado end-to-end en verde antes de expandir.
- **Tarea 2 (`eeb0880` test / `18c654a` feat):** `OwnedGamesDlcView` + `/api/catalogue/owned-dlc/`. `IsAuthenticated`, deriva todo de `request.user` (sin parametro de usuario objetivo; un `?user=` se ignora). `RelatedContent.filter(parent_work_id__in=<library work ids>, relation__in=["dlc","expansion"])` agrupado por juego base, proyectado con tupla allowlist-echo (`base_game{slug,title}`, `dlc[{work_id,slug,title,cover,relation}]`). Los `child_work` fuera de `governed_works()` (`is_dlc=True` / `in_corpus=False`) se devuelven igual. Sin DLC resolubles -> `{"groups": []}` con 200.
- **Tarea 3 (`44d4e53` test / `818f68c` feat):** `catalogue/ratings.py::display_rating(work)` — mezcla ponderada por confianza de `work.rating` (0-100, peso `min(max(rating_count,1),50)`) y la media de `LibraryEntry.rating_half_steps` x10 restringida a `Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)` (peso `min(max(n,1),50)`). Sin ninguna fuente -> `None`. No lee `CorpusRatingSnapshot`. `rating_breakdown(work) -> {igdb_count, savepoint_count}` (solo agregados), cableado en el serializer de ficha. `savepoint_rating_stats()` calcula las medias/conteos locales de una pagina en una sola query, pasada por `context` del serializer.
- **Tests:** `test_new_releases.py` 9, `test_owned_dlc.py` 6, `test_display_rating.py` 9 -> **24 passed**. Regresion `pytest apps/api/catalogue -q` -> **109 passed**. Suite completa `pytest apps/api -q` -> **319 passed**.

## Task Commits

1. **Tarea 1: serializer ampliado + NewReleasesView (tracer, TDD)** - `ee76b86` (test) -> `a9b796c` (feat)
2. **Tarea 2: OwnedGamesDlcView owner-scoped (TDD)** - `eeb0880` (test) -> `18c654a` (feat)
3. **Tarea 3: display_rating mezclado en vivo + rating_breakdown (TDD)** - `44d4e53` (test) -> `818f68c` (feat)

**Plan metadata:** `<este commit>` (docs: cierre de plan, `Closes #21`)

## Files Created/Modified

- `apps/api/catalogue/ratings.py` (nuevo) - `display_rating`, `rating_breakdown`, `savepoint_rating_stats`, filtro `_REAL_ACCOUNT`, techo `_CONFIDENCE_CAP = 50`
- `apps/api/catalogue/serializers.py` - `summary`/`rating`/`rating_count`/`display_rating` (tarjeta+ficha) + `rating_breakdown` (ficha); helper `_display_rating_for` + `SAVEPOINT_STATS_CONTEXT_KEY`; `get_provenance` prefiere IGDB sobre la lista prefetch
- `apps/api/catalogue/views.py` - `NewReleasesView` + `NewReleasesThrottle`, `OwnedGamesDlcView`, `_card_context`, `GameListView` pasa el contexto de stats
- `apps/api/catalogue/urls.py` - rutas `new-releases/` (`name="new-releases"`) y `owned-dlc/` (`name="owned-dlc"`)
- `apps/api/catalogue/tests/test_new_releases.py`, `test_owned_dlc.py`, `test_display_rating.py` (nuevos)

## Decisions Made

- **Reparto de la mezcla D-09.** `w = min(max(n, 1), 50)` por fuente; un valor presente siempre pesa >= 1 aunque su `n` sea 0/None; el techo 50 evita que una fuente con `n` enorme ahogue a la otra. Es el contrato de `must_haves` (restringido al mismo conjunto de cuentas que `rank_popularity_v1`); el reparto concreto queda **pendiente de confirmacion del autor** (ver "Issues Encountered").
- **`rating_breakdown.igdb_count = 0` cuando `work.rating is None`** aunque `rating_count` tuviera valor, para que la eleccion de copy de la ficha (`ratingBreakdown` / `...ExternalOnly` / `...LocalOnly`, por "conteo > 0") no anuncie usuarios de IGDB sin numero mostrable.
- **`NewReleasesView` responde una lista JSON desnuda**, no `{results: [...]}`, porque el plan fija "ventana vacia -> `[]`" en tres sitios (must_haves, behavior, acceptance_criteria).
- **`NewReleasesThrottle` con rate en la clase** (subclase de `SimpleRateThrottle`, scope `catalogue_new_releases`, `120/min`) en vez de anadir el scope a `config/settings.py` — ese fichero esta fuera del limite de ficheros de este plan en modo worktree. Sigue siendo un throttle por-IP con scope propio (intencion del plan).
- **`get_provenance` prefiere el `SourceRecord` `source=igdb`** y cae al primero disponible; conserva el test heredado (`test_detail.py`, source unico wikidata).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] N+1 introducido por `display_rating` por fila en el listado de catalogo**
- **Found during:** Tarea 3 (regresion `pytest apps/api/catalogue -q`)
- **Issue:** `GameCardSerializer.get_display_rating` llamaba a `display_rating(work)`, que ejecuta un `aggregate` de `LibraryEntry` por tarjeta. `test_search.py::test_list_endpoint_has_no_n_plus_one_and_is_query_bounded` fallo (33 queries frente al tope de 18).
- **Fix:** `catalogue/ratings.py::savepoint_rating_stats(work_ids)` calcula `{work_id: (media_x10, n)}` de toda la pagina en **una** query; `GameListView` y `NewReleasesView` la pasan por `context` del serializer; `display_rating(work, savepoint_stats=...)` acepta el dato precomputado y solo hace la query por-obra cuando no se le pasa (ruta de ficha).
- **Files modified:** `apps/api/catalogue/ratings.py`, `apps/api/catalogue/serializers.py`, `apps/api/catalogue/views.py`
- **Verification:** `pytest apps/api/catalogue -q` -> 109 passed (incluye el test de cota de queries); `pytest apps/api -q` -> 319 passed
- **Committed in:** `818f68c` (commit de la Tarea 3)

---

**Total deviations:** 1 auto-fixed (1 bug de rendimiento introducido y corregido en la misma tarea).
**Impact on plan:** Sin scope creep. El fix es necesario para no degradar el endpoint de listado existente; la API publica no cambia de forma.

## Issues Encountered

- **Confirmacion del autor pendiente (flagged assumption D-09 / 02-RESEARCH Open Question 3).** El plan delega en el autor el reparto exacto de pesos externo/local y si cuentan las cuentas auto-registradas. Se implemento el contrato de `must_haves`: restringido a `demo_anchor | demo_identity` (mismas cuentas que `rank_popularity_v1`), peso proporcional a `n` acotado a 50, un valor presente pesa >= 1. El resto del plan no depende del valor concreto de los pesos, pero **el autor debe ratificar este reparto** (registrado en coverage D6, `human_judgment: true`) antes de que 02-13 cierre DATA-07 y de que 02-06/02-12 lo consuman en UI.
- **Modo worktree:** no se modificaron `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` ni `config/settings.py`. El unico cambio no commiteado del arbol (`.claude/settings.local.json`) es ruido preexistente, no tocado por este plan.

## Known Stubs

Ninguno. Todos los caminos van a datos reales: `governed_works()` sobre el corpus persistente, `LibraryEntry` real con la restriccion de cuentas, `GameWork.rating`/`summary` poblados por el importador de 02-02.

## User Setup Required

Ninguno. Sin configuracion de servicios externos.

## Next Phase Readiness

- **02-06 (UI: ficha + home)** puede consumir: `summary`, `rating`, `rating_count`, `display_rating`, `rating_breakdown` en el serializer de ficha; `display_rating` en la tarjeta; `GET /api/catalogue/new-releases/` (lista de tarjetas) y `GET /api/catalogue/owned-dlc/` (`{groups: [...]}`, autenticado).
- **02-12 (UI: recomendaciones)** puede usar `display_rating` como el numero de producto unico.
- **02-13 (DATA-07)** cierra el requisito compartido: aqui solo se entrega la faceta de contrato de datos (mezcla determinista documentada, snapshot no participa). El reparto de pesos D-09 espera ratificacion del autor (coverage D6).
- **Aviso de alcance heredado (flagged assumption 2):** `sort=rating_desc` y `min_rating` siguen operando sobre `GameWork.total_rating` (Plan 02-03), no sobre `display_rating`. Alinear la clave de orden/umbral con el valor mostrado esta diferido a un pase posterior; la semantica de exclusion de D-07 no se ve afectada (ambos campos son null para obras gobernadas sin rating).

## Self-Check: PASSED

- `02-05-SUMMARY.md` creado en `.planning/phases/02-.../`.
- Commits verificados en `git log`: `ee76b86`, `a9b796c`, `eeb0880`, `18c654a`, `44d4e53`, `818f68c`.
- Ficheros nuevos presentes: `apps/api/catalogue/ratings.py`, `apps/api/catalogue/tests/{test_new_releases,test_owned_dlc,test_display_rating}.py`.
- `pytest apps/api -q` -> 319 passed; trio del plan -> 24 passed; regresion catalogue -> 109 passed.
- Arbol limpio salvo `.claude/settings.local.json` (ruido preexistente).

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Completed: 2026-09-07*
