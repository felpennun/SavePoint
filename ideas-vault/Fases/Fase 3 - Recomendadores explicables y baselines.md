---
tags: [fase/3, roadmap, tema/recomendadores, tema/evaluacion]
---

# Fase 3 - Recomendadores explicables y baselines

Meta: correr el harness congelado sobre los baselines aleatorio y de
popularidad mas el recomendador de la Fase 2 y variantes de contenido
adicionales, con enrutado de arranque en frio, exclusiones, explicaciones
deterministas, la suite completa de metricas, informe por cohortes y artefactos
recalculables de forma independiente.

## Estado actual

La discusión de la fase está **completada y lista para planificación** (2026-09-08). Todavía
no es una fase planificada ni ejecutada.

## Decisiones incorporadas en la discusión

- Actualizar el corpus gobernado antes de los nuevos experimentos, sin reescribir el trabajo
  cerrado de la fase 2.
- Aumentar la cobertura de ratings mediante fuentes autorizadas y trazables; no hacer scraping
  de Metacritic u OpenCritic ni consumir más RAWG.
- Calcular y conservar PopScore para el catálogo de tendencia y como señal pequeña del
  recomendador, junto con snapshots, procedencia y fecha de corte.
- Excluir juegos con fecha futura respecto a la fecha actual de catálogo, colección y
  recomendaciones.
- Usar rating, géneros, saga, desarrollador, plataforma, número de valoraciones, novedad y
  tendencia/popularidad como métricas del recomendador.
- Basar la recomendación en la colección del usuario, incluyendo juegos en progreso; usar
  juegos con al menos una valoración o con rating válido aunque no tengan contador de votos.
  Los juegos sin rating pueden seguir explorándose en el catálogo, pero no los devolverá el
  recomendador.
- Considerar las valoraciones propias de 3,5 o más y aplicar una señal negativa a candidatos
  similares cuando al menos tres juegos del mismo género de la colección estén por debajo de
  ese umbral.
- La búsqueda por nombre será por similitud y no quedará limitada por la ordenación de
  relevancia; se excluirán duplicados de ediciones especiales o deluxe según metadatos y
  tokens definidos.
- La web mostrará el ranking real generado por el algoritmo, no listas placeholder.

Fuentes canónicas: [`03-CONTEXT.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-CONTEXT.md) y
[`03-DISCUSSION-LOG.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-DISCUSSION-LOG.md).

## Enlaces

- [[Metricas de ranking]] · [[Diversidad y novedad]] · [[Cohortes de usuario]]
- [[Artefacto de evaluacion reproducible]] · [[Versionado de resultados]]
- [[Baseline aleatorio]] · [[Baseline de popularidad]] · [[Recomendador basado en contenido]]
- [[Requisitos - Experimentacion y evaluacion]]
