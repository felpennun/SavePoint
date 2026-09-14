# Backup y recuperación de SavePoint

Este runbook mantiene una ruta local y de coste recurrente cero para la demo
académica. PostgreSQL es la fuente transaccional; el dump es privado y los
artefactos saneados se publican solo cuando son necesarios y lícitos.

## Política

- `backup-postgres.ps1 -BackupKind daily` crea un dump PostgreSQL custom-format,
  checksum SHA-256 y manifiesto allowlisted.
- `backup-before-change.ps1` exige `migration`, `import`, `deploy` o `config` y
  crea el backup manual antes de modificar el sistema.
- `rotate-backups.ps1` conserva exactamente la ventana: 7 diarios y 4 semanales;
  los ficheros permanecen en almacenamiento privado.
- `restore-disposable-db.ps1` valida el manifiesto, restaura en una base
  desechable con nombre único, ejecuta migraciones, `manage.py check` y el smoke
  de health, y elimina únicamente esa base aunque falle el proceso.

Política sin secretos: nunca se copian contraseñas, tokens, cookies, cadenas
de conexión ni logs brutos. Los secretos se regeneran en el entorno de destino
mediante su gestor local de variables; no se recuperan desde el dump.

## Operación local

```powershell
$backupRoot = 'D:\savepoint-private-backups'
powershell -ExecutionPolicy Bypass -File scripts/backup-postgres.ps1 -BackupRoot $backupRoot -BackupKind daily
powershell -ExecutionPolicy Bypass -File scripts/backup-before-change.ps1 -BackupRoot $backupRoot -ChangeType migration
powershell -ExecutionPolicy Bypass -File scripts/rotate-backups.ps1 -BackupRoot $backupRoot
powershell -ExecutionPolicy Bypass -File scripts/check-backup-manifest.ps1 -ManifestPath 'D:\savepoint-private-backups\weekly-YYYYMMDD-HHMMSS-PID.manifest.json'
powershell -ExecutionPolicy Bypass -File scripts/restore-disposable-db.ps1 -BackupRoot $backupRoot
```

Para PostgreSQL fuera de Compose se puede usar `-Native`; la autenticación la
resuelve libpq desde el entorno del operador y nunca se escribe como argumento.
Las tareas programadas solo contienen la ruta del directorio privado y el
script: no contienen secretos ni payloads de aplicación.

## Programación sin servicio de pago

Registrar la tarea diaria y la restauración mensual en el Programador de tareas
local con `register-daily-backup-task.ps1` y
`register-monthly-restore-task.ps1`. La restauración mensual debe ejecutarse
contra PostgreSQL local o un destino temporal gratuito ya disponible; no se
supone SLA, almacenamiento externo ni proveedor de pago.

## Recuperación

1. Conservar el manifiesto y su dump fuera del repositorio y verificar su SHA-256.
2. Regenerar las credenciales del destino y configurar variables por nombre.
3. Ejecutar la restauración mensual sobre la base desechable.
4. Revisar conteos, constraints, migraciones y health antes de cualquier cambio
   de destino canónico.
5. Hacer un nuevo backup manual antes de una migración, import, despliegue o
   cambio de configuración posterior.

La evidencia publicable consiste únicamente en manifiestos y hashes saneados;
el dump privado nunca entra en releases, Issues, logs ni en Git.
