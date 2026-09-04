---
phase: 01-three-day-public-demo-slice
plan: 01
subsystem: supply-chain
tags: [nextjs, pnpm, uv, lockfiles, dependency-audit, reproducibility]
requires: []
provides:
  - Human-approved dependency baseline with official-source evidence
  - Exact npm and Python manifests and transitive lockfiles
  - Fail-closed allowlist checker and negative controls
affects: [all-phase-01-plans, frontend, backend, ci, thesis-evidence]
actuals:
  tokens: 21504
  tasks: 2
  commits: 2
tech-stack:
  added: [Node.js 24.13.0, pnpm 11.25.0, Next.js 16.3.4, React 19.2.7, Python 3.13, uv 0.12.9, Django 5.2.17 LTS, DRF 3.18.0]
  patterns: [exact direct pins, generated transitive locks, official registry verification, fail-first dependency allowlist]
key-files:
  created: [package.json, pnpm-workspace.yaml, pnpm-lock.yaml, pyproject.toml, uv.lock, scripts/check-dependencies.ps1]
  modified: [docs/verification/dependency-legitimacy.md]
key-decisions:
  - "Next.js queda fijado a 16.3.4, la versión estable parcheada más próxima autorizada, porque 16.2.12 no superó el umbral de vulnerabilidades altas."
  - "Toda dependencia directa debe tener versión exacta, evidencia oficial y nueva aprobación humana antes de incorporarse."
patterns-established:
  - "Supply-chain gate: manifests exactos, locks generados, auditoría y controles negativos antes de implementar."
requirements-completed: [SEC-02, OPS-02]
coverage:
  - id: D1
    description: "Conjunto de dependencias e imágenes aprobado por el autor y documentado con razones y fuentes oficiales."
    requirement: SEC-02
    verification:
      - kind: manual_procedural
        ref: "Autorizaciones humanas registradas en docs/verification/dependency-legitimacy.md"
        status: pass
    human_judgment: true
    rationale: "La aceptación de dependencias y del cambio de versión es una decisión explícita del autor del TFG."
  - id: D2
    description: "Locks exactos y allowlist fail-closed sin vulnerabilidades conocidas en el árbol npm."
    requirement: OPS-02
    verification:
      - kind: other
        ref: "powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1"
        status: pass
      - kind: other
        ref: "corepack pnpm audit --audit-level high --json"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 01: Dependency Legitimacy and Locks Summary

**Baseline reproducible de dependencias con Next.js 16.3.4, locks exactos, auditoría sin vulnerabilidades y checker fail-closed.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-04T13:15:00Z
- **Completed:** 2026-09-04T13:40:34Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Se registraron la aprobación humana, la procedencia oficial y la justificación académica de cada tecnología.
- Se fijaron dependencias directas y transitivas para Node 24/pnpm y Python 3.13/uv.
- Se sustituyó el lock vulnerable de Next.js 16.2.12 por 16.3.4: la auditoría final registra cero vulnerabilidades en todas las severidades.
- El checker valida manifests, locks y digests OCI, rechaza versiones flotantes y falla ante un canary no aprobado.

## Task Commits

1. **Task 1: Aprobar legitimidad y compatibilidad de dependencias** — `90e86f4`
2. **Task 2: Resolver locks exclusivamente desde la aprobación** — `b76ab2c`

## Files Created/Modified

- `package.json` y `pnpm-workspace.yaml` — runtime, gestor y dependencias npm exactas.
- `pnpm-lock.yaml` — resolución transitiva npm íntegra y auditable.
- `pyproject.toml` y `uv.lock` — contrato Python 3.13 y resolución PyPI exacta.
- `scripts/check-dependencies.ps1` — allowlist, pins, locks, digests y controles negativos.
- `docs/verification/dependency-legitimacy.md` — fuentes, alternativas, riesgos, autorizaciones y resultado de auditoría para la tesis.

## Decisions Made

- Next.js 16.3.4 conserva el major y la arquitectura aprobados, evita prereleases y elimina el árbol vulnerable observado en 16.2.12.
- No se permiten rangos, `latest`, overrides silenciosos ni nuevas dependencias sin repetir el gate.

## Deviations from Plan

### Human-authorized security correction

- **Found during:** Task 2
- **Issue:** `next@16.2.12` resolvía un árbol con tres vulnerabilidades altas y dos moderadas.
- **Resolution:** se detuvo el plan, el autor autorizó expresamente 16.3.4, se regeneró el lock sin scripts y se repitió la auditoría.
- **Verification:** `pnpm audit` final: 0 critical, high, moderate, low e info; checker normal 0 y canary 1.
- **Committed in:** `b76ab2c`

**Total deviations:** 1 corrección de seguridad autorizada. **Impact:** mismo major y arquitectura; superficie de riesgo reducida sin ampliar dependencias directas.

## Issues Encountered

- Docker Desktop no estaba activo durante la comprobación final. No afecta a los locks ya generados y verificados estructuralmente; la instalación congelada dentro de las imágenes fijadas se volverá a comprobar cuando los Dockerfiles se creen en los planes posteriores.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Los planes posteriores pueden consumir únicamente estas versiones con instalación congelada.
- Cualquier paquete directo nuevo o cambio de versión reabre el gate humano.

## Self-Check: PASSED

- Los siete artefactos declarados existen.
- Los commits `90e86f4` y `b76ab2c` existen en el historial.
- Checker normal, controles de versión flotante, canary negativo, lock congelado y auditoría npm pasaron.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
