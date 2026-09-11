---
tags: [fase/3, fase/4, tema/evaluacion, tema/recomendadores, resultado]
---

# Evaluación offline final — protocolo 14, 400 usuarios, split test

Cálculo final del harness congelado ejecutado con éxito el 2026-09-11, consumiendo el
split `test` de protocolo v14 (`protocol_sha256 7b255fb2c0...`) una sola vez. Fuente
canónica y completa:
[[../../docs/verification/evaluation-results-400-test-2026-09-11.md|evaluation-results-400-test-2026-09-11.md]].
Sustituye al resultado de protocolo v12
([[2026-09-11 - Evaluación offline final protocolo 12 (400 usuarios, test)]]), que quedaba
dominado por un hallazgo metodológico (74 % `insufficient_history`) en vez de un resultado
comparativo.

## Resultado, en una frase

**Esta vez sí hay ganador estadísticamente defendible.** `hybrid-weighted-cf-v1`
(nDCG@10 = 0,1526) y `content-cbf-weighted-v1` (0,1452) superan significativamente a
`random-v1`, `popularity-v1` (y también a `recency-v1`) tras corrección de Holm sobre 120
comparaciones — 14 de 120 sobreviven, frente a 0/120 en el cálculo de v12. Friedman
ómnibus: χ² = 105,28, p = 1,29 × 10⁻¹⁵, n = 79.

## Qué cambió respecto a v12 para llegar aquí

1. **Rediseño de población (protocolo v13, 2026-09-10/11):** biblioteca 10-20, franja
   PopScore 75 % redondeada al alza, mínimo 5 positivos elegibles garantizados por
   biblioteca. Resultado: 0 % `insufficient_history` en el split test (era 74 % en v12) —
   las diez variantes de contenido usan similitud de tags real para el 100 % de los
   usuarios.
2. **Piso de rating externo en el LOO (protocolo v14, hoy):** el positivo retirado debe
   tener rating IGDB ≥ 70 además de cumplir el gusto personal del usuario — corrige un
   sesgo de popularidad conocido en la literatura (Cremonesi, Koren y Turrin, 2010; Steck,
   2011). Verificado: cuesta 0 usuarios sobre los 400. Ver
   [[2026-09-11 - Piso de rating externo en LOO y paralelizacion offline]].
3. **Optimizaciones de rendimiento** (cache de señales offline y web, precómputo +
   fork): 3 h 42 min → 1 h 11 min de pared para el mismo número de algoritmos, sin cambiar
   ningún valor puntuado. Ver
   [[2026-09-11 - Cache de señales compartidas offline y web]].

## Hallazgos secundarios

- El modo de combinación `weighted_sum` supera significativamente a `multiplicative` en
  las comparaciones directas disponibles — la única diferenciación entre variantes de
  contenido *entre sí* (no solo contra baseline) que sobrevive Holm.
- `cf-user-knn-v1` (colaborativo puro) no se diferencia significativamente de ningún otro
  algoritmo pese a tener nDCG@10 = 0,0525, por debajo de las variantes `weighted_sum`.
- Concentración (HHI) y diversidad intra-lista mejoran drásticamente frente a v12
  (HHI 0,55-0,71 → 0,005-0,03; diversidad 0,006-0,12 → 0,50-0,61) — consecuencia directa
  de que el contenido ya no colapsa al mismo *fallback* que los baselines.

## Siguiente paso (decisión ya tomada por el autor, no ejecutada en esta tarea)

Estudio con 20 usuarios reales, biblioteca propia, evaluación de calidad por encuestas —
capítulo de evaluación distinto y complementario, no comparativo con este resultado. Ver
[[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]].

Commits relevantes en `main`: `349f390`, `9b7ff13`, y el commit de este documento.
