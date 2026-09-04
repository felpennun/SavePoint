---
phase: 01-three-day-public-demo-slice
plan: 13
subsystem: documentation
tags: [adr, provenance, agent-ledger, sha256, powershell]
requires:
  - phase: 01-11
    provides: offline reproducibility, deployment checks and secret scanner evidence
provides:
  - five sourced and reversible Phase 1 architecture decision records
  - append-only typed agent activity/evidence ledger
  - fail-first evidence checker for schema, attribution, paths, hashes and secrets
affects: [thesis, methodology, data-governance, phase-verification]
actuals:
  tokens: 7635
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [sourced ADRs, typed append-only JSONL, fail-first evidence validation]
key-files:
  created:
    - docs/adr/ADR-001-architecture.md
    - docs/adr/ADR-002-postgresql.md
    - docs/adr/ADR-003-data-sources.md
    - docs/adr/ADR-004-session-boundary.md
    - docs/adr/ADR-005-deployment-parity.md
    - docs/methodology/agent-ledger.jsonl
    - docs/methodology/agent-method.md
    - scripts/check-evidence.ps1
  modified: []
key-decisions:
  - "La evidencia separa estrictamente proposal, automated-check y author-decision; sólo el actor humano puede emitir esta última."
  - "Los hashes y rutas reproducen artefactos redistribuibles sin conservar conversaciones completas ni secretos."
  - "Los cinco ADR cubren las decisiones materiales identificadas de Phase 1, sujetos a confirmación final del autor/tutor."
patterns-established:
  - "ADRs: contexto, alternativas, decisión, evidencia/fuentes, consecuencias, reversibilidad y aprobación."
  - "Ledger: una entrada JSON por línea, UTC, actor separado, tipo exacto y SHA-256 de artefactos."
requirements-completed: [DATA-01, DATA-02, DOC-01, AGENT-01, AGENT-02, AGENT-03]
coverage:
  - id: D1
    description: "Cinco ADR justifican arquitectura, PostgreSQL, fuentes/media, sesión y despliegue con alternativas y reversibilidad."
    requirement: DOC-01
    verification:
      - kind: other
        ref: "powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1 -ADRs"
        status: pass
    human_judgment: true
    rationale: "El checker valida estructura y fuentes, pero el autor debe confirmar que no falta una decisión material."
  - id: D2
    description: "El ledger tipado enlaza investigación, UI, planificación, ejecución, fallos, correcciones y decisiones humanas."
    requirement: AGENT-03
    verification:
      - kind: other
        ref: "powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1"
        status: pass
    human_judgment: true
    rationale: "La suficiencia del formato de atribución depende de la política académica y revisión del autor/tutor."
  - id: D3
    description: "El checker demuestra fail-first para tipo/hash y valida no vacuamente rutas, hashes, autoría y patrones de secretos."
    requirement: AGENT-02
    verification:
      - kind: other
        ref: "scripts/check-evidence.ps1: canaries inválidos y 10 entradas reales PASS"
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-09-04
status: complete
---

# Phase 01 Plan 13: Evidencia de arquitectura y metodología de agentes

**Cinco ADR citables y un ledger agentic tipado quedan protegidos por un gate fail-first que verifica autoría, rutas, SHA-256 y exposición de secretos.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-09-04T20:00:00Z (aprox.)
- **Completed:** 2026-09-04T20:18:00Z (aprox.)
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Documenté las cinco decisiones materiales de Phase 1 distinguiendo evidencia del repositorio, fuentes externas, supuestos, consecuencias, reversibilidad y autor de la decisión.
- Creé un método de atribución honesto y un ledger JSONL con investigación, UI, planificación, ejecución, un fallo real, su corrección y decisiones humanas separadas.
- Implementé un checker no vacuo que rechaza primero canaries de tipo y hash inválidos, después verifica el ledger real y escanea evidencia por patrones de secretos.

## Task Commits

1. **Task 1: Escribir ADRs verificables de Phase 1** - `d7e3c8d` (docs)
2. **Task 2: Registrar metodología técnica de agentes y autoría** - `ca146f7` (docs)

## Files Created/Modified

- `docs/adr/ADR-001-architecture.md` a `ADR-005-deployment-parity.md` - decisiones de arquitectura, datos, seguridad y operación.
- `docs/methodology/agent-method.md` - protocolo, roles, responsabilidad, privacidad y limitaciones.
- `docs/methodology/agent-ledger.jsonl` - diez eventos tipados y enlazados por hash.
- `scripts/check-evidence.ps1` - gate estructural, criptográfico y de secretos con autocanaries.

## Decisions Made

- Ningún PASS automático se presenta como revisión independiente ni decisión del autor.
- Cuando el runtime no expone una versión exacta de modelo se registra la familia disponible y la limitación, sin inventar metadata.
- Las conversaciones completas y valores de entorno quedan fuera del ledger; se conservan artefactos redistribuibles, comandos sanitizados y hashes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] El verificador de Task 1 estaba asignado como artefacto de Task 2**
- **Found during:** Task 1
- **Issue:** `check-evidence.ps1` no existía, pero el verify obligatorio de Task 1 exigía ejecutarlo con `-ADRs`.
- **Fix:** Se creó primero el modo ADR no vacuo junto a Task 1 y se amplió con ledger/canaries en Task 2.
- **Files modified:** `scripts/check-evidence.ps1`
- **Verification:** el modo `-ADRs` reportó 5 ADR completos; el modo integral reportó 10 entradas válidas.
- **Committed in:** `d7e3c8d`, ampliado en `ca146f7`

---

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** necesario para ejecutar el gate en el orden del plan, sin ampliar el alcance final.

## Issues Encountered

- El primer patrón PowerShell para detectar el campo de autor no manejó de forma portable el carácter acentuado; se sustituyó por una comprobación de prefijo estable antes del primer commit.

## Known Stubs

None. Las menciones a `placeholder` describen la política deliberada de assets sin licencia completa, no una implementación pendiente.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DATA-01/02 y DOC-01 disponen de racional y evidencia contemporánea enlazada.
- AGENT-01..03 quedan implementados técnicamente; el autor/tutor debe confirmar que el formato satisface la política académica del TFG.
- La elección/alta de PaaS sigue correctamente separada como checkpoint humano y no se atribuye al agente.

## Self-Check: PASSED

- Los ocho artefactos declarados existen.
- Los commits `d7e3c8d` y `ca146f7` existen.
- El checker integral termina con código 0.

---
*Phase: 01-three-day-public-demo-slice*
*Completed: 2026-09-04*
