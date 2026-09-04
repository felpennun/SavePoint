# ADR-002: PostgreSQL como ruta persistente canónica

- **Estado:** Aceptada para Phase 1
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe
- **Redacción/evidencia:** agente `gsd-executor`; propuesta asistida revisable.

## Contexto

Obras, ediciones, copias, estados, valoraciones y procedencia tienen relaciones, unicidad y transacciones que deben comportarse igual en desarrollo, pruebas y despliegue. [EVIDENCIA: `apps/api/catalogue/models.py`, `apps/api/library/models.py`]

## Alternativas consideradas

1. PostgreSQL 18.6 en todas las rutas.
2. SQLite local/pruebas: sencillo, pero difiere en tipos, constraints, concurrencia y búsqueda.
3. MongoDB: flexibilidad documental a costa de integridad relacional.
4. PostgreSQL 17: aceptable sólo si el proveedor gestionado no soporta 18; local y remoto deben conservar la misma major.

## Decisión

PostgreSQL 18.6 es la única base de datos de aplicación y pruebas de integración. Django ORM/migraciones son la interfaz; constraints y transacciones viven también en la base. La imagen local está fijada por tag y digest. [DECISIÓN HUMANA: `docs/verification/dependency-legitimacy.md`]

## Evidencia y fuentes

- `infra/compose.yaml` fija `postgres:18.6@sha256:4ef4...c2280` y healthcheck.
- `apps/api/tests/test_postgres_sentinel.py` rechaza otra base/versión.
- `apps/api/config/settings.py` rechaza esquemas distintos de PostgreSQL.
- [PostgreSQL releases](https://www.postgresql.org/docs/release/) y [pg_trgm](https://www.postgresql.org/docs/current/pgtrgm.html).

## Consecuencias

- Positivas: paridad, integridad relacional, locks y búsqueda disponibles de forma reproducible.
- Negativas: Docker/servidor requerido; backups y upgrades operativos; mayor coste que SQLite.
- Limitación: las pruebas actuales demuestran el slice, no carga ni recuperación ante desastre.

## Reversibilidad

Los dumps lógicos y migraciones permiten cambiar de patch o proveedor. Cambiar de motor exige ADR y suite completa porque no se presume portabilidad semántica del ORM.

## Aprobación y revisión

**Aprobada para Phase 1.** Revalidar soporte, backups, región y versión del proveedor antes del despliegue público.
