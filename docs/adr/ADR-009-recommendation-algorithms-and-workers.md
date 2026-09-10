<!-- generated-by: gsd-doc-writer -->

# ADR-009: Algoritmos de recomendación y workers paralelos

**Estado:** aceptado  
**Fecha:** 2026-09-10  
**Autor de la decisión:** Felipe

## Contexto

SavePoint necesita una base reproducible para el TFG que compare contenido,
colaboración e híbridos y que, a la vez, entregue estanterías personalizadas
en web. Las etiquetas editoriales curadas son la señal semántica principal y
deben incorporar IDF por rareza sin que el número de tags favorezca por sí solo
a una obra. El catálogo de variantes, la evaluación offline y la web deben
compartir candidatos, snapshots, fórmulas y versiones.

El sistema también debe recalcular varias secciones tras un cambio de
biblioteca sin bloquear una petición HTTP ni publicar una mezcla de revisiones.

## Alternativas consideradas

- Usar géneros, keywords, Theme, Perspective y GameMode crudos como dimensiones
  independientes.
- Usar solo coseno o una suma con pesos iguales para todo el contenido.
- Incorporar raw rating, volumen o PopScore sin transformación bayesiana o
  normalización por corpus.
- Implementar únicamente un algoritmo complejo, por ejemplo una factorización
  o una red neuronal.
- Ejecutar todas las secciones secuencialmente en una única petición o en un
  único worker.
- Introducir Redis como fuente de verdad de la cola.

## Decisión

Se adopta un catálogo versionado compuesto por:

- `random-v1` y `popularity-v1` como baselines offline;
- once variantes de contenido, incluyendo cuatro combinaciones con PopScore,
  una variante de recencia y dos capas MMR;
- `cf-user-knn-v1`, `hybrid-weighted-cf-v1` y `hybrid-mmr-v1`;
- `tag-taste-v1` como heurística de producto fuera de la comparación académica.

El vector de contenido usa `tag = 0,75`, `platform = 0,25`, y bonuses máximos
de `franchise = 0,02` y `developer = 0,015`. Los tags usan:

```text
idf(t) = ln((N + 1) / (df_t + 1)) + 1
w(tag:t) = 0,75 * idf(t) / sqrt(sum(idf(tag_j)^2))
```

La similitud de tags/plataformas usa una afinidad F0,5 que prioriza precisión de
la candidata. Franquicia y desarrollador solo confirman coincidencias ya
presentes en el perfil. Ratings externos usan shrinkage bayesiano con `m = 25`,
calidad cuadrática y confianza `n/(n+25)`. PopScore normaliza por snapshot y
combina `Visits`, `Playing`, `Played` y `Want to Play` con pesos
`0,40/0,25/0,25/0,10`. MMR se aplica después de la relevancia con
`lambda = 0,80`.

El colaborativo es user-KNN con ratings explícitos centrados por la media,
mínimo de dos obras comunes y máximo de 20 vecinos positivos. El híbrido usa
`0,60` de contenido Weighted y `0,40` de colaboración, con fallback de
contenido cuando no hay vecindad.

La web encola una sección por algoritmo publicado en PostgreSQL y ejecuta un
worker dedicado por `algorithm_id`. Los resultados solo pasan a un
`RecommendationSnapshot` cuando todas las secciones de la revisión han
terminado correctamente. Un cambio de revisión o de huella vuelve obsoletos
los cálculos antiguos. La evaluación offline usa un proceso por algoritmo,
valida que todos comparten contrato y no marca el test como consumido si uno
falla.

## Evidencia y fuentes

- Especificación completa y fórmulas:
  [`docs/methodology/recommendation-algorithms.md`](../methodology/recommendation-algorithms.md).
- Registro de variantes:
  `apps/api/recommendations/content/variants.py`.
- IDF y pesos de features:
  `apps/api/recommendations/content/features.py`.
- User-KNN e híbridos:
  `apps/api/recommendations/collaborative.py` y
  `apps/api/recommendations/hybrid.py`.
- Publicación y cola:
  `apps/api/recommendations/published.py`, `jobs.py`, `signals.py` y `models.py`.
- Evaluación paralela:
  `apps/api/evaluation/runner.py` y
  `apps/api/evaluation/management/commands/run_evaluation_parallel.py`.
- Contrato congelado:
  [`protocol.json`](../methodology/protocol.json).
- Base científica del diseño, con la separación entre principios publicados y
  parámetros propios del corpus:
  [`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md#15-base-científica-de-las-decisiones).
- Referencia seminal de recomendación basada en contenido:
  [Pazzani y Billsus, DOI 10.1007/978-3-540-72079-9_10](https://doi.org/10.1007/978-3-540-72079-9_10).
- Referencia de filtrado colaborativo por usuarios:
  [Resnick et al., GroupLens, DOI 10.1145/192844.192905](https://doi.org/10.1145/192844.192905).
- Referencia de sistemas híbridos:
  [Burke, DOI 10.1023/A:1021240730564](https://doi.org/10.1023/A:1021240730564).
- Referencia de MMR:
  [Carbonell y Goldstein, DOI 10.1145/290941.291025](https://doi.org/10.1145/290941.291025).
- Referencia de evaluación de listas y nDCG:
  [Järvelin y Kekäläinen, DOI 10.1145/582415.582418](https://doi.org/10.1145/582415.582418).
- Referencia de IDF y ponderación de términos:
  [scikit-learn, TF-IDF term weighting](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting).
- Referencia de transacciones atómicas:
  [Django database transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

## Consecuencias

La decisión produce un sistema interpretable, con una señal editorial
dominante, control de etiquetas frecuentes, candidatos idénticos para la
comparación y publicación sin estados parciales. También permite atribuir una
diferencia entre variantes a la combinación estudiada y no a un cambio
silencioso de corpus o de features.

El coste es mantener varias variantes, snapshots y workers, y recalcular IDF al
cambiar el corpus. La población sintética y leave-one-out limitan la validez
externa. No se afirma que Item-KNN, factorización, modelos neuronales o grafos
sean peores; quedan fuera por alcance, datos y reproducibilidad.

## Reversibilidad

La decisión es reversible mediante nuevas versiones de feature set, regla de
similitud o algoritmo. No se deben modificar silenciosamente los IDs ni el
protocolo ya congelado: cualquier fórmula nueva debe recibir versión, pruebas,
huella de configuración, evidencia y una comparación bajo un split no
consumido. La cola puede cambiar de backend más adelante si un benchmark
demuestra que PostgreSQL no satisface la latencia, pero el snapshot atómico y
la separación entre cálculo y publicación deben conservarse.

## Aprobación y revisión

La decisión queda aceptada por **Felipe** el 2026-09-10. Debe revisarse si
cambia la taxonomía editorial, si se incorpora una nueva fuente de señales, si
la cobertura colaborativa deja de ser suficiente o si una evaluación con datos
reales justifica comparar modelos de mayor complejidad. La revisión debe
actualizar simultáneamente este ADR, el documento metodológico, el protocolo y
la nota enlazada del vault de Obsidian.
