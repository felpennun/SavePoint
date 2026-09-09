---
quick_task: bootstrap-existing-recommendation-snapshots
created: 2026-09-09
status: complete
---

# Inicialización de snapshots existentes

## Objetivo

Permitir que las colecciones creadas antes del worker reciban su primer snapshot sin editar la
colección ni ejecutar manualmente una operación por usuario.

## Decisión

Añadir un comando idempotente que cree la revisión inicial cuando existe actividad de biblioteca
o copias propias y encole el refresco en PostgreSQL. El worker conserva el cálculo fuera de las
peticiones web.
