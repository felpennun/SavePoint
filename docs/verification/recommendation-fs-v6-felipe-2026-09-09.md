---
fecha: 2026-09-09
estado: verificado
---

# Verificación de `fs-v6` con `felipe`

## Contrato

`fs-v6` calcula la similitud de contenido con género y plataforma como núcleo.
Sus pesos relativos son `0,50` y `0,25`, normalizados entre las facetas
disponibles. Saga/franquicia y desarrollador conservan `0,15` y `0,10` como
bonus de confirmación: solo se activan cuando el valor coincide con una
preferencia ponderada del usuario. La presencia aislada de una saga o un
desarrollador no aporta puntos.

La función vive en `apps/api/recommendations/content/similarity.py` y es
consumida por `rank_content_v1`; por tanto, endpoint web, workers y evaluación
offline comparten código y pesos.

## Materialización

- Corpus: `2026.09.2`.
- Obras gobernadas: `190.479`.
- Vectores `fs-v6`: `190.479`.
- Vectores creados en esta pasada: `121.021`.
- Vectores actualizados en esta pasada: `69.458`.
- Filas `fs-v5` y datos de catálogo: conservados.

## Cuenta `felipe`

- Revisión de colección: `14`.
- Secciones publicadas: `10`.
- Jobs de la configuración vigente: `10/10 succeeded`.
- Revisión del snapshot activo: `14`.
- Versión de features del snapshot: `fs-v6`.

## Pruebas

- `191` pruebas backend de recomendaciones y evaluación: PASS.
- `tsc --noEmit` de web: PASS.
- Preflight de entradas: PASS.
- La evaluación offline de los 400 usuarios no se ejecutó.

