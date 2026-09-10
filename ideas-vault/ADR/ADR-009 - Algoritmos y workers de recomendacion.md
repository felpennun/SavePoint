---
tags: [adr, tema/recomendadores, tema/evaluacion, tema/arquitectura]
---

# ADR-009 - Algoritmos y workers de recomendación

**Estado:** aceptado (2026-09-10). Fuente canónica:
[[../docs/adr/ADR-009-recommendation-algorithms-and-workers|ADR-009]] y
[[../docs/methodology/recommendation-algorithms|especificación completa]].

## Decisión resumida

SavePoint usa un catálogo versionado de baselines, variantes content-based,
user-KNN, híbridos y MMR. La señal semántica principal es el conjunto de tags
curados: `0,75` tags y `0,25` plataformas; franquicia (`0,02`) y desarrollador
(`0,015`) solo son confirmaciones. Los tags se ponderan por IDF suavizado y se
normalizan por obra para conservar el peso total de la familia.

La comparación offline usa 16 algoritmos y la web publica 15 secciones más la
heurística de producto `tag-taste-v1`. Web y offline comparten rankers,
features, snapshots, candidatos y versiones. Las diferencias deliberadas son
el conjunto de usuarios de referencia colaborativo: todos los demás en web y
solo `train` offline.

## Workers

Cada mutación de biblioteca crea una revisión y una sección en PostgreSQL por
algoritmo publicado. Los workers dedicados se ejecutan en paralelo, pero los
resultados permanecen privados hasta que todas las secciones de la revisión
terminan correctamente. Entonces se activa un único snapshot. Revisiones o
configuraciones antiguas se marcan obsoletas y no pueden publicarse.

La decisión busca separar latencia HTTP, aislamiento de fallos, tiempo de pared
de la evaluación y consistencia de la versión visible. PostgreSQL sigue siendo
la fuente durable; no se introduce Redis sin evidencia de rendimiento.

## Base científica

La arquitectura contenido–perfil–comparación se apoya en Pazzani y Billsus
([[https://doi.org/10.1007/978-3-540-72079-9_10|content-based recommendation]]).
La ponderación IDF y el espacio vectorial parten de Salton y Buckley
([[https://doi.org/10.1016/0306-4573(88)90021-0|term weighting]]). User-KNN se relaciona con GroupLens ([[https://doi.org/10.1145/192844.192905|Resnick et al.]]) y el diseño híbrido con Burke
([[https://doi.org/10.1023/A:1021240730564|hybrid recommender systems]]).
MMR se basa en Carbonell y Goldstein
([[https://doi.org/10.1145/290941.291025|diversity-based reranking]]) y nDCG
en Järvelin y Kekäläinen
([[https://doi.org/10.1145/582415.582418|cumulated gain evaluation]]).

Estas fuentes justifican las familias y principios, no los pesos concretos de
SavePoint. `0,75/0,25`, `beta = 0,5`, `m = 25`, `lambda = 0,80`, los umbrales,
las semillas y los demás parámetros son decisiones locales, explícitas y
reproducibles que deben validarse con el protocolo congelado.

## Enlaces

- [[Recomendador basado en contenido]]
- [[Recomendador colaborativo]]
- [[Recomendador hibrido]]
- [[Conjunto de candidatos compartido]]
- [[Versionado de resultados]]
- [[Jobs offline]]
- [[Paridad de despliegue]]
- [[Mapa - Investigacion (recomendadores)]]
