---
tags: [adr, tema/arquitectura, tema/datos]
---

# ADR-002 - PostgreSQL canonico

**Estado:** aceptada para Fase 1. Fuente: `docs/adr/ADR-002-postgresql.md`.

Decision: PostgreSQL 18.6 es la unica base de datos de aplicacion y de pruebas de
integracion. Django ORM/migraciones son la interfaz; constraints y transacciones
viven tambien en la base. La imagen local esta fijada por tag y digest, y un test
centinela rechaza otra base o version.

Alternativas descartadas: SQLite local/pruebas (difiere en tipos, constraints,
concurrencia y busqueda), MongoDB (flexibilidad documental a costa de integridad
relacional).

## Enlaces

- [[PostgreSQL]] · [[Reproducibilidad academica]]
- [[ADR-001 - Monolito modular Django + Next.js]]
- [[Fase 1 - Demo publico de tres dias]]
