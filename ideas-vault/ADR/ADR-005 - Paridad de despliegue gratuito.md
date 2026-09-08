---
tags: [adr, tema/arquitectura]
---

# ADR-005 - Paridad de despliegue gratuito

**Estado:** topologia aprobada; alta externa pendiente. Fuente:
`docs/adr/ADR-005-deployment-parity.md`.

Decision: Compose sigue construyendo `web` y `api` desde Dockerfiles y orquesta
PostgreSQL con healthchecks. La demo publica usa Vercel Hobby para Next.js,
Render Free para la imagen API y Neon Free para PostgreSQL, con proxy same-origin
de Vercel a Render. La equivalencia es funcional, de versiones, commit y datos.
Restriccion explicita del autor: coste cero, sin tarjeta, sin recursos de pago.

## Enlaces

- [[Paridad de despliegue]] · [[Contenedores y CI]] · [[PostgreSQL]]
- [[Fase 1 - Demo publico de tres dias]]
