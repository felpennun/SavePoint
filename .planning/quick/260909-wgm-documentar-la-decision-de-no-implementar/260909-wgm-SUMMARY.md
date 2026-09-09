---
phase: quick-documentation
plan: 01
subsystem: documentation
tags: [recommendations, hybrid, mmr, methodology, obsidian]

# Dependency graph
requires:
  - phase: Fase 4
    provides: Contrato vigente de `cf-user-knn-v1`, `hybrid-weighted-cf-v1` y las variantes MMR de contenido.
provides:
  - Decisión metodológica documentada sobre el alcance de la comparación de Fase 4.
  - Especificación reproducible de `hybrid-mmr-v1` como propuesta futura no implementada.
  - Sincronización de la decisión en las dos notas relacionadas del vault vivo.
affects: [Fase 4, recomendaciones híbridas, metodología, tesis]

# Actuals (#2632)
actuals:
  tokens: 1355
  tasks: 2
  commits: 0

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Separar explícitamente algoritmos implementados, decisiones de alcance y propuestas futuras en la evidencia metodológica."
    - "Mantener la arquitectura canónica como fuente y enlazarla desde las notas conceptuales del vault."

key-files:
  created: []
  modified:
    - docs/verification/recommendation-architecture-2026-09-09.md
    - ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md
    - ideas-vault/Conceptos/Recomendador hibrido.md

key-decisions:
  - "La comparación actual de Fase 4 se limita a `cf-user-knn-v1` y `hybrid-weighted-cf-v1`; Item-KNN, los recomendadores neuronales y otros modelos complejos quedan fuera por alcance y validez, no por una afirmación de inferioridad algorítmica."
  - "`hybrid-mmr-v1` queda definido como Propuesta — no implementado, sin worker, estantería, registro, snapshot ni resultados."

patterns-established:
  - "Las propuestas futuras conservan fecha, estado explícito, fórmula, límites de ejecución y enlace a la fuente canónica."

requirements-completed: [REC-05, DOC-03]

coverage:
  - id: D1
    description: "Arquitectura canónica con la frontera metodológica de Fase 4 y la fórmula reproducible propuesta para `hybrid-mmr-v1`."
    requirement: REC-05
    verification:
      - kind: other
        ref: "PowerShell: verificación de términos requeridos en recommendation-architecture-2026-09-09.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "Notas del vault sincronizadas con la propuesta, su estado no implementado y los enlaces canónicos y relacionados."
    requirement: DOC-03
    verification:
      - kind: other
        ref: "PowerShell: verificación de términos requeridos en las dos notas del vault"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-09-09
status: complete
---

# Tarea rápida 260909-wgm: límite metodológico de Fase 4 y propuesta híbrida MMR

**La arquitectura y el vault vivo separan los algoritmos colaborativo e híbrido implementados de `hybrid-mmr-v1`, definido con MMR reproducible como propuesta futura no implementada.**

## Rendimiento

- **Duración:** 6 min
- **Iniciada:** 2026-09-09T21:29:02Z
- **Completada:** 2026-09-09
- **Tareas:** 2
- **Archivos objetivo modificados:** 3

## Logros

- Documentada la decisión de mantener la comparación en `cf-user-knn-v1` y `hybrid-weighted-cf-v1`, con la exclusión metodológica de Item-KNN, modelos neuronales y otros modelos complejos.
- Definida `hybrid-mmr-v1` con composición 0,60/0,40, fallback Weighted, pool de 100 o `5 * K`, `lambda = 0,80`, coseno de `fs-v9` y profundidad de 20.
- Sincronizadas las dos notas del vault con el estado `Propuesta — no implementado`, los límites explícitos y los enlaces a la arquitectura canónica.

## Commits de tareas

No se realizaron commits por instrucción explícita del autor; el orquestador gestionará el commit final de la documentación.

## Archivos modificados

- `docs/verification/recommendation-architecture-2026-09-09.md` — frontera metodológica y especificación canónica de `hybrid-mmr-v1`.
- `ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md` — alcance aceptado y propuesta futura enlazada.
- `ideas-vault/Conceptos/Recomendador hibrido.md` — definición híbrida actual y composición MMR propuesta.

## Decisiones tomadas

Se siguió el plan exactamente: documentación-only, sin implementar `hybrid-mmr-v1`, sin ejecutar algoritmos y sin modificar código, base de datos, workers, shelves, protocolo, snapshots ni resultados.

## Desviaciones del plan

Ninguna. Se conservaron los cambios paralelos preexistentes del árbol de trabajo y se modificaron únicamente los tres documentos objetivo.

## Problemas encontrados

Ninguno que requiriera cambios fuera del plan. Las dos verificaciones automatizadas y `git diff --check` pasaron.

## Configuración requerida por el usuario

Ninguna.

## Preparación para el siguiente trabajo

La arquitectura y el vault dejan preparada la trazabilidad para una futura decisión sobre `hybrid-mmr-v1`, pero no autorizan su implementación ni la generación de resultados. Cualquier trabajo posterior deberá conservar el corpus, las exclusiones, las semillas y el contrato de evaluación vigentes.

---
*Tarea: 260909-wgm*
*Completada: 2026-09-09*

## Self-Check: PASSED

- `260909-wgm-SUMMARY.md` existe y contiene `status: complete`.
- Los tres documentos objetivo existen y contienen los términos requeridos por las verificaciones del plan.
- Las dos verificaciones automatizadas y `git diff --check` pasan.
- No se realizaron commits, conforme a la instrucción explícita del autor.
