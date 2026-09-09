# Contrato compartido de algoritmos de recomendación — 2026-09-09

## Alcance

La comparación offline y la página de recomendaciones comparten el catálogo
publicable definido por `apps/api/recommendations/published.py`. No hay una
implementación, conjunto de señales ni pesos alternativos para el worker web:
el runner y los workers consumen el mismo catálogo versionado de IDs y los
rankers compartidos; las variantes de contenido usan `rank_content_v1` y las
de Fase 4 sus rankers colaborativo e híbrido equivalentes.

Las once variantes de contenido y los dos algoritmos de Fase 4 comparados y publicados son:

| `algorithm_id` | Estantería | Worker dedicado |
|---|---|---|
| `content-cbf-weighted-v1` | Afinidad por contenido | `recommendation-worker-weighted` |
| `content-cbf-multiplicative-v1` | Afinidad equilibrada | `recommendation-worker-multiplicative` |
| `content-cbf-twostage-v1` | Afinidad en dos etapas | `recommendation-worker-twostage` |
| `content-cbf-neg-v1` | Afinidad con tus preferencias en cuenta | `recommendation-worker-negative` |
| `content-cbf-weighted-pop-v1` | Afinidad por contenido y popularidad | `recommendation-worker-weighted-pop` |
| `content-cbf-multiplicative-pop-v1` | Afinidad equilibrada con popularidad | `recommendation-worker-multiplicative-pop` |
| `content-cbf-twostage-pop-v1` | Afinidad en dos etapas con popularidad | `recommendation-worker-twostage-pop` |
| `content-cbf-neg-pop-v1` | Afinidad con preferencias y popularidad | `recommendation-worker-negative-pop` |
| `recency-v1` | Novedades afines a ti | `recommendation-worker-recency` |
| `content-cbf-mmr-v1` | Afinidad diversa por contenido | `recommendation-worker-mmr` |
| `content-cbf-mmr-pop-v1` | Afinidad diversa con popularidad | `recommendation-worker-mmr-pop` |
| `cf-user-knn-v1` | Coincidencia con usuarios similares | `recommendation-worker-collaborative` |
| `hybrid-weighted-cf-v1` | Afinidad híbrida contenido + usuarios | `recommendation-worker-hybrid` |

`random-v1` y `popularity-v1` son baselines de evaluación: se calculan para
interpretar los resultados de investigación, pero no son recomendaciones
personales y por ello no tienen worker ni estantería de producto.

`genre-taste-v1` es una heurística complementaria de producto. Tiene el
worker `recommendation-worker-genre` y una estantería por género, pero no se
presenta como variante de la comparación de contenido.

## Señales y pesos congelados en esta configuración

La señal de candidato `rating_confidence` v3 es compartida por el producto y la
evaluación offline. Para una obra con rating IGDB observado, usa directamente
ese rating con potencia 2 (`rating_quality = (rating / 100)^2`) y después lo ajusta con el volumen
normalizado logarítmicamente de `total_rating_count`: `rating_quality * (0,80 +
0,20 * rating_volume)`. Así las notas altas se separan más y una nota alta con
muchas valoraciones conserva ventaja, sin permitir que el volumen sustituya a
la calidad. `display_rating` y las valoraciones SavePoint no entran en este
cálculo. El perfil de rating por género solo se usa como fallback cuando la obra
no tiene rating IGDB observado, y queda marcado en `rating_term_is_fallback`.

La similitud de contenido usa `fs-v9` y la regla `facet-similarity-v5`. Género y
plataforma forman el núcleo con pesos 0,50 y 0,25. Su afinidad combina cobertura
ponderada del perfil con precisión de la obra mediante una media F0,5: la
precisión tiene más influencia que la cobertura, por lo que una obra que declara
muchos géneros o plataformas necesita que una proporción mayor de ellos coincida.
Saga/franquicia y desarrollador usan pesos máximos 0,02 y 0,015, y actúan como
bonus positivos solo cuando coinciden con valores presentes en el perfil
 ponderado del usuario. El bonus opcional máximo es 0,035; tener una saga o
desarrollador cualquiera no aporta puntos y una faceta ausente no se imputa ni
penaliza.

PopScore usa `igdb-engagement-weighted-v2`: visitas 0,40; jugando 0,25;
jugado 0,25; quiere jugar 0,10. Solo existe si están disponibles las cuatro
primitivas normalizadas de IGDB.

En las variantes que incluyen PopScore, su influencia publicada es 0,20. En
Weighted-Pop y Negative-Pop comparte la suma con contenido 0,55 y
rating-confidence 0,25; en Multiplicative-Pop usa `swing = 0,20`; en
Two-Stage-Pop forma el desempate con pesos 0,80 para rating-confidence y 0,20
para PopScore. Recency mantiene 0,40 para recencia y asigna 0,20 a cada una de
contenido, rating-confidence y PopScore. La ausencia se imputa a 0,0.

La elegibilidad de recomendación es más estricta que la pertenencia al
catálogo: una obra debe estar en el corpus gobernado, tener fecha no futura,
`rating` de usuario IGDB no nulo y `total_rating_count >= 5`. En el corpus
`2026.09.2` esto produce `13.618` candidatas sobre `190.479` obras gobernadas.
Las obras que
no cumplen alguno de esos requisitos continúan visibles en el catálogo, pero
no pueden aparecer en ningún algoritmo ni estantería de recomendaciones.

Las variantes `content-cbf-weighted-v1`, multiplicativa, dos etapas y
negativa conservan sus fórmulas versionadas en
`recommendations/content/variants.py`. La valoración personal de cada semilla
modula el perfil con intensidad cuadrática `(rating_half_steps / 10)^2`, además
del peso de estado (`completed = 3`, `playing = 2`); por eso una valoración alta
aporta más evidencia que una valoración simplemente positiva y la repetición de
un género acumula peso. `recency-v1` añade recencia a las señales de contenido,
rating-confidence y PopScore con pesos 0,30; 0,20; 0,10; y 0,40 respectivamente.
La recencia usa años naturales: el año del corte vale 1,0 y cada año anterior
vale 0,35 veces el anterior. El volumen ya está compuesto dentro de
`rating_confidence`, por lo que no se suma de nuevo. El rating del usuario forma
el perfil de preferencia; no se suma de nuevo como rating del candidato.

## Profundidad de presentación

Cada estantería publicada calcula y entrega como máximo los **20** juegos con
mayor puntuación de su algoritmo. Esta profundidad de presentación es
independiente de los valores `K = 5, 10, 20` empleados exclusivamente para
las métricas de la evaluación offline.

La heurística complementaria `genre-taste-v1` ya no genera varias estanterías
deterministas. Selecciona el género que aparece en más entradas de la
biblioteca (empate por `slug`), calcula hasta 20 candidatas de ese único género
y expone una sola estantería. La actividad y la valoración del usuario no
pueden desplazar esa selección por frecuencia.
Sus resultados se ordenan por la puntuación exacta de gusto descendente;
la valoración IGDB solo desempata y los empates finales usan el slug canónico.

## Publicación y consistencia

Un cambio en la colección encola quince trabajos, uno por sección publicada.
Cada worker reclama únicamente su `algorithm_id`. Sus resultados permanecen
privados hasta que los quince han terminado correctamente; entonces se crea y
activa un único `RecommendationSnapshot`. Si cambia la colección o la huella
de configuración durante el cálculo, el resultado se marca obsoleto y no
puede sustituir al snapshot anterior.

La huella de configuración incluye versión de features, versión de regla de
similitud, pesos de faceta,
fórmula y pesos de PopScore, y los parámetros de cada variante. Por tanto, un
cambio de arquitectura o pesos no puede reutilizar silenciosamente una
recomendación calculada con la configuración anterior.

Cuando una mutación crea una revisión posterior, los trabajos en cola o en
ejecución de revisiones/configuraciones anteriores se marcan obsoletos de
inmediato. Los rankers comprueban cooperativamente esa condición durante los
bucles costosos, abandonan el cálculo desfasado y cada worker dedicado reclama
el trabajo de su mismo algoritmo para la revisión más reciente. Ningún trabajo
obsoleto puede publicarse.

La rejilla de 31 configuraciones de `docs/methodology/protocol.json` conserva
su función de espacio de exploración y validación metodológica. No es un
conjunto adicional de estanterías ni de workers: el conjunto realmente
ejecutado para comparar y publicar es el catálogo versionado de catorce
variantes publicables: conserva los baselines anteriores, añade las cuatro
variantes PopScore descritas arriba, las dos variantes MMR de contenido y
`hybrid-mmr-v1`.

## Variantes PopScore publicables — actualización 2026-09-09

La arquitectura actual conserva los cuatro baselines de contenido y añade cuatro
variantes paralelas que incorporan PopScore: suma ponderada, combinación
multiplicativa, dos etapas y suma con señal negativa. Cada variante usa el mismo
`rank_content_v1`, la misma señal `rating_final` y sus pesos versionados en
`ALGORITHM_REGISTRY`; por tanto, la comparación offline y la web ejecutan exactamente
la misma fórmula. `recency-v1` también aplica esta política de PopScore y mantiene
`recency_score` como señal adicional.

En las cinco variantes que usan PopScore, una obra sin las cuatro primitivas de
popularidad recibe `popscore = 0.0` mediante `popscore_missing_floor`, sin
renormalizar los pesos. El payload conserva `popscore_imputed = true` para hacer
auditable la imputación. En la variante multiplicativa el rango es 0,85–1,15; en
las variantes aditivas el cero es una contribución/penalización real, y en dos
etapas solo afecta al desempate dentro de la banda de similitud.

El producto publica una estantería por cada una de las catorce variantes personales,
además de la estantería de género y la de DLC. Hay un worker dedicado por variante:
los nuevos servicios se añaden al catálogo existente y todos comparten la
revisión de colección y la publicación atómica del snapshot.

## Verificación

- `pytest /workspace/apps/api/recommendations/tests /workspace/apps/api/evaluation/tests -q`: 192 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec vitest run tests/recommendations.test.ts`: 9 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit`: correcto.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.

## Variantes MMR

Se añaden dos variantes publicables: `content-cbf-mmr-v1`, basada en Weighted,
y `content-cbf-mmr-pop-v1`, basada en Weighted-Pop. Primero calculan la
relevancia de su algoritmo base y despues aplican MMR sobre el pool de las 100
mejores candidatas, o cinco veces K cuando sea mayor. Con `lambda = 0,80`, cada
seleccion maximiza `0,80 * relevancia - 0,20 * similitud_maxima` frente a los
elementos ya seleccionados. La similitud es el coseno de los vectores fs-v9.
El primer elemento siempre es el de mayor relevancia base; las siguientes
posiciones reducen redundancia sin modificar las puntuaciones base.

## Fase 4: colaborativo e híbrido — actualización 2026-09-09

La arquitectura añade tres algoritmos personales, sin modificar las once
variantes de contenido existentes:

- `cf-user-knn-v1` centra las valoraciones explícitas de `LibraryEntry` por la
  media de cada usuario y calcula coseno sobre al menos dos obras valoradas en
  común. Usa los 20 vecinos positivos más similares y predice cada candidata
  con la media ponderada de sus valoraciones. Si no hay vecindario suficiente,
  usa la frecuencia global de interacción de la población de referencia.
- `hybrid-weighted-cf-v1` combina `0,60 * content-cbf-weighted-v1` y
  `0,40 * cf-user-knn-v1`. Cuando no existe señal colaborativa, conserva el
  resultado de Weighted como fallback explícito.
- `hybrid-mmr-v1` reutiliza esa relevancia híbrida y aplica MMR sobre el pool
  `max(100, 5 * K)`, con `lambda = 0,80`, coseno de `fs-v9` y publicación de 20
  resultados.

En la web, la referencia colaborativa excluye al usuario actual y cada
algoritmo tiene su propio worker y estantería. En offline, la referencia es
exclusivamente el split `train`, para impedir fuga desde validación o test.
Ambos caminos reciben el mismo manifiesto de candidatas, exclusiones, corpus y
semillas. La configuración se identifica con protocolo v10.

La evaluación offline se ejecuta con `run_evaluation_parallel`: crea un proceso
aislado por algoritmo, recoge estado, error y duración individual, y conserva
el tiempo total de pared y la suma de tiempos de workers. Si falla uno, el
artefacto queda marcado como fallido y no se registra el marcador de test.

## Frontera metodológica de la Fase 4 — 2026-09-09

La comparación inicial de la Fase 4 implementaba únicamente `cf-user-knn-v1` y
`hybrid-weighted-cf-v1`. Esta decisión no altera las variantes de contenido ya
aceptadas, incluidas `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1`. La fase
mantiene así un conjunto acotado de comparadores que puede auditarse con el
corpus controlado y sintético disponible, valoraciones explícitas, el protocolo
congelado, el contrato de candidatos y exclusiones, y el presupuesto de tuning
ya fijado.

Quedan fuera del alcance metodológico actual Item-KNN, los recomendadores
neuronales y otros modelos complejos. El corpus controlado y sintético no
aporta una base suficiente para atribuir diferencias a esos modelos sin
introducir más supuestos; el uso de valoraciones explícitas favorece que la
señal colaborativa vigente sea legible; y el protocolo congelado exige
comparadores reproducibles dentro del mismo particionado, semillas y
presupuesto. Añadir arquitecturas con más grados de libertad de tuning también
ampliaría el espacio de decisiones y dificultaría separar una mejora del
algoritmo de una ventaja de ajuste. La exclusión es, por tanto, una decisión de
alcance y de validez de esta fase, no una afirmación de inferioridad
algorítmica. No genera artefactos ejecutables ni resultados comparables para
ninguno de esos modelos en esta fase.

### `hybrid-mmr-v1`: propuesta posteriormente autorizada

Como línea de trabajo posterior se definió `hybrid-mmr-v1`, que fue autorizada
y se implementó en la actualización del 2026-09-10. Primero calcula la relevancia de
`hybrid-weighted-cf-v1` con la composición exacta
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`; cuando falta señal
colaborativa, conserva el fallback Weighted ya definido. Después aplica la
misma regla MMR de contenido sobre las 100 mejores candidatas o `5 * K` cuando
sea mayor: el primer elemento es el de mayor relevancia base y cada selección
posterior maximiza `0,80 * relevancia - 0,20 * similitud_maxima`, con
`lambda = 0,80` y similitud coseno sobre `fs-v9`. La profundidad de presentación
propuesta es de 20 resultados.

Esta propuesta se distingue de `content-cbf-mmr-v1`, que reordena la relevancia
Weighted de contenido, y de `content-cbf-mmr-pop-v1`, que reordena
Weighted-Pop; también se distingue de `hybrid-weighted-cf-v1`, que combina las
señales pero no aplica la etapa MMR. La implementación actual tiene worker,
estantería, registro y entrada en el runner offline, aunque todavía no tiene
resultados de evaluación de los 400 usuarios. Cualquier trabajo futuro deberá
conservar el corpus, las exclusiones, las semillas y el contrato de evaluación
vigentes, y documentar por separado cualquier cambio.

## Actualización v10: rating bayesiano y confianza explícita

La señal global usa `rating-confidence-v5-final` tanto en web como en
evaluación offline. Se calcula `rating_bayes = (n * rating_igdb + 25 *
media_corpus) / (n + 25)`, `rating_quality = (rating_bayes / 100)^2`,
`rating_confidence = n / (n + 25)` y `rating_final = rating_quality *
rating_confidence`. `n` es `total_rating_count`; `media_corpus` es la media IGDB
ponderada por ese recuento en el snapshot congelado. Una candidata de poca
evidencia se contrae hacia la media y además recibe menor confianza. No se
aplica ya un multiplicador de volumen separado.
- `docker compose -f infra/compose.yaml config --quiet`: configuración de los
  catorce workers válida.

## Verificación de la Fase 4

La configuración actual declara 14 workers válidos: 13 secciones personales
y la heurística de género. La actualización de Felipe en la revisión 14
terminó con los 14 trabajos en `succeeded`; el snapshot activo contiene 13
secciones personales y cada una entrega 20 resultados. La regresión backend
completa pasó con 482 tests y TypeScript pasó con `tsc --noEmit`.

## Estado actualizado de la Fase 4 — 2026-09-10

La orden explícita del autor amplía la implementación de la Fase 4 con
`hybrid-mmr-v1`. La variante está implementada en el ranker compartido de web
y offline, tiene worker dedicado, estantería localizada y entrada propia en
la suite de evaluación. No se ha ejecutado todavía la evaluación de los 400
usuarios; esta sección documenta implementación y contrato, no resultados
experimentales.

`hybrid-mmr-v1` reutiliza la relevancia de `hybrid-weighted-cf-v1`:
`0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`. Si no hay vecindad
colaborativa suficiente, conserva el fallback Weighted. Sobre esa relevancia
ordena un pool de `max(100, 5 * K)` candidatas con MMR, `lambda = 0,80` y
similitud coseno de `fs-v9`; la publicación entrega 20 resultados. Se
distingue de `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1` porque su
relevancia de partida incorpora colaboración explícita.

### Señal global de rating v5

Desde el protocolo v10, todos los rankers content-based y los híbridos que
consumen calidad global usan una única señal observada:

`rating_bayesian_normalized = ((n * rating_igdb + m * corpus_prior) / (n + m)) / 100`

`rating_quality = rating_bayesian_normalized ^ 2`

`rating_confidence = n / (n + m)`

`rating_final = rating_quality * rating_confidence`

`n` es `total_rating_count` y `m = 25` es una constante congelada. El rating
bayesiano aporta calidad estabilizada hacia la media del corpus y la confianza
aporta una penalización explícita cuando hay poca evidencia. `rating_volume`
se conserva como evidencia explicativa, pero no vuelve a multiplicarse. La
señal no sustituye el rating personal de las semillas ni las valoraciones
explícitas que usa `cf-user-knn-v1`.

El contrato v10 incorpora la fórmula, `m = 25`, `hybrid-mmr-v1`, sus pesos, el
pool y MMR, y eleva la rejilla declarada a 31 configuraciones. Web y offline
leen el mismo ranker y los mismos snapshots, por lo que el cambio de señal no
puede producir dos arquitecturas distintas.
