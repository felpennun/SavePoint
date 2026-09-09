---
quick_id: 260909-msb
status: complete
---

# Resumen

Web y offline comparten ahora `rating_confidence`: rating IGDB normalizado con
potencia 2, modulado por el volumen logarítmico normalizado de
`total_rating_count` con suelo 0,80 y refuerzo máximo del 20 %. El volumen no
se suma de nuevo como señal independiente. `display_rating` permanece fuera
del ranking.

La rejilla offline se actualizó para declarar `rating_confidence`, y el
contrato pasó a protocolo v3 para invalidar la configuración anterior de forma
reproducible. Los workers siguen consumiendo el mismo registro de algoritmos
que el runner offline.

## Verificación

- Recomendaciones y evaluación: 180 pruebas pasadas.
- Frontend: 9 pruebas de recomendaciones pasadas.
- TypeScript: `tsc --noEmit` correcto.
