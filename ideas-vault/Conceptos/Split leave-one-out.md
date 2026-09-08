---
tags: [concepto, tema/evaluacion]
---

# Split leave-one-out

El split es leave-one-out por usuario: de los juegos relevante-positivos del
usuario (estado `completed` o `rating_half_steps >= 7`) se retira exactamente
uno, elegido de forma determinista por `random.Random(f"{seed}:{user.id}")` con
la semilla congelada. Un usuario sin ningun juego relevante-positivo se excluye
del split en lugar de provocar un error.

## Enlaces

- [[Protocolo de evaluacion congelado]] · [[Metricas de ranking]] · [[Valoraciones]]
