---
tags: [fase/3, fase/4, tema/evaluacion, tema/recomendadores, tema/arquitectura, tema/rendimiento]
---

# Piso de rating externo en el LOO + paralelización offline por precómputo

Dos decisiones tomadas el 2026-09-11, después de congelar protocolo v13
([[2026-09-11 - Evaluación offline final protocolo 12 (400 usuarios, test)]]) y de construir
la cache compartida de señales ([[2026-09-11 - Cache de señales compartidas offline y web]]),
justo antes de producir el artefacto final del split `test`.

## 1. Protocolo v14 — piso de rating externo en la selección del positivo retirado (LOO)

### El problema

`evaluation/splits.py::leave_one_out()` elegía el positivo retirado con `rng.choice()`
sobre el conjunto de positivos del usuario (`completed` o `rating_half_steps >= 7`) —
**sin mirar en ningún momento el rating externo de IGDB de esa obra**. Un candidato solo
necesita `rating IS NOT NULL AND total_rating_count >= 5` para ser elegible
(`catalogue/corpus.py`), sin piso sobre el *valor* del rating; y el PopScore que exige la
población v13 para sus 5 positivos garantizados es puramente de volumen de
engagement (visitas, want-to-play, jugando, jugado — `catalogue/popularity.py`),
independiente del rating externo.

Como la mayoría de las 16 variantes combinan similitud de contenido con
`rating_confidence` y/o PopScore (`recommendations/content/combine.py::combine`), un
positivo retirado con rating externo bajo podía hundirse en el ranking pase lo que pase
con la calidad del modelado de contenido. La métrica terminaba midiendo, en parte, la
popularidad/calidad catalogada de la obra retirada, no solo la precisión del modelado de
preferencia — un sesgo de popularidad ya documentado en la literatura de evaluación
offline de sistemas de recomendación top-N (Cremonesi, Koren & Turrin, *"Performance of
Recommender Algorithms on Top-N Recommendation Tasks"*, RecSys 2010; Steck, *"Item
Popularity and Recommendation Accuracy"*, RecSys 2011).

### La decisión

Se plantearon tres opciones (ver conversación de sesión):

1. No tocar el protocolo, añadir análisis estratificado por tercil de rating externo —
   más seguro, cero re-congelado, pero no corrige el sesgo en el número que se cita como
   resultado principal.
2. **Exigir un rating externo mínimo también para el positivo retirado** (elegida).
3. Reportar una métrica secundaria de "acierto por contenido puro" — descartada por
   introducir una definición de métrica no anticipada por `protocol.json`, mayor
   complejidad a defender en el TFG para un beneficio similar al de la opción 2.

Antes de fijar el umbral se midió el impacto real sobre los 400 usuarios v13 (script de
solo lectura, sin tocar nada congelado): con el umbral en la mediana del corpus (70 sobre
100 IGDB, sobre las 13.618 candidatas elegibles de `2026.09.2`), **0 de los 400 usuarios
pierden todos sus positivos elegibles** — ni siquiera al forzar la mediana completa. Se
adoptó `relevance.heldout_min_external_rating = 70`.

### Implementación

- `docs/methodology/protocol.json`: `protocol_version` 13 → 14;
  `relevance.heldout_min_external_rating: 70`. Fórmulas, similitud, candidatas, pesos,
  población sintética: sin cambios respecto a v13.
- `evaluation/splits.py::leave_one_out()`: filtra el conjunto de positivos elegibles al
  piso antes de la elección aleatoria seedeada; si eso vacía el conjunto, devuelve `None`
  (mismo comportamiento que "sin positivo elegible") en vez de ignorar el piso en
  silencio.
- `evaluation/protocol.py`: nueva propiedad `Protocol.heldout_min_external_rating`,
  `None` en protocolos congelados antes de que existiera este campo (no-op ahí — la
  suite de tests fijada en v6/v1 para probar guardas de versión sigue intacta).
- `require_version(protocol, 13)` → `14` en los dos puntos de `evaluation/candidates.py`
  y `PROTOCOL_VERSION` en `recommendations/service.py` (comparte guarda con la web).
- Tests nuevos en `evaluation/tests/test_splits.py`: un positivo por debajo del piso se
  descarta; solo se elige entre los que lo superan (comprobado 20 semillas); un protocolo
  sin el campo (compatibilidad hacia atrás) no se ve afectado.

Commit: `349f390`.

## 2. Paralelización offline por precómputo (compute-once, fan-out después)

### El problema

`run_evaluation_parallel` pone cada uno de los 16 algoritmos en su **propio proceso del
sistema operativo** (`ProcessPoolExecutor`), así que la cache cruzada entre algoritmos
añadida en la misma sesión (`134c6e0` — `prepared["_profile_cache"]` /
`_rating_term_cache` / `_similarity_cache`, compartidos dentro de un único proceso
Python) nunca la beneficiaba: cada worker recalculaba desde cero el bucle
O(candidatas × usuarios) de `facet_similarity`/`rating_term`. Medido en la propia
corrida: ~14 minutos por variante de contenido, sobre 79 usuarios del split test y
13.618 candidatas — 13 variantes de ese calibre habrían tardado del orden de 3 horas en
paralelo 2+1.

### La decisión

Trasladar al offline exactamente el mismo patrón "calcula una vez, reparte después"
construido para la cola web ese mismo día
([[2026-09-11 - Cache de señales compartidas offline y web]]), pero explotando una
propiedad que la web no tiene: los 16 algoritmos offline corren desde el **mismo proceso
padre** que lanza `ProcessPoolExecutor`, y en Linux/CPython el método de arranque de
`multiprocessing` por defecto es `fork` (confirmado en el contenedor: Python 3.13,
`multiprocessing.get_start_method() == "fork"`). Un proceso hijo forkeado hereda la
memoria del padre por copy-on-write en el instante del fork — así que si el padre
calcula la señal compartida **antes** de crear el pool de procesos, cada worker ya la
tiene sin necesidad de servirla desde una base de datos ni de volver a serializarla
(`pickle`) por worker.

### Implementación

- `evaluation/runner.py::run()` se parte en dos funciones:
  - `build_evaluation_context(protocol, corpus_version, split)`: todo lo independiente
    de qué algoritmo puntúa (conjuntos de candidatas por usuario, vectores, perfil de
    tags, prior de rating...) — antes se reconstruía dentro de cada llamada a `run()`.
  - `precompute_shared_content_signals(context)`: rellena
    `context["evaluation_prepared"]["_profile_cache"/"_rating_term_cache"/"_similarity_cache"]`
    para **todos** los usuarios del split de una vez, no de forma perezosa por algoritmo.
    `rating_term` no depende del usuario, así que se calcula una vez por obra
    independientemente de cuántos usuarios tenga el split; `facet_similarity` una vez
    por (usuario, obra) — el mismo volumen total de trabajo que `run_evaluation` ya
    pagaba a lo largo de sus 16 llamadas secuenciales, hecho una sola vez.
  - `run()` acepta un `context=` opcional; omitirlo preserva exactamente el
    comportamiento anterior (usado por `run_evaluation`, sin cambios).
- `run_evaluation_parallel.py`: construye y precomputa el contexto en el proceso padre,
  en un global de módulo `_SHARED_CONTEXT`, **antes** de crear cualquier
  `ProcessPoolExecutor`; `_drain_pool` pasa `mp_context=multiprocessing.get_context("fork")`
  de forma explícita en vez de confiar en el valor por defecto de la plataforma.
  `--serial-tail` se mantiene disponible pero deja de ser necesario por defecto para la
  seguridad de memoria, porque el coste restante de cada worker (combinar señales +
  MMR opcional) es ahora mucho menor.

### Verificación

- `run()` con contexto precomputado produce un artefacto **idéntico byte a byte**
  (salvo `duration_seconds`) al de `run()` sin contexto, sobre el mismo
  protocolo/corpus/split.
- Test unitario aparte: `precompute_shared_content_signals` reproduce exactamente los
  mismos valores que una llamada sin cache a `rank_content_v1` — no solo que las claves
  de cache existen, sino que un valor "envenenado" a propósito en la cache se refleja en
  el resultado (prueba de que de verdad se lee, no que coincide por casualidad).
- Corrida real: contexto construido en 36,6s, señales precomputadas en 173,2s (2,9 min)
  para 79 usuarios × 13.618 candidatas — frente a ~14,2 min que tardaba *un solo*
  algoritmo de contenido sin esta pieza.

Commit: `9b7ff13`.

## Lo que no se aplicó, y por qué

- **Cache oportunista para la web** (tabla + "si no está, la calculo yo"): descartada
  por el autor a favor del job de señales dedicado — es una carrera (varios workers que
  arrancan casi a la vez recalculan igual), y para la web sí hace falta un mecanismo
  cross-proceso real porque los 13 workers dependientes son contenedores separados y
  de larga duración, sin punto de fork compartido. Ver
  [[2026-09-11 - Cache de señales compartidas offline y web]].
- **Métrica secundaria de "acierto por contenido puro"** (ignorando rating/popscore) para
  compensar el sesgo del LOO: descartada frente al piso de rating externo — habría exigido
  definir y justificar una métrica nueva no anticipada por `protocol.json`, con un
  beneficio metodológico similar al de exigir directamente que el positivo retirado
  también supere un piso de calidad catalogada.
- **Regenerar la población sintética** para acompañar el piso de rating: no hizo falta —
  verificado empíricamente que ningún usuario de los 400 pierde su elegibilidad al
  umbral elegido, así que la semilla/manifiesto de población v13 sigue siendo válida
  bajo protocolo v14.
- **Compartir el precómputo offline vía `RecommendationSignalCache`** (la tabla de la
  web): no se reutilizó para offline — la ventaja allí es específicamente el fork
  compartido de un único proceso padre, que no necesita persistencia en base de datos;
  añadir una tabla habría sido complejidad sin beneficio para este caso de uso de
  corridas por lotes.
