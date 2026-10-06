# API de investigación protegida — Fase 7

## Propósito y autoridad

La API publica únicamente la evaluación v15 ya congelada. Django/DRF es la autoridad
de sesión, permisos, allowlists y serialización; el navegador no concede acceso ni
recalcula métricas. Las vistas llaman a `evaluation.panel_contract` y no importan el
runner, consultan PostgreSQL para reconstruir resultados ni aceptan operaciones de
mutación.

La capability `can_view_research` exige el permiso Django
`evaluation.view_research_panel`. `can_manage_platform` es una capability distinta,
basada en `accounts.manage_platform` (con compatibilidad explícita para
`auth.change_user`). `Platform Admin` no convierte a una cuenta en `Research Viewer`.

## Rutas y respuestas

Todas las rutas son privadas, de solo lectura, `Cache-Control: private, no-store` y
throttle `research` (`60/min` por IP). Una sesión ausente recibe la respuesta de
autenticación DRF (`401`, o `403` según el cliente), sin precargar datos. Una cuenta
autenticada sin permiso recibe `404 {"detail":"Not found."}`, igual que un recurso
inexistente, sin mencionar el panel.

| Método y ruta | Consulta allowlisted | Respuesta |
|---|---|---|
| `GET /api/evaluation/runs/` | ninguna | `runs`, `algorithms`, `cohorts`, `metrics`, `formats` |
| `GET /api/evaluation/comparison/` | `run`, `algorithm`, `cohort`, `metric` | run, filtros, opciones, filas, definiciones, timings, procedencia, limitaciones y descargas |
| `GET /api/evaluation/artifacts/` | `run` | metadatos saneados y SHA-256 de artefacto, cohortes y protocolo |
| `GET /api/evaluation/exports/` | `run`, `algorithm`, `cohort`, `metric`, `format` | descarga `csv`, `json` o `svg` desde el snapshot |

Los valores de consulta se comparan con las opciones publicadas. Se rechazan claves
desconocidas, parámetros repetidos, valores vacíos, expresiones (`__`, `=`, `&`, `|`,
`;`, comillas), rutas, formatos no publicados, runs inexistentes y combinaciones fuera
del snapshot, con `400` genérico. No existe `/api/evaluation/rerun/`; los métodos
`POST`, `PUT`, `PATCH` y `DELETE` no están implementados y una sesión real además
debe superar CSRF antes de llegar a un método no permitido.

## DTOs y saneamiento

Los serializers son funciones manuales con allowlist. `RunSummary` conserva la
identidad v15, protocolo `15`, corpus `2026.09.2`, split `test`, commit y hashes.
Cada fila conserva el orden del backend y contiene algoritmo, cohorte, `K`, recuentos,
métricas exactas o `null`, razón de ausencia y timing publicado. Las métricas
run-level no se atribuyen artificialmente a cohortes.

`artifacts` solo devuelve identificador, nombre de fichero fijo, formato JSON, MIME,
estado publicado y SHA-256. Las exportaciones usan el nombre fijo
`evaluation-400-test-2026-09-12-v15.{csv,json,svg}`, MIME explícito y cabecera
`X-Content-SHA256`. No se sirven `per_user`, logs, dumps privados, rutas absolutas,
cookies, tokens, contraseñas ni credenciales.

El cliente debe presentar los valores recibidos. No ordena filas, redondea para
comparar, agrega cohortes, cruza runs, calcula medias o genera archivos.

## Procedencia y limitaciones

La fuente es la publicación v15 validada por
[`phase-07-evidence-contract.md`](phase-07-evidence-contract.md): artefacto de
resultados, snapshot de cohortes y puntero metodológico con anclajes compatibles.
La deriva del puntero `protocol.json` posterior no se oculta: la API conserva la
identidad declarada por v15 y no recalcula. La evidencia sigue siendo una simulación
con usuarios sintéticos; los tiempos de CPU y el entorno histórico no disponibles
permanecen como `null`/limitación.

## Verificación reproducible

```text
docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check
docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_phase7_api.py -q
docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests/test_phase7_contract.py -q
git diff --check
```

La suite dedicada cubre Research Viewer, Platform Admin sin Research Viewer, cuenta
normal, sesión ausente, capability combinada, IDOR/run no publicado, filtros hostiles,
XSS en valores reflejados, CSRF y métodos no permitidos, Content-Disposition, ausencia
de secretos y throttle. `MeView` mantiene una proyección explícita de identidad y
capabilities server-side.

## Trazabilidad

| Requisito / decisión | Evidencia |
|---|---|
| EVAL-13, EVAL-14 | Rutas de runs/comparison/artifacts/exports y filas/exportaciones del snapshot |
| SEC-01, SEC-03, SEC-04 | Sesión DRF, 404 neutro, separación de capabilities y protección CSRF |
| SEC-05, SEC-06 | Allowlists de query/DTO, nombres/MIME fijos y throttle `research` |
| QUAL-01 | Contrato HTTP reproducible, datos backend-first y no recalculación cliente |
| D-07-02, D-07-03, D-07-04, D-07-05, D-07-14, D-07-16 | Permiso Django, lectura v15, separación administrativa, filtros, descargas y hashes |

La revisión académica de interpretación, procedencia y adecuación de las tablas
corresponde al autor del TFG; el executor aporta la implementación y los checks
deterministas, no una aprobación independiente.
