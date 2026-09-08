---
tags: [fase/3, tema/recomendadores, tema/explicabilidad, estado/completado]
---

# Señales de contenido y explicación honesta

## Resultado

El plan 03-02 introduce `fs-v2` y separa la señal personal positiva de la negativa.
Solo `completed` y `playing` con al menos 3,5/5 construyen afinidad positiva. Tres
ratings bajos del mismo género habilitan únicamente `content-cbf-neg-v1`, una variante
identificable y reversible.

El ranking expone parámetros, umbrales y disponibilidad de señales. Rating externo y
volumen de valoraciones proceden de la instantánea gobernada; una ausencia sigue siendo
`null`. PopScore, franquicia y desarrollador no se inventan: el corpus todavía no los
persiste y permanecen marcados como no disponibles hasta un import con snapshot y
procedencia.

Las razones son tokens deterministas de género o plataforma presentes en el resultado.
La API los convierte a nombres canónicos y la interfaz reutiliza la plantilla localizada
aprobada; cuando no hay evidencia devuelve una razón ausente.

## Reapertura de contrato — 2026-09-09

El autor añade que la valoración propia de cada juego semilla debe figurar
explícitamente como intensidad de preferencia. `ProfileInputs` registra el
número de semillas positivas, la suma y la media de sus `rating_half_steps`;
no confunde esa señal personal con el rating externo del candidato.

Franquicia y desarrolladora pasan a persistirse con su ID IGDB estable. Solo
entran en `fs-v3` si su cobertura medida en el corpus gobernado llega al 50 %.
PopScore se prepara como instantánea de primitivas crudas por obra, tipo,
fecha, fuente y hash; todavía no tiene un peso activo en el recomendador.

La composición acordada usa exclusivamente `Visits`, `Want to Play`,
`Playing` y `Played` de IGDB. Cada tipo se normaliza con `log1p` y percentil de
rango medio en su snapshot; `igdb-engagement-mean-v1` es la media simple de
las cuatro y se declara ausente si falta una. El valor ya es trazable en el
DTO, pero todavía no cambia la puntuación de ningún recomendador.

La recencia se calcula por separado en `recency-v1`: `exp(-ln(2) * edad_días /
365)`, solo en obras ya lanzadas y con rating externo observado. Es un
algoritmo independiente; no cambia el orden de las variantes de contenido ni
el de PopScore.

No se ha consultado IGDB, ni se ha reimportado o gobernado un corpus nuevo, ni
se han ejecutado experimentos. La decisión siguiente es revisar esta base y,
solo después, publicar un nuevo corpus y capturar sus instantáneas.

## Evidencia canónica

- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-PLAN|Plan 03-02]]
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-SUMMARY|Resumen 03-02]]
- `apps/api/recommendations/content/profile.py`
- `apps/api/recommendations/content/rank.py`
- `apps/api/recommendations/tests/test_content_v2.py`

## Verificación

- 43 pruebas específicas de recomendaciones y evaluación pasan.
- TypeScript del frontend pasa.
- La suite backend completa pasa: 409 pruebas en 74,82 s.

## Enlaces

- [[2026-09-08 - Tracer v2 de recomendaciones]]
- [[Explicabilidad]]
- [[Fase 3 - Recomendadores explicables y baselines]]
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-CONTEXT|Contexto de fase 03]]
