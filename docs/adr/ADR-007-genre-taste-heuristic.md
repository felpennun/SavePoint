# ADR-007: Un heurístico determinista de gusto por géneros para la página de recomendaciones

- **Estado:** Aceptado
- **Fecha:** 2026-09-06
- **Autor de la decisión:** Felipe (página de recomendaciones pedida por el autor, D-04 / REC-10; la frontera heurístico-sobre-modelo la fija `01.1-CONTEXT.md` D-09 y `01.1-RESEARCH.md`)
- **Redacción / evidencia:** agente de ejecución; las reglas de ranking de abajo están enforced por `apps/api/recommendations/tests/test_genre_heuristic.py` (21 tests, ejecutados con `docker compose -f infra/compose.yaml run --rm api pytest`).
- **Fase / Plan:** 01.1 / 01.1-05 · **Requisito:** REC-10 · **Issue de GitHub:** #13
- **Baseline hermano:** [`apps/api/library/popularity.py`](../../apps/api/library/popularity.py) (`rank_popularity_v1`, REC-02) — el agregado no personalizado del que esta página debe ser visiblemente distinta.
- **Sustituido por (futuro):** el recomendador basado en contenido de la Fase 6 (REC-03, `ROADMAP.md`) — ver *Frontera*.

## Contexto

`REC-10` pide "a dedicated recommendations page [that] exposes genre-oriented suggestions reflecting the signed-in user's own recorded tastes, distinct from the public popularity baseline." El autor priorizó esta página como un entregable de **producto** para la Fase 01.1 (D-04).

El trabajo riguroso de recomendadores — una comparación documentada de enfoques basados en contenido, colaborativos e híbridos con artefactos versionados, explicaciones y manejo de arranque en frío — es la **Fase 6 (`REC-03`)**, y va por detrás de la congelación de evaluación comparativa de la Fase 2. Construir aquí algo que se le parezca duplicaría trabajo futuro y difuminaría la narrativa de los dos sistemas en la tesis. `01.1-RESEARCH.md` (tabla "Don't Hand-Roll") es explícito: la página de la Fase 01.1 debe ser *"a stateless, request-time aggregation over `LibraryEntry` rows … mirroring `library/popularity.py`'s shape"*, **no** un modelo entrenado ni un feature store persistido.

El `rank_popularity_v1` existente ya establece el patrón de la casa para un ranking defendible y no-ML: un único queryset resuelto, una tabla de pesos explícita, un desempate determinista y un DTO que siempre declara `algorithm_id` + `generated_at` + `input_snapshot_sha256` + un string `limitation` explícito, para que nunca se confunda con algo más de lo que es.

## Alternativas consideradas

- **Un modelo entrenado basado en contenido / colaborativo ahora.** Rechazado: eso es la Fase 6 (`REC-03`) detrás de la congelación de evaluación de la Fase 2; hacerlo aquí duplica trabajo futuro y difumina la narrativa de la tesis (ver *Contexto* y *Frontera*).
- **Reutilizar `rank_popularity_v1` filtrado por los géneros del usuario.** Rechazado: sigue siendo un agregado público; D-09 exige que la página refleje la actividad *propia del usuario autenticado*, y un estado de historial insuficiente nunca debe caer a un agregado (§6).
- **Persistir un vector de gusto por usuario / feature store.** Rechazado: innecesario para un conteo de frecuencia en tiempo de petición y sin estado, y crearía un artefacto versionado que esta fase explícitamente no debe poseer.
- **`httpx`/async o una librería de recomendadores.** No aplica — no se introduce ninguna dependencia nueva; el heurístico es puro ORM + Python (tabla "Don't Hand-Roll" de `01.1-RESEARCH.md`).

## Decisión

Entregar **`rank_genre_taste_v1(user, limit)`** en una app nueva `apps/api/recommendations/`: un heurístico de frecuencia de géneros determinista, en tiempo de petición y sin estado, acotado estrictamente a un usuario, expuesto en `GET /api/recommendations/genre-taste/` detrás de `IsAuthenticated`. `ALGORITHM_ID = "genre-taste-v1"`.

### 1. Vector de gusto — pesos

Cada fila `LibraryEntry` propia del usuario contribuye un **peso de actividad** a *cada* `Genre` adjunto al `GameWork` de esa entrada:

```
activity_weight(entry) = STATUS_WEIGHT[entry.current_status] + (entry.rating_half_steps or 0) / 10

STATUS_WEIGHT = { completed: 3.0, playing: 2.0, pending: 1.0, abandoned: 0.0, <unset>: 0.0 }
rating contribution  = rating_half_steps / 10   ->  0.1 .. 1.0   (rating nulo = 0.0)

taste_weight[genre] = Σ  activity_weight(entry)   por cada entrada cuya obra lleva `genre`
```

La tabla de estados es una copia deliberada de `_STATUS_WEIGHTS` de `library/popularity.py`, y el término de rating es el mismo `rating_half_steps / 10` que usa el baseline de popularidad — el heurístico personal y el baseline público hablan el mismo idioma de "cuánto cuenta esta interacción". `abandoned` y las entradas sin estado no contribuyen nada: un título del que rebotaste o que no sigues no es evidencia de gusto.

### 2. Ranking de candidatos

Rankear las filas `GameWork` del catálogo por solapamiento sumado de géneros con el vector de gusto:

- **Excluir** toda obra de la que el usuario ya tenga *cualquier* `LibraryEntry` (con estado o sin él).
- **Excluir** `is_dlc = True`.
- **Requerir** al menos un género en común con el vector de gusto (`taste_weight > 0`).
- `score(work) = Σ taste_weight[g]` para `g` en `work.genres ∩ taste_genres`.
- **Desempate:** `canonical_slug` ascendente. Entradas idénticas producen por tanto un orden idéntico.
  - La base de datos ordena por `Sum(CASE …)` en `double precision` IEEE-754, pero las contribuciones de rating son múltiplos de `0.1` (no representables exactamente), así que dos obras con el mismo score *racional* pueden llevar sumas float distintas y caer a un lado u otro de un `LIMIT` ingenuo. El servicio por eso sobre-lee un múltiplo fijo de `limit` (`_CANDIDATE_OVERFETCH = 4`, así que como mucho `50 × 4 = 200` filas candidatas — sigue acotado según la amenaza T-01.1-11), y luego hace el re-score de aritmética exacta y el desempate por `canonical_slug` **autoritativos** en Python antes de truncar a `limit`. El orden de la BD es solo un pre-filtro de candidatos; la semántica del corte documentada se decide en Python (repo-review 2026-09-06, hallazgo L-03).
- Cada ítem de resultado lleva su **evidencia de explicación por solapamiento de géneros**: `matched_genres = [{slug, name, weight}, …]` ordenado por weight desc y luego slug, más `work_id`, `slug`, `title`, `score`.

### 3. Consulta acotada (amenaza T-01.1-11)

La base de datos de desarrollo tiene 312,483 obras / 23 géneros, así que un escaneo ingenuo de solapamiento de géneros es una superficie de DoS. La consulta de ranking se conduce por la **tabla through de la M2M `GameWork.genres`**, filtrada por `genre_id__in=<géneros de gusto>` (el índice `genre_id` auto-creado de la tabla through), agrupada por obra, agregada con una suma `CASE` de los pesos por género, ordenada y **acotada con `LIMIT` en SQL** a `limit × _CANDIDATE_OVERFETCH` (≤ 200; ver la nota de desempate de arriba). Postgres nunca escanea el catálogo completo y el working set nunca es mayor que esa pool de candidatos acotada. No se requiere migración de índice nueva — el índice `genre_id` auto de la tabla through más el `LIMIT` de SQL acotan el escaneo; el índice único de `canonical_slug` sirve el orden de desempate.

### 4. Cota de `limit`

`limit` se clampa a **`[1, 50]`, por defecto `20`**. El endpoint rechaza un `limit` no entero con `400`; un entero fuera de rango se clampa (no se rechaza) a esa cota. El servicio clampa defensivamente también, así que un llamador directo no puede pasar un valor sin acotar.

### 5. Reproducibilidad — `input_snapshot_sha256`

El DTO lleva un SHA-256 sobre un JSON canónico de **(el vector de gusto ordenado) + (la lista de resultados `(slug, score)` ordenada)**. Dos llamadas que hasheen igual son demostrablemente el mismo ranking sobre el mismo snapshot de gusto; cualquier cambio en la actividad del usuario o en el orden producido es siempre visible como un cambio de hash. `generated_at` es un corte de snapshot — solo la actividad con `updated_at <= generated_at` alimenta el vector de gusto — igual que el argumento `cutoff` de `rank_popularity_v1`, así que un ranking puede recomputarse idénticamente a posteriori.

### 6. Historial insuficiente — nunca un fall-back

Cuando el usuario no tiene actividad con estado/rating que lleve género, el resultado es una **forma distinta y explícita**: `insufficient_history: True`, `results: []` y un string `limitation` que dice que la página debe mostrar un estado vacío/de onboarding. **Nunca** cae a `rank_popularity_v1` ni a ningún agregado — D-09 exige que la página refleje la actividad *propia* del usuario autenticado, así que una lista pública disfrazada de "tus recomendaciones" sería un bug de corrección.

### 7. Seguridad (amenaza T-01.1-10)

`RecommendationsView` es `IsAuthenticated` y llama al servicio solo con `request.user`. No acepta ningún parámetro de usuario objetivo. La respuesta se re-proyecta por una allowlist explícita de claves (`algorithm_id`, `generated_at`, `input_snapshot_sha256`, `insufficient_history`, `limitation`, `results`; ítems: `work_id`, `slug`, `title`, `score`, `matched_genres`) para que un cambio futuro en el DTO del servicio no pueda ensanchar silenciosamente el contrato del cable. Las peticiones anónimas reciben `403` sin datos de gusto en el cuerpo.

## Frontera — es una funcionalidad de producto, no la contribución algorítmica de la tesis

`genre-taste-v1` es **deliberadamente más simple** que el recomendador de la Fase 6 y no forma parte de la evaluación comparativa de la Fase 2:

- Es un **conteo de frecuencia sobre una tabla**, no un modelo aprendido. No hay paso de entrenamiento, ni embedding, ni matriz de similitud, ni feature store persistido, ni artefacto que versionar más allá del propio código.
- **No tiene estrategia de arranque en frío** más allá de "decirlo" (§6). El arranque en frío es de la Fase 6.
- **No** reclama calidad predictiva y no debe compararse contra, ni reportarse junto a, la comparación basada en contenido / colaborativa / híbrida de la Fase 6. El string `limitation` de cada respuesta lo dice con palabras para que el frontend y cualquier lector posterior no puedan confundir los dos.
- Su papel en la tesis es hacer que el producto de la Fase 01.1 se lea como un sitio de catalogación real (D-01, D-04) y dar a la Fase 6 un contrato concreto de página y endpoint ya cableado que reemplazar.

## Evidencia y fuentes

- **Tests que lo enforcen:** [`apps/api/recommendations/tests/test_genre_heuristic.py`](../../apps/api/recommendations/tests/test_genre_heuristic.py) — la tabla de pesos, las exclusiones, el desempate (incluido el caso del borde de `limit`), la determinación de `input_snapshot_sha256`, la forma de historial insuficiente y el scoping `IsAuthenticated` están todos fijados por tests.
- **Baseline hermano:** [`apps/api/library/popularity.py`](../../apps/api/library/popularity.py) (`rank_popularity_v1`) — el lenguaje de pesos de estado/rating compartido y la forma de DTO que este heurístico replica.
- **Investigación:** [`.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md`](../../.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md) — la guía "Don't Hand-Roll" que fija esto como una agregación sin estado, no un modelo.
- **Seguimiento de revisión:** `docs/verification/repo-review-2026-09-06.md` (no incluido en el repositorio público) hallazgo L-03 — el desempate float-vs-exacto en el borde de `limit`, resuelto con el sobre-fetch + re-score exacto en Python de §2.
- **Referencias externas:** agregación / expresiones condicionales de Django usadas por la consulta de ranking — `https://docs.djangoproject.com/en/5.2/topics/db/aggregation/` y `https://docs.djangoproject.com/en/5.2/ref/models/conditional-expressions/`; la representación de coma flotante binaria detrás de la nota L-03 — `https://docs.python.org/3/tutorial/floatingpoint.html`.

## Consecuencias

**Positivas**
- `REC-10` se entrega ahora como una página real, personalizada y explicable sin adelantar la Fase 6.
- Determinista + con fingerprint: reproducible para la redacción de la tesis y barato de testear (21 tests unitarios/integración, sin fixtures más allá de un puñado de filas).
- Misma gramática de DTO que `rank_popularity_v1`, así que los dos endpoints de ranking son visiblemente hermanos con una distinción explícita, satisfaciendo D-09.
- Consulta acotada y dirigida por índice — segura frente al catálogo de 312k filas (T-01.1-11); acotada al dueño (T-01.1-10).

**Negativas / límites**
- La frecuencia de géneros es una señal de gusto tosca: un usuario con un solo RPG completado obtiene una página toda de RPG. Es aceptable para una estantería de producto y es exactamente el tipo de limitación que la Fase 6 existe para abordar.
- Sin control de diversidad/novedad, sin decaimiento por recencia más allá del corte `generated_at`, sin normalización por género (una obra en muchos géneros de gusto siempre supera a una obra en uno). Documentado, no arreglado.
- Depende de la cobertura de géneros del catálogo de la importación de IGDB (ADR-006). Las obras sin géneros no son rankeables y simplemente nunca aparecen.
- Un segundo endpoint de ranking con su propio DTO que mantener al paso de `popularity.py` si el contrato compartido cambia.

## Reversibilidad

Autocontenido: la app `recommendations` no tiene modelos ni migraciones. Borrar el directorio de la app, su línea en `INSTALLED_APPS` y su include en `config/urls.py` elimina la funcionalidad sin impacto de esquema. Se espera que la Fase 6 reemplace las tripas de `rank_genre_taste_v1` (o cambie la llamada al servicio de la vista) manteniendo la URL `GET /api/recommendations/genre-taste/` y la forma del DTO.

## Aprobación y revisión

**Aceptado.** Cualquier cambio en la tabla de pesos, en las reglas de exclusión, en la cota de `limit` `[1, 50]`, en el desempate o en la construcción de `input_snapshot_sha256` sustituye esta decisión y requiere una entrada de ADR nueva y una nueva ejecución de `test_genre_heuristic.py`.
