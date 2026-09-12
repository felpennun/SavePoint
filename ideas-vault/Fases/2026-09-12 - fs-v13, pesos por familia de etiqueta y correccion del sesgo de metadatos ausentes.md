---
tags: [fase/03, fase/04, tema/recomendadores, decision, resultado]
---

# fs-v13 — pesos por familia de etiqueta curada y corrección del sesgo de metadatos ausentes

Decisión de diseño y cambio de fórmula ratificados el 2026-09-12 (protocolo v16),
que sustituyen `fs-v12-curated-tags-idf` (protocolo v15) tanto en web como en la
evaluación offline. Motivado por dos hallazgos reales encontrados en sesión
revisando el reparto de peso del contenido, no por una idea de diseño previa.

## Hallazgo 1 — un subgénero raro pesaba más que el género

Bajo fs-v12, género/subgénero/tema/modo/característica compartían un único
presupuesto de 0,75 ("tag"), repartido por IDF suavizado dentro de ese bloque.
Con datos reales del corpus (`souls-like` IDF≈7,54 frente a `rpg`≈2,88 y
`action`≈1,97), una obra con `genre:rpg + genre:action + subgenre:souls-like +
mode:singleplayer` acababa con `souls-like` pesando **0,674 sobre 1,21** de
magnitud total — más que los dos géneros juntos (0,433) — solo por ser
estadísticamente raro en el corpus, no por ser más relevante para el gusto del
usuario. Esto invertía la jerarquía semántica ya declarada del proyecto
("género como núcleo").

## Hallazgo 2 — una obra sin tema salía mejor parada que una con tema

La primera corrección propuesta (repartir el presupuesto en 5 familias
renormalizadas entre sí) introducía un sesgo distinto, señalado por el autor:
si una familia (p. ej. tema) falta en una comparación, el mecanismo de
renormalización dinámica (`core = Σ peso·afinidad / Σ peso`, solo sobre
familias presentes en ambos lados) le da a las familias restantes una cuota
*relativa* mayor. Dos obras con la misma afinidad de género exacta podían
puntuar distinto según si la otra además tenía un tema flojo o ningún tema en
absoluto — premiando la escasez de metadatos, lo contrario de lo que debería
pasar. Esto contradecía el principio ya vigente en el proyecto para
franchise/developer: *"ausente es neutro, nunca resta ni redistribuye"*.

## Diseño final (protocolo v16)

- **Género + subgénero fusionados en una sola familia `tag`** (presupuesto
  0,60): un subgénero no compite con el género, lo refina (Souls-like acota
  RPG), así que comparten presupuesto e IDF con naturalidad.
- **`tag` y `platform`** (0,05, bajado de 0,25) son las únicas familias
  **núcleo**, renormalizadas entre sí — ambas con cobertura casi universal, así
  que el caso de renormalización (una de las dos ausente) es raro de verdad,
  no el camino común, y no reproduce el sesgo del Hallazgo 2.
- **`theme`** (0,20), **`mode`** (0,05) y **`feature`** (0,10) pasan a ser
  familias **opcionales/bono**, con el mismo tratamiento que ya tenían
  franchise/developer: una coincidencia solo suma, una ausencia en cualquiera
  de los dos lados no resta ni redistribuye — corrige el Hallazgo 2 sin volver
  a introducir el Hallazgo 1.
- **IDF propio por familia**, incluida `platform` (que antes no tenía IDF en
  absoluto, solo `1/√k`): el universo de referencia `N` de cada familia es
  "obras gobernadas con al menos un valor de esa familia", no el corpus
  gobernado completo — de lo contrario `feature` (~13 % de cobertura) saldría
  con un IDF inflado frente a `tag` (cobertura casi total) simplemente por
  tener un denominador `N` mal dimensionado para su propia población.
- Reparto final: `tag 0,60 / theme 0,20 / feature 0,10 / mode 0,05 / platform
  0,05` (núcleo `tag`+`platform`) + `franchise 0,02 / developer 0,015`
  (bonos, sin cambios).

## Verificado con datos reales antes de cerrar

Ejemplo real del corpus (`10-years-after`, 6 tags de género/subgénero + 2
temas + 1 modo + 1 plataforma): el bloque `tag:*` normaliza exactamente a 0,6
de magnitud, `theme:*` a 0,2, `mode:*`/`platform:*` a 0,05 cada uno al ser el
único valor de su familia — confirma que la implementación reproduce
exactamente la fórmula diseñada, no solo en el papel.

## Alcance del cambio

- `recommendations/content/features.py` — pesos, agrupación por `kind`, IDF
  por familia (`tag_idf_profile`/`theme_idf_profile`/`mode_idf_profile`/
  `feature_idf_profile`/`platform_idf_profile`/`all_family_idf_profiles`),
  `feature_vector()` reescrito.
- `recommendations/content/similarity.py` — `_OPTIONAL_FACETS` gana
  theme/mode/feature; `_CORE_FACETS` se queda en (tag, platform) con los
  nuevos pesos; `SIMILARITY_RULE_VERSION` → `facet-similarity-v8`.
- Todo el hilo de reparto de `tag_idf` (`rank.py`, `profile.py`, `hybrid.py`,
  `signal_cache.py`, `evaluation/runner.py`, `evaluation/splits.py`,
  `rebuild_feature_vectors`) pasa a repartir un `family_idf` (bundle de los 5
  perfiles) en vez de un único diccionario plano — usado tanto por los 16
  algoritmos web como por el runner de evaluación offline, sin caminos
  separados.
- `FEATURE_SET_VERSION` → `fs-v13-family-weighted-tags`; `WorkFeatureVector`
  rematerializado para las 190.479 obras gobernadas.
- `docs/methodology/protocol.json` → `protocol_version: 16`, con narrativa
  completa de ambos hallazgos y la corrección; `recommendations/service.py`
  y los guardas `require_version()` de `evaluation/candidates.py` alineados.
- 518/518 tests del backend en verde (incluye las fixtures de ~9 archivos de
  test que aún construían perfiles con el modelo `Genre` heredado en vez de
  `CuratedLabel`, corregidas en la misma sesión al investigar el bug de
  etiquetas duplicadas en la interfaz que motivó todo este hilo).

## Pendiente, explícitamente no hecho en esta sesión

- **No se ha vuelto a ejecutar la evaluación offline de 400 usuarios** bajo
  protocolo v16 — el cambio de fórmula invalida la comparabilidad directa con
  v15 (mismo split, pero puntuaciones de contenido distintas); un nuevo
  cálculo final es una decisión explícita pendiente del autor, no implícita
  en "aplícalo para que lo usen los algoritmos".
- **La interfaz aún no muestra tema/modo/característica por separado** en la
  ficha de cada juego (quedó pedido en la misma conversación, antes de decidir
  los pesos); la etiqueta `"tags"` de `catalogue/serializers.py::_tags()`
  sigue devolviendo las cinco familias mezcladas para la ficha pública.
- El informe de cobertura (`coverage_report()`) no desglosa todavía
  theme/mode/feature por separado (solo tags/platforms/franchises/developers);
  es diagnóstico, no bloquea el cálculo, pero es una mejora pendiente.

## Fuentes canónicas

- [`docs/methodology/protocol.json`](../../docs/methodology/protocol.json) —
  `protocol_version: 16`.
- [`apps/api/recommendations/content/features.py`](../../apps/api/recommendations/content/features.py) —
  módulo con el docstring completo de la fórmula y su justificación.
- [[2026-09-12 - Evidencia UI-E2E de recomendaciones para el cierre de Fase 3 (QUAL-02)]] —
  el hallazgo de etiquetas duplicadas que arrancó esta investigación.
