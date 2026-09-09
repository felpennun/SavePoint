---
quick_task: asynchronous-recommendation-cache
status: complete
completed: 2026-09-09
---

# Resumen

Se preparó el cálculo personal asíncrono de recomendaciones.

- `RecommendationState` registra la revisión de colección y el snapshot activo.
- `RecommendationRefreshJob` implementa una cola PostgreSQL coalescida por usuario y revisión.
- El worker publica las cinco variantes de contenido y género como un bundle atómico; los
  cálculos que quedan obsoletos no se publican.
- `GET /api/recommendations/snapshot/` devuelve `empty`, `building`, `stale` o `ready` sin
  bloquearse.
- La interfaz conserva el snapshot anterior y refresca el servidor mientras existe un trabajo
  pendiente; el primer cálculo muestra estado de preparación.
- El Compose local incorpora el worker sin añadir Redis.
- Se añadieron pruebas del endpoint, invalidación, publicación y preservación del snapshot; la
  suite dirigida de recomendaciones terminó con 46 pruebas superadas.
- No se ejecutaron algoritmos sobre la población sintética ni la evaluación experimental.
