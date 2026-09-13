# Contrato de evidencia del panel de investigación — publicación v15

## Propósito

Este documento fija la frontera de lectura que alimentará el panel de investigación,
la API y las exportaciones de la Fase 7. El contrato consume una publicación ya
ejecutada; no vuelve a ejecutar la evaluación, no consulta PostgreSQL y no modifica
ningún snapshot científico.

La implementación canónica es
[`apps/api/evaluation/panel_contract.py`](../../apps/api/evaluation/panel_contract.py).
Su lector abre únicamente las tres rutas relativas allowlisted de la publicación,
calcula SHA-256 sobre sus bytes y valida la identidad antes de construir cualquier DTO.

## Fuentes canónicas y anclajes

| Fuente | Ruta relativa | Identidad esperada |
|---|---|---|
| Artefacto publicado | `apps/api/evaluation-400-test-2026-09-12-v15.artifact.json` | SHA-256 `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab` |
| Desglose de cohortes | `docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.json` | SHA-256 `7417c29ffa02de5e512bc8f2aeb4ba9a992a53d50f85af76dc441cf1a555aab0` |
| Protocolo vigente | `docs/methodology/protocol.json` | anclajes compatibles de corpus, snapshots, split, semillas y simulación |

La publicación expone como identidad de protocolo la versión `15` y el checksum
`d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a`, tal como declara
el artefacto v15. El `protocol.json` del repositorio puede ser un protocolo posterior
(actualmente v16); se comprueban sus anclajes compartidos, pero nunca se usa ese
protocolo posterior para recalcular o reinterpretar las métricas v15. Si cambian los
anclajes publicados, el lector falla cerrado.

Otros anclajes inmutables del run son:

- corpus `2026.09.2`;
- snapshot de corpus `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc`;
- snapshot de PopScore `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097`;
- split `test`, semillas `20260907` y `20260908`, y 400 usuarios de población;
- estado `succeeded`, 79 usuarios evaluables y el manifiesto de split declarado por el artefacto.

## Shape público

El lector devuelve un `PublishedRun` inmutable compuesto por estos DTOs:

### `RunSummary`

Contiene `run_id`, estado, fecha de publicación observable, versión de protocolo,
corpus, split, commit, feature set, número de semillas, hashes del artefacto, cohortes,
protocolo, snapshots y manifiesto. `code_commit=unavailable` se conserva como valor
explícito de procedencia: no se sustituye por el commit actual.

### `ComparisonRow`

Cada fila conserva el orden del backend: cohorte, algoritmo y `K` (`5`, `10`, `20`).
Incluye identificadores allowlisted, recuentos de población/evaluación, métricas de
acierto (`precision`, `recall`, `ndcg`, `map`), diversidad, novedad, recuento recomendado
y duración del worker. Cada métrica tiene `metric_id`, valor exacto o `null`, unidad,
dirección y explicación de ausencia.

Las métricas `catalogue_coverage`, `concentration_hhi` y `prediction_coverage` son
`run-level-only`: el JSON de cohortes las declara no desagregables porque el artefacto
no conserva las listas completas. Por tanto, cada fila de cohorte las marca como `null`
con esa explicación, sin aproximarlas ni copiarlas como si fueran datos de la cohorte.
La cohorte `no_history` conserva sus recuentos y su razón de no evaluabilidad; no se
convierte en un algoritmo con puntuación cero.

### `EvidenceDetails`

Agrupa procedencia, configuración allowlisted, limitaciones y las rutas relativas de
fuente. La configuración conserva semillas, split, K, headline, población, grid-size,
ejecución paralela y el feature set; el entorno es `null` porque v15 no lo registró
históricamente. No se exponen usuarios individuales, `per_user`, logs, dumps privados,
rutas absolutas, cookies, tokens, credenciales ni payloads internos.

### `ExportPayload`

`build_export_payload` solo acepta `csv`, `json` y `svg`. Cada salida incluye `run_id`,
filtros normalizados, nombre seguro, tipo MIME, checksum de la salida y filas públicas.
CSV y JSON contienen la misma tabla y procedencia; SVG contiene una representación
textual accesible cuyos valores proceden de las mismas filas. El cliente posterior no
debe ordenar, agregar, recalcular métricas ni serializar `per_user`.

## Allowlist de consulta

Los únicos filtros son `run_id`, `algorithm_id`, `cohort_id` y `metric_id`. Sus valores
se derivan de la publicación; se rechazan claves desconocidas, listas repetidas,
expresiones de consulta, valores ausentes y combinaciones no publicadas. `format` solo
se valida en la construcción de exportaciones y acepta `csv`, `json` o `svg`.

`filter_options` se genera en un orden estable a partir del artefacto y del snapshot.
No existe un filtro libre de ORM ni una ruta de archivo construida con entrada del
usuario.

## Regla de no recalcular

`panel_contract.py` no importa `evaluation.runner`, ningún ranker ni una función de
evaluación. La lectura es de solo lectura: JSON y bytes se abren para lectura, se
validan y se proyectan manualmente a DTOs congelados. El sentinel de publicación
rechaza checksum, versión, corpus, split, población, cohortes o hashes que se separen
de la identidad v15 antes de servir datos.

## Trazabilidad de requisitos

| Requisito | Cobertura de este contrato |
|---|---|
| EVAL-13 | RunSummary, filas de comparación, algoritmos, cohortes, K, métricas y configuración allowlisted para la futura API/panel. |
| EVAL-14 | Filas exactas, definiciones de métrica, orden estable y exportaciones CSV/JSON/SVG con checksum. |
| DOC-05 | Las salidas solo pueden derivarse de artefactos inmutables con SHA-256; no se vuelve a ejecutar la evaluación. |
| AGENT-05 | Procedencia, costes/tiempos disponibles, limitación de simulación, no desagregabilidad y amenaza de deriva documentadas. |

El resultado sigue siendo evidencia de simulación sobre arquetipos sintéticos y no
evidencia sobre usuarios reales. Los tiempos de entorno y CPU no disponibles para v15
se mantienen como limitación, no se rellenan con una medición posterior.

## Verificación reproducible

Desde la raíz del repositorio:

```text
docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_phase7_contract.py -q
docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_phase7_contract.py -k "allowlist or cohort or export or immutable" -q
git diff --check
```

Las pruebas cubren carga contra los archivos reales, mutación de bytes, rutas y filtros
hostiles, cohorte no evaluable, nulidad de métricas run-level, exportaciones saneadas y
ausencia de imports del runner. El comando de verificación observa el estado congelado;
no ejecuta ningún ranking ni modifica los artefactos publicados.

## Responsabilidad y revisión

El `gsd-executor` implementa el lector y produce checks deterministas; no es un revisor
académico independiente. El autor del TFG debe revisar la procedencia, las licencias,
la interpretación y la adecuación de las tablas antes de presentar la evidencia.
