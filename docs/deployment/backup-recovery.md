# Backup y recuperación de SavePoint

Este documento recoge cómo se hacen y se restauran copias de seguridad de la base de datos PostgreSQL de SavePoint con un coste recurrente cero. PostgreSQL es la fuente transaccional; el volcado es privado y nunca entra en Git, en issues, en registros ni en lanzamientos. Solo se pueden publicar manifiestos y sumas de verificación saneados.

## Política

- `scripts/backup-postgres.ps1` crea un volcado en formato *custom* de PostgreSQL, su SHA-256 y un manifiesto con una lista de campos permitidos: tipo de copia, fecha UTC, commit de Git, huella de las migraciones y recuentos esenciales (usuarios, obras, entradas de biblioteca y copias). No incluye secretos.
- Los tipos de copia son `daily`, `weekly` y `manual`. Se hace una copia `manual` antes de cualquier migración, importación, despliegue o cambio de configuración.
- La política de retención es conservar los últimos 7 volcados diarios y 4 semanales, siempre en almacenamiento privado fuera del repositorio.
- Política sin secretos: nunca se copian contraseñas, tokens, cookies, cadenas de conexión ni registros sin revisar. Los secretos se regeneran en el entorno de destino a través de su gestor de variables y no se recuperan del volcado.

## Hacer una copia

```powershell
$backupRoot = 'D:\savepoint-private-backups'   # directorio privado, fuera del repositorio
powershell -ExecutionPolicy Bypass -File scripts/backup-postgres.ps1 -BackupRoot $backupRoot -BackupKind manual
```

El script obtiene el volcado de la base de datos del contenedor `db` de Compose. Para un PostgreSQL fuera de Compose se usa `-Native`; la autenticación la resuelve `libpq` desde el entorno de quien lo ejecuta y nunca se pasa como argumento. Junto al volcado quedan el fichero `.sha256` y el manifiesto `.manifest.json`.

## Programación sin servicio de pago

La copia diaria se puede programar con el Programador de tareas del sistema, que solo necesita la ruta del directorio privado y la del script: la tarea no contiene secretos ni datos de la aplicación. No se supone ningún SLA, almacenamiento externo ni proveedor de pago.

## Recuperación

1. Conservar el manifiesto y su volcado fuera del repositorio y comprobar el SHA-256 del volcado contra el del manifiesto.
2. Restaurar siempre primero en una **base desechable** con nombre único (`pg_restore` sobre una base nueva), nunca encima de la base en uso.
3. Aplicar las migraciones, ejecutar `manage.py check` y comprobar `GET /health/`.
4. Revisar los recuentos, las restricciones y las migraciones contra los del manifiesto antes de cambiar el destino canónico.
5. Regenerar las credenciales del destino y configurarlas por nombre de variable.
6. Hacer una copia `manual` nueva antes de cualquier migración, importación, despliegue o cambio de configuración posterior.

La base de producción alojada en Neon tiene sus propios mecanismos de recuperación y no se cubre con este procedimiento.
