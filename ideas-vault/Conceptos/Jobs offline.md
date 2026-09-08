---
tags: [concepto, tema/arquitectura, tema/metodologia]
---

# Jobs offline

Los algoritmos, la importacion de catalogo y el enriquecimiento de ratings corren
como **comandos de gestion explicitos**, nunca dentro de una peticion HTTP.
Evita latencia impredecible, carreras y estado de modelo irreproducible, y
mantiene el acceso a proveedores externos fuera del tiempo de peticion (CAT-06,
OPS-03).

## Enlaces

- [[Comando govern_corpus]] · [[Feature vectors de contenido]] · [[IGDB]] · [[RAWG]]
- [[Artefacto de evaluacion reproducible]] · [[ADR-001 - Monolito modular Django + Next.js]]
