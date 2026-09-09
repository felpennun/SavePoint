---
quick_task: integrate-pending-evaluation-runner
status: complete
completed: 2026-09-09
---

# Resumen

Se integraron los cambios pendientes de evaluación y sus evidencias.

- `metrics.py` incorpora cobertura de catálogo, cobertura de predicción, concentración HHI,
  diversidad intra-lista y novedad, con denominadores y valores no estimables explícitos.
- `runner.py` verifica el hash de PopScore, conserva snapshots con `total_rating_count`,
  calcula novedad usando exclusivamente interacciones de entrenamiento y persiste valores por
  usuario y agregados beyond-accuracy.
- Se archivaron las evidencias del corpus gobernado, popularidad, ratings y materialización de
  PopScore para `2026.09.2`.
- Se añadió la prueba conocida de beyond-accuracy y se alineó el fixture de candidatos con la
  regla congelada: cualquier rating IGDB no nulo satisface la alternativa de elegibilidad.
- La suite dirigida pasó: **120 tests**.
- No se ejecutó ningún algoritmo ni evaluación experimental.

La caché `fs-v4` queda explicada en
`docs/verification/evaluation-runner-integration-2026-09-09.md`.
