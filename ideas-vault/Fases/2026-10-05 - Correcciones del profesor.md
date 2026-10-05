---
tags: [tfg, correcciones, memoria]
estado: en curso
fecha: 2026-10-05
---

# Correcciones del profesor (registro)

La memoria de `thesis/` se sincronizó el 2026-10-05 con `SavePoint TFG (2).zip`, la versión que ya lleva algunas
correcciones (12 ficheros cambian: bibliografía y secciones 00 a 08). Aquí se anota cada corrección pendiente o hecha.

## Hechas por Claude

1. **Capítulo "Diseño y arquitectura": falta un diagrama de clases/entidades.** El capítulo 4 tenía un modelo de
   dominio simplificado (solo nombres de entidad). Ahora la sección "Modelo de datos, API y sesión" incluye tres
   diagramas de entidades con atributos, claves y cardinalidades, generados desde los modelos reales de Django
   (Figuras 5.2 catálogo, 5.3 biblioteca y cuentas, 5.4 amistades y recomendaciones), con un párrafo que explica la
   notación, y el capítulo 4 enlaza a ellos. Generador reproducible: `scripts/thesis-figures/generate_modelo_datos.py`
   (paso 1 con Django extrae `models_meta.json`; paso 2 con matplotlib dibuja; cada atributo se valida contra el modelo).
   La tabla de endpoints (`tab:endpoints`) pasa de `[H]` a flotante para evitar media página en blanco.
   La memoria queda en 95 páginas.

2. **Resultados "v15 usando v12" frente a la Tabla 5.3 con v13 (capítulo núcleo de investigación, §5.5).** No era un error
   de cifras sino de comunicación: hay dos numeraciones independientes. El *protocolo* de evaluación (v12, v14 y v15 se
   ejecutaron hasta el final) y el *conjunto de características* (`fs-v12`, `fs-v13`). El artefacto publicado
   (`evaluation-400-test-2026-09-12-v15.artifact.json`) registra `protocol_version = 15` y
   `feature_set_version = fs-v12-curated-tags-idf`. La Tabla 5.3 mostraba solo los pesos de `fs-v13` (código vigente),
   con el que **no** se calcularon los resultados. Diferencias reales (commit `5d39108`, 2026-09-12): en `fs-v12`
   etiqueta 0,75 (fusionando género, subgénero, tema, característica y modo) y plataforma 0,25 con reparto plano; en
   `fs-v13` etiqueta 0,60, tema 0,20, característica 0,10, modo 0,05 y plataforma 0,05 con IDF propio. Franquicia
   (0,02) y desarrollador (0,015) no cambian. No existe evaluación publicada con `fs-v13`.
   Cambios en la memoria: párrafo inicial de §5.5 reescrito (las dos numeraciones, qué versión da qué cifras), la
   Tabla 5.3 con una columna por versión, aclaraciones sobre plataforma y núcleo de similitud en `fs-v12`, una frase
   en el protocolo de evaluación del capítulo 7 y otra al abrir "Evolución del protocolo", `fs-v12` en los pies de las
   tablas y la figura de resultados, y una frase en las limitaciones del capítulo 8.

3. **"El número de juegos no coincide con lo que se muestra en el punto 6.2.2".** En la memoria no hay ninguna cifra de
   juegos escrita en §5.5; la incoherencia real era que §6.2.2 da solo las cifras de `2026.09.1` (312.710 obras,
   193.885 gobernadas, 7-09-2026) mientras la evaluación (cap. 7) usa `2026.09.2`, que tiene **190.479** obras
   gobernadas (corte temporal 2026-09-09; `docs/verification/igdb-import-audit-2026-09-09.md` y el artefacto v15) y
   que la memoria no citaba. Cambios: §6.2.2 explica las dos versiones y da la cifra de `2026.09.2`; §5.5 (regla de
   candidata) y §7 (protocolo) citan 190.479 y remiten a §6.2.2. **Aclaración del autor:** lo que el profesor ve es la
   captura de la página de inicio (Figuras de §5.4, `01-inicio-claro/oscuro.png`), cuya franja inferior muestra
   190 479 obras gobernadas (30 695 con nota de IGDB, 33 plataformas, 74 años), cifra de `2026.09.2`, frente a las
   193.885 de §6.2.2. Se añadió una frase junto a las figuras que las ata a `2026.09.2` y a §6.2.2. Las capturas no
   se tocan: son correctas.

4. **Pruebas y verificación (§6.5): faltaba una tabla de resultados finales, la relación requisitos-pruebas o algún caso
   de prueba concreto.** Se añadió la subsección "Resultados finales y trazabilidad" con: tabla de resultado final por
   suite (backend 788/788 en 146 s y frontend 66/66, ejecutados el 2026-10-05; navegador 56/56 del 14-09, no repetido
   desde el rediseño), reparto del backend por área (informe JUnit de esa ejecución: catalogue 156, evaluation 154,
   library 140, accounts 134, recommendations 119, tests 82, audit 3), tabla de trazabilidad de los 15 casos de uso
   (y sus requisitos) con el fichero de pruebas y su número, y dos casos de prueba concretos (CP-1 reintento idempotente
   del alta de copia; CP-2 una colección ajena no revela su existencia) con su prueba automatizada real. Se actualizó
   la frase de recuentos (antes 773 backend del 4-10). Cifras verificadas ejecutando la suite con Docker.

5. **Capítulo 7, Tabla 7.1: el texto decía "tiempo de pared" pero la tabla no tenía esa columna; y no quedaba claro si la
   cohorte `active_history_10_to_20` eran los 79 usuarios.** Se añadió a la tabla la columna *Tiempo (s)* con el
   `duration_seconds` de cada algoritmo del artefacto v15 (de 5,1 s en `popularity-v1` a 493,1 s en `hybrid-mmr-v1`; es
   la duración del proceso de cada algoritmo, no por usuario; en total 4.297,9 s de pared con 2 procesos en paralelo).
   Cohorte: NO son los 79. `active_history_10_to_20` son los 390 usuarios sintéticos con biblioteca no vacía de 10 a 20
   entradas (regla `_cohort_for` de `evaluation/synthetic.py`, protocolo v13); `no_history` son los 10 de arranque en
   frío (0 evaluables). Los 79 evaluados son los de la cohorte activa que caen en la partición de prueba y tienen algún
   ítem relevante elegible (80 solicitados, 1 omitido). Se explica en la presentación de la tabla, en su pie y en la
   sección del protocolo. Posible incoherencia por revisar: el texto del protocolo describe arquetipos con tamaños de
   biblioteca distintos, mientras que desde el protocolo v13 todos los usuarios con historial tienen 10-20 entradas.

6. **Capítulo 7: "los protocolos v6 a v14" se mencionaban sin haberse explicado.** Tabla nueva "Versiones del protocolo de
   evaluación" (al abrir "Evolución del protocolo") reconstruida del historial de `docs/methodology/protocol.json`, de los
   commits y de los documentos de verificación: v1-v2 (congelación inicial; primera ejecución con la población de la Fase 2,
   26 de 40 evaluables), v3-v6 (similitud por facetas y señal de calidad), v7-v9 (peso de PopScore 0,20, rating bayesiano
   m=25, regla de elegibilidad), v10 (rating final, MMR híbrido, rejilla de 31), v11-v12 (etiquetas curadas unificadas; primer
   cálculo con 400 usuarios), v13 (población regenerada; ejecución invalidada por candidatas duplicadas), v14 (piso de
   calidad externa), v15 (leave-fraction-out). No hay documento ni artefacto propio de v11 ni de v3-v5, por eso van agrupadas.
   Hasta v14 la partición fue siempre leave-one-out. Las numeraciones de la Tabla de resultados cambian: ahora es la 7.3.
7. **Capítulo 7: faltaba explicar el reparto entrenamiento/validación/prueba, por qué solo 79 de 400 son evaluables y si se
   ajustaron hiperparámetros en validación.** Subsección nueva 7.2.1 con tabla del reparto (240/80/80 por usuario, semilla
   fija; entrenamiento = referencia del filtrado colaborativo y base de novedad; validación reservada; prueba = comparación
   final con un único consumo por versión). Los 79 son la partición de prueba (80 solicitados) menos 1 usuario sin ítem
   relevante elegible; los otros 320 no se evalúan por diseño. Hiperparámetros: el protocolo declaró una rejilla de 31
   configuraciones para puntuarse solo sobre validación, pero **no se conserva ninguna ejecución de esa rejilla** (todos los
   artefactos son de la partición de prueba; el preflight del 2026-09-09 la deja `not_run`); los parámetros de las 16
   variantes son decisiones de diseño (cap. 5), ni ajustados sobre prueba ni sobre validación. Limitación declarada: el
   protocolo cambió de v12 a v15 viendo resultados de prueba, de modo que el consumo único rige por versión, no entre
   versiones. Datos verificados en `docs/methodology/evaluation-protocol.md`, el artefacto v15 y los checkpoints.
8. **Capítulo 7: v13 aparecía como protocolo válido.** Revisado todo el TFG: solo el cap. 7 lo nombraba. v13 se ejecutó pero
   su ejecución de prueba quedó invalidada por un error del banco de pruebas (candidatas duplicadas por el JOIN con las
   etiquetas curadas, que desbordaba nDCG/MAP de los algoritmos de contenido; commit `69a1b4e`, artefacto
   `evaluation-400-test-2026-09-11.INVALID-duplicate-candidates.artifact.json`). Ahora el texto dice que los resultados
   válidos son solo v12, v14 y v15; la tabla de versiones y la narrativa de "dos cambios sucesivos" aclaran que el paso del
   74 % al 0 % de historial insuficiente se midió en la ejecución v14 (que reúne la población de v13 y el piso de calidad),
   no en v13. Los números de las secciones 5.5 y 8 ya decían "v12, v14 y v15" y no cambian.

## Pendientes

Las demás correcciones del profesor, a medida que el autor las vaya indicando.

Relacionado: [[2026-10-05 - Informe y plan para manana]].
