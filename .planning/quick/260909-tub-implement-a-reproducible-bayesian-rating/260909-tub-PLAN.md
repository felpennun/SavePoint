---
quick_id: 260909-tub
status: complete
---

# Plan: señal bayesiana de fiabilidad del rating

## Objetivo

Sustituir la atenuación lineal basada en volumen por una valoración IGDB
bayesiana y reproducible. La misma señal debe alimentar la web, los workers y
la evaluación offline, sin modificar el corpus candidato ni el perfil de
contenido.

## Decisiones

- Media previa: media de ratings IGDB del snapshot congelado del corpus.
- Fuerza de la previa: 25 valoraciones totales (`m = 25`). Con `n = 5`, el
  rating observado conserva 1/6 de su peso; con `n = 25`, mitad; con `n = 100`,
  cuatro quintas partes.
- Fórmula: `(n / (n + m)) * rating_igdb + (m / (n + m)) * media_previa`;
  después se normaliza y se eleva al cuadrado, como el contrato actual de
  énfasis de calidad.
- La señal de volumen sigue expuesta como evidencia, pero no multiplica otra
  vez la puntuación: su efecto queda incorporado en el rating bayesiano.

## Tareas

1. Implementar la previa y la transformación bayesiana versionada, y adaptar
   ranker, combinadores y protocolo compartido.
2. Actualizar pruebas, documentación, vault y artefactos GSD; ejecutar la
   reevaluación de Felipe en los diez workers.

## Verificación

- Pruebas backend de recomendaciones y evaluación.
- TypeScript web.
- Diez workers de Felipe publicados bajo la nueva huella.
- Comparación reproducible de Silksong y Terraria.
