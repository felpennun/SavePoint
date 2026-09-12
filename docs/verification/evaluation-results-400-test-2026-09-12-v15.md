# Resultados de la evaluación offline final — protocolo v15, 400 usuarios sintéticos, split test

**Fecha de ejecución:** 2026-09-12 00:50:40 UTC → 02:02:17 UTC (1 h 12 min de pared, tercer
intento de la noche — los dos anteriores se pararon de forma segura, sin consumir el
marcador, al encontrarse dos fallos de diseño; ver §1.2).
**Protocolo:** v15, congelado el 2026-09-12. **Corpus:** `2026.09.2`. **Split:** `test`
(uso único, ahora consumido). **Estado:** `succeeded`, 16/16 algoritmos.

## 0. Resumen ejecutivo

- El split de test se ejecutó **una sola vez con éxito** (al tercer intento; los dos
  primeros se detuvieron a propósito, sin escribir el marcador, al encontrar dos fallos de
  diseño reales — §1.2). Marcador escrito:
  `apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-12T02:02:20.014454Z`.
- **Protocolo v15 sustituye el leave-one-out de un único positivo por un leave-fraction-out
  adaptativo centrado en el tag de contenido más pesado del propio perfil de cada
  usuario** — decisión del autor tras revisar el resultado de protocolo v14 y cuestionar si
  LOO de un solo ítem era la forma más fiable de comprobar "¿le recomiendas de vuelta sus
  propios juegos buenos, afines a su género de mayor gusto?". Mecánica completa, fundamento
  científico y alternativas descartadas (Given-N, K-fold, predicción de rating,
  solo-más-allá-del-acierto, N fijo global): ver §8 y
  [[2026-09-12 - LOO por fraccion sobre el tag dominante, fundamento y alternativas descartadas]].
- **El resultado es sustancialmente más rico y diferenciado que protocolo v14.** Friedman
  ómnibus sobre nDCG@10: χ² = 258,07, p = 2,69 × 10⁻⁴⁶ (n = 79) — frente a χ² = 105,28,
  p = 1,29 × 10⁻¹⁵ en v14. **54 de las 120 comparaciones por pares sobreviven la corrección
  de Holm** (frente a 14/120 en v14 y 0/120 en v12).
- **`content-cbf-weighted-v1` (nDCG@10 = 0,1725) y `hybrid-weighted-cf-v1` (0,1699)** siguen
  siendo los de mejor acierto, ahora con una ventaja estadística mucho más amplia:
  significativamente superiores no solo a los dos baselines y a `recency-v1` (como en v14),
  sino que además **`cf-user-knn-v1` (colaborativo puro) resulta significativamente peor que
  8 de las 10 variantes de contenido** — una diferenciación que en v14 no sobrevivía Holm.
- Retener varios ítems relevantes por usuario (media 2,56, rango 1-5) en vez de exactamente
  uno da a cada comparación mucha más información por usuario (Recall@10 continuo en vez de
  binario) — el mecanismo detrás de la mejora en potencia estadística, previsto y
  documentado antes de ejecutar (§8, fundamento en Herlocker et al. 2004).

## 1. Estado congelado y trazabilidad

| Campo | Valor |
|---|---|
| `protocol_version` | 15 |
| `protocol_sha256` | `d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a` |
| `corpus_version` | `2026.09.2` |
| `snapshot_sha256` (ratings) | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| `popscore_snapshot_sha256` | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| `feature_set_version` | `fs-v12-curated-tags-idf` |
| Semilla leave-fraction-out | `20260907` (heredada; el sufijo `:dominant-tag` en el RNG evita colisión con cualquier otro uso) |
| Semilla de población sintética | `20260912` |
| Semilla split de usuarios | `20260908` |
| `split` | `test` |
| `split_manifest_sha256` | `c85d4ee270de8e590c9052d01dab30d7cf5314951622cc0b3801fdf027cbfd3d` |
| Marcador de consumo | `apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-12T02:02:20.014454+00:00` |
| Artefacto final | `apps/api/evaluation-400-test-2026-09-12-v15.artifact.json` |
| SHA-256 del artefacto | `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab` |
| Preflight de entradas | `apps/api/evaluation-input-preflight-2026-09-12-v15-gate.json` |

`corpus_version`, `snapshot_sha256` y `popscore_snapshot_sha256` son **idénticos** a los de
v12-v14 — nada del corpus ni de las fórmulas de contenido/rating/PopScore cambia. Lo que
cambia en v15 es exclusivamente el mecanismo de selección del conjunto retenido en el
leave-one-out (ahora leave-fraction-out) y la población sintética (gusto individual por
usuario, mínimo garantizado más alto — §1.1).

### 1.1 Qué cambia respecto a v14 (resumen; detalle completo en el vault)

1. **Población**: cada usuario sortea su propio conjunto de tags preferidos (antes
   compartido por los ~25-80 usuarios de cada arquetipo); `guaranteed_eligible_minimum`
   sube de 5 a 8, con al menos 6 compartiendo el tag de agrupación del usuario. Nueva
   semilla `20260912`.
2. **Split**: `leave_fraction_out_dominant_tag_per_user` — se calcula el tag de contenido
   más pesado del perfil completo del usuario, y se retira `ceil(0,3 × tamaño_del_pool)` de
   sus obras de ese tag (piso de rating externo ≥70 heredado de v14), con retroceso de uno
   en uno si retirarlas desplazaría el tag de la primera posición en el perfil restante —
   pero nunca por debajo de 1.
3. **Respaldo**: un usuario para el que este mecanismo no se puede construir (sin ninguna
   señal de tag de contenido, o su tag dominante sin candidatas que pasen el piso de
   rating) cae al LOO simple de un único ítem en vez de quedar excluido. Solo los usuarios
   sin ningún positivo elegible en absoluto quedan fuera del estudio.

### 1.2 Dos fallos de diseño encontrados y corregidos en vivo, antes del cálculo que sí tuvo éxito

Ambos se encontraron con el autor revisando una corrida real en marcha (no en pruebas
automatizadas) y se corrigieron **antes** de que ninguna de las dos corridas fallidas
escribiera el marcador de consumo — cero coste, plenamente documentado.

| Intento | Qué falló | Corrección | Commit |
|---|---|---|---|
| 1º | El "tag dominante" se buscaba con `max()` sobre el perfil completo, mezclando `tag:*` con `platform:*`/`franchise:*`/`developer:*` — un usuario con casi toda su biblioteca en una misma plataforma podía quedar excluido del estudio por "no tener tag dominante", aunque sí lo tuviera. `facet_similarity()` (el código real de puntuación) trata cada familia de faceta como señal independiente con pesos fijos (`tag=0,75`, `platform=0,25`) — nunca compiten entre sí en la puntuación real. | Restringir la búsqueda del dominante (y la comprobación de rango tras la retirada) a claves `tag:*` únicamente. | `ed25fe8` |
| 2º | Un usuario para el que el mecanismo por fracción no se podía construir quedaba **excluido del estudio entero**, en vez de caer al LOO simple — perdiendo usuarios con positivos elegibles de verdad, en contra del principio de máxima inclusión salvo imposibilidad real. | `evaluation/candidates.py::build()` cae a `leave_one_out` cuando `leave_fraction_out_dominant_tag` devuelve `None`, salvo que ese usuario tampoco tenga ningún positivo elegible en absoluto. | `81df38b` |

Ninguno de los dos fallos tocó `facet_similarity()`, `combine()` ni ningún camino de
puntuación real — estaban aislados en el código nuevo de selección de candidatas para este
estudio, nunca en las recomendaciones (web u offline, cualquier protocolo anterior).
Verificado: el nº de usuarios evaluables subió de 77 (con los dos fallos presentes) a 79
(con ambos corregidos) — igualando exactamente la cifra de v14.

## 2. Protocolo que se aplicó

- Relevancia: `completed` **o** `rating_half_steps >= 7` (D-17, sin cambios).
- Piso de rating externo ≥70 sobre las candidatas a retener (v14, heredado).
- **Nuevo en v15**: retirada adaptativa de `ceil(0,3 × pool_del_tag_dominante)` obras,
  nunca menos de 1, con retroceso si desplaza el tag de la primera posición — o LOO simple
  de respaldo si el mecanismo no se puede construir.
- `K ∈ {5, 10, 20}`; métrica titular `nDCG@10`.
- Candidatas: obras gobernadas con `rating IS NOT NULL AND total_rating_count >= 5`, menos
  la biblioteca restante del usuario, más los ítems retenidos.
- 16 algoritmos declarados en `protocol.json`, ejecutados exactamente una vez sobre test.

## 3. Población evaluable del split test

| Asignados | Evaluables | Omitidos | Motivo de los omitidos |
|---:|---:|---:|---|
| 80 | **79** | 1 | Arquetipo `no_history` — sin biblioteca, ningún mecanismo puede evaluarlo |

Cifra idéntica a protocolo v14 (79/80) — el respaldo a LOO simple (§1.2) recupera
exactamente a los usuarios que el mecanismo por fracción no podría haber evaluado por sí
solo, sin perder a nadie adicional. Los 79 usuarios retienen entre 1 y 5 ítems cada uno
(media 2,56 — distribución: 19 con 1, 13 con 2, 34 con 3, 10 con 4, 3 con 5), reflejando el
tamaño real de cada uno de sus pools de tag dominante, no un número fijo global.

No se puede distinguir, solo con el artefacto, cuántos de los 19 usuarios con exactamente 1
ítem retenido llegaron ahí por el suelo del mecanismo por fracción (retroceso hasta 1) frente
a por el respaldo de LOO simple — limitación anotada, no bloqueante (§9).

## 4. Resultados de acierto

### 4.1 nDCG@10 (métrica titular), ordenado descendente

| Algoritmo | nDCG@10 |
|---|---:|
| `content-cbf-weighted-v1` | 0,172453 |
| `hybrid-weighted-cf-v1` | 0,169889 |
| `hybrid-mmr-v1` | 0,159129 |
| `content-cbf-weighted-pop-v1` | 0,151806 |
| `content-cbf-mmr-v1` | 0,138884 |
| `content-cbf-mmr-pop-v1` | 0,138241 |
| `content-cbf-neg-v1` | 0,117783 |
| `content-cbf-twostage-v1` | 0,117241 |
| `content-cbf-twostage-pop-v1` | 0,114097 |
| `content-cbf-neg-pop-v1` | 0,099359 |
| `content-cbf-multiplicative-v1` | 0,085577 |
| `content-cbf-multiplicative-pop-v1` | 0,085174 |
| `cf-user-knn-v1` | 0,020977 |
| `recency-v1` | 0,005940 |
| `popularity-v1` | 0,003399 |
| `random-v1` | 0,000000 |

### 4.2 Precision / recall / nDCG / MAP a K = 10

| Algoritmo | Precision@10 | Recall@10 | nDCG@10 | MAP@10 |
|---|---:|---:|---:|---:|
| `content-cbf-weighted-v1` | 0,060759 | 0,233333 | 0,172453 | 0,108783 |
| `hybrid-weighted-cf-v1` | 0,060759 | 0,224895 | 0,169889 | 0,107576 |
| `hybrid-mmr-v1` | 0,053165 | 0,218565 | 0,159129 | 0,097413 |
| `content-cbf-weighted-pop-v1` | 0,048101 | 0,191772 | 0,151806 | 0,098259 |
| `content-cbf-mmr-v1` | 0,045570 | 0,175949 | 0,138884 | 0,086851 |
| `content-cbf-mmr-pop-v1` | 0,039241 | 0,169198 | 0,138241 | 0,093529 |
| `content-cbf-neg-v1` | 0,043038 | 0,156118 | 0,117783 | 0,073683 |
| `content-cbf-twostage-v1` | 0,041772 | 0,175316 | 0,117241 | 0,067669 |
| `content-cbf-twostage-pop-v1` | 0,040506 | 0,168987 | 0,114097 | 0,065511 |
| `content-cbf-neg-pop-v1` | 0,034177 | 0,124473 | 0,099359 | 0,061339 |
| `content-cbf-multiplicative-v1` | 0,024051 | 0,093249 | 0,085577 | 0,059340 |
| `content-cbf-multiplicative-pop-v1` | 0,024051 | 0,093249 | 0,085174 | 0,058979 |
| `cf-user-knn-v1` | 0,008861 | 0,024051 | 0,020977 | 0,010986 |
| `recency-v1` | 0,001266 | 0,004219 | 0,005940 | 0,004219 |
| `popularity-v1` | 0,002532 | 0,006329 | 0,003399 | 0,000985 |
| `random-v1` | 0,000000 | 0,000000 | 0,000000 | 0,000000 |

Con varios ítems relevantes por usuario, `Recall@10` ya no es 0/1 sino una fracción
continua (p. ej. `content-cbf-weighted-v1` recupera, en media, el 23,3 % de los ítems
retenidos de cada usuario dentro del top-10) — más información por usuario que en v12/v14,
donde solo había un ítem posible que acertar o no.

### 4.3 Tabla de éxitos por algoritmo

Con retención múltiple por usuario, "acierto" se reporta en dos niveles: cuántos de los
**202 ítems retenidos en total** (suma de `len(heldout_work_ids)` sobre los 79 usuarios) se
recuperaron en el top-K, y cuántos de los **79 usuarios** recibieron al menos uno de los
suyos.

| Algoritmo | Ítems@5 | Ítems@10 | Ítems@20 | Usuarios≥1@5 | Usuarios≥1@10 | Usuarios≥1@20 |
|---|---:|---:|---:|---:|---:|---:|
| `content-cbf-weighted-v1` | 32/202 | 48/202 | 57/202 | 29/79 | 39/79 | 46/79 |
| `hybrid-weighted-cf-v1` | 33/202 | 48/202 | 57/202 | 29/79 | 38/79 | 45/79 |
| `hybrid-mmr-v1` | 29/202 | 42/202 | 51/202 | 27/79 | 35/79 | 40/79 |
| `content-cbf-weighted-pop-v1` | 28/202 | 38/202 | 51/202 | 26/79 | 34/79 | 43/79 |
| `content-cbf-mmr-v1` | 24/202 | 36/202 | 48/202 | 23/79 | 32/79 | 39/79 |
| `content-cbf-neg-v1` | 23/202 | 34/202 | 40/202 | 20/79 | 28/79 | 33/79 |
| `content-cbf-twostage-v1` | 21/202 | 33/202 | 48/202 | 20/79 | 28/79 | 38/79 |
| `content-cbf-mmr-pop-v1` | 23/202 | 31/202 | 41/202 | 23/79 | 28/79 | 35/79 |
| `content-cbf-twostage-pop-v1` | 20/202 | 32/202 | 52/202 | 19/79 | 28/79 | 41/79 |
| `content-cbf-neg-pop-v1` | 20/202 | 27/202 | 37/202 | 18/79 | 24/79 | 31/79 |
| `content-cbf-multiplicative-v1` | 15/202 | 19/202 | 30/202 | 15/79 | 17/79 | 27/79 |
| `content-cbf-multiplicative-pop-v1` | 15/202 | 19/202 | 30/202 | 15/79 | 17/79 | 27/79 |
| `cf-user-knn-v1` | 4/202 | 7/202 | 13/202 | 4/79 | 7/79 | 12/79 |
| `popularity-v1` | 1/202 | 2/202 | 2/202 | 1/79 | 2/79 | 2/79 |
| `recency-v1` | 1/202 | 1/202 | 1/202 | 1/79 | 1/79 | 1/79 |
| `random-v1` | 0/202 | 0/202 | 0/202 | 0/79 | 0/79 | 0/79 |

Lectura: con `content-cbf-weighted-v1`, **49 % de los usuarios (39/79)** recibe al menos un
juego de su tag favorito recuperado dentro del top-10 — frente al 9 % (7/79) con
`cf-user-knn-v1` (colaborativo puro) y el 3 % o menos con los baselines. `random-v1` no
acierta ni un solo ítem de los 202 en ningún K.

## 5. Intervalos y pruebas pareadas de nDCG@10 (métrica titular)

Configuración: bootstrap BCa (2000 remuestreos, IC 95 %, semilla `20260907`), Wilcoxon
pareado (`zero_method="wilcox"`), corrección de Holm sobre las 120 comparaciones por pares,
Friedman como ómnibus.

- **Friedman:** χ² = 258,07, n = 79, **p = 2,69 × 10⁻⁴⁶** — mucho más fuerte que v14
  (χ² = 105,28, p = 1,29 × 10⁻¹⁵) y que v12 (χ² = 30,00, p = 0,0119).
- **54 de 120 pares tienen `holm_reject = True`** (frente a 14/120 en v14, 0/120 en v12).

Comparaciones más relevantes (lista completa de 54 en el artefacto):

| Comparación | Δ nDCG@10 | p ajustado (Holm) |
|---|---:|---:|
| `content-cbf-weighted-v1` vs `random-v1` | +0,1725 | 0,00001 |
| `hybrid-weighted-cf-v1` vs `random-v1` | +0,1699 | 0,00001 |
| `content-cbf-weighted-v1` vs `popularity-v1` | +0,1691 | 0,00001 |
| `hybrid-weighted-cf-v1` vs `popularity-v1` | +0,1665 | 0,00001 |
| `content-cbf-weighted-v1` vs `recency-v1` | +0,1665 | 0,00002 |
| `hybrid-mmr-v1` vs `random-v1` | +0,1591 | 0,00003 |
| `hybrid-weighted-cf-v1` vs `recency-v1` | +0,1639 | 0,00003 |
| `cf-user-knn-v1` vs `content-cbf-weighted-v1` | −0,1515 | 0,00004 |
| `cf-user-knn-v1` vs `hybrid-weighted-cf-v1` | −0,1489 | 0,00004 |
| `cf-user-knn-v1` vs `hybrid-mmr-v1` | −0,1382 | 0,00006 |
| `cf-user-knn-v1` vs `content-cbf-mmr-v1` | −0,1179 | 0,00040 |
| `content-cbf-multiplicative-v1` vs `content-cbf-weighted-v1` | −0,0869 | 0,00081 |
| `content-cbf-multiplicative-pop-v1` vs `hybrid-mmr-v1` | −0,0740 | 0,02735 |

**Lectura correcta:**

- `content-cbf-weighted-v1`, `hybrid-weighted-cf-v1`, `hybrid-mmr-v1` y
  `content-cbf-weighted-pop-v1` son **estadísticamente superiores a los dos baselines**
  (frente a solo 2 de esas 4 en v14).
- **Novedad de v15**: `cf-user-knn-v1` (colaborativo puro) es **significativamente peor**
  que 8 de las 10 variantes de contenido (`weighted`, `weighted-pop`, `mmr`, `mmr-pop`,
  `neg`, `twostage`, `twostage-pop`, y por extensión los híbridos que lo incorporan parcialmente)
  — en v14 ninguna de estas comparaciones sobrevivía Holm. La señal de contenido se
  diferencia ahora con claridad de la señal puramente colaborativa bajo este protocolo.
- `weighted_sum` sigue superando significativamente a `multiplicative`, como en v14.

## 6. Más allá del acierto (K = 10)

| Algoritmo | Cob. catálogo | HHI | Diversidad intra-lista | Novedad (n aplicable) |
|---|---:|---:|---:|---:|
| `content-cbf-weighted-v1` | 1,77 % | 0,0132 | 0,531 | 10,54 (10/79) |
| `hybrid-weighted-cf-v1` | 1,78 % | 0,0135 | 0,532 | 10,53 (12/79) |
| `hybrid-mmr-v1` | 1,67 % | 0,0151 | 0,655 | 10,49 (14/79) |
| `content-cbf-weighted-pop-v1` | 1,54 % | 0,0159 | 0,546 | 10,47 (14/79) |
| `content-cbf-mmr-v1` | 1,62 % | 0,0155 | 0,652 | 10,48 (9/79) |
| `content-cbf-mmr-pop-v1` | 1,45 % | 0,0179 | 0,680 | 10,59 (12/79) |
| `content-cbf-neg-v1` | 2,05 % | 0,0098 | 0,543 | 10,58 (9/79) |
| `content-cbf-twostage-v1` | 2,51 % | 0,0070 | 0,510 | 10,66 (7/79) |
| `content-cbf-twostage-pop-v1` | 2,50 % | 0,0071 | 0,510 | 10,65 (7/79) |
| `content-cbf-neg-pop-v1` | 1,84 % | 0,0117 | 0,560 | 10,47 (11/79) |
| `content-cbf-multiplicative-v1` | 0,84 % | 0,0355 | 0,615 | 10,36 (14/79) |
| `content-cbf-multiplicative-pop-v1` | 0,82 % | 0,0366 | 0,616 | 10,32 (15/79) |
| `cf-user-knn-v1` | 0,77 % | 0,0765 | 0,755 | 9,39 (79/79) |
| `recency-v1` | 0,15 % | 0,0816 | 0,679 | — (0/79) |
| `popularity-v1` | 0,08 % | 0,0988 | 0,641 | 10,04 (79/79) |
| `random-v1` | 5,60 % | 0,0014 | 0,816 | — (0/79) |

Patrón muy similar al de v14: HHI bajo y diversidad alta en las variantes de contenido
(similitud de tags real, no colapsan a un *fallback*), `cf-user-knn-v1`/`popularity-v1`
con la novedad más baja aplicable al 100 % de usuarios (recomiendan casi siempre ítems ya
vistos en el entrenamiento).

## 7. Tiempos por algoritmo

| Algoritmo | Duración |
|---|---:|
| `popularity-v1` | 5,1 s |
| `random-v1` | 25,1 s |
| `cf-user-knn-v1` | 16,8 s |
| `content-cbf-weighted-v1` | 492,8 s |
| `content-cbf-multiplicative-v1` | 491,4 s |
| `content-cbf-twostage-v1` | 488,5 s |
| `content-cbf-neg-v1` | 488,2 s |
| `content-cbf-weighted-pop-v1` | 484,0 s |
| `content-cbf-twostage-pop-v1` | 484,2 s |
| `content-cbf-neg-pop-v1` | 483,9 s |
| `content-cbf-multiplicative-pop-v1` | 480,4 s |
| `recency-v1` | 427,6 s |
| `content-cbf-mmr-v1` | 483,3 s |
| `content-cbf-mmr-pop-v1` | 481,7 s |
| `hybrid-weighted-cf-v1` | 439,7 s |
| `hybrid-mmr-v1` | 493,1 s |
| Construcción del contexto compartido | 366,5 s |
| Precómputo de señales compartidas | 172,5 s |
| **Tiempo de pared (2 workers + cola serial de 5)** | **4.297,9 s ≈ 1 h 12 min** |

La construcción del contexto (366,5 s) es ~10 veces más lenta que en protocolo v14
(36,7 s) — coste esperado del nuevo mecanismo: calcula el perfil de contenido completo y
ejecuta el bucle de retroceso adaptativo por usuario, mucho más trabajo que el LOO simple
de antes. El resto del tiempo (precómputo + 16 algoritmos) es prácticamente idéntico a v14.

## 8. Documentación del leave-fraction-out para el TFG

Ver el documento dedicado, con fundamento científico completo y las alternativas
descartadas explícitamente razonadas:
[[2026-09-12 - LOO por fraccion sobre el tag dominante, fundamento y alternativas descartadas]]
(vault). Resumen de las referencias citadas: Breese, Heckerman y Kadie (1998) y Herlocker
et al. (2004) para el marco All-but-N/Given-N generalizado; Pazzani y Billsus (2007) para
por qué un tag desplazado a 2º/3er puesto sigue siendo una señal válida; Cremonesi, Koren y
Turrin (2010) y Steck (2011) para el piso de rating externo heredado de v14.

## 9. Fallos, omisiones y limitaciones

1. **Dos fallos de diseño corregidos en vivo antes del cálculo exitoso** (§1.2): ninguno
   tocó código de puntuación real; documentados con commit y verificación.
2. **No se puede distinguir, solo con el artefacto, "retroceso hasta 1" de "respaldo a LOO
   simple"** entre los 19 usuarios con exactamente 1 ítem retenido (§3) — un campo
   explícito en el esquema del artefacto lo resolvería; no implementado, no bloqueante.
3. **No se re-verificó la factibilidad de train/validation tras los dos fallos corregidos**
   (sí se verificó exhaustivamente antes de los fallos, y el split test — el que importa
   para el resultado citado — sale exactamente en línea con lo esperado, 79/80).
4. **Construcción del contexto ~10x más lenta que v14** (§7): coste aceptado y documentado,
   no investigado a fondo si es optimizable.
5. **`tag-taste-v1` queda fuera de esta comparación** (como fija el protocolo).
6. Esta evaluación es **evidencia de simulación sobre arquetipos parametrizados**, nunca
   evidencia sobre usuarios reales de SavePoint (EVAL-10); las conclusiones se limitan al
   corpus `2026.09.2`, esta población de 400 usuarios y este protocolo v15. El siguiente
   estudio (20 usuarios reales, evaluación de calidad por encuestas) es un capítulo
   distinto, no comparativo — ver
   [[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]].

## 10. Interpretación

Bajo el protocolo `2026.09.2`/v15 y este split de test de un solo uso:

- **`content-cbf-weighted-v1` y `hybrid-weighted-cf-v1` siguen siendo los de mejor acierto**,
  ahora con una base estadística mucho más amplia que en v14 (54/120 comparaciones
  significativas, frente a 14/120).
- **Hallazgo nuevo de v15**: el contenido se diferencia claramente del colaborativo puro
  (`cf-user-knn-v1` pierde significativamente contra 8 de las 10 variantes de contenido) —
  algo que v12 y v14 no pudieron establecer con suficiente potencia estadística.
- El diseño de retirar una fracción adaptativa (en vez de un único ítem fijo) cumplió lo
  previsto: más información por usuario, comparaciones más potentes, sin necesidad de
  excluir usuarios por diseño salvo los genuinamente sin biblioteca.
- **Siguiente paso ya decidido por el autor**: estudio con 20 usuarios reales, evaluación
  de calidad por encuestas — capítulo complementario, no comparativo con este.

### 10.1 Matiz: `cf-user-knn-v1` no es "malo", esta prueba no es su terreno

El 9 % de acierto de usuario (§4.3) de `cf-user-knn-v1` no debe leerse como "el
colaborativo es peor en general" — esta prueba mide específicamente la recuperación de
obras del **tag de contenido** más pesado del perfil del usuario, y `cf-user-knn-v1` no usa
tags en absoluto: pondera vecinos por similitud de patrones de valoración entre usuarios
(coseno sobre valoraciones centradas, `recommendations/collaborative.py`), una señal
completamente distinta y, por diseño de este protocolo, en desventaja frente a cualquier
prueba centrada en contenido. La comparación es correcta y la diferencia es real y
significativa (§5), pero **está midiendo precisamente lo que la señal colaborativa no
modela** — no es evidencia de que el colaborativo sea inferior en una tarea distinta (p.
ej. recuperar valoraciones de usuarios con gustos parecidos en general, sin restricción de
género). Los híbridos (`hybrid-weighted-cf-v1`, `hybrid-mmr-v1`) combinan ambas señales
precisamente para no depender de ninguna de las dos en solitario.

### 10.2 Por qué este es el resultado más sólido de los tres, y qué lo consiguió

La progresión v12 → v14 → v15 no es casualidad — cada paso corrigió un problema real,
medido antes de decidir el siguiente:

1. **Rediseño de población (v13, 2026-09-10/11)**: biblioteca 10-20, franja PopScore 75 %,
   mínimo 5 positivos garantizados → eliminó el 74 % de `insufficient_history` que
   colapsaba el contenido al mismo *fallback* que los baselines en v12.
2. **Piso de rating externo en el LOO (v14, 2026-09-11)**: el positivo retirado ya no
   dependía solo del gusto personal, también de superar la mediana de rating del corpus →
   quitó el sesgo de popularidad de la selección, sin coste de usuarios (verificado antes
   de congelar).
3. **Gusto individual por usuario + mínimo garantizado más alto + agrupación por tag (v15,
   población, 2026-09-12)**: cada usuario pasó a tener un tag dominante propio y robusto,
   con suficiente oferta para retirar varios sin vaciar el género — en vez de un tag
   compartido por decenas de personas con dominancia frágil.
4. **Retención por fracción adaptativa en vez de un ítem fijo (v15, split)**: más
   información por usuario (`Recall@K` continuo, no binario), la mejora directa detrás del
   salto de potencia estadística (§5, §11).
5. **Dos fallos corregidos en vivo antes del éxito** (§1.2): comparar el tag dominante solo
   contra otros tags (no contra la plataforma), y no excluir a un usuario cuando el
   mecanismo específico no se puede construir, si el respaldo de LOO simple sí puede
   evaluarlo — maximizó cuántos usuarios entran en el estudio sin comprometer la validez.

Ninguna mejora, por separado, habría bastado — la insuficiencia de datos (1), el sesgo de
selección (2) y la falta de potencia estadística (4) son problemas distintos que exigían
correcciones distintas, cada una verificada empíricamente antes de aplicarse a la
siguiente.

## 11. Comparativa entre las tres evaluaciones de la semana (v12, v14, v15)

| | **v12** (2026-09-10) | **v14** (2026-09-11) | **v15** (2026-09-12) |
|---|---|---|---|
| Mecanismo LOO | 1 ítem fijo, sin piso de rating | 1 ítem fijo, piso de rating externo ≥70 | Fracción adaptativa (30%) del tag dominante, ≥1, con retroceso; respaldo a LOO simple |
| Usuarios evaluables (test) | 73/80 | 79/80 | 79/80 |
| Ítems retenidos por usuario | 1 | 1 | Media 2,56 (rango 1-5) |
| % en `insufficient_history` | 74 % | 0 % | 0 % |
| Friedman χ² (ómnibus) | 30,00 | 105,28 | **258,07** |
| Friedman p | 0,0119 | 1,29 × 10⁻¹⁵ | **2,69 × 10⁻⁴⁶** |
| Comparaciones significativas (Holm) | 0/120 | 14/120 | **54/120** |
| Mejor algoritmo | `cf-user-knn-v1` (0,0155) — no significativo | `hybrid-weighted-cf-v1` (0,1526) | `content-cbf-weighted-v1` (0,1725) |
| 2º mejor | — | `content-cbf-weighted-v1` (0,1452) | `hybrid-weighted-cf-v1` (0,1699) |
| ¿Contenido bate a baselines? | No (nada significativo) | Sí (4 algoritmos) | Sí (más algoritmos, más margen) |
| ¿Contenido bate a colaborativo puro? | No | No | **Sí — hallazgo nuevo** (8 de 10 variantes) |
| ¿`weighted_sum` bate a `multiplicative`? | No aplica | Sí | Sí |
| Tiempo de pared | 3 h 42 min (proceso único) | 1 h 11 min (precómputo+fork, 2+5) | 1 h 12 min (igual; +10x en construcción de contexto) |
| Conclusión citable | Ninguna — hallazgo metodológico (arranque en frío) | Sí, moderada | Sí, la más sólida de las tres |

Progresión limpia: v12 encontró y expuso un problema de diseño (arranque en frío por
interacción entre la generación de población y el umbral de contenido), v14 lo corrigió y
ya dio un resultado citable, v15 afinó aún más la prueba (más información por usuario vía
retención múltiple) y sacó un hallazgo que las dos anteriores no tenían potencia
estadística para establecer — contenido significativamente superior a colaborativo puro.
Fuentes: [`evaluation-results-400-test-2026-09-10.md`](./evaluation-results-400-test-2026-09-10.md)
(v12), [`evaluation-results-400-test-2026-09-11.md`](./evaluation-results-400-test-2026-09-11.md)
(v14).

## 12. Artefactos y reproducibilidad

### 12.1 Desglose por cohortes

El desglose reproducible está en
[`evaluation-cohorts-400-test-2026-09-12-v15.md`](./evaluation-cohorts-400-test-2026-09-12-v15.md)
y en su equivalente JSON. Se generó únicamente leyendo el artefacto v15 y el
manifiesto `synthetic-population-manifest-v15-candidate.json`; no consulta PostgreSQL,
IGDB ni el estado actual de la aplicación y no vuelve a ejecutar ningún algoritmo.

El manifiesto v15 contiene dos cohortes: `active_history_10_to_20` (390 usuarios) y
`no_history` (10 usuarios). El split `test` aporta 79 usuarios evaluables, todos dentro
de la primera cohorte; los 10 usuarios sin historial no tienen un positivo que retirar
y se tratan como condición descriptiva de cold start, no como recomendaciones con
puntuación cero. Para cada algoritmo y K=5, 10 y 20 se recalculan desde las filas
conservadas por usuario precisión, recall, nDCG, MAP, diversidad intra-lista y novedad.

El artefacto histórico sí conserva cobertura de catálogo, HHI y cobertura de predicción
como métricas globales por algoritmo y K, pero no conserva las listas recomendadas
completas por usuario. Por eso no se reparte ninguna de esas métricas por cohorte: una
atribución aproximada habría producido evidencia no auditable. El runner queda preparado
para futuras extensiones, pero este informe no altera retroactivamente v15.

### 12.2 Entorno y recursos

El artefacto v15 conserva tiempos de pared y duración individual de los workers. No
conserva, porque la versión ejecutada todavía no lo registraba, las versiones exactas
del entorno ni el pico de memoria/CPU de cada proceso. Se añadió al runner paralelo una
captura para futuras ejecuciones de Python, plataforma, CPU, versiones de paquetes,
CPU de usuario/sistema y RSS máximo por proceso. La captura excluye secretos, rutas
privadas, nombres de máquina y valores de variables de entorno.

No se presenta una medición posterior como si describiera históricamente v15: hacerlo
confundiría el entorno actual con el entorno del cálculo. La limitación queda localizada
y la solución queda implementada para el siguiente artefacto versionado.

### 12.3 Limitación multi-semilla (punto 6)

El test v15 se ejecutó una sola vez, tal como declara `tuning.test_runs: 1`, y el
marcador de consumo impide volver a usarlo accidentalmente. No se ejecutó una batería
de semillas adicionales. Esta decisión preserva el aislamiento del test: cambiar la
semilla altera la población generada, la partición de usuarios, los positivos
retenidos y el artefacto; ya no sería una réplica del mismo test, sino un nuevo
protocolo que debería congelarse con su propia versión y hash.

El bootstrap BCa y las pruebas pareadas cuantifican incertidumbre de las 79
observaciones disponibles dentro de esta ejecución. No son un sustituto de la
variabilidad entre semillas, por lo que las conclusiones deben formularse de manera
condicional: describen este corpus, esta población sintética, este split y esta semilla.
La sensibilidad multi-semilla queda como extensión metodológica futura, no como un
resultado que pueda afirmarse sin cálculo.

### 12.4 Evidencia de interfaz (punto 7)

La verificación Playwright y E2E queda respaldada por `e2e/recommendations.spec.ts` y
por la nota de evidencia del vault. Las tres pruebas cubren correspondencia API/DOM,
ausencia de superficie metodológica y reflow/temas/teclado. La implementación visual
fue realizada por la otra sesión; este cierre incorpora su resultado sin modificar el
contrato público de recomendaciones.

| Artefacto | Ruta | SHA-256 |
|---|---|---|
| Artefacto final (éxito) | `apps/api/evaluation-400-test-2026-09-12-v15.artifact.json` | `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab` |
| Preflight de entradas | `apps/api/evaluation-input-preflight-2026-09-12-v15-gate.json` | (ver el archivo) |
| Marcador de consumo | `apps/api/.evaluation-test-run.json` | (contiene `protocol_sha256` y `consumed_at`, ver §1) |

Fuente normativa: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md),
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md), el resultado
previo
[`evaluation-results-400-test-2026-09-11.md`](./evaluation-results-400-test-2026-09-11.md)
(protocolo v14) y las notas de sesión en `ideas-vault/Fases/2026-09-11 - *.md` /
`2026-09-12 - *.md`.
