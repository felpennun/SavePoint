# Corrección de duplicados en `tag-taste-v1`

Fecha: 2026-09-10  
Alcance: cuenta demo `felipe`, revisión de colección 14.

## Causa

`GameWorkCuratedLabel` conserva una fila por evidencia de procedencia. Una misma
obra y etiqueta pueden aparecer varias veces cuando la etiqueta procede de más de
una faceta curada. La consulta de candidatos de `tag-taste-v1` aplicaba un límite
sin deduplicar previamente los `work_id`, por lo que una obra podía ocupar varias
posiciones del resultado.

Además, la publicación de snapshots usaba `get_or_create()` sin actualizar el
payload cuando ya existía un snapshot para la misma revisión e identidad de entrada.

## Corrección

- La consulta de candidatos aplica `DISTINCT` sobre el identificador de obra antes
  del límite.
- La heurística deduplica las etiquetas por identificador al construir
  `matched_tags` y la puntuación.
- Una regeneración actualiza el snapshot existente con el payload nuevo.

## Verificación

La ejecución de `tag-taste-v1` y su snapshot publicado para `felipe` producen:

- 20 resultados.
- 20 `work_id` únicos.
- Ningún duplicado de obra en la sección `tags`.
- Trabajo `tag-taste-v1` en estado `succeeded`, sin error.
