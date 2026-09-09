---
fecha: 2026-09-09
estado: verificado
---

# Auditoría de entradas de recomendación

Esta auditoría prepara la ejecución de la Fase 3. No ejecuta ningún algoritmo ni
consume el conjunto de test. Se ha realizado sobre el corpus gobernado `2026.09.2`.

## 1. Manifiesto reproducible de población

El manifiesto [JSON de población](synthetic-population-manifest-2026.09.2.json) queda
fijado con:

- semilla `20260909`;
- 400 usuarios activos bajo el marcador `synthetic-eval-user`;
- 2.868 entradas de biblioteca;
- identificador de cuenta para los 400 usuarios;
- estado, rating propio, obra, release, edición y copia física/digital por entrada;
- regla `rating_count >= 1` y pesos escalonados documentados;
- partición prevista 240/80/80 con semilla `20260908`;
- hash interno del manifiesto: `be3e43c451724c9c3add784394955397292d20438dc18f17c60b1984e1f4dd38`.

El hash se recalculó desde el JSON canónico y coincide.

## 2. Aislamiento de la población activa

La evidencia completa está en [la auditoría de aislamiento](synthetic-population-isolation-2026.09.2.json).

- Población activa: **400** usuarios.
- Población histórica de Fase 2 conservada: **200** usuarios.
- Solapamiento entre ambas: **0**.
- Partición real: **240 train / 80 validation / 80 test**.
- Particiones disjuntas: **sí**.
- Unión de las particiones igual a la población activa: **sí**.
- Consulta del runner: únicamente `DemoAccountIdentity.marker == 'synthetic-eval-user'`.

Por tanto, los 200 usuarios históricos no entran en la evaluación activa.

## 3. Cobertura y ausencia de señales

La [evidencia JSON de cobertura](recommendation-signal-coverage-2026.09.2.json) y el
comando `audit_recommendation_signals` dejan el recuento reproducible. Sobre las
190.479 obras gobernadas, 30.623 son candidatas a algoritmo.

| Señal o faceta | Presentes | Cobertura | Decisión |
|---|---:|---:|---|
| Géneros | 190.479 | 100,00 % | incluir |
| Plataformas permitidas | 190.479 | 100,00 % | incluir |
| Desarrolladores | 101.018 | 53,03 % | incluir |
| Franquicias | 11.555 | 6,07 % | excluir de los vectores |
| Rating de usuarios IGDB | 27.036 | 14,19 % | usar cuando exista |
| `total_rating_count` | 30.623 | 16,08 % | usar como volumen |
| `recency_score` elegible | 27.036 | 14,19 % | usar solo en la variante de recencia |
| PopScore completo | 9.929 | 5,21 % | usar cuando estén las cuatro primitivas |

El rating usado por los recomendadores sigue siendo el rating de usuarios IGDB; no se
combina con `total_rating` de críticos. `total_rating_count` solo expresa volumen.

### Política de nulos

- Facetas categóricas ausentes: se omiten del vector disperso.
- Rating externo ausente: se aplica fallback a la mediana por género cuando corresponda.
- Volumen ausente: se excluye la señal y se renormalizan los pesos activos.
- Recencia ausente, futura o sin rating: devuelve `null` y no aporta puntuación.
- PopScore con alguna primitiva ausente: no se compone ni se imputa.

## Resultado

Los tres puntos están preparados y verificados. La base, el manifiesto y el contrato de
señales están listos para la siguiente acción, pero los algoritmos aún no se han lanzado.

Fuentes canónicas: [`protocol.json`](../methodology/protocol.json),
[`03-CONTEXT.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-CONTEXT.md)
y [`03-DISCUSSION-LOG.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-DISCUSSION-LOG.md).
