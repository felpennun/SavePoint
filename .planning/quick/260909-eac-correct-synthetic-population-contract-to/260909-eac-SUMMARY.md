---
name: correct-synthetic-population-contract
status: complete
completed: 2026-09-09
---

# Resumen

Corregido el contrato: los 400 usuarios de la Fase 3 sustituyen a los 200 de
la Fase 2 como población activa. El split queda en 240 train, 80 validation y
80 test; se conservan las cohortes 10/100/50/240. La población titular se ha
persistido con la semilla `20260909`, selección escalonada por `rating_count >= 1`
y pesos 1/2/4/8/16/32. La BD contiene 400 usuarios activos y conserva los 200
históricos con marcador de Fase 2; no se ha ejecutado ningún algoritmo ni
evaluación.
