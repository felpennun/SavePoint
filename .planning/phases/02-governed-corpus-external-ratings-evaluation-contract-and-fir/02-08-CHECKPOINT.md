---
phase: 02
plan: 08
github_issue: 24
status: complete
completed_tasks: 3
total_tasks: 3
updated: 2026-09-07
---

# Checkpoint de decisión — Plan 02-08

## Tarea 1 — Ratificar los parámetros congelados del protocolo (D-17..D-22)

`gate="blocking-human"`, `reversibility=one-way`. El protocolo `protocol.json` es el
contrato de evidencia EVAL-03: una vez que una comparación citada en el TFG lo referencia
por hash, cambiar relevancia / K / split / métricas / presupuesto de tuning invalida esa
comparación y obliga a re-narrar el capítulo de evaluación.

## Decisión adoptada

**Selección del autor (2026-09-07): `ratify-as-proposed`.** Se congelan D-17..D-22 y la
rejilla de ~18 configuraciones tal como las propone `02-08-PLAN.md` Tarea 1, sin ediciones.

| Parámetro | Valor congelado |
|---|---|
| Relevancia (D-17) | `current_status == "completed"` **O** `rating_half_steps >= 7` (≥ 3.5/5) |
| Split (D-18) | leave-one-out por usuario, semilla determinista; el ítem retirado vuelve al candidate set |
| K (D-19) | report a `[5, 10, 20]`; métrica titular `ndcg@10` |
| Usuarios sintéticos (D-20) | ~8 arquetipos × ~25 (~200) + cohorte cold-start 1-3; arquetipos concretos → Plan 02-09 |
| Tuning (D-21) | split usuarios disjunto ~120/40/40 por semilla; rejilla ≤ 24, congelada en ~18: `weighted_sum` {(0.7,0.3),(0.5,0.5),(0.3,0.7)} × 3 feature sets = 9; `multiplicative` × 3 = 3; `two_stage` bandas {3,5} × 3 = 6. Se puntúa solo en validación; test una sola vez |
| Métricas (D-22) | ranking: `precision@k`, `recall@k`, `ndcg@k`, `map@k` (Fase 2 calcula al menos estas); más-allá-del-acierto + cohortes → Fase 3 |

`corpus_version` y `snapshot_sha256` quedan como placeholder en `protocol.json`, a resolver
en el Plan 02-13 contra el `CorpusVersion` activo.

## Estado

- Tarea 1: **ratificada** (este documento).
- Tarea 2: **completada** (`2f51d16`) — app `evaluation` en `INSTALLED_APPS`, `docs/methodology/protocol.json`
  (12 claves congeladas + `simulation: true`), `docs/methodology/evaluation-protocol.md`
  (`## Amenazas a la validez`), `protocol.py` (loader fail-closed, `frozen_hash`, tope de rejilla,
  marcador de test consumido), `metrics.py` (precision/recall/nDCG/MAP a mano). 46 tests verdes.
- Tarea 3: **completada** (`2696c54`) — `splits.py`: `relevant_positive_ids` (D-17),
  `leave_one_out` determinista por `(seed, user.pk)` con `sha256` del manifiesto de candidatos,
  `user_split` disjunto 120/40/40. 8 tests verdes.
- Cierre: `02-08-SUMMARY.md` escrito; suite completa `pytest apps/api` 280/280; commit de
  metadatos con `Closes #24`.

**Plan 02-08 COMPLETO (2026-09-07).**
