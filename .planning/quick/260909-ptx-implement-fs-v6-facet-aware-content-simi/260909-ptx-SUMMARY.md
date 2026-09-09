---
quick_id: 260909-ptx
status: complete
completed: 2026-09-09
---

# Resumen: similitud de contenido fs-v6

## Resultado

Se implementó `fs-v6` en el módulo compartido que utilizan el endpoint web,
los diez workers y el runner offline. Género y plataforma forman el núcleo de
similitud; saga/franquicia y desarrollador solo aportan un bonus acotado cuando
coinciden con valores presentes en el perfil ponderado del usuario. La mera
presencia de esos metadatos no concede puntos y su ausencia no se imputa ni
penaliza.

La caché contiene `190.479/190.479` vectores `fs-v6`; las filas anteriores no
se borraron. `felipe` tiene un snapshot publicado de la revisión 14 con las
diez secciones completadas y `feature_set_version = fs-v6`.

## Verificación

- 191 pruebas backend de recomendaciones y evaluación: PASS.
- TypeScript web (`tsc --noEmit`): PASS.
- Preflight del corpus y población sintética: PASS; no se ejecutó la
  evaluación offline de los 400 usuarios.
- Los diez jobs de `felipe`: `succeeded`.

## Artefactos

- `apps/api/feature-vector-cache-fs-v6-2026.09.2.json`
- `apps/api/recommender-input-preflight-fs-v6-2026.09.2.json`
- `docs/verification/recommendation-fs-v6-felipe-2026-09-09.md`

