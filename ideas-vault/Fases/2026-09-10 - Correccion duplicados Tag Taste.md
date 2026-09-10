---
fecha: 2026-09-10
estado: vigente
fuente: [[docs/verification/tag-taste-deduplication-2026-09-10]]
---

# Corrección de duplicados en Tag Taste

## Qué ha cambiado

`tag-taste-v1` deduplica los juegos antes de aplicar el límite y también deduplica
las etiquetas de evidencia por obra. La publicación actualiza snapshots existentes
cuando se regenera una revisión.

## Impacto

La sección `tags` de `felipe` vuelve a mostrar 20 juegos distintos. Las múltiples
fuentes de una misma etiqueta siguen conservándose en la tabla de evidencia, pero
no multiplican resultados ni puntuación.

## Enlaces relacionados

- [[Fases/2026-09-10 - Taxonomía editorial unificada]]
- [[docs/verification/tag-taste-deduplication-2026-09-10]]
