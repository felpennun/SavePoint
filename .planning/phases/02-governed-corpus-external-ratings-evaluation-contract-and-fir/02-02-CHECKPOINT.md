---
phase: 02
plan: 02
github_issue: 18
status: complete
completed_tasks: 3
total_tasks: 3
updated: 2026-09-07
---

# Checkpoint de decision — Plan 02-02

Las tareas 1 y 2 están completas y commiteadas. La tarea 3 decide si se incorpora RAWG
como segunda fuente y cambia el alcance de la fase, por lo que requiere respuesta del
autor antes de escribir ADR-008 o código condicional.

## Evidencia medida

Medición contra la base de desarrollo persistente después de aplicar las migraciones
`0006_governed_corpus` y `0007_igdb_rating_fields`:

| Campo | Conteo | Cobertura |
|---|---:|---:|
| Obras gobernadas | 193.885 | 100 % de la vista |
| `total_rating IS NOT NULL` | 0 | 0,00 % |
| `rating IS NOT NULL` | 0 | 0,00 % |
| Snapshots IGDB insertados | 0 | 0 |

El JSON del comando de snapshot informó `corpus_version=2026.09.1`,
`governed_count=193885`, `total_rating_present=0` y `rating_present=0`. La base se
importó originalmente antes de ampliar `GAME_FIELDS`; se intentó iniciar el re-import
para poblar los campos nuevos, pero el contenedor no tiene las variables de entorno
`IGDB_CLIENT_ID` y `IGDB_CLIENT_SECRET`. No se imprimió ningún secreto.

Por tanto, el 0,00 % es una medición real y reproducible del estado persistente, pero no
debe interpretarse como cobertura final de IGDB tras el re-import ampliado. Si el autor
proporciona el entorno operativo con esas variables, el re-import y la medición deben
repetirse antes de publicar cifras finales.

## Verificación completada

- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue/tests/test_igdb_import.py -q` — **21 passed**.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue/tests/test_rating_snapshot.py -q` — **2 passed**.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue -q` — **66 passed**.
- Snapshot insert-only: una segunda ejecución no modifica la fila y un cambio posterior de `GameWork.rating` no cambia el snapshot.
- `GAME_FIELDS` incluye rating de usuarios, resumen, aliases y compañías; no incluye `aggregated_rating`.

## Decisión requerida

**¿Debe entrar RAWG como segunda fuente de ratings en esta fase?**

- `igdb-only`: aceptar y documentar la cobertura medida; cerrar DATA-07 con una regla de desempate prospectiva en ADR-008, sin `rawg.py` ni reconciliación ejecutable.
- `add-rawg N`: añadir RAWG acotado al top-N por `rating_count` sobre la allowlist, con ADR, backlink, reconciliación slug → título normalizado + año y conteo de no emparejados. Indicar el valor concreto de N.

La decisión queda registrada en `docs/adr/ADR-008-external-ratings.md`.

## Decisión adoptada

El autor ha indicado intentar IGDB primero y añadir RAWG si no se puede encontrar
rating para todo el corpus. Como no había credenciales operativas para ninguna fuente,
se añade RAWG acotado con `N=10.000`, ordenado por `rating_count` descendente y con
desempate determinista. La implementación está probada; queda pendiente una ejecución
autenticada para medir cobertura RAWG real.

### Ratificación final (2026-09-07, re-import ampliado completado)

El re-import IGDB con `GAME_FIELDS` ampliado terminó y persistió: corpus activo
`2026.09.1`, 193.885 obras gobernadas, 27.014 con `rating` de usuario (**13,933 %**),
30.672 con `total_rating` (15,820 %); 27.014 `CorpusRatingSnapshot` `source="igdb"`
insertados. La cifra 13,933 % está muy por debajo del ~60 % orientativo (no vinculante)
de D-06 y lejos de «rating para todo el corpus».

**Selección del autor en el checkpoint de reanudación: `Ejecutar RAWG N=10.000`.** Se
autoriza la ejecución en vivo de `enrich_rawg_ratings --corpus-version 2026.09.1
--limit 10000` con `--env-file .env.local` y evidencia JSON fuera de Git. Antes de
lanzar: añadir `shm_size` al servicio `db` de Compose para evitar el `DiskFull` en
memoria compartida observado en el paso de evidencia de IGDB. Después: medir cobertura
RAWG real (emparejados / no emparejados / snapshots insertados), congelar evidencia,
escribir `02-02-SUMMARY.md` y cerrar con `Closes #18`.

### Resultado de la ejecución RAWG — 2026-09-07 (COMPLETO)

Verificación previa en BD (constraints bloqueantes de `.continue-here.md`): `IgdbImportRun`
`complete` (cursor 416.648, 312.560 works importados), 312.710 `GameWork`, 193.885 obras
gobernadas `2026.09.1`, 27.014 con `rating` IGDB, 27.014 snapshots `source="igdb"`, 0
`source="rawg"`. Todo coincide; se procedió.

`shm_size: "256mb"` añadido al servicio `db` en `infra/compose.yaml`. Ejecución en 18
lotes de 500 con `--offset` (resiliencia frente al reinicio del contenedor `db` por el
worktree concurrente de 02-08) y `--env-file .env.local`; `RAWG_API_KEY` solo por
entorno, nunca impreso ni commiteado. Evidencia JSON por lote conservada en scratchpad,
fuera del control de versiones.

| Métrica | Valor |
|---|---:|
| Obras consideradas (top-10.000 por `rating_count` IGDB) | 10.000 |
| Emparejadas (slug exacto / título normalizado + año, con `rating` usable) | 8.575 |
| No emparejadas (descartadas y contadas) | 1.425 |
| Emparejadas sin `rating` usable | 0 |
| `CorpusRatingSnapshot(source="rawg")` insertados | 8.575 |
| `SourceRecord(source="rawg")` | 8.553 |
| `GameWork.rating` mutado | no (huella SHA-256 idéntica antes/después) |
| Cobertura combinada `igdb` OR `rawg` sobre 193.885 obras | 27.014 = **13,9330 %** (sin cambio) |
| Cobertura nueva solo por RAWG | **0 obras** |

Hallazgo: el corte ordenado por `rating_count` de IGDB es un subconjunto de las 27.014
obras que ya tienen `rating` IGDB, así que RAWG aporta contraste de fuente, no cobertura
nueva. `pytest apps/api/catalogue -q` → 70 passed. Re-ejecución de `--offset` idempotente
(`snapshots_inserted=0`). Detalle en `docs/adr/ADR-008-external-ratings.md` y
`docs/verification/igdb-catalogue-freeze.md`. Plan 02-02 cerrado.
