---
tags: [concepto, tema/evaluacion]
---

# Conjunto de candidatos compartido

`apps/api/evaluation/candidates.py` es el **unico** constructor del conjunto de
candidatos por usuario; `runner.py` comprueba que cada algoritmo recibe y
devuelve el mismo universo permitido, con las mismas exclusiones. Asi una
diferencia de metricas no se atribuye a poblaciones o candidatos distintos
(control contra sesgo).

## Enlaces

- [[Exclusion de ya consumidos]] · [[Control contra sesgo]] · [[Protocolo de evaluacion congelado]]
