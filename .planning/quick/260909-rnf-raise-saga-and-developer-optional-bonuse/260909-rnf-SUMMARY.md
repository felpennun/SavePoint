---
quick_id: 260909-rnf
status: complete
completed: 2026-09-09
---

# Resumen: recalibracion fs-v8 y comparacion de Felipe

## Resultado

Se publico `fs-v8` / `facet-similarity-v4`. Saga/franquicia usa un bonus maximo
de `0,20` y desarrollador un bonus maximo de `0,15`, ambos multiplicados por
afinidad y aplicados solo cuando existe coincidencia real. El nucleo de
genero/plataforma cambio de F1 a F0,5 para dar mas peso a la precision del
candidato y reducir la ventaja de obras con listas amplias de metadatos.

La cache contiene 190.479 vectores fs-v8 y los diez workers de Felipe terminaron
`succeeded`, publicando la revision 14. Se archivo la comparacion aislada de
Silksong y Terraria en las diez secciones.

## Verificacion

- Recomendaciones y evaluacion backend: `194 passed`.
- TypeScript web: `tsc --noEmit` correcto.
- Cache fs-v8: `190.479` vectores reconstruidos.
- Workers de Felipe: `10/10 succeeded`.
- Evaluacion offline de los 400 usuarios: no ejecutada; esta tarea solo reevaluo
  la cuenta personal solicitada.

## Evidencia

- `docs/verification/recommendation-fs-v8-comparison-felipe-2026-09-09.md`
- `apps/api/feature-vector-cache-fs-v8-2026.09.2.json`
