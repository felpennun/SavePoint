---
quick_id: 260909-ov6
status: complete
---

# Resumen — umbral común de candidatos

## Resultado

Se estableció una única regla para web y offline:
`rating IS NOT NULL AND total_rating_count >= 5`.

El catálogo gobernado continúa conservando `190479` obras consultables. El
subconjunto algorítmico del corpus `2026.09.2` contiene `13618` candidatas.
La web (`build_common`/`build_candidate_manifest`) y el runner offline
(`leave_one_out`) consumen `evaluation_candidate_works`, por lo que no pueden
divergir en la frontera de candidatos.

## Contrato y evidencias

- El protocolo reproducible pasó a `protocol_version: 6`.
- Snapshot de ratings: `c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc`.
- Hash de PopScore conservado: `16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097`.
- Hash del protocolo v6: `41a9da80c99c03e7fd0684351d7e3a675651a13fe9ca1b59cbbd4451e9d8b542`.
- El ruleset de gobernanza se actualizó a v3 y su hash es
  `28ff0ac107bddb2d36faf38732c1040a2052853d33514dbee146389bd0079144`.
- Se regeneraron `docs/verification/corpus-governance-2026.09.2.json`,
  `apps/api/corpus-governance-2026.09.2.json`,
  `apps/api/corpus-ratings-2026.09.2.json` y el preflight de entrada.
- El fingerprint de caché incluye la política de candidatos, invalidando la
  reutilización silenciosa de snapshots calculados bajo el umbral anterior.

## Verificación

- Preflight: PASS; 400 usuarios sintéticos, split 240/80/80, rejilla de 28,
  cero candidatos inválidos.
- Backend dirigido: `61 passed`.
- TypeScript web: `tsc --noEmit` correcto dentro del contenedor web.
- No se ejecutaron rankings, workers ni evaluación experimental.
- No se instaló `statistics.py`; queda como siguiente tarea.
