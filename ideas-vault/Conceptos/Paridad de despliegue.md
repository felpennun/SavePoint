---
tags: [concepto, tema/arquitectura]
---

# Paridad de despliegue

Doble entrega: Compose local construye `web` y `api` desde Dockerfiles con
PostgreSQL y healthchecks (OPS-02), y una demo publica de coste cero usa Vercel
Hobby + Render Free + Neon Free (OPS-01), con equivalencia funcional, de
versiones, commit y datos. Modo demo offline lawful sin API ni Internet (OPS-03).
Compose es el fallback canonico.

## Enlaces

- [[PostgreSQL]] · [[Contenedores y CI]] · [[Reproducibilidad academica]]
- [[ADR-005 - Paridad de despliegue gratuito]]
