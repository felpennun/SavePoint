---
tipo: fase
fase: 7
fecha: 2026-09-13
fuentes:
  - "[[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-CONTEXT.md]]"
  - "[[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-RESEARCH.md]]"
  - "[[.planning/ROADMAP.md]]"
---

# Fase 7 — Panel de investigación y hardening

La planificación divide la fase en tres waves: contrato y límites de evidencia; API,
administración y seguridad; UI accesible, operaciones y firma final. La fase debe leer
artefactos congelados y no relanzar el split de evaluación consumido.

## Decisiones registradas

- PostgreSQL, Django/DRF, Compose y los artefactos versionados siguen siendo la base; no
  se añade infraestructura nueva sin evidencia de necesidad.
- La autoridad de permisos permanece en backend y los DTOs se construyen por allowlist.
- Backups, import/export y logs se prueban con checksums, límites, rutas seguras y scans de
  secretos antes de incorporarlos a la evidencia de tesis.

## Siguiente acción

Ejecutar `07-00-PLAN.md` tras revisar los seis planes y sus issues #65–#70.

## Contrato UI — 2026-09-14

El contrato visual canónico del panel está en
`[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-UI-SPEC.md]`.
Mantiene el sistema manual de tokens, define `/[locale]/research` como superficie privada
de lectura/exportación y exige que cada gráfico SVG tenga una tabla semántica equivalente.
La visibilidad del enlace Research depende de una capacidad server-side, no de la mera
presencia de sesión; `Platform Admin` continúa separado en Django Admin. No se añaden
dependencias de gráficos, servicios ni costes recurrentes.
