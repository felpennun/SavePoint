---
tags: [fase/3, fase/4, tema/evaluacion, tema/recomendadores, resultado]
---

# Evaluación offline final — protocolo 15, 400 usuarios, split test

Cálculo final del harness congelado ejecutado con éxito el 2026-09-12 (al tercer intento;
los dos primeros se detuvieron a propósito, sin coste, al encontrar dos fallos de diseño
reales — ver más abajo), consumiendo el split `test` de protocolo v15
(`protocol_sha256 d492cfe3...`) una sola vez. Fuente canónica y completa:
[[../../docs/verification/evaluation-results-400-test-2026-09-12-v15.md|evaluation-results-400-test-2026-09-12-v15.md]].
Sustituye al resultado de protocolo v14
([[2026-09-11 - Evaluación offline final protocolo 14 (400 usuarios, test)]]).

## Resultado, en una frase

**El resultado más rico y estadísticamente potente de las cuatro corridas de esta semana.**
Friedman ómnibus: χ² = 258,07, p = 2,69 × 10⁻⁴⁶ (n = 79) — 54 de 120 comparaciones por pares
sobreviven Holm (v14: 14/120; v12: 0/120). `content-cbf-weighted-v1` (nDCG@10 = 0,1725) y
`hybrid-weighted-cf-v1` (0,1699) siguen ganando, pero ahora con una diferenciación nueva:
**el contenido supera significativamente al colaborativo puro** (`cf-user-knn-v1` pierde
contra 8 de las 10 variantes de contenido) — algo que v12 y v14 no pudieron establecer.

## Qué cambió respecto a v14

El leave-one-out de un único positivo se sustituye por un **leave-fraction-out adaptativo**
centrado en el tag de contenido más pesado del perfil de cada usuario: se retira
`ceil(0,3 × tamaño_del_pool)` de sus obras de ese tag (nunca menos de 1), con retroceso si
eso desplazara el tag de la primera posición en el perfil restante. Fundamento científico
completo (marco All-but-N/Given-N, por qué un tag desplazado sigue siendo señal válida, y
qué alternativas se descartaron y por qué):
[[2026-09-12 - LOO por fraccion sobre el tag dominante, fundamento y alternativas descartadas]].

## Dos fallos encontrados y corregidos en vivo (mismo día, antes del éxito)

1. El "tag dominante" se buscaba mezclando familias de faceta (`tag:*` contra
   `platform:*`) — un usuario con casi toda su biblioteca en una plataforma podía quedar
   excluido sin motivo real. Corregido restringiendo la búsqueda a `tag:*` (commit
   `ed25fe8`).
2. Un usuario para el que el mecanismo por fracción no se podía construir quedaba excluido
   del estudio entero en vez de caer al LOO simple. Corregido con una caída explícita
   (commit `81df38b`) — solo quedan fuera los usuarios sin ningún positivo elegible.

Ninguno de los dos tocó código de puntuación real (`facet_similarity`/`combine`) — estaban
aislados en la selección de candidatas para este estudio nuevo.

## Cifras clave

- 79/80 usuarios evaluables en test (igual que v14) — el respaldo a LOO simple recupera
  exactamente a quienes el mecanismo por fracción no podría haber evaluado por sí solo.
- Media de 2,56 ítems retenidos por usuario (rango 1-5), frente a exactamente 1 en v12/v14.
- Construcción del contexto compartido ~10 veces más lenta que v14 (366,5 s vs 36,7 s) —
  coste esperado del nuevo mecanismo (perfil completo + retroceso adaptativo por usuario).

## Siguiente paso

Estudio con 20 usuarios reales, evaluación de calidad por encuestas — capítulo
complementario, no comparativo. Ver
[[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]].

Commits relevantes en `main`: `10f3e8f`, `51df245`, `ed25fe8`, `81df38b`, y el de este
documento.
