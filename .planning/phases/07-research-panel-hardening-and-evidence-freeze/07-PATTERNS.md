---
phase: 07-research-panel-hardening-and-evidence-freeze
source: local-codebase
mapped: 2026-09-13
---

# Patrones reutilizables

| Área | Patrón existente | Aplicación en Fase 7 |
|---|---|---|
| API | Servicios Django + vistas DRF + serializers manuales | Mantener reglas de permiso y proyección fuera de la UI |
| Persistencia | PostgreSQL, migraciones y constraints | Sentinel de esquema, índices, hashes y restauración |
| Frontend | Next.js SSR, DTOs normalizados, `apiFetch` y CSRF | Panel de investigación y administración sin duplicar autoridad |
| Experimentos | Protocolo JSON, snapshots y artefactos versionados | Solo lectura, comparación reproducible y exportación trazable |
| Seguridad | Checks de secretos/dependencias, 404 genérico y allowlists | Hardening, auditoría, SSRF/redirect, XSS/CSRF y headers |
| Calidad | pytest/pytest-django, Vitest/TypeScript, Playwright/axe | Gates por wave y verificación final con limitaciones explícitas |
| Evidencia | `docs/verification/`, vault vivo y commits con issue | Firma de requisitos, hashes, costes, amenazas y contribución |
