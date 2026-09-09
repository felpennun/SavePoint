---
tags: [concepto, tema/evaluacion, fase/2]
---

# Usuarios sinteticos

Arquetipos parametrizados y regenerables por semilla. La Fase 3 usa 400 usuarios
nuevos que sustituyen a los 200 de Fase 2 como población activa, con cohortes
10/100/240/50 (sin historial, 1–4, 5–10 y más de 10 juegos). Las bibliotecas
solo usan obras con `rating_count >= 1` y aplican pesos escalonados crecientes
(1/2/4/8/16/32) por tramos de volumen para aproximar la concentración real de
popularidad. El resultado se audita en
`docs/verification/synthetic-users-validation.md`.
Cualquier resultado bajo el protocolo es **evidencia de simulacion, no evidencia
sobre usuarios reales** (EVAL-09, EVAL-10).

## Enlaces

- [[Cuentas simuladas]] · [[Protocolo de evaluacion congelado]] · [[Control contra sesgo]]
- [[Cohortes de usuario]]
