# IDF por rareza de etiquetas

Fecha: 2026-09-10
Estado: decisión aplicada

## Decisión

Los vectores de contenido aplican IDF suavizado a las etiquetas curadas para
reducir la influencia de tags genéricos y destacar los específicos. El bloque
de etiquetas se renormaliza por L2 a `0,75`; plataformas mantiene `0,25` y los
bonuses de franquicia y desarrollador no cambian.

## Contrato

```text
idf(tag) = ln((N + 1) / (df_tag + 1)) + 1
peso(tag, obra) = 0,75 * idf(tag) / sqrt(sum(idf(tag_j)^2))
```

El mapa se calcula por `corpus_version` y se comparte entre workers web y
evaluación offline. Se incrementan las versiones a `fs-v12-curated-tags-idf`,
`facet-similarity-v7` y protocolo `12`.

Fuente: `docs/verification/similitud-curated-tags-2026-09-10.md`.
