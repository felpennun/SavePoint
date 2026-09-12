# Checkpoint de cierre: evaluación offline protocolo v15 sobre usuarios sintéticos

**Fecha del checkpoint:** 2026-09-12
**Estado:** gate técnico superado y **cálculo final ya completado con éxito** en el momento
de escribir este documento — a diferencia del checkpoint de protocolo v12
([`evaluation-checkpoint-400-users-2026-09-10.md`](./evaluation-checkpoint-400-users-2026-09-10.md)),
que se redactó *antes* de lanzar el cálculo, este se redacta como registro de cierre del
gate que efectivamente se usó, para dejar trazabilidad exacta de qué estado congelado
produjo el resultado ya publicado.
**Cálculo final:** completado el 2026-09-12 02:02:17 UTC, al tercer intento (los dos
primeros se detuvieron a propósito, sin coste, al encontrar dos fallos de diseño reales
antes de escribir el marcador de consumo — ver más abajo). Resultado, tablas y análisis
estadístico completos en
[`evaluation-results-400-test-2026-09-12-v15.md`](./evaluation-results-400-test-2026-09-12-v15.md).

> **Nota de alcance.** Este documento no es una condición pendiente de cumplir (el cálculo
> ya se hizo); es el registro del gate técnico congelado que se usó, en el mismo formato que
> el checkpoint de protocolo v12, para que quede una foto exacta y citable del estado fuente
> por cada protocolo congelado, junto al resultado. Los dos intentos fallidos previos al
> éxito **no** tocaron el marcador de consumo del split `test`; el detalle de qué falló y
> cómo se corrigió está en §1.2 del documento de resultados y en el vault
> ([[2026-09-12 - LOO por fraccion sobre el tag dominante, fundamento y alternativas descartadas]]).

## Decisión de alcance

La evaluación reutiliza la misma población sintética base de Fase 3 (400 cuentas), ahora
regenerada bajo la semilla `20260912` para que cada usuario sortee su propio conjunto de
tags preferidos (en vez de un conjunto compartido por arquetipo, como en v12-v14). La unidad
de análisis sigue siendo el usuario, no la recomendación individual ni el algoritmo aislado.

La población conserva las cuatro cohortes fijadas en el protocolo:

| Cohorte | Usuarios | Tratamiento bajo v15 |
|---|---:|---|
| Sin historial | 10 | Cohorte descriptiva de cold start; sin ningún positivo elegible, queda fuera de ambos mecanismos de retención. |
| Historial escaso | 100 | `leave_fraction_out_dominant_tag_per_user` si tiene señal de tag de contenido con pool suficiente; si no, cae a `leave_one_out` simple. |
| Historial intensivo | 50 | Igual que arriba. |
| Historial normal | 240 | Igual que arriba. |

En la comprobación viva del split `test` (80 cuentas asignadas), **79 usuarios fueron
evaluables** — exactamente el mismo número que en v14, porque el respaldo a
`leave_one_out` (§1.1) recupera precisamente a los usuarios para los que el mecanismo por
fracción no se podía construir, y solo deja fuera a quien no tiene ningún positivo elegible
en absoluto (`skipped_reason: "no eligible positive item for leave-one-out"`,
`skipped_user_count: 1`). A diferencia de v12-v14, donde cada usuario evaluable retenía
exactamente 1 ítem, en v15 el número de ítems retenidos por usuario varía (media 2,56, rango
1-5) según el tamaño del pool de su tag dominante y el resultado del retroceso adaptativo.

## Evidencia del gate técnico

| Elemento congelado o comprobado | Valor |
|---|---|
| Corpus activo | `2026.09.2` |
| Obras gobernadas | `190479` |
| Universo candidato elegible | `13618` |
| Versión del protocolo | `15` |
| SHA-256 del protocolo | `d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a` |
| Feature set | `fs-v12-curated-tags-idf` |
| Hash snapshot de ratings | `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc` |
| Hash snapshot de PopScore | `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097` |
| Hash manifiesto de población | `28c95dd621d26132e6939f85ff37a37b254f0121f52bf617595f9345bef1267a` |
| Semilla de población sintética | `20260912` |
| Semilla de partición de usuarios | `20260908` |
| Semilla leave-fraction-out / leave-one-out | `20260907` (heredada; el sufijo `:dominant-tag` en el RNG evita colisión con otros usos de la misma semilla) |
| Partición | `240 train / 80 validation / 80 test` |
| Solapamiento con población histórica | `0` |
| Hash manifiesto del split (`test`) | `c85d4ee270de8e590c9052d01dab30d7cf5314951622cc0b3801fdf027cbfd3d` |
| Marcador de test consumido | `true` — `apps/api/.evaluation-test-run.json`, `consumed_at: 2026-09-12T02:02:20.014454+00:00` |
| Preflight de entradas | `passed`; `apps/api/evaluation-input-preflight-2026-09-12-v15-gate.json`; algoritmos no ejecutados en el preflight |
| Artefacto final | `apps/api/evaluation-400-test-2026-09-12-v15.artifact.json` |
| SHA-256 del artefacto final | `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab` |
| Usuarios evaluables / asignados | `79 / 80` (skip 1, cero positivos elegibles) |
| Ejecución paralela | `--max-workers 2 --serial-tail 5` (16 workers totales); pared `4297,87 s`; suma de duración por worker `6266,85 s` |

La auditoría de entradas comprobó, igual que en v12-v14, que no hay fechas inválidas en el
corpus ni en las candidatas, que las candidatas cumplen la regla de rating, y que la
rejilla congelada contiene 31 configuraciones. Los valores de cobertura de señales y las
decisiones de facetas están en
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md).

## Protocolo que debe respetarse

- Relevancia: `completed` o `rating_half_steps >= 7` (sin cambios desde v6).
- Piso de calidad del retenido: `heldout_min_external_rating >= 70` (heredado de v14) sobre
  cualquier obra candidata a ser retenida, en ambos mecanismos.
- Split por usuario: **leave-fraction-out adaptativo sobre el tag dominante**
  (`leave_fraction_out_dominant_tag_per_user`) — se retira `ceil(0,3 × tamaño_del_pool)`
  del pool elegible del tag de contenido más pesado del perfil (nunca menos de 1), con
  retroceso de a uno si la retirada desplaza el tag de la primera posición en el perfil
  recalculado, salvo que el retroceso ya haya llegado a `n=1` (el mínimo de 1 manda sobre la
  condición de dominancia). **Respaldo**: si este mecanismo no se puede construir para un
  usuario (sin señal de tag de contenido, o su tag dominante sin candidatas que superen el
  piso de rating), se usa `leave_one_out` simple de un único ítem — solo un usuario sin
  ningún positivo elegible en absoluto queda excluido del estudio.
- `K`: 5, 10 y 20; métrica headline: `nDCG@10`.
- Algoritmos offline: los mismos 16 IDs declarados en `protocol.json`, sin cambios desde
  v12 — de `random-v1` y `popularity-v1` a contenido, MMR, `cf-user-knn-v1` y los dos
  híbridos.
- Métricas de acierto: precision, recall, nDCG y MAP — `evaluation/metrics.py` ya estaba
  escrito para el caso general multi-relevante, así que el paso a conjuntos retenidos de
  tamaño variable no exigió ningún cambio en el cálculo de estas métricas.
- Métricas complementarias: cobertura de catálogo, cobertura de predicción, concentración
  HHI, diversidad intra-lista y novedad.
- Comparación estadística: observaciones pareadas por usuario; bootstrap BCa de la
  diferencia media (2000 remuestreos), Wilcoxon pareado (`zero_method="wilcox"`), corrección
  de Holm y Friedman ómnibus cuando sea estimable. No se presenta un `p` aislado como prueba
  de superioridad universal.
- Los 240 usuarios de train siguen siendo la referencia colaborativa y la base de
  frecuencia para novedad; validation se reserva para selección; test se usa una sola vez
  para la comparación final — y ya se usó, según este mismo checkpoint.

El protocolo declara explícitamente que esto sigue siendo evidencia de simulación sobre
arquetipos parametrizados, no evidencia de satisfacción de usuarios reales. Las conclusiones
se limitan al corpus `2026.09.2`, a estas cohortes y a este protocolo. El siguiente estudio
planeado (20 usuarios reales, evaluación de calidad por encuestas) es un capítulo
complementario y explícitamente no comparativo con este resultado — ver
[[2026-09-11 - Siguiente estudio, 20 usuarios reales y evaluacion de calidad]].

## Condición que se cumplió antes de ejecutar

A diferencia del checkpoint de protocolo v12 (que documentó una condición *pendiente* de
congelar el árbol de trabajo), en este ciclo el estado fuente se congeló y confirmó antes de
lanzar el cálculo que sí tuvo éxito: los dos fallos de diseño encontrados durante los
intentos previos (comparación de tag dominante contra facetas independientes; exclusión en
vez de respaldo a `leave_one_out`) se corrigieron y commitearon (`ed25fe8`, `81df38b`) **antes** de que la tercera corrida
escribiera el marcador de consumo. Ninguna
corrida fallida modificó el protocolo congelado ni el marcador; ambas se detuvieron con
`kill -9` sobre el proceso exacto dentro del contenedor tras confirmarse por `/proc` que
seguía vivo, y se verificó en ambos casos que `.evaluation-test-run.json` seguía intacto
(la marca previa de protocolo v14) antes de relanzar.

## Comando que produjo el cálculo final

```powershell
docker compose -f infra/compose.yaml exec -T api python manage.py run_evaluation_parallel --corpus-version 2026.09.2 --split test --max-workers 2 --serial-tail 5 --evidence-json /workspace/apps/api/evaluation-400-test-2026-09-12-v15.artifact.json
```

Se usó `--max-workers 2 --serial-tail 5` en vez de `--max-workers 4` (usado en protocolo
v12) porque un intento anterior con más concurrencia agotó la RAM disponible: el reparto de
contexto precomputado entre procesos hijos por `fork()` no evita que CPython reescriba el
contador de referencias de casi cada objeto al leerlo, lo que ensucia página por página la
memoria "compartida" y hace que cada worker acabe reteniendo su propia copia completa
(~1,7-1,9 GB observados por worker). Esta combinación de flags es ahora la regla operativa
por defecto para lanzamientos sin supervisión de `run_evaluation_parallel` en esta máquina.
No se ejecutó `--force-new-protocol`, no se regeneró la población después de fijar el
manifiesto, y el split `test` se ejecutó una sola vez.

## Artefactos conservados al terminar

El cálculo se considera terminado porque se conservan, todos comprometidos en `main`:

1. el JSON completo del artefacto y su SHA-256
   (`apps/api/evaluation-400-test-2026-09-12-v15.artifact.json`,
   `5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab`);
2. el hash del protocolo, los dos hashes de snapshots (ratings, PopScore), el hash del
   manifiesto de población y el hash del manifiesto de split, todos en la tabla de §"Evidencia
   del gate técnico" de este documento y repetidos en cada una de las 16 secciones del
   artefacto;
3. las 16 secciones de algoritmo, sus tiempos individuales, el tiempo de pared y la suma de
   duración por worker;
4. las comparaciones estadísticas por pares (Friedman, Wilcoxon+Holm, bootstrap BCa) para
   `nDCG@10` y el resto de métricas de acierto;
5. la nota de resultados completa con: tabla por algoritmo y por `K`; tabla de aciertos en
   bruto por `K` a nivel de ítem y de usuario; intervalos y pruebas pareadas de `nDCG@10`;
   desglose de la distribución de ítems retenidos por usuario; métricas de diversidad,
   novedad, cobertura y concentración; la tabla comparativa v12/v14/v15; el matiz de equidad
   sobre `cf-user-knn-v1`; la explicación de las cinco mejoras que producen el resultado v15;
   fallos, usuarios omitidos y limitaciones; interpretación prudente con la bibliografía ya
   documentada, sin convertir resultados sintéticos en afirmaciones sobre usuarios reales —
   todo en
   [`evaluation-results-400-test-2026-09-12-v15.md`](./evaluation-results-400-test-2026-09-12-v15.md);
6. el fundamento científico exhaustivo de por qué se eligió leave-fraction-out sobre el tag
   dominante y por qué se descartaron Given-N, K-fold, predicción de rating, solo-más-allá-
   del-acierto y N fijo global, en
   [[2026-09-12 - LOO por fraccion sobre el tag dominante, fundamento y alternativas descartadas]].

Fuente normativa: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md) y
[`recommendation-algorithms.md`](../methodology/recommendation-algorithms.md).
