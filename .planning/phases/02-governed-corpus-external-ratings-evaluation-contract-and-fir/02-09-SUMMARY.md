---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 09
status: complete
completed: 2026-09-07
requirements: [EVAL-09, EVAL-10, AUTH-02]
---

# Phase 2 Plan 09: usuarios sintéticos reproducibles — resumen

## Resultado

Se implementó una población de 200 usuarios sintéticos, distribuida en ocho arquetipos
paramétricos de 25 usuarios cada uno. La cohorte `jugador-ocasional-cold-start` contiene
25 perfiles con entre uno y tres juegos. La semilla `20260907` produjo historiales
deterministas sobre el corpus `2026.09.1` y se persistió de forma idempotente en la base
local.

Cada cuenta usa `DemoAccountIdentity` con `marker="synthetic-eval-user"`, `seed_key`
determinista y ancla UUID derivada mediante `uuid.uuid5`. El baseline `rank_popularity_v1`
excluye este marcador, por lo que la población de evaluación no altera la superficie pública
ni el ranking de popularidad de la demo.

## Archivos principales

- `apps/api/evaluation/archetypes.py`: arquetipos, rangos y mezclas de estados.
- `apps/api/evaluation/synthetic.py`: generación en memoria, validación, persistencia
  transaccional y renderizado del informe.
- `apps/api/evaluation/management/commands/generate_synthetic_users.py`: comando con
  `--seed`, `--corpus-version`, `--dry-run` y `--validation-report`.
- `docs/verification/synthetic-users-validation.md`: informe estadístico reproducible y
  limitación EVAL-10.

## Commits

| Commit | Descripción |
|---|---|
| `0b90de7` | `feat(02-09): add deterministic synthetic evaluation users` |

## Verificación

- Pruebas específicas de 02-09 y popularidad: **17 passed**.
- Suite completa del backend en Docker: **352 passed**.
- Ejecución real `--dry-run`: 200 usuarios validados y 25 cold-start.
- Persistencia real: 200 cuentas creadas con sus historiales; una segunda ejecución actualiza
  las mismas identidades mediante sus `seed_key`, sin duplicarlas.
- El informe no contiene contraseñas ni datos personales.

## Desviaciones y límites

La generación usa la taxonomía de géneros disponible en el corpus gobernado; la
"concentración de saga" se aproxima mediante concentración en un género porque el modelo de
catálogo todavía no incorpora una entidad de franquicia. La evidencia obtenida es de
simulación controlada y no permite concluir comportamiento de usuarios reales.

## Self-Check: PASSED

Todos los archivos del plan existen, el marcador sintético está separado del marcador de
demo normal, la persistencia es atómica y las verificaciones automatizadas requeridas están
en verde.
