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
