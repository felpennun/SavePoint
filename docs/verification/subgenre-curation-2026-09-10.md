# Curación reproducible de subgéneros — 2026-09-10

## Alcance

Se creó una capa derivada `Subgenre` a partir de las keywords brutas de IGDB.
La tabla `Keyword` y sus asociaciones originales no se modifican: conservan
la evidencia recibida del proveedor. Solo las variantes incluidas en el mapa
editorial versionado pueden entrar en `Subgenre`.

La versión aplicada es `subgenres-2026.09.10-v1`, con una frecuencia mínima de
2 obras por subgénero canónico.

## Resultado

| Medida | Resultado |
|---|---:|
| Keywords brutas | 6.546 |
| Filas de keyword incluidas en reglas | 92 |
| Keywords explícitamente excluidas | 8 |
| Keywords no listadas, conservadas solo en bruto | 6.446 |
| Grupos canónicos antes del umbral | 46 |
| Subgéneros canónicos publicados | 41 |
| Grupos canónicos descartados por frecuencia | 5 |
| Obras con al menos un subgénero | 18.159 |
| Asociaciones obra-subgénero | 22.514 |

Las exclusiones explícitas son `gamedev`, `gamejam`, `gameshow` y `highscore`,
incluyendo sus variantes de escritura. Permanecen en la capa bruta, pero están
fuera del corpus curado de subgéneros.

Los cinco grupos que no alcanzaron dos obras distintas son `battle royale`,
`natureminds`, `tangledcrisis`, `tinyrogue` y `tmtamstudio`.

## Reglas destacadas

- `rogue-like`, `roguelite` y `roguelike` se consolidan en `roguelike`.
- `action roguelite` se consolida en `action roguelike`.
- `roguelike deckbuilder` se consolida en `roguelike deckbuilding`.
- `japanese rpg` se consolida en `jrpg`.
- `arpg`, `actionrpg` y `action-rpg` se consolidan en `action rpg`.
- Las variantes de separadores y puntuación siguen exactamente el mapa
  declarado en `apps/api/catalogue/subgenres.py`.

La huella SHA-256 del mapa aplicado es
`27fac028fa9e88ec9f969b03199478c32ad8cde25c4d29cf7ddd2e97483583da`.

## Política de uso

Los recomendadores deberán consumir `GameWork.subgenres` y no la relación
bruta `GameWork.keywords`. Cualquier ampliación o corrección del mapa debe
crear una nueva versión, regenerar la capa derivada y producir nueva evidencia.

## Reproducibilidad

La curación se ejecuta con:

```text
python manage.py curate_subgenres --version subgenres-2026.09.10-v1 --min-work-frequency 2
```

Implementación y mapa: `apps/api/catalogue/subgenres.py`.
Comando: `apps/api/catalogue/management/commands/curate_subgenres.py`.
Modelo y trazabilidad: `Subgenre` y `SubgenreKeyword` en
`apps/api/catalogue/models.py`.
