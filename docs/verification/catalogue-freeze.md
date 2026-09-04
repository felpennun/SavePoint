# Congelación del corpus de catálogo y allowlist de assets

**Estado:** APPROVED
**Fecha de verificación:** 2026-09-04
**Decisión humana:** Felipe autorizó explícitamente el corpus y la allowlist de assets con el mensaje `corpus aprobado`, tras revisar la cobertura por era/plataforma/género y la tabla completa de licencias por asset presentada en el checkpoint.
**Trabajo del agente:** adquisición reproducible desde Wikidata Query Service (candidato, sin importar), revisión de metadata de licencia por archivo en Wikimedia Commons, validación estructural automática (recuento, unicidad de QID, cobertura mínima, checksums enlazados) y presentación del resultado al autor para decisión legal final.
**Límite de la aprobación:** cualquier ampliación del corpus, sustitución de query de adquisición o cambio en un asset ya congelado exige repetir este gate humano. La importación a PostgreSQL (Plan 01-06) sólo puede ejecutarse con este documento en estado APPROVED.

Este registro desarrolla el contrato de adquisición de [01-COVERAGE.md](../../.planning/phases/01-three-day-public-demo-slice/01-COVERAGE.md) y la investigación de [01-RESEARCH.md](../../.planning/phases/01-three-day-public-demo-slice/01-RESEARCH.md).

## Snapshot congelado

| Campo | Valor |
|---|---|
| Fuente | Wikidata Query Service (`https://query.wikidata.org/sparql`) |
| Licencia de datos | CC0 1.0 (https://www.wikidata.org/wiki/Wikidata:Licensing) |
| Fecha de recuperación / corte (UTC) | 2026-09-04T16:24:18Z |
| Recuento de juegos | 150 |
| Snapshot | `data/raw/wikidata-games.json` |
| SHA-256 del snapshot | `a2b5d8d1f4388b21a03a5c3c983840e38db2c5e176613913985a5e38f7408159` |
| Manifest de catálogo | `data/manifests/catalogue.json` (checksum enlazado al snapshot anterior) |
| Manifest de assets | `data/manifests/assets.json` (checksum enlazado al mismo snapshot) |
| `promotion` (manifest) | `blocked-until-human-freeze` → pasa a habilitado sólo tras este documento |

## Criterios D-05/D-06 (cobertura)

El corpus representa múltiples eras, géneros, PC, consolas actuales e históricas, tal como exige D-05/D-06; ninguna de las cifras siguientes es forzada artificialmente por el esquema o el importador, que no imponen ese límite.

| Era | Juegos | | Familia de plataforma | Juegos |
|---|---:|---|---|---:|
| pre-1990 | 46 | | PC | 93 |
| 1990s | 27 | | Arcade/móvil/otro | 40 |
| 2000s | 39 | | Nintendo | 42 |
| 2010s | 25 | | PlayStation | 21 |
| 2020s | 12 | | Xbox | 24 |
| unknown | 1 | | Sega | 13 |
| | | | Otro | 10 |

Géneros distintos: 77. Títulos con alias/etiqueta en español: 89/150.

## Decisión por asset (D-07)

19 candidatos de carátula revisados individualmente contra Wikimedia Commons; cero quedan sin resolución — cada uno tiene una decisión explícita (`candidate` o `placeholder`) en `data/manifests/assets.json`.

**APPROVED — 17 candidatos con autor, licencia, URL de licencia y URL de fuente completos:**

| # | Archivo | Licencia | Autor |
|---|---|---|---|
| 1 | 0 A.D. — Seleukiden-Stadt Ken Wood 23.png | CC BY-SA 4.0 | PantheraLeo1359531/Wildfire Games |
| 2 | 3 cossacks european wars.JPG | GFDL | GSC Game World |
| 3 | Assassin's Creed II by Reindertot.jpg | CC BY 2.0 | Reindertot |
| 4 | Boulder Dash Cover Art 1984-1988.jpg | CC BY-SA 4.0 | Ernst Krogtoft / BBG Entertainment GmbH |
| 5 | Dig Dug (Taizo Hori) and Pooka characters.png | CC BY 3.0 | Unknown author |
| 6 | E3 2011 - Forza Motorsport 4 (Xbox).jpg | CC BY 2.0 | The Conmunity — Pop Culture Geek |
| 7 | Ksame.png | GPL | RaviC (en.wikipedia) |
| 8 | Musée Mécanique 205.JPG | CC BY-SA 3.0 | User:Piotrus |
| 9 | Nintendo 64 with Paper Mario.jpg | CC BY-SA 2.0 | Bryan Ochala |
| 10 | Pac-Man gameplay (1x pixel-perfect recreation).png | CC BY 3.0 | Bandai Namco Entertainment America |
| 11 | Quake cover.png | CC BY 3.0 | Xbox México |
| 12 | Signed Pong Cabinet.jpg | CC BY-SA 3.0 | Chris Rand |
| 13 | Space Invaders - Midway's.JPG | CC BY-SA 3.0 | Jordiferrer |
| 14 | Stalkershot 2.jpg | GFDL | GSC Game World |
| 15 | VVVVVV - The Tomb of Mad Carew.png | CC BY-SA 3.0 | Terry Cavanagh |
| 16 | Widelands-svn3311.jpg | GPL | Widelands Development Team |
| 17 | Xblast.jpg | GPL | Cunni |

**PLACEHOLDER — 2 candidatos con metadata incompleta, resueltos automáticamente al placeholder propio (nunca aprobados sin resolución):**

| # | Archivo | Motivo |
|---|---|---|
| 18 | Netrek-client-cow.png | Licencia "Public domain" declarada pero sin URL de licencia verificable |
| 19 | Warzone 2100 - base.jpg | Sin autor atribuido |

Cualquier juego del corpus sin candidato de carátula usa igualmente el placeholder propio por defecto; no hay excepciones fuera de esta tabla.

## Verificación

- `python scripts/acquire_catalogue.py --validate-only` — PASS: candidato válido, 150 juegos, aún sin promover.
- Checksums de `catalogue.json`/`assets.json` enlazados al SHA-256 del snapshot — coinciden.
- `python -m json.tool` sobre los tres archivos — JSON válido. (El `<verify>` original del plan usa `docker compose run --rm api python -m json.tool`; el servicio `api` no monta `data/` como volumen ni lo copia en `apps/api/Dockerfile`, así que ese comando exacto no puede ejecutarse contra la infraestructura actual — desviación documentada en `01-05-SUMMARY.md`.)
- Cero assets sin resolución: 19/19 tienen `decision` explícita en `assets.json`.

## Resultado

**APPROVED.** El corpus y la allowlist de assets quedan congelados en el snapshot y checksums anteriores. Plan 01-06 (import a PostgreSQL) puede proceder únicamente contra este snapshot exacto; cualquier cambio de origen, query o asset requiere una nueva revisión humana y un nuevo registro en este documento.
