---
phase: 04-collaborative-and-hybrid-comparison
status: active
---

# Contexto de la Fase 4

## Decisiones del autor

- La Fase 4 incorpora exactamente dos algoritmos nuevos a la suite web y
  offline:
  - `cf-user-knn-v1`, filtrado colaborativo basado en similitud usuario-usuario.
  - `hybrid-weighted-cf-v1`, combinación del algoritmo Weighted con la señal
    colaborativa anterior.
- Cada algoritmo tendrá un worker web independiente y una estantería propia,
  con explicación localizada.
- La evaluación offline incluirá un worker por algoritmo y ejecutará los
  trabajos en paralelo. Cada trabajo registrará duración, estado y errores; el
  artefacto final conservará también el tiempo total y el tiempo de cada
  algoritmo.
- Las variantes existentes de contenido, PopScore y MMR no se modifican.

## Contrato metodológico decidido

- Todos los algoritmos reciben el mismo candidate set, exclusiones, split,
  métricas, seeds y snapshots que la suite de Fase 3.
- El colaborativo usa ratings explícitos de `LibraryEntry` normalizados a
  `[0, 1]`, centra cada usuario sobre su media y calcula coseno sobre obras
  valoradas en común. Se consideran vecinos con al menos dos obras comunes y
  se usan los 20 vecinos positivos más similares.
- Para usuarios sin vecinos suficientes, el colaborativo usa una señal global
  de frecuencia de interacción calculada sobre la población de referencia; no
  inventa similitud individual.
- En offline, la población de referencia colaborativa es únicamente `train`.
  En web es la población persistida disponible, excluyendo al usuario actual.
- El híbrido combina `0,60 * content_weighted + 0,40 * collaborative` y
  utiliza el contenido como fallback cuando no hay señal colaborativa.
- Los workers web publican de forma atómica el snapshot completo solo cuando
  terminan todas las secciones de la revisión actual.

## Límites

- No se incorporan ALS, BPR, item-kNN, deep learning ni variantes PopScore del
  colaborativo o híbrido en esta fase.
- La paralelización offline no permite que un algoritmo vea resultados de otro
  ni modifica el protocolo de evaluación; únicamente divide el trabajo y
  añade medición temporal.

