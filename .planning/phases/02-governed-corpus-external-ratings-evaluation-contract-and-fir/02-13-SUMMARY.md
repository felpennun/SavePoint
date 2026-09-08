---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 13
subsystem: evaluation
tags: [evaluation, reproducibility, synthetic-users, content-based, ratings, provenance, methodology]

requires:
  - phase: 02-08
    provides: "Protocolo congelado, métricas de ranking, split leave-one-out y guardia de test consumido."
  - phase: 02-09
    provides: "Población de usuarios sintéticos reproducible y validada."
  - phase: 02-10
    provides: "Baseline aleatorio y representación de características para contenido."
  - phase: 02-11
    provides: "Tres variantes del recomendador de contenido y sus contratos versionados."
provides:
  - "Arnés de evaluación con candidate set único y manifiesto compartido entre cinco algoritmos."
  - "Primera comparación completa sobre el split test sintético y artefacto JSON inmutable."
  - "Informe en español con identidad, métricas por K, interpretación y limitaciones."
  - "Controles metodológicos AGENT-04 y reglas deterministas DATA-07 documentados."
affects: [phase-03, DOC-04, AGENT-04, DATA-07, EVAL-01]

actuals:
  tokens: 0
  tasks: 3
  commits: 0

key-files:
  created:
    - docs/verification/evaluation-run-first.md
    - docs/verification/evaluation-run-first.artifact.json
    - docs/methodology/agent-methodology-controls.md
    - apps/api/evaluation/candidates.py
    - apps/api/evaluation/runner.py
    - apps/api/evaluation/management/commands/run_evaluation.py
    - apps/api/evaluation/tests/test_runner.py
  modified:
    - docs/methodology/protocol.json
    - docs/adr/ADR-008-external-ratings.md

key-decisions:
  - "El split test se ejecutó una sola vez con el protocolo v2; el marcador consumido impide reintentos silenciosos."
  - "La población real de este run es de 26 usuarios evaluados de 40 solicitados; 14 se excluyen por falta de positivo elegible."
  - "Los ceros de nDCG@10 y del resto de métricas son un resultado legítimo de simulación y no justifican cambiar el protocolo a posteriori."
  - "La reconciliación de identificadores conserva IGDB como identidad canónica y documenta el desempate prospectivo entre fuentes sin sobrescribir snapshots."

requirements-completed: [EVAL-01, DOC-04, AGENT-04, DATA-07]

coverage:
  - id: D1
    description: "Todos los algoritmos reciben el mismo candidate set por usuario y el manifiesto queda hasheado."
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "apps/api/evaluation/tests/test_runner.py"
        status: pass
  - id: D2
    description: "El artefacto final registra cinco algoritmos, métricas Precision/Recall/nDCG/MAP en K=5,10,20, ranks held-out, hashes, semillas y simulation:true."
    requirement: EVAL-01
    verification:
      - kind: artifact
        ref: "docs/verification/evaluation-run-first.artifact.json"
        status: pass
  - id: D3
    description: "El informe explica la ejecución, el empate en nDCG@10 y las amenazas de interpretar una simulación sintética como evidencia de usuarios reales."
    requirement: DOC-04
    verification:
      - kind: document
        ref: "docs/verification/evaluation-run-first.md"
        status: pass
  - id: D4
    description: "La metodología documenta controles frente a alucinación, sesgo, error y exposición de información, separando propuesta, verificación automática y decisión del autor."
    requirement: AGENT-04
    verification:
      - kind: gate
        ref: "scripts/check-evidence.ps1"
        status: pass
  - id: D5
    description: "ADR-008 documenta reconciliación determinista de identificadores, conflictos de rating, procedencia y backlink RAWG."
    requirement: DATA-07
    verification:
      - kind: gate
        ref: "scripts/check-evidence.ps1"
        status: pass

duration: "run v2 ya completado; cierre documental"
completed: 2026-09-08
status: complete_pending_author_review
---

# Fase 2, plan 13: primera comparación reproducible

## Accomplishments

- Se validó el run v2 sobre el protocolo 2, el corpus `2026.09.1` y el snapshot de ratings
  congelado. El artefacto conserva 40 usuarios solicitados, 26 evaluados y 14 excluidos.
- El runner comparó `random-v1`, `popularity-v1` y las variantes
  `content-cbf-weighted-v1`, `content-cbf-multiplicative-v1` y `content-cbf-twostage-v1`
  sobre candidate sets compartidos.
- Se resolvieron los placeholders de `protocol.json` y se generó el informe legible de la
  comparación en `docs/verification/evaluation-run-first.md`.
- Se mantuvieron separados el corpus gobernado completo y el universo elegible de la
  evaluación: el catálogo puede seguir buscando obras sin valoración, pero el runner solo
  las incorpora si cumplen la regla de elegibilidad del protocolo.
- Se completaron la documentación AGENT-04 y la sección DATA-07 del ADR-008.

## Verification

| Comprobación | Resultado |
|---|---|
| `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/evaluation -q` | `69 passed` |
| `powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1` | `PASS` |
| Artefacto final | Cinco algoritmos, K=5/10/20, hashes, semillas, ranks y limitación presentes |
| Experimento duplicado | No ejecutado; el protocolo v2 está consumido y protegido |

## Issues Encountered

El resultado agregado fue `0.000` para Precision, Recall, nDCG y MAP en todos los algoritmos
y cortes. El held-out no apareció en los top-20 observados. Es un resultado válido bajo la
simulación y se conserva sin cambiar semillas, población o reglas después de ver el resultado.

## Next Phase Readiness

La Fase 2 queda técnicamente preparada para su cierre: el contrato de evaluación, el corpus,
la procedencia, el runner y la evidencia están disponibles. La única revisión pendiente es la
decisión humana del autor sobre la interpretación académica del resultado de simulación y la
firma de fase. La Fase 3 puede planificarse después de esa firma, usando el artefacto como
entrada sin repetir el split test.
