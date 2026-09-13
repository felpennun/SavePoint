---
phase: 07-research-panel-hardening-and-evidence-freeze
source: ROADMAP.md, REQUIREMENTS.md, Phase 06 verification
created: 2026-09-13
---

# Contexto de la Fase 7

## Alcance

La fase debe convertir el demostrador y los resultados de recomendación en un panel de
investigación reproducible, endurecer la operación y congelar la evidencia de tesis. Debe
mantener PostgreSQL como fuente transaccional, los artefactos offline inmutables y la
separación entre web, API y trabajos de investigación.

## Resultados esperados

- Panel accesible para comparar ejecuciones, algoritmos, cohortes, métricas, tiempos,
  parámetros, procedencia, limitaciones y exportaciones.
- Administración controlada de usuarios, catálogo, imports, jobs y experimentos, con
  eliminación/anominización y auditoría sin secretos.
- Hardening verificable de autorización, inyección, XSS/CSRF, SSRF/redirecciones,
  rate-limit, headers, errores, dependencias, secretos y pipeline.
- Backups y restauración probados para PostgreSQL y artefactos, con logs estructurados.
- Evidencia documental final reproducible, referencias canónicas, costes, limitaciones,
  amenazas de validez y contribución de agentes.

## Límites

No introducir microservicios, colas, almacenes nuevos ni entrenamiento dentro de HTTP sin
evidencia de necesidad. No relanzar el split de evaluación consumido ni modificar snapshots
congelados. Toda exposición administrativa debe ser autenticada, autorizada y auditable.

## Criterios heredados

La privacidad server-side, los DTOs allowlisted, el proxy same-origin, los checks de
dependencias/secretos, el contrato de PostgreSQL y la procedencia de Fase 6 son
precondiciones, no deben degradarse durante la fase.
