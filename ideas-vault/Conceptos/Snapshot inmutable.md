---
tags: [concepto, tema/datos, tema/evaluacion]
---

# Snapshot inmutable

`CorpusRatingSnapshot` conserva observaciones de rating **inmutables** por
`corpus_version` y `source`. Los datos mutables de la API no pueden alterar
retrospectivamente un experimento cerrado (DATA-06). El runner rechaza una
ejecucion si falta un snapshot para una obra gobernada con rating o si hay deriva
de version.

## Enlaces

- [[Ratings externos]] · [[Corpus gobernado]] · [[Procedencia de datos]]
- [[Artefacto de evaluacion reproducible]] · [[Control contra errores]]
