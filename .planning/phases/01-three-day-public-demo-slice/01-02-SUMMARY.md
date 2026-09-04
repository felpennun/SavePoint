---
phase: 01-three-day-public-demo-slice
plan: 02
subsystem: infrastructure-testing
tags: [docker-compose, postgresql, pytest, vitest, playwright, security-fixtures, accessibility]
requires:
  - phase: 01-01
    provides: [approved exact dependencies, immutable OCI references, audited lockfiles]
provides:
  - Healthy PostgreSQL 18.6 integration-test path with a real non-empty sentinel
  - Non-empty Vitest runner and discoverable Chromium Playwright runner
  - Synthetic A/B, XSS, hostile URL, and tampered-hash fixtures
  - Versioned keyboard, reflow, screen-reader, privacy, and hostile-input manual protocol
affects: [all-phase-01-plans, backend, frontend, e2e, security, accessibility, thesis-evidence]
actuals:
  tokens: 17112
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [immutable OCI images, non-root application containers, PostgreSQL-only integration, fail-on-empty test runners, synthetic hostile fixtures]
key-files:
  created: [infra/compose.yaml, apps/api/Dockerfile, apps/api/tests/test_postgres_sentinel.py, apps/web/vitest.config.ts, e2e/sentinel.spec.ts, e2e/fixtures/hostile.json, docs/verification/phase-01-manual.md]
  modified: [apps/web/Dockerfile, pnpm-lock.yaml]
key-decisions:
  - "La prueba de integración abre una conexión psycopg real a PostgreSQL 18.6 mediante parámetros separados y nunca registra el DSN ni las credenciales."
  - "Los sentinels fallan si no se descubre ninguna prueba y los fixtures hostiles usan exclusivamente datos e identificadores sintéticos."
  - "Los contenedores de aplicación ejecutan como usuarios no privilegiados y el contexto Docker excluye configuración local y artefactos sensibles."
patterns-established:
  - "Wave 0 runner gate: cada framework debe ejecutar o descubrir al menos una aserción real antes del scaffold funcional."
  - "Security fixture boundary: casos A/B, XSS, URL y checksum son sintéticos, versionados y no contienen secretos reales."
requirements-completed: [OPS-02, QUAL-03, SEC-02]
coverage:
  - id: D1
    description: "Compose arranca PostgreSQL 18.6 saludable y pytest verifica el motor mediante una conexión real, sin SQLite."
    requirement: OPS-02
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_postgres_sentinel.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Vitest ejecuta una prueba no vacía y Playwright descubre un sentinel Chromium sin requerir servidor."
    requirement: QUAL-03
    verification:
      - kind: unit
        ref: "corepack pnpm --dir apps/web test --run"
        status: pass
      - kind: e2e
        ref: "corepack pnpm exec playwright test e2e/sentinel.spec.ts --list"
        status: pass
    human_judgment: false
  - id: D3
    description: "Fixtures hostiles completos y protocolo manual 320 px/400 %, teclado, lector de pantalla y privacidad quedan versionados sin secretos."
    requirement: SEC-02
    verification:
      - kind: other
        ref: "JSON structural check plus scripts/check-dependencies.ps1 and static checklist inspection"
        status: pass
    human_judgment: false
duration: 12min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 02: Wave 0 Infrastructure and Test Runners Summary

**PostgreSQL 18.6 real, contenedores no privilegiados y sentinels no vacíos para pytest, Vitest y Playwright, acompañados por fixtures de seguridad y un protocolo manual reproducible.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-04T13:41:00Z
- **Completed:** 2026-09-04T13:53:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- Compose construye imágenes fijadas por digest, espera a PostgreSQL y ejecuta una prueba psycopg que confirma PostgreSQL 18.6.
- Vitest ejecuta una aserción real y Playwright enumera un test Chromium sin ocultar una suite vacía.
- Los casos A/B, XSS, URL maliciosa y checksum incorrecto, junto con el protocolo manual bilingüe de accesibilidad y privacidad, quedan preparados para los planes funcionales.

## Task Commits

1. **Task 1: Arrancar PostgreSQL y ejecutar sentinel backend** — `4aaa889`
2. **Task 2: Ejecutar Vitest y descubrir Playwright** — `22d2854`

## Files Created/Modified

- `infra/compose.yaml` — topología local con PostgreSQL saludable y servicios API/web no privilegiados.
- `apps/api/Dockerfile` — entorno Python 3.13.7 reproducible desde `uv.lock`.
- `apps/web/Dockerfile` — entorno Node 24.13.0 reproducible desde `pnpm-lock.yaml`.
- `apps/api/pytest.ini`, `apps/api/conftest.py` y `apps/api/tests/test_postgres_sentinel.py` — runner pre-scaffold y conexión PostgreSQL sin imprimir secretos.
- `apps/web/package.json`, `apps/web/vitest.config.ts` y `apps/web/tests/sentinel.test.ts` — workspace y sentinel Vitest fail-on-empty.
- `playwright.config.ts` y `e2e/sentinel.spec.ts` — descubrimiento Chromium independiente de servidor.
- `e2e/fixtures/hostile.json` — identidades A/B y entradas hostiles exclusivamente sintéticas.
- `docs/verification/phase-01-manual.md` — protocolo repetible para teclado, 320 px, zoom 400 %, lector de pantalla, privacidad y seguridad.
- `.gitignore` y `.dockerignore` — exclusión de secretos locales, dependencias, cachés y resultados generados.

## Decisions Made

- PostgreSQL es la única ruta de integración; el sentinel falla si no observa la versión 18.6 del servidor real.
- Las credenciales locales de Compose son valores sintéticos de test, no secretos de infraestructura; se pasan por campos separados para impedir que un fallo imprima un DSN completo.
- Los runners no usan `passWithNoTests`; el éxito exige una prueba real o un test Playwright enumerado.
- El protocolo manual registra commit, entorno y revisor sin copiar cookies, cabeceras, contraseñas ni variables de entorno.

## Verification Results

- `docker compose -f infra/compose.yaml config --quiet` — PASS.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_postgres_sentinel.py -q` — PASS, 1 test, PostgreSQL 18.6.
- `corepack pnpm --dir apps/web test --run` — PASS, 1 file/1 test.
- `corepack pnpm exec playwright test e2e/sentinel.spec.ts --list` — PASS, 1 Chromium test discovered.
- `docker compose -f infra/compose.yaml build web` — PASS con lock congelado.
- Contenedores API/web — PASS como UID 10001 y 1000 respectivamente.
- `scripts/check-dependencies.ps1` — PASS; allowlist y referencias OCI inmutables conservadas.
- Fixture JSON y checklist — PASS; identidades A/B distintas, tres payloads XSS, cinco URL hostiles y hash SHA-256 deliberadamente incorrecto.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Excluidos secretos y artefactos del repositorio y del contexto Docker**
- **Found during:** Tasks 1 y 2
- **Issue:** El repositorio greenfield no tenía `.gitignore` ni `.dockerignore`; un futuro `.env` podía alcanzar Git o el contexto de build.
- **Fix:** Se añadieron exclusiones explícitas para configuración local, dependencias, cachés y resultados.
- **Files modified:** `.gitignore`, `.dockerignore`
- **Verification:** los builds Docker y `git status --short` no incorporan los directorios generados.
- **Committed in:** `4aaa889`, `22d2854`

**2. [Rule 3 - Blocking] Añadido el manifiesto mínimo del workspace web**
- **Found during:** Task 2
- **Issue:** `pnpm --dir apps/web test --run` no puede ejecutar un script sin un `package.json` en ese workspace.
- **Fix:** Se creó un manifiesto sin dependencias nuevas, con script Vitest y modo ESM; el lock aprobado se regeneró sin cambiar versiones.
- **Files modified:** `apps/web/package.json`, `pnpm-lock.yaml`
- **Verification:** instalación congelada y Vitest pasan; el checker de dependencias sigue verde.
- **Committed in:** `22d2854`

**3. [Rule 1 - Bug] Corregida la copia de una carpeta node_modules opcional inexistente**
- **Found during:** Task 2, verificación de imagen web
- **Issue:** El Dockerfile intentaba copiar `apps/web/node_modules`, que no existe cuando el workspace no declara paquetes propios.
- **Fix:** El runtime conserva únicamente el `node_modules` raíz, desde el que pnpm resuelve los binarios aprobados.
- **Files modified:** `apps/web/Dockerfile`
- **Verification:** `docker compose -f infra/compose.yaml build web` y el sentinel dentro del contenedor pasan.
- **Committed in:** `22d2854`

**Total deviations:** 3 auto-fixed (1 seguridad crítica, 1 bloqueo, 1 bug). **Impact:** no se añadió ninguna dependencia ni se cambió la arquitectura; se cerraron riesgos necesarios para que la infraestructura sea ejecutable y segura.

## Issues Encountered

- Docker Desktop estaba detenido al iniciar. Se arrancó en segundo plano y el daemon quedó disponible para las verificaciones reales.
- El sandbox denegó inicialmente las descargas npm (`EACCES`). Se repitió la instalación con acceso de red aprobado y exclusivamente desde el lock ya autorizado; no cambió ninguna versión.

## Known Stubs

None. Las celdas `_pending_` del encabezado de evidencia manual son campos procedurales que se rellenan durante cada revisión humana, no datos de aplicación ni una implementación incompleta.

## Threat Flags

| Flag | File | Description |
|---|---|---|
| threat_flag: local-database-boundary | `infra/compose.yaml` | Introduce una red Compose interna y credenciales sintéticas locales; PostgreSQL no publica puerto al host y los runners no imprimen el DSN. |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Los planes de scaffold y dominio pueden ejecutar comprobaciones rápidas sobre los tres runners reales.
- Los fixtures hostiles y el protocolo manual están listos para enlazarse a las pruebas funcionales posteriores.
- No hay bloqueos; las verificaciones dependen de Docker Desktop activo para la ruta PostgreSQL.

## Self-Check: PASSED

- Los artefactos declarados existen y los commits `4aaa889` y `22d2854` están en el historial.
- Los tres runners ejecutan o descubren exactamente una prueba real.
- No se encontraron TODO, FIXME, placeholders de UI ni valores vacíos que fluyan a renderizado.
- Ningún requisito compartido se marcó prematuramente: `requirements.ready-ids` devolvió 0/3.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
