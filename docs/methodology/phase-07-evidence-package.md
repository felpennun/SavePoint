# Paquete de evidencia de la Fase 7

## Propósito y estado

Este paquete congela una proyección thesis-ready del único run publicado de evaluación
v15. Su fuente de resultados es el artefacto `evaluation-400-test-2026-09-12-v15`; el
generador solo lee fuentes allowlisted, verifica sus SHA-256 y escribe salidas agregadas.
No ejecuta el runner, no consulta PostgreSQL y no cambia el artefacto científico.

El paquete se generó con `phase-07-evidence-v1`. El manifest es la referencia de identidad
de las salidas y su propio hash no se incluye dentro de sí mismo: la revisión de su
contenido queda cubierta por Git y por el commit de cierre de esta tarea.

## Identidad de la publicación

| Campo | Valor |
|---|---|
| Run | `evaluation-400-test-2026-09-12-v15` |
| Estado | `succeeded` |
| Protocolo productor | v15; SHA-256 `d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a` |
| Corpus | `2026.09.2` |
| Snapshot de corpus | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| Snapshot PopScore | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| Split | `test` |
| Split manifest | `c85d4ee270de8e590c9052d01dab30d7cf5314951622cc0b3801fdf027cbfd3d` |
| Commit declarado por el run | `unavailable` (se conserva, no se sustituye por el commit actual) |
| Artefacto fuente | SHA-256 `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab` |
| Cohortes fuente | SHA-256 `7417c29ffa02de5e512bc8f2aeb4ba9a992a53d50f85af76dc441cf1a555aab0` |

El fichero `docs/methodology/protocol.json` es actualmente un puntero v16. El generador
solo comprueba sus anclajes compartidos (corpus, snapshots, semillas, K y simulación); no
usa v16 para recalcular o reinterpretar ninguna cifra v15.

## Población y filas publicables

El artefacto conserva 400 usuarios en la población activa y 79 usuarios evaluables, con un
usuario omitido por no tener un positivo elegible. También registra literalmente
`requested_user_count=80`, que corresponde al subconjunto solicitado para la evaluación;
se publica como metadato y no se transforma en otra cifra. El total de split sigue siendo
400. Esta distinción evita ocultar una diferencia de nomenclatura del artefacto.

La tabla contiene 96 filas: dos cohortes (`active_history_10_to_20` y `no_history`), los
16 algoritmos del artefacto y K igual a 5, 10 y 20. Las métricas de precisión, recall,
nDCG, MAP, diversidad intra-lista, novedad y recuento recomendado proceden de
`summary_by_k` del JSON de cohortes. Cobertura de catálogo, HHI y cobertura de predicción
se dejan nulas por cohorte porque la fuente las declara solo a nivel del run; no se
copian ni se aproximan. La cohorte sin historial mantiene sus recuentos y razón de no
evaluabilidad, sin convertirse en una puntuación cero.

La figura SVG representa nDCG@10 de `active_history_10_to_20` con escala fija 0--1. Cada
barra conserva la etiqueta del algoritmo y el valor publicado; la tabla CSV/JSON sigue
siendo la fuente auditable y la figura incluye título y descripción accesibles.

## Tiempos y entorno

Los tiempos son los publicados por el run: 16 workers, dos workers máximos, ejecución por
algoritmo, suma de duraciones `6266.847883` segundos y tiempo de pared
`4297.870888` segundos, con cola serial de 5. También se conservan las marcas de inicio y
fin de suite y de cada algoritmo. No se inventa tiempo de CPU.

El entorno observado no fue registrado por v15. El paquete conserva únicamente las
declaraciones versionadas: Python `==3.13.*`, uv `==0.12.9`, Node `24.20.0`, pnpm
`11.26.0`, Next `16.3.4`, React `19.2.7`, TypeScript `6.0.3`, Playwright `1.62.1` y la
imagen PostgreSQL 18.6 fijada por digest en Compose. Los hashes de `uv.lock` y
`pnpm-lock.yaml` están en el manifest.

## Procedencia, licencias y coste

La procedencia primaria del panel es la publicación v15 y su snapshot de cohortes. La
decisión y los términos aplicables a IGDB/Twitch están documentados en
`docs/adr/ADR-006-igdb-source.md` y `docs/verification/igdb-catalogue-freeze.md`; el
contrato de proyección es `docs/verification/phase-07-evidence-contract.md` (no incluido en el repositorio público). La licencia
no se infiere desde el paquete: el autor debe revisar los términos antes de redistribuir
datos externos.

El coste recurrente declarado para esta demo académica es 0 EUR, sin tarjeta ni servicio
de pago nuevo. No se incluye el corpus bruto, un dump de base de datos, portadas replicadas
ni datos de proveedor en bloque. Las salidas son agregados saneados y deben publicarse solo
después de la revisión de licencias del autor.

## Limitaciones y amenazas a la validez

- La evaluación es simulación sobre arquetipos sintéticos; no demuestra comportamiento de
  usuarios reales.
- Es un único run de test. Las semillas de partición y población no sustituyen un estudio
  de sensibilidad entre múltiples seeds.
- Los 79 evaluables no permiten tratar la población nominal de 400 como 400 observaciones
  de ranking.
- No hay CPU, sistema operativo ni entorno completo históricos; solo se conservan tiempos
  de pared del artefacto.
- Los hashes prueban identidad de bytes, no veracidad, calidad ni adecuación legal.
- El agente que genera el paquete no es un revisor académico independiente; la selección,
  interpretación y presentación final corresponden al autor.

## Reproducción segura

Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/generate-phase-07-evidence.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1
git diff --check
```

El primer comando debe informar `rows=96` y `source hashes verified before write`. Repetirlo
con las mismas fuentes produce los mismos hashes de CSV, JSON y SVG. El proceso no invoca
`run_evaluation`, no lee el marker de consumo y no escribe sobre el artefacto v15.

## Archivos emitidos

Estos ficheros se generaron en `docs/verification/` y no incluido en el repositorio público; se conservan aquí sus huellas para poder comprobarlos en el repositorio de desarrollo.

| Archivo | SHA-256 |
|---|---|
| `docs/verification/phase-07-evidence-manifest.json` | `9f7a37a5fa33b93e92cf945d54771d4c755874a80116ea80d72d62549e6ad17d` |
| `docs/verification/phase-07-results.csv` | `084e975c993891fc8e16565c3c5f5deed67d5d65678c5ada918bf27e4afdc52b` |
| `docs/verification/phase-07-results.json` | `48949831e95aee76a42335b5c9ad59060a0db2d8311651f374eb1ef51b9be548` |
| `docs/verification/phase-07-comparison.svg` | `5749cd3a0d8311382cbb9d6fb83be5f1980b4284d57902bac5eca71e6ebda573` |

La proyección excluye filas individuales, secretos, cookies, credenciales, logs crudos,
dumps privados y rutas absolutas. El disclosure de IA y el reparto de responsabilidades
están en `ai-use-disclosure.md` y `phase-07-agent-contributions.md`.
