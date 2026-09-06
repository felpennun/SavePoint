---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 01
subsystem: api
tags: [django, postgresql, corpus, provenance, reproducibility]

requires:
  - phase: 01.1-real-scale-catalogue-and-product-experience
    provides: "GameWork, GameRelease, Platform, Genre y SourceRecord del catálogo IGDB"
provides:
  - "Frontera de corpus gobernado versionada y reversible"
  - "Comando govern_corpus con checksum, diccionario, informe de calidad y manifiesto determinista"
  - "Modelos CorpusVersion y CorpusRatingSnapshot para el contrato de snapshots"
affects: [02-02, 02-03, 02-05, 02-08, 02-10, 02-11, 02-13]

actuals:
  tokens: 7600
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Comandos offline PostgreSQL con advisory lock, transacción y evidencia JSON sin secretos"
    - "Vistas de investigación acotadas por in_corpus y corpus_version, sin borrar el catálogo fuente"

key-files:
  created:
    - "apps/api/catalogue/migrations/0006_governed_corpus.py"
    - "apps/api/catalogue/corpus.py"
    - "apps/api/catalogue/management/commands/govern_corpus.py"
    - "apps/api/catalogue/tests/test_govern_corpus.py"
    - "docs/verification/corpus-governance-freeze.md"
    - "docs/verification/corpus-governance-freeze.json"
  modified:
    - "apps/api/catalogue/models.py"

key-decisions:
  - "La allowlist queda fijada a 39 slugs de plataforma ratificados por el autor; Steam se resuelve como PC/Windows."
  - "La ausencia de rating no excluye una obra del corpus; la política de rating se mantiene separada."
  - "La opción --version del comando se reserva para corpus_version, sustituyendo la opción genérica de Django."

patterns-established:
  - "La marca in_corpus es reversible y corpus_version identifica la vista consumible por experimentos."
  - "El checksum usa pares SourceRecord(source_id, snapshot_sha256) ordenados numéricamente y separados con NUL/LF."

requirements-completed: [DATA-03, DOC-02, DATA-06]

coverage:
  - id: D1
    description: "Reglas D-03 aplicadas sobre PostgreSQL y persistidas en una vista gobernada reversible"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_govern_corpus.py::test_govern_corpus_applies_every_d03_clause_and_keeps_unrated"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api/catalogue -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Evidencia citable con checksum, diccionario, calidad, exclusiones y muestra determinista"
    requirement: DOC-02
    verification:
      - kind: integration
        ref: "apps/api/catalogue/tests/test_govern_corpus.py::test_govern_corpus_is_idempotent_and_emits_all_evidence_sections"
        status: pass
    human_judgment: false
  - id: D3
    description: "Reejecución del comando sobre la base de desarrollo persistente y conservación del checksum medido"
    requirement: DATA-06
    verification:
      - kind: manual_procedural
        ref: "python manage.py govern_corpus --evidence-json docs/verification/corpus-governance-freeze.json"
        status: unknown
    human_judgment: true
    rationale: "La base persistente a escala y el checksum publicado requieren una ejecución humana controlada fuera de la base efímera de pytest."

duration: 45min
completed: 2026-09-07
status: complete
---

# Phase 2: Gobernanza, ratings externos, contrato de evaluación y primer recomendador avanzado — Plan 01

**Corpus IGDB gobernado, reversible y versionado con evidencia determinista de checksum, calidad y procedencia**

## Performance

- **Duration:** 45 min de ejecución y verificación
- **Started:** 2026-09-07T00:30:00+02:00
- **Completed:** 2026-09-07
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- El autor ratificó la allowlist completa de 39 plataformas; la implementación la centraliza por slug.
- La migración aditiva conserva el catálogo fuente y añade `in_corpus`, `corpus_version`, `summary`, `CorpusVersion` y `CorpusRatingSnapshot`.
- `govern_corpus` aplica D-03 sin exigir rating, produce una versión monotónica, toma un advisory lock y emite evidencia JSON no enumerativa.
- Las pruebas PostgreSQL específicas pasan 3/3 y la regresión completa de `catalogue` pasa 62/62.

## Task Commits

1. **Tarea 1: Ratificación de allowlist** — `a8ffda2` (checkpoint de decisión)
2. **Tarea 2: Frontera gobernada y tracer PostgreSQL** — `4ed82bf` (feat)
3. **Tarea 3: Evidencia DATA-03 y documentación** — `ab68ce5` (docs)

**Plan metadata:** pendiente de commit de cierre con SUMMARY y sincronización de estado.

## Files Created/Modified

- `apps/api/catalogue/models.py` — campos de gobernanza y modelos de snapshot/versión.
- `apps/api/catalogue/migrations/0006_governed_corpus.py` — migración aditiva sin data migration.
- `apps/api/catalogue/corpus.py` — allowlist ratificada, validación D-03 y queryset gobernado.
- `apps/api/catalogue/management/commands/govern_corpus.py` — aplicación de reglas y evidencia.
- `apps/api/catalogue/tests/test_govern_corpus.py` — cláusulas, idempotencia y secciones de evidencia.
- `docs/verification/corpus-governance-freeze.md` — contrato documental en español.
- `docs/verification/corpus-governance-freeze.json` — artefacto JSON regenerable.

## Decisions Made

- Steam se representa mediante PC/Windows, porque no es una plataforma IGDB independiente.
- El rating queda fuera de las reglas de pertenencia: se conservarán también obras no valoradas.
- La evidencia usa una muestra determinista de hasta 300 registros y no un volcado masivo.

## Deviations from Plan

**1. Reemplazo de la opción base `--version` de Django**
- **Encontrado durante:** Tarea 2, al construir el parser del management command.
- **Problema:** Django registra `--version` globalmente y bloquea una segunda declaración.
- **Corrección:** El comando reemplaza la acción base para que `--version` signifique la versión del corpus, como exige el plan.
- **Verificación:** Las pruebas de command pasan y la opción se usa en los fixtures.
- **Commit:** `4ed82bf`.

**Total de desviaciones:** 1 corrección necesaria de integración.
**Impacto:** Se conserva la interfaz documental del plan sin añadir una dependencia ni alterar otros comandos.

## Issues Encountered

Ninguno pendiente. La regresión completa de catálogo quedó verde.

## User Setup Required

Ninguno.

## Next Phase Readiness

02-02 puede añadir los campos de rating de usuarios y poblar snapshots sin tocar la frontera ni los modelos de versión. Queda pendiente la ejecución manual sobre la base de desarrollo persistente para convertir D3 en evidencia medida a escala.

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Plan: 01*
*Completed: 2026-09-07*
