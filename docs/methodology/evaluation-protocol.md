# Protocolo de evaluación offline

Este documento describe, de forma general, cómo se comparan los recomendadores de SavePoint. Es la lectura en prosa del contrato legible por máquina [`protocol.json`](./protocol.json), que es el que valida el código (`apps/api/evaluation/protocol.py`) y el que manda si hay una discrepancia.

## Estado y naturaleza de la evidencia

- **Contrato vigente:** `protocol.json` está en la versión 16 del protocolo (congelado el 2026-09-12).
- **Evidencia publicada:** el artefacto citado en la memoria corresponde a la versión 15 del protocolo y a una única ejecución sobre la partición de prueba. Las ejecuciones válidas son las de las versiones 12, 14 y 15; la versión 13 se descartó por un defecto del arnés (candidatas duplicadas). El conjunto de características de la evidencia publicada es `fs-v12`; el `fs-v13` del contrato vigente no se ha evaluado.
- **Simulación, no usuarios reales:** todos los usuarios del arnés son sintéticos, generados de forma determinista a partir de arquetipos. Todo artefacto lleva `simulation: true` y una cadena `limitation` explícita: los resultados describen cómo se ordenan los algoritmos sobre esa población simulada, no la satisfacción de personas reales.
- **Reversibilidad:** una vez que una comparación citada referencia `protocol.json` por su hash, cambiar la relevancia, los valores de K, la partición, las métricas o el presupuesto de ajuste invalida esa comparación. Por eso cualquier cambio sube la versión del protocolo y exige un nuevo consumo del test.

## Población y partición

La población experimental son 400 usuarios sintéticos regenerables por semilla: 10 sin historial y 390 con una biblioteca de 10 a 20 entradas. Cada usuario elige sus propias etiquetas de contenido preferidas y solo se incluyen obras con al menos una valoración externa, con una selección sin reemplazo que pondera más las obras con más valoraciones.

Se reparten por usuario, no por ítem, en tres subconjuntos disjuntos con una semilla fija: **240 de entrenamiento, 80 de validación y 80 de prueba**. Las métricas finales se calculan solo sobre los usuarios de prueba. El entrenamiento sirve de población de referencia para el filtrado colaborativo y de base de frecuencias para la novedad. De los 80 usuarios de prueba, 79 tienen al menos un ítem relevante elegible y son los evaluados; el artefacto registra 80 solicitados, 79 evaluados y 1 omitido.

## Relevancia, partición de ítems y candidatas

- **Relevancia.** Una obra de la biblioteca es relevante si su estado es «terminado» o su valoración es de al menos 3,5 sobre 5 (7 medios puntos). Las obras que se retienen deben además tener una valoración externa agregada de al menos 70 puntos.
- **Leave-fraction-out.** Para cada usuario se localiza su etiqueta de contenido con más peso y se retira de ese grupo un número de obras igual al techo del 30 % de su tamaño, nunca menos de una, retrocediendo de una en una si la retirada desplazaría esa etiqueta del primer puesto del perfil restante. Si ese mecanismo no se puede construir para un usuario, se recurre al *leave-one-out* simple de un único ítem; solo queda fuera quien no tiene ningún positivo elegible.
- **Candidatas.** El universo que puede entrar en cualquier algoritmo es un subconjunto explícito del corpus gobernado: obras con fecha no futura, con valoración de usuarios de IGDB y con al menos 5 valoraciones totales. Las demás siguen en el catálogo y la colección, pero no se recomiendan ni cuentan en las métricas. El conjunto de candidatas de un usuario es ese universo menos su biblioteca restante más los ítems retirados, que siempre se reincorporan, y es **idéntico para todos los algoritmos**.
- **Sin filtración.** Ningún ítem retenido participa en la construcción del perfil; su presencia entre las candidatas permite medir si se recupera.

## Métricas

- Se reporta en **K = 5, 10 y 20**; la métrica titular es `nDCG@10`.
- **Acierto y ranking:** `precision@k`, `recall@k`, `ndcg@k` y `map@k`, escritas a mano y verificadas con casos de respuesta conocida (`apps/api/evaluation/tests/test_metrics.py`). Con varios ítems retenidos por usuario, `Recall@K` deja de ser binario.
- **Más allá del acierto:** diversidad intra-lista, novedad y número de ítems recomendados, que se conservan por usuario y pueden agregarse por cohorte sin volver a ejecutar los algoritmos; y cobertura de catálogo, concentración (HHI) y cobertura de predicción, que dependen del conjunto de listas completo y se publican solo globales, porque no se guardaron las listas completas por usuario. Así no se fabrica una desagregación no auditable.

## Señales de los algoritmos

- **Calidad externa.** Se usa la valoración de IGDB con un ajuste bayesiano: `rating_bayesiano = (n·rating + m·media_corpus)/(n + m)` con `m = 25`, donde `n` es el número total de valoraciones y la media es la del corpus congelado ponderada por ese número. La calidad es ese valor normalizado elevado al cuadrado y la señal final es `calidad × n/(n + m)`. Se aplica una sola vez en cada variante que consume calidad externa, y no a las valoraciones personales ni a la similitud colaborativa.
- **Similitud de contenido.** Un conjunto de características versionado combina etiquetas y plataformas como núcleo, con una media F0,5 (`beta = 0,5`) que prioriza la precisión de la candidata, y tema, modo, característica, saga y desarrollador solo como confirmaciones positivas cuando coinciden con el perfil del usuario. Cada familia de etiquetas tiene su propio IDF suavizado y los metadatos ausentes no se imputan ni penalizan.
- **Popularidad.** PopScore agrega primitivas de interés normalizadas y su ausencia se imputa a 0,0, no a una señal neutra.
- **Reordenación.** Las variantes MMR puntúan el mismo conjunto que su algoritmo base y reordenan las mejores candidatas (las 100 primeras o cinco veces K, lo que sea mayor) con `lambda = 0,80`.

## Algoritmos comparados

Dieciséis variantes sobre el mismo protocolo: `random-v1`, `popularity-v1`, `recency-v1`, las variantes de contenido (`content-cbf-weighted`, `multiplicative`, `twostage`, `neg` y sus versiones con PopScore), las dos MMR (`content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`), `cf-user-knn-v1`, `hybrid-weighted-cf-v1` y `hybrid-mmr-v1`. Se ejecuta un proceso por algoritmo sobre los mismos manifiestos y el artefacto registra el tiempo de cada proceso, el tiempo total de pared y los fallos, sin publicar resultados parciales como si fueran una comparación completa. Desde el cierre de la fase 3 el ejecutor paralelo captura además, en las ejecuciones nuevas, el entorno no sensible (Python, plataforma, CPU, versiones de paquetes) y los recursos del proceso; no se atribuye retroactivamente a la v15, porque una medición posterior no sería una observación histórica válida.

## Ajuste de hiperparámetros y aislamiento del test

El protocolo declara, antes de ejecutar nada, una rejilla de ajuste de como máximo 31 configuraciones que debía puntuarse solo sobre validación con `nDCG@10`. No se conserva ninguna ejecución de esa rejilla: los parámetros de las dieciséis variantes (pesos por familia, `lambda`, pesos de PopScore y demás) son decisiones de diseño justificadas, no valores seleccionados sobre validación ni sobre la prueba.

La partición de prueba se consume **una sola vez por versión del protocolo** (`test_runs: 1`). El consumo queda anotado en un marcador y el cargador se niega a repetirlo salvo que se suba la versión. Eso no equivale a un aislamiento completo: el protocolo se modificó de la versión 12 a la 15 después de ver los resultados de las versiones anteriores, y el consumo único rige dentro de cada versión, no entre ellas.

Las semillas fijas permiten reproducir exactamente el artefacto, pero no permiten afirmar robustez frente a otras poblaciones hasta realizar un estudio de sensibilidad versionado. Repetir el test con otra semilla requiere cambiar protocolo, manifiesto y hash, sin mutar el marcador ya consumido. Los intervalos *bootstrap* del artefacto cuantifican la incertidumbre dentro de la muestra pareada observada, no la variación entre semillas.

## Corpus y huellas

El protocolo apunta al corpus congelado `2026.09.2`. `snapshot_sha256` identifica el snapshot de valoraciones de usuarios y `popscore_snapshot_sha256` identifica las primitivas normalizadas y el compuesto PopScore. El ejecutor toma la versión y ambas huellas de forma explícita y aborta si detecta deriva respecto de los datos congelados.

## Amenazas a la validez

- **Validez externa de los usuarios sintéticos.** Son arquetipos parametrizados, no una muestra de personas reales; sus bibliotecas y valoraciones se generan por semilla a partir de una plantilla de comportamiento. Las conclusiones deben separar la evidencia de simulación de cualquier evidencia sobre usuarios reales.
- **Retención de pocos ítems.** Retirar uno o pocos ítems relevantes convierte la evaluación en un problema de recuperación con poca información por usuario, lo que favorece a los algoritmos que aciertan lo popular u obvio y penaliza poco la diversidad. Las métricas más allá del acierto compensan en parte este sesgo.
- **Fuente única de valoración externa.** La señal de calidad y la relevancia por valoración se apoyan en una única fuente (IGDB, y de forma condicional RAWG). Un sesgo sistemático de esa fuente —comunidades sobre-representadas, inflación de notas en juegos recientes, cobertura desigual— se propaga a ambas señales. La cobertura se documenta en el informe de calidad de datos y en el ADR-008.
- **Circularidad de los arquetipos.** Si los arquetipos se diseñan con las mismas características que consume el recomendador (géneros, plataformas, saga, desarrollador), la evaluación puede medir en parte la coincidencia entre el generador y el modelo. Los arquetipos se fijaron a partir de literatura de simulación de usuarios y se validaron antes de usarlos.
- **Congelación y repetición.** Un error en `protocol.json` descubierto tras una comparación citada no se puede corregir sin invalidarla. La mitigación es el cargador que falla de forma cerrada y sus pruebas, que fijan la forma del contrato y sus invariantes antes de que corra ninguna variante.

## Fuentes

- Contrato: [`protocol.json`](./protocol.json); cargador y guardas de congelación: `apps/api/evaluation/protocol.py`.
- Métricas: `apps/api/evaluation/metrics.py`; partición: `apps/api/evaluation/splits.py`; candidatas: `apps/api/evaluation/candidates.py`; ejecutor: `apps/api/evaluation/runner.py`.
- Pruebas que fijan lo anterior: `apps/api/evaluation/tests/test_protocol.py`, `test_metrics.py`, `test_splits.py` y `test_runner.py`.
- Decisiones relacionadas: [ADR-008](../adr/ADR-008-external-ratings.md) y [ADR-009](../adr/ADR-009-recommendation-algorithms-and-workers.md).
