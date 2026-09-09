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

La discusión de la fase está **completada y lista para planificación** (2026-09-08). La fase
está planificada, pero la comparación todavía no se ha ejecutado.

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
- Usar únicamente `rating` como nota de usuarios IGDB. `total_rating` (la combinación con
  crítica) queda excluido para no contar dos veces la calidad; `total_rating_count` se conserva
  como volumen y regla de elegibilidad.
- La rejilla queda en 24 configuraciones: 15 sumas ponderadas, 3 multiplicativas y 6 de dos
  etapas. `recency-v1` combina contenido, rating de usuarios, volumen y PopScore, y añade
  `recency_score` con peso propio.
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

## Estado de datos — 2026-09-09

El corpus algorítmico activo es `2026.09.2`; sus hashes de ratings y PopScore están fijados en
[`docs/methodology/protocol.json`](../../docs/methodology/protocol.json). La base contiene 400
usuarios sintéticos activos para la comparación principal y conserva 200 usuarios históricos de
Fase 2. La nueva población usa `rating_count >= 1` con ponderación escalonada creciente por
volumen, y las cohortes 10/100/240/50 ya están verificadas; todavía no se ha ejecutado ningún
algoritmo. Las franquicias de IGDB se tratan como la señal de saga y se incluyen cuando
existen, sin excluirlas por su cobertura global del 6,07 %; las obras sin saga simplemente
no reciben esa dimensión dispersa. Los controles finales de validación y archivo también
han pasado: no hay fechas ausentes/futuras ni candidatos inelegibles, la rejilla 24 cumple
15/3/6, solo usa rating de usuario y mantiene recencia en seis configuraciones. Los
resultados están archivados; todavía no se han ejecutado algoritmos.

La auditoría previa a algoritmos confirma 400 usuarios activos, 200 históricos preservados,
0 solapamiento y split 240/80/80. El manifiesto reproducible tiene hash
`be3e43c451724c9c3add784394955397292d20438dc18f17c60b1984e1f4dd38`. La cobertura de señales
es: géneros/plataformas 100 %, desarrolladores 53,03 %, franquicias 6,07 %, rating IGDB
14,19 %, volumen 16,08 % y PopScore completo 9.929 obras. Todavía no se ha ejecutado ningún
algoritmo.

## Integración del runner — 2026-09-09

El runner ya incorpora cobertura de catálogo y predicción, concentración HHI, diversidad
intra-lista y novedad. La novedad se calcula con probabilidades de interacciones de los usuarios
de entrenamiento, sin leer el conjunto de test para construir la señal. La suite dirigida pasó
120/120 tests y las evidencias del corpus, ratings, popularidad y PopScore quedaron archivadas.
No se ha lanzado ninguna evaluación experimental.

`fs-v4` es el namespace versionado de los vectores dispersos de contenido. Incluye la faceta
`franchise` de IGDB como señal de saga, además de géneros, plataformas y desarrolladores cuando
corresponde. El cambio de `fs-v3` a `fs-v4` impide reutilizar vectores creados con reglas antiguas;
una obra sin saga simplemente omite esa dimensión. La reconstrucción se completó para las
190.479 obras gobernadas: 186.211 vectores creados, 4.268 actualizados y 0 ausentes. La evidencia
está en [[../../apps/api/feature-vector-cache-2026.09.2.json|la evidencia de caché]].

## Contrato visual enmendado — 2026-09-09

La página de recomendaciones mostrará una sección independiente para cada variante publicable de
contenido: suma ponderada, combinación multiplicativa, dos etapas, señal negativa y recencia. A
continuación aparecerán la heurística por género y el estante relacional de DLC. Cada sección
algorítmica tendrá una explicación localizada de una o dos frases y conservará el orden real del
backend. La rejilla de investigación, los baselines académicos y las métricas no se mostrarán al
usuario final.

Fuente canónica: [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-UI-SPEC|contrato visual de Fase 3]].

Evidencia detallada: [[../../docs/verification/recommendation-input-audit-2026-09-09.md|auditoría de entradas de recomendación]].

## Caché personal y decisión sobre Redis — 2026-09-09

La web adopta un flujo stale-while-revalidate por usuario. Cada cambio de colección crea una
nueva revisión y un trabajo coalescido en PostgreSQL; el worker calcula las cinco variantes de
contenido y la heurística de género fuera de la petición. El bundle se publica de forma
atómica, por lo que el usuario conserva la versión anterior hasta que el nuevo cálculo está
completo. Si no hay snapshot previo, la interfaz muestra preparación y actualiza el estado
mediante refrescos breves del servidor.

Decisión: no instalar Redis en esta fase. PostgreSQL ya es la fuente de verdad y puede alojar
la cola durable, la revisión de colección y los snapshots; añadir Redis ahora duplicaría estado
operativo sin evidencia de necesidad. Se reconsiderará tras medir latencia y concurrencia en
la demo. Si se incorpora, será una aceleración efímera para lecturas o señalización, nunca el
único almacén del resultado publicado.

Fuente canónica: [[../../docs/verification/evaluation-runner-integration-2026-09-09|integración del runner y caché personal]].

## Arquitectura compartida de evaluación y producto — 2026-09-09

La comparación offline y el producto comparten el catálogo versionado de cinco
variantes de contenido: suma ponderada, multiplicativa, dos etapas, señal
negativa y recencia. El runner y cada worker consumen los mismos
`algorithm_id`, el mismo registro de variantes y los mismos pesos; los
baselines aleatorio y de popularidad se quedan únicamente en la evaluación.

Cada variante publicable tiene worker y estantería propios. La heurística por
género se ejecuta también con worker dedicado, como sección complementaria de
producto. Los seis trabajos de una revisión se publican de forma atómica: el
snapshot anterior se conserva hasta que todos han terminado. `fs-v5` pondera
género/plataforma/saga/desarrollador como 0,50/0,25/0,15/0,10; PopScore v2 usa
visitas/jugando/jugado/quiere jugar como 0,40/0,25/0,25/0,10.

Fuente canónica: [[../../docs/verification/recommendation-architecture-2026-09-09|contrato compartido de algoritmos]].

## Elegibilidad de calidad endurecida — 2026-09-09

Las recomendaciones ya no aceptan la alternativa previa de una sola
observación total o fallback de género sin nota propia. Toda obra recomendada
debe tener `rating` de usuario IGDB y `total_rating_count >= 10`, además de
pertenecer al corpus gobernado y no tener fecha futura. El catálogo conserva
las obras restantes para exploración, pero no entran en ningún ranking.

Fuente canónica: [[../../docs/verification/recommendation-architecture-2026-09-09|contrato compartido de algoritmos]].

## Enlaces

- [[Metricas de ranking]] · [[Diversidad y novedad]] · [[Cohortes de usuario]]
- [[Artefacto de evaluacion reproducible]] · [[Versionado de resultados]]
- [[Baseline aleatorio]] · [[Baseline de popularidad]] · [[Recomendador basado en contenido]]
- [[Requisitos - Experimentacion y evaluacion]]
La inicialización de colecciones preexistentes se realiza con el comando idempotente
`enqueue_recommendation_refreshes`, que solo crea la revisión y el trabajo pendiente.
La limpieza de cuentas del 2026-09-09 dejó 600 usuarios sintéticos, tres cuentas demo y la
cuenta personal simulada `felipe`. Se eliminaron siete cuentas residuales de pruebas E2E/probes,
sin entradas ni copias.

## Comprobación de recomendaciones publicadas — 2026-09-09

Cada estantería web publica como máximo los 20 resultados con mayor puntuación.
Esta profundidad de producto no altera la evaluación offline: sus métricas se
calculan para `K = 5`, `K = 10` y `K = 20`.

La elegibilidad global ya es estricta para todos los algoritmos: obra gobernada,
fecha no futura, ausencia en la colección, `rating` de usuario IGDB no nulo y
`total_rating_count >= 10`. Por tanto, ni los ranking de contenido ni la
heurística de género pueden publicar una obra sin nota IGDB o con un volumen
inferior al umbral. El snapshot anterior de `felipe` se conserva hasta el
próximo cambio de colección, momento en que los seis workers publicarán el
bundle conforme a este contrato.
