---
tags: [concepto, tema/producto, fase/5]
---

# Importacion y exportacion

**Actualizado tras el cierre de la Fase 5 (Plan 05-04, D-08/D-09):** el usuario
exporta su coleccion, valoraciones, listas, comentarios y favoritos visibles en
un CSV UTF-8 versionado, determinista y owner-scoped (PORT-01, solo CSV; JSON
queda fuera de este cierre). Las celdas CSV neutralizan formulas potencialmente
maliciosas de forma idempotente (PORT-04, `neutralize_spreadsheet_formula` en
`apps/api/library/export.py`).

La previsualizacion y validacion de una importacion antes de aplicarla (PORT-02)
y los resultados de fila deterministas ante errores y duplicados (PORT-03)
quedan **pendiente**, asignados explicitamente a la Fase 7: ningun endpoint,
parser ni test de feature de importacion existe en `apps/api/library` tras la
Fase 5. Vease la matriz de decision en
`.planning/phases/05-complete-collection-workflows-and-portability/05-PORTABILITY-RECONCILIATION.md`.

## Enlaces

- [[Listas personalizadas]] · [[Inventario de copias]] · [[Reproducibilidad academica]]
- [[Fase 5 - Coleccion y portabilidad]]
