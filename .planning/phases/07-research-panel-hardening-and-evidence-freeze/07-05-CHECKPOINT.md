---
phase: 07
plan: 05
status: checkpoint
updated: 2026-09-14
---

# Checkpoint de Task 3

La gate `scripts/verify-phase-07-launch.ps1` se detuvo fail-closed durante el
backup semanal desechable. El proceso hijo observado era `pg_dump --format=custom`
contra el servicio `db`; permaneció activo varios minutos sin producir el
directorio temporal ni el manifest esperado. La ejecución se canceló con salida
1 para no mantener una sesión sin progreso.

## Evidencia concreta

- Gate bloqueada: backup semanal, antes de validación de manifest, restore,
  health y headers.
- Proceso: `docker compose ... exec -T db pg_dump --format=custom`.
- Resultado observado: no apareció `weekly-*.manifest.json` en el backup root
  temporal; el proceso no devolvió código durante las esperas sucesivas.
- Acción: cancelación controlada de la misma ejecución; no se inició una segunda
  gate.
- La evidencia generada por un intento anterior contenía valores efímeros en la
  tabla de comandos. Se eliminó y se corrigió el script para redactar cualquier
  argumento `PASSWORD`, `SECRET`, `TOKEN` o `KEY` antes de generar documentos.

## Pendiente para continuar

1. Investigar por qué `pg_dump` no completa en el contenedor `db`, sin imprimir
   credenciales, dumps ni logs brutos.
2. Reejecutar la gate completa desde el principio y conservar solo estado
   resumido, manifest y signoff sin secretos.
3. No usar `Closes #70` hasta que todos los gates pasen.
