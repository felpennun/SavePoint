---
tags: [concepto, tema/datos, fuente, fase/2]
---

# RAWG

Segunda cadena de procedencia contrastable para ratings, anadida en la Fase 2
(ADR-008). Enriquecimiento **offline** acotado a `N=10.000` obras por ejecucion
(por debajo de las 20.000 req/mes del plan gratuito). Solo usa `rating` y
`ratings_count` convertidos de escala 0-5 a 0-100; no muta `GameWork.rating`.
Exige backlink activo a `https://rawg.io` en toda superficie que muestre sus
datos. En la ejecucion del 2026-09-07 aporto **0 cobertura nueva**.

## Enlaces

- [[IGDB]] · [[Ratings externos]] · [[Reconciliacion determinista]] · [[Atribucion]]
- [[ADR-008 - Ratings externos gobernados y RAWG]]
