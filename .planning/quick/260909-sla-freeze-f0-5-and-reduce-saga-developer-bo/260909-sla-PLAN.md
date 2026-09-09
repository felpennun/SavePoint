---
quick_id: 260909-sla
status: complete
---

# Plan: fijar F0,5, bonus opcionales y peso de PopScore

## Objetivo

Consolidar F0,5 como regla oficial del nucleo, reducir los bonus maximos a
`0,02` para saga/franquicia y `0,015` para desarrollador, y reforzar
moderadamente el peso de PopScore. El contrato debe ser identico en web,
workers y evaluacion offline, con resultados de Felipe reconstruidos bajo una
nueva version del protocolo.

## Tareas

1. Versionar el contrato fs-v9/facet-similarity-v5, cambiar los pesos de
   afinidad y PopScore, y actualizar pruebas, protocolo y documentacion
   canonica.
2. Reconstruir la cache, reiniciar/reencolar los diez workers de Felipe y
   verificar la publicacion completa.
3. Archivar la reevaluacion de Felipe y actualizar el estado GSD/vault vivo.

## Verificacion

- Suite backend de recomendaciones y evaluacion.
- TypeScript web.
- 190.479 vectores fs-v9.
- 10/10 workers de Felipe en estado `succeeded`.
- Comparacion reproducible de Silksong y Terraria con el nuevo contrato.
