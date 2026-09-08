---
tags: [concepto, tema/recomendadores]
---

# Exclusion de ya consumidos

Las recomendaciones excluyen juegos ya consumidos segun reglas configuradas
(REC-07). En el harness, `apps/api/evaluation/candidates.py` es el unico
constructor del conjunto de candidatos y aplica las mismas exclusiones a todos
los algoritmos, para que una diferencia de metricas no venga de universos
distintos.

## Enlaces

- [[Conjunto de candidatos compartido]] · [[Control contra sesgo]]
- [[Protocolo de evaluacion congelado]]
