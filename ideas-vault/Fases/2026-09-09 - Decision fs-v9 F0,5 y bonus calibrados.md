# Decision fs-v9: F0,5 y bonus calibrados

Fecha: 2026-09-09

## Decision

Se congela `fs-v9` / `facet-similarity-v5` como contrato compartido de web,
workers y evaluacion offline. El nucleo genero/plataforma mantiene F0,5
(`beta = 0,5`), con pesos 0,50 y 0,25. La saga/franquicia usa un bonus maximo
de 0,02 y el desarrollador un bonus maximo de 0,015.

Los bonus solo se activan por coincidencia con el perfil ponderado del usuario.
La suma opcional maxima es 0,035; no se concede puntuacion por tener una saga o
desarrollador cualquiera, ni se penaliza la ausencia de estas facetas.

## Motivo

F0,5 reduce la ventaja de candidatos con listas de generos o plataformas muy
amplias al dar mas peso a la precision. Los bonus 0,02 y 0,015 conservan el
valor explicativo de saga y desarrollador sin permitir que dominen las señales
principales de calidad, contenido y popularidad.

## Evidencia

- Cache fs-v9: 190.479 vectores para `2026.09.2`.
- Workers de Felipe: 10/10 completados, revision publicada 14.
- Comparacion reproducible: [`recommendation-fs-v9-comparison-felipe-2026-09-09.md`](../../docs/verification/recommendation-fs-v9-comparison-felipe-2026-09-09.md).
- Contrato canonico: [`protocol.json`](../../docs/methodology/protocol.json).

## Refuerzo posterior de PopScore

Se aumenta moderadamente el peso de PopScore, conservando sus señales y su
normalizacion. Las variantes Weighted-Pop y Negative-Pop usan
contenido 0,55, rating-confidence 0,25 y PopScore 0,20; Multiplicative-Pop usa
`swing = 0,20`; Two-Stage-Pop usa 0,80 para rating-confidence y 0,20 para
PopScore; y Recency usa 0,20 para contenido, rating-confidence y PopScore, con
0,40 para recencia. El protocolo pasa a la version 7 para que el cambio quede
separado y reproducible.
