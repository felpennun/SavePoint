# Curación editorial v5 — 2026-09-10

## Cambios aplicados

Se añaden `Pixel Art` y `Superhero` al vocabulario editorial. Ambas etiquetas
se obtienen únicamente desde `Subgenre`:

- `pixelart` → `Pixel Art`.
- `superhero` → `Superhero`.

`Superhero` se conserva como etiqueta propia y no se convierte en `Action` ni
en `Sci-fi`.

## Resultado local

| Medida | Resultado |
|---|---:|
| Etiquetas editoriales | 58 |
| Juegos con alguna etiqueta | 297.151 |
| Evidencias obra-etiqueta | 1.200.815 |
| Evidencias directas desde `Keyword` | 0 |
| `Pixel Art` | 5.109 |
| `Superhero` | 783 |

## Flujo de procedencia

Las facetas brutas no se sobrescriben. Las etiquetas derivadas conservan el
origen (`genre`, `theme`, `game_mode`, `player_perspective` o `subgenre`) en
`GameWorkCuratedLabel.source_kind`.

Las keywords siguen el flujo intermedio:

`Keyword` → `Subgenre` → `CuratedLabel`

## Reproducibilidad

- Versión editorial: `curated-labels-2026.09.10-v5`.
- Huella SHA-256: `3e6d97fd217278641c38040335892a6e0e84f9987eb1f82649c8e0935c7dad10`.
- Comando: `python manage.py curate_labels --version curated-labels-2026.09.10-v5`.
