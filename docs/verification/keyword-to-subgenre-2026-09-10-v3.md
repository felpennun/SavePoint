# Curación de Keyword a Subgenre v3 — 2026-09-10

## Cambios aplicados

Se normalizaron estas variantes dentro de subgéneros existentes:

- `pixel graphics` → `pixelart`.
- `side-scrolling` → `sidescroller`.
- `minigames` → `minigame`.
- `shmup` → `shoot'em up`.

También se añadieron los candidatos prioritarios como subgéneros normalizados:

`action adventure`, `hidden object`, `psychological horror`, `turn-based`,
`music and rhythm`, `bullet hell`, `tower defense`, `cyberpunk`,
`survival horror`, `brawler`, `turn-based rpg`, `2d platformer`, `dark fantasy`,
`dating simulation`, `city builder`, `precision platforming` y
`puzzle platformer`.

## Regla especial de Cyberpunk

`cyberpunk` se asigna a la etiqueta editorial de género independiente
`Cyberpunk`. No se transforma en `Sci-fi` ni genera ambas etiquetas.

## Resultado local

| Medida | Resultado |
|---|---:|
| Subgéneros con al menos dos juegos | 66 |
| Etiquetas editoriales | 56 |
| Juegos con al menos una etiqueta editorial | 297.118 |
| Evidencias editoriales con origen `keyword` | 0 |
| Juegos con `Cyberpunk` | 1.123 |

Frecuencias de los nuevos subgéneros principales:

| Subgenre | Juegos |
|---|---:|
| `action adventure` | 2.314 |
| `hidden object` | 2.121 |
| `psychological horror` | 1.939 |
| `turn-based` | 1.488 |
| `music and rhythm` | 1.406 |
| `bullet hell` | 1.304 |
| `tower defense` | 1.221 |
| `cyberpunk` | 1.123 |
| `survival horror` | 959 |
| `brawler` | 759 |
| `turn-based rpg` | 717 |
| `2d platformer` | 683 |
| `dark fantasy` | 825 |
| `dating simulation` | 810 |
| `city builder` | 642 |
| `precision platforming` | 614 |
| `puzzle platformer` | 596 |

Tras la normalización, `pixelart` queda en 5.109 juegos, `sidescroller` en
1.539 y `minigame` en 1.618.

## Reproducibilidad

- Normalización: `apps/api/catalogue/subgenres.py`.
- Mapeo editorial: `apps/api/catalogue/management/commands/curate_labels.py`.
- Versiones: `subgenres-2026.09.10-v3` y `curated-labels-2026.09.10-v4`.
- Huellas SHA-256: `d985c77125ea5ff8710eeeb78afb0872442d3625c23d145ed8acdc66c7ef2b34` y
  `6ea6b63d0007644e16902783dba1ee79ee96ec459a7b674d2f8b600147677cbb`.
