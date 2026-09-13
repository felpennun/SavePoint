---
fecha: 2026-09-14
estado: vigente
fuente: [[../../docs/verification/phase-07-research-api.md]]
---

# API protegida del panel de investigación

## Qué ha cambiado

La API Django de Fase 7 publica el snapshot de evaluación v15 mediante cuatro rutas
GET allowlisted: runs, comparison, artifacts y exports. `Research Viewer` se resuelve
con `has_perm("evaluation.view_research_panel")`; una cuenta autenticada sin ese
permiso recibe 404 neutro y una sesión ausente sigue el flujo de autenticación.

## Impacto

Las capacidades de investigación y administración permanecen separadas. Las filas,
timings, hashes y exportaciones proceden del contrato inmutable de 07-00; no hay
re-run, mutación ni cálculo de métricas en el cliente. Los filtros y formatos no
allowlisted fallan cerrado y las descargas no exponen `per_user`, logs, dumps ni
secretos.

## Enlaces relacionados

- [[../Conceptos/Panel de investigacion]]
- [[../../.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-01-PLAN.md]]
- [[../../.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-00-SUMMARY.md]]
