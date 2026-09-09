# Registro de decisiones y cambios de la jornada — 2026-09-09

## Propósito

Este documento consolida las decisiones tomadas durante la jornada sobre el
corpus, los datos, los recomendadores, la interfaz, la caché, los workers y la
preparación del estudio offline. Es un registro de diseño y verificación; no
contiene resultados de la evaluación de los 400 usuarios sintéticos porque esa
ejecución todavía no se ha lanzado.

## 1. Corpus y datos

Se separaron dos conceptos que habían quedado mezclados:

- El catálogo conserva las 190.479 obras del corpus gobernado para búsqueda y
  consulta.
- Los algoritmos usan únicamente las 13.618 candidatas que cumplen
  `rating IS NOT NULL AND total_rating_count >= 5`, con fecha conocida y no
  futura. Las obras restantes siguen siendo visibles, pero no pueden entrar en
  ningún ranking.

La razón es preservar descubribilidad y trazabilidad sin permitir que una obra
sin rating IGDB o con evidencia insuficiente contamine las recomendaciones.
`rating_count` sigue siendo el número asociado a la observación de rating,
mientras que `total_rating_count` es el volumen total de valoraciones IGDB y es
la señal de confianza. No se usan como sinónimos.

La reimportación de IGDB se mantuvo aditiva: no se borraron datos existentes y
se añadieron o actualizaron campos de señales, desarrolladores, franquicias,
fechas y relaciones DLC/expansión. Los DLC se alojan como obras relacionadas y
no como recomendaciones independientes. El rating visible
`display_rating` combina IGDB y SavePoint únicamente para la interfaz; no entra
en los algoritmos.

## 2. Señales y decisiones de modelado

### Rating IGDB y volumen

Se decidió que una obra con rating IGDB observado conserve su propia calidad,
sin ser arrastrada hacia la media de su género. La transformación actual es:

```text
rating_quality = (rating / 100)^2
rating_confidence = rating_quality * (0,80 + 0,20 * rating_volume)
```

El volumen es `log1p(total_rating_count)` normalizado frente al máximo de la
vista congelada. El perfil medio por género solo queda como fallback explícito
cuando falta el rating observado. La versión de esta señal es
`rating-confidence-v3`. La decisión evita que ratings de 95, 85 y 75 queden
demasiado próximos y premia que una nota alta esté respaldada por muchas
valoraciones.

### Perfil de la colección

Las valoraciones personales de las semillas sí influyen en el perfil del
usuario. La intensidad es `(rating_half_steps / 10)^2` y se combina con el peso
del estado (`completed = 3`, `playing = 2`, `pending = 1`, `abandoned = 0`).
Los géneros repetidos acumulan evidencia ponderada. Solo las entradas
completadas o en curso con al menos 3,5/5 forman evidencia positiva; los
ratings bajos se reservan para el algoritmo negativo con salvaguarda de tres
obras.

### Similitud de contenido

La evolución fue:

1. `fs-v4` fijó la representación inicial de facetas.
2. `fs-v6` añadió saga/franquicia como señal IGDB y desarrollador como señal
   opcional; ambos solo aportaban si coincidían con el perfil y su ausencia
   era neutral.
3. La revisión de Felipe mostró que el bonus de desarrollador se diluía y que
   las obras con muchos géneros acumulaban coincidencias por amplitud. La
   configuración actual es `fs-v7` con regla `facet-similarity-v3`.

En `fs-v7`:

- género pesa `0,50`;
- plataforma pesa `0,25`;
- saga/franquicia pesa `0,18`;
- desarrollador pesa `0,12`.

Género y plataforma calculan una media armónica entre cobertura ponderada del
perfil y precisión de la obra. Una obra con muchos géneros no recibe ventaja
solo por enumerarlos. Saga y desarrollador son confirmaciones exactas y
positivas: no aportan nada por mera presencia, pero una coincidencia puede
aportar hasta `0,18` o `0,12`; juntas tienen un máximo de `0,30`. Así la
coincidencia es visible sin convertirse en el único criterio.

La ausencia de franquicia sigue siendo un dato neutral. La auditoría de Felipe
confirmó que Hollow Knight y Silksong no tienen franquicia IGDB importada, por
lo que no puede existir bonus de saga entre ellos. Sí comparten `Team Cherry`.
Hades y Hades II comparten `Supergiant Games`, por lo que sí pueden recibir el
bonus de desarrollador.

## 3. PopScore y recencia

PopScore se compone con las cuatro señales IGDB normalizadas: visitas `0,40`,
jugando `0,25`, jugado `0,25` y quiere jugar `0,10`. Las variantes PopScore
imputan `0,0` cuando falta la señal completa, evitando que una obra sin datos
se beneficie de una renormalización.

`recency-v1` conserva contenido, rating-confidence y PopScore, pero añade una
recencia por año natural: año del corte `1,0`, año anterior `0,35`, y así
sucesivamente. Sus pesos son `0,30`, `0,20`, `0,10` y `0,40`. El objetivo es
que una novedad sea realmente novedosa y que una obra antigua no suba solo por
tener afinidad histórica.

## 4. Algoritmos y estudio offline

Web, workers y runner offline comparten `rank_content_v1`, el registro de
variantes, la elegibilidad, las señales y los pesos. Se publican nueve
variantes de contenido: cuatro baselines, cuatro variantes PopScore y
`recency-v1`. Existe además `genre-taste-v1` como heurística complementaria,
con una sola estantería para el género más frecuente de la biblioteca.

La web muestra 20 resultados por estantería. El estudio offline mantiene
`K = 5, 10, 20`, selecciona por `ndcg@10` y usa la rejilla declarada en el
protocolo v6. La población activa es de 400 usuarios sintéticos, sustituyendo
los 200 históricos, con split `240/80/80` para train/validation/test. La
selección de obras de sus bibliotecas exige `rating_count >= 1` y usa pesos
escalonados para aproximar la distribución real de volumen.

Se preparó `apps/api/evaluation/statistics.py` con NumPy y SciPy para las
comparaciones pareadas posteriores: bootstrap, Friedman, Wilcoxon y Holm. No
se usa para tunear parámetros y todavía no se ha ejecutado el estudio de los
400 usuarios.

## 5. Web, caché y workers

La página de recomendaciones usa snapshots por usuario y el patrón
stale-while-revalidate: conserva el snapshot anterior mientras el nuevo se
calcula y solo publica cuando todas las secciones terminan correctamente. La
caché es común en infraestructura, pero cada usuario tiene su snapshot y su
huella de colección independientes.

Los diez workers trabajan en paralelo, uno por sección, y abandonan resultados
obsoletos si cambia la colección o la configuración. La publicación es
atómica: ningún resultado parcial sustituye al snapshot visible. Redis quedó
pospuesto porque PostgreSQL ya cubre la caché durable y no existe todavía una
medición de latencia o concurrencia que justifique introducir otra dependencia.

La interfaz se actualizó para mostrar una estantería por variante, explicación
breve y señales relevantes. El catálogo se ordena únicamente por PopScore; los
otros modos de ordenación se retiraron del panel. Las tarjetas de colección,
portada y ficha de juego muestran el mismo `display_rating`.

## 6. Verificación de la jornada

- Caché fs-v7: 190.479/190.479 vectores materializados para
  `2026.09.2`.
- Corpus activo: 190.479 obras gobernadas y 13.618 candidatas algorítmicas.
- Workers de Felipe: 10/10 `succeeded`; snapshot publicado en revisión 14,
  con `feature_set_version = fs-v7`.
- Pruebas backend dirigidas de recomendaciones/evaluación: 192 pasadas.
- TypeScript web: correcto con `tsc --noEmit`.
- La huella publicada cambió a una configuración nueva, por lo que no se
  reutilizó el snapshot fs-v6 anterior.

## 7. Pendientes y límites declarados

- Hollow Knight, Silksong, Hades y Hades II necesitan una futura mejora de
  cobertura de franquicias si se quiere evaluar también la señal de saga en
  esos casos.
- La evaluación estadística y la comparación de los 400 usuarios siguen
  pendientes.
- Las métricas de latencia y concurrencia determinarán si Redis aporta una
  mejora suficiente para justificar su instalación.

Fuentes canónicas: [`protocol.json`](../methodology/protocol.json),
[`evaluation-protocol.md`](../methodology/evaluation-protocol.md),
[`recommendation-architecture-2026-09-09.md`](recommendation-architecture-2026-09-09.md)
y [`feature-vector-cache-fs-v7-2026.09.2.json`](../../apps/api/feature-vector-cache-fs-v7-2026.09.2.json).

## 8. Reevaluacion fs-v8

La configuracion vigente posterior a la jornada usa `fs-v8` y
`facet-similarity-v4`. Saga/franquicia tiene un bonus maximo de `0,20` y
desarrollador de `0,15`, aplicados solo mediante coincidencia y afinidad.

El nucleo genero/plataforma conserva los pesos `0,50` y `0,25`, pero su
afinidad usa F0,5: la precision del candidato pesa mas que la cobertura del
perfil. Esto reduce la ventaja de obras que enumeran muchos generos o
plataformas. El cambio se aplica al vector versionado, al ranker compartido,
los workers y el runner offline.

## 9. Decision final fs-v9

Tras reevaluar el efecto del bonus de saga/franquicia y desarrollador, se fija
como contrato definitivo `fs-v9` / `facet-similarity-v5`:

- F0,5 se mantiene en el nucleo genero/plataforma, con pesos 0,50 y 0,25.
- La precision del candidato conserva mas influencia que la cobertura del
  perfil. Esto limita la ventaja artificial de obras que declaran muchos
  generos o plataformas.
- Saga/franquicia aporta como maximo 0,02 cuando existe coincidencia con el
  perfil ponderado del usuario.
- Desarrollador aporta como maximo 0,015 bajo la misma condicion.
- El bonus opcional combinado queda limitado a 0,035. No se premia la mera
  presencia de una saga o desarrollador y una faceta ausente no se penaliza.

La reduccion busca que estas relaciones mejoren la personalizacion sin hacer
que una saga o una desarrolladora dominen el rating IGDB, la similitud de
contenido o PopScore. La misma formula, version y pesos se usan en el ranker
web, los diez workers y la evaluacion offline. La cache fs-v9 contiene 190.479
vectores y los diez workers de Felipe publicaron correctamente la revision 14.
La comparacion reproducible de Silksong y Terraria queda archivada en
[`recommendation-fs-v9-comparison-felipe-2026-09-09.md`](recommendation-fs-v9-comparison-felipe-2026-09-09.md).

## 10. Refuerzo moderado de PopScore

Se decide aumentar moderadamente la influencia de PopScore sin cambiar su
normalizacion ni sus cuatro señales IGDB. La configuracion queda asi:

- Weighted-Pop y Negative-Pop: contenido 0,55, rating-confidence 0,25 y
  PopScore 0,20.
- Multiplicative-Pop: `swing = 0,20`, con factor entre 0,80 y 1,20.
- Two-Stage-Pop: desempate con rating-confidence 0,80 y PopScore 0,20.
- Recency: contenido 0,20, rating-confidence 0,20, PopScore 0,20 y recencia
  0,40.

El objetivo es que la popularidad tenga un efecto apreciable y comparable al
rating sin dominar la similitud ni la recencia. Se mantiene `popscore_missing_floor
= 0,0`, de modo que una obra sin PopScore sigue recibiendo una penalizacion
explicita. El cambio incrementa la version del protocolo a 7 y se reevaluara
con el mismo snapshot de corpus.
