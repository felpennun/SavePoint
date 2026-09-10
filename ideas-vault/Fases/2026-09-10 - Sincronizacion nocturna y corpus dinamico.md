# Sincronización nocturna y corpus dinámico

Estado: propuesta futura, no implementada.

## Objetivo

Actualizar cada noche el catálogo gobernado con juegos nuevos y cambios de IGDB
sin publicar una versión incompleta ni destruir los artefactos reproducibles.

## Diseño recomendado

1. Registrar un cursor o `watermark` de sincronización y consultar una ventana de
   seguridad para detectar actualizaciones atrasadas.
2. Crear una nueva `corpus_version` y hacer upsert idempotente por lotes.
3. Detectar juegos nuevos o modificados y recalcular sus datos derivados.
4. Recalcular los artefactos globales afectados, especialmente IDF y las
   normalizaciones de popularidad.
5. Validar cobertura, recuentos, checksums y consistencia antes de publicar.
6. Cambiar atómicamente la versión activa y encolar después los snapshots de
   recomendaciones.

La versión anterior debe permanecer disponible hasta que la nueva supere todas
las validaciones. Un fallo conserva la última versión buena y permite reintentar.

## Optimización

- Mantener snapshots y procedencia por versión del corpus.
- Invalidar vectores mediante dependencias etiqueta → juego cuando sea posible.
- Actualizar novedades solo para juegos nuevos o con cambios de fecha.
- Actualizar ratings y PopScore únicamente para juegos modificados.
- Limitar la concurrencia de workers; la ejecución simultánea de los 15 workers
  puede saturar PostgreSQL.
- Conservar al menos la última versión válida para rollback.

La incidencia actual de PostgreSQL confirmó además que los vectores de
características deben materializarse una vez por versión del corpus y
reutilizarse entre usuarios. Los workers no deben volver a precargar las
relaciones completas del catálogo para cada usuario; solo se consultan juegos
sin vector materializado. Las estadísticas inmutables de una versión se
pueden mantener en caché dentro de cada worker y deben invalidarse al cambiar
la versión del corpus.

## Estimación

- Prototipo: 2–4 días.
- Implementación robusta con idempotencia, reintentos, publicación atómica,
  observabilidad y tests: 5–10 días.
- Optimización incremental para un volumen grande de usuarios: 1–2 semanas
  adicionales.

## Fuente canónica

La propuesta se describe en la conversación del 2026-09-10 y deberá convertirse
en un ADR antes de implementarse.
