---
phase: 02
plan: 08
github_issue: 24
status: in_progress
completed_tasks: 1
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
- Tarea 2: pendiente — app `evaluation`, `protocol.json` + `evaluation-protocol.md`, `metrics.py`, tests.
- Tarea 3: pendiente — `splits.py` (leave-one-out por usuario + partición train/val/test), tests.
- Cierre: `02-08-SUMMARY.md` + commit con `Closes #24`.
