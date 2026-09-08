---
tags: [adr, tema/recomendadores]
---

# ADR-007 - Heuristico de gusto por generos

**Estado:** aceptado (2026-09-06). Fuente:
`docs/adr/ADR-007-genre-taste-heuristic.md`. Requisito REC-10.

Decision: entregar `rank_genre_taste_v1(user, limit)` en `apps/api/recommendations/`:
un heuristico de frecuencia de generos determinista, sin estado y en tiempo de
peticion, acotado a un usuario, en `GET /api/recommendations/genre-taste/` tras
`IsAuthenticated`. Peso de actividad = peso de estado (completed 3, playing 2,
pending 1, abandoned/sin estado 0) + `rating_half_steps/10`. Excluye obras ya en
biblioteca y DLC. Desempate por `canonical_slug`. Consulta acotada por indice
(catalogo de 312k filas) y `input_snapshot_sha256` para reproducibilidad.

**Frontera:** es funcionalidad de **producto**, no la contribucion algoritmica de
la tesis. Sin arranque en frio real (solo lo declara). Lo sustituira el
[[Recomendador basado en contenido]] de fase posterior manteniendo URL y DTO.

## Enlaces

- [[Heuristico de gusto por generos]] · [[Baseline de popularidad]] (baseline hermano)
- [[Explicabilidad]] · [[Reproducibilidad academica]] · [[Pagina de recomendaciones]]
- [[Fase 01.1 - Catalogo a escala real]]
