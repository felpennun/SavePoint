---
tipo: fase
fase: 7
fecha: 2026-09-13
estado: superada; conservar como nota histórica
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

## Estado final

La fase está completada y la nota canónica es [[Fase 7 - Panel de investigacion y hardening]].
La evidencia final, el gate y el signoff están en [[../../.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-VERIFICATION]],
[[../../docs/verification/phase-07-launch-gate]] y [[../../docs/verification/phase-07-signoff]].

## Contrato UI — 2026-09-14

El contrato visual canónico del panel está en
`[.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-UI-SPEC.md]`.
Mantiene el sistema manual de tokens, define `/[locale]/research` como superficie privada
de lectura/exportación y exige que cada gráfico SVG tenga una tabla semántica equivalente.
La visibilidad del enlace Research depende de una capacidad server-side, no de la mera
presencia de sesión; `Platform Admin` continúa separado en Django Admin. No se añaden
dependencias de gráficos, servicios ni costes recurrentes.

Esta nota conserva el contexto inicial de planificación; para el resultado ejecutado debe
consultarse la nota canónica y el resumen final de 07-05.
