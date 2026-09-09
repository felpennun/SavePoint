---
quick_task: bootstrap-existing-recommendation-snapshots
status: complete
completed: 2026-09-09
---

# Resumen

Se añadió `enqueue_recommendation_refreshes`, un comando idempotente que detecta usuarios con
colección existente, crea su revisión inicial y encola el trabajo para `recommendation-worker`.
No altera ni borra entradas, copias, valoraciones ni snapshots publicados.
