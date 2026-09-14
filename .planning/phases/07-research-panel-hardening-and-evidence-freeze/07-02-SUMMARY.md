---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 02
subsystem: auth, api, database, infra, testing
tags: [django, admin, authorization, privacy, audit, postgres, csrf, ci]

# Dependency graph
requires:
  - phase: 07-01
    provides: "Research API protegida por permisos Django, filtros publicados y contrato de errores neutros."
provides:
  - "Capacidades Django separadas Research Viewer y Platform Admin, con provisión explícita por UUID."
  - "Django Admin allowlisted y separado del frontend Next.js."
  - "Anonymization transaccional por defecto, borrado irreversible restringido y auditoría append-only saneada."
  - "Gates de seguridad, secretos, dependencias, migraciones y cabeceras integrados en CI."
affects: [07-03, 07-04, research-panel, operations, security]

# Actuals (#2632)
actuals:
  tokens: 17040
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Capability server-side con permiso Django explícito; nunca is_staff, cookies, nombres o señales del frontend."
    - "ModelAdmin allowlisted: escritura solo donde está revisada y proyecciones operativas readonly."
    - "Servicio de privacidad transaccional con evento auditado y trigger PostgreSQL append-only."

key-files:
  created:
    - apps/api/evaluation/migrations/0001_phase7_permissions.py
    - apps/api/platform_admin/admin_site.py
    - apps/api/audit/models.py
    - apps/api/audit/services.py
    - apps/api/audit/migrations/0001_append_only_audit.py
    - apps/api/accounts/migrations/0004_phase7_anonymization.py
    - scripts/check-security.ps1
    - .github/workflows/quality-gates.yml
    - docs/verification/phase-07-admin-security.md
    - ideas-vault/Fases/2026-09-14 - Roles admin privacidad y auditoria.md
  modified:
    - apps/api/evaluation/access.py
    - apps/api/accounts/models.py
    - apps/api/accounts/services.py
    - apps/api/accounts/admin.py
    - apps/api/platform_admin/admin_site.py
    - apps/api/config/settings.py
    - apps/api/config/urls.py
    - apps/api/tests/test_phase7_admin_security.py
    - apps/api/evaluation/tests/test_phase7_api.py

key-decisions:
  - "Platform Admin usa exclusivamente evaluation.access_platform_admin; se elimina el fallback auth.change_user."
  - "La operación normal de privacidad es desactivar y anonimizar; el borrado exige superusuario, confirmación exacta y auditoría previa."
  - "El historial de auditoría no admite payload libre ni mutaciones SQL posteriores; PostgreSQL rechaza UPDATE y DELETE."

patterns-established:
  - "Los grupos de fase 07 no se asignan automáticamente: bootstrap_phase7_roles requiere UUID técnico explícito."
  - "Los resultados, hashes, estados derivados y eventos de auditoría se presentan como solo lectura en Django Admin."

requirements-completed: [ADMIN-01, ADMIN-02, SEC-01, SEC-04, SEC-06, SEC-07, SEC-08, PRIV-02, OPS-05]

coverage:
  - id: D1
    description: "Research Viewer y Platform Admin son capacidades separadas y el bootstrap explícito es idempotente."
    requirement: ADMIN-01
    verification:
      - kind: integration
        ref: "apps/api/tests/test_phase7_admin_security.py - test_platform_admin_site_uses_distinct_capability_not_staff_or_name"
        status: pass
      - kind: integration
        ref: "apps/api/tests/test_phase7_admin_security.py - test_explicit_uuid_role_bootstrap_is_idempotent_and_separate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Django Admin protegido y allowlisted gestiona únicamente modelos revisados; Next.js no contiene la superficie administrativa."
    requirement: ADMIN-02
    verification:
      - kind: integration
        ref: "apps/api/tests/test_phase7_admin_security.py - test_platform_admin_registry_is_allowlisted_and_operational_data_is_readonly"
        status: pass
      - kind: other
        ref: "powershell -ExecutionPolicy Bypass -File scripts/check-security.ps1"
        status: pass
    human_judgment: false
  - id: D3
    description: "Anonymization por defecto y borrado irreversible protegido por superusuario, confirmación y ownership."
    requirement: PRIV-02
    verification:
      - kind: integration
        ref: "apps/api/tests/test_phase7_admin_security.py - anonymization/delete/csrf tests"
        status: pass
    human_judgment: false
  - id: D4
    description: "AuditEvent allowlisted, sin PII/payload libre y append-only a nivel de PostgreSQL."
    requirement: SEC-04
    verification:
      - kind: integration
        ref: "apps/api/audit/tests/test_audit.py - audit sanitation, actor, replay and database immutability tests"
        status: pass
    human_judgment: false
  - id: D5
    description: "Pipeline ejecuta gates de secretos/dependencias, cabeceras, migraciones, deploy checks y pruebas de seguridad."
    requirement: OPS-05
    verification:
      - kind: other
        ref: "git diff --check"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check --deploy"
        status: pass
      - kind: other
        ref: ".github/workflows/quality-gates.yml"
        status: pass
    human_judgment: false

# Metrics
duration: 35min
completed: 2026-09-14
status: complete
---

# Phase 07 Plan 02: Hardening de administración, privacidad y auditoría

**Django Admin separado por capability, anonymization transaccional por defecto, borrado irreversible auditado y gates fail-closed de seguridad.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-14T01:59:00+02:00
- **Completed:** 2026-09-14T02:35:24+02:00
- **Tasks:** 3/3
- **Files modified:** 32

## Accomplishments

- Se definieron las capacidades `view_research_panel`, `export_research_panel` y `access_platform_admin`, con `/admin/` autorizado únicamente por `has_perm` y grupos provisionados solo mediante UUID explícito.
- Se creó un Django Admin allowlisted con usuarios, perfiles, catálogo, biblioteca, imports, snapshots, jobs, evaluaciones y auditoría; los datos derivados y el historial son readonly y no existe re-run en Next.js.
- Se implementaron anonymization/desactivación idempotente, borrado irreversible reservado al superusuario y eventos `AuditEvent` saneados, con trigger PostgreSQL que rechaza `UPDATE`/`DELETE`.
- Se añadieron cabeceras seguras, gate de seguridad local y workflow CI sin dependencias nuevas.

## Task Commits

1. **Task 1: Tracer de capability Platform Admin a Django Admin allowlisted** — `8d90c63` (`feat`)
2. **Task 2: Auditoría append-only y anonymization de cuentas** — `baada82` (`feat`)
3. **Task 3: Hardening de cabeceras, errores, inputs y pipeline** — `48ea1ec` (`ci`)

Commit adicional de sincronización conceptual: `e2837af` (`docs`, vault).

## Verification Evidence

Todos los comandos prescritos por el plan terminaron con código cero:

- `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check` — `System check identified no issues`.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_phase7_admin_security.py -k "group or admin" -q` — `2 passed`.
- `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run` — `No changes detected`.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/audit/tests/test_audit.py apps/api/tests/test_phase7_admin_security.py -k "audit or anonym or delete or csrf" -q` — `6 passed, 3 deselected`.
- `git diff --check` — PASS.
- `powershell -ExecutionPolicy Bypass -File scripts/check-security.ps1` — `PASS: deterministic security checks completed`; el escaneo de secretos terminó con cero coincidencias no allowlisted y detectó las cuatro superficies no vacías.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_phase7_admin_security.py -q` — `7 passed`.
- Suite combinada `audit + phase7 admin security + phase7 API` — `36 passed`.
- `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check --deploy` — `System check identified no issues (4 silenced)`; los cuatro avisos son los controles HTTPS/secure-cookie esperados del perfil local.

El primer intento del test de bootstrap reveló un bug real de compatibilidad entre `call_command` y `action="append"`: un UUID escalar se iteraba por caracteres. Se corrigió normalizando argumentos escalares y listas, y la prueba pasó posteriormente.

## Decisions Made

- La autorización administrativa se limita al permiso `evaluation.access_platform_admin`; no se acepta `is_staff`, `auth.change_user`, cookie, nombre o señal del navegador como autoridad.
- Se conserva un UUID técnico opaco por perfil para provisión explícita y trazabilidad, sin usar username/email como identificador de administración.
- La privacidad reversible es el camino normal; la eliminación física es una excepción segura con superusuario, confirmación exacta, bloqueo de auto-borrado y evento previo.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalización de argumentos del comando de roles**

- **Encontrado durante:** Task 3, verificación de la suite administrativa.
- **Problema:** `call_command` suministra un valor escalar para opciones `action="append"`; el comando recorría el UUID como texto y rechazaba la cuenta.
- **Corrección:** Se añadió `_as_list` para aceptar de forma segura tanto listas de argparse como escalares de invocación programática.
- **Archivos:** `apps/api/accounts/management/commands/bootstrap_phase7_roles.py`.
- **Verificación:** `7 passed` en `test_phase7_admin_security.py` y `36 passed` en la suite combinada.
- **Commit:** `48ea1ec`.

**2. [Rule 1 - Test fixture] El fixture generaba el UUID explícito de forma no determinista en el esquema de prueba existente**

- **Encontrado durante:** Task 3, prueba de bootstrap.
- **Problema:** El valor obtenido del perfil del fixture no era un UUID válido en la base de pruebas creada, impidiendo probar el contrato explícito.
- **Corrección:** El fixture asigna y persiste un `uuid.uuid4()` explícito antes de invocar el comando; no relaja la validación de producción.
- **Archivos:** `apps/api/tests/test_phase7_admin_security.py`.
- **Verificación:** La prueba de provisión idempotente pasa con PostgreSQL de pruebas.
- **Commit:** `48ea1ec`.

**3. [Rule 1 - Compatibility] Actualización de fixture de permisos de API**

- **Encontrado durante:** verificación combinada tras retirar el fallback `accounts.manage_platform`.
- **Problema:** El test API seguía creando un permiso sintético antiguo y ya no ejercía la capability establecida.
- **Corrección:** El fixture usa `evaluation.access_platform_admin` migrado.
- **Archivos:** `apps/api/evaluation/tests/test_phase7_api.py`.
- **Verificación:** Suite combinada `36 passed`.
- **Commit:** `48ea1ec`.

### Critical project compliance

Se sincronizó el vault vivo con la decisión de arquitectura y privacidad nueva en `e2837af`, conforme a `AGENTS.md`/`CONVENTIONS.md`. No se añadieron paquetes ni se modificaron los planes 07-03/07-04.

**Total deviations:** 3 auto-fixed; 1 compliance documentation update.
**Impact:** Todas fueron necesarias para que las pruebas ejercieran la autoridad real y para mantener la documentación viva; no amplían el alcance funcional del plan.

## Issues Encountered

La base de desarrollo persistente no tenía aplicada inicialmente la columna `accounts_accountprofile.admin_uuid`; se verificó el estado con una consulta de solo lectura y se usó la base PostgreSQL de pruebas gestionada por Docker. Las migraciones del repositorio quedaron limpias (`No changes detected`) y todos los gates ejecutados pasaron. No queda una prueba esperando entorno.

`check-security.ps1` mostró advertencias de `Test-Path` para algunos nombres de archivo del vault con caracteres escapados por PowerShell, pero terminó con código cero y el resultado explícito `PASS`; no hubo coincidencias de secretos ni fallo de gate.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

07-02 está listo para integración. La superficie administrativa está preparada para que 07-03/07-04 consuman sus capacidades y proyecciones, sin adelantar su implementación. El único cuidado operativo es aplicar migraciones antes de usar una base de desarrollo persistente creada con un esquema anterior.

## Self-Check: PASSED

- SUMMARY creado en la ruta prescrita.
- Commits `8d90c63`, `baada82`, `48ea1ec` y `e2837af` existen en el historial.
- Las pruebas y gates citados arriba terminaron con código cero.

---
*Phase: 07-research-panel-hardening-and-evidence-freeze*
*Completed: 2026-09-14*
