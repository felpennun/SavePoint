---
phase: 02
plan: 02
status: queued
created: 2026-09-07
depends_on: 02-02 SUMMARY (pass 1 RAWG) landing on main
---

# Cola de trabajo — más ratings para el corpus gobernado

Decisiones del autor el 2026-09-07, a ejecutar **después** de que cierre la pasada 1 de
RAWG (10.000 obras por `rating_count`) y se fusione 02-02.

## 1. Verificación del import IGDB (antes de nada)

El autor no está convencido de la cobertura de rating (13,933 %) y cree que el import
"se paró a la mitad". El registro dice lo contrario (`IgdbImportRun.status == complete`,
cursor 416648, 312.560 obras; lo que falló fue la query de evidencia por `DiskFull`, con
los datos ya commiteados — anti-patrón "confiar solo en el exit code").

**No resetear el import.** Verificación read-only primero:

- `IgdbImportRun`: `status`, `pass_cursor`, `started_at` / `finished_at`, `last_error`,
  y si hubo más de una run (¿re-import parcial desde un cursor?).
- `GameWork.objects.count()` vs IGDB `POST /v4/games/count` con `game_type = 0`.
- `governed_works("2026.09.1")`: total, `rating IS NOT NULL`, `total_rating IS NOT NULL`.
- ¿Hay un rango de `igdb_id` / cursor sin los campos ampliados (`rating`, `summary`,
  `alternative_names`, …)? Comparar obras con `updated_at` anterior a la fecha del
  re-import ampliado.

Resultado A — el import está completo y 13,9 % es la densidad real de rating de usuario
de IGDB: no hay nada que reimportar; el hueco se llena con RAWG + APIs futuras.
Resultado B — hay una franja sin campos nuevos o un desajuste de conteo: **reanudar**
el `IgdbImportRun` existente para esa franja (nunca reset del cursor), re-`_upsert`
solo de las obras afectadas, re-medir.

## 2. Segunda pasada de RAWG (elección del autor)

- Filtro: `rating IS NULL` **y** sin `CorpusRatingSnapshot(source="rawg")` para la
  versión activa **y** `first_release_date` entre 2022-01-01 y 2026-12-31.
- Orden: **popularidad** — `total_rating_count DESC NULLS LAST`,
  `rating_count DESC NULLS LAST`, `first_release_date DESC`, `pk`.
  (El autor eligió popularidad sobre `total_rating` porque un título más conocido
  reconcilia mejor contra RAWG; prima la tasa de match.)
- Límite: `--limit 20000`, corre hasta el 429 de RAWG y para limpio. Insert-only,
  idempotente. La API key nunca se imprime ni commitea.
- Reconciliación sin cambios: slug exacto → título normalizado + año, resto se cuenta
  y descarta. Sin fuzzy.

## 3. Enmienda a ADR-008

Registrar la pasada 2: criterio de orden (popularidad), filtro de año 2022-2026,
límite = agotar cuota, y el motivo declarado del autor — "máxima cantidad de datos
ahora; el relleno del resto se hará con otras APIs al final". Mantener el resto de
ADR-008 (no redistribución, snapshots inmutables, no sobrescribir `GameWork.rating`).

## Implementación

`enrich_rawg_ratings` necesita flags nuevos: `--only-unrated`, `--release-year-min`,
`--release-year-max`, `--order-by {rating_count,popularity,total_rating}`. Con tests
del nuevo modo de selección. Trabajo pequeño; va como seguimiento de 02-02, no como
desviación en caliente (el ejecutor actual tiene tomado `apps/api/catalogue/`).
