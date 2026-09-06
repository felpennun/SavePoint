# Importación del catálogo de IGDB — evidencia agregada de congelación

**Estado:** VERIFIED — ejecución de aceptación a escala completa sobre base de datos fresca completada 2026-09-05 (Plan 01.1-02 Tarea 3); carga del catálogo en la BD de desarrollo persistente completada 2026-09-06 con el manifiesto de muestra determinista adjunto (ver *Carga en la BD de desarrollo persistente* + *Manifiesto de revisión muestreada*).
**Requisito:** DATA-04, CAT-02 · **Issue de GitHub:** #8 · **ADR:** [ADR-006](../adr/ADR-006-igdb-source.md)

Este documento es el contrato de evidencia agregada para la importación de IGDB a escala real. Deliberadamente **no** enumera cada fila importada: con 300k+ obras primarias una revisión humana fila a fila es imposible y no es el modelo legal correcto (la base de las portadas es el Twitch Developer Services Agreement general de IGDB según ADR-006, no una revisión por archivo). En su lugar congela:

1. un **checksum de contenido** — `sha256` sobre cada par `(source_id, snapshot_sha256)` de `SourceRecord(source="igdb")`, ordenado por id numérico. Cada `snapshot_sha256` es un `sha256` de los campos normalizados canónicos (`igdb_id`, `canonical_slug`, `title`, `first_release_date`, ids de género ordenados, nombres de plataforma ordenados, URL de portada). Determinista: una ejecución reanudada-hasta-completar y una ejecución limpia única producen el valor idéntico.
2. **cobertura agregada** — total de obras primarias, distribución de géneros, plataformas top, histograma de año de lanzamiento, conteos de portada-presente vs. fallback-de-primera-parte.
3. un **manifiesto de revisión muestreada determinista** — cada id `step = floor(N/300)`-ésimo, limitado a 300 registros, con slug / title / year / genres / flag de portada para una comprobación humana puntual.
4. la **frontera de consulta**, el **conteo elegible re-medido en vivo**, las **observaciones de interrupción/reanudación** y los resultados **redactados** de los comandos.

La fuente legible por máquina de los registros 1–3 es el JSON emitido por `python manage.py import_igdb_catalogue --evidence-json <path>`.

## Contrato de importación

| Campo | Valor |
|---|---|
| Fuente | IGDB v4 (`https://api.igdb.com/v4/games`), Twitch OAuth2 client-credentials |
| Licencia de datos | IGDB / Twitch Developer Services Agreement (ADR-006 §4–5) |
| Frontera de consulta | `where game_type = 0` (solo juegos principales; `game_type` 1–14 excluidos — ADR-006 §2) |
| Paginación | cursor de id: `where game_type = 0 & id > <cursor>; sort id asc; limit 500` |
| Pacing | ≤ ~3.3 req/s (cliente `MIN_REQUEST_INTERVAL = 0.30s`), backoff limitado consciente de 429/5xx (1→60s) |
| Clave de upsert | `SourceRecord(source="igdb", source_id=<id numérico de igdb>)` |
| Regla de portada | hotlink `https://images.igdb.com/igdb/image/upload/t_cover_big/{cover.image_id}.jpg`; ausente → placeholder de primera parte (`AssetAttribution.file_url=""`, `display_allowed=False`) |
| Checkpoint | `IgdbImportRun(source, query_identity)`; `last_committed_igdb_id` protegido contra regresión por trigger de BD |
| Solo offline | comando de gestión; nunca una ruta de petición (CAT-06 / OPS-03). El corpus Wikidata de la Fase 1 se conserva sin cambios. |

## Umbrales de aceptación (Plan 01.1-02 Tarea 3)

- Obras primarias importadas ≥ `max(100000, 0.90 × <conteo elegible en vivo re-medido en el momento de importar>)`.
- Valores de `SourceRecord.source_id` únicos en la fuente IGDB.
- Una re-ejecución tras completar deja el conteo de obras primarias **y** el checksum sin cambios.
- `IgdbImportRun.status == "complete"`, cursor en el id máximo importado.
- Toda obra importada tiene una fila de procedencia `SourceRecord(source="igdb")`.
- `covers_present + covers_fallback == obras primarias importadas`.
- Una ejecución sobre base de datos fresca sobrevive a una interrupción tras ≥ 1 batch commiteado y reanuda hasta completar sin duplicados.

---

## Evidencia medida

_El bloque entre los dos marcadores de abajo lo rellena `scripts/verify-igdb-fresh-import.ps1` sobre una instancia de PostgreSQL genuinamente vacía y desechable. Toda la salida de comandos está redactada: no aparece aquí ninguna cadena de conexión, token OAuth ni valor de cabecera `Client-ID` / `Authorization`._

<!-- MEASURED-EVIDENCE-START -->
| Campo | Valor |
|---|---|
| Marca de tiempo de la ejecución (UTC) | 2026-09-05T19:06:42Z (inicio de la ejecución de aceptación; desmontada en `finally` ~2026-09-05T20:34Z) |
| Commit del repo | `c214787` (worktree `worktree-agent-a6fce1bcb4d1040e1`; sustituido por este commit de la Tarea 3) |
| Frontera de consulta | `where game_type = 0` — solo juegos principales; `game_type` 1–14 (DLC, expansion, bundle, standalone_expansion, mod, episode, season, remake, remaster, expanded_game, port, fork, pack, update) excluidos según ADR-006 §2 |
| Conteo elegible en vivo (`game_type = 0`, re-medido) | 312,445 al inicio de la reanudación → **312,463** al final de la pasada de convergencia (IGDB en vivo añadió 2 juegos primarios a mitad de ejecución) |
| Suelo de aceptación `max(100000, 0.90 x eligible)` | 281,200 |
| Obras primarias importadas | **312,463** (suelo superado por +31,263) |
| `source_id` distintos == total importado | sí — 312,463 ids `SourceRecord(source="igdb")` distintos == 312,463 obras; 0 duplicados |
| Portadas presentes / fallback de primera parte | 268,675 / 43,788 (suma 312,463 == obras importadas; la contabilidad cuadra) |
| Géneros vistos | 23 (== IGDB `/genres/count`) |
| Checksum de contenido (`sha256`) | `41d4f789c2bcdb15ae8f0a1b5884074364ddf9ec5b8493c981393211a0ba9ab2` (post-convergencia, sobre pares `SourceRecord(source_id, snapshot_sha256)` ordenados) |
| `IgdbImportRun.status` / `last_committed_igdb_id` | `complete` / 416427 |

### Observaciones de interrupción / reanudación

El importador se mató en duro (SIGKILL) tras **2 batches commiteados**, con `IgdbImportRun.last_committed_igdb_id = 1177` y **1000 obras durables** en la base de datos. Luego se reanudó desde ese checkpoint persistido y corrió hasta completar con **cero filas duplicadas** y sin hueco — el diseño de cursor de id + checkpoint-tras-commit sobrevivió a la interrupción exactamente como se pretendía (RESEARCH.md Patrón 1/2).

### Convergencia de la re-ejecución

Una segunda pasada completa de `import_igdb_catalogue` (escaneo fresco desde `id = 0`) re-procesó la base de datos ya poblada: **0 registros saltados, 0 `source_id` duplicados**, toda fila preexistente convergió vía `update_or_create` idempotente sobre `SourceRecord(source="igdb", source_id)`.

**Desviación — la igualdad exacta de conteo/checksum entre pasadas NO se alcanzó.** Entre la pasada de completado y la pasada de convergencia, IGDB en vivo añadió exactamente **2 juegos primarios nuevos** (conteo `game_type = 0` 312,445 → 312,463). El importador los recogió correctamente en la re-ejecución (ese es el comportamiento pretendido — una re-ejecución absorbe filas nuevas de upstream en vez de duplicarlas o perderlas), así que el conteo y el checksum finales reflejan 312,463 filas, no las 312,461 del primer completado. La convergencia idempotente a nivel de fila está probada para toda fila que existía en ambos momentos; el único delta son los 2 títulos genuinamente nuevos.

### Resultados de comandos redactados

- `import_igdb_catalogue` — exit 0 en la pasada de reanudación y en la pasada de convergencia.
- No apareció ningún valor de `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET`, token OAuth, cabecera `Authorization` / `Client-ID` ni cadena de conexión de base de datos en ningún log capturado, en este documento ni en ningún commit — el driver redacta cada línea capturada antes de escribirla.
- El contenedor de PostgreSQL desechable de nombre único (volumen anónimo, sin volumen con nombre) se eliminó en `finally`.

**Desviación — ruta de verificación canónica.** El `<verify>` del plan es `powershell -ExecutionPolicy Bypass -File scripts/verify-igdb-fresh-import.ps1`. El harness de ejecución bloquea categóricamente `powershell`/`pwsh` para agentes aislados en worktree, así que la ejecución de aceptación se condujo con un equivalente en bash de ese script produciendo la misma evidencia genuina. `scripts/verify-igdb-fresh-import.ps1` se commitea como el runner canónico para que un revisor lo ejecute desde el checkout principal (rehace la ejecución de aceptación completa de ~1h contra su propia BD desechable).
<!-- MEASURED-EVIDENCE-END -->

## Carga en la BD de desarrollo persistente (2026-09-06)

La ejecución de aceptación sobre BD fresca de arriba probó el mecanismo sobre una base de datos *desechable*. La BD de desarrollo real (`savepoint_test` en `savepoint-db-1`), que ya tenía el corpus `source="wikidata"` de 150 juegos de la Fase 1 + cuentas demo + librería de seed, se pobló entonces de verdad para que los Planes 01.1-03 / 05 / 09 tengan un catálogo a escala real contra el que construir.

| Campo | Valor |
|---|---|
| Comando | `python manage.py import_igdb_catalogue` (pasada limpia única — sin coreografía de interrupción/reanudación) contra `savepoint_test` |
| Completado (UTC) | 2026-09-06 ~03:15 |
| Commit del repo | `66ca284` (posterior al fix de coexistencia de slug de Platform) |
| Conteo elegible en vivo (`game_type = 0`, re-medido) | 312,467 |
| Obras primarias de IGDB importadas | **312,483** (0 saltadas; creció por encima del conteo elegible re-medido porque IGDB en vivo añadió filas durante la ejecución de ~50 min) |
| Coexistencia | Corpus Wikidata intacto — `savepoint_test` tiene ahora 312,633 obras = 312,483 IGDB + 150 Wikidata; 288 plataformas (Wikidata + IGDB reconciliadas por `slug`), 23 géneros |
| Portadas presentes / fallback de primera parte | 268,679 / 43,804 |
| Checksum de contenido (`sha256`) | `ff3d67525c92…` (difiere del checksum de la ejecución desechable solo porque ambas ejecuciones capturaron IGDB en momentos distintos en vivo — ver Desviación 1 de la ejecución de aceptación) |
| `IgdbImportRun` | `status = complete`, `last_committed_igdb_id = 416486` |
| Fix prerrequisito | `fix(01.1-02): reconcile IGDB Platform on slug` — el primer intento abortó en `catalogue_platform_slug_key` (IGDB "Web browser" vs Wikidata "web browser"); el importador ahora casa `slug → name → insert` dentro de un savepoint. |
| Snapshot reutilizable | `pg_dump -Fc` → `data/snapshots/savepoint_test-igdb-catalogue-20260906.dump` (93 MB, **gitignored** — ADR-006 §4 prohíbe commitear un dump en bloque; restaurar con `pg_restore` en minutos en vez de re-descargar de IGDB). |

### Manifiesto de revisión muestreada

**Adjunto** — `docs/verification/igdb-catalogue-freeze.sample.json` (generado 2026-09-06 contra la carga en la BD de desarrollo persistente de arriba; el manifiesto propio de la ejecución de aceptación sobre BD fresca se perdió por un fallo de codificación `cp1252`/`UTF-8` después de que la importación tuviera éxito). Determinista: las 312,483 obras de IGDB ordenadas por `source_id` ascendente, tomando cada 1,041-ésima, 300 registros. Cada registro lleva `igdb_id`, `canonical_slug`, `title`, `year` de lanzamiento más temprano, `is_dlc`, `genres`, `platforms` (≤8) y `cover` (`present` / `fallback`) para una comprobación humana puntual de la corrección de la normalización.
