# Checkpoint de preparación: evaluación offline sobre usuarios sintéticos

**Fecha del checkpoint:** 2026-09-10  
**Estado:** gate técnico superado; congelación científica del estado fuente **completada** (commit `b1ec0f7`, más los commits de reproducibilidad `b956256`/`3fba4bb`/`64efe32` descritos en el resultado final).  
**Cálculo final iniciado:** sí — completado con éxito el 2026-09-11. Resultado, tablas y análisis
estadístico en [`evaluation-results-400-test-2026-09-10.md`](./evaluation-results-400-test-2026-09-10.md).

> **Corrección posterior (2026-09-11).** Este checkpoint se calculó en `HEAD 8766b9d`,
> **antes** de la congelación real (`b1ec0f7`), y sus conteos de usuarios evaluables
> (`232/79/79`, tabla de cohortes y párrafo siguientes) se hicieron bajo una regla de
> elegibilidad de candidatas más laxa (`total_rating_count >= 1`, vigente hasta las
> 2026-09-09 14:19) que la que aplica el protocolo congelado
> (`rating IS NOT NULL AND total_rating_count >= 5`, vigente desde `b4f024b`). Bajo la
> regla realmente vigente, los conteos autoritativos —reproducidos en la ejecución
> final— son **train 227 / validation 78 / test 73** (skip 13/2/7 en vez de 8/1/1). Los
> 12 usuarios adicionales que ahora se omiten tienen biblioteca no vacía pero su único
> positivo elegible tiene `total_rating_count` entre 1 y 4, por debajo del umbral `>=5`;
> no es una regresión de datos, es la aplicación correcta de la regla de elegibilidad ya
> vigente cuando se congeló el protocolo. El detalle completo está en
> [`evaluation-results-400-test-2026-09-10.md`](./evaluation-results-400-test-2026-09-10.md) §3.
> Los números de esta sección se dejan como estaban por trazabilidad del proceso; no se
> deben citar como el conteo final.

## Decisión de alcance

La evaluación utilizará la población sintética de Fase 3 completa como grupo
estudiado: 400 cuentas generadas de forma determinista. La unidad de análisis
será el usuario, no la recomendación individual ni el algoritmo aislado. El
resultado principal se informará como distribución y media por usuario, con
comparaciones pareadas sobre exactamente los mismos usuarios y candidatos.

La población contiene cuatro cohortes fijadas en el protocolo:

| Cohorte | Usuarios | Tratamiento |
|---|---:|---|
| Sin historial | 10 | Se conserva como cohorte descriptiva de cold start; no tiene un positivo que retener mediante leave-one-out. |
| Historial escaso | 100 | Evaluación normal si contiene un positivo elegible. |
| Historial intensivo | 50 | Evaluación normal si contiene un positivo elegible. |
| Historial normal | 240 | Evaluación normal si contiene un positivo elegible. |

En la comprobación viva, 390 de los 400 usuarios tienen al menos un positivo
elegible: 232 en train, 79 en validation y 79 en test. Por tanto, el test tiene
80 cuentas asignadas, pero producirá 79 observaciones evaluables. Esta exclusión
no es un fallo ni un cero artificial: el runner la registra como
`skipped_reason = no eligible positive item for leave-one-out`.

## Evidencia del gate técnico

| Elemento congelado o comprobado | Valor |
|---|---|
| Corpus activo | `2026.09.2` |
| Obras gobernadas | `190479` |
| Universo candidato elegible | `13621` |
| Versión del protocolo | `12` |
| SHA-256 del protocolo | `02af71222ffcc964ac940e7ebbe3c51c87fc70cf869f55248e4dce836f894a61` |
| Feature set | `fs-v12-curated-tags-idf` |
| Hash snapshot de ratings | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| Hash snapshot de PopScore | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| Hash manifiesto de población | `be3e43c451724c9c3add784394955397292d20438dc18f17c60b1984e1f4dd38` |
| Semilla de población | `20260909` |
| Semilla de partición | `20260908` |
| Partición | `240 train / 80 validation / 80 test` |
| Solapamiento con población histórica | `0` |
| Marcador de test consumido | `false` (`apps/api/.evaluation-test-run.json` no existe) |
| Preflight de entradas | `passed`; algoritmos no ejecutados |
| Tests específicos de evaluación | `95 passed` |

La auditoría de entradas también comprobó que no hay fechas inválidas en el
corpus o las candidatas, que las candidatas cumplen la regla de rating, que la
cobertura de tags y plataformas es completa, y que la rejilla congelada contiene
31 configuraciones. Los valores de cobertura y las decisiones de señales están
en [`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md).
El resumen machine-readable de esta comprobación está en
[`evaluation-preflight-2026-09-10.json`](./evaluation-preflight-2026-09-10.json).

## Protocolo que debe respetarse

- Relevancia: `completed` o `rating_half_steps >= 7`.
- Split por usuario: leave-one-out determinista; el positivo retenido vuelve al
  conjunto de candidatos y se excluye el resto de la biblioteca.
- `K`: 5, 10 y 20; métrica headline: `nDCG@10`.
- Algoritmos offline: 16 IDs declarados en `protocol.json`, desde
  `random-v1` y `popularity-v1` hasta contenido, MMR, `cf-user-knn-v1` y los dos
  híbridos.
- Métricas de acierto: precision, recall, nDCG y MAP.
- Métricas complementarias: cobertura de catálogo, cobertura de predicción,
  concentración HHI, diversidad intra-lista y novedad.
- Comparación estadística: observaciones pareadas por usuario; bootstrap de la
  diferencia media, Wilcoxon pareado, corrección de Holm y Friedman cuando sea
  estimable. No se debe presentar un `p` aislado como prueba de superioridad
  universal.
- Los 240 usuarios de train son la referencia colaborativa y la base de
  frecuencia para novedad; validation se reserva para selección; test se usa
  una sola vez para la comparación final.

El protocolo declara explícitamente que esto es evidencia de simulación sobre
arquetipos parametrizados, no evidencia de satisfacción de usuarios reales.
Las conclusiones deberán limitarse al corpus `2026.09.2`, a estas cohortes y a
este protocolo.

## Condición pendiente antes de ejecutar

El gate de datos y código pasa, pero el árbol de trabajo contiene cambios sin
commit en `docs/methodology/protocol.json`, `apps/api/evaluation/**` y
`apps/api/recommendations/**`, además de cambios de interfaz pertenecientes a
otra LLM. El `HEAD` observado es `8766b9da16a7e3bfdc7d462761f8fabe1af51800`,
pero ese SHA no identifica por sí solo los cambios sin commit.

Antes del test final, el responsable debe congelar el estado fuente sin tocar
`apps/web`: integrar o confirmar los cambios relevantes, guardar el SHA de
commit resultante y comprobar que el protocolo no cambia después de iniciar la
ejecución. Si no se puede hacer ese freeze, la otra LLM debe detenerse y
reportarlo como bloqueo de reproducibilidad; no debe forzar un protocolo nuevo
ni retocar algoritmos a la vista de los resultados.

## Comando previsto para el cálculo final

Después de superar la condición anterior, el prompt operativo asociado indica
ejecutar:

```powershell
docker compose -f infra/compose.yaml exec -T api python manage.py run_evaluation_parallel --corpus-version 2026.09.2 --split test --max-workers 4 --evidence-json /workspace/apps/api/evaluation-400-test-2026-09-10.artifact.json
```

Se fija `--max-workers 4` para reducir la presión sobre PostgreSQL observada en
la recomputación paralela web. El número de workers es una condición de
ejecución y debe quedar registrado en `parallel_execution`; no modifica las
fórmulas ni la comparación. No debe ejecutarse `--force-new-protocol`, no debe
regenerarse la población y no debe ejecutarse el test dos veces.

## Artefactos obligatorios al terminar

El cálculo no se considerará terminado hasta conservar el JSON completo, su
SHA-256, el SHA del código, el hash del protocolo, los dos hashes de snapshots,
el hash del manifiesto de split, las 16 secciones, los tiempos de cada worker,
el tiempo de pared, el estado de cada worker y las comparaciones estadísticas.
La LLM que lo ejecute debe redactar además una nota de resultados con:

1. tabla por algoritmo y por `K`;
2. intervalos y pruebas pareadas de `nDCG@10`;
3. desglose por las cuatro cohortes, señalando el `n` evaluable de cada una;
4. métricas de diversidad, novedad, cobertura y concentración;
5. fallos, usuarios omitidos y limitaciones;
6. interpretación prudente con la bibliografía ya documentada, sin convertir
   resultados sintéticos en afirmaciones sobre usuarios reales.

Fuente normativa: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md) y
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md).
