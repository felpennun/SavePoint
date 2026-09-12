---
tags: [fase-04, recomendadores, evaluacion, decision, limitacion]
estado: aceptada-con-limitacion
fecha: 2026-09-12
---

# Cierre de Fase 4: comparativa colaborativa e híbrida

La Fase 4 queda aceptada por Felipe el 2026-09-12. Se incorporaron
`cf-user-knn-v1` y `hybrid-weighted-cf-v1` a web y offline, con candidatos,
exclusiones, explicaciones y fallbacks compartidos. También se verificaron los
workers y el runner offline paralelo.

## Evidencia

- [[../../docs/verification/phase-04-signoff-2026-09-12|Firma de cierre de Fase 4]].
- [[../../.planning/phases/04-collaborative-and-hybrid-comparison/04-VERIFICATION|Verificación de Fase 4]].
- [[../../docs/verification/evaluation-results-400-test-2026-09-12-v15|Resultados offline v15]].
- [[../../docs/verification/evaluation-checkpoint-400-users-2026-09-12-v15|Checkpoint offline v15]].

El cálculo v15 terminó con 16/16 algoritmos y 79/80 usuarios evaluables. El
runner registró `max_workers=2`, `serial_tail=5` y 4.297,9 segundos de tiempo de
pared. Los artefactos conservan métricas, resultados por usuario, cobertura,
diversidad, novedad, contrastes pareados y tiempos.

## Limitación aceptada

El split `test` se consumió una sola vez y la evaluación usa una única semilla.
El bootstrap y los contrastes pareados describen incertidumbre interna, pero no
sustituyen una sensibilidad multi-semilla. Esta extensión queda delimitada como
trabajo futuro y requerirá un protocolo y artefactos nuevos. Las conclusiones
actuales se restringen a la población sintética, corpus, protocolo y semilla
congelados.

## Requisitos

REC-04, REC-05 y DOC-03 pasan a completos. El siguiente paso de planificación es
la Fase 5.
