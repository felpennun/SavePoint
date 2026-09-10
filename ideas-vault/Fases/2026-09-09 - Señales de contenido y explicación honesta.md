---
tags: [fase/3, tema/recomendadores, tema/explicabilidad, estado/completado]
---

# Señales de contenido y explicación honesta

## Resultado

El plan 03-02 introduce `fs-v2` y separa la señal personal positiva de la negativa.
Solo `completed` y `playing` con al menos 3,5/5 construyen afinidad positiva. Tres
ratings bajos del mismo género habilitan únicamente `content-cbf-neg-v1`, una variante
identificable y reversible.

El ranking expone parámetros, umbrales y disponibilidad de señales. Rating externo y
volumen de valoraciones proceden de la instantánea gobernada; una ausencia sigue siendo
`null`. PopScore, franquicia y desarrollador no se inventan: el corpus todavía no los
persiste y permanecen marcados como no disponibles hasta un import con snapshot y
procedencia.

Las razones son tokens deterministas de género o plataforma presentes en el resultado.
La API los convierte a nombres canónicos y la interfaz reutiliza la plantilla localizada
aprobada; cuando no hay evidencia devuelve una razón ausente.

## Reapertura de contrato — 2026-09-09

El autor añade que la valoración propia de cada juego semilla debe figurar
explícitamente como intensidad de preferencia. `ProfileInputs` registra el
número de semillas positivas, la suma y la media de sus `rating_half_steps`;
no confunde esa señal personal con el rating externo del candidato.

Franquicia y desarrolladora pasan a persistirse con su ID IGDB estable. La
franquicia se interpreta como saga y entra en `fs-v4` siempre que exista en
alguna obra; no se descarta por cobertura global. El desarrollador mantiene el
umbral del 50 %.
PopScore se prepara como instantánea de primitivas crudas por obra, tipo,
fecha, fuente y hash; todavía no tiene un peso activo en el recomendador.

La decisión del autor de 2026-09-09 trata `franchise` de IGDB como la señal de saga. Se
incluye aunque su cobertura sea baja; las obras sin franquicia omiten esa dimensión, sin
imputación ni exclusión global.

La composición acordada usa exclusivamente `Visits`, `Want to Play`,
`Playing` y `Played` de IGDB. Cada tipo se normaliza con `log1p` y percentil de
rango medio en su snapshot; `igdb-engagement-mean-v1` es la media simple de
las cuatro y se declara ausente si falta una. El valor ya es trazable en el
DTO, pero todavía no cambia la puntuación de ningún recomendador.

La recencia se calcula por separado en `recency-v1`: `exp(-ln(2) * edad_días /
365)`, solo en obras ya lanzadas y con rating externo observado. Es un
algoritmo independiente; no cambia el orden de las variantes de contenido ni
el de PopScore.

No se ha consultado IGDB, ni se ha reimportado o gobernado un corpus nuevo, ni
se han ejecutado experimentos. La decisión siguiente es revisar esta base y,
solo después, publicar un nuevo corpus y capturar sus instantáneas.

## Frontera de catálogo y candidatos — 2026-09-09

El autor separa dos vistas sin duplicar obras. El catálogo de una versión nueva
incluye únicamente juegos con fecha conocida ya publicada al corte fijado; los
futuros y sin fecha continúan almacenados, pero no se muestran. El universo de
salida de los algoritmos es el subconjunto
`total_rating_count >= 1 OR rating IS NOT NULL`, sin el umbral histórico de
1.000 valoraciones. La biblioteca del usuario puede conservar cualquier juego
del catálogo y usarlo como semilla.

`rating` y `rating_count` proceden de usuarios de IGDB; `total_rating` y
`total_rating_count` agregan usuarios y crítica externa. La reimportación
aditiva, el corpus `2026.09.2` y sus snapshots ya están completados; no se ha
calculado ningún ranking.

La auditoría confirmó que no hay títulos ni slugs vacíos. Las obras futuras,
sin fecha y los DLC permanecen almacenados, pero fuera de la vista gobernada.
Las ausencias parciales de señales opcionales son cobertura real de IGDB y no
se rellenan artificialmente. El PopScore compuesto se materializó en
`CorpusPopularityScore` para las obras con las cuatro primitivas observadas.

## Importación de facetas de clasificación IGDB — 2026-09-09

El autor decide traer en crudo las cuatro facetas de clasificación fina que
IGDB ofrece y que el catálogo no importaba: `themes` (vocabulario cerrado,
~22), `player_perspectives` (7), `game_modes` (~6) y `keywords` (etiquetas
libres de la comunidad, decenas de miles). IGDB no tiene un concepto de
«subgénero» con jerarquía: los géneros son planos y estas facetas son lo más
parecido a una clasificación más fina.

El primer paso es solo **persistir**, sin interpretarlas. El contrato acordado:
upserts idempotentes que nunca sobrescriben un valor observado con `null`;
nada de migraciones, gobierno del corpus, recálculo de PopScore,
reconstrucción de vectores ni reinicios de workers en paralelo; relaciones
nuevas por lotes con checkpoint (el importador ya es reanudable); y ninguna
faceta entra en el recomendador hasta una versión posterior explícita con
nueva caché de features y evaluación.

Las facetas quedan **fuera** del `_record_digest` y del checksum de contenido
del catálogo, y fuera del corpus gobernado: son enriquecimiento aditivo, no
identidad. Así, adjuntarlas no mueve la evidencia congelada ni obliga a
refrescar pins de hash ni el ledger.

Pendiente para una versión posterior: normalización de `keywords` mediante un
mapa de sinónimos versionado y con hash (por ejemplo `roguelike` /
`rogue-like` / `roguelite` colapsados a un canónico), denylist de metadatos de
tienda y umbral de frecuencia. Es una decisión editorial que afecta a los
resultados del recomendador y necesitará su propia nota de metodología;
fusionar `roguelike` con `roguelite` es defendible pero no es un hecho de los
datos.

Implementado: modelos `Theme`, `PlayerPerspective`, `GameMode`, `Keyword` con
sus M2M en `GameWork` (patrón `Genre`); migración
`catalogue/0014_igdb_content_facets` (solo tablas nuevas, segura con los
workers en marcha); `GAME_FIELDS` ampliado por dot-expansion sin coste de
cuota; parseo y `.add()` idempotente en `import_igdb_catalogue`, con cobertura
de facetas en el JSON de evidencia. Seguimiento en la issue #43.

Resultado de la pasada (2026-09-09, ~1h52 sobre el contenedor `db` local):
`complete`, 626 lotes, 330.850 obras IGDB (136 nuevas absorbidas de forma
aditiva, 312.740 actualizadas, 0 descartadas). Cobertura:

- `themes` — 22 valores, 179.744 obras. Top: Action (107.862), Fantasy
  (24.806), Science fiction (18.977), Horror (18.004).
- `game_modes` — 6 valores, 234.761 obras. Single player (223.984),
  Multiplayer (45.412), Co-operative (21.708).
- `player_perspectives` — 7 valores, 128.185 obras. Bird view / Isometric
  (36.516), Side view (33.132), First person (30.236).
- `keywords` — 6.546 valores distintos, 131.829 obras, ~490k enlaces. Los
  valores más frecuentes confirman el problema de ruido previsto: «digital
  distribution», «steam achievements», «steam», «nudity», «sexual content»,
  «2d», «casual», «licensed game», «unofficial». Sin curación no son usables
  como señal explicable.

El checksum de contenido del catálogo pasó a `b9729c7f257fd30c…` únicamente
por las 136 obras nuevas de upstream (mismo fenómeno ya documentado en
`igdb-catalogue-freeze.md`): el `diff` de `_record_digest` es solo un
comentario, sin ninguna clave de faceta añadida, y ocho pruebas confirman que
adjuntar o quitar facetas converge al mismo checksum.

## Evidencia canónica

- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-PLAN|Plan 03-02]]
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-SUMMARY|Resumen 03-02]]
- [[../../docs/verification/igdb-import-audit-2026-09-09|Auditoría de importación IGDB y señales]]
- Issue #43 — Importar facetas de clasificación IGDB (themes, keywords, player_perspectives, game_modes)
- `apps/api/igdb-facets-import-evidence.json` — cobertura de la pasada de facetas
- `apps/api/recommendations/content/profile.py`
- `apps/api/recommendations/content/rank.py`
- `apps/api/recommendations/tests/test_content_v2.py`

## Verificación

- 43 pruebas específicas de recomendaciones y evaluación pasan.
- TypeScript del frontend pasa.
- La suite backend completa pasa: 409 pruebas en 74,82 s.

## Enlaces

- [[2026-09-08 - Tracer v2 de recomendaciones]]
- [[Explicabilidad]]
- [[Fase 3 - Recomendadores explicables y baselines]]
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-CONTEXT|Contexto de fase 03]]

## Curación inicial de subgéneros — 2026-09-10

El autor fija el primer mapa editorial para convertir una selección explícita
de `keywords` en una variable derivada `subgenres`. La capa bruta permanece
intacta y las keywords no listadas no se promocionan silenciosamente: quedan
fuera del corpus curado hasta una decisión posterior. `gamedev`, `gamejam`,
`gameshow` y `highscore` quedan excluidas de forma explícita.

La versión aplicada es `subgenres-2026.09.10-v1`, con frecuencia mínima de dos
obras. El mapa colapsa `rogue-like`/`roguelite`/`roguelike` en `roguelike` y
conserva el contexto de los compuestos (`action roguelike`,
`roguelike deckbuilding`). El resultado publicado contiene 41 subgéneros,
18.159 obras y 22.514 asociaciones. La evidencia canónica está en
[[../../docs/verification/subgenre-curation-2026-09-10|Curación reproducible de subgéneros]]
y la implementación en `apps/api/catalogue/subgenres.py`.

## Propuesta de clasificación semántica — 2026-09-10

La lista inicial mezcla subgéneros con temas, mecánicas, modos, presentación,
época, licencias y ruido. La propuesta es conservar tres espacios separados:
`subgenre` para familias de juego, `theme` para ambientación/tono/tema y una
tercera capa para mecánicas, modos y formato. No se deben generar todas las
combinaciones posibles entre temas y subgéneros; pueden combinarse en el vector
del recomendador con pesos independientes y explicaciones como «roguelike» +
«fantasía».

Se consideran subgéneros o familias de juego defendibles: `action roguelike`,
`action rpg`, `autobattler`, `jrpg`, `match3`, `minigolf` como subgénero
deportivo, `roguelike`, `roguelike deckbuilding`, `shoot'em up`, `spacecombat`
y `wargame`. `autochess` se trataría como variante o alias de `autobattler`, no
como una familia paralela.

`post-apocalyptic`, `lovecraft`, `swordsorcery`, `superhero`, `hip-hop` y
`k-pop` son mejores candidatos para `theme` o estilo temático. `dungeons &
dragons` debería reservarse para licencia/IP y `spaceship` para ambientación u
objeto, no para subgénero.

`deckbuilding`, `bossfight`, `shopkeeper`, `spellcaster`, `superpower` y
`swordplay` son mecánicas, roles o capacidades; `online co-op` es modo;
`sidescroller` y `non-linear` describen presentación o estructura;
`pixelart`, `1-bit`, `old school` y `1990s` describen estética o época;
`cross-play` y `colorblind friendly` son características del producto;
`minigame` y `rollercoaster` describen actividad o contenido; `roadtrip` y
`fanservice` son motivos narrativos; `e-sports` es contexto competitivo.

`pacman`, `tangledcrisis`, `tinyrogue` y `tmtamstudio` deben descartarse del
corpus de subgéneros por ser nombres propios, posibles títulos o entidad de
desarrollo, no categorías semánticas estables. `game dev`, `game jam`,
`game show` y `high score` ya están excluidas por decisión expresa del autor.

## Propuesta de taxonomía editorial final — 2026-09-10

El autor propone una lista final de 40 etiquetas únicas para la clasificación
visible: `Action`, `Adventure`, `Anime`, `Arcade`, `Beat'em up`, `Card Game`,
`Casual`, `Co-op`, `Comedy`, `Family Friendly`, `Fantasy`, `Fighting`, `Hack
and Slash`, `Horror`, `Indie`, `JRPG`, `MMO`, `Metroidvania`, `Multiplayer`,
`Open World`, `Platformer`, `Puzzle`, `RPG`, `Racing`, `Retro`, `Roguelike`,
`Sci-fi`, `Shooter`, `Side Scroller`, `Simulation`, `Singleplayer`,
`Souls-like`, `Sports`, `Stealth`, `Story Rich`, `Strategy`, `Survival`,
`Turn-Based`, `VR` y `Visual Novel`. La repetición de `Fantasy` se elimina.

La lista debe implementarse como una capa `CuratedLabel` versionada, sin
sobrescribir las tablas brutas de IGDB. Cada etiqueta tendrá una categoría
interna (`genre`, `theme`, `mode`, `format` o `feature`) aunque el usuario la
vea en un filtro unificado. Esto permite combinar, por ejemplo,
`Roguelike` + `Fantasy`, sin confundir una ambientación con una familia de
juego en los recomendadores.

Mapeo directo previsto: `Genre` aporta `Adventure`, `Arcade`, `Fighting`,
`Indie`, `Platformer`, `Puzzle`, `Racing`, `RPG`, `Shooter`, `Simulation`,
`Sports`, `Strategy` y `Visual Novel`; `Theme` aporta `Action`, `Comedy`,
`Fantasy`, `Horror`, `Open World`, `Sci-fi`, `Stealth` y `Survival`; y
`GameMode` aporta `Co-op`, `MMO`, `Multiplayer` y `Singleplayer`.

Las restantes etiquetas se obtienen mediante un mapa de keywords versionado:
`Anime`, `Casual`, `Family Friendly`, `JRPG`, `Metroidvania`, `Retro`,
`Roguelike`, `Side Scroller`, `Souls-like`, `Story Rich`, `Turn-Based` y `VR`.
`Card Game` exige keywords de cartas y no se deriva automáticamente de todo
`Card & Board Game`. La fuente IGDB combinada `Hack and slash/Beat 'em up` no
se dividirá artificialmente: cada una de las dos etiquetas necesitará
evidencia específica de keyword.

La asignación será unión de evidencias, con reglas explícitas de alias,
implicaciones controladas (`Turn-Based Strategy` aporta `Turn-Based` y
`Strategy`; `MMO` puede aportar también `Multiplayer`) y una etiqueta interna
de no clasificado si se exige cobertura total. Los vectores de recomendación
usarán nombres de espacio y pesos separados, no un único saco semántico.
