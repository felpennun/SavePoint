---
tags: [concepto, tema/evaluacion, fase/2]
---

# Protocolo de evaluacion congelado

Congelado el 2026-09-07 y ratificado por Felipe. Contrato legible por maquina en
`docs/methodology/protocol.json`; el cargador `apps/api/evaluation/protocol.py`
lo valida y se niega a correr si la rejilla de tuning supera 24 combinaciones o
si el split de test ya fue consumido. Fija relevancia, K, usuarios, conjuntos de
candidatos, exclusiones, manifiestos de split, metricas, semillas, presupuesto de
tuning y aislamiento del test **antes** de que corra cualquier recomendador
avanzado (EVAL-01, EVAL-02, EVAL-03).

Reversibilidad one-way: en cuanto una comparacion citada en el TFG lo referencia
por su SHA-256, cambiar relevancia/K/split/metricas/tuning invalida esa
comparacion. Todo artefacto derivado lleva `simulation: true`.

## Enlaces

- [[Split leave-one-out]] · [[Metricas de ranking]] · [[Usuarios sinteticos]]
- [[Conjunto de candidatos compartido]] · [[Artefacto de evaluacion reproducible]]
- [[Fase 2 - Corpus gobernado y evaluacion]]
