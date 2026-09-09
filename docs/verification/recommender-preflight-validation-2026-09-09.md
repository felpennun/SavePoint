---
fecha: 2026-09-09
estado: verificado
---

# Validación previa y archivo de resultados

Este documento registra los controles 4 y 5 previos al lanzamiento de algoritmos.
La evidencia estructurada está en [recommender-input-preflight-2026.09.2.json](recommender-input-preflight-2026.09.2.json).

## Control 4: validación final

Resultado: **PASS**.

- Corpus gobernado: **190.479** obras.
- Candidatas a algoritmo: **30.623**.
- Obras gobernadas con fecha ausente o posterior al `2026-09-09`: **0**.
- Candidatas con fecha ausente o futura: **0**.
- Candidatas que incumplen `total_rating_count >= 1 OR rating IS NOT NULL`: **0**.
- Población activa/histórica: **400 / 200**, con solapamiento **0**.
- Split: **240 train / 80 validation / 80 test**.
- Protocolo: versión **2** y vector **fs-v4**.

## Control 5: contrato y archivo reproducible

Resultado: **PASS**.

- Rejilla total: **24** configuraciones.
- Modos: **15 weighted_sum / 3 multiplicative / 6 two_stage**.
- Configuraciones con `recency_score`: **6**, exclusivamente en la familia prevista.
- Todas las configuraciones usan `user_rating`.
- Ninguna usa `total_rating` combinado con crítica.
- Se guardaron los resultados completos, incluyendo cobertura, nulos, corpus, población,
  rejilla y estado de ejecución.
- Estado de ejecución: `not_run`.

## Conclusión

Los datos y el contrato están validados y archivados para iniciar la siguiente fase. No se
han ejecutado rankings, tuning ni evaluación del conjunto de test.
