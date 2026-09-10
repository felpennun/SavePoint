# Curación de etiquetas editoriales v2 — 2026-09-10

## Decisión aplicada

La etiqueta editorial de género se construye a partir de `Genre`, `Theme`,
`GameMode`, `PlayerPerspective` y `Subgenre`. `Keyword` no se usa como fuente
directa de `CuratedLabel`.

Las keywords siguen formando parte de la capa bruta y pueden alimentar la
normalización previa que genera `Subgenre`. Por tanto, el flujo es:

`Keyword` → `Subgenre` → `CuratedLabel`

La versión de normalización de subgéneros es
`subgenres-2026.09.10-v2` y la versión del mapa editorial es
`curated-labels-2026.09.10-v2`.

## Subgéneros incorporados

| Subgénero canónico | Etiqueta editorial | Juegos distintos |
|---|---|---:|
| `anime` | `Anime` | 6.998 |
| `casual` | `Casual` | 5.907 |
| `family friendly` | `Family Friendly` | 908 |
| `metroidvania` | `Metroidvania` | 1.199 |
| `souls-like` | `Souls-like` | 387 |
| `story rich` | `Story Rich` | 1.882 |

Las variantes configuradas para estas claves se normalizan antes del mapeo:
`anime`, `casual game`, `soulslike`, `souls like` y las variantes editoriales
equivalentes definidas en `apps/api/catalogue/subgenres.py`.

## Resultado local

| Medida | Resultado |
|---|---:|
| Etiquetas curadas | 48 |
| Juegos con al menos una etiqueta | 295.737 |
| Evidencias obra-etiqueta | 1.128.417 |
| Evidencias con origen `keyword` | 0 |

## Reproducibilidad

- Normalización: `apps/api/catalogue/subgenres.py`.
- Mapeo editorial: `apps/api/catalogue/curated_labels.py` y
  `apps/api/catalogue/management/commands/curate_labels.py`.
- Comandos ejecutados: `curate_subgenres` y `curate_labels` con las versiones
  indicadas arriba.
- Huella SHA-256 del mapa editorial: `ec9a1d303fff43d2ba75286d35b588d1da6094cd519d86b9890cc28e092b7c87`.

Las facetas brutas de IGDB no se sobrescriben; las relaciones curadas conservan
el origen de cada asignación mediante `GameWorkCuratedLabel.source_kind`.
