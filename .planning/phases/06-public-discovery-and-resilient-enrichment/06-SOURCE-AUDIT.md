# Auditoría de cobertura de fuentes — Fase 6

Esta auditoría se realizó antes de cerrar los planes y cubre las cuatro fuentes obligatorias. No se consideran huecos las ideas diferidas de `06-CONTEXT.md`, ni el trabajo que pertenece a otras fases.

| Fuente | Elemento de alcance | Cobertura planificada | Estado |
|---|---|---|---|
| GOAL | Public Discovery and Resilient Enrichment ampliado con módulo social completo | `06-00` reconciliación; `06-01` relaciones; `06-02` catálogo/enriquecimiento; `06-03` perfil/proyecciones; `06-04` comentarios/mensajes backend; `06-05` descubrimiento web; `06-06` perfiles/amistades web; `06-07` inbox web; `06-08` ficha/i18n web; `06-09` evidencia | Cubierto |
| REQ | `PROF-03` | `06-00` rebaseline trazable; `06-03` DTO/políticas y perfil básico separado; `06-04` comentarios autorizados; `06-06` perfiles web; `06-08` ficha; `06-09` regresión y signoff | Cubierto |
| REQ | `PROF-04` | `06-00` alcance; `06-03` autorización de URLs y 404 genérico; `06-06` rutas directas; `06-09` E2E/IDOR | Cubierto |
| REQ | `CAT-05` | `06-00` preservación en Fase 6; `06-02` backend/facets/enriquecimiento local; `06-05` UI; `06-09` evidencia | Cubierto |
| REQ | `SOCIAL-03` [ASSUMED] | `06-00` confirmación; `06-01` persistencia y transiciones; `06-06` módulo social; `06-09` E2E | Cubierto |
| REQ | `SOCIAL-04` [ASSUMED] | `06-00` confirmación; `06-03` perfiles, colecciones, listas y autorización; `06-04` comentarios; `06-06` UI; `06-08` ficha; `06-09` E2E | Cubierto |
| REQ | `SOCIAL-05` [ASSUMED] | `06-00` confirmación; `06-04` recomendaciones, inbox, lectura y cooldown; `06-07` badge/página; `06-09` E2E/evidencia | Cubierto |
| RESEARCH | Django/DRF modular monolith, PostgreSQL, servicios y políticas server-side | `06-01`, `06-02`, `06-03` y `06-04`, con migraciones serializadas y pruebas PostgreSQL obligatorias | Cubierto |
| RESEARCH | CAT-05 necesita contrato de facets para dimensiones locales disponibles, incluida editorial si falta | `06-02` modelos, consulta allowlisted, migración aditiva y pruebas de contrato; `06-05` contrato GET | Cubierto |
| RESEARCH | Enriquecimiento reproducible, local, idempotente, con procedencia; sin API live en HTTP | `06-02` importador/snapshot; `06-05` hashes y evidencia de no contaminación | Cubierto |
| RESEARCH | Next.js responsive/accessibility, contratos tipados, i18n y E2E | `06-05`..`06-08` frontend; `06-09` Playwright, axe, teclado y viewport | Cubierto |
| CONTEXT | D-01 CAT-05 completo y selección visual abierta | `06-00`, `06-02`, `06-05`, `06-09` | Cubierto |
| CONTEXT | D-02 búsquedas GET compartibles | `06-02`, `06-05`, `06-09` | Cubierto |
| CONTEXT | D-03 amistad bidireccional, solicitud/aceptación y alias exacto | `06-01`, `06-06`, `06-09` | Cubierto |
| CONTEXT | D-04 módulo social y acciones diferenciadas | `06-01`, `06-06`, `06-09` | Cubierto |
| CONTEXT | D-05 rechazo/eliminación/bloqueo con semántica distinta | `06-01`, `06-03`, `06-06`, `06-09` | Cubierto |
| CONTEXT | D-06..D-08 privacidad, autorización server-side y 404 indistinguible | `06-00`, `06-03`, `06-06`, `06-09` | Cubierto |
| CONTEXT | D-09..D-12 allowlists de colección/listas/comentarios y ausencia de estadísticas/privados | `06-00`, `06-03`, `06-04`, `06-06`, `06-08`, `06-09` | Cubierto |
| CONTEXT | D-13..D-15 recomendación privada, inbox/badge y cooldown de 7 días | `06-00`, `06-04`, `06-07`, `06-09` | Cubierto |

## Resultado

No hay elementos GOAL, REQ, RESEARCH o CONTEXT sin plan. `SOCIAL-03`, `SOCIAL-04` y `SOCIAL-05` quedan confirmados como decisiones de implementación `[ASSUMED]` en `06-RESEARCH.md` y `06-00`; `SOCIAL-01`/`SOCIAL-02` no se sustituyen. Las decisiones D-01..D-15 permanecen obligatorias y se citan en las acciones de los planes.
