---
quick_task: include-igdb-franchise-saga-as-recommendation-signal
status: complete
completed: 2026-09-09
---

# Resumen

Se aplicó la decisión de incluir `franchise` de IGDB como señal de saga.

- La cobertura de saga es 11.555/190.479 obras (6,07 %), pero la señal queda activa
  cuando existe; las obras sin saga omiten esa dimensión.
- La versión de vectores pasa de `fs-v3` a `fs-v4` para invalidar cachés previas.
- El desarrollador conserva su umbral de cobertura del 50 %.
- La auditoría actualizada confirma `include_franchise: true`.
- Pruebas de recomendaciones: 35 pasadas.
- No se ejecutó ningún algoritmo ni evaluación.
