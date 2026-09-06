# Firma de la Fase 01.1: Catálogo a escala real y experiencia de producto

**Estado: ACEPTADA CONDICIONALMENTE** por Felipe (autor), 2026-09-06, contra el commit `2d49fc8df2beaf7fb741a68c9f835b7f51f57295`.

No desplegada — todo plan de esta fase está mergeado en `origin/main` y corre solo en el stack local de `docker compose` (ver *Estado del despliegue* abajo).

Este documento es el registro de cierre de fase de la Fase 01.1, el seguimiento a escala real pedido por el autor tras la Fase 1 (que se firma por separado en `docs/verification/phase-01-signoff.md`). Enlaza la evidencia automática, la verificación de objetivo de fase y las decisiones del propio autor. No suaviza el único criterio de éxito parcial ni las limitaciones arrastradas para presentar la fase como más completa de lo que es.

## Naturaleza de esta aceptación

El gate humano de calidad de producto de la fase (QUAL-05 / D-07, Plan 01.1-07) se cerró como una **aprobación anticipada condicional del autor**. El 2026-09-06, antes de desconectarse, el autor autorizó explícitamente APROBADO para las cuatro superficies D-07 (catálogo, detalle de juego, registro, recomendaciones) en escritorio y móvil, condicionado a que la evidencia automática pasara — cosa que hizo. La aprobación se hizo contra el conjunto de capturas en sesión, **no** un recorrido en vivo completo por viewport; ese recorrido queda diferido por elección del autor, con la intención declarada de ejecutar una pasada dedicada de refinamiento de diseño una vez la funcionalidad esté completa y de esperar cambios de UI en cualquier caso. Esto está registrado textualmente en `docs/verification/phase-01.1-product-review.md` → `## Revisión del autor`, y en `.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-07-SUMMARY.md`.

## Evidencia automática (esta sesión, en o cerca del commit `2d49fc8`)

| Check | Comando | Resultado |
|---|---|---|
| Suite de tests del backend | `docker compose -f infra/compose.yaml run --rm api pytest apps/api -q` | pasando (demo-identity de accounts, búsqueda/filtro/orden de catálogo, heurístico de recomendaciones, importador) |
| Build del frontend | `pnpm --dir apps/web run build` | éxito, sin error de tipos/build (Next 16.3.4 + React 19 + TS + Tailwind v4) |
| Unit del frontend / paridad i18n | `pnpm --dir apps/web test` | 16 pasados (incluye paridad de claves de mensaje EN/ES) |
| Playwright de producto + axe | `pnpm exec playwright test e2e/a11y.spec.ts e2e/demo-journey.spec.ts --project=chromium` | 41 pasados en 3 ejecuciones consecutivas; axe cero critical/serious en catálogo, detalle, registro, recomendaciones (más homepage/login/fuentes) en escritorio 1280×800 y móvil 375×812 |
| Artefactos de captura | commiteados en `e2e/artifacts/phase-01.1/` | 8 ficheros — catálogo / detalle / registro / recomendaciones × escritorio / móvil |
| Gate de estructura de la revisión de producto | regex `powershell -File` sobre `docs/verification/phase-01.1-product-review.md` | PASS — `Veredicto de Playwright: PASS`, `Veredicto de axe: PASS`, tabla de Artefactos de captura acotada de 8 filas, PASS escritorio+móvil por superficie |
| Gate de revisión del autor | regex `powershell -File` (Plan 01.1-07 Tarea 2) | `AUTHOR-REVIEW GATE: PASS` |
| Barrido de secretos | `powershell -File scripts/check-secrets.ps1` | PASS exit 0 — contenedores/imágenes/logs en ejecución + árbol escaneados, cero matches con forma de secreto fuera de allowlist |
| Carga de catálogo a escala real | `docs/verification/igdb-catalogue-freeze.md` + `.sample.json` | 312,483 obras primarias de IGDB (`game_type = 0`) cargadas en la BD de desarrollo junto al corpus Wikidata de 150 obras; checksum de contenido `ff3d67525c92…`, cobertura agregada, manifiesto de revisión muestreada determinista de 300 filas; `GET /api/catalogue/games/` → `count: 312633` |
| Política de dependencias | `powershell -File scripts/check-dependencies.ps1` | PASS — solo `requests==2.34.2` añadido en esta fase, fijado + legitimidad registrada |

## Criterios de éxito

Detalle completo: `.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-VERIFICATION.md` (`status: verified`, `score: 5/5` tras la re-verificación de SC3 del 2026-09-06; al cierre inicial fue `gaps_found`, `4/5`).

| # | Criterio | Veredicto |
|---|---|---|
| SC1 | Catálogo a escala real con fuente IGDB, con licencia/atribución documentadas y procedencia por obra | **VERIFICADO** — 312,633 obras; comparación DATA-04 de ADR-006; `docs/verification/igdb-api-probe.md` con evidencia de sondeo redactada y términos textuales de la DSA + FAQ de IGDB; API de fuentes + procedencia en el detalle de juego |
| SC2 | Ordenar y filtrar el catálogo por plataforma, género y otros metadatos | **VERIFICADO** — `parse_catalogue_query` con allowlists `platform` / `genre` / `year_from` / `year_to` / `min_rating` + un conjunto `sort` de 6 claves, cada una con desempate por `canonical_slug`; entrada hostil / fuera de lista → 400 acotado; DTO de facetas sin N+1; `FilterBar` compartible por URL; la migración `0004` añade los campos escalares + 4 índices |
| SC3 | Múltiples cuentas precargadas distintas inician y cierran sesión de forma independiente | **VERIFICADO** (re-verificado el 2026-09-06 tras el plan de seguimiento) — `bootstrap_demo_accounts` ahora reconcilia el usuario primario preexistente bajo `LEGACY_ANCHOR_KEY` (lo adopta en vez de abortar con `SeedContractError`); `infra/compose.yaml` y `apps/api/render-start.sh` llaman al comando **plural**; `DEMO_ACCOUNTS` lleva 3 cuentas (`demo-visitor` / `demo-critico` / `demo-coleccionista`), placeholder inerte D-02 en compose y `sync: false` en `render.yaml`. Verificado en vivo: arranque `Demo accounts ready (total=3, created=2, rotated=1)`; cada cuenta hace login (200) y logout (200) independientemente, sesión invalidada tras logout (403). 31 tests de bootstrap + 209 de la suite api pasan. |
| SC4 | La interfaz se lee como un producto de catalogación profesional | **VERIFICADO (aprobación condicional del autor)** — sistema de tokens de variables CSS de primera parte claro/oscuro con cookie SSR `sp-theme` sin flash; `ThemeToggle`; `ScorePill` / `StatusPill` / `StarRating` / `CoverImage` / `FilterBar`; todas las superficies D-07 rediseñadas; `01.1-UI-SPEC.md` VERIFICADO 7/7 por el checker; Playwright 41 pasados + axe limpio + 8 capturas |
| SC5 | Página de recomendaciones dedicada: sugerencias por género a partir de la actividad propia del usuario, distinta del baseline de popularidad | **VERIFICADO** — `rank_genre_taste_v1`, un heurístico por petición sin estado que **nunca** cae al baseline de popularidad (D-09), con `input_snapshot_sha256` y una forma `insufficient_history` distinta; `RecommendationsView` es `IsAuthenticated`; ADR-007 lo documenta como heurístico y explícitamente **no** la contribución de ML de la tesis; página web con gate de auth, disclosure de algoritmo + limitación y un enlace de navegación solo-autenticado |

**Veredicto de fase:** al cierre inicial, 4/5 criterios VERIFICADOS y 1 PARCIAL (SC3). Tras el plan de seguimiento del 2026-09-06 (reconciliar-y-cablear, opción A autorizada por el autor), **SC3 pasa a VERIFICADO** → **5/5 criterios VERIFICADOS**. Ver *Addenda posteriores a la firma*.

## Limitaciones nombradas arrastradas fuera de esta fase

Registradas en `.planning/phases/01.1-real-scale-catalogue-and-product-experience/deferred-items.md`:

1. ~~**SC3 — las cuentas precargadas plurales no están cableadas a ningún runtime.**~~ **RESUELTO el 2026-09-06** con el plan de seguimiento (ver *Addenda*). `bootstrap_demo_accounts` reconcilia el usuario primario preexistente bajo `LEGACY_ANCHOR_KEY`; compose y `render-start.sh` llaman al plural; 3 cuentas demo activas y verificadas en vivo (login/logout independiente).
2. **`total_rating` es NULL en las 312,633 filas.** Ninguna fuente previa lo llevaba; el importador ahora lo captura pero no se ha reejecutado. El filtro de "valoración mínima de IGDB" y el orden `rating_desc` son contractualmente correctos pero actualmente inertes.
3. **`first_release_date` está poblado para aproximadamente el 75% de las filas** (con backfill desde releases vía subconsulta correlacionada en la migración `0004`; las filas sin release con fecha quedan NULL).
4. **La página de recomendaciones muestra el estado de onboarding / `insufficient_history`** para la cuenta demo y las cuentas recién registradas, que no tienen historial de librería con género en la BD de desarrollo con seed. El ranking personalizado en sí está unit-testeado de forma determinista.
5. **La navegación superior autenticada hace overflow horizontal por debajo de ~430px** (chrome compartido, no una sola superficie). Necesita una decisión de diseño sobre densidad del chrome móvil. (`deferred-items.md` → `### D-01.1-10-a`.)
6. **El detalle de juego se lee un poco escaso** — chips de género condicionales; la portada podría ser más grande / más dominante. Cosmético.
7. **El recorrido en vivo completo por viewport del autor está pendiente** por elección del autor (ver *Naturaleza de esta aceptación*).

## Estado del despliegue

**Nada de la Fase 01.1 está desplegado.** No se ejecutó ningún comando de despliegue durante esta fase. Todo el trabajo mergeado está en `origin/main`. La demo pública de la Fase 1 (`docs/verification/phase-01-signoff.md`, `https://save-point-orpin.vercel.app`, API `https://savepoint-api-37nz.onrender.com`, commit `1af981e`) sigue sirviendo la UI pre-rediseño contra el catálogo Wikidata de 150 obras.

Desplegar la Fase 01.1 requeriría, como decisión del autor separada y explícita:

- hacer push del frontend rediseñado `apps/web`;
- aplicar las migraciones nuevas de esta fase (campos de género + importación de IGDB, y `catalogue/0004_catalogue_filter_sort_fields`);
- cargar la base de datos desplegada con el catálogo de IGDB (~312k filas) — **comprobar primero el límite de tamaño del tier de hosting**; hay un `pg_dump` de 93 MB de la BD de desarrollo cargada en `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (gitignored) como ruta de restauración;
- decidir si además reejecutar el importador para poblar `total_rating`.

Como hubo aproximadamente veinte pushes a `main` esta sesión, deberían comprobarse los paneles de Vercel y Render en busca de builds auto-disparados contra la base de datos de producción aún sin cargar antes de cualquier decisión de despliegue.

## Decisiones del autor y próximos pasos (registrado para la tesis)

- El autor aceptó la Fase 01.1 como entregada, **condicionalmente**, y pidió que la fase se cerrara de forma autónoma (2026-09-06) con checkpoints, una revisión de todo el repo y una limpieza conservadora.
- Los ítems cosméticos (densidad del detalle de juego, overflow de la navegación superior autenticada, estado de onboarding de recomendaciones) son para una **pasada dedicada de refinamiento de diseño** una vez la funcionalidad esté completa; el autor espera explícitamente cambios de UI se cierre o no la fase ahora.
- El hueco de cableado de SC3 se resolvió el 2026-09-06 (ver *Addenda*).
- La Fase 2 (Corpus gobernado y contrato de evaluación congelado) **no** está empezada.

### Addenda posteriores a la firma (2026-09-06, el mismo día)

- **Decisión de despliegue (autor):** el autor revisó el panel de Vercel — hay un build del frontend rediseñado en vivo, pero el catálogo está vacío y la vista de catálogo da error (la base de datos desplegada todavía tiene solo el corpus de 150 juegos; el catálogo IGDB de 312k es solo local). La decisión del autor: **dejar el despliegue público actual tal cual por ahora.** La demo a los examinadores se ejecuta desde el stack local de `docker compose`; cablear el despliegue a datos reales de internet (cargar el catálogo en una BD desplegada, aplicar migraciones, `NUM_PROXIES` / `ALLOWED_HOSTS`) queda diferido al final del proyecto *"cuando todo esté montado"*. Esto es una decisión del autor registrada, no un defecto pendiente contra el alcance de la Fase 01.1.
- **Remediación de seguridad de todo el repo (autorizada por el autor):** tras la revisión de todo el árbol (`docs/verification/repo-review-2026-09-06.md`) el autor instruyó *"quiero que apruebes todos en su totalidad"*. **Los 16 hallazgos de la revisión** (3 Alta / 6 Media / 7 Baja) están ahora arreglados en cinco tandas commiteadas (`a2b480a` auth/throttle, `7b05133` importador, `5e6082d` búsqueda/recs, `6637578` cabeceras del frontend, `6370cf2` config de gunicorn/deploy), cada una verificada (`pytest apps/api` 206 pasados; `pnpm --dir apps/web build` + 16 tests web; Playwright a11y 36 en verde bajo la nueva CSP). Esto añade una dependencia fijada, `gunicorn==23.0.0` (legitimidad registrada), y una migración, `catalogue/0005_igdbimportrun_pass_cursor`. Un problema pre-existente descubierto por separado — `scripts/check-evidence.ps1` estaba en rojo en `main` (bug CRLF de hashing; ADR-006/007 con encabezados en inglés vs el contrato español del gate) — **también se arregló** (commits `e55ff8f`/`bc48f5a`): el gate normaliza CRLF→LF antes de hashear, ADR-006/007 traducidos al español con los siete encabezados requeridos, y tres pins de hash del ledger refrescados a su valor LF. `check-evidence.ps1` ahora pasa en verde.
- **SC3 resuelto (plan de seguimiento, opción A autorizada por el autor):** `bootstrap_demo_accounts` gana reconciliación del usuario primario legacy — cuando el contrato `DEMO_ACCOUNTS` incluye la entrada `key="demo-anchor-primary"` y ese usuario ya existe (por el comando singular) sin `DemoAccountIdentity`, lo **adopta** en vez de abortar con `SeedContractError`; una colisión genuinamente ajena sigue siendo fail-closed. `infra/compose.yaml` y `apps/api/render-start.sh` pasan al comando plural; `DEMO_ACCOUNTS` = 3 cuentas (`demo-visitor` / `demo-critico` / `demo-coleccionista`), placeholder inerte D-02 en compose y `sync: false` en `render.yaml`; `check-secrets.ps1` allowlista las dos contraseñas placeholder nuevas. Verificado en vivo contra el stack: `Demo accounts ready (total=3, created=2, rotated=1)`, las 3 cuentas login (200) / logout (200) independiente, sesión invalidada (403 tras logout). 3 tests de reconciliación nuevos + 209 de la suite api + `check-secrets.ps1` en verde. `01.1-VERIFICATION.md` pasa a `status: verified`, score **5/5**; `deferred-items.md` marca SC3 como RESUELTO.
- **Traducción de `docs/` al español (autorizada por el autor):** convención de idioma fijada por el autor el 2026-09-06 — toda la documentación de tesis y las conversaciones en español, el código en inglés. Barrido de `docs/` completo: ADR-006/007, `igdb-api-probe.md`, `igdb-catalogue-freeze.md`, `phase-01-manual.md`, `phase-01.1-product-review.md`, `repo-review-2026-09-06.md`, `public-demo.md` y este documento traducidos; los gates de contenido asociados (`verify-igdb-adr.ps1`, `verify-igdb-probe.ps1`, `verify-igdb-fresh-import.ps1`) actualizados en paralelo; las citas legales textuales de IGDB se conservan en inglés. La foto congelada `docs/verification/phase-01-signoff.2026-09-05T10-45.md` se deja en inglés como registro histórico.

## Reversibilidad

Todo plan de esta fase es un commit discreto en `main`, con push. El estado de fase-completa está tagueado `phase-01.1-complete` en el commit `2d49fc8`. La base de datos de desarrollo puede restaurarse desde `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` vía `pg_restore` en minutos.

---
*Firmado: 2026-09-06 (aprobación anticipada condicional)*
*Commit: `2d49fc8df2beaf7fb741a68c9f835b7f51f57295`*
*Firma de la Fase 1.0 (separada, ya aceptada): `docs/verification/phase-01-signoff.md`*
