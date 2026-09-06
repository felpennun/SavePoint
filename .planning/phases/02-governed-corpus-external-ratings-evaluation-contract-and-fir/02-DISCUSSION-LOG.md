# Phase 2: Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-06
**Phase:** 2-Governed Corpus, External Ratings, Evaluation Contract, and First Advanced Recommender
**Areas discussed:** Gobernanza del corpus, Ratings externos e inmutabilidad, Formulación del primer recomendador, Protocolo de evaluación y usuarios sintéticos, Home (novedades/tendencia)

---

## Gobernanza del corpus

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Lista curada (~30-40 plataformas mainstream) | El asistente propone la lista concreta, el autor la revisa; una obra entra si tiene ≥1 release en alguna | ✓ |
| Por categoría de plataforma de IGDB | Aceptar console + portable_console + computer + operating_system; excluir arcade y 'platform' | |
| No borrar plataformas, solo ocultar juegos sin plataforma mainstream | Se conservan las 288 plataformas; se oculta el juego si ninguna es mainstream | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Chip/filtro "En Steam" desde enlaces de tienda de IGDB | Filtro "disponible en Steam" + enlace en la ficha | |
| Me refería a PC / Windows | La allowlist de PC ya cubre la mayoría de juegos de Steam | ✓ |
| Enlaces de tienda en la ficha, sin filtro | Steam/GOG/Epic en detalle, sin filtro de catálogo | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Nombre basura O sin release en allowlist O es DLC | Sin género / sin fecha se conservan pero se listan en el informe | |
| Lo anterior + también excluir sin género y sin fecha de lanzamiento | Corpus más pequeño y denso | ✓ |
| Solo nombre basura y DLC | Mínimo; se queda casi todo | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Marca reversible: campo in_corpus + checksum sobre esa vista | Se conservan las 312k filas; sin tamaño objetivo fijo | ✓ |
| Borrado físico: el corpus ES la base de datos | DELETE de filas no gobernadas | |
| Marca reversible + tope duro de tamaño | Como la recomendada + cap (p.ej. 50k) | |

**User's choice:** lista curada; "Steam" = PC/Windows; reglas estrictas (incluye excluir sin género y sin fecha); marca reversible `in_corpus` sin tope.
**Notes:** —

---

## Ratings externos e inmutabilidad

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| IGDB total_rating bien importado + RAWG/Metacritic solo si la cobertura queda baja | IGDB primario; RAWG con su propio ADR si <~60% | ✓ (con matices) |
| IGDB + RAWG desde el principio | Dos fuentes ya en esta fase | |
| Solo IGDB total_rating | Sin segunda fuente | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Sin suelo duro: se mide y se reporta con honestidad | % de cobertura al informe de calidad | ✓ |
| Exigir >=70% y añadir fuentes hasta llegar | Forzar cobertura mínima | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Mostrar "sin valoración", excluir de sort/filtro por rating; recomendador con fallback explícito | Mediana de género como señal declarada en el recomendador | ✓ |
| Imputar mediana de género en todas partes | También de cara al usuario | |
| Ocultar del catálogo los juegos sin rating | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Tabla snapshot por versión de corpus; experimentos leen snapshot, catálogo lee valor vivo | CorpusRatingSnapshot; cumple DATA-06 | ✓ (con matiz) |
| Congelar total_rating y no volver a importarlo nunca | | |

**User's choice:** IGDB bien importado + RAWG/Metacritic si hace falta para la allowlist; **preferencia por ratings de usuarios, no de crítica**; **investigar bien** cómo funcionan los campos de rating de IGDB/RAWG (el autor no vio ningún rating en lo montado); sin suelo de cobertura; "sin valoración" + fallback de mediana de género en el recomendador; snapshot por `corpus_version` **más** las valoraciones de los propios usuarios de SavePoint sumándose al rating general en vivo.
**Notes:** El campo `total_rating` existe pero el importador IGDB no lo puebla — a investigar y arreglar. Vigilar contaminación entre rating de producto (vivo, mezclado) y de investigación (snapshot).

---

## Formulación del primer recomendador

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Extender rank_genre_taste_v1 con un término de rating | Trazador sobre código en producción; contenido completo a la Fase 3 | |
| Basado en contenido completo ya en la Fase 2 | Vector de features + similitud coseno + rating | ✓ |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Suma ponderada con coeficientes documentados y congelados | final = w1·sim + w2·rating (+ w3·rating_propio) | ✓ (como una variante) |
| Multiplicativo | final = sim · rating | ✓ (como una variante) |
| Dos fases (similitud manda, rating desempata) | Bandas de similitud | ✓ (como una variante) |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Perfil de rating por género + rating propio del candidato cuando exista | Media por género del snapshot + rating propio según confianza | ✓ |
| Solo el rating propio del candidato | Fallback a mediana de género si falta | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Frase corta determinista + detalle desplegable, sin prosa generada | Tabla de contribución por género + término de rating | ✓ |
| Solo la tabla estructurada | | |
| Solo la frase corta | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Laboratorio: variantes con nombre comparadas bajo el protocolo | modo de combinación + features como parámetros; algorithm_id claro | ✓ |
| Elegir una combinación ahora, variantes en la Fase 3 | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Features: géneros + plataformas + franquicia/saga + desarrollador + rating | El planner confirma cobertura de campos IGDB | ✓ |
| Features: géneros + plataformas + rating | Franquicia/desarrollador a la Fase 3 | |
| Que lo proponga la investigación según lo que IGDB dé | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| DLCs: estante propio "Para tus juegos" + señal en el modelo | DLC fuera del catálogo normal, sección aparte si tienes el base | ✓ |
| Solo un empuje dentro de la lista principal | | |
| Fuera del alcance de la Fase 2 | | |

**User's choice:** contenido completo ya en la Fase 2, construido como **laboratorio** de variantes con nombre (las tres combinaciones se implementan y se comparan); features ricas (géneros + plataformas + franquicia + desarrollador + rating); término de rating por perfil de género + rating propio; explicación frase + desplegable marcando la variante; DLCs con estante propio.
**Notes:** El autor pidió explícitamente el enfoque de laboratorio ("es un entorno de estudio") y añadió plataforma y "DLCs de tus juegos" como señales a considerar además de género y rating.

---

## Protocolo de evaluación y usuarios sintéticos

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Completado O valorado alto (rating_half_steps >= 7) | Dos señales de "le gustó" | ✓ |
| Solo valoración alta (>= umbral) | | |
| Cualquier interacción positiva (salvo abandonado) | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Leave-one-out por usuario; K=5,10,20 (titular K=10) | Se retira un juego que le gustó, semilla fija | ✓ |
| Holdout aleatorio 20% por usuario; K=5,10,20 | | |
| Split temporal global | Los usuarios sintéticos no tienen marcas de tiempo reales | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| ~8 arquetipos × ~25 usuarios (~200) + cohorte cold-start explícita | Parámetros por semilla, regenerable, informe de validación | ✓ |
| ~4 arquetipos, más usuarios por arquetipo | | |
| Que lo proponga la investigación desde literatura RecSys | | |

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Rejilla ≤24 en validación, test una vez; congelar toda la lista de métricas, ranking en Fase 2 | train/validación/test disjunto; titular nDCG@10 | ✓ |
| Sin tuning en Fase 2: parámetros fijados a mano y justificados | | |
| Rejilla mayor (≤100 configs) | | |

**User's choice:** relevancia = completado O rating ≥ 7; leave-one-out por usuario, K=5/10/20 titular K=10; ~8 arquetipos × ~25 (~200) + cohorte cold-start 1-3; rejilla ≤24 en validación con split train/validación/test, test único, lista de métricas congelada (Precision/Recall/nDCG/MAP + cobertura/novedad/diversidad), Fase 2 calcula ranking y Fase 3 el resto.
**Notes:** El autor pidió explicación adicional sobre combinación de señales y sobre tuning/métricas; se le explicó con ejemplo numérico y con el porqué del split de validación (evitar overfitting al benchmark) antes de decidir.

---

## Home (novedades / tendencia)

| Opción | Descripción | Elegida |
|--------|-------------|---------|
| Tira "Novedades" ya en el pase de UI de la Fase 2; "tendencia" externa a la Fase 6 | Novedades por first_release_date, sin datos nuevos | ✓ |
| Todo a la Fase 6 | Ni novedades ni tendencia en la Fase 2 | |
| Novedades + tendencia vía popularidad de IGDB, ambas en la Fase 2 | Amplía una fase ya grande | |

**User's choice:** estante "Novedades" (por `first_release_date`) en el pase de UI de la Fase 2; señal de tendencia externa (popularidad IGDB / Steam / picos de jugadores) diferida a la Fase 6.
**Notes:** Surgió a mitad de la discusión; rating y "estar de moda" son señales distintas.

---

## Claude's Discretion

- Arquitectura del backfill de `GameAlias` sobre las obras IGDB (causa raíz del bug de búsqueda) y de la creación de alias en el importador IGDB.
- Forma exacta de los parámetros de URL de los filtros multi-selección (semántica propuesta: varios géneros = AND, varias plataformas = OR).
- Alcance concreto del pase de UI (densidad de catálogo, panel de filtros como desplegables/chips, ficha de juego "escasa").
- Lista concreta de plataformas de la allowlist (a proponer, el autor la revisa).
- Arquetipos concretos de usuario sintético y parámetros (a proponer desde literatura RecSys, el autor los revisa).
- Conjunto exacto de features fiables según cobertura de campos IGDB sobre el corpus gobernado.

## Deferred Ideas

- Filtro / chips por tienda (Steam / GOG / Epic) y enlaces de tienda en la ficha → Fase 6.
- Estante "Tendencia" / juegos de moda por señal externa de popularidad (IGDB Popularity, `hypes`, Steam, picos de jugadores) → Fase 6.
- Segunda o más fuentes de ratings más allá de IGDB/RAWG (p.ej. OpenCritic dedicado) → futura, solo si la cobertura lo exige.
- Modelo de features CAT-05 completo (modos de juego, tags, publishers como entidades) → Fase 6.
- Recomendador colaborativo / híbrido → Fase 4.
- Conjunto completo de métricas más-allá-del-acierto + cohortes + tests estadísticos + recálculo desde artefactos → Fase 3.
- Cobertura total de portadas across el corpus gobernado (heredado de 01.1 D-06) → incremental.
