---
tags: [concepto, tema/arquitectura, tema/datos]
---

# PostgreSQL

PostgreSQL 18.6 es la unica base de datos de aplicacion y de pruebas de
integracion. Modela obras, ediciones, copias, estados, valoraciones, listas y
procedencia con integridad relacional; aporta JSONB y busqueda (`pg_trgm`) sin
anadir otro datastore. Imagen local fijada por tag y digest; un test centinela
rechaza otra base o version. Nunca SQLite en produccion ni en tests de
integracion.

## Enlaces

- [[Monolito modular Django]] · [[Busqueda tolerante]] · [[Paridad de despliegue]]
- [[ADR-002 - PostgreSQL canonico]]
