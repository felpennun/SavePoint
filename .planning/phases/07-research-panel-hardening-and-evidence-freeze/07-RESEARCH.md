---
phase: 07-research-panel-hardening-and-evidence-freeze
source: local-codebase-and-phase-06-evidence
researched: 2026-09-13
---

# Investigación local de la Fase 7

## Hallazgos

- Django/DRF y PostgreSQL son la frontera transaccional existente; las reglas de autorización y los DTOs allowlisted deben permanecer en servicios/API.
- La evaluación offline ya tiene protocolo, snapshots, artefactos y resultados congelados. El panel debe leer metadatos y artefactos versionados, no recalcular ni mutar el split `test`.
- Compose ya separa `web`, `api`, `db` y workers. La fase debe aprovechar comandos explícitos y no introducir una cola o datastore nuevo sin benchmark.
- El frontend Next.js usa Server Components para lecturas y `apiFetch`/CSRF para mutaciones; el panel debe seguir el mismo patrón y generar exportaciones desde contratos tipados.
- Fase 6 deja como gates reutilizables PostgreSQL, migraciones, `check-dependencies.ps1`, `check-secrets.ps1`, TypeScript, Vitest, Playwright y axe.

## Riesgos

- Exponer artefactos o endpoints administrativos sin autorización produce IDOR o fuga de credenciales.
- Recalcular resultados desde datos vivos rompe reproducibilidad y contamina la evidencia.
- Import/export y backups pueden aceptar rutas, URLs o archivos no confiables; requieren allowlists, límites, checksum y pruebas de restauración.
- Logs, errores y capturas pueden incluir secretos; deben escanearse antes de documentarse.

## Estrategia

Construir primero contratos de lectura y sentinel de inmutabilidad; después permisos/hardening y operaciones; luego panel accesible/exportaciones; finalmente backups, auditoría y firma reproducible. Cada wave debe dejar tests y evidencia no sensible.

## Límites de investigación

No se añade ML nuevo, no se relanza la evaluación consumida, no se cambia el corpus congelado y no se selecciona proveedor de despliegue sin evidencia actual de coste/backup/portabilidad.
