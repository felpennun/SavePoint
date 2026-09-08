# Phase 3: Explainable Content Recommenders and Baseline Comparison - Discussion Log

## Ampliación posterior del alcance — 2026-09-08

El autor amplió la preparación de la Fase 3 antes de los experimentos:

- Actualizar el corpus gobernado y aumentar su cobertura de juegos valorados.
  La aspiración inicial de 100.000 juegos deja de ser un gate obligatorio; se
  acepta el máximo legal, trazable y reproducible, siempre que se demuestre una
  mejora sobre la cobertura actual.
- No realizar más peticiones a RAWG por agotamiento de cuota. Se investigarán
  Steam User Reviews, OpenCritic, IMDb y MobyGames con un spike previo de
  cobertura y condiciones. Metacritic/OpenCritic no se raspan y Giant Bomb se
  descarta mientras su API de juegos permanezca indisponible.
- Capturar PopScore de todos los juegos elegibles para los que IGDB lo ofrezca,
  usarlo en «Tendencia» del catálogo y como señal pequeña del recomendador,
  siempre mediante snapshots fechados y reproducibles.
- Excluir de todas las superficies los lanzamientos posteriores al día actual;
  congelar la fecha de corte en los experimentos.
- Ampliar las señales a rating, géneros, saga, desarrollador, plataforma,
  volumen de valoraciones, recencia y tendencia; validar pesos mediante
  variantes y ablaciones en vez de fijarlos por intuición.
- Incluir `playing` en el perfil positivo, exigir valoración propia ≥ 3,5/5 y
  generar una señal negativa de género solo cuando existan al menos tres juegos
  mal valorados que compartan dicho género.
- Hacer que la web presente el ranking real del algoritmo y reservar la señal
  colaborativa/híbrida para la Fase 4.
- Separar el corpus explorable del conjunto de salida: las aproximadamente
  200.000 obras gobernadas siguen disponibles para búsqueda, colección y como
  semillas de similitud, pero el recomendador solo puede devolver juegos con al
  menos una valoración o con un rating externo válido cuyo recuento no esté
  disponible.
- Cuando hay texto de búsqueda, ordenar por similitud de nombre/alias y no por
  relevancia, rating ni volumen de votos. Los filtros elegidos por el usuario
  pueden acotar resultados, pero la coincidencia textual gobierna el orden.
- Excluir del catálogo y de las recomendaciones las ediciones alternativas,
  usando metadatos de versión y los tokens `edition`, `edición` y `deluxe` como
  salvaguarda. Se marcan como excluidas; no se borran de la importación.

La investigación inicial encontró que Steam ofrece documentación oficial para
obtener `review_score`, positivos, negativos y total de reseñas por App ID. La
cobertura y el enlace con IGDB todavía deben medirse. OpenCritic parece útil como
fuente crítica adicional, pero no se verificó una vía oficial pública que
autorice una extracción completa; queda condicionado a permiso o API oficial.
CONTEXT.md contiene el contrato detallado y prevalece sobre las decisiones
anteriores incompatibles.

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-07
**Phase:** 3-Explainable Content Recommenders and Baseline Comparison
**Areas discussed:** Métricas beyond-accuracy, Estadística + numpy/scipy, Cohortes y sin-historial, Artefactos inmutables + runs fallidos

---

## Aclaración posterior a la discusión (2026-09-07)

Tras cerrar las cuatro áreas, el autor indicó: *"asume que la fase 3 se va a
ejecutar después de terminar la fase 2, a la que no se le van a hacer cambios"*.

Esto **supersede** dos elecciones tomadas durante la discusión:

- "Rehacer la población de la Fase 2 antes de la Fase 3" y "Sí, reabrir y
  re-congelar para 400 antes de la Fase 3" → ya **no** hay puente de re-freeze
  previo ni modificación de la Fase 2.
- En su lugar: la población enriquecida de ≥ 400 usuarios y el
  `protocol_version: 2` (métricas beyond-accuracy, `robustness`, `user_split`
  re-dimensionado, cohorte cold-start 1-4) son **trabajo interno de la Fase 3**,
  aditivo sobre el `protocol.json` v1 congelado. La población de 200 de la
  Fase 2, su `protocol.json` v1 y la comparación 02-13 quedan intactos y se
  citan como primer resultado.

CONTEXT.md D-06, D-07, D-12, D-13, D-14 y la sección "Dependencias y conflictos
entre fases" reflejan ya este encaje.

---

## Métricas beyond-accuracy (EVAL-04, EVAL-05)

### Distancia ítem-ítem para diversidad intra-lista

| Option | Description | Selected |
|--------|-------------|----------|
| Coseno sobre `WorkFeatureVector` | Reutiliza el vector de features ya cacheado del recomendador de contenido; cero código nuevo; el content-cbf saldrá menos diverso y el aleatorio más | ✓ |
| Jaccard de géneros | Independiente del modelo, más legible, menos resolución | |
| Ambas por separado | Dos columnas; permite discutir la sensibilidad de la métrica | |

**User's choice:** Coseno sobre `WorkFeatureVector`.
**Notes:** El autor pidió explicaciones más sencillas antes de decidir; tras el ejemplo concreto eligió esta opción.

### Señal de la que se deriva la novedad

| Option | Description | Selected |
|--------|-------------|----------|
| Frecuencia en la población sintética | `-log2(fracción de usuarios sintéticos que tienen el ítem)`; misma señal que `rank_popularity_v1`; reproducible offline | ✓ |
| `rating_count` externo de IGDB | Popularidad "del mundo real" pero cobertura ~13,9 % y sesgo de fuente única | |
| Rareza de contenido | Atipicidad de géneros/plataformas; no depende de interacciones | |

**User's choice:** Frecuencia en la población sintética (definición estándar de RecSys).
**Notes:** El autor cuestionó primero por qué hacer una "novedad falsa" si la Fase 6 la rehace. Se aclaró que la métrica de evaluación (interna, congelada, para las tablas del TFG) y el estante de "tendencia" de producto (datos externos en vivo, Fase 6) son artefactos distintos y la Fase 6 no toca `protocol.json`. El autor también observó, con razón, que el recuento histórico de valoraciones no indica tendencia ni novedad actual — motivo para descartar `rating_count` externo. Se etiquetará como "novedad respecto a la población simulada".

### Detalle de la cobertura de catálogo

| Option | Description | Selected |
|--------|-------------|----------|
| Cobertura simple a 10 y 20 | Fracción única del corpus en el top-N de algún usuario | |
| Cobertura + concentración (Gini/entropía) | Añade el reparto de la exposición | ✓ (recomendación registrada; el autor delegó) |
| Solo cobertura a 10 | Lo mínimo de EVAL-05 | |

**User's choice:** "lo que recomiendes" → cobertura agregada a N∈{10,20} + índice de concentración (Gini o entropía) como cifra secundaria.
**Notes:** Delegado explícitamente en Claude.

### Métricas extra además de las tres

| Option | Description | Selected |
|--------|-------------|----------|
| Quedarnos con las tres | Cobertura + diversidad + novedad + ranking congelado | ✓ |
| + sesgo de popularidad (APLT/ARP) | Columna extra muy citable en RecSys | |
| + serendipia / Tú decides | Novedad condicionada a acierto | |

**User's choice:** Quedarnos con las tres.

---

## Estadística + numpy/scipy (EVAL-06, EVAL-08, EVAL-09)

### Multi-semilla: qué varía entre semillas

| Option | Description | Selected |
|--------|-------------|----------|
| 8-10 baratas + 1 población regenerada | Re-sortear held-out (mismos usuarios) + 1 población nueva de comprobación; sección `robustness` en `protocol.json` | ✓ |
| Solo 8-10 baratas | Incertidumbre por muestreo de usuarios queda como limitación declarada | |
| Población regenerada en todas | La más honesta, la más cara, posible inviable en Python puro | |
| Tú decides / research | | |

**User's choice:** 8-10 baratas + 1 población regenerada.
**Notes:** El autor añadió aquí un bloque de requisitos sobre las cuentas sintéticas (ver más abajo y en CONTEXT.md D-12/D-13).

### Usuarios sintéticos más ricos: encaje con el freeze de la Fase 2

| Option | Description | Selected |
|--------|-------------|----------|
| Población nueva enriquecida en Fase 3 encima de la congelada | Dos poblaciones; no rehace nada de la Fase 2 | |
| Rehacer la población de la Fase 2 antes de la Fase 3 | Una sola población; exige re-ratificar EVAL-09 y re-ejecutar 02-13 | ✓ |
| Tú decides / research+planner | | |

**User's choice:** Rehacer la población de la Fase 2 antes de la Fase 3.
**Notes:** Ampliado después a ≥ 400 usuarios, lo que obliga a reabrir el protocolo congelado (`protocol_version` → 2, `user_split` nuevo). El autor confirmó explícitamente "Sí, reabrir y re-congelar para 400 antes de la Fase 3".

### Composición del generador de usuarios sintéticos

| Option | Description | Selected |
|--------|-------------|----------|
| Filtro `rating_count ≥ 10` con 1-2 excepciones sembradas | Bibliotecas con juegos ≥ 10 valoraciones, salvo 1-2 usuarios con un juego sin valoración | ✓ |
| Filtro estricto | Todos con `rating_count ≥ 10`; no ejercita el camino "sin valoración" | |
| Tú decides el umbral | | |

**User's choice:** Filtro `rating_count ≥ 10` con 1-2 excepciones sembradas.
**Notes:** Requisitos numéricos del autor: ≥ 400 usuarios; 10 con 0 juegos, 100 con 1-4 juegos, 50 con >10, resto 5-10; notas propias variadas; algunas cuentas con `OwnedCopy` y otras sin ninguna.

### Señal negativa de notas propias bajas: ¿variante nueva?

| Option | Description | Selected |
|--------|-------------|----------|
| Sí, añadir variante con señal negativa | `content-cbf-neg-v1`: nota baja resta afinidad al género, con salvaguarda | |
| No, solo evaluar las 3 existentes | | |
| Tú decides | | ✓ |

**User's choice:** Tú decides.
**Notes:** El autor razonó la idea (bajar puntos del género por nota propia baja, salvo que sea el único juego del género → "es que es mal juego"). Queda como Claude's Discretion: research valora coste/aporte, planner propone en el PLAN si entra o se difiere, autor ratifica.

### Banda de incertidumbre

| Option | Description | Selected |
|--------|-------------|----------|
| Bootstrap sobre usuarios + dispersión entre semillas | Cubre las dos fuentes de ruido | ✓ |
| Solo bootstrap sobre usuarios | | |
| Solo dispersión entre semillas | | |

**User's choice:** Bootstrap sobre usuarios + dispersión entre semillas.

### Test estadístico de comparación

| Option | Description | Selected |
|--------|-------------|----------|
| Friedman + Wilcoxon por pares + Holm | Omnibus + pareado no paramétrico + corrección múltiple; receta estándar RecSys | ✓ |
| Solo Wilcoxon + Holm | Sin omnibus | |
| t de Student pareado | Paramétrico; nDCG en LOO de un positivo no es normal | |

**User's choice:** Friedman + Wilcoxon por pares + Holm.

### Implementación de la estadística (decisión aplazada del 02-10)

| Option | Description | Selected |
|--------|-------------|----------|
| Híbrido: métricas a mano, scipy solo para tests | | |
| Todo Python puro | Coherente con la ratificación de 02-10; más código y más tests | |
| Aprobar scipy para todo lo estadístico | Tests + bootstrap + intervalos vía `scipy.stats`; nueva dependencia con gate | ✓ |

**User's choice:** Aprobar scipy para todo lo estadístico.
**Notes:** Requiere gate de aprobación de dependencia en el PLAN (pin exacto + evidencia PyPI). Las métricas de ranking y beyond-accuracy siguen escritas a mano y verificadas.

---

## Cohortes y sin-historial (EVAL-07)

### Grupos de usuarios para el desglose

| Option | Description | Selected |
|--------|-------------|----------|
| Por tamaño de biblioteca y por arquetipo | 0 / 1-4 / 5-10 / >10 + ~8 arquetipos | ✓ |
| Solo por tamaño de biblioteca | Tablas más cortas; se pierde el "qué arquetipo se beneficia de qué algoritmo" | |
| Tú decides | | |

**User's choice:** Por tamaño de biblioteca y por arquetipo.
**Notes:** El autor no conocía el término "cohorte"; se explicó como "grupo de usuarios que comparten un rasgo, para mirar sus resultados por separado".

### Usuario con 0 juegos en la tabla del TFG

| Option | Description | Selected |
|--------|-------------|----------|
| "No evaluable en acierto" + chequeo de cold-start | Acierto/ranking = "no definido bajo LOO"; se mide validez del fallback + beyond-accuracy de lo recomendado | ✓ |
| Darles un positivo sintético | Permite nDCG pero ya no son "sin historial" | |
| No incluir grupo de 0 juegos | EVAL-07 dice "including zero-history users" | |

**User's choice:** "No evaluable en acierto" + chequeo de cold-start.
**Notes:** El autor respondió inicialmente sobre la UX de producto de un usuario nuevo (mensaje "aún no tienes juegos" + CTA al catálogo); se separó esa idea (Fase 5 / Fase 6, ya diferida) de la pregunta de evaluación.

### Etiqueta de cohorte por usuario

| Option | Description | Selected |
|--------|-------------|----------|
| Se guarda en el manifiesto de generación (EVAL-09) | Reproducible, sin ambigüedad entre runs | ✓ (recomendación registrada; el autor delegó) |
| Se deriva en tiempo de evaluación | Si cambian los cortes, las tablas dejan de ser comparables | |

**User's choice:** "haz la recomendación" → se guarda en el manifiesto de generación.
**Notes:** El autor añadió aquí los números de población (≥ 400; 10@0, 100@1-4, 50@>10).

---

## Artefactos inmutables + runs fallidos (EVAL-06, EVAL-11, EVAL-12, criterio 4, QUAL-02)

### Qué se persiste por run

| Option | Description | Selected |
|--------|-------------|----------|
| Lista top-N (N grande) por usuario y algoritmo + relevantes + cohorte + tiempos | Recalculable offline sin re-ejecutar modelos; JSON commiteado + MANIFEST | ✓ |
| Solo el rango del held-out + métricas ya calculadas por K | No permite añadir métricas ni cohortes nuevas sin re-correr | |
| Ranking completo sobre todos los candidatos | Enorme, inviable de commitear | |

**User's choice:** Lista top-N (N grande) por usuario y algoritmo + relevantes + cohorte + tiempos.

### Identidad del entorno (EVAL-11)

| Option | Description | Selected |
|--------|-------------|----------|
| Completa y automática | SHA git + versión de Python + hash de lockfiles + `pip freeze` hasheado + SO + digest de contenedor | ✓ |
| Mínima | Solo SHA git + versión de Python + hash de lockfile | |

**User's choice:** Completa y automática.

### Run que falla a medias (criterio 4)

| Option | Description | Selected |
|--------|-------------|----------|
| Estado explícito + el recálculo rechaza lo no-completo | `status: complete\|partial\|failed`; artefacto parcial se escribe pero no alimenta tablas | ✓ |
| Todo o nada | Ante cualquier error no se escribe nada | |

**User's choice:** Estado explícito + el recálculo rechaza lo no-completo.

### Forma de salida de la Fase 3

| Option | Description | Selected |
|--------|-------------|----------|
| Doc de informe generado con tablas, en español, para el TFG | Sin UI interactiva; el panel accesible es Fase 7 | ✓ |
| Además, una vista web mínima de solo lectura | Adelanta parte de la Fase 7 | |
| Tú decides | Formato exacto (Markdown / LaTeX / ambos) | |

**User's choice:** Doc de informe generado con tablas, en español, para el TFG.

---

## Claude's Discretion

- Variante de contenido con señal negativa (`content-cbf-neg-v1` u otro nombre): research evalúa coste/aporte, planner propone si entra como variante nueva comparada bajo el mismo protocolo o se difiere, autor ratifica en el PLAN.
- Fórmula exacta de la métrica de novedad (variante de Vargas & Castells, normalización, ítems con frecuencia cero).
- Gini vs entropía para el índice de concentración de cobertura.
- Valor exacto de N en la persistencia top-N y formato del informe (Markdown / LaTeX / ambos).
- Presupuesto de tiempo y posibles recortes de la ejecución de reproducción por defecto (QUAL-02).
- Tamaño total exacto de la población (≥ 400) y proporciones del `user_split` — propuestos por research, ratificados por el autor (D-13 es one-way).

## Deferred Ideas

- Estante "Tendencia / Novedades reales" desde datos externos de visitas/popularidad → Fase 6 (ya diferido en `02-CONTEXT.md` D-24).
- Pulido de la página `/recomendaciones` para el usuario sin juegos (mensaje + CTA al catálogo) → Fase 5.
- Panel de investigación interactivo y accesible con gráficas + export de figuras → Fase 7 (EVAL-13, EVAL-14, QUAL-04).
- Serendipia, APLT/ARP y otras métricas beyond-accuracy adicionales — no entran en la Fase 3.
- Escenarios de split alternativos al leave-one-out (leave-N-out, split temporal) para explotar el multi-positivo — no se abren en la Fase 3.
