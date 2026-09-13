# Auditoría de cobertura de fuentes — Fase 6

Esta auditoría se realizó antes de cerrar los planes y cubre las cuatro fuentes obligatorias. No se consideran huecos las ideas diferidas de `06-CONTEXT.md`, ni el trabajo que pertenece a otras fases.

| Fuente | Elemento de alcance | Cobertura planificada | Estado |
|---|---|---|---|
| GOAL | Public Discovery and Resilient Enrichment ampliado con módulo social completo | `06-00` reconciliación; `06-01` relaciones; `06-02` catálogo/enriquecimiento; `06-03` privacidad/mensajes; `06-04` UI; `06-05` evidencia | Cubierto |
| REQ | `PROF-03` | `06-00` rebaseline trazable; `06-03` DTO/políticas; `06-04` perfiles; `06-05` regresión y signoff | Cubierto |
| REQ | `PROF-04` | `06-00` alcance; `06-03` autorización de URLs y 404 genérico; `06-04` rutas directas; `06-05` E2E/IDOR | Cubierto |
| REQ | `CAT-05` | `06-00` preservación en Fase 6; `06-02` backend/facets/enriquecimiento local; `06-04` UI; `06-05` evidencia | Cubierto |
| REQ | `SOCIAL-03` [ASSUMED] | `06-01` persistencia y transiciones; `06-04` módulo social; `06-05` E2E | Cubierto |
| REQ | `SOCIAL-04` [ASSUMED] | `06-03` perfiles, colecciones, listas, comentarios y autorización; `06-04` UI; `06-05` E2E | Cubierto |
| REQ | `SOCIAL-05` [ASSUMED] | `06-03` recomendaciones, inbox, lectura y cooldown; `06-04` badge/página; `06-05` E2E/evidencia | Cubierto |
| RESEARCH | Django/DRF modular monolith, PostgreSQL, servicios y políticas server-side | `06-01` y `06-03`, con migraciones y pruebas PostgreSQL obligatorias | Cubierto |
| RESEARCH | CAT-05 necesita contrato de facets para dimensiones locales disponibles, incluida editorial si falta | `06-02` modelos, consulta allowlisted, migración aditiva y pruebas de contrato | Cubierto |
| RESEARCH | Enriquecimiento reproducible, local, idempotente, con procedencia; sin API live en HTTP | `06-02` importador/snapshot; `06-05` hashes y evidencia de no contaminación | Cubierto |
| RESEARCH | Next.js responsive/accessibility, contratos tipados, i18n y E2E | `06-04` frontend; `06-05` Playwright, axe, teclado y viewport | Cubierto |
| CONTEXT | D-01 CAT-05 completo y selección visual abierta | `06-00`, `06-02`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-02 búsquedas GET compartibles | `06-02`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-03 amistad bidireccional, solicitud/aceptación y alias exacto | `06-01`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-04 módulo social y acciones diferenciadas | `06-01`, `06-03`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-05 rechazo/eliminación/bloqueo con semántica distinta | `06-01`, `06-03`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-06..D-08 privacidad, autorización server-side y 404 indistinguible | `06-03`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-09..D-12 allowlists de colección/listas/comentarios y ausencia de estadísticas/privados | `06-03`, `06-04`, `06-05` | Cubierto |
| CONTEXT | D-13..D-15 recomendación privada, inbox/badge y cooldown de 7 días | `06-03`, `06-04`, `06-05` | Cubierto |

## Resultado

No hay elementos GOAL, REQ, RESEARCH o CONTEXT sin plan. `SOCIAL-03`, `SOCIAL-04` y `SOCIAL-05` son IDs de reconciliación propuestos como `[ASSUMED]`; `06-00` exige confirmarlos mediante el mecanismo GSD antes de ejecutar la implementación. Las decisiones D-01..D-15 permanecen obligatorias y se citan en las acciones de los planes.
