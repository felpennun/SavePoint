# Multi-Source Coverage Audit — Phase 01

Auditoría regenerada contra los 16 planes actuales. Cada referencia apunta a una tarea o contrato real; no se incluyen ideas expresamente diferidas.

## Goal

| ID | Feature/constraint | Plan/task | Status |
|---|---|---|---|
| GOAL-01 | Demo pública lawful y reproducible offline en tres días | 01-04 T1–T2, 01-09 T1–T2, 01-11 T1–T2, 01-12 T1–T2, 01-14 T1 | COVERED |

## Requirements (23/23)

| ID | Plan/task | Status |
|---|---|---|
| AUTH-01 | 01-15 T1–T2; 01-04 T2; 01-09 T1 | COVERED |
| PROF-02 | 01-07 T2; 01-09 T2 | COVERED |
| CAT-01 | 01-06 T2; 01-09 T1 | COVERED |
| CAT-03 | 01-05 T1–T2; 01-06 T1; 01-09 T1–T2 | COVERED |
| CAT-04 | 01-03 T1; 01-06 T1; 01-04 T1 | COVERED |
| CAT-06 | 01-06 T1–T2; 01-09 T1 | COVERED |
| LIB-01 | 01-04 T1; 01-09 T1; 01-16 T1–T2 | COVERED |
| LIB-02 | 01-07 T1; 01-09 T1; 01-16 T1–T2 | COVERED |
| INV-01 | 01-07 T1; 01-09 T1 | COVERED |
| INV-02 | 01-07 T1; 01-09 T1 | COVERED |
| INV-05 | 01-07 T2; 01-09 T2 | COVERED |
| DATA-01 | 01-05 T1–T2; 01-13 T1 | COVERED |
| DATA-02 | 01-05 T1–T2; 01-13 T1 | COVERED |
| REC-02 | 01-07 T3; 01-16 T1–T2; 01-09 T2 | COVERED |
| SEC-02 | 01-01 T1–T2; 01-02 T2; 01-15 T1–T2; 01-11 T2; 01-12 T1–T2 | COVERED |
| OPS-01 | 01-12 T1–T2; 01-14 T1 | COVERED |
| OPS-02 | 01-01 T1–T2; 01-02 T1; 01-03 T1–T2; 01-11 T1 | COVERED |
| OPS-03 | 01-15 T1; 01-16 T2; 01-11 T1; 01-12 T2 | COVERED |
| QUAL-03 | 01-02 T1–T2; 01-08 T1; 01-09 T1–T2; 01-10 T1; 01-14 T1 | COVERED |
| DOC-01 | 01-13 T1; 01-14 T1 | COVERED |
| AGENT-01 | 01-13 T2; 01-14 T1 | COVERED |
| AGENT-02 | 01-13 T2; 01-14 T1 | COVERED |
| AGENT-03 | 01-13 T2; 01-14 T1 | COVERED |

## Research constraints

| ID | Constraint | Plan/task | Status |
|---|---|---|---|
| RES-01 | Django/DRF + Next + PostgreSQL y sesión/CSRF same-origin | 01-01 T1–T2; 01-02 T1; 01-03 T1–T2; 01-04 T1–T2 | COVERED |
| RES-02 | Snapshot Wikidata CC0 y media Commons por archivo | 01-05 T1–T2; 01-06 T1 | COVERED |
| RES-03 | Sin API runtime; import atómico/idempotente | 01-06 T1–T2; 01-11 T1 | COVERED |
| RES-04 | Cuenta/credencial runtime separadas de interacciones | 01-15 T1–T2; 01-16 T1–T2 | COVERED |
| RES-05 | Baseline versionado antes de superficies públicas | 01-07 T3; 01-16 T1–T2; dependencia 01-09→01-16 | COVERED |
| RES-06 | Render/Compose parity, secret gate y PostgreSQL/E2E | 01-02 T1–T2; 01-11 T1–T2; 01-12 T1–T2 | COVERED |

## Context decisions (20/20)

| ID | Decision | Plan/task | Status |
|---|---|---|---|
| D-01 | Portada realista | 01-08 T1; 01-09 T1 | COVERED |
| D-02 | Login convencional y acceso demo visible | 01-15 T1–T2; 01-04 T2 | COVERED |
| D-03 | Catálogo tras login | 01-15 T2; 01-04 T2 | COVERED |
| D-04 | Sin tour; guion separado | 01-08 T1; 01-09 T1 | COVERED |
| D-05 | Corpus inicial 100–300 | 01-05 T1–T2 | COVERED |
| D-06 | Representación de eras/géneros/plataformas | 01-05 T1–T2 | COVERED |
| D-07 | Máximo de carátulas lawful; placeholder propio | 01-05 T1–T2; 01-09 T1 | COVERED |
| D-08 | Procedencia por ficha y página global | 01-05 T1–T2; 01-06 T1; 01-09 T2 | COVERED |
| D-09 | Obra→release/plataforma→edición→copia | 01-03 T1; 01-06 T1; 01-04 T1 | COVERED |
| D-10 | ES/EN por usuario con fallback y aliases | 01-05 T1; 01-06 T2; 01-08 T1 | COVERED |
| D-11 | DLC hijo, no backlog independiente | 01-05 T1; 01-06 T1 | COVERED |
| D-12 | Búsqueda tolerante | 01-05 T1; 01-06 T2 | COVERED |
| D-13 | Cinco estrellas en medios pasos | 01-07 T1; 01-09 T1 | COVERED |
| D-14 | Estado actual e historial fechado | 01-04 T1 | COVERED |
| D-15 | Copia corta: formato/plataforma/edición | 01-07 T1; 01-09 T1 | COVERED |
| D-16 | Rating/status a nivel de obra; copias separadas | 01-07 T1; 01-09 T1 | COVERED |
| D-17 | Estilo oscuro cover-led | 01-08 T1 | COVERED |
| D-18 | Tokens semánticos provisionales | 01-08 T1 | COVERED |
| D-19 | Grid adaptativo y acciones no hover-only | 01-08 T1; 01-09 T1 | COVERED |
| D-20 | Navegación superior desktop/menú móvil | 01-08 T1 | COVERED |

## Architecture and deployment ranges

- Arquitectura/tracer y dominio: 01-01–01-04, 01-06–01-08, con bootstrap temprano 01-15 y seed posterior al esquema 01-16.
- Superficies y aceptación: 01-09–01-10 y 01-14.
- Runtime, seguridad y despliegue: 01-11–01-12; Compose ordena migrate→import→bootstrap→interacciones.
- Evidencia de tesis y agentes: 01-13–01-14.

Los 29 elementos del probe sin SPEC permanecen resueltos como criterios o `FLAGGED ASSUMPTION`; las prohibiciones bespoke siguen descriptor-less y pendientes de juicio humano. Los controles OWASP canónicos se remiten a los threat models y al posterior `$gsd-secure-phase`, sin duplicarlos como prohibiciones.
