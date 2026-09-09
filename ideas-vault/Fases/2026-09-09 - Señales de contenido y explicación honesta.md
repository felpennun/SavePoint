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

Franquicia y desarrolladora pasan a persistirse con su ID IGDB estable. La
franquicia se interpreta como saga y entra en `fs-v4` siempre que exista en
alguna obra; no se descarta por cobertura global. El desarrollador mantiene el
umbral del 50 %.
PopScore se prepara como instantánea de primitivas crudas por obra, tipo,
fecha, fuente y hash; todavía no tiene un peso activo en el recomendador.

La decisión del autor de 2026-09-09 trata `franchise` de IGDB como la señal de saga. Se
incluye aunque su cobertura sea baja; las obras sin franquicia omiten esa dimensión, sin
imputación ni exclusión global.

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

## Frontera de catálogo y candidatos — 2026-09-09

El autor separa dos vistas sin duplicar obras. El catálogo de una versión nueva
incluye únicamente juegos con fecha conocida ya publicada al corte fijado; los
futuros y sin fecha continúan almacenados, pero no se muestran. El universo de
salida de los algoritmos es el subconjunto
`total_rating_count >= 1 OR rating IS NOT NULL`, sin el umbral histórico de
1.000 valoraciones. La biblioteca del usuario puede conservar cualquier juego
del catálogo y usarlo como semilla.

`rating` y `rating_count` proceden de usuarios de IGDB; `total_rating` y
`total_rating_count` agregan usuarios y crítica externa. La reimportación
aditiva, el corpus `2026.09.2` y sus snapshots ya están completados; no se ha
calculado ningún ranking.

La auditoría confirmó que no hay títulos ni slugs vacíos. Las obras futuras,
sin fecha y los DLC permanecen almacenados, pero fuera de la vista gobernada.
Las ausencias parciales de señales opcionales son cobertura real de IGDB y no
se rellenan artificialmente. El PopScore compuesto se materializó en
`CorpusPopularityScore` para las obras con las cuatro primitivas observadas.

## Evidencia canónica

- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-PLAN|Plan 03-02]]
- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-02-SUMMARY|Resumen 03-02]]
- [[../../docs/verification/igdb-import-audit-2026-09-09|Auditoría de importación IGDB y señales]]
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
