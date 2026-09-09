---
phase: 04-collaborative-and-hybrid-comparison
plan: 01
status: complete
---

# Resumen 04-01 — Rankers compartidos

Se implementaron exactamente dos algoritmos nuevos:

- `cf-user-knn-v1`: vecinos de usuario sobre ratings explícitos de
  `LibraryEntry`, normalizados a `[0,1]`, centrados por media, con mínimo de
  dos obras comunes y los 20 vecinos positivos más similares.
- `hybrid-weighted-cf-v1`: combinación `0,60 * Weighted + 0,40 * CF`, con
  fallback explícito a contenido cuando no existe vecindario colaborativo.

Ambos rankers comparten el DTO, manifiesto de candidatas y exclusiones del
servicio web y del runner offline. El fallback colaborativo usa frecuencia de
interacción de la población de referencia y no inventa similitud individual.

Verificación: `test_phase4.py` y la regresión completa de `apps/api` pasan.
