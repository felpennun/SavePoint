---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 05
subsystem: release-verification
tags: [playwright, axe, evidence, backup, restore, launch-gate]
requires:
  - 07-03
  - 07-04
provides:
  - Browser-visible verification of research and admin journeys
  - Reproducible, aggregate-only v15 evidence package
  - Fail-closed launch gate with disposable recovery verification
affects:
  - QUAL-01
  - QUAL-04
  - DOC-05
  - DOC-06
  - AGENT-05
  - AGENT-06
  - OPS-04
  - OPS-05
  - SEC-07
tech-stack:
  added:
    - Standard-library PowerShell launch and evidence gates
  patterns:
    - Process-only demo credentials with redacted evidence
    - Minimal DB/API/web launch scope for release checks
    - Explicit PostgreSQL idle-session cleanup before recovery checks
key-files:
  created:
    - e2e/research-panel.spec.ts
    - e2e/admin-security.spec.ts
    - scripts/generate-phase-07-evidence.ps1
    - scripts/verify-phase-07-launch.ps1
    - docs/verification/phase-07-launch-gate.md
    - docs/verification/phase-07-signoff.md
  modified:
    - e2e/a11y.spec.ts
    - e2e/deployed-smoke.spec.ts
    - infra/compose.yaml
decisions:
  - La gate arranca solo DB/API/web; los workers no forman parte del recorrido de lanzamiento y agotaban el presupuesto local de conexiones.
  - El healthcheck web admite la latencia SSR observada del catálogo y usa 20 segundos.
  - La política de cabeceras comprueba las directivas obligatorias sin rechazar extensiones seguras como browsing-topics.
  - El backup y restore usan almacenamiento desechable; la evaluación v15 no se relanza ni se modifica.
metrics:
  browser_final: "56 passed, 0 failed, 0 skipped"
  backend_regression: "736 passed, 0 failed"
  frontend_regression: "70 passed, 0 failed"
  evidence_rows: 96
  launch_gate: PASS
  recovery: "weekly backup and disposable restore PASS"
completed: 2026-09-14
status: complete
---

# Fase 07 Plan 05: cierre de gate y evidencia

## Entregado

- Se verificaron los recorridos browser-visible de autenticación, Research Viewer,
  Platform Admin, filtros, comparación, exportaciones, estados, responsive,
  teclado, temas y axe en español e inglés.
- Se generó el paquete v15 desde snapshots existentes, con 96 filas agregadas,
  hashes, procedencia, limitaciones, contribuciones, referencias académicas y
  disclosure de IA. No contiene `per_user`, dumps, logs brutos ni secretos.
- Se implementó una gate única y fail-closed que cubre configuración Compose,
  migraciones, deploy checks, contratos/API/admin/portabilidad/operaciones,
  Vitest, TypeScript, Playwright/axe, secretos, dependencias, evidencia,
  backup, manifest, restore desechable, health, headers e integridad de fuentes.

## Verificación final

La ejecución final de `scripts/verify-phase-07-launch.ps1` terminó con:

```text
PASS: Phase 7 launch gate complete; all checks passed.
```

La ejecución no invocó `run_evaluation`, no recalculó métricas y confirmó que
los artefactos v15 permanecen invariantes. El dump temporal (~543 MB) y la base
de restore fueron desechables y se eliminaron al terminar la gate.

## Correcciones durante la gate

- Se amplió el timeout del healthcheck web porque el SSR local de `/es` tarda
  aproximadamente 15 segundos con el catálogo completo.
- Se limitó el arranque de la gate a DB/API/web y se añadió limpieza de sesiones
  idle más reinicio de API antes de backup/restore, evitando saturar las 100
  conexiones del PostgreSQL local.
- Se relajó la aserción de `Permissions-Policy` para exigir las directivas de
  cámara, micrófono y geolocalización sin rechazar directivas adicionales.
- Se corrigió la deriva histórica del hash fijado en el ledger siguiendo el
  procedimiento canónico de evidencia.

La regresion final queda verde con 736 tests backend contra PostgreSQL y 70
tests frontend. Tambien se alinearon dos tests heredados de perfiles y uno de
platinum con la proyeccion vigente de propietario, amistad aceptada y ficha
basica anonima.

## Limitaciones honestas

La evidencia v15 sigue siendo una simulación con población sintética, un único
run de test, 400 usuarios solicitados y 79 evaluables. La revisión visual final
del autor sobre reflow 320 px/400 %, adecuación legal y demostración académica
continúa siendo una responsabilidad humana; no se presenta como evidencia de
usuarios reales.

## Commits e integración

Los commits parciales mantienen `Refs #70`. El cierre de la issue #70 se hará
únicamente en el commit que integre este resumen, la gate y el signoff, después
de la verificación formal de fase.
