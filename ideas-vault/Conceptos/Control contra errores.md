---
tags: [concepto, tema/metodologia]
---

# Control contra errores

Tests unitarios, de integracion y de contrato. Metricas en funciones
independientes (`precision_at_k`, `recall_at_k`, `ndcg_at_k`, `map_at_k`) para
K = 5/10/20. Variantes registradas en `variants.py`; protocolo en `protocol.json`;
semillas congeladas. Si una ejecucion no produce un artefacto completo se
documenta como pendiente o fallida, nunca se sustituyen metricas por estimaciones.

## Enlaces

- [[Metricas de ranking]] · [[Snapshot inmutable]] · [[Artefacto de evaluacion reproducible]]
- [[Controles metodologicos AGENT-04]] · [[Testing y calidad]]
