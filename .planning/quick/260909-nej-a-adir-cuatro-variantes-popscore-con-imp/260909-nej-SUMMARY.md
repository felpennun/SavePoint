---
quick_id: 260909-nej
status: complete
completed_at: "2026-09-09"
---

# Resumen: variantes PopScore con imputación mínima

Se añadieron cuatro variantes publicables manteniendo intactos los baselines
anteriores: suma ponderada, combinación multiplicativa, dos etapas y suma con
señal negativa. Las cuatro usan `popscore_missing_floor: 0.0`, sin
renormalización, y conservan `popscore_imputed` para hacer auditable la
imputación. `recency-v1` adopta la misma política mientras mantiene
`recency_score` como señal adicional.

La comparación offline y la web comparten `ALGORITHM_REGISTRY` y
`rank_content_v1`. El protocolo se actualizó a v4 y la rejilla a 28
configuraciones. Compose incorpora los cuatro workers nuevos; la página de
recomendaciones incorpora sus cuatro estanterías y traducciones explicativas.

## Verificación

- Backend: 181 pruebas de recomendaciones y evaluación pasadas.
- Frontend: 9 pruebas Vitest pasadas y `tsc --noEmit` correcto.
- `docker compose config --quiet`: correcto.
- API, web, base de datos y los diez workers: ejecutándose; API y web
  saludables, web HTTP 200.
- No se lanzó la evaluación offline ni se generaron resultados experimentales.
