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

## Pendientes

Las demás correcciones del profesor, a medida que el autor las vaya indicando.

Relacionado: [[2026-10-05 - Informe y plan para manana]].
