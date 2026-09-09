---
quick_id: 260909-o1u
status: complete
completed_at: 2026-09-09
---

# Resumen

Se implementó la nueva intensidad de valoración personal y la recencia por año natural en el
núcleo compartido de recomendaciones. El perfil web, los workers y el runner offline consumen la
misma lógica; no se ejecutó ninguna evaluación experimental ni se recalcularon recomendaciones.

## Cambios realizados

- Las valoraciones personales de los juegos semilla se normalizan y elevan a potencia 2 antes de
  sumarse al peso del estado: `completed = 3`, `playing = 2`, `pending = 1`, `abandoned = 0`.
- La repetición de géneros continúa acumulándose y ahora cada semilla aporta según esa intensidad.
  Los baselines públicos permanecen no personalizados.
- `recency-v1` dejó la semivida diaria y pasó a años naturales: año del corte `1,0`, año anterior
  `0,35`, y cada año adicional vuelve a multiplicar por `0,35`.
- Los pesos oficiales de `recency-v1` quedaron en contenido `0,30`, rating-confidence `0,20`,
  PopScore `0,10` y recencia `0,40`. La rejilla conserva sus seis configuraciones de recencia,
  con una variante de `0,40` y otra de `0,45` para esta señal.
- El contrato reproducible pasó de protocolo v4 a v5. Se actualizaron el DTO TypeScript, la
  validación de versión, la documentación canónica y el vault de Obsidian.

## Verificación

- Backend: `182 passed` en las suites de recomendaciones y evaluación.
- TypeScript: `tsc --noEmit` correcto.
- Frontend: `6 files, 27 tests passed` excluyendo la suite de navegación que requiere Chromium.
- La suite completa de Vitest queda pendiente únicamente porque el contenedor no contiene el
  ejecutable Chromium de Playwright (`chromium_headless_shell`); no es un fallo del cambio.
- JSON de `docs/methodology/protocol.json` parseado correctamente y `git diff --check` sin errores.

## Fuente

- `apps/api/recommendations/_weights.py`
- `apps/api/recommendations/content/recency.py`
- `apps/api/recommendations/content/rank.py`
- `apps/api/recommendations/content/variants.py`
- `docs/methodology/protocol.json`
