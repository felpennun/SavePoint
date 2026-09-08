---
tags: [concepto, tema/recomendadores, fase/1]
---

# Baseline de popularidad

`rank_popularity_v1` (REC-02): agregado **no personalizado** sobre filas
`LibraryEntry`, con una tabla de pesos explicita (estado + `rating_half_steps/10`),
desempate determinista y un DTO que siempre declara `algorithm_id`,
`generated_at`, `input_snapshot_sha256` y una cadena `limitation`. Establece el
"patron de la casa" para un ranking defendible y no-ML que replican los demas.

Aislado del baseline: las cuentas `synthetic-eval-user` no alteran este agregado
publico.

## Enlaces

- [[Heuristico de gusto por generos]] · [[Baseline aleatorio]] · [[Versionado de resultados]]
- [[ADR-007 - Heuristico de gusto por generos]] · [[Fase 1 - Demo publico de tres dias]]
