---
phase: quick-implementation
plan: 01
subsystem: recommendations
tags: [hybrid, mmr, rating, web, offline]
requires:
  - phase: Fase 4
    provides: cf-user-knn-v1, hybrid-weighted-cf-v1 y variantes MMR de contenido
provides:
  - hybrid-mmr-v1 compartido entre web y offline
  - rating-final con calidad bayesiana y confianza explícita
  - worker, estantería y entrada de evaluación independientes
affects: [Fase 4, evaluación, recomendaciones web, metodología]
key-files:
  created: []
  modified:
    - apps/api/recommendations/content/features.py
    - apps/api/recommendations/content/combine.py
    - apps/api/recommendations/content/rank.py
    - apps/api/recommendations/hybrid.py
    - apps/api/evaluation/runner.py
    - apps/api/evaluation/protocol.py
    - docs/methodology/protocol.json
    - docs/methodology/evaluation-protocol.md
    - docs/verification/recommendation-architecture-2026-09-09.md
    - ideas-vault/Conceptos/Recomendador hibrido.md
    - ideas-vault/Fases/2026-09-09 - Variantes MMR.md
    - ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md
key-decisions:
  - "rating_final = rating_quality * rating_confidence, con m=25 y sin volver a aplicar rating_volume."
  - "hybrid-mmr-v1 combina 0,60 Weighted y 0,40 User-kNN y aplica MMR con lambda=0,80 sobre max(100, 5*K)."
  - "Item-KNN y modelos neuronales/complejos permanecen fuera del alcance de la comparación."
requirements-completed: [REC-05, REC-08, REC-09, EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06, EVAL-11, EVAL-12, DOC-03, QUAL-02]
status: complete
completed: 2026-09-10
commits:
  - 78ef5dc
  - f86a96c
  - 2c12838
---

# Tarea rápida 260909-ws8: MMR híbrido y rating final

## Resultado

Se implementó `hybrid-mmr-v1` con el mismo ranker en web y offline. Combina
`0,60` de `content-cbf-weighted-v1` y `0,40` de `cf-user-knn-v1`, conserva el
fallback Weighted, aplica MMR sobre `max(100, 5 * K)` con `lambda = 0,80` y
publica 20 resultados. Cuenta con worker y estantería propios y está incluido
en el runner paralelo offline.

La señal global queda definida como `rating_final`: rating bayesiano
normalizado al cuadrado (`rating_quality`) multiplicado por `n / (n + 25)`
(`rating_confidence`), con `n = total_rating_count`. No se modifica el rating
personal de las semillas ni la señal colaborativa.

## Verificación

- Backend completo: 487 pruebas correctas.
- Recomendaciones y evaluación: 206 pruebas correctas.
- Pruebas focalizadas de fórmula, MMR, servicio, workers, protocolo y runner: 74 correctas.
- TypeScript: `tsc --noEmit` correcto.
- Compose: configuración válida.
- Migraciones: `makemigrations --check --dry-run` sin cambios pendientes.
- JSON del protocolo: válido; protocolo v10, 31 configuraciones y 16 algoritmos offline.
- No se ejecutó la evaluación experimental de los 400 usuarios.

La suite web completa ejecutó 28 pruebas; las seis pruebas de navegación siguen
sin poder ejecutarse en el contenedor efímero porque la instalación de
Chromium no persiste entre contenedores. Las pruebas de recomendaciones sí
pasaron; el bloqueo restante es únicamente del entorno Playwright.

## Alcance

No se implementaron Item-KNN, modelos neuronales ni otros modelos complejos.
La decisión y sus motivos están documentados en la arquitectura canónica y en
las notas del vault.

