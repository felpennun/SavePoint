---
tags: [adr, tema/datos]
---

# ADR-003 - Snapshot Wikidata CC0

**Estado:** aceptada y corpus congelado. Fuente: `docs/adr/ADR-003-data-sources.md`.

Decision: congelar 150 juegos de datos estructurados de Wikidata declarados CC0,
conservando consulta, URL, corte UTC y SHA-256. Cada archivo de Wikimedia Commons
se trata por separado: solo `candidate` con autor, licencia, URL de licencia y
fuente completas; en otro caso, placeholder propio. No se consultan proveedores
en runtime.

Acotada despues por [[ADR-006 - IGDB como fuente a escala real]] para el catalogo
a escala real, pero sigue vigente para el corpus de la Fase 1 y el comportamiento
en tiempo de peticion.

## Enlaces

- [[Wikidata]] · [[Wikimedia Commons]] · [[Snapshot inmutable]]
- [[Procedencia de datos]] · [[Legalidad y licencias]] · [[Identificadores canonicos]]
- [[Fase 1 - Demo publico de tres dias]]
