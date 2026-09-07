---
phase: 02
plan: 10
github_issue: 26
status: complete
completed_tasks: 3
total_tasks: 3
updated: 2026-09-07
---

# Checkpoint de decisión — Plan 02-10

## Tarea 1 — Python puro vs adoptar `numpy` ahora

`gate="blocking"`. Reversibilidad: barata (reescritura acotada de la aritmética de
vectores/métricas) pero cambia la superficie de revisión de seguridad.

## Decisión adoptada

**Selección del autor (2026-09-07): `pure-python`** — a recomendación del asistente.

### Motivo

1. Es la **recomendación primaria de `02-RESEARCH.md`** (Standard Stack, Open Question 2):
   vectores dispersos (~10 no-ceros), escala offline (≤150k obras × ~200 usuarios × ≤24
   configs) que no necesita vectorización para un runtime aceptable.
2. Mantiene la **postura de dependencias mínimas** del proyecto (5 directas, cada una con
   gate de legitimidad + pin + 4 artefactos + ledger + ADR). Adoptar `numpy` ahora dispara
   toda esa maquinaria para algo que RESEARCH dice que aún no hace falta.
3. **Coherencia**: `apps/api/recommendations/genre_heuristic.py` (recomendador de la Fase 1)
   ya es Python + stdlib.
4. **Superficie de revisión de seguridad** (Fase 7): un TFG sobre métodos reproducibles y
   defendibles se beneficia de un conjunto de dependencias mínimo y auditable; `numpy` es
   grande (extensiones C, BLAS).
5. El contraargumento (reescritura en la Fase 3) es débil: la reescritura es **acotada**
   (aritmética de vectores + funciones de métrica); la Fase 3 necesita `numpy` sobre todo
   para la **capa estadística** (EVAL-08: incertidumbre, tests de significación), que es
   otra ruta de código distinta del coseno del recomendador; y diferir permite decidir con
   las cifras reales de rendimiento de la Fase 2 en la mano.
6. Reversibilidad asimétrica: añadir `numpy` más tarde es fácil; quitarlo del set de
   dependencias / ledger / ADR / superficie de seguridad, no.

La Fase 3 revisita `numpy` para la capa estadística con datos de rendimiento reales.

## Estado

- Tarea 1: **ratificada** (este documento). No se dispara el gate de dependencias.
- Tarea 2: **completa** — `rank_random_v1` (REC-01) + coseno stdlib. RED `50b3194` -> GREEN `6a8341e`.
- Tarea 3: **completa** — `feature_vector` / `coverage_report` / `genre_rating_profile`, `build_profile`,
  `WorkFeatureVector` + migración `0001_work_feature_vector`, comando `rebuild_feature_vectors`.
  RED `6043036` -> GREEN `d189117`.
- Cierre: `02-10-SUMMARY.md` escrito; commit de metadatos con `Closes #26`.
- Verificación: `pytest apps/api/recommendations -q` -> 48 passed; suite completa
  (`-w /workspace/apps/api`) -> 345 passed, 0 regresiones; `makemigrations --check` limpio.
