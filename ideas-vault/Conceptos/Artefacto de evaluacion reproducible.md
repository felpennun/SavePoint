---
tags: [concepto, tema/evaluacion, tema/metodologia]
---

# Artefacto de evaluacion reproducible

Los resultados se generan desde `apps/api/evaluation/runner.py` y se conservan
como un artefacto JSON, no como una explicacion redactada a mano. Cada ejecucion
registra codigo, entorno, dataset, split, semillas, parametros, modelo y
metricas (EVAL-11); los artefactos almacenados permiten recalcular los agregados
sin reejecutar ningun modelo (EVAL-12). Si una ejecucion no puede producir un
artefacto completo, se documenta como pendiente o fallida, nunca se estiman sus
metricas.

## Enlaces

- [[Versionado de resultados]] · [[Snapshot inmutable]] · [[Panel de investigacion]]
- [[Reproducibilidad academica]] · [[Fase 3 - Recomendadores explicables y baselines]]
