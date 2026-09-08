---
tags: [concepto, tema/recomendadores, fase/2]
---

# Recomendador basado en contenido

Primer recomendador avanzado de la tesis (REC-03). Combina la afinidad de genero
propia del usuario con los ratings externos agregados de juegos comparables,
excluye titulos ya consumidos, muestra una explicacion determinista basada en
features persistidas y registra versiones de modelo, features y datos de entrada.
Laboratorio parametrico con tres modos de combinacion (`weighted_sum`,
`multiplicative`, `two_stage`) y varios conjuntos de features; variantes con
nombre en `apps/api/recommendations/content/variants.py`. Para obras sin rating
observado usa la mediana marcada de sus generos como fallback y propaga
`rating_term_is_fallback`.

## Enlaces

- [[Explicabilidad]] · [[Arranque en frio]] · [[Exclusion de ya consumidos]]
- [[Versionado de resultados]] · [[Ratings externos]] · [[Feature vectors de contenido]]
- [[Protocolo de evaluacion congelado]] · [[ADR-008 - Ratings externos gobernados y RAWG]]
