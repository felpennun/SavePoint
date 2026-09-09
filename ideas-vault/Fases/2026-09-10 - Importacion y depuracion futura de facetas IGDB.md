---
tags: [fase, datos, igdb, pendiente]
---

# Importación y depuración futura de facetas IGDB

## Estado — 2026-09-10

Se verificó la importación aditiva de `themes`, `game_modes`,
`player_perspectives` y `keywords` en la base de datos local. Las cantidades de
valores y obras asociadas coinciden con la evidencia de importación, sin
nombres vacíos ni IDs IGDB duplicados.

## Decisión aplazada

La depuración y el análisis de calidad no se ejecutan todavía. Primero se
terminará la interfaz web. Después se estudiarán cobertura, valores ausentes,
frecuencia, sinónimos, ruido y normalización; cualquier transformación deberá
ser versionada y conservar el valor bruto. Solo tras esa revisión se decidirá
si las facetas entran en una nueva versión de los vectores y de los
recomendadores.

## Fuente canónica

[Verificación de la importación](../../docs/verification/igdb-facets-import-2026-09-10.md)

Relacionada: [[Diccionario de datos e informe de calidad]]
