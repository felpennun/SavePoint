---
quick_id: 260909-tub
status: complete
---

# Resumen: rating bayesiano reproducible

Se sustituyó el multiplicador lineal de volumen por
`rating-confidence-v4-bayesian`: media previa IGDB congelada, ponderada por
`total_rating_count`, con fuerza fija de 25 observaciones. El ajuste se aplica
antes de la potencia cuadrática de calidad y el volumen no se aplica una
segunda vez.

Web, workers y evaluación offline llaman al mismo ranker. El protocolo se
elevó a v8 y la huella de configuración cambia, por lo que no se reutilizan
snapshots incompatibles. Se recalcularon los diez workers de `felipe` para la
revisión 14: 10/10 terminaron y el snapshot se publicó atómicamente.

Verificación: 195 pruebas backend de recomendaciones/evaluación, TypeScript
correcto y contraste documentado de Silksong frente a Terraria en
`docs/verification/recommendation-bayesian-rating-felipe-2026-09-09.md`.

