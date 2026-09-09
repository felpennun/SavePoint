---
quick_id: 260909-qlu
status: complete
completed: 2026-09-09
---

# Resumen: rating observado, similitud fs-v7 y documentación de jornada

## Resultado

El rating IGDB observado ya no se diluye con el perfil medio del género:
`rating-confidence-v3` usa directamente `(rating / 100)^2` y el refuerzo
acotado por `total_rating_count`. El perfil por género queda como fallback para
obras sin rating observado.

La similitud se versionó como `fs-v7`/`facet-similarity-v3`. Género y plataforma
usan media armónica entre cobertura del perfil y precisión del candidato. Saga
y desarrollador pesan `0,18` y `0,12`, con bonus positivo solo por coincidencia
real y máximo combinado `0,30`.

La caché contiene 190.479 vectores y los diez workers de Felipe terminaron con
éxito y publicaron la revisión 14. Silksong obtiene bonus de desarrollador
`0,12`; Hades II obtiene `0,1143` por Supergiant Games; no hay bonus de saga
porque esas relaciones no están presentes en los datos IGDB importados.

## Verificación

- Recomendaciones y evaluación backend: `192 passed`.
- TypeScript web: `tsc --noEmit` correcto.
- Caché fs-v7: `190.479/190.479` vectores.
- Workers de Felipe: `10/10 succeeded`.
- Evaluación offline de los 400 usuarios: no ejecutada.

## Documentación

- `docs/verification/jornada-decisiones-recomendacion-2026-09-09.md`
- `docs/verification/recommendation-fs-v7-felipe-2026-09-09.md`
- `docs/verification/recommendation-architecture-2026-09-09.md`
- `docs/methodology/protocol.json`
- `ideas-vault/Fases/Fase 3 - Recomendadores explicables y baselines.md`
