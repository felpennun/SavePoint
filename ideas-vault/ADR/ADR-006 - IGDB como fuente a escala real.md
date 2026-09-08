---
tags: [adr, tema/datos]
---

# ADR-006 - IGDB como fuente a escala real

**Estado:** aceptado (2026-09-05). Fuente: `docs/adr/ADR-006-igdb-source.md`.
Requisito DATA-04; desbloquea CAT-02 y REC-10.

Decision: adoptar IGDB v4 como fuente del catalogo a escala real. Es el unico
candidato que combina cobertura real (~312.000 juegos primarios `game_type=0`),
modelado de primera clase de genero/plataforma/portada, **sin cuota mensual**,
coste cero y permiso publicado del operador para almacenar y servir los datos.
Portadas por hotlink (no replicadas); ausentes caen al placeholder de la Fase 1.
No se re-sindica el dataset en bloque. Atribucion estatica "Data from IGDB.com".
Nueva dependencia: `requests==2.34.2`.

Comparado con RAWG (techo de 20.000 req/mes, backlink obligatorio a rawg.io) y
Wikidata escalado (CC0 mas limpio pero cobertura de juegos escasa e inestable).

## Enlaces

- [[IGDB]] · [[RAWG]] · [[Wikidata]] · [[Atribucion]] · [[Legalidad y licencias]]
- [[ADR-003 - Snapshot Wikidata CC0]] · [[ADR-008 - Ratings externos gobernados y RAWG]]
- [[Fase 01.1 - Catalogo a escala real]] · [[Jobs offline]]
