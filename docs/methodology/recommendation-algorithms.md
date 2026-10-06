<!-- generated-by: gsd-doc-writer -->

# Algoritmos de recomendación de SavePoint

**Estado:** especificación técnica vigente, aceptada el 2026-09-10;
sección 3 (pesos y familias de contenido) y sección 5.1 (núcleo de
similitud) revisadas el 2026-09-13 para `fs-v13` — ver ADR-009 y
[[2026-09-12 - fs-v13, pesos por familia de etiqueta y correccion del sesgo de metadatos ausentes]]  
**Protocolo de evaluación:** `protocol_version = 16`  
**Corpus congelado:** `2026.09.2`  
**Feature set:** `fs-v13-family-weighted-tags`  
**Regla de similitud:** `facet-similarity-v8`  
**Fórmula IDF:** `smoothed-idf-l2-per-family-v2`

Este documento es la descripción técnica canónica del sistema de recomendación
implementado. Define qué algoritmos existen, qué datos consumen, cómo se
calculan sus señales, cómo se combinan, qué limitaciones tienen y por qué se
han elegido frente a alternativas no implementadas. Las evidencias fechadas
de cada importación, cobertura o ejecución siguen siendo documentos de
`docs/verification/`; este documento describe el contrato vigente, no sustituye
los hashes de esos artefactos.

## 1. Alcance y catálogo implementado

SavePoint mantiene tres familias conceptuales:

1. **Baselines:** sirven para interpretar el resultado experimental; no
   pretenden representar el gusto de una persona.
2. **Contenido:** comparan las características de una obra con el perfil
   construido a partir de la biblioteca del usuario.
3. **Colaborativo e híbrido:** usan valoraciones explícitas de otros usuarios,
   o combinan esa señal con contenido.

La implementación offline compara 16 algoritmos:

| Identificador | Familia | ¿Se publica en web? | Papel |
|---|---|---:|---|
| `random-v1` | baseline | No | Suelo de comparación aleatorio |
| `popularity-v1` | baseline | No | Popularidad agregada de cuentas demo |
| `content-cbf-weighted-v1` | contenido | Sí | Variante ponderada de referencia |
| `content-cbf-multiplicative-v1` | contenido | Sí | Producto contenido × rating |
| `content-cbf-twostage-v1` | contenido | Sí | Banda de similitud y desempate por rating |
| `content-cbf-neg-v1` | contenido | Sí | Variante con evidencia negativa |
| `content-cbf-weighted-pop-v1` | contenido + PopScore | Sí | Suma con popularidad externa |
| `content-cbf-multiplicative-pop-v1` | contenido + PopScore | Sí | Producto con oscilación de popularidad |
| `content-cbf-twostage-pop-v1` | contenido + PopScore | Sí | Banda y desempate rating/PopScore |
| `content-cbf-neg-pop-v1` | contenido + PopScore | Sí | Suma con evidencia negativa y PopScore |
| `recency-v1` | contenido + novedad | Sí | Contenido, rating, PopScore y recencia |
| `content-cbf-mmr-v1` | contenido + diversidad | Sí | MMR sobre Weighted |
| `content-cbf-mmr-pop-v1` | contenido + diversidad | Sí | MMR sobre Weighted-Pop |
| `cf-user-knn-v1` | colaborativo | Sí | Vecindad de usuarios por ratings |
| `hybrid-weighted-cf-v1` | híbrido | Sí | `0,60` contenido + `0,40` colaborativo |
| `hybrid-mmr-v1` | híbrido + diversidad | Sí | Híbrido seguido de MMR |

Además existe `tag-taste-v1`, que es una heurística de producto publicada en
su propia sección. No forma parte de la comparación académica de los 16
algoritmos: se diseñó como una funcionalidad sencilla de onboarding y no como
un modelo entrenado.

Los IDs conservan el sufijo `v1` por compatibilidad del catálogo de variantes.
La configuración matemática que consumen sí está versionada globalmente por
`FEATURE_SET_VERSION`, `SIMILARITY_RULE_VERSION`, la fórmula de rating, la
fórmula de PopScore y la huella de configuración publicada.

## 2. Frontera común de datos

### 2.1 Obra gobernada y candidata

La consulta común parte de `governed_works(corpus_version)`:

```text
is_dlc = false
AND in_corpus = true
AND first_release_date <= eligibility_cutoff_date
AND, si se solicita, corpus_version = corpus_version
```

La elegibilidad de recomendación es más estricta que la visibilidad del
catálogo:

```text
rating IS NOT NULL
AND total_rating_count >= 5
```

Una obra no elegible continúa disponible para búsqueda, ficha y colección,
pero no entra en ningún algoritmo de recomendaciones. Tampoco se recomienda
ninguna obra que ya tenga una fila `LibraryEntry` del usuario, con
independencia de si está pendiente, jugando, terminada, abandonada o sin
valoración.

Esta frontera evita tres problemas: mezclar DLC con obras principales,
recomendar lanzamientos futuros y permitir que una nota externa sin suficiente
evidencia domine la salida.

### 2.2 Evaluación offline

El protocolo utiliza `leave_one_out_per_user`:

1. Una obra relevante es una entrada `completed` o una entrada con
   `rating_half_steps >= 7`.
2. Se escoge una obra relevante mediante `random.Random(f"{seed}:{user_id}")`.
3. Esa obra es el único positivo retenido.
4. Se elimina del historial visible del usuario para construir el perfil, pero
   se devuelve al conjunto de candidatas para que pueda recuperarse.
5. Todos los algoritmos reciben exactamente el mismo manifiesto de candidatas.

El particionado vigente es de 400 usuarios sintéticos: 240 para `train`, 80
para `validation` y 80 para `test`, con semilla `20260908`. La comparación
calcula `precision@K`, `recall@K`, `nDCG@K` y `MAP@K` para `K = 5, 10, 20`; la
métrica principal es `nDCG@10`. También se calculan cobertura, concentración,
diversidad intra-lista y novedad cuando son estimables.

La relevancia del test es binaria y el split tiene un único positivo por
usuario. Por ello, las cifras responden a una prueba de recuperación de un
ítem retenido, no a una estimación completa de satisfacción humana.

## 3. Representación de contenido

### 3.1 Señal editorial unificada

La dimensión semántica principal es `GameWork.curated_labels`, expuesta en el
vector como `tag:<slug>`. **Desde `fs-v13` (2026-09-13), esta familia contiene
únicamente género y subgénero** (`CuratedLabel.Kind.GENRE`/`SUBGENRE`): un
subgénero como `Souls-like` es un refinamiento de un género como RPG, no una
señal competidora, así que comparten un único bloque IDF. Tema, modo y
característica —antes parcialmente fundidos aquí— ahora tienen sus propias
familias (`theme:`, `mode:`, `feature:`; ver §3.2). Las keywords crudas, Theme
crudo sin curar, Player-Perspective y GameMode no entran directamente como
dimensiones.

Esto evita que sinónimos o metadatos editoriales de distinto nivel pesen como
si fueran conceptos independientes. Por ejemplo, variantes normalizadas de
roguelike comparten una única etiqueta curada; `Superhero`, `Pixel Art` y
`Cyberpunk` se representan como etiquetas del corpus con la política editorial
vigente. `Cyberpunk` es una etiqueta de género/tag; `Superhero` es de tema
(`theme:`) y `Pixel Art` de característica (`feature:`) desde `fs-v13` — cada
una vive ahora en su propia familia en vez de competir por IDF dentro de un
único bloque `tag:`.

### 3.2 Pesos de familias (revisado 2026-09-13, `fs-v13`)

El contrato de familias es:

| Familia | Namespace del vector | Peso máximo | Tipo | Función |
|---|---|---:|---|---|
| Etiquetas curadas (género + subgénero) | `tag:` | `0,60` | Núcleo | Semántica diferenciativa principal |
| Tema | `theme:` | `0,20` | Opcional/bono | Ambiente/escenario (Horror, Fantasía, Sci-fi…) |
| Característica | `feature:` | `0,10` | Opcional/bono | Descriptor técnico/formato (Mundo abierto, VR, Retro…) |
| Modo | `mode:` | `0,05` | Opcional/bono | Contexto social (Un jugador, Cooperativo…) |
| Plataformas permitidas | `platform:` | `0,05` | Núcleo | Compatibilidad material |
| Franquicia/saga | `franchise:` | `0,02` | Opcional/bono | Confirmación positiva |
| Desarrollador | `developer:` | `0,015` | Opcional/bono | Confirmación positiva |

**Núcleo vs. opcional/bono, y por qué solo dos familias son núcleo.** Hasta
`fs-v12`, género, subgénero, tema, modo y característica compartían un único
presupuesto (`0,75`) repartido por IDF dentro de ese bloque, con plataforma
como segundo núcleo (`0,25`). Dos hallazgos en sesión revisando el reparto de
peso motivaron el cambio a `fs-v13`, ambos documentados en detalle en
[[2026-09-12 - fs-v13, pesos por familia de etiqueta y correccion del sesgo de metadatos ausentes]]
y en ADR-009:

1. Un subgénero estadísticamente raro (p. ej. `souls-like`, IDF≈7,54) podía
   pesar más que los géneros de una obra juntos (p. ej. `rpg`+`action`,
   IDF≈2,88+1,97) solo por su rareza en el corpus, invirtiendo la jerarquía
   semántica declarada del proyecto ("género como núcleo").
2. La primera corrección probada —repartir el mismo presupuesto entre las
   cinco familias, renormalizado dinámicamente solo sobre las familias
   presentes en ambos lados— introducía un sesgo distinto: si una familia
   (p. ej. tema) faltaba en una comparación, las familias restantes recibían
   automáticamente una cuota *relativa* mayor. Dos obras con la misma
   afinidad de género exacta podían puntuar distinto según si la otra
   además tenía un tema flojo o ningún tema, premiando la escasez de
   metadatos en vez de ser neutral a ella.

La solución final limita el **núcleo renormalizado** (`core` en §5.1) a
`tag` y `platform` — las dos familias con cobertura casi universal, así que
el caso de renormalización (una de las dos ausente) es realmente raro, no el
camino común. `theme`, `mode` y `feature` reciben el mismo tratamiento que ya
tenían `franchise`/`developer`: una coincidencia solo suma al resultado final
(fuera del núcleo), y una ausencia en cualquiera de los dos lados no resta ni
redistribuye — se excluye de esa comparación por completo, nunca se pliega en
el denominador renormalizado del núcleo. El bonus opcional combinado
(`theme + feature + mode + franchise + developer`) queda acotado por
construcción a la suma de sus pesos máximos.

Las plataformas se restringen a la allowlist de
`catalogue.corpus.PLATFORM_ALLOWLIST`. Un facet ausente se omite; no se imputa
ni redistribuye su peso a otra familia.

### 3.3 IDF por familia (revisado 2026-09-13, `fs-v13`)

La rareza se calcula una vez por versión del corpus, nunca con datos privados
del usuario — pero **desde `fs-v13`, cada familia tiene su propio universo de
referencia `N`**: "obras gobernadas con al menos un valor de esa familia", no
el corpus gobernado completo. De lo contrario, una familia con cobertura baja
(`feature`, ~13 %) saldría con un IDF inflado frente a una casi universal
(`tag`, ~100 %) solo por tener un denominador mal dimensionado para su propia
población — no por ser realmente más rara dentro de su propio dominio.

```text
N_f     = número de obras gobernadas con al menos un valor de la familia f
df_t    = número de esas obras que tienen el valor t
s       = 1,0  (suavizado aditivo)

idf(t)  = ln((N_f + s) / (df_t + s)) + 1
```

El suavizado mantiene un valor finito incluso para un valor observado en una
sola obra. Para una obra con conjunto de valores `T` de la familia `f`, su
bloque se normaliza conservando exactamente el peso configurado de esa
familia (`FACET_WEIGHTS[f]`, tabla de §3.2):

```text
q_t       = idf(t)
norm_T    = sqrt(sum(q_t² para t en T))
w(f:t)    = FACET_WEIGHTS[f] * q_t / norm_T
```

Una etiqueta genérica y muy frecuente **dentro de su propia familia** aporta
menos en la dirección del vector; una etiqueta rara y diferenciativa aporta
más. La normalización L2 por obra y por familia es esencial: IDF cambia la
dirección semántica, pero no permite que una obra con muchos valores de una
familia gane únicamente por tener más campos. `platform` recibe ahora IDF
propio por la misma vía (antes usaba un reparto plano `1/√k`, ver más abajo).

Si no se proporciona un perfil IDF, la función de bajo nivel mantiene el modo
uniforme `peso_familia / sqrt(|T|)` para compatibilidad de fixtures. Los
rankers web, offline, el perfil y la caché de vectores siempre resuelven los
cinco perfiles IDF (`tag`/`theme`/`mode`/`feature`/`platform`) del corpus
activo (`all_family_idf_profiles`).

Franquicia y desarrollador no usan IDF: si una obra tiene `k` valores
observados,

```text
w(f:v) = peso_familia / sqrt(k)
```

La caché `WorkFeatureVector` almacena estos vectores dispersos. Es una caché
determinista, no un modelo entrenado. `FEATURE_SET_VERSION` cambió a
`fs-v13-family-weighted-tags` y las 190.479 obras gobernadas fueron
rematerializadas bajo el nuevo contrato el 2026-09-12.

## 4. Perfil de preferencias del usuario

### 4.1 Peso de cada entrada

El peso de actividad se comparte entre el perfil de contenido y
`tag-taste-v1`:

```text
status_weight(completed) = 3
status_weight(playing)   = 2
status_weight(pending)   = 1
status_weight(abandoned) = 0

r = clamp(rating_half_steps / 10, 0, 1)
rating_intensity = r²

entry_weight = status_weight + rating_intensity
```

La potencia `2` hace que una valoración alta sea evidencia más intensa que
una valoración simplemente positiva. El rating personal no se suma de nuevo a
la puntuación de una candidata: modula la fuerza con la que la obra de la
biblioteca contribuye al perfil.

### 4.2 Perfil positivo

El perfil de contenido usa únicamente entradas `completed` o `playing` con
rating personal. Una entrada con rating inferior a `7` no se añade al perfil
positivo; aporta evidencia negativa separada. Para cada obra usada:

```text
v_i       = feature_vector(work_i)
v'_i      = v_i / ||v_i||₂

profile   = sum(entry_weight_i * v'_i) /
            sum(entry_weight_i)
```

El perfil resultante no se vuelve a normalizar globalmente antes de calcular
la afinidad; sus valores conservan la intensidad relativa acumulada de las
entradas.

### 4.3 Evidencia negativa

Si una obra `completed` o `playing` tiene rating personal menor que `7`, sus
tags se cuentan como evidencia de rechazo. Solo se activa una etiqueta
negativa cuando aparece en al menos tres entradas de baja valoración. El
vector negativo se construye con esos recuentos y se normaliza con L2.

Solo `content-cbf-neg-v1` y `content-cbf-neg-pop-v1` consumen esta señal. La
protección evita convertir una única experiencia negativa en una preferencia
negativa estable.

### 4.4 Arranque en frío

Con menos de tres entradas positivas o sin perfil con features, las variantes
de contenido entran en modo `insufficient_history`. No inventan un perfil
personal: ordenan con la combinación de señales de candidato de su variante y
declaran la limitación en el payload. El endpoint de `tag-taste-v1` devuelve
un estado explícito sin historial. No se usa silenciosamente la biblioteca de
otro usuario.

## 5. Similitud de contenido

### 5.1 Afinidad por facet

Para una familia `f`, sean `P_f` los valores positivos del perfil y `C_f` los
valores de la candidata. El solapamiento conserva los pesos del perfil:

```text
overlap_f        = P_f ∩ C_f
profile_coverage = sum(P_f[t] para t en overlap_f) / sum(P_f[t] para t en P_f)
candidate_precision = |overlap_f| / |C_f|
```

El núcleo usa una media F con `beta = 0,5`:

```text
F_beta = ((1 + beta²) * coverage * precision) /
         (beta² * precision + coverage)
```

`beta < 1` da más influencia a la precisión de la candidata que a la
cobertura del perfil. Así, una obra que declara muchos géneros o plataformas
no gana automáticamente por enumerar más valores.

La similitud de núcleo es una media ponderada solo sobre las familias que
tienen datos en ambos lados. **Desde `fs-v13`, el núcleo se limita a `tag` y
`platform`** (§3.2) — las únicas dos con cobertura casi universal, por lo que
renormalizar cuando una falta es de verdad un caso raro:

```text
core = sum(weight_f * F_beta_f) / sum(weight_f activos)
```

Con datos completos, `weight_tag = 0,60` y `weight_platform = 0,05`.

### 5.2 Bonus de confirmación (revisado 2026-09-13, `fs-v13`)

Tema, característica, modo, franquicia y desarrollador son ahora familias
opcionales/bono con el mismo tratamiento: una escala de coincidencia positiva
contra el valor más fuerte del perfil de esa familia, fuera del núcleo
renormalizado:

```text
optional_affinity_f = min(1,
    sum(P_f[t] para t en overlap_f) / max(P_f[t] para t en P_f))

optional_bonus = 0,20 * affinity_theme
               + 0,10 * affinity_feature
               + 0,05 * affinity_mode
               + 0,02 * affinity_franchise
               + 0,015 * affinity_developer

similarity = min(1, core + optional_bonus)
```

Una familia opcional que no coincide aporta `0`; una familia ausente en
cualquiera de los dos lados es neutral — ni resta, ni redistribuye su peso al
núcleo. Esta asimetría es deliberada: un tema, una saga o un estudio
confirman un interés ya observado, pero no deben reemplazar la similitud
semántica de género/plataforma, y su ausencia no debe inflar artificialmente
esa similitud de núcleo (ver el hallazgo 2 de §3.2).

### 5.3 Coseno

La función `cosine(p, v)` se reserva para comparar vectores completos, en
particular la redundancia de MMR y la diversidad de listas:

```text
cosine(p, v) = (sum(p_i * v_i)) /
              (sqrt(sum(p_i²)) * sqrt(sum(v_i²)))
```

Se devuelve `0` si algún vector está vacío, se acota a `[0, 1]` y la
auto-similitud de un vector no vacío es exactamente `1`. La similitud
principal de contenido es la regla por facets anterior, porque permite
explicar por separado tags, plataformas, franquicia y desarrollador.

## 6. Señales escalares de candidata

Estas señales no son dimensiones del vector de contenido.

### 6.1 Rating externo con confianza bayesiana

El rating de candidata procede del `CorpusRatingSnapshot` congelado. Si hay
varias filas de snapshot para una obra, el rating de la obra se pondera por
`rating_count`; el `total_rating_count` usado para confianza es el máximo
disponible en las filas seleccionadas.

El prior del corpus es la media de ratings ponderada por `total_rating_count`:

```text
corpus_prior = sum(rating_j * count_j) / sum(count_j)
```

Para cada candidata observada:

```text
n = total_rating_count
m = 25
rating_bayes = (n * rating_igdb + m * corpus_prior) / (n + m)
rating_bayesian_normalized = rating_bayes / 100
rating_quality = rating_bayesian_normalized²
rating_confidence = n / (n + m)
rating_final = rating_quality * rating_confidence
```

El prior contrae las notas con poca evidencia hacia la media y
`rating_confidence` conserva una penalización explícita por volumen. El
volumen no se vuelve a multiplicar: `rating_volume` es una señal de evidencia
para el payload:

```text
rating_volume = log1p(n) / log1p(max_n_del_view)
```

Cuando una candidata no tiene rating externo observado, el sistema puede usar
la mediana del rating externo por sus tags curados y aplicar la transformación
de calidad. El resultado se marca `rating_term_is_fallback = true`; no se
presenta como una observación IGDB.

### 6.2 PopScore de IGDB

El PopScore no usa el número bruto directamente. Para cada primitiva de IGDB
se transforma `value` con `log1p(value)` y después se calcula un percentil de
ranking promedio dentro del snapshot congelado:

```text
normalised = 0,5                                      si solo hay una fila
normalised = (start_rank + end_rank - 1) / (2 * (n - 1))  en otro caso
```

Los empates ocupan el intervalo común y todos los valores quedan en `[0, 1]`.
Las cuatro primitivas obligatorias son:

| Primitiva | Peso |
|---|---:|
| `Visits` | `0,40` |
| `Playing` | `0,25` |
| `Played` | `0,25` |
| `Want to Play` | `0,10` |

La composición es:

```text
PopScore = 0,40 Visits
         + 0,25 Playing
         + 0,25 Played
         + 0,10 WantToPlay
```

Si falta cualquiera de las cuatro primitivas, no existe composición observada.
Las variantes que la consumen aplican el suelo explícito `popscore = 0,0` y
marcan `popscore_imputed = true`; no redistribuyen los pesos.

### 6.3 Recencia

Solo es estimable para una obra con fecha no futura y rating externo observado.
Para el año del corte:

```text
year_gap = max(0, cutoff.year - release_date.year)
recency_score = 0,35 ^ year_gap
```

Por tanto, las obras del año del corte valen `1,0`, las del año anterior
`0,35`, etc. Se eligen años naturales en vez de una semivida diaria para que
la señal sea interpretable y reproducible.

## 7. Algoritmos de contenido y combinaciones

En las fórmulas siguientes:

- `C` es la similitud de contenido `facet_similarity` en `[0,1]`.
- `R` es `rating_final` o el fallback de rating marcado.
- `P` es PopScore normalizado; cuando falta en una variante Pop vale `0`.
- `N` es la similitud negativa.
- `X` es `recency_score`.

La función `combine` limita las entradas a `[0,1]`. En las sumas ponderadas,
si una señal opcional es `None`, se excluye y se divide por la suma de los
pesos activos; el cero imputado de PopScore sí es un término activo.

### 7.1 Cuatro variantes base

| Algoritmo | Fórmula exacta | Motivo |
|---|---|---|
| Weighted | `S = 0,70 C + 0,30 R` | Referencia aditiva legible; contenido domina y rating ordena |
| Multiplicative | `S = C * R` | Una candidata necesita simultáneamente afinidad y calidad |
| Two-stage | `b = min(4, floor(5C)); S = b + R/6` | La afinidad determina la banda; rating no rescata una baja afinidad |
| Negative | `S = max(0, 0,70C + 0,30R - N)` | Penaliza tags repetidamente mal valorados |

`content-cbf-weighted-v1` es la referencia de las variantes porque sus pesos
son explícitos y su comportamiento es fácil de explicar. Las demás aíslan
decisiones de combinación que se pueden comparar manteniendo las mismas
candidatas, features y snapshots.

### 7.2 Variantes con PopScore

| Algoritmo | Fórmula exacta |
|---|---|
| Weighted-Pop | `S = 0,55C + 0,25R + 0,20P` |
| Multiplicative-Pop | `S = C * R * (0,80 + 0,40P)` |
| Two-Stage-Pop | `b = min(4, floor(5C)); S = b + (0,80R + 0,20P)/6` |
| Negative-Pop | `S = max(0, 0,55C + 0,25R + 0,20P - N)` |

En la variante multiplicativa, `P = 0` produce un factor `0,80` y `P = 1`
produce `1,20`; es un ajuste acotado, no una sustitución de la afinidad.
PopScore se incorpora como señal externa de descubrimiento, no como evidencia
personal del usuario.

### 7.3 `recency-v1`

Su combinación nominal es:

```text
S = 0,20C + 0,20R + 0,20P + 0,40X
```

El peso de `0,40` hace que sea una variante de novedades, pero conserva
personalización de contenido. Si `X` no es estimable, la combinación ponderada
renormaliza los pesos de las señales activas. No se añade `rating_volume` como
otro término porque su información ya participa en `R` mediante la confianza
bayesiana.

## 8. Diversidad mediante MMR

MMR es una capa de reordenación, no un nuevo modelo de relevancia. Primero se
calcula el ranking base y se conserva su relevancia como evidencia. Después se
selecciona de un pool de tamaño:

```text
pool = max(100, 5 * K)
```

El primer elemento es el de mayor relevancia base. Cada siguiente elemento
maximiza:

```text
MMR(i) = lambda * relevance(i)
       - (1 - lambda) * max(cosine(i, j) para j ya seleccionados)
```

Con `lambda = 0,80`:

```text
MMR(i) = 0,80 * relevance(i) - 0,20 * redundancia(i)
```

Se usa el coseno de los vectores `fs-v13` (§3) para la redundancia. MMR reduce
listas dominadas por obras casi idénticas sin cambiar la fórmula de relevancia
del algoritmo base. El payload expone `mmr_relevance`, `mmr_redundancy` y
`mmr_score`.

Las variantes son `content-cbf-mmr-v1` sobre Weighted,
`content-cbf-mmr-pop-v1` sobre Weighted-Pop y `hybrid-mmr-v1` sobre el híbrido.

## 9. Colaborativo basado en usuarios

### 9.1 `cf-user-knn-v1`

Este algoritmo usa exclusivamente valoraciones personales explícitas de
`LibraryEntry`; no usa tags, plataformas, IDF, PopScore ni rating IGDB de la
candidata.

Cada rating personal se normaliza:

```text
r_ui = clamp(rating_half_steps / 10, 0, 1)
```

Para el usuario objetivo `u` y un usuario de referencia `v`, se toma la
intersección de obras valoradas `I_uv`. Si hay menos de dos obras comunes, la
similitud es `0`. En la intersección se centra cada vector en su media:

```text
sim(u,v) = sum((r_ui - mean_u) * (r_vi - mean_v)) /
           (sqrt(sum((r_ui - mean_u)²)) *
            sqrt(sum((r_vi - mean_v)²)))
```

Solo se conservan similitudes positivas y se seleccionan los 20 vecinos con
mayor similitud. La predicción de una candidata `i` es:

```text
CF(i) = sum(sim(u,v) * r_vi para vecinos que valoraron i) /
        sum(sim(u,v) para esos vecinos)
```

Si no hay vecindad útil o ningún vecino cubre la candidata, se usa el fallback
de frecuencia de interacción de la población de referencia:

```text
frequency(i) = usuarios_de_referencia_con_rating(i) /
               usuarios_de_referencia_con_rating_alguno
```

En web la referencia son todos los demás usuarios con ratings; en offline es
exclusivamente `train`. Esa diferencia es intencionada para evitar que
validación/test contaminen la comparación. Se expone `neighbor_count` y
`rating_term_is_fallback` para que la salida sea auditable.

### 9.2 Por qué no usa IDF

IDF corrige la frecuencia de documentos en una representación de contenido.
`cf-user-knn-v1` no compara documentos ni features: compara coincidencias de
comportamiento usuario-obra. Aplicar IDF a esa señal mezclaría dos espacios
semánticos y no tendría una definición natural de `df_tag`. Si se desea
reducir la popularidad de ítems en colaboración, debe definirse como una
variante colaborativa independiente —por ejemplo con una penalización de
popularidad de ítem—, no reutilizando IDF de tags.

## 10. Algoritmos híbridos

### 10.1 `hybrid-weighted-cf-v1`

Se calcula la relevancia de `content-cbf-weighted-v1` y la de
`cf-user-knn-v1`, sobre la misma candidatura:

```text
H(i) = 0,60 * ContentWeighted(i)
     + 0,40 * CF(i)
```

Si el colaborativo no tiene historial suficiente, se conserva la relevancia
Weighted completa (`H = ContentWeighted`) y se marca el fallback. No se
penaliza a un usuario nuevo por carecer de vecinos.

### 10.2 `hybrid-mmr-v1`

Reutiliza exactamente `H(i)`, toma un pool `max(100, 5*K)` y aplica la fórmula
MMR de la sección 8 con `lambda = 0,80`. La diversidad se aplica después de
combinar contenido y colaboración, por lo que no cambia el reparto `0,60/0,40`
de relevancia.

## 11. `tag-taste-v1`: heurística de producto

`tag-taste-v1` no es una variante más de la comparación académica. Es un
algoritmo de producto determinista, sencillo y transparente:

1. Lee la biblioteca del usuario hasta `generated_at`.
2. Calcula `entry_weight` con la fórmula común.
3. Acumula cada tag curado de cada obra vista con
   `taste_weight(tag) += entry_weight * idf(tag)`.
4. Elige como tag primario el que aparece en más entradas; los empates usan
   `slug` canónico.
5. Busca obras inéditas gobernadas con ese tag, rating de catálogo y al menos
   1.000 valoraciones de catálogo.
6. Ordena por la suma exacta de pesos de los tags coincidentes, después por
   `GameWork.total_rating` y finalmente por `canonical_slug`.

Su fórmula de puntuación es:

```text
TagTaste(i) = sum(taste_weight(t) para tags t de i que están en el perfil)
```

El IDF aquí evita que un tag que aparece en casi toda la biblioteca domine el
gusto. La selección del tag primario sigue siendo por frecuencia de entradas,
no por el máximo peso IDF; esa separación mantiene estable la idea de
“género principal” de la estantería.

## 12. Explicabilidad y DTO

Los rankers no generan una explicación textual libre. Devuelven evidencia
numérica y tokens localizables:

- `contributions`: porcentaje de contribución de cada tag solapado;
- `reason_signals`: como máximo dos señales que existen realmente en perfil y
  candidata;
- `rating_term` y `rating_term_is_fallback`;
- `negative_similarity` cuando aplica;
- señales escalares (`rating_final`, `rating_volume`, `popscore`, `recency_score`);
- en colaborativo, número de vecinos;
- en MMR, relevancia, redundancia y score de selección.

`display_rating` es una señal de presentación del producto y se hidrata en el
borde de la respuesta. No modifica el score del algoritmo ni sustituye al
rating externo congelado.

## 13. Paralelización web y offline

### 13.1 Worker web por sección

Una modificación de `LibraryEntry` u `OwnedCopy` incrementa
`RecommendationState.collection_revision` y encola una sección por cada
algoritmo publicado. La configuración actual tiene 15 secciones: las 14
variantes de contenido/colaborativo/híbridas y `tag-taste-v1`.

Cada servicio de Compose ejecuta:

```text
python manage.py process_recommendation_jobs --loop \
  --algorithm-id <su-algorithm-id>
```

La cola vive en PostgreSQL, que es la fuente de verdad. La reclamación usa
`select_for_update(skip_locked=True)`, de modo que dos procesos no calculan la
misma sección. Cada trabajo incorpora revisión, algoritmo y
`configuration_fingerprint`.

El snapshot no se publica parcialmente:

1. cada worker calcula y persiste su `result_payload` privado;
2. si una sección falla, se conserva el snapshot anterior;
3. solo cuando las 15 secciones han terminado en `succeeded` se crea/actualiza
   el `RecommendationSnapshot` y se activa en `RecommendationState`;
4. si cambia la colección o la configuración durante el cálculo, el trabajo se
   marca `obsolete` y no puede publicar datos obsoletos.

La huella de configuración incluye versión de features, versión de similitud,
pesos de familias, IDF, PopScore, rating y parámetros de todas las variantes.

### 13.2 Evaluación offline paralela

`run_evaluation_parallel` crea un proceso aislado por algoritmo mediante
`ProcessPoolExecutor`. Cada proceso:

- recibe el mismo protocolo, corpus y split;
- reconstruye el ranker compartido para un único `algorithm_id`;
- devuelve duración, estado y artefacto;
- no escribe el marcador de test por separado.

El proceso padre valida que todos los artefactos coinciden en protocolo, hash
de snapshots, corpus, feature set, split y manifiesto de candidatos. Solo
fusiona resultados si todos tienen éxito. Si uno falla, el artefacto global es
`failed` y no se marca el test como consumido.

### 13.3 Razones de la decisión

La paralelización se ha elegido por cuatro razones:

1. **Latencia de producto:** una recomputación no bloquea la petición HTTP ni
   obliga a esperar secuencialmente todas las estanterías.
2. **Aislamiento de fallos:** una variante lenta o defectuosa no invalida el
   estado anterior ni impide que las demás terminen su trabajo privado.
3. **Rendimiento experimental:** las variantes son comparadores independientes
   una vez congelados los candidatos; varios procesos reducen el tiempo de
   pared y conservan el tiempo individual de cada algoritmo.
4. **Reproducibilidad:** la paralelización está por encima del ranker. No crea
   fórmulas diferentes: web y offline llaman a las mismas funciones y declaran
   los mismos hashes.

La publicación atómica es la contrapartida necesaria: la ejecución es paralela,
pero la visibilidad para el usuario es una única versión completa. PostgreSQL
se mantiene como fuente durable para evitar introducir Redis o una cola
externa como requisito metodológico sin evidencia de necesidad.

## 14. Decisiones frente a alternativas no implementadas

| Alternativa | Decisión | Motivo técnico/metodológico |
|---|---|---|
| Géneros IGDB crudos | No usar directamente | La taxonomía editorial unificada evita duplicados y mezcla de niveles |
| Keywords, Theme, Perspective o GameMode crudos | No usar directamente | Tienen ruido, sinónimos y semánticas heterogéneas; solo entran tras curación |
| Raw rating o `display_rating` como vector | No usar | Es una señal escalar y mezclarla con tags confundiría similitud con calidad |
| Volumen bruto sumado al rating | No usar dos veces | `total_rating_count` ya participa en shrinkage y confianza bayesiana |
| PopScore bruto | No usar | Escala larga y sesgo de popularidad; se normaliza por snapshot y percentil |
| Igualar pesos tag/plataforma | No usar | La decisión de producto prioriza semántica y mantiene plataforma como restricción |
| Franquicia/desarrollador como núcleo | No usar | Cobertura desigual y riesgo de recomendar por coincidencia superficial |
| Penalización negativa sin umbral | No usar | Una sola mala experiencia no basta para inferir rechazo estable |
| Coseno puro como similitud principal | No usar | Menos separable en explicaciones y más vulnerable a features abundantes |
| Media aritmética sin F0,5 | No usar | Favorece candidatas con muchos metadatos declarados |
| Semivida diaria de recencia | No usar | Es menos interpretable y sensible al día exacto del corte; se prefieren años |
| Item-KNN colaborativo | No implementar ahora | Requiere una matriz ítem-ítem y otra hipótesis de generalización; user-KNN es más legible con el rating explícito disponible |
| ALS/BPR/matrix factorization | No implementar ahora | Añaden entrenamiento, hiperparámetros y dependencia de interacciones suficientes; dificultan atribuir resultados con población sintética |
| Redes neuronales, embeddings o LLM | No implementar ahora | Coste, opacidad y requisitos de datos no justificados por la pregunta del TFG |
| Modelos de grafos o secuenciales | No implementar ahora | El historial actual no tiene una hipótesis temporal/secuencial que justifique esa complejidad |
| Optimización multiobjetivo en el score | No implementar ahora | Se separan relevancia y diversidad: MMR permite estudiar la diversidad sin ocultarla dentro de los pesos de afinidad |
| IDF en colaborativo | No usar | IDF pertenece al espacio documento-tag; CF opera sobre usuario-obra |

Estas exclusiones son decisiones de alcance y validez, no afirmaciones de que
los métodos descartados sean universalmente peores. Podrían evaluarse en una
extensión del TFG, pero exigirían una variante versionada, nuevos controles de
datos y una comparación bajo el mismo protocolo.

## 15. Base científica de las decisiones

La literatura respalda las familias y principios metodológicos utilizados,
pero no convierte los valores concretos de SavePoint en constantes universales.
La distinción es importante para el TFG:

- **Fundamento científico:** contenido, ponderación de términos, similitud,
  vecinos colaborativos, híbridos, diversificación y métricas tienen
  antecedentes publicados.
- **Decisión de diseño de SavePoint:** los pesos por familia de `fs-v13`
  (`tag = 0,60`, `theme = 0,20`, `feature = 0,10`, `mode = 0,05`,
  `platform = 0,05`), los bonuses, `beta = 0,5`,
  `m = 25`, los pesos de estado, el umbral de tres obras, `lambda = 0,80`,
  `K = 5/10/20`, el mínimo de cinco ratings, los pesos de PopScore y
  `year_decay = 0,35` son elecciones explícitas para este corpus y este TFG.
  Se justifican por interpretabilidad, cobertura, control del sesgo y
  reproducibilidad, y deben defenderse con la evaluación congelada; no se
  presentan como valores demostrados por una fuente externa.

### 15.1 Correspondencia entre literatura y sistema

| Elemento implementado | Base científica | Qué se toma de la literatura | Qué se decide localmente |
|---|---|---|---|
| Recomendador basado en contenido | Pazzani y Billsus (2007), [DOI 10.1007/978-3-540-72079-9_10](https://doi.org/10.1007/978-3-540-72079-9_10) | Describir los ítems, construir un perfil de intereses y comparar ambos para recomendar | Tags curados, uso de biblioteca, estados y rating personal como intensidad |
| Vector disperso, IDF y coseno | Salton y Buckley (1988), [DOI 10.1016/0306-4573(88)90021-0](https://doi.org/10.1016/0306-4573(88)90021-0) | La ponderación estadística de términos y la representación vectorial permiten discriminar rasgos informativos | IDF por familia curada (tag/theme/mode/feature/platform), suavizado `+1`, normalización L2 y peso de familia `0,60` para `tag` (`fs-v13`) |
| F-beta | van Rijsbergen (1979), referencia bibliográfica en [Information Retrieval](https://www.dcs.gla.ac.uk/Keith/Preface.html) | Equilibrar precisión y cobertura con un parámetro `beta` | `beta = 0,5` para priorizar precisión de la candidata y limitar el efecto de metadata abundante |
| User-KNN colaborativo | Resnick et al. (1994), [GroupLens, DOI 10.1145/192844.192905](https://doi.org/10.1145/192844.192905), y Herlocker et al. (2004), [DOI 10.1145/963770.963772](https://doi.org/10.1145/963770.963772) | Filtrado colaborativo por preferencias de usuarios similares, similitud sobre ratings y agregación ponderada | Ratings explícitos, centrado por la media, mínimo de dos coincidencias y `K = 20` vecinos positivos |
| Híbrido | Burke (2002), [DOI 10.1023/A:1021240730564](https://doi.org/10.1023/A:1021240730564) | Combinar fuentes complementarias para aprovechar sus ventajas y compensar sus debilidades | Suma `0,60` contenido + `0,40` CF y fallback de contenido en cold start |
| MMR y diversidad | Carbonell y Goldstein (1998), [DOI 10.1145/290941.291025](https://doi.org/10.1145/290941.291025) | Reordenar maximizando relevancia y penalizando redundancia con `lambda` | Pool `max(100, 5K)`, `lambda = 0,80` y coseno sobre `fs-v13` |
| Evaluación de ranking | Järvelin y Kekäläinen (2002), [DOI 10.1145/582415.582418](https://doi.org/10.1145/582415.582418), y Herlocker et al. (2004) | La posición importa; nDCG, precision, recall y MAP son familias adecuadas para listas ordenadas | `nDCG@10` como headline, `K = 5/10/20`, un positivo leave-one-out y métricas más-allá-del-acierto |
| Diversidad y novedad | McNee, Riedl y Konstan (2006), [DOI 10.1145/1125451.1125659](https://doi.org/10.1145/1125451.1125659), y Vargas y Castells (2011), [DOI 10.1145/2043932.2043955](https://doi.org/10.1145/2043932.2043955) | La exactitud no agota la utilidad; diversidad, novedad y cobertura deben medirse aparte | MMR solo como capa de reordenación y métricas `intra_list_diversity`, novedad y cobertura sin ocultarlas en nDCG |
| Shrinkage bayesiano | Fundamento de Empirical Bayes y shrinkage, [Cambridge, Large-Scale Inference](https://doi.org/10.1017/CBO9780511761362.002) | Las observaciones escasas pueden contraerse hacia un prior común para reducir varianza | Prior de media ponderada del corpus, `m = 25`, potencia de calidad `2` y confianza `n/(n+25)` |

La fuente de contenido justifica la arquitectura perfil–ítem–comparación, no
la semántica concreta de los videojuegos. Por eso la curación editorial de
`CuratedLabel` es una decisión de validez de datos: se eliminan duplicados y
ruido antes de aplicar el modelo, y se conserva el diccionario de mapeo como
evidencia. Del mismo modo, la literatura de IDF justifica dar más peso a rasgos
discriminativos, pero el cálculo `df` sobre obras gobernadas y la elección de
suavizado son adaptaciones reproducibles al corpus de SavePoint.

### 15.2 Justificación científica de no usar otros modelos

La factorización matricial es una alternativa reconocida en recomendación
colaborativa; Koren, Bell y Volinsky la presentan en [Matrix Factorization
Techniques for Recommender Systems, DOI 10.1109/MC.2009.263](https://doi.org/10.1109/MC.2009.263).
No se incorpora en esta versión porque la pregunta del TFG exige comparar
señales legibles sobre una población controlada, y una factorización
introduciría factores latentes, entrenamiento y más grados de libertad. Esta
es una limitación de alcance, no una conclusión de inferioridad.

También se evita presentar una lista exacta como evidencia suficiente de
utilidad. McNee et al. advierten que optimizar solo métricas de exactitud puede
producir listas poco útiles; por eso SavePoint publica métricas de diversidad,
novedad, cobertura y concentración aparte, sin inventar una puntuación única
que oculte el trade-off.

### 15.3 Evaluación y amenazas de validez

La evaluación se documenta como simulación, no como prueba con usuarios
reales. La literatura de evaluación de recomendadores insiste en que la tarea,
los datos, la división, la agregación y la métrica pueden cambiar la conclusión;
Herlocker et al. lo sistematizan en su revisión y el trabajo de [Sun (2022),
DOI 10.48550/arXiv.2210.04149](https://doi.org/10.48550/arXiv.2210.04149) discute
específicamente los efectos de los splits y de los baselines de popularidad.
Por eso el protocolo fija corpus, usuarios, semillas, candidatos, exclusiones,
K, métrica headline y consumo único del test antes de comparar algoritmos.

Esto no elimina las amenazas: un único positivo hace que `Recall@K` sea
binario, los usuarios son sintéticos, y la referencia colaborativa no puede
representar una comunidad real. La consecuencia científica correcta es
interpretar los resultados como comparación interna bajo el protocolo
`2026.09.2`, no como una afirmación universal sobre qué algoritmo “es mejor”.

## 16. Reproducibilidad, límites y fuentes de implementación

Cada resultado declara `algorithm_id`, `feature_set_version`, `corpus_version`,
hashes de snapshots, hash de candidatos, parámetros, fecha de generación y
limitación. El protocolo fail-closed comprueba su estructura, su hash y el
consumo único del test.

Las principales limitaciones actuales son:

- la población de evaluación es sintética y no representa satisfacción de
  usuarios reales;
- leave-one-out con un único positivo reduce la evaluación a recuperación
  binaria;
- el rating externo depende de una fuente gobernada y puede tener sesgos de
  cobertura;
- user-KNN web usa todos los demás usuarios disponibles, mientras offline
  está restringido a train, por lo que sus contextos de referencia no son
  idénticos aunque el ranker sí sea el mismo;
- `tag-taste-v1` es un producto heurístico y no debe compararse como si fuera
  el mismo tipo de modelo que los rankers de la tesis.

Fuentes de implementación:

- Features, IDF, rating y cobertura:
  `apps/api/recommendations/content/features.py`.
- Perfil positivo/negativo:
  `apps/api/recommendations/content/profile.py`.
- Similitud:
  `apps/api/recommendations/content/similarity.py`.
- Combinaciones y variantes:
  `apps/api/recommendations/content/combine.py` y
  `apps/api/recommendations/content/variants.py`.
- Ranker de contenido y MMR:
  `apps/api/recommendations/content/rank.py` y
  `apps/api/recommendations/content/diversity.py`.
- Colaborativo e híbrido:
  `apps/api/recommendations/collaborative.py` y
  `apps/api/recommendations/hybrid.py`.
- Heurística de tags:
  `apps/api/recommendations/genre_heuristic.py`.
- Servicio, catálogo de IDs y huella:
  `apps/api/recommendations/service.py` y
  `apps/api/recommendations/published.py`.
- Cola y publicación atómica:
  `apps/api/recommendations/jobs.py`, `signals.py` y `models.py`.
- Evaluación y paralelización:
  `apps/api/evaluation/runner.py` y
  `apps/api/evaluation/management/commands/run_evaluation_parallel.py`.
- Contrato congelado:
  `docs/methodology/protocol.json` y
  `apps/api/evaluation/protocol.py`.

Documentos relacionados: [`ADR-009`](../adr/ADR-009-recommendation-algorithms-and-workers.md),
[`evaluation-protocol.md`](./evaluation-protocol.md),
`similitud-curated-tags-2026-09-10.md`
y `recommendation-architecture-2026-09-09.md` (ambos de `docs/verification/`, no incluido en el repositorio público).
