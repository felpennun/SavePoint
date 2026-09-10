# Cobertura de facetas y etiquetas — 2026-09-10

## Resultado

La cobertura actual no tiene valores huérfanos en las tablas de facetas: todos
los valores almacenados tienen al menos un juego asociado. `Card & Board Game`
ya está mapeado a `Card Game`.

| Faceta | Valores | Juegos con algún valor | Juegos sin valor |
|---|---:|---:|---:|
| `Genre` | 23 | 282.454 | 48.546 |
| `Theme` | 22 | 179.744 | 151.256 |
| `GameMode` | 6 | 234.761 | 96.239 |
| `PlayerPerspective` | 7 | 128.185 | 202.815 |
| `Keyword` | 6.546 | 131.829 | 199.171 |
| `Subgenre` derivado | 65 | 44.965 | 286.035 |

La ausencia de una faceta en un juego no implica por sí sola un fallo de
importación: IGDB no tiene por qué proporcionar todos los campos para cada
obra. La comprobación de integridad sí confirma que no hay filas de faceta sin
relación con juegos.

## Valores todavía sin mapeo

### Theme

`Erotic` (9.957), `Warfare` (3.940), `Drama` (4.191), `Thriller` (2.144),
`Business` (2.506) y `Non-fiction` (2.306).

No son equivalencias olvidadas como `Card & Board Game`; requieren decidir si
se incorporan como tags propios o si permanecen como facetas brutas.

### PlayerPerspective

Solo `Virtual Reality` → `VR` se mapea. `Text`, `Third person`, `Auditory`,
`Side view`, `First person` y `Bird view / Isometric` permanecen sin mapear por
decisión: describen perspectiva o formato, no un tag editorial equivalente.

### Subgenre

No se asignan todavía `colorblind friendly` (23), `k-pop` (11), `cross-play`
(23), `bossfight` (1.904), `shopkeeper` (89), `e-sports` (114), `fanservice`
(127), `superpower` (198), `swordplay` (103), `roadtrip` (23), `non-linear`
(230), `minigame` (1.618), `hip-hop` (52) y `spellcaster` (176). Son
características, formatos, temas o roles sin una equivalencia editorial
aprobada.

## Etiquetas finales

Las 58 etiquetas editoriales tienen al menos un juego asociado. El número total
de juegos con alguna etiqueta es 297.562; las etiquetas se solapan entre sí.
Las evidencias mantienen su origen y no existe ninguna evidencia editorial
directa desde `Keyword`.
