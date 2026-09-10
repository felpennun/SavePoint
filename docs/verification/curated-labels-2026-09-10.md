# Curación inicial de etiquetas editoriales — 2026-09-10

## Alcance

Se publicó la primera capa `CuratedLabel` para unificar la clasificación
editorial sin sobrescribir las facetas brutas de IGDB ni la capa derivada
`Subgenre`. La versión aplicada es `curated-labels-2026.09.10-v1`.

La lista contiene 48 etiquetas. Cada etiqueta conserva una categoría interna
(`genre`, `subgenre`, `theme`, `mode` o `feature`), aunque la interfaz pueda
mostrar un filtro único.

## Cambios aplicados

- `Battle Royale` se incorpora como etiqueta propia y también aporta
  `Multiplayer`.
- `deckbuilder`, `deck building`, `deck-building`, `deckbuilding`,
  `roguelike deckbuilder` y `roguelike deckbuilding` aportan `Deckbuilder`.
- Las variantes compuestas con roguelike aportan simultáneamente `Roguelike`
  y `Deckbuilder`.
- `japanese rpg` y `jrpg` aportan únicamente `JRPG`; no implican `RPG`.
- `Hack and slash/Beat 'em up` aporta únicamente `Hack and Slash`.
  `Beat'em up` no recibe asignaciones automáticas.
- Se incorporan también `MOBA`, `Music`, `Pinball`, `Point-and-Click`,
  `Trivia` y `Tactical` mediante sus valores de `Genre`.

## Resultado local

| Medida | Resultado |
|---|---:|
| Etiquetas curadas | 48 |
| Juegos con al menos una etiqueta | 295.704 |
| Evidencias obra-etiqueta | 1.138.127 |
| `Battle Royale` | 706 juegos distintos |
| `Deckbuilder` | 994 juegos distintos |
| `JRPG` | 1.034 juegos distintos |
| Juegos `JRPG` que también reciben `RPG` por esta regla | 0 |
| `Hack and Slash` | 4.357 juegos distintos |
| `Beat'em up` asignados automáticamente | 0 |

## Incorporación posterior de facetas IGDB

### `themes`

Mapeo directo a la lista editorial: `Action` → `Action`, `Comedy` → `Comedy`,
`Fantasy` → `Fantasy`, `Horror` → `Horror`, `Open world` → `Open World`,
`Science fiction` → `Sci-fi`, `Stealth` → `Stealth` y `Survival` → `Survival`.

`4X` puede aportar `Strategy`, pero debe declararse como regla explícita. El
resto de valores actuales (`Business`, `Drama`, `Educational`, `Erotic`,
`Historical`, `Kids`, `Mystery`, `Non-fiction`, `Party`, `Romance`, `Sandbox`,
`Thriller` y `Warfare`) no tiene una equivalencia segura en la lista actual.
No se deben convertir automáticamente en `Story Rich`, `Open World`,
`Multiplayer` u otra etiqueta cercana.

### `player_perspectives`

Solo `Virtual Reality` → `VR` es una equivalencia segura. `First person`,
`Third person`, `Bird view / Isometric`, `Side view`, `Text` y `Auditory` son
perspectivas o formatos sin etiqueta equivalente en la lista actual. En
particular, `Side view` no implica `Side Scroller`.

### `game_modes`

`Battle Royale` → `Battle Royale` + `Multiplayer`; `Co-operative` → `Co-op` +
`Multiplayer`; `Massively Multiplayer Online (MMO)` → `MMO` + `Multiplayer`;
`Multiplayer` → `Multiplayer`; y `Single player` → `Singleplayer`.
`Split screen` no se convierte automáticamente en `Co-op`, porque también
puede representar modos competitivos.

## Reproducibilidad

Implementación y reglas: `apps/api/catalogue/curated_labels.py`.
Comando: `python manage.py curate_labels`.
Modelo y procedencia: `CuratedLabel` y `GameWorkCuratedLabel`.
Huella del mapa: `3dfa4e27747c4be703b21545aade1d6ac094ebdea865f34143e9856a0d02e0f3`.

Revisión posterior: se elimina `Beat'em up` del vocabulario curado. La keyword
original se conserva y las evidencias de `Hack and slash/Beat 'em up` siguen
asignándose únicamente a `Hack and Slash`.

La versión aplicada también incorpora `Split screen` → `Split Screen` y
`Virtual Reality` → `VR`. La primera cubre 4.608 obras y la segunda 4.032
obras distintas al combinar la evidencia de perspectiva y keywords. `4X`
aporta `Strategy` para 655 obras.

La revisión posterior añade `4X (explore, expand, exploit, and exterminate)`
→ `Strategy`. `Split screen` se mantiene sin mapeo automático: aparece en
4.608 obras, coincide con `Co-operative` en 1.752, con `Multiplayer` en 3.495
y con `Single player` en 4.328. Hay 1.077 obras con `Split screen` y
`Single player` sin `Multiplayer`, por lo que no es una equivalencia segura.
Si se quiere exponer en la lista final, se recomienda una etiqueta propia
`Split Screen`.
