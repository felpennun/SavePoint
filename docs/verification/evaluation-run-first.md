# Primera comparación de recomendadores bajo protocolo congelado

## Propósito

Este documento resume la primera ejecución completa del arnés de evaluación de SavePoint.
La ejecución compara el baseline aleatorio, el baseline de popularidad y las tres variantes
del recomendador basado en contenido sobre los mismos usuarios sintéticos, particiones,
exclusiones y conjuntos de candidatos. El artefacto JSON es la fuente de verdad y conserva
el detalle por usuario: `docs/verification/evaluation-run-first.artifact.json`.

## Identidad y reproducibilidad

| Campo | Valor |
|---|---|
| Commit del código | `9f167cf` |
| Versión del protocolo | `2` |
| Hash SHA-256 del protocolo | `9a313dcd2673c96793db823e3cc06ebb4b07e7b0e7359d9c4a951b370ae089ff` |
| Versión del corpus | `2026.09.1` |
| Hash SHA-256 del snapshot de ratings | `648df3ded83dfab9e6f479a0d80291d3690e783e7b25f424b8e1e4260d839f01` |
| Versión del conjunto de características | `fs-v1` |
| Hash del manifiesto de partición | `f7550e3bef4730dbbaf120a8dd002950aef510543c74bcf0670ce30e6fe69aea` |
| Semilla leave-one-out | `20260907` |
| Semilla de partición de usuarios | `20260908` |
| Split ejecutado | `test` |
| Simulación | `true` |

El comando ejecutado fue:

```text
docker compose -f infra/compose.yaml run --rm api python manage.py run_evaluation --corpus-version 2026.09.1 --split test --evidence-json /workspace/apps/api/evaluation-run-first.artifact.json
```

El protocolo exigió una única ejecución del split de test. El marcador de consumo impide
repetirla sin una nueva versión explícita del protocolo.

## Población y conjunto de candidatos

Se solicitaron 40 usuarios sintéticos y se evaluaron 26. Otros 14 se excluyeron porque no
tenían un positivo elegible para leave-one-out. Un positivo es elegible si tiene al menos una
valoración o un rating externo válido, de acuerdo con la regla congelada para la evaluación.
El corpus gobernado permanece completo para la búsqueda del catálogo, pero el universo de
esta comparación queda acotado a obras evaluables.

Cada usuario evaluado conserva su propio hash de candidatos. Los conjuntos compartidos entre
los cinco algoritmos contienen entre 26.997 y 27.014 obras, y el held-out se reincorpora al
conjunto para que todos los algoritmos tengan la misma oportunidad de recuperarlo. Cuando el
held-out no aparece en el top 20 devuelto, `heldout_rank` se registra como `null`; no se
interpreta como un dato ausente, sino como "fuera del ranking observado".

## Resultados agregados

Los valores son promedios sobre los 26 usuarios evaluados. En esta ejecución todos los
algoritmos obtuvieron cero aciertos dentro de K=20; por ello las cuatro métricas agregadas
son `0.000` en los tres cortes.

| Algoritmo | K | Precision | Recall | nDCG | MAP |
|---|---:|---:|---:|---:|---:|
| `random-v1` | 5 | 0.000 | 0.000 | 0.000 | 0.000 |
| `random-v1` | 10 | 0.000 | 0.000 | 0.000 | 0.000 |
| `random-v1` | 20 | 0.000 | 0.000 | 0.000 | 0.000 |
| `popularity-v1` | 5 | 0.000 | 0.000 | 0.000 | 0.000 |
| `popularity-v1` | 10 | 0.000 | 0.000 | 0.000 | 0.000 |
| `popularity-v1` | 20 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-weighted-v1` | 5 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-weighted-v1` | 10 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-weighted-v1` | 20 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-multiplicative-v1` | 5 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-multiplicative-v1` | 10 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-multiplicative-v1` | 20 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-twostage-v1` | 5 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-twostage-v1` | 10 | 0.000 | 0.000 | 0.000 | 0.000 |
| `content-cbf-twostage-v1` | 20 | 0.000 | 0.000 | 0.000 | 0.000 |

## Lectura del resultado

El titular del protocolo es `nDCG@10`. La comparación observada queda empatada:
`random-v1`, `popularity-v1` y las tres variantes de contenido presentan `nDCG@10 = 0.000`.
No se debe convertir este empate en una afirmación de que los algoritmos tienen la misma
calidad general: la muestra es sintética, el split utiliza un único positivo por usuario y
el catálogo elegible es muy grande frente al corte top-20.

El resultado es un hallazgo válido de la simulación, no un motivo para repetir el test ni
evidencia sobre usuarios reales. La interpretación está limitada a los arquetipos, corpus,
ratings, semillas y configuración congelados en este artefacto. Las comparaciones con más
semillas, cohortes, cobertura, diversidad, novedad e incertidumbre corresponden a la Fase 3.

## Verificación

| Comprobación | Resultado |
|---|---|
| `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/evaluation -q` | `69 passed` |
| `powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1` | `PASS` |
| Artefacto JSON | Cinco algoritmos, tres cortes, métricas por usuario y hashes presentes |
| Repetición del split de test | Bloqueada por el marcador de protocolo consumido |

## Limitaciones

La ejecución mide evidencia de simulación sobre cuentas sintéticas y no comportamiento de
usuarios reales. El snapshot de ratings y el corpus son inmutables para esta comparación,
pero su cobertura y distribución condicionan los resultados. El documento tampoco sustituye
la revisión humana de la adecuación académica de las métricas, los supuestos y la
interpretación.
