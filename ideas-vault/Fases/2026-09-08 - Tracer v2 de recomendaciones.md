---
tags: [fase/3, tema/recomendadores, tema/evaluacion]
---

# Tracer v2 de recomendaciones

## Resultado

El plan 03-01 conecta el endpoint autenticado con el ranker de contenido real mediante
`recommendations.service.recommend_for_user`. El servicio valida `protocol_version: 2`, crea un
manifiesto hashado del universo explorable y del universo de salida, excluye obras vistas y
fechas futuras, y rechaza cualquier resultado que escape del manifiesto.

La pagina conserva el orden recibido en una lista `<ol>`. Las razones son evidencia determinista
de solapamiento de generos y se omiten cuando no hay senal suficiente; no se inventa copy para
rellenar una tarjeta.

## Evidencia canonica

- [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-01-PLAN|Plan 03-01]]
- `apps/api/recommendations/service.py`
- `apps/api/evaluation/tests/test_protocol_v2.py`
- `apps/api/recommendations/tests/test_service.py`

## Verificacion

La bateria backend del plan pasa con 49 pruebas. El chequeo TypeScript tambien pasa. Vitest pasa
28 pruebas; la suite de overflow requiere descargar el navegador Chromium de Playwright en el
entorno de ejecucion.

## Enlaces

- [[Conjunto de candidatos compartido]]
- [[Explicabilidad]]
- [[Fase 3 - Recomendadores explicables y baselines]]
- [[2026-09-09 - Señales de contenido y explicación honesta]]
