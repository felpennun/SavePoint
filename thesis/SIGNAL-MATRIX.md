# Matriz de señales demostradas

La matriz separa la publicación v15 (`fs-v12-curated-tags-idf`) de la configuración
vigente v16 (`fs-v13-family-weighted-tags`). Los pesos v16 no se atribuyen a los
resultados v15. Fuentes comunes: `docs/methodology/recommendation-algorithms.md:118-641`,
`docs/methodology/protocol.json:1-25` y las rutas de implementación indicadas.

| señal | representación, transformación y fórmula demostradas | pesos o umbrales demostrados | ámbito | implementación y test | límite o sesgo |
| --- | --- | --- | --- | --- | --- |
| Tags: géneros y subgéneros | Vector de etiquetas; IDF suavizado por familia y normalización L2 por obra en v16. Fórmula: `ln((N_family + 1)/(df_value + 1)) + 1`. | V16: familia `tag` 0,60. V15 permanece en `fs-v12`, sin importar pesos v16 a la publicación. | Directa, contenido y ranking. | `content/features.py:81-136`; `test_content_features.py`, `test_similarity_weights.py`. | Cobertura y rareza de metadatos pueden sesgar similitud. |
| Plataformas | Vector de plataforma y afinidad de faceta. | V16: core 0,05; el protocolo la trata como señal de disponibilidad, no de gusto principal. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | Plataforma no expresa por sí sola preferencia de contenido. |
| Temas | Faceta opcional; coincidencia positiva sobre el perfil ponderado. | V16: 0,20; ausencia neutral, no redistribuye peso. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | Cobertura incompleta; ausencia no debe premiarse. |
| Modos de juego | Faceta opcional con coincidencia positiva. | V16: 0,05; ausencia neutral. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | Metadato ausente o heterogéneo. |
| Características o perspectivas | Faceta opcional de metadatos de obra. | V16: `feature` 0,10; ausencia neutral. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | La cobertura baja puede inflar relevancia si no se normaliza por familia. |
| Franquicia | Coincidencia opcional de confirmación. | V16: 0,02, solo suma cuando hay solapamiento. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | Puede favorecer secuelas y concentrar recomendaciones. |
| Desarrollador | Coincidencia opcional de confirmación. | V16: 0,015, solo suma cuando hay solapamiento. | Directa, contenido. | `content/features.py`; `test_content_features.py`. | No equivale a preferencia por género o mecánica. |
| Valoración externa | Rating bayesiano normalizado con confianza: `rating_final = rating_quality * rating_confidence`, `rating_confidence = n/(n+m)`, con `m=25`. | V16: potencia de calidad 2,0; prior ponderado del corpus. | Directa, contenido e híbrido. | `content/features.py:86-108`, combinadores; `test_content*.py`. | Depende de fuente y volumen de votos externos. |
| PopScore | Popularidad externa materializada; se combina en variantes `*-pop-v1`. | V15: solo variantes PopScore; v16 conserva configuración separada. | Directa en variantes PopScore, no universal. | `content/variants.py`; `test_content*.py`. | Sesgo de popularidad y cobertura de la fuente. |
| Recencia | Señal derivada de fecha; variante `recency-v1` combina contenido, rating, PopScore y recencia. | Decaimiento y parámetros: documentación de protocolo y `content/recency.py`. | Directa solo en `recency-v1`. | `content/recency.py`; `test_content*.py`. | Novedad temporal no demuestra gusto del usuario. |
| Valoraciones personales | Interacciones explícitas usadas para vecindad de usuarios. | Umbrales y vecindad: `recommendation-algorithms.md:563-617`. | Directa en `cf-user-knn-v1` e híbridos. | `recommendations/collaborative.py`; tests de recomendaciones y evaluación. | Cold start sin historial o ratings suficientes. |
| Similitud de contenido | Afinidad de perfil y candidato; en core v16 se usa `F_beta(profile_coverage, candidate_precision)` con `beta=0,5`. | Core v16: tag 0,60 y plataforma 0,05; opcionales no redistribuyen peso. | Directa, contenido e híbrido. | `content/similarity.py`, `content/features.py`; `test_similarity_v6.py`, `test_similarity_weights.py`. | Depende de metadatos y de la representación de perfil. |
| Redundancia por pares | MMR selecciona relevancia frente a similitud con ítems ya elegidos. | V15: `lambda=0,80` para variantes MMR documentadas. | Directa solo en `*-mmr-v1`. | `content/diversity.py`; `test_diversity.py`. | Diversidad mayor no implica relevancia mayor. |
| Relevancia híbrida | Suma de contenido y colaborativo sobre las mismas candidatas. | `hybrid-weighted-cf-v1`: 0,60 contenido + 0,40 colaborativo; MMR híbrido usa `lambda=0,80`. | Directa solo en híbridos. | `recommendations/hybrid.py`; tests de recomendaciones. | Hereda falta de cobertura de ambas fuentes. |
| Popularidad agregada | Conteo o señal agregada de cuentas demo. | Sin peso personalizado: baseline `popularity-v1`. | Directa solo como baseline. | `recommendations/baselines.py`; `test_baselines.py`. | No personaliza y puede concentrar exposición. |
| Aleatoriedad | Orden aleatorio de candidatas elegibles. | Sin peso. | Directa solo como baseline. | `recommendations/baselines.py`; `test_baselines.py`. | Control de comparación, no señal de gusto. |

Las señales de presentación no se declaran aquí como entradas de ranking. Para v15, las
fórmulas y pesos de publicación deben leerse únicamente en el artefacto y documentación
v15; la implementación v16 se conserva como estado actual y no reescribe el experimento.
