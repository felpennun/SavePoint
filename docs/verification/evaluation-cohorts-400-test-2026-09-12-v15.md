# Desglose por cohortes de la evaluación offline v15

- Protocolo: `15`
- Corpus: `2026.09.2`
- Split: `test`
- Usuarios del manifiesto: **400**
- Usuarios evaluables registrados: **79**

Este informe es una transformación determinista del artefacto JSON ya ejecutado y del manifiesto de población. No relanza algoritmos ni consulta datos vivos.

## Cohorte `active_history_10_to_20`

Población: **390**; evaluables: **79**.

| Algoritmo | K | Usuarios | Precision | Recall | nDCG | MAP | ILD | Novedad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cf-user-knn-v1` | 5 | 79 | 0.010127 | 0.013080 | 0.015848 | 0.009599 | 0.795688 | 9.251489 |
| `cf-user-knn-v1` | 10 | 79 | 0.008861 | 0.024051 | 0.020977 | 0.010986 | 0.754513 | 9.394273 |
| `cf-user-knn-v1` | 20 | 79 | 0.008228 | 0.058228 | 0.031633 | 0.013455 | 0.730247 | 9.476712 |
| `content-cbf-mmr-pop-v1` | 5 | 79 | 0.058228 | 0.130802 | 0.122111 | 0.087219 | 0.716632 | 10.473768 |
| `content-cbf-mmr-pop-v1` | 10 | 79 | 0.039241 | 0.169198 | 0.138241 | 0.093529 | 0.680200 | 10.589826 |
| `content-cbf-mmr-pop-v1` | 20 | 79 | 0.025949 | 0.212869 | 0.153622 | 0.097497 | 0.661531 | 10.542551 |
| `content-cbf-mmr-v1` | 5 | 79 | 0.060759 | 0.124895 | 0.116003 | 0.078885 | 0.679210 | 10.458390 |
| `content-cbf-mmr-v1` | 10 | 79 | 0.045570 | 0.175949 | 0.138884 | 0.086851 | 0.652327 | 10.480766 |
| `content-cbf-mmr-v1` | 20 | 79 | 0.030380 | 0.250211 | 0.161605 | 0.093779 | 0.638919 | 10.612487 |
| `content-cbf-multiplicative-pop-v1` | 5 | 79 | 0.037975 | 0.075316 | 0.076772 | 0.055011 | 0.587635 | 10.104749 |
| `content-cbf-multiplicative-pop-v1` | 10 | 79 | 0.024051 | 0.093249 | 0.085174 | 0.058979 | 0.615933 | 10.317384 |
| `content-cbf-multiplicative-pop-v1` | 20 | 79 | 0.018987 | 0.141772 | 0.102001 | 0.062491 | 0.635516 | — |
| `content-cbf-multiplicative-v1` | 5 | 79 | 0.037975 | 0.075316 | 0.077070 | 0.055222 | 0.587124 | 10.115476 |
| `content-cbf-multiplicative-v1` | 10 | 79 | 0.024051 | 0.093249 | 0.085577 | 0.059340 | 0.615115 | 10.355598 |
| `content-cbf-multiplicative-v1` | 20 | 79 | 0.018987 | 0.141772 | 0.102407 | 0.062855 | 0.634479 | — |
| `content-cbf-neg-pop-v1` | 5 | 79 | 0.050633 | 0.094937 | 0.086017 | 0.056751 | 0.545994 | 10.439747 |
| `content-cbf-neg-pop-v1` | 10 | 79 | 0.034177 | 0.124473 | 0.099359 | 0.061339 | 0.559519 | 10.466245 |
| `content-cbf-neg-pop-v1` | 20 | 79 | 0.023418 | 0.171941 | 0.115820 | 0.066017 | 0.584953 | 10.448839 |
| `content-cbf-neg-v1` | 5 | 79 | 0.058228 | 0.106540 | 0.096557 | 0.065559 | 0.532080 | 10.560937 |
| `content-cbf-neg-v1` | 10 | 79 | 0.043038 | 0.156118 | 0.117783 | 0.073683 | 0.543108 | 10.576684 |
| `content-cbf-neg-v1` | 20 | 79 | 0.025316 | 0.193460 | 0.129917 | 0.077149 | 0.561032 | — |
| `content-cbf-twostage-pop-v1` | 5 | 79 | 0.050633 | 0.089030 | 0.083375 | 0.052971 | 0.497884 | 10.792559 |
| `content-cbf-twostage-pop-v1` | 10 | 79 | 0.040506 | 0.168987 | 0.114097 | 0.065511 | 0.510358 | 10.650395 |
| `content-cbf-twostage-pop-v1` | 20 | 79 | 0.032911 | 0.263502 | 0.145382 | 0.073711 | 0.519726 | — |
| `content-cbf-twostage-v1` | 5 | 79 | 0.053165 | 0.101688 | 0.088272 | 0.055503 | 0.497750 | 10.743142 |
| `content-cbf-twostage-v1` | 10 | 79 | 0.041772 | 0.175316 | 0.117241 | 0.067669 | 0.509918 | 10.660924 |
| `content-cbf-twostage-v1` | 20 | 79 | 0.030380 | 0.241561 | 0.140015 | 0.073534 | 0.521759 | — |
| `content-cbf-weighted-pop-v1` | 5 | 79 | 0.070886 | 0.143882 | 0.131787 | 0.091280 | 0.535371 | 10.459062 |
| `content-cbf-weighted-pop-v1` | 10 | 79 | 0.048101 | 0.191772 | 0.151806 | 0.098259 | 0.545733 | 10.468217 |
| `content-cbf-weighted-pop-v1` | 20 | 79 | 0.032278 | 0.259283 | 0.174094 | 0.104589 | 0.572853 | 10.553087 |
| `content-cbf-weighted-v1` | 5 | 79 | 0.081013 | 0.158017 | 0.141141 | 0.096466 | 0.520643 | 10.541991 |
| `content-cbf-weighted-v1` | 10 | 79 | 0.060759 | 0.233333 | 0.172453 | 0.108783 | 0.531312 | 10.542109 |
| `content-cbf-weighted-v1` | 20 | 79 | 0.036076 | 0.290084 | 0.189875 | 0.113597 | 0.552866 | 10.657336 |
| `hybrid-mmr-v1` | 5 | 79 | 0.073418 | 0.151055 | 0.131954 | 0.086902 | 0.678814 | 10.477303 |
| `hybrid-mmr-v1` | 10 | 79 | 0.053165 | 0.218565 | 0.159129 | 0.097413 | 0.654906 | 10.491573 |
| `hybrid-mmr-v1` | 20 | 79 | 0.032278 | 0.263291 | 0.174010 | 0.102090 | 0.642100 | 10.597739 |
| `hybrid-weighted-cf-v1` | 5 | 79 | 0.083544 | 0.164346 | 0.143048 | 0.097310 | 0.522765 | 10.537885 |
| `hybrid-weighted-cf-v1` | 10 | 79 | 0.060759 | 0.224895 | 0.169889 | 0.107576 | 0.531636 | 10.527585 |
| `hybrid-weighted-cf-v1` | 20 | 79 | 0.036076 | 0.291772 | 0.189622 | 0.113217 | 0.553611 | 10.679847 |
| `popularity-v1` | 5 | 79 | 0.002532 | 0.003165 | 0.001912 | 0.000633 | 0.667191 | 9.814751 |
| `popularity-v1` | 10 | 79 | 0.002532 | 0.006329 | 0.003399 | 0.000985 | 0.641143 | 10.041032 |
| `popularity-v1` | 20 | 79 | 0.001266 | 0.006329 | 0.003399 | 0.000985 | 0.644683 | — |
| `random-v1` | 5 | 79 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.809858 | — |
| `random-v1` | 10 | 79 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.816096 | — |
| `random-v1` | 20 | 79 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.817112 | — |
| `recency-v1` | 5 | 79 | 0.002532 | 0.004219 | 0.005940 | 0.004219 | 0.661540 | — |
| `recency-v1` | 10 | 79 | 0.001266 | 0.004219 | 0.005940 | 0.004219 | 0.678891 | — |
| `recency-v1` | 20 | 79 | 0.000633 | 0.004219 | 0.005940 | 0.004219 | 0.691582 | — |

## Cohorte `no_history`

Población: **10**; evaluables: **0**.

> La cohorte no contiene positivos elegibles para este split; no se puede calcular ranking personalizado.

| Algoritmo | K | Usuarios | Precision | Recall | nDCG | MAP | ILD | Novedad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cf-user-knn-v1` | 5 | 0 | — | — | — | — | — | — |
| `cf-user-knn-v1` | 10 | 0 | — | — | — | — | — | — |
| `cf-user-knn-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-pop-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-pop-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-pop-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-mmr-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-pop-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-pop-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-pop-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-multiplicative-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-pop-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-pop-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-pop-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-neg-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-pop-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-pop-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-pop-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-twostage-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-pop-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-pop-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-pop-v1` | 20 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-v1` | 5 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-v1` | 10 | 0 | — | — | — | — | — | — |
| `content-cbf-weighted-v1` | 20 | 0 | — | — | — | — | — | — |
| `hybrid-mmr-v1` | 5 | 0 | — | — | — | — | — | — |
| `hybrid-mmr-v1` | 10 | 0 | — | — | — | — | — | — |
| `hybrid-mmr-v1` | 20 | 0 | — | — | — | — | — | — |
| `hybrid-weighted-cf-v1` | 5 | 0 | — | — | — | — | — | — |
| `hybrid-weighted-cf-v1` | 10 | 0 | — | — | — | — | — | — |
| `hybrid-weighted-cf-v1` | 20 | 0 | — | — | — | — | — | — |
| `popularity-v1` | 5 | 0 | — | — | — | — | — | — |
| `popularity-v1` | 10 | 0 | — | — | — | — | — | — |
| `popularity-v1` | 20 | 0 | — | — | — | — | — | — |
| `random-v1` | 5 | 0 | — | — | — | — | — | — |
| `random-v1` | 10 | 0 | — | — | — | — | — | — |
| `random-v1` | 20 | 0 | — | — | — | — | — | — |
| `recency-v1` | 5 | 0 | — | — | — | — | — | — |
| `recency-v1` | 10 | 0 | — | — | — | — | — | — |
| `recency-v1` | 20 | 0 | — | — | — | — | — | — |

## Métricas que permanecen globales

El artefacto v15 no guarda el ranking completo de cada usuario. Por ello `catalogue_coverage`, `concentration_hhi` y `prediction_coverage` se mantienen como métricas globales por algoritmo y K; el informe no las asigna a cohortes por aproximación.

## Lectura metodológica

La cohorte `no_history` es una condición descriptiva de arranque en frío: no debe interpretarse como un algoritmo con rendimiento cero. Las cohortes con historial sí se comparan sobre las mismas listas de candidatos, el mismo split y el mismo artefacto, por lo que sus medias son comparables dentro de los límites del estudio sintético.
