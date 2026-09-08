---
tags: [adr, tema/datos, tema/evaluacion]
---

# ADR-008 - Ratings externos gobernados y RAWG

**Estado:** aceptado por el autor (2026-09-07). Fuente:
`docs/adr/ADR-008-external-ratings.md`. Requisitos DATA-05..08, DOC-02.

Decision: IGDB sigue siendo fuente primaria; se anade un enriquecimiento RAWG
**offline** acotado a `N=10.000` obras por ejecucion sobre el corpus gobernado
activo. `enrich_rawg_ratings` no corre en rutas HTTP, no muta `GameWork.rating`,
escribe observaciones separadas en `CorpusRatingSnapshot(source="rawg")`,
reconcilia por slug exacto y luego titulo normalizado + ano (sin fuzzy) y
convierte la escala 0-5 a 0-100. La senal primaria es el rating de usuarios.

Resultado autenticado 2026-09-07: 8.575 obras emparejadas, **0 cobertura nueva**
(el top-10.000 por `rating_count` ya tenia rating IGDB). RAWG queda como segunda
cadena de procedencia contrastable, no como via para subir cobertura. Toda
superficie con datos RAWG muestra backlink activo a rawg.io.

## Enlaces

- [[Ratings externos]] · [[RAWG]] · [[IGDB]] · [[Snapshot inmutable]]
- [[Reconciliacion determinista]] · [[Procedencia de datos]] · [[Corpus gobernado]]
- [[Fase 2 - Corpus gobernado y evaluacion]]
