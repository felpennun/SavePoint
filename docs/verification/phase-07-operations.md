# Evidencia operativa de la Fase 07

## Alcance

Esta evidencia cubre `PORT-02`, `PORT-03`, `OPS-04`, `OPS-05` y la supervisión
allowlisted de imports/jobs exigida por `ADMIN-02`. No contiene dumps,
credenciales, cookies, URLs con secretos ni logs brutos.

## Backup y restore

Los scripts `backup-postgres.ps1`, `backup-before-change.ps1`,
`rotate-backups.ps1` y `restore-disposable-db.ps1` forman una cadena local de
coste recurrente cero. El manifiesto registra commit, corpus, protocolo,
fingerprint de migraciones y hashes de artefactos saneados. El checker rechaza
campos incompletos, paths fuera de `BackupRoot` y checksums incorrectos.

La retención es de 7 diarios y 4 semanales. El restore mensual usa un nombre de
base `savepoint_restore_*` generado en cada ejecución y elimina solo ese nombre
en `finally`; nunca recibe la base canónica como destino. Las tareas programadas
no llevan secretos en sus argumentos.

## Observabilidad

`config.observability` emite JSON únicamente con `operation_ref`, actor técnico,
tipo, estado, timestamps, recurso allowlisted y duración. Las transiciones
operativas usan `queued`, `running`, `succeeded` y `failed`; cualquier excepción
se transforma en `operation_failed`. No se serializan filenames, URLs, payloads,
cookies, tokens, cadenas de conexión ni mensajes de excepción. Django configura
el logger `savepoint.operations` con salida de consola para que Admin y los
operadores puedan correlacionar una operación sin consultar datos sensibles.

## Verificaciones

- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts/check-backup-manifest.ps1 -Help`
- Validación de manifiesto y SHA-256 en un directorio temporal privado.
- Restore desechable con migraciones, constraints, conteos esenciales y smoke
  de `/health/`.
- `scripts/check-secrets.ps1` sobre código, manifiestos y superficies de logs.

### Resultado del restore desechable

El backup semanal y la comprobaciÃ³n de su manifiesto sÃ­ pasaron. El restore
mensual se ejecutÃ³ con:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/restore-disposable-db.ps1 -BackupRoot 'C:\Users\Felipe\AppData\Local\Temp\savepoint-ops-450e0c4f815940b2b42ce56200d1ee37' -ManifestPath 'C:\Users\Felipe\AppData\Local\Temp\savepoint-ops-450e0c4f815940b2b42ce56200d1ee37\weekly-20260914-030113-27544.manifest.json'
```

La salida verificÃ³ el manifiesto y copiÃ³ el dump al contenedor, pero la
migraciÃ³n de la base desechable terminÃ³ con `psycopg.errors.UniqueViolation`:
`could not create unique index "accounts_accountprofile_admin_uuid_key"`,
`Key (admin_uuid)=(a9e04b98-472b-4078-adbb-622215d75dc8) is duplicated`, y
`Disposable restore command failed.` (exit code 1). La base canÃ³nica no fue
usada como destino y el script fallÃ³ cerrado antes del smoke de `/health/`.

`fails_when` del gate operativo: cualquier error de Docker/credenciales, o no
completar restore + migraciones + constraints + conteos esenciales + smoke de
`/health/`, deja esta verificaciÃ³n sin pasar. El bloqueo actual es el dato
duplicado que impide aplicar `accounts.0004_phase7_anonymization`; requiere
corregir el fixture/dump o la migraciÃ³n en el trabajo propietario antes de
repetir el restore. No se modifica aquÃ­ porque queda fuera del alcance de
portabilidad/operaciones de este plan.

## Trazabilidad

| Requisito | Evidencia |
|---|---|
| PORT-02 / PORT-03 | `apps/api/library/tests/test_portability.py` y los endpoints de preview/apply |
| OPS-04 | `docs/deployment/backup-recovery.md` y scripts de backup/rotación/restore |
| OPS-05 | `apps/api/config/observability.py`, `apps/api/config/settings.py` y `apps/api/tests/test_phase7_operations.py` |
| ADMIN-02 | Estados saneados consultables desde Django Admin, sin edición directa |

Los límites de tamaño, retención y restauración son decisiones operativas
explícitas y deben repetirse en cada ejecución de evidencia.
