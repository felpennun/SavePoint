---
phase: 04-collaborative-and-hybrid-comparison
plan: 03
status: complete
---

# Resumen 04-03 — Evaluación offline paralela

Se añadió el comando `run_evaluation_parallel`, que crea un proceso aislado
por algoritmo, limita la concurrencia mediante `--max-workers` y combina solo
artefactos completos con hashes compartidos. Cada worker registra inicio, fin,
duración, estado y error; el artefacto combinado registra tiempo de pared y
suma de tiempos de workers.

Un fallo genera un manifiesto explícito `status: failed`, deja vacío el mapa de
algoritmos y no consume el marcador del split `test`. Tras la implementación se
ejecutó el protocolo v15 sobre los 400 usuarios sintéticos: terminó con 16/16
algoritmos y 79/80 usuarios evaluables. El resultado está congelado en
`docs/verification/evaluation-results-400-test-2026-09-12-v15.md` y no se repite
porque el split de test se consume una sola vez.

La ejecución v15 usó `max_workers=2` y `serial_tail=5`, registró 4.297,9 s de
tiempo de pared y dejó tiempos individuales por algoritmo. La ausencia de
repetición multi-semilla se conserva como limitación metodológica explícita,
no como un fallo silencioso de la implementación.

Verificación: `test_parallel.py` cubre combinación y fallo controlado; el
protocolo v9 declara la política de proceso por algoritmo y medición temporal.
