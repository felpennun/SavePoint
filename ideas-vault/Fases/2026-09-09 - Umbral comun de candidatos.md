# Umbral común de candidatos

Se establece para web y offline la misma regla simultánea:
`rating IS NOT NULL AND total_rating_count >= 5`.

El catálogo gobernado no se recorta: el corpus `2026.09.2` mantiene `190.479`
obras consultables. El subconjunto algorítmico contiene `13.618` candidatas.
El builder compartido de candidatos lo consume tanto el runner offline como los
workers web, y el fingerprint de caché incorpora la política para no reutilizar
resultados calculados con el umbral anterior.

El contrato reproducible pasa a `protocol_version: 6` y el snapshot de ratings
queda fijado en:
`c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc`.

Fuentes canónicas: [[../../docs/verification/recommendation-architecture-2026-09-09|contrato compartido de algoritmos]],
[[../../docs/methodology/protocol|protocolo de evaluación]] y
[[../../docs/verification/recommender-input-preflight-2026.09.2.json|preflight]].
