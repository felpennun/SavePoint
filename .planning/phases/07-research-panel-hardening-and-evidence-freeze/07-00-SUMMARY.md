---
phase: 07-research-panel-hardening-and-evidence-freeze
plan: 00
subsystem: api
tags: [django, evaluation, evidence, sha256, allowlist, exports]

requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: artefactos versionados, convenciones de privacidad y gates de evidencia
provides:
  - contrato de lectura inmutable para el artefacto de evaluación v15
  - DTOs allowlisted de ejecución, comparación, evidencia y exportación
  - pruebas de hashes, filtros, cohortes no evaluables y exclusión de datos privados
affects: [07-01, 07-03, 07-05, research-panel, thesis-evidence]

actuals:
  tokens: 11211
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - proyección manual desde snapshots JSON inmutables
    - dataclasses congeladas y allowlists de publicación
    - exportación backend con checksum y sin datos por usuario

key-files:
  created:
    - apps/api/evaluation/panel_contract.py
    - apps/api/evaluation/tests/test_phase7_contract.py
    - docs/verification/phase-07-evidence-contract.md
  modified:
    - ideas-vault/Conceptos/Panel de investigacion.md

key-decisions:
  - "La identidad histórica v15 declarada por el artefacto (versión, checksum, corpus, snapshots, split y semillas) es la autoridad de publicación; el protocol.json posterior solo aporta anclajes compartidos y nunca recalcula cifras."
  - "Las métricas catalogue_coverage, concentration_hhi y prediction_coverage se exponen como null por cohorte con explicación porque el snapshot las declara run-level-only."
  - "La configuración se proyecta por allowlist y el entorno histórico ausente permanece como null; no se sustituye por una medición posterior."

requirements-completed: [EVAL-13, EVAL-14, DOC-05, AGENT-05]

coverage:
  - id: D1
    description: "Loader inmutable que valida el artefacto v15, cohortes, protocolo y hashes antes de construir DTOs."
    requirement: EVAL-13
    verification:
      - kind: integration
        ref: "apps/api/evaluation/tests/test_phase7_contract.py#test_load_real_v15_publication_and_builds_sanitized_comparison"
        status: pass
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests -q (128 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Filtros, cohortes, métricas y formatos allowlisted, con filas ordenadas y valores null legítimos."
    requirement: EVAL-14
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_phase7_contract.py -k allowlist or cohort or export or immutable (11 passed, 5 deselected)"
        status: pass
      - kind: unit
        ref: "apps/api/evaluation/tests/test_phase7_contract.py#test_exports_are_allowlisted_and_contain_only_public_rows[json]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Contrato de evidencia documentado con mapeo de campos, SHA-256, limitaciones y trazabilidad de requisitos."
    requirement: DOC-05
    verification:
      - kind: other
        ref: "git diff --check"
        status: pass
      - kind: other
        ref: "Select-String docs/verification/phase-07-evidence-contract.md EVAL-13 EVAL-14 DOC-05 AGENT-05 SHA-256 protocol corpus limitation"
        status: pass
    human_judgment: false
  - id: D4
    description: "Procedencia de trabajo asistido y limitaciones de reproducibilidad registradas en el contrato y el vault vivo."
    requirement: AGENT-05
    verification:
      - kind: other
        ref: "docs/verification/phase-07-evidence-contract.md#Responsabilidad y revisión"
        status: pass
    human_judgment: false

duration: 18 min
completed: 2026-09-14
status: complete
---

# Phase 07 Plan 00: Research evidence contract Summary

**Contrato Django de evidencia v15 con hashes, DTOs allowlisted, cohortes auditables y exportaciones saneadas sin recalcular la evaluación**

## Performance

- **Duration:** 18 min
- **Started:** 2026-09-13T23:14:00Z
- **Completed:** 2026-09-13T23:32:38Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Se creó `panel_contract.py`, que carga solo las tres rutas publicadas, valida bytes e identidad v15 y proyecta `RunSummary`, `ComparisonRow`, `EvidenceDetails` y `ExportPayload` sin importar el runner.
- Se fijaron allowlists de ejecución, algoritmo, cohorte, métrica y formato; el orden del backend se conserva, la cohorte `no_history` queda explícitamente no evaluable y las métricas run-level no se atribuyen artificialmente a cohortes.
- Se añadieron exportaciones CSV/JSON/SVG con checksum y una suite de contrato que excluye `per_user`, logs, dumps, rutas absolutas y expresiones de consulta.
- Se documentó el shape, el mapeo de campos, la procedencia, la limitación de entorno de v15 y la trazabilidad EVAL-13/EVAL-14/DOC-05/AGENT-05; el vault vivo quedó enlazado.

## Task Commits

1. **Task 1: Tracer de artefacto v15 a DTO de comparación saneado** - `dec2ffc` (feat)
2. **Task 2: Allowlist de filtros, cohortes, métricas y formatos** - `fed3449` (test)
3. **Task 3: Registrar el contrato y la trazabilidad de fuente** - `1ef1336` (docs)

Commit adicional requerido por `AGENTS.md` para sincronizar el vault vivo: `d1c9fc1` (docs).

**Plan metadata:** se añadirá en el commit de cierre tras el autochequeo.

## Files Created/Modified

- `apps/api/evaluation/panel_contract.py` - loader, invariantes de publicación, DTOs y exportadores saneados.
- `apps/api/evaluation/tests/test_phase7_contract.py` - pruebas contra artefactos reales y entradas hostiles.
- `docs/verification/phase-07-evidence-contract.md` - contrato ejecutable y evidencia en español.
- `ideas-vault/Conceptos/Panel de investigacion.md` - enlace vivo a la decisión y sus fuentes canónicas.

## Decisions Made

- Se conserva la identidad histórica v15 del artefacto. La deriva del puntero actual `protocol.json` a v16 se trata como limitación de procedencia: se comprueban únicamente los anclajes comunes y nunca se presentan cifras recalculadas.
- Las métricas globales no desagregables se marcan `null` con explicación en cada cohorte, y la ausencia de entorno histórico no se rellena.
- El contrato no incorpora dependencias nuevas ni consultas ORM; la fuente de verdad sigue siendo el artefacto publicado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Resolución de deriva entre el artefacto v15 y el puntero de protocolo vigente**

- **Found during:** Task 1 (Tracer de artefacto v15 a DTO de comparación saneado)
- **Issue:** El artefacto real declara protocolo v15 y checksum `d492…`, pero `docs/methodology/protocol.json` ya contiene v16 y un feature set posterior; exigir igualdad literal impediría cargar la publicación v15 que este plan debe congelar.
- **Fix:** Se hizo autoritativa la identidad v15 declarada por el artefacto y se validan del puntero posterior solo los anclajes invariantes de corpus, snapshots, split, semillas, K y simulación. La diferencia queda explícita en la documentación y no se modifica ningún artefacto científico.
- **Files modified:** `apps/api/evaluation/panel_contract.py`, `docs/verification/phase-07-evidence-contract.md`
- **Verification:** Suite de contrato completa: 14 passed; suite de evaluación: 128 passed.
- **Committed in:** `dec2ffc` y `1ef1336`

**2. [Rule 2 - AGENTS.md hard constraint] Sincronización del vault vivo**

- **Found during:** cierre del plan
- **Issue:** `AGENTS.md` exige registrar en `ideas-vault/` toda decisión o limitación nueva material.
- **Fix:** Se añadió una nota fechada y enlazada en `ideas-vault/Conceptos/Panel de investigacion.md`, sin guardar secretos ni logs.
- **Files modified:** `ideas-vault/Conceptos/Panel de investigacion.md`
- **Verification:** diff limpio y commit dedicado con `Refs #65`.
- **Committed in:** `d1c9fc1`

**Total deviations:** 2 auto-fixed (Rule 3: 1; Rule 2/AGENTS.md: 1).
**Impact on plan:** Ambas desviaciones son necesarias para consumir honestamente la publicación v15 y mantener la trazabilidad del repositorio; no se relanzó la evaluación ni se modificaron snapshots.

## Issues Encountered

- La deriva v15/v16 descrita arriba fue resuelta de forma explícita y queda visible para los siguientes planes. No hubo gates de autenticación, instalaciones de dependencias ni verificaciones omitidas.

El gate global de requisitos compartidos no autoriza todavia el cierre de los IDs declarados por planes posteriores: EVAL-13, EVAL-14, DOC-05 y AGENT-05 tambien pertenecen a otras entregas de la fase. Por eso `REQUIREMENTS.md` permanece en `Pending` hasta que se completen esos planes.

## Authentication Gates

None - no se necesitaron servicios externos ni credenciales.

## User Setup Required

None - no hay configuración externa ni servicios nuevos.

## Next Phase Readiness

El contrato público está listo para que `07-01` conecte endpoints Django/DRF y para que `07-03` implemente la UI sin interpretar el JSON bruto. `07-05` debe conservar la comprobación de la limitación v15/v16 y el gate final de evidencia.

---
*Phase: 07-research-panel-hardening-and-evidence-freeze*
*Plan: 00*
*Completed: 2026-09-14*

## Self-Check: PASSED

- `07-00-SUMMARY.md` existe en la ruta canónica.
- Los commits `dec2ffc`, `fed3449`, `1ef1336` y `d1c9fc1` existen en el historial.
- `uat classify-coverage` clasificó D1-D4 como cobertura automática completa.
- `git diff --check` no encontró errores.
