---
fecha: 2026-09-09
estado: verificado
---

# Integración del runner de evaluación

Se integraron los cambios pendientes de la evaluación de la Fase 3 sobre el corpus
`2026.09.2`. Esta integración prepara el harness; no ejecuta algoritmos, tuning ni una
evaluación experimental.

## Cambios integrados

- `apps/api/evaluation/metrics.py` añade cobertura de catálogo, cobertura de predicción,
  concentración HHI, diversidad intra-lista y novedad.
- `apps/api/evaluation/runner.py` comprueba el hash del snapshot de PopScore, incluye
  `total_rating_count` en la huella, verifica la población activa y calcula la novedad con
  probabilidades derivadas únicamente de las interacciones de entrenamiento.
- El artefacto del runner conserva valores por usuario, agregados, denominadores, cobertura de
  señales y versión del conjunto de features.
- Se incorporan las evidencias `corpus-governance-2026.09.2.json`,
  `corpus-popularity-2026.09.2.json`, `corpus-ratings-2026.09.2.json` y
  `popscore-materialization-2026.09.2.json`.

## Verificación

La suite dirigida de evaluación y recomendación pasó con **120 tests**:

```text
120 passed in 8.47s
```

También se corrigió un fixture cuyo comentario afirmaba que un rating IGDB fuera de rango era
inválido. El contrato congelado de candidatos usa `total_rating_count >= 1 OR rating IS NOT
NULL`; por tanto, un rating no nulo satisface la segunda alternativa y el test ahora refleja la
regla de producción.

## Qué es la caché `fs-v4`

`fs-v4` es la versión del conjunto de features de contenido, no una versión del algoritmo ni un
resultado de recomendaciones. Para cada obra, el sistema puede guardar un vector disperso en
`WorkFeatureVector`, identificado por la obra y por `feature_set_version`. Sus dimensiones son
facetas como `genre:<slug>`, `platform:<slug>`, `franchise:<slug>` y
`developer:<slug>`.

La etiqueta `fs-v4` nació al activar `franchise` de IGDB como señal de saga. Las filas `fs-v3`
se construyeron con esa faceta excluida por su cobertura global baja, así que no se pueden
reutilizar silenciosamente: les falta una dimensión que ahora forma parte del vector. La versión
actúa como namespace y evita mezclar vectores calculados con reglas distintas.

Cuando una obra no tiene saga, la dimensión se omite de su vector disperso; no se inventa ni se
imputa un valor. El desarrollador mantiene su umbral de cobertura del 50 %. El runner puede
calcular vectores bajo demanda y el comando de reconstrucción puede completar la caché antes de
una ejecución experimental futura.

La reconstrucción de la caché `fs-v4` se completó el 2026-09-09 sobre las 190.479 obras
gobernadas: se crearon 186.211 filas, se actualizaron 4.268 y no queda ninguna obra sin vector
`fs-v4`. La operación no borra datos de catálogo ni de ratings; `update_or_create` mantiene la
fila correspondiente a cada pareja obra-versión.

La evidencia completa está en
[`feature-vector-cache-2026.09.2.json`](../../apps/api/feature-vector-cache-2026.09.2.json).

Fuentes canónicas: [`recommendation-input-audit-2026-09-09.md`](recommendation-input-audit-2026-09-09.md),
[`protocol.json`](../methodology/protocol.json) y el código de
[`features.py`](../../apps/api/recommendations/content/features.py).
