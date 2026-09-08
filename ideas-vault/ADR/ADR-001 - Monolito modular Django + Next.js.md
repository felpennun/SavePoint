---
tags: [adr, tema/arquitectura]
---

# ADR-001 - Monolito modular Django + Next.js

**Estado:** aceptada para Fase 1. Fuente: `docs/adr/ADR-001-architecture.md`.

Decision: monolito modular Django/DRF para identidad, reglas y persistencia, con
frontend Next.js/TypeScript. Modulos por dominio (`accounts`, `catalogue`,
`library`) que comparten despliegue y PostgreSQL. Los algoritmos futuros corren
como jobs explicitos, nunca dentro de peticiones HTTP.

Alternativas descartadas: FastAPI + SQLAlchemy (obliga a componer auth/admin/
migraciones), Django templates + HTMX (base menos natural para el panel
experimental), microservicios (coste operativo injustificado).

## Enlaces

- [[Monolito modular Django]] · [[Frontend Next.js]] · [[Jobs offline]]
- [[ADR-002 - PostgreSQL canonico]] · [[ADR-004 - Sesion Django same-origin]]
- [[Fase 1 - Demo publico de tres dias]]
