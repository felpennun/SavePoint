# Matriz de algoritmos evaluados

## Identidad de la publicación y frontera temporal

La única fuente de resultados de esta matriz es la publicación
`evaluation-400-test-2026-09-12-v15`: protocolo 15, feature set
`fs-v12-curated-tags-idf`, corpus `2026.09.2`, split `test` y K igual a 5, 10 y
20. Sus 16 identificadores proceden de
`docs/verification/phase-07-evidence-manifest.json:9-168`; sus valores proceden de
`docs/verification/phase-07-results.json`, campo `rows`, y del CSV homónimo.

El puntero actual `docs/methodology/protocol.json:1-25` declara protocolo 16 y
`fs-v13-family-weighted-tags`. Se puede usar para describir la implementación vigente,
pero no para recalcular ni reinterpretar las métricas v15. La web puede mostrar
resultados publicados, no crear evidencia experimental nueva desde la interfaz.

La evidencia v15 corresponde a una población sintética: 400 usuarios activos y 79
evaluables. Hay un único run publicado; las semillas fijas no sustituyen un estudio
multi-semilla. Los valores no se generalizan automáticamente a usuarios reales, otros
corpus ni otros protocolos.

## Catálogo exacto y resultados publicados

En cada celda de K se registra `Precision / Recall / nDCG / MAP` para la cohorte
`active_history_10_to_20`; el tiempo es el de pared por algoritmo en segundos. Las
familias, las señales y las fórmulas remiten a
`docs/methodology/recommendation-algorithms.md:38-53,475-641`. La implementación es
actual y queda separada de la identidad evaluada.

| algorithm_id | familia y objetivo demostrados | evaluated_v15 | current_v16 / web_published | implementación y prueba actuales | K=5 | K=10 | K=20 | tiempo |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| `random-v1` | Baseline aleatorio. | Sí | Separado; la web solo publica. | `recommendations/baselines.py`; `test_baselines.py`. | 0,00000 / 0,00000 / 0,00000 / 0,00000 | 0,00000 / 0,00000 / 0,00000 / 0,00000 | 0,00000 / 0,00000 / 0,00000 / 0,00000 | 25,08 |
| `popularity-v1` | Baseline de popularidad agregada. | Sí | Separado; la web solo publica. | `recommendations/baselines.py`; `test_baselines.py`. | 0,00253 / 0,00316 / 0,00191 / 0,00063 | 0,00253 / 0,00633 / 0,00340 / 0,00098 | 0,00127 / 0,00633 / 0,00340 / 0,00098 | 5,14 |
| `content-cbf-weighted-v1` | Contenido, suma ponderada de referencia. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,08101 / 0,15802 / 0,14114 / 0,09647 | 0,06076 / 0,23333 / 0,17245 / 0,10878 | 0,03608 / 0,29008 / 0,18987 / 0,11360 | 492,79 |
| `content-cbf-multiplicative-v1` | Contenido, producto con rating. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,03797 / 0,07532 / 0,07707 / 0,05522 | 0,02405 / 0,09325 / 0,08558 / 0,05934 | 0,01899 / 0,14177 / 0,10241 / 0,06286 | 491,41 |
| `content-cbf-twostage-v1` | Banda de similitud y desempate por rating. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,05316 / 0,10169 / 0,08827 / 0,05550 | 0,04177 / 0,17532 / 0,11724 / 0,06767 | 0,03038 / 0,24156 / 0,14002 / 0,07353 | 488,52 |
| `content-cbf-neg-v1` | Contenido con evidencia negativa. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,05823 / 0,10654 / 0,09656 / 0,06556 | 0,04304 / 0,15612 / 0,11778 / 0,07368 | 0,02532 / 0,19346 / 0,12992 / 0,07715 | 488,19 |
| `content-cbf-weighted-pop-v1` | Contenido y PopScore, suma. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,07089 / 0,14388 / 0,13179 / 0,09128 | 0,04810 / 0,19177 / 0,15181 / 0,09826 | 0,03228 / 0,25928 / 0,17409 / 0,10459 | 483,98 |
| `content-cbf-multiplicative-pop-v1` | Producto con PopScore. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,03797 / 0,07532 / 0,07677 / 0,05501 | 0,02405 / 0,09325 / 0,08517 / 0,05898 | 0,01899 / 0,14177 / 0,10200 / 0,06249 | 480,41 |
| `content-cbf-twostage-pop-v1` | Banda con rating y PopScore. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,05063 / 0,08903 / 0,08338 / 0,05297 | 0,04051 / 0,16899 / 0,11410 / 0,06551 | 0,03291 / 0,26350 / 0,14538 / 0,07371 | 484,22 |
| `content-cbf-neg-pop-v1` | Evidencia negativa y PopScore. | Sí | V16 no redefine v15. | `content/variants.py`; `test_content*.py`. | 0,05063 / 0,09494 / 0,08602 / 0,05675 | 0,03418 / 0,12447 / 0,09936 / 0,06134 | 0,02342 / 0,17194 / 0,11582 / 0,06602 | 483,93 |
| `recency-v1` | Contenido, rating, PopScore y recencia. | Sí | V16 no redefine v15. | `content/recency.py`; `test_content*.py`. | 0,00253 / 0,00422 / 0,00594 / 0,00422 | 0,00127 / 0,00422 / 0,00594 / 0,00422 | 0,00063 / 0,00422 / 0,00594 / 0,00422 | 427,63 |
| `content-cbf-mmr-v1` | MMR sobre Weighted. | Sí | V16 no redefine v15. | `content/diversity.py`; `test_diversity.py`. | 0,06076 / 0,12489 / 0,11600 / 0,07889 | 0,04557 / 0,17595 / 0,13888 / 0,08685 | 0,03038 / 0,25021 / 0,16160 / 0,09378 | 483,30 |
| `content-cbf-mmr-pop-v1` | MMR sobre Weighted-Pop. | Sí | V16 no redefine v15. | `content/diversity.py`; `test_diversity.py`. | 0,05823 / 0,13080 / 0,12211 / 0,08722 | 0,03924 / 0,16920 / 0,13824 / 0,09353 | 0,02595 / 0,21287 / 0,15362 / 0,09750 | 481,71 |
| `cf-user-knn-v1` | Colaborativo por vecindad de usuarios. | Sí | V16 no redefine v15. | `recommendations/collaborative.py`; tests de recomendaciones y evaluación. | 0,01013 / 0,01308 / 0,01585 / 0,00960 | 0,00886 / 0,02405 / 0,02098 / 0,01099 | 0,00823 / 0,05823 / 0,03163 / 0,01345 | 16,79 |
| `hybrid-weighted-cf-v1` | Híbrido 0,60 contenido y 0,40 colaborativo. | Sí | V16 no redefine v15. | `recommendations/hybrid.py`; tests de recomendaciones. | 0,08354 / 0,16435 / 0,14305 / 0,09731 | 0,06076 / 0,22489 / 0,16989 / 0,10758 | 0,03608 / 0,29177 / 0,18962 / 0,11322 | 439,74 |
| `hybrid-mmr-v1` | Híbrido seguido de MMR. | Sí | V16 no redefine v15. | `recommendations/hybrid.py`, `content/diversity.py`; `test_diversity.py`. | 0,07342 / 0,15105 / 0,13195 / 0,08690 | 0,05316 / 0,21857 / 0,15913 / 0,09741 | 0,03228 / 0,26329 / 0,17401 / 0,10209 | 493,11 |

## Límites de interpretación

La comparación estadística publicada se concentra en `nDCG@10` y en 79 observaciones.
La tabla solo expone diferencias numéricas del artefacto congelado. Antes de declarar
una diferencia estadísticamente significativa o metodológicamente defendible hay que
remitir al contraste, al corpus, al protocolo y a sus amenazas de validez. Ningún valor
de esta matriz demuestra preferencia de usuarios reales.

Fuentes complementarias: `docs/methodology/evaluation-v15-appendix.md:1-32`,
`docs/methodology/phase-07-evidence-package.md:5-8,83-93` y
`docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.*`.
