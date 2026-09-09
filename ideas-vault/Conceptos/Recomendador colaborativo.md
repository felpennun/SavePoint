---
tags: [concepto, tema/recomendadores, fase/4]
---

# Recomendador colaborativo

Al menos un metodo de filtrado colaborativo (REC-04): k-NN usuario/item o
factorizacion de matrices sobre interacciones dispersas (SciPy sparse), evaluado
para cohortes elegibles con los mismos candidatos, exclusiones, particiones,
metricas y presupuesto de tuning que los metodos previos. Es trabajo de la
Fase 4.

## Implementacion aceptada — 2026-09-09

Se concreta como `cf-user-knn-v1`: ratings explicitos normalizados y centrados
por usuario, minimo de dos obras comunes, top-20 vecinos positivos y fallback
por frecuencia global. Offline usa exclusivamente usuarios `train`; web usa
los demas usuarios persistidos. Tiene worker y estanteria propios. Fuente:
`docs/verification/recommendation-architecture-2026-09-09.md`.

## Enlaces

- [[Recomendador basado en contenido]] · [[Recomendador hibrido]]
- [[Protocolo de evaluacion congelado]] · [[Cohortes de usuario]]
- [[Fase 4 - Colaborativo e hibrido]]
