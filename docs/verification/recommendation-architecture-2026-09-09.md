# Contrato compartido de algoritmos de recomendación — 2026-09-09

## Alcance

La comparación offline y la página de recomendaciones comparten el catálogo
publicable definido por `apps/api/recommendations/published.py`. No hay una
implementación, conjunto de señales ni pesos alternativos para el worker web:
el runner llama a `rank_content_v1` con los mismos `algorithm_id` y el mismo
`ALGORITHM_REGISTRY` que consumen los workers personales.

Los cinco algoritmos comparados y publicados son:

| `algorithm_id` | Estantería | Worker dedicado |
|---|---|---|
| `content-cbf-weighted-v1` | Afinidad por contenido | `recommendation-worker-weighted` |
| `content-cbf-multiplicative-v1` | Afinidad equilibrada | `recommendation-worker-multiplicative` |
| `content-cbf-twostage-v1` | Afinidad en dos etapas | `recommendation-worker-twostage` |
| `content-cbf-neg-v1` | Afinidad con tus preferencias en cuenta | `recommendation-worker-negative` |
| `recency-v1` | Novedades afines a ti | `recommendation-worker-recency` |

`random-v1` y `popularity-v1` son baselines de evaluación: se calculan para
interpretar los resultados de investigación, pero no son recomendaciones
personales y por ello no tienen worker ni estantería de producto.

`genre-taste-v1` es una heurística complementaria de producto. Tiene el
worker `recommendation-worker-genre` y sus estanterías por género, pero no se
presenta como variante de la comparación de contenido.

## Señales y pesos congelados en esta configuración

La similitud de contenido usa `fs-v5`. Sus pesos de faceta, antes de la
normalización coseno, son: género 0,50; plataforma 0,25; saga/franquicia 0,15;
desarrollador 0,10. Una faceta ausente se omite para esa obra; no se imputa.

PopScore usa `igdb-engagement-weighted-v2`: visitas 0,40; jugando 0,25;
jugado 0,25; quiere jugar 0,10. Solo existe si están disponibles las cuatro
primitivas normalizadas de IGDB.

La elegibilidad de recomendación es más estricta que la pertenencia al
catálogo: una obra debe estar en el corpus gobernado, tener fecha no futura,
`rating` de usuario IGDB no nulo y `total_rating_count >= 10`. Las obras que
no cumplen alguno de esos requisitos continúan visibles en el catálogo, pero
no pueden aparecer en ningún algoritmo ni estantería de recomendaciones.

Las variantes `content-cbf-weighted-v1`, multiplicativa, dos etapas y
negativa conservan sus fórmulas versionadas en
`recommendations/content/variants.py`. `recency-v1` añade recencia a las
señales de contenido, rating externo, volumen y PopScore con pesos 0,45;
0,20; 0,10; 0,10; 0,15 respectivamente. El rating del usuario forma el perfil
de preferencia; no se suma de nuevo como rating del candidato.

## Profundidad de presentación

Cada estantería publicada calcula y entrega como máximo los **20** juegos con
mayor puntuación de su algoritmo. Esta profundidad de presentación es
independiente de los valores `K = 5, 10, 20` empleados exclusivamente para
las métricas de la evaluación offline.

## Publicación y consistencia

Un cambio en la colección encola seis trabajos, uno por sección publicada.
Cada worker reclama únicamente su `algorithm_id`. Sus resultados permanecen
privados hasta que los seis han terminado correctamente; entonces se crea y
activa un único `RecommendationSnapshot`. Si cambia la colección o la huella
de configuración durante el cálculo, el resultado se marca obsoleto y no
puede sustituir al snapshot anterior.

La huella de configuración incluye versión de features, pesos de faceta,
fórmula y pesos de PopScore, y los parámetros de cada variante. Por tanto, un
cambio de arquitectura o pesos no puede reutilizar silenciosamente una
recomendación calculada con la configuración anterior.

La rejilla de 24 configuraciones de `docs/methodology/protocol.json` conserva
su función de espacio de exploración y validación metodológica. No es un
conjunto adicional de estanterías ni de workers: el conjunto realmente
ejecutado para comparar y publicar es el catálogo versionado de cinco
algoritmos anterior.

## Verificación

- `pytest /workspace/apps/api/recommendations/tests -q`: 86 passed.
- Pruebas dirigidas de PopScore, vectores y cola: 27 passed.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `docker compose -f infra/compose.yaml config --quiet`: configuración de los
  seis workers válida.
