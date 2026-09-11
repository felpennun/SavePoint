---
tags: [fase/3, fase/4, tema/recomendadores, tema/arquitectura, tema/rendimiento]
---

# Cache de señales compartidas — evaluación offline y cola web

Los 16 algoritmos ofrecidos (11 variantes de contenido + 2 MMR + colaborativo + 2
híbridos) comparten, para un mismo `(usuario, obra, corpus_version, datos de tags)`, el
cálculo más caro de `rank_content_v1` (`recommendations/content/rank.py`):
`build_profile_inputs`, `facet_similarity` (positiva y negativa) y `rating_term`. Solo la
aritmética final de `combine()` (weighted_sum, multiplicative, two_stage,
negative_weighted_sum, mmr...) difiere por variante. Ninguna de las tres piezas depende de
qué algoritmo pregunta.

## Offline (commit `134c6e0`)

El runner de evaluación (`evaluation/runner.py`) ejecuta los 16 algoritmos sobre los mismos
usuarios en **un solo proceso Python** (`run_evaluation`, no el paralelo), así que basta con
memoizar en el propio diccionario `prepared` que ya se pasa a `rank_content_v1`:
`prepared["_profile_cache"]` (por `user.pk`), `prepared["_rating_term_cache"]` (por
`work.id` — no depende del usuario), `prepared["_similarity_cache"]` (por
`(user.pk, work.id)`). Verificado byte a byte: 12/12 combinaciones usuario×algoritmo
producen el mismo resultado con y sin cache.

## Web (commit `9b1374c`)

En producción cada una de las 13 variantes que llaman a `rank_content_v1` (las 11 base +
`hybrid-weighted-cf-v1` + `hybrid-mmr-v1`, que la envuelven internamente) corre en su
**propio contenedor** (`infra/compose.yaml`, un `recommendation-worker-*` por
`algorithm_id`). Un dict en memoria de un worker no lo ve otro proceso, así que la
memoización offline no sirve tal cual.

Se evaluaron dos diseños con el autor antes de implementar:

1. **Cache oportunista** (descartado): tabla + "si no está, la calculo yo". Es una
   carrera — varios workers que arrancan casi a la vez recalculan igual. Rechazado por el
   autor ("no los quiero tener calculando").
2. **Job de señales dedicado** (implementado): un nuevo `algorithm_id`,
   `content-signals-v1`, corre en su propio worker
   (`recommendation-worker-signals`), calcula la matriz señal×candidata una vez por
   `(usuario, revisión de colección, configuración)` y la persiste en
   `RecommendationSignalCache`. La cola (`recommendations/jobs.py`,
   `_claim_next_job`) no deja reclamar ningún job de las 13 variantes dependientes
   hasta que exista una fila `SUCCEEDED` de señales para esa misma clave —  vía
   `Exists()` en la consulta de reclamo, no un lock ni una llamada bloqueante: un
   worker sin nada que reclamar simplemente vuelve a sondear en su intervalo normal
   (`--poll-seconds`).

`recommend_for_user` (`recommendations/service.py`) ahora acepta un `prepared` opcional
que reenvía a `rank_content_v1` y, a través de él, a los dos híbridos — sin tocar
`cf-user-knn-v1` ni `tag-taste-v1` (`genre_heuristic`), que nunca pasan por
`rank_content_v1` y por tanto no son dependientes.

## Verificación

Sin regresiones: mismo baseline de 51 fallos preexistentes en `apps/api/recommendations`
antes y después del cambio (deuda de tests no relacionada, ya presente en `134c6e0` con
un conteo equivalente de 61 sobre el total del backend), más 3 tests nuevos en verde
(`test_signal_cache.py`, y un test de exclusión de reclamo en `test_jobs.py`). `python
manage.py makemigrations --check` confirma que el modelo y la migración
(`0004_recommendationsignalcache.py`) están sincronizados.

## Pendiente

El siguiente paso, ya solicitado por el autor, es revisar si el propio protocolo congelado
puede mejorarse para aumentar la validez del hallazgo de `insufficient_history` (ver
[[2026-09-11 - Evaluación offline final protocolo 12 (400 usuarios, test)]]) — no
empezado todavía.

Commits: `134c6e0` (offline), `9b1374c` (web).
