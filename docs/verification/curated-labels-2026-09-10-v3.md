# Curación de etiquetas editoriales v3 — 2026-09-10

## Decisión aplicada

Se amplía el vocabulario editorial con siete etiquetas derivadas directamente
de valores de `Theme`:

`Mystery`, `Educational`, `Kids`, `Romance`, `Historical`, `Party` y `Sandbox`.

La regla sigue sin cambiar: `Keyword` no genera etiquetas editoriales
directamente. Cuando una etiqueta procede de keywords, debe pasar por la capa
normalizada `Subgenre`.

## Resultado local

| Medida | Resultado |
|---|---:|
| Etiquetas curadas | 55 |
| Juegos con al menos una etiqueta | 297.011 |
| Evidencias obra-etiqueta | 1.168.660 |
| Evidencias con origen `keyword` | 0 |

| Theme | Etiqueta editorial | Juegos distintos |
|---|---|---:|
| Mystery | `Mystery` | 7.564 |
| Educational | `Educational` | 6.680 |
| Kids | `Kids` | 6.413 |
| Romance | `Romance` | 6.137 |
| Historical | `Historical` | 4.976 |
| Party | `Party` | 4.443 |
| Sandbox | `Sandbox` | 4.030 |

No se han añadido equivalencias automáticas inseguras como `Kids → Family
Friendly`, `Sandbox → Open World` o `Drama → Story Rich`.

## Propuesta pendiente para Subgenre

La revisión conservadora de los subgéneros aún no se ha aplicado. Los dos
candidatos principales son:

- `pixelart` (3.404 juegos) → nueva etiqueta `Pixel Art`.
- `superhero` (783 juegos) → nueva etiqueta `Superhero`.

No se recomienda convertir automáticamente `bossfight`, `cross-play`,
`e-sports`, `fanservice`, `minigame`, `non-linear`, `shopkeeper`, `spellcaster`,
`superpower` o `swordplay` en géneros: describen características, distribución,
estructura, roles o temas, pero no una categoría de juego suficientemente
estable.

## Reproducibilidad

- Mapa: `apps/api/catalogue/curated_labels.py`.
- Comando: `python manage.py curate_labels --version curated-labels-2026.09.10-v3`.
- Versión del mapa: `curated-labels-2026.09.10-v3`.
- Huella SHA-256: `c071a32a84cc16d76e8e4f2b717dfad3b0c750b46a54c8fb5c670333c8a42b8e`.
