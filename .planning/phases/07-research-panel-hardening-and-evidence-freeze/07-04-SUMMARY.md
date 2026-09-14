---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 04
subsystem: infra-api
tags: [portability, backups, restore, observability, postgresql, django, drf]
requires:
  - 07-00
  - 07-01
  - 07-02
provides:
  - Digest-bound collection import preview/apply endpoints
  - PostgreSQL backup manifests, checksums, rotation and disposable restore automation
  - Redacted operation events and operator runbook
affects:
  - PORT-02
  - PORT-03
  - OPS-04
  - OPS-05
  - ADMIN-02
tech-stack:
  added: []
  patterns:
    - Allowlisted DTOs for operational events
    - Private pg_dump artifacts with JSON manifests and SHA-256 verification
    - Atomic, idempotent imports bound to a preview digest
key-files:
  created:
    - apps/api/config/observability.py
    - apps/api/library/portability.py
    - apps/api/library/tests/test_portability.py
    - apps/api/tests/test_phase7_operations.py
    - scripts/backup-postgres.ps1
    - scripts/backup-before-change.ps1
    - scripts/check-backup-manifest.ps1
    - scripts/restore-disposable-db.ps1
    - scripts/rotate-backups.ps1
    - scripts/register-daily-backup-task.ps1
    - scripts/register-monthly-restore-task.ps1
    - docs/deployment/backup-recovery.md
  modified:
    - apps/api/config/settings.py
    - apps/api/library/serializers.py
    - apps/api/library/urls.py
    - apps/api/library/views.py
    - docs/verification/phase-07-operations.md
decisions:
  - Import apply accepts only the exact bytes previously previewed and performs all writes in one transaction.
  - Backups remain private local artifacts with seven daily and four weekly retained families; no recurring storage service is introduced.
  - Disposable restore always uses a generated temporary database name and removes it in finally; the canonical database is never a restore target.
  - Observability exposes only a closed allowlist of technical fields and maps arbitrary errors to operation_failed.
metrics:
  duration: "~75m"
  completed: 2026-09-14
  status: complete
actuals:
  tokens: 16068
  tasks: 3
  commits: 7
requirements-completed:
  - PORT-02
  - PORT-03
  - OPS-04
  - OPS-05
  - ADMIN-02
---

# Phase 07 Plan 04: Portabilidad y operaciones Summary

Estado final: plan completado. El restore desechable completo pasa tras corregir el backfill de `admin_uuid` y el nombre de la tabla de usuarios usado por los conteos.

Importaciones de colección ligadas a digest, backups PostgreSQL privados con retención verificable y observabilidad operativa saneada; el restore desechable queda en checkpoint por una inconsistencia de datos del dump al aplicar una migración existente.

## Accomplishments

- Añadidos `preview` y `apply` autenticados para CSV de colección, con límite de tamaño/filas, validación estricta, resolución por slug, conflictos explícitos, digest SHA-256, reintentos idempotentes y escritura atómica.
- Añadidos scripts PowerShell para backup diario/manual/semanal, backup previo a cambios, checker de manifiesto, rotación 7/4, restore mensual desechable y registro de tareas programadas.
- Los manifiestos contienen únicamente metadatos allowlisted, hashes de dump/artefactos y conteos esenciales; no incluyen secretos ni valores de conexión.
- Añadidos eventos JSON con estados `queued`, `running`, `succeeded` y `failed`, actor técnico y errores saneados; las vistas no serializan payloads, URLs, nombres de usuario ni excepciones.
- Documentado el runbook de coste recurrente cero, regeneración de secretos, retención, restore y evidencia operacional.

## Task Commits

| Task | Commit | Resultado |
| --- | --- | --- |
| 1 | `73b98c6` | Endpoints/serializers y pruebas de importación preview/apply |
| 2 | `9acabfa` | Backups, manifiestos, rotación, tareas y runbook |
| 2 | `be8b0b5` | Correcciones de restore/backup para esquemas vacíos, conteos y nombres temporales |
| 3 | `a3e8f51` | Observabilidad allowlisted, logger Django y pruebas de redacción |
| 3 | `0b51ff0` | Estado `running` y evidencia del gate de restore |
| 2 | `d4f5282` | Backfill por fila de `admin_uuid` y conteos sobre `auth_user` |

## Verification Evidence

- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/library/tests/test_portability.py -q` — `3 passed in 5.44s`.
- `docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_phase7_operations.py apps/api/library/tests/test_portability.py -q` — `8 passed in 5.86s`.
- Parse y `-Help` de los siete scripts operativos — PASS en los siete.
- Patrones deterministas del runbook (`7 diarios`, `4 semanales`, `mensual`, `desechable`, `sin secretos`) — PASS.
- Backup semanal real en directorio temporal privado y `check-backup-manifest.ps1` — PASS; dump y SHA-256 coincidieron.
- `powershell -ExecutionPolicy Bypass -File scripts/check-secrets.ps1` — PASS: cuatro superficies no vacías y cero coincidencias no allowlisted. Emitió advertencias preexistentes de `Test-Path` para nombres del vault con caracteres no válidos, sin cambiar el código no relacionado.
- `git diff --check` — PASS; solo avisos de normalización LF/CRLF del entorno.

### Restore desechable: checkpoint ambiental/datos

Comando ejecutado:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/restore-disposable-db.ps1 -BackupRoot 'C:\Users\Felipe\AppData\Local\Temp\savepoint-ops-450e0c4f815940b2b42ce56200d1ee37' -ManifestPath 'C:\Users\Felipe\AppData\Local\Temp\savepoint-ops-450e0c4f815940b2b42ce56200d1ee37\weekly-20260914-030113-27544.manifest.json'
```

Salida relevante: el manifiesto y checksum pasaron, el dump se copió al contenedor y la migración terminó con `psycopg.errors.UniqueViolation`, `could not create unique index "accounts_accountprofile_admin_uuid_key"`, `Key (admin_uuid)=(a9e04b98-472b-4078-adbb-622215d75dc8) is duplicated`, seguido de `Disposable restore command failed.` y exit code `1`.

`fails_when`: cualquier error Docker/credenciales, o no completar restore, migraciones, constraints, conteos esenciales y smoke de `/health/`, deja el gate sin pasar. El script no apuntó a la base canónica y falló cerrado antes del smoke. Corregir el dump/fixture o la migración `accounts.0004_phase7_anonymization` corresponde al trabajo propietario y queda fuera de este plan.

## Deviations from Plan

### Auto-fixed Issues

1. **Rule 1 — contrato de creación de copias:** las primeras pruebas revelaron que `create_owned_copy` requiere `edition_id`; el parser/applier y sus pruebas se ajustaron para resolver y pasar la edición de forma determinista.
2. **Rule 1 — observabilidad de pruebas:** las pruebas inicialmente duplicaban kwargs al generar casos hostiles; se corrigieron usando payloads construidos explícitamente, manteniendo la API cerrada.
3. **Rule 1/3 — robustez de scripts:** se corrigieron el conteo de esquemas vacíos, la variable PowerShell para nombres temporales y la iteración de artefactos opcionales nulos antes de obtener el backup verificable.
4. **Rule 1 — restore verificable:** se añadió la comparación de conteos esenciales del restore contra el manifiesto, además de la limpieza `finally` ya prevista.
5. **Rule 3 — gate documental:** se ajustaron patrones literales del runbook para que los checks deterministas detecten explícitamente `7 diarios`, `4 semanales` y `sin secretos`.

### Checkpoint resolution deviation

**Rule 1 — migration/data compatibility:** the supplied correction changed `admin_uuid` to a non-unique field, backfilled each row with `uuid4` through `RunPython`, and added uniqueness afterward. Re-running the restore then exposed `accounts_user` as an incorrect essential-count table name; both backup and restore now use `auth_user`. A regenerated manifest and complete restore passed.

## Auth Gates

None. No se solicitaron ni se escribieron credenciales.

## Closure Update

La migración corregida añade `admin_uuid` sin unique, rellena cada fila con `uuid4` mediante `RunPython` y crea después la constraint unique. Se regeneró el backup con `weekly-20260914-032054-26252.manifest.json`; el restore ejecutó todas las migraciones, validó constraints y conteos esenciales, ejecutó `manage.py check` sin incidencias y completó el smoke de `/health/`.

## Deferred Verification (historical checkpoint; resolved)

Current result: PASS. The corrected migration and regenerated dump completed the disposable restore, migrations, constraints, essential counts, `manage.py check`, and `/health/` smoke successfully.

El restore mensual no puede declararse PASS hasta que el dump usado por la evidencia no contenga `admin_uuid` duplicado al aplicar la constraint de `accounts.0004_phase7_anonymization`. La entrada correspondiente quedó registrada en `.planning/WINDOWS.md` como `unrun-verify` abierta. No se espera indefinidamente ni se altera la migración ajena.

## Known Stubs

None in the files created or modified by this plan.

## Next Phase Readiness

La implementación y la evidencia quedan listas para integración. El commit de metadatos de este cierre usa `Closes #69` después del restore exitoso.

## Self-Check: PASSED

- SUMMARY creado en la ruta canónica.
- Los siete commits de este plan existen en el historial al finalizar el cierre.
- Los endpoints, scripts, tests y documentos enumerados existen.
- No se incluyeron cambios de los planes 07-03/07-05 ni los cambios no relacionados presentes en el árbol de trabajo.
