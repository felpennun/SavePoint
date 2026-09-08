---
tags: [adr, tema/arquitectura, tema/seguridad]
---

# ADR-004 - Sesion Django same-origin

**Estado:** aceptada para la demo controlada. Fuente: `docs/adr/ADR-004-session-boundary.md`.

Decision: Django emite y valida la sesion; el navegador solo llama rutas
same-origin de Next.js, que las reescribe al API. Las mutaciones requieren token
CSRF, las cookies van con `credentials: same-origin`, el logout invalida la
sesion y los redirects solo aceptan paths relativos.

Alternativas descartadas: JWT en almacenamiento del navegador (amplia emision,
rotacion, revocacion y riesgo XSS), CORS con credenciales entre origenes, OIDC
externo (excesivo para cuentas sinteticas controladas).

## Enlaces

- [[Frontera de sesion same-origin]] · [[Frontend Next.js]] · [[Monolito modular Django]]
- [[Fase 1 - Demo publico de tres dias]]
