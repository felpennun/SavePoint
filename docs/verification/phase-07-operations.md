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

## Verificaciones

- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts/check-backup-manifest.ps1 -Help`
- Validación de manifiesto y SHA-256 en un directorio temporal privado.
- Restore desechable con migraciones, constraints, conteos esenciales y smoke
  de `/health/`.
- `scripts/check-secrets.ps1` sobre código, manifiestos y superficies de logs.

## Trazabilidad

| Requisito | Evidencia |
|---|---|
| PORT-02 / PORT-03 | `apps/api/library/tests/test_portability.py` y los endpoints de preview/apply |
| OPS-04 | `docs/deployment/backup-recovery.md` y scripts de backup/rotación/restore |
| OPS-05 | `apps/api/config/observability.py` y `apps/api/tests/test_phase7_operations.py` |
| ADMIN-02 | Estados saneados consultables desde Django Admin, sin edición directa |

Los límites de tamaño, retención y restauración son decisiones operativas
explícitas y deben repetirse en cada ejecución de evidencia.
