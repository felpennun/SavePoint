---
phase: 02
plan: 09
github_issue: 25
status: in_progress
completed_tasks: 1
total_tasks: 3
updated: 2026-09-07
---

# Checkpoint de decisión — Plan 02-09

## Tarea 1 — Ratificar los ~8 arquetipos de usuario sintético (D-20)

`gate="blocking"`. **No es one-way**: la población es regenerable con otra semilla o
especificación.

## Decisión adoptada

**Selección del autor (2026-09-07): `ratify-as-proposed`.** Se ratifican los 8 arquetipos
y sus rangos de parámetros tal como los propone `02-09-PLAN.md` Tarea 1:

| # | Arquetipo | Rasgos |
|---|-----------|--------|
| 1 | Monogénero severo | 1-2 géneros preferidos; puntúa severo |
| 2 | Monogénero generoso | 1-2 géneros; puntúa generoso |
| 3 | Omnívoro medio | 5+ géneros; puntúa medio |
| 4 | Completista de saga | concentración alta en una saga |
| 5 | Explorador de novedades | sesgo hacia lanzamientos recientes |
| 6 | Coleccionista de pendientes | biblioteca grande, mayoría `pending` |
| 7 | Jugador ocasional cold-start | 1-3 juegos (cohorte cold-start separada) |
| 8 | Veterano de biblioteca grande | 50+ juegos, mezcla de estados |

Ejes de variación: nº de géneros preferidos (1-2 / 3-4 / 5+), tamaño de biblioteca
(5-15 / 20-40 / 50+), generosidad al puntuar (severo / medio / generoso), concentración
en saga, mezcla de estados `completed`/`playing`/`pending`/`abandoned`.

Cada arquetipo × ~25 usuarios con semillas independientes; la cohorte cold-start (1-3
juegos) es explícita y separada. Total ~200 + cohorte cold-start.

## Estado

- Tarea 1: **ratificada** (este documento).
- Tarea 2: pendiente — generador por semilla, persistencia con marcador distinto.
- Tarea 3: pendiente — aislamiento del baseline de popularidad + `docs/verification/synthetic-users-validation.md`.
- Cierre: `02-09-SUMMARY.md` + commit con `Closes #25`.
