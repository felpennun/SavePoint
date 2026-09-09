---
quick_task: include-igdb-franchise-saga-as-recommendation-signal
created: 2026-09-09
status: complete
---

# Incluir franquicia IGDB como señal de saga

## Objetivo

Aplicar la decisión del autor de que `franchise` de IGDB representa saga y no debe
descartarse por su baja cobertura global.

## Entregables

1. Activar la faceta `franchise:<slug>` cuando exista en alguna obra gobernada.
2. Invalidar la caché vectorial anterior mediante una nueva versión de features.
3. Actualizar pruebas, auditoría, documentación canónica y vault.

## Restricción

No ejecutar algoritmos, tuning ni evaluación.
