---
quick_id: 260909-sla
status: complete
completed: 2026-09-09
---

# Resumen: contrato fs-v9 y PopScore reforzado

## Resultado

Se consolido `fs-v9` / `facet-similarity-v5` como contrato compartido por el
ranker web, los workers y la evaluacion offline. F0,5 queda fijado para el
nucleo de genero/plataforma; los bonus opcionales son 0,02 para saga/franquicia
y 0,015 para desarrollador. Posteriormente se aumento moderadamente el peso de
PopScore sin alterar su normalizacion.

La configuracion final de PopScore es:

- Weighted-Pop y Negative-Pop: contenido 0,55, rating-confidence 0,25,
  PopScore 0,20.
- Multiplicative-Pop: `swing = 0,20`, factor entre 0,80 y 1,20.
- Two-Stage-Pop: rating-confidence 0,80 y PopScore 0,20 en el desempate.
- Recency: contenido 0,20, rating-confidence 0,20, PopScore 0,20 y recencia
  0,40.

La ausencia de PopScore sigue imputandose a 0,0. El protocolo offline pasa a
version 7 y los guards de web/offline se actualizaron para aceptar esa version.

## Verificacion

- Cache fs-v9: 190.479 vectores para `2026.09.2`.
- Workers de Felipe: 10/10 `succeeded`; snapshot activo publicado en revision
  14 con la nueva huella.
- Backend: `194 passed`.
- Web: `tsc --noEmit` correcto.
- Reevaluacion de Felipe archivada en
  `docs/verification/recommendation-fs-v9-comparison-felipe-2026-09-09.md`.
- No se ejecuto la evaluacion offline de los 400 usuarios.
