# Contrato compartido de algoritmos de recomendación — 2026-09-09

## Alcance

La comparación offline y la página de recomendaciones comparten el catálogo
publicable definido por `apps/api/recommendations/published.py`. No hay una
implementación, conjunto de señales ni pesos alternativos para el worker web:
el runner llama a `rank_content_v1` con los mismos `algorithm_id` y el mismo
`ALGORITHM_REGISTRY` que consumen los workers personales.

Las nueve variantes de contenido comparadas y publicadas son:

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

`random-v1` y `popularity-v1` son baselines de evaluación: se calculan para
interpretar los resultados de investigación, pero no son recomendaciones
personales y por ello no tienen worker ni estantería de producto.

`genre-taste-v1` es una heurística complementaria de producto. Tiene el
worker `recommendation-worker-genre` y una estantería por género, pero no se
presenta como variante de la comparación de contenido.

## Señales y pesos congelados en esta configuración

La señal de candidato `rating_confidence` es compartida por el producto y la
evaluación offline. Primero transforma el rating de usuario IGDB con potencia
2 (`rating_quality = (rating / 100)^2`) y después lo ajusta con el volumen
normalizado logarítmicamente de `total_rating_count`: `rating_quality * (0,80 +
0,20 * rating_volume)`. Así las notas altas se separan más y una nota alta con
muchas valoraciones conserva ventaja, sin permitir que el volumen sustituya a
la calidad. `display_rating` y las valoraciones SavePoint no entran en este
cálculo.

La similitud de contenido usa `fs-v6`. Género y plataforma forman el núcleo con
pesos 0,50 y 0,25, normalizados solo entre las facetas disponibles. Saga/
franquicia y desarrollador conservan pesos relativos 0,15 y 0,10, pero actúan
como bonus acotados únicamente cuando coinciden con valores presentes en el
perfil ponderado del usuario. Tener una saga o desarrollador cualquiera no
aporta puntos; una faceta ausente no se imputa ni penaliza.

PopScore usa `igdb-engagement-weighted-v2`: visitas 0,40; jugando 0,25;
jugado 0,25; quiere jugar 0,10. Solo existe si están disponibles las cuatro
primitivas normalizadas de IGDB.

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

Un cambio en la colección encola diez trabajos, uno por sección publicada.
Cada worker reclama únicamente su `algorithm_id`. Sus resultados permanecen
privados hasta que los diez han terminado correctamente; entonces se crea y
activa un único `RecommendationSnapshot`. Si cambia la colección o la huella
de configuración durante el cálculo, el resultado se marca obsoleto y no
puede sustituir al snapshot anterior.

La huella de configuración incluye versión de features, pesos de faceta,
fórmula y pesos de PopScore, y los parámetros de cada variante. Por tanto, un
cambio de arquitectura o pesos no puede reutilizar silenciosamente una
recomendación calculada con la configuración anterior.

Cuando una mutación crea una revisión posterior, los trabajos en cola o en
ejecución de revisiones/configuraciones anteriores se marcan obsoletos de
inmediato. Los rankers comprueban cooperativamente esa condición durante los
bucles costosos, abandonan el cálculo desfasado y cada worker dedicado reclama
el trabajo de su mismo algoritmo para la revisión más reciente. Ningún trabajo
obsoleto puede publicarse.

La rejilla de 28 configuraciones de `docs/methodology/protocol.json` conserva
su función de espacio de exploración y validación metodológica. No es un
conjunto adicional de estanterías ni de workers: el conjunto realmente
ejecutado para comparar y publicar es el catálogo versionado de nueve
variantes publicables: conserva los baselines anteriores y añade las cuatro
variantes PopScore descritas arriba.

## Variantes PopScore publicables — actualización 2026-09-09

La arquitectura actual conserva los cuatro baselines de contenido y añade cuatro
variantes paralelas que incorporan PopScore: suma ponderada, combinación
multiplicativa, dos etapas y suma con señal negativa. Cada variante usa el mismo
`rank_content_v1`, la misma señal `rating_confidence` y sus pesos versionados en
`ALGORITHM_REGISTRY`; por tanto, la comparación offline y la web ejecutan exactamente
la misma fórmula. `recency-v1` también aplica esta política de PopScore y mantiene
`recency_score` como señal adicional.

En las cinco variantes que usan PopScore, una obra sin las cuatro primitivas de
popularidad recibe `popscore = 0.0` mediante `popscore_missing_floor`, sin
renormalizar los pesos. El payload conserva `popscore_imputed = true` para hacer
auditable la imputación. En la variante multiplicativa el rango es 0,85–1,15; en
las variantes aditivas el cero es una contribución/penalización real, y en dos
etapas solo afecta al desempate dentro de la banda de similitud.

El producto publica una estantería por cada una de las nueve variantes de contenido,
además de la estantería de género y la de DLC. Hay un worker dedicado por variante:
los cuatro nuevos se añaden a los seis servicios existentes y todos comparten la
revisión de colección y la publicación atómica del snapshot.

## Verificación

- `pytest /workspace/apps/api/recommendations/tests /workspace/apps/api/evaluation/tests -q`: 181 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec vitest run tests/recommendations.test.ts`: 9 passed.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit`: correcto.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `docker compose -f infra/compose.yaml config --quiet`: configuración de los
  diez workers válida.
