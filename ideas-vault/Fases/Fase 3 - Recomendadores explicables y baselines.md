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

## Planificación de la fase

La planificación se ha preparado el 2026-09-08 en cuatro planes y tres ondas:

- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-01-PLAN|03-01]]: tracer, candidatos compartidos y protocolo v2.
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-PLAN|03-02]]: señales, variantes y explicaciones.
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-03-PLAN|03-03]]: métricas beyond-accuracy y estadística; contiene un checkpoint humano para SciPy/NumPy.
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-04-PLAN|03-04]]: runner, evidencia, web y sincronización del vault.

Artefactos de preparación: [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-RESEARCH|investigación]], [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-VALIDATION|contrato Nyquist]], [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-PATTERNS|mapa de patrones]] y [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-UI-SPEC|contrato visual aprobado]].

La planificación mantiene la decisión del proyecto de actualizar este vault con cada nueva decisión o información relevante. No se ha añadido una matriz API porque la fase usa snapshots gobernados y no integra una API externa nueva.

## Enlaces

- [[Metricas de ranking]] · [[Diversidad y novedad]] · [[Cohortes de usuario]]
- [[Artefacto de evaluacion reproducible]] · [[Versionado de resultados]]
- [[Baseline aleatorio]] · [[Baseline de popularidad]] · [[Recomendador basado en contenido]]
- [[Requisitos - Experimentacion y evaluacion]]
