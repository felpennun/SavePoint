# Auditoría de importación IGDB y señales — 2026-09-09

## Resultado

La importación principal se reanudó desde el cursor `10845` y terminó con
`312759` obras IGDB principales. La segunda pasada sincronizó `17957` obras
relacionadas y `17957` relaciones DLC/expansión. Ambas operaciones fueron
aditivas: el importador conserva valores ya observados cuando IGDB omite un
campo, añade valores nuevos no presentes y no elimina alias, lanzamientos,
relaciones ni portadas existentes.

## Corpus gobernado

- Versión activa: `2026.09.2`.
- Corte temporal: `2026-09-09`.
- Obras visibles en catálogo: `190479`.
- Obras candidatas a algoritmos: `30623`, con
  `total_rating_count >= 1 OR rating IS NOT NULL`.
- Obras futuras, sin fecha o DLC en catálogo: `0`.

La evidencia detallada está en
[`corpus-governance-2026.09.2.json`](corpus-governance-2026.09.2.json).

## Cobertura de señales

Las cuatro primitivas PopScore (`Visits`, `Want to Play`, `Playing` y `Played`)
se capturaron y normalizaron por separado con `log1p` y percentil de rango
medio. El compuesto `igdb-engagement-mean-v1` se materializó en la nueva tabla
`CorpusPopularityScore` únicamente cuando las cuatro primitivas estaban
presentes: `9929` obras. El valor conserva la versión de fórmula, la fecha de
cálculo y el hash de las primitivas.

| Señal | Obras con observación |
|---|---:|
| Visits | 46419 |
| Want to Play | 60713 |
| Playing | 19426 |
| Played | 61477 |

También se almacenaron `rating`, `rating_count`, `total_rating` y
`total_rating_count`, además de desarrolladores y franquicias cuando IGDB los
proporciona. Los campos opcionales no se rellenan artificialmente: en el
catálogo gobernado hay `101018` obras con desarrollador, `11555` con
franquicia y `27036` con rating de usuario.

Evidencias: [`corpus-popularity-2026.09.2.json`](corpus-popularity-2026.09.2.json),
[`corpus-ratings-2026.09.2.json`](corpus-ratings-2026.09.2.json) y
[`popscore-materialization-2026.09.2.json`](popscore-materialization-2026.09.2.json).

## Integridad

No hay obras con slug o título vacío. Todas las obras del corpus gobernado
tienen fecha, al menos un lanzamiento fechado y no son DLC. Los campos
opcionales con ausencias reflejan cobertura real de IGDB y quedan cuantificados
en la evidencia; no se convierten en ceros ni en texto inventado.
