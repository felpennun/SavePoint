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
algoritmos y no consume el marcador del split `test`. La evaluación final de
los 400 usuarios no se ejecutó durante esta implementación.

Verificación: `test_parallel.py` cubre combinación y fallo controlado; el
protocolo v9 declara la política de proceso por algoritmo y medición temporal.
