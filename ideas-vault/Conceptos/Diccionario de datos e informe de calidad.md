---
tags: [concepto, tema/datos]
---

# Diccionario de datos e informe de calidad

Artefactos que acompanan al corpus fijo (DATA-03): un diccionario de campos y un
informe de calidad / campos ausentes, para que un investigador entienda y
verifique el dataset sin ejecutar el pipeline.

## Enlaces

- [[Corpus gobernado]] · [[Comando govern_corpus]] · [[Procedencia de datos]]

## Estado de las facetas IGDB — 2026-09-10

La importación aditiva de `themes`, `game_modes`, `player_perspectives` y
`keywords` está verificada en PostgreSQL. Las tablas contienen 22, 6, 7 y
6.546 valores distintos, respectivamente, y las asociaciones cubren 179.744,
234.761, 128.185 y 131.829 obras; las cifras coinciden con la evidencia de
importación. No hay nombres vacíos ni IDs IGDB duplicados.

El análisis semántico y la depuración quedan aplazados. Mientras tanto, las
facetas se conservan como enriquecimiento no gobernado y no alimentan el
corpus, la caché de vectores ni los recomendadores. La verificación completa y
el plan posterior están en [la evidencia de facetas](../../docs/verification/igdb-facets-import-2026-09-10.md).

## Estado de las facetas IGDB — 2026-09-10

La importación aditiva de `themes`, `game_modes`, `player_perspectives` y
`keywords` está verificada en PostgreSQL. Las tablas contienen 22, 6, 7 y
6.546 valores distintos, respectivamente, y las asociaciones cubren 179.744,
234.761, 128.185 y 131.829 obras; las cifras coinciden con la evidencia de
importación. No hay nombres vacíos ni IDs IGDB duplicados.

El análisis semántico y la depuración quedan aplazados. Mientras tanto, las
facetas se conservan como enriquecimiento no gobernado y no alimentan el
corpus, la caché de vectores ni los recomendadores. La verificación completa y
el plan posterior están en [[../../docs/verification/igdb-facets-import-2026-09-10]].
