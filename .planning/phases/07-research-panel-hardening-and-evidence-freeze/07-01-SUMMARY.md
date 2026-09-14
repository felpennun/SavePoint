---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 01
subsystem: api
tags: [django, drf, session-auth, permissions, allowlist, exports, evidence]

requires:
  - phase: 07-research-panel-hardening-and-evidence-freeze
    provides: Contrato inmutable v15, DTOs allowlisted, hashes y exportadores saneados de 07-00.
provides:
  - API Django backend-first protegida para runs, comparación, artefactos y exportaciones.
  - Capabilities server-side separadas para Research Viewer y Platform Admin.
  - Matriz pytest de autenticación, permisos, filtros, CSRF, headers, secretos y throttle.
  - Documentación HTTP y trazabilidad de la API de investigación.
affects: [07-02, 07-03, 07-05, research-panel, django-admin]

actuals:
  tokens: 8493
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - Permisos Django server-side con 404 neutro para cuentas autenticadas sin capability.
    - Vistas DRF read-only con parser de query allowlisted, DTOs manuales y no-store.
    - Exportaciones backend con formatos, MIME, Content-Disposition y SHA-256 fijos.

key-files:
  created:
    - apps/api/evaluation/access.py
    - apps/api/evaluation/serializers.py
    - apps/api/evaluation/views.py
    - apps/api/evaluation/urls.py
    - apps/api/evaluation/tests/test_phase7_api.py
    - docs/verification/phase-07-research-api.md
    - ideas-vault/Fases/2026-09-14 - API protegida del panel de investigacion.md
  modified:
    - apps/api/accounts/views.py
    - apps/api/accounts/serializers.py
    - apps/api/accounts/tests/test_account_me.py
    - apps/api/config/urls.py
    - apps/api/config/settings.py

key-decisions:
  - "Research Viewer se resuelve exclusivamente con evaluation.view_research_panel mediante has_perm; Platform Admin mantiene una capability distinta y no concede acceso al panel."
  - "El parámetro HTTP format queda bajo el control de la allowlist de exports; se desactiva el URL renderer override de DRF para que csv y svg no terminen en 404 antes de la vista."
  - "La publicación v15 se conserva como única fuente: la API no recalcula, no consulta el runner y no sirve per_user, logs, dumps ni secretos."

requirements-completed: [EVAL-13, EVAL-14, SEC-01, SEC-03, SEC-04, SEC-05, SEC-06, QUAL-01]

coverage:
  - id: D1
    description: "Una cuenta Research Viewer consulta la comparación v15 real mediante una ruta DRF protegida."
    requirement: EVAL-13
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_api.py::test_viewer_can_read_real_v15_comparison"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check"
        status: pass
    human_judgment: false
  - id: D2
    description: "Runs, artefactos, filtros y exportaciones permanecen allowlisted, saneados y limitados al snapshot publicado."
    requirement: EVAL-14
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_api.py -q (26 passed)"
        status: pass
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_contract.py -q (16 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "La autoridad backend, la separación de roles y los controles HTTP de seguridad están probados y documentados."
    requirement: SEC-01
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_api.py -q (roles, 404, CSRF, IDOR, inputs, headers, secrets, throttle)"
        status: pass
      - kind: other
        ref: "docs/verification/phase-07-research-api.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "MeView expone capabilities calculadas por el backend sin mezclar Research Viewer con Platform Admin."
    requirement: QUAL-01
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_api.py::test_combined_capabilities_are_separate_server_decisions"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_account_me.py -q"
        status: pass
    human_judgment: false

duration: 26 min
completed: 2026-09-14
status: complete
---

# Phase 07 Plan 01: Research API hardening Summary

**API Django backend-first para la publicación v15, con Research Viewer por permiso, 404 neutro, filtros allowlisted y exportaciones saneadas**

## Performance

- **Duration:** 26 min
- **Started:** 2026-09-14T01:32:00+02:00
- **Completed:** 2026-09-14T01:57:36+02:00
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Se publicaron cuatro endpoints GET (`runs`, `comparison`, `artifacts` y `exports`) conectados exclusivamente al contrato inmutable del plan 07-00.
- `ResearchViewerPermission` exige sesión y `has_perm("evaluation.view_research_panel")`; las cuentas autenticadas sin permiso reciben 404 neutro y las anónimas reciben autenticación DRF.
- `MeView` devuelve capabilities explícitas y separadas; las consultas, exportaciones, headers y DTOs se validan y sanean en backend.
- La suite dedicada cubre roles, IDOR, inyección, XSS, CSRF, métodos no permitidos, redirects/rutas, secretos y throttle; la suite completa de evaluación quedó en `154 passed`.

## Task Commits

Cada tarea fue commiteada atómicamente:

1. **Task 1: Tracer GET comparison protegido hasta el snapshot publicado** - `30a0a87` (feat)
2. **Task 2: Completar runs, artifacts, exports y capability de cuenta** - `cf378fd` (feat)
3. **Task 3: Cerrar pruebas de autoridad backend y contrato HTTP** - `62f05aa` (test)

Commit adicional requerido por `AGENTS.md` para sincronizar el vault vivo: `27c1c59` (docs).

**Plan metadata:** se añadirá en el commit de cierre tras el autochequeo.

## Files Created/Modified

- `apps/api/evaluation/access.py` - capability de Research Viewer, capability administrativa separada y permiso DRF.
- `apps/api/evaluation/views.py` - endpoints GET read-only, parser de filtros, no-store y descargas seguras.
- `apps/api/evaluation/serializers.py` - proyecciones manuales de runs, comparación y artefactos.
- `apps/api/evaluation/urls.py` y `apps/api/config/urls.py` - integración de `/api/evaluation/`.
- `apps/api/evaluation/tests/test_phase7_api.py` - matriz de seguridad y contrato HTTP.
- `apps/api/accounts/views.py`, `apps/api/accounts/serializers.py` - capabilities server-side en `MeView`.
- `apps/api/accounts/tests/test_account_me.py` - actualización de la allowlist esperada de `MeView`.
- `apps/api/config/settings.py` - scope `research` y desactivación segura del URL renderer override de DRF.
- `docs/verification/phase-07-research-api.md` - documentación, procedencia, límites y trazabilidad.
- `ideas-vault/Fases/2026-09-14 - API protegida del panel de investigacion.md` - sincronización del vault vivo.

## Decisions Made

- La API consume la publicación v15 validada por 07-00 y nunca importa el runner ni reconstruye rankings desde datos vivos.
- La authorization se decide en cada endpoint con permisos Django; el nombre de usuario, `is_staff`, cookies y cualquier estado del frontend no sustituyen a `has_perm`.
- La descarga es siempre backend-first: `csv`, `json` y `svg` usan contenido del snapshot, filename constante, MIME explícito y checksum.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Registrar el throttle `research` antes del tracer**

- **Found during:** Task 1 (Tracer GET comparison protegido hasta el snapshot publicado)
- **Issue:** La nueva vista declaraba `ScopedRateThrottle` con scope `research`, pero settings aún no tenía una tarifa y DRF fallaba con `ImproperlyConfigured` antes de ejecutar la vista.
- **Fix:** Se añadió `research: 60/min` manteniendo intactas las tarifas existentes.
- **Files modified:** `apps/api/config/settings.py`
- **Verification:** Tracer dedicado y `manage.py check` pasan.
- **Committed in:** `30a0a87`.

**2. [Rule 1 - Bug] Evitar que DRF intercepte `format=csv|svg`**

- **Found during:** Task 2 (Completar runs, artifacts, exports y capability de cuenta)
- **Issue:** El URL renderer override global de DRF interpretaba `format=csv` y `format=svg` antes de la vista y devolvía 404, aunque JSON funcionaba.
- **Fix:** Se fijó `REST_FRAMEWORK.URL_FORMAT_OVERRIDE = None`, dejando `format` bajo la allowlist estricta del endpoint de exportación.
- **Files modified:** `apps/api/config/settings.py`, `apps/api/evaluation/tests/test_phase7_api.py`
- **Verification:** Los tres formatos de exportación pasan y la suite API queda en `26 passed`.
- **Committed in:** `cf378fd`.

**3. [Rule 1 - Test contract] Actualizar el test de allowlist de `MeView`**

- **Found during:** Task 2 (Completar runs, artifacts, exports y capability de cuenta)
- **Issue:** La ampliación prevista de la proyección explícita hacía obsoleto el test existente que exigía exactamente dos claves.
- **Fix:** Se extendió la expectativa para comprobar el objeto `capabilities` y sus valores por defecto.
- **Files modified:** `apps/api/accounts/tests/test_account_me.py`
- **Verification:** Tests de `MeView` pasan junto con la suite API.
- **Committed in:** `cf378fd`.

**4. [Rule 2 - AGENTS.md] Sincronizar el vault vivo**

- **Found during:** cierre de Task 3
- **Issue:** La implementación produjo una decisión de arquitectura y un contrato de seguridad nuevos que `AGENTS.md` exige registrar en `ideas-vault/`.
- **Fix:** Se añadió una nota fechada enlazada a la evidencia canónica y a los planes 07-00/07-01, sin secretos ni logs.
- **Files modified:** `ideas-vault/Fases/2026-09-14 - API protegida del panel de investigacion.md`
- **Verification:** Nota presente y commit documental separado.
- **Committed in:** `27c1c59`.

**Total deviations:** 4 auto-fixed (Rule 3: 1; Rule 1: 2; Rule 2/AGENTS.md: 1).
**Impact on plan:** Todas fueron correcciones directamente necesarias para que el tracer, los formatos exigidos, los tests existentes y la trazabilidad de proyecto funcionaran; no se instalaron dependencias ni se tocaron otros planes o snapshots.

## Issues Encountered

- El primer staging encontró `Permission denied` al crear `.git/index.lock`; se reintentó con aprobación elevada y los commits se realizaron correctamente.
- Un intento inicial de staging del vault no citó su ruta con espacios; se dejó fuera del commit de código y se incorporó después en el commit documental separado `27c1c59`.

## Authentication Gates

None - no se necesitaron credenciales ni servicios externos.

## User Setup Required

None - no hay dependencias nuevas ni configuración externa requerida.

## Known Stubs

None. El panel queda limitado intencionadamente a la publicación v15 existente y no incluye re-run, mutación ni cálculo de métricas.

## Next Phase Readiness

07-02 puede añadir/provisionar los grupos y permisos de administración sobre esta base sin cambiar el contrato HTTP. 07-03 puede consumir las cuatro rutas y la capability `can_view_research`; debe conservar el orden y los valores recibidos, sin recalcular en cliente. 07-05 debe mantener los checks de v15/v16, secretos, headers y evidencia final.

---
*Phase: 07-research-panel-hardening-and-evidence-freeze*
*Plan: 01*
*Completed: 2026-09-14*

## Self-Check: PASSED

- `07-01-SUMMARY.md` existe en la ruta canónica.
- Los commits `30a0a87`, `cf378fd`, `62f05aa` y `27c1c59` existen en el historial.
- `git diff --check` no encontró errores.
