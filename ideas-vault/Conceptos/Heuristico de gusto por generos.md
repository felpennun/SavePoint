---
tags: [concepto, tema/recomendadores, fase/1.1]
---

# Heuristico de gusto por generos

`rank_genre_taste_v1`: conteo de frecuencia de generos determinista, sin estado y
en tiempo de peticion, acotado a un usuario. Suma pesos de actividad (estado +
rating) por genero, rankea obras del catalogo por solapamiento de generos,
excluye obras ya en biblioteca y DLC, desempata por `canonical_slug` y adjunta
`matched_genres` como evidencia de explicacion. Historial insuficiente devuelve
una forma explicita (`insufficient_history: true`), nunca un fallback al agregado
publico.

Es funcionalidad de **producto**, no la contribucion algoritmica de la tesis
(ver [[ADR-007 - Heuristico de gusto por generos]]).

## Enlaces

- [[Baseline de popularidad]] · [[Recomendador basado en contenido]] (lo sustituira)
- [[Explicabilidad]] · [[Arranque en frio]] · [[Pagina de recomendaciones]]
