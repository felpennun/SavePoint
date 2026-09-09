---
quick_task: asynchronous-recommendation-cache
created: 2026-09-09
status: complete
---

# Caché personal asíncrona de recomendaciones

## Objetivo

Adoptar el flujo stale-while-revalidate para que la página de recomendaciones nunca espere al
cálculo de los algoritmos: conservar el último resultado, recalcular tras cambios de colección
y publicar un bundle completo únicamente cuando termine.

## Alcance

- Revisiones de colección y trabajos coalescidos persistidos en PostgreSQL.
- Worker independiente y comando `process_recommendation_jobs`.
- Snapshot por usuario con publicación atómica y descarte de resultados obsoletos.
- Endpoint autenticado y página que muestra el snapshot anterior mientras actualiza.
- Cinco estantes de contenido, heurística de género y DLC con explicaciones localizadas.
- Verificación de migraciones, configuración Compose y pruebas del flujo.

## Decisión de infraestructura

No instalar Redis todavía. PostgreSQL es suficiente como cola durable y fuente de verdad para el
snapshot; Redis se reconsiderará después de medir latencia y concurrencia en la demo.

## Restricción

Preparar el mecanismo sin ejecutar la evaluación experimental de los 400 usuarios sintéticos.
