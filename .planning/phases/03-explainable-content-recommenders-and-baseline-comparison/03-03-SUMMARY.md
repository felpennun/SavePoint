---
phase: 03-explainable-content-recommenders-and-baseline-comparison
plan: 03
status: completed_with_limitations
completed: 2026-09-12
github_issue: 39
---

# Resumen 03-03 — Métricas, incertidumbre y contrastes

## Resultado

El harness conserva métricas de acierto y *beyond-accuracy* por usuario antes de
agregarlas, con denominadores explícitos y estado no aplicable cuando corresponde.
La comparación estadística se ejecuta sobre observaciones pareadas por usuario e
incluye bootstrap BCa, Friedman, Wilcoxon bilateral y corrección de Holm. El
artefacto final v15 contiene además las semillas, hashes de protocolo, corpus,
ratings, PopScore, población y split, junto con los tiempos de cada worker y el
estado final.

## Trabajo verificado en este cierre

- Se añadió `evaluation.cohort_analysis`, que une el artefacto congelado con el
  manifiesto de los 400 usuarios sin consultar datos vivos ni relanzar algoritmos.
- Se añadió el comando `analyze_evaluation_artifact` para producir JSON y Markdown
  citable por cohorte.
- Se cubren las cohortes realmente presentes en v15: `active_history_10_to_20`
  (390 usuarios en el manifiesto, 79 evaluables en test) y `no_history` (10,
  correctamente no evaluables por ranking).
- El informe calcula por cohorte precisión, recall, nDCG, MAP, diversidad
  intra-lista y novedad para K=5, 10 y 20.
- Cobertura de catálogo, HHI y cobertura de predicción se mantienen como métricas
  globales del run porque v15 no guardó las listas recomendadas completas. No se
  inventa un reparto por cohortes.
- Se añadió cobertura de tests para el análisis por cohortes y para la captura de
  recursos del merge paralelo: `3 passed` en los tests dirigidos.

## Limitación metodológica aceptada

El punto 6 del cierre solicitado —repetir el experimento con varias semillas— no se
ejecuta sobre el test v15. El marcador de test ya está consumido y el protocolo fija
`test_runs: 1`; repetirlo exigiría un nuevo protocolo, población, split y artefacto
versionados. La limitación se documenta como parte de la validez: el resultado v15
es evidencia condicional para esta población sintética, corpus y semilla, no una
estimación de robustez entre semillas. El bootstrap cuantifica incertidumbre de las
observaciones pareadas dentro de este run, pero no sustituye la sensibilidad entre
semillas.

## Archivos principales

- `apps/api/evaluation/metrics.py`
- `apps/api/evaluation/statistics.py`
- `apps/api/evaluation/cohort_analysis.py`
- `apps/api/evaluation/management/commands/analyze_evaluation_artifact.py`
- `docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.md`
- `docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.json`

## Verificación

```text
docker compose -f infra/compose.yaml exec -T api pytest \
  /workspace/apps/api/evaluation/tests/test_cohort_analysis.py \
  /workspace/apps/api/evaluation/tests/test_parallel.py -q
3 passed
```

No se volvió a ejecutar `run_evaluation_parallel`; el artefacto v15 permanece
inmutable.
