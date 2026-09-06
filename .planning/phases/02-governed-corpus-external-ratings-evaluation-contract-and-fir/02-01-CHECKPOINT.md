# Checkpoint — Plan 02-01

Actualizado: 2026-09-07. Issue: #17. Ola: 1.

## Tarea 1 completada: ratificación D-01

El autor ratificó expresamente la propuesta completa de 39 plataformas de `02-RESEARCH.md`, Pattern 1:

> nada mejor dejemoslo como esta, estoy de acuerdo con la lista actual, en el filtro que aparezcan las consolas actuales primero

Esta respuesta sustituye su selección inicial de modificar la lista. No quedan altas ni bajas pendientes.

- PC: Windows, Mac, Linux.
- PlayStation: 1, 2, 3, 4, 5, PSP, Vita.
- Xbox: original, 360, One, Series X|S.
- Nintendo: NES, SNES, N64, GameCube, Wii, Wii U, Switch, Game Boy, GBC, GBA, DS, 3DS.
- Sega: Master System, Mega Drive/Genesis, Game Gear, Saturn, Dreamcast.
- Atari: 2600, 5200, 7800, Lynx, Jaguar.
- iOS, Android, navegador web.

Steam se resuelve como PC/Windows. La implementación debe reconciliar los slugs con la BD y avisar si no resuelven, como exige el plan; ratificar la lista no verifica los identificadores técnicos asumidos en RESEARCH.

Verificación: respuesta directa del autor en la sesión. No corresponde ejecutar tests para esta decisión documental.

## Siguiente acción

Ejecutar la tarea 2 de `02-01-PLAN.md` (modelos, migración aditiva, reglas y comando de gobernanza con fixtures PostgreSQL). La tarea 3 añade el informe y checksum. Al terminar cada una: verificar, commit atómico `Refs #17`, actualizar este checkpoint y avisar al orquestador.

La nueva preferencia de ordenar primero las consolas actuales se registra en 02-04; no modifica la pertenencia al corpus.

## Tarea 2 terminada: frontera gobernada

- Añadidos `GameWork.in_corpus`, `corpus_version`, `summary`, el índice compuesto de
  corpus y los modelos `CorpusRatingSnapshot` / `CorpusVersion` en la migración aditiva
  `0006_governed_corpus`.
- `catalogue/corpus.py` centraliza las 39 plataformas ratificadas, la validación D-03 y
  `governed_works(corpus_version)`.
- `govern_corpus` aplica las cinco cláusulas D-03 sin borrar obras ni excluir las que no
  tienen rating; usa lock advisory y transacción offline.

Verificación: `docker compose -f infra/compose.yaml run --rm api pytest
apps/api/catalogue/tests/test_govern_corpus.py -q` — **3 passed**.

## Tarea 3 terminada: evidencia DATA-03

- El comando emite checksum SHA-256, diccionario, informe de calidad con coberturas y
  motivos de exclusión, slugs no resueltos y manifiesto determinista de hasta 300 filas.
- Se añadieron `docs/verification/corpus-governance-freeze.md` y el artefacto JSON
  acompañante.
- Verificación de regresión: `docker compose -f infra/compose.yaml run --rm api pytest
  apps/api/catalogue -q` — **62 passed**.
- La opción `--version` reemplaza deliberadamente la opción genérica de Django para
  seleccionar la `corpus_version` del contrato; la versión de aplicación no es relevante
  para un comando de gobernanza.

## Cierre

Las tres tareas de 02-01 están completas y verificadas. El comando queda preparado para
ser consumido por snapshots de rating y por el resto de la fase.
