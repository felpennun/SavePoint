---
phase: 07-research-panel-hardening-and-evidence-freeze
verified: 2026-09-14T10:45:00Z
status: passed
score: 18/18 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
---

# Fase 07: Research Panel, Hardening, and Evidence Freeze — Verification

## Resultado

La fase supera la verificación goal-backward. El demostrador localizado presenta
la comparación publicada v15 mediante API y UI protegidas; la evidencia se
genera desde snapshots hash-pinned; y la gate de lanzamiento ejecuta backend,
frontend, browser/axe, seguridad, evidencia y recuperación sin recalcular la
evaluación.

La gate canónica terminó con:

```text
PASS: Phase 7 launch gate complete; all checks passed.
```

## Verdades verificadas

1. La comparación de runs, algoritmos, cohortes, métricas, tiempos y procedencia
   se sirve mediante DTOs allowlisted y se presenta en tabla, SVG y descargas
   equivalentes.
2. Research Viewer y Platform Admin son capacidades separadas; el admin Django
   permanece protegido y no se exponen acciones de re-run/delete en la UI.
3. Autenticación, autorización, XSS/CSRF, SSRF/redirect, rate limiting,
   cabeceras, errores, secretos, dependencias y auditoría pasan sus suites y
   checkers deterministas.
4. El backup semanal y el restore mensual desechable completan sus manifests,
   checksums, migraciones, conteos y health sin apuntar a la base canónica.
5. El paquete de evidencia v15 conserva corpus, protocolo, seeds, configuración,
   métricas, tiempos, hashes, procedencia, costes, limitaciones, referencias,
   contribuciones y disclosure de IA, sin `per_user`, dumps, logs brutos ni
   secretos.
6. Los recorridos Chromium/axe cubren español e inglés, autenticación, filtros,
   exportaciones, estados, responsive, teclado, temas y ausencia de acciones
   destructivas: 56 passed, 0 failed, 0 skipped.
7. La regeneración del paquete converge tras sincronizar el hash allowlisted de
   `infra/compose.yaml`; `check-evidence.ps1` y `git diff --check` pasan.
8. El objetivo MVP de la fase está expresado como User Story y la matriz de
   requisitos/ROADMAP queda alineada con los SUMMARY.

## Comprobaciones automatizadas

La gate ejecutó y aprobó configuración Compose, arranque DB/API/web, provisión
de roles, migraciones, `check --deploy`, contratos de evaluación, API, admin,
portabilidad y operaciones, Vitest, TypeScript, Playwright/axe Chromium,
`check-secrets.ps1`, `check-dependencies.ps1`, `check-security.ps1`,
`check-evidence.ps1`, contrato de manifest, backup semanal, validación del
manifest, restore desechable, health same-origin, headers seguros y snapshots
de integridad.

La suite backend de fase reportó 57 tests y la auditoría 3 tests; la suite
frontend reportó 70/70. La ejecución final no invocó `run_evaluation`, no
consumió ni modificó `apps/api/.evaluation-test-run.json` y no recalculó las
métricas publicadas.

La regresion posterior al cierre de la gate ejecuto la suite backend completa
contra PostgreSQL: 736 tests pasaron. La suite frontend completa quedo en
70 tests pasados desde `apps/web`, con la configuracion de Vitest y el alias
de imports correctos.

## Cobertura de requisitos

Quedan cubiertos por implementación, pruebas y/o gate: `EVAL-13`, `EVAL-14`,
`ADMIN-01`, `ADMIN-02`, `SEC-01`, `SEC-03`, `SEC-04`, `SEC-05`, `SEC-06`,
`SEC-07`, `SEC-08`, `PRIV-02`, `OPS-04`, `OPS-05`, `QUAL-01`, `QUAL-04`,
`DOC-05`, `DOC-06`, `AGENT-05`, `AGENT-06`, `PORT-02` y `PORT-03`.

## Limitaciones y revisión humana

El paquete v15 sigue representando una simulación con población sintética, un
único run de test, 400 usuarios solicitados y 79 evaluables. La revisión final
del autor sobre adecuación legal de redistribución, recorrido visual, reflow a
320 px y zoom 400 %, y aceptación académica del disclosure permanece como
revisión humana recomendada; no se presenta esa revisión como evidencia
automática ni como resultado de usuarios reales.

## Trazabilidad

- Contexto y decisiones: `07-CONTEXT.md`, `07-DISCUSSION-LOG.md` y `07-UI-SPEC.md`.
- Implementación y tareas: `07-00-SUMMARY.md` a `07-05-SUMMARY.md`.
- Evidencia: `docs/verification/phase-07-evidence-manifest.json` y salidas v15.
- Gate y firma: `docs/verification/phase-07-launch-gate.md` y
  `docs/verification/phase-07-signoff.md`.
- Metodología, referencias y uso de IA: `docs/methodology/phase-07-evidence-package.md`,
  `academic-reference-register.md` y `ai-use-disclosure.md`.

_Verificado: 2026-09-14._
_Verificador: gate determinista de la Fase 07 y revisión goal-backward._
