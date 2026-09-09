---
name: update-recommendation-grids-and-signal-contract
status: complete
completed: 2026-09-09
---

# Resumen

Se actualizó el contrato de señales de la Fase 3 sin ejecutar algoritmos ni
evaluaciones.

## Cambios

- La rejilla de `docs/methodology/protocol.json` pasa a 24 configuraciones:
  15 `weighted_sum`, 3 `multiplicative` y 6 `two_stage`.
- `recency-v1` combina contenido, rating de usuarios, volumen total y PopScore,
  y añade `recency_score` con semivida de 365 días.
- `total_rating` combinado con crítica queda fuera de las fórmulas; `rating` de
  usuarios es la única nota de calidad. `total_rating_count` es elegibilidad y
  volumen.
- El snapshot conserva `total_rating_count` mediante migración aditiva y el
  protocolo fija corpus `2026.09.2`, hash de ratings y hash de PopScore.
- Se actualizaron el runner, DTO, metodología, contexto de fase y vault vivo.

## Verificación

- Migración aplicada y `makemigrations --check --dry-run`: sin cambios.
- `31 passed` en protocolo y snapshot de ratings.
- `57 passed` en protocolo, runner y variantes content.
- No se ejecutó `run_evaluation` ni un ranking de producción.

## Nota de integración

`apps/api/evaluation/runner.py`, `apps/api/evaluation/metrics.py` y
`apps/api/evaluation/tests/test_beyond_accuracy.py` ya tenían cambios paralelos
del trabajo 03-03; se conservaron y no se deben resetear.
