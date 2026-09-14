# Mapa estructural de fuentes para la nueva memoria

## Propósito y lectura de este documento

Este mapa compara cuatro fuentes de estructura, no cuatro modelos de contenido. La
plantilla de la ETSII fija el soporte editorial; los dos TFG de referencia muestran
formas de organizar una memoria de ingeniería; la memoria histórica documenta un
estado anterior de SavePoint. La propuesta final conserva el soporte de la plantilla,
pero desplaza el foco hacia la investigación reproducible sobre recomendación. No
autoriza todavía la redacción de capítulos ni la modificación de ficheros LaTeX.

Las rutas, hashes y cobertura completa se fijan en
`thesis/SOURCE-MANIFEST.json`. Los PDF tienen cobertura declarada de páginas completa,
pero el índice textual se ha extraído de sus TXT complementarios; la revisión visual
detallada de maquetación, tablas, figuras y fórmulas debe hacerse antes de la entrega
final. No se copia la prosa de las memorias de referencia.

## Fuentes y localizadores

| Fuente | Identidad y cobertura | Uso estructural | Límite |
| --- | --- | --- | --- |
| Plantilla ETSII | `thesis/referencias/plantilla-etsii/TFG.tex:9-64`; SHA-256 `142a2e8c2bb9ae6c3d1e2e0a67e7ac65ca2d85d3dc25d89fb767856baa9044b2`; árbol `plantilla-etsii/` | Clase, portada, preliminares, índices, bibliografía y jerarquía de capítulos. | Es una plantilla, no una prescripción temática. |
| TFG BarGAIN | `thesis/referencias/proyect-final.pdf`, páginas 1-92, SHA-256 `893a46bc03b38ad865dbb5e29f0b90bffc941f25159ceb5b62bb031823ef733a`; índice en `proyecto-front.txt:95-352` y continuación en `proyecto-toc2.txt`. | Orden de gestión, requisitos, diseño, pruebas y manuales. | Su problema y resultados no son trasladables a SavePoint. |
| TFG de predicción volcánica | `thesis/referencias/TFG_Predicción_De_Erupciones_Volcánicas_Mediante_Inteligencia_Artificial.pdf`, páginas 1-117; índice en `volcanes-front.txt:113-264`, SHA-256 del TXT `a13e18e05743c48426f885750157f8842d503ab0b606d6f0673dcb6e9b5845cc`. | Separación por partes, trazabilidad, planificación e investigación experimental. | Las fórmulas, modelos y cifras pertenecen a ese estudio. |
| Memoria histórica de SavePoint | `SavePoint_TFG_Overleaf_2026-09-07.zip`, 68 entradas, SHA-256 `0b1abf0a59498c751cc6fc269a4bed4e22ad8c4b8370d57ac4c07a73b026f4f3`; comparación: 68 iguales, 0 diferentes, 0 ausentes respecto a `thesis/`. | Identificar la estructura previa y evitar presentarla como la nueva memoria. | Es una instantánea histórica, no evidencia suficiente para resultados nuevos. |

## 1. Plantilla oficial ETSII

La plantilla usa `report` a 12 puntos e importa configuración común mediante
`etc/pkgs` y `etc/style` (`TFG.tex:9-13`). Define variables de portada y conserva
portada, agradecimientos, resumen y abstract antes de los índices (`TFG.tex:16-42`).
Después incorpora índice general, índices de figuras y tablas, e índice de extractos
de código (`TFG.tex:45-53`). La bibliografía se resuelve con `unsrtnat` y
`bibliografia.bib` (`TFG.tex:60-62`).

| Orden | Entrada de la plantilla | Localizador | Adaptación a SavePoint |
| ---: | --- | --- | --- |
| 0 | Portada, agradecimientos, resumen y abstract | `sections/00_portada.tex`, `00_agradecimientos.tex`, `00_resumen.tex`, `00_abstract.tex` | Conservar y completar con autoría exclusiva de Felipe Peña Núñez. |
| 1 | Índices general, de figuras, tablas y listados | `TFG.tex:45-53` | Conservar; evaluar un índice de algoritmos solo si es compatible con los paquetes ya presentes. |
| 2 | Introducción | `sections/01_Introduccion.tex:1` | Contexto, problema científico, objetivos, alcance, preguntas y límites. |
| 3 | Estudio previo y gestión | `sections/02_Gestion.tex:1-14` | Planificación, costes, riesgos, GSD, GitHub Issues, agentes y Obsidian bajo dirección del autor. |
| 4 | Análisis del problema | `sections/03_Analisis.tex:1-15` | Requisitos, actores, reglas, casos de uso y trazabilidad. |
| 5 | Diseño de la solución | `sections/04_Diseño.tex:1-6` | Arquitectura, datos, API, seguridad, snapshots y ADR. |
| 6 | Implementación | `sections/05_Implementacion.tex:1-8` | Implementación como soporte, sin desplazar el capítulo científico central. |
| 7 | Pruebas | `sections/06_Pruebas.tex:1-6` | Pruebas funcionales, de seguridad, accesibilidad, reproducibilidad y evaluación offline. |
| 8 | Conclusiones | `sections/XX_Conclusiones.tex:1` | Discusión prudente, limitaciones y trabajo futuro. |

Los ejemplos didácticos de `sections/ejemplos_borrame.tex` no son parte de la
estructura final: sirven para conservar el patrón de figuras, tablas, ecuaciones y
listados, no para añadir un capítulo de ejemplos.

## 2. Índice real del TFG BarGAIN

El índice general del TFG BarGAIN enumera los preliminares y nueve capítulos
(`proyecto-front.txt:95-119`, `319-352`). La secuencia combina antecedentes y
comparación competitiva con una gestión temprana, seguida de requisitos, diseño,
manual, pruebas y conclusiones.

| Orden | Nivel y título real | Página | Localizador | Adaptación razonada |
| ---: | --- | ---: | --- | --- |
| 1 | Introducción y objetivos del proyecto | 1 | `proyecto-front.txt:105-119` | Mantener, incorporando problema científico y límites de generalización. |
| 2 | Análisis de antecedentes y aportación realizada | 4 | `proyecto-front.txt:121-135` | Convertir en estado del arte de catalogación y recomendación. |
| 3 | Comparación con otras alternativas | 6 | `proyecto-front.txt:137-147` | Integrar como subsección del estado del arte y decisiones, sin aislarla como eje. |
| 4 | Análisis temporal y costes de desarrollo | 8 | `proyecto-front.txt:149-171` | Integrar en gestión y metodología, con fases, riesgos y desviaciones. |
| 5 | Análisis de requisitos | 14 | `proyecto-front.txt:173-189` | Conservar con actores, requisitos de información, funcionales, no funcionales y trazabilidad. |
| 6 | Diseño e implementación | 22 | `proyecto-front.txt:191-273` | Separar diseño de implementación, situando algoritmo y protocolo antes de esta última. |
| 7 | Manual de usuario | 41 | `proyecto-front.txt:275-317` | No convertirlo en capítulo central; remitir las capturas y flujos al diseño o anexo. |
| 8 | Pruebas y resultados | 64 | `proyecto-front.txt:319-349` | Dividir en metodología experimental, resultados y pruebas de software. |
| 9 | Conclusiones | 69 | `proyecto-front.txt:352` | Conservar como cierre crítico y trabajo futuro. |

## 3. Índice real del TFG de predicción volcánica

Este TFG presenta explícitamente cinco partes: Introducción, Planificación, Ejecución,
Cierre y Anexo (`volcanes-front.txt:115-171`, `254-264`). La planificación es muy
detallada: requisitos, casos de uso, trazabilidad, EDT, costes, calidad, riesgos y
desviaciones (`volcanes-front.txt:129-170`). La ejecución separa investigación,
iteraciones, aplicación web, instalación, manuales y despliegue
(`volcanes-front.txt:173-252`).

| Parte y orden | Título real | Página | Localizador | Adaptación razonada |
| --- | --- | ---: | --- | --- |
| I.1 | Introducción | 2 | `volcanes-front.txt:115-125` | Conservar como apertura, pero no como única parte científica. |
| II.2 | Planificación | 6 | `volcanes-front.txt:127-170` | Conservar la profundidad de gestión y trazabilidad. |
| III.3 | Investigación | 49 | `volcanes-front.txt:171-228` | Inspirar un bloque autónomo de fundamentos, algoritmos, protocolo y resultados. |
| III.4 | Aplicación Web | 75 | `volcanes-front.txt:230-252` | Conservar como soporte de demostración, no como resultado de investigación principal. |
| IV.5 | Cierre | 93 | `volcanes-front.txt:254-262` | Conservar lecciones, conclusiones y trabajo futuro. |
| V | Anexo | 96 | `volcanes-front.txt:264` | Reservar para material de consulta, tablas extensas y comandos reproducibles. |

El índice de figuras, cuadros, algoritmos y códigos muestra que tales índices pueden
aportar trazabilidad cuando corresponden a artefactos explicados en el texto
(`volcanes-front.txt:266-506`). SavePoint debe usar esta idea con prudencia: cada
figura, tabla, fórmula, listado o algoritmo necesita fuente, etiqueta y cita previa.

## 4. Memoria histórica de SavePoint

La instantánea histórica conserva la misma estructura y los mismos 68 ficheros que el
árbol `thesis/` al comparar cada entrada del ZIP por SHA-256. Su `TFG.tex` contiene
portada, resumen, abstract, acrónimos, cuatro índices y diez capítulos
(`thesis/TFG.tex:10-72`). Entre estos aparecen introducción, estado del arte,
planificación y metodología, requisitos, diseño, datos, implementación, pruebas,
despliegue y conclusiones.

| Orden histórico | Elemento | Localizador | Decisión para la nueva memoria |
| ---: | --- | --- | --- |
| 0 | Preliminares e índices | `thesis/TFG.tex:38-56` | Mantener el soporte, revisar contenido y añadir solo índices compatibles. |
| 1-5 | Introducción, estado del arte, metodología, requisitos y diseño | `thesis/TFG.tex:59-63` | Reordenar para que gestión, fundamentos y requisitos mantengan una trazabilidad clara. |
| 6 | Datos | `thesis/TFG.tex:64` | Integrar con la metodología experimental y procedencia. |
| 7-9 | Implementación, pruebas y despliegue | `thesis/TFG.tex:65-67` | Mantener como capítulos de soporte, compactos frente al bloque científico. |
| 10 | Conclusiones | `thesis/TFG.tex:68` | Mantener con afirmaciones limitadas a la evidencia publicada. |

La igualdad entre ZIP y árbol no convierte la memoria histórica en la nueva memoria.
Su función es evitar pérdidas de trabajo verificables y revelar contenido que debe
revisarse frente al estado del repositorio actual.

## 5. Mapa propuesto para SavePoint

La estructura propuesta conserva los mecanismos de la plantilla, toma de los dos TFG
la necesidad de planificar y trazar, y cambia el centro de gravedad hacia el estudio de
recomendadores reproducibles. Es un mapa de cobertura, no prosa definitiva.

| Parte propuesta | Capítulo o bloque | Cobertura prevista | Procedencia estructural |
| --- | --- | --- | --- |
| Preliminares | Portada, agradecimientos, resumen, abstract, acrónimos e índices | Autoría, síntesis bilingüe y navegación. | Plantilla ETSII. |
| I | Introducción | Contexto, motivación, problema, objetivos, preguntas, alcance, aportaciones y limitaciones. | Plantilla y ambos TFG. |
| II | Gestión, planificación y metodología | Fases, costes, riesgos, calidad, GSD, agentes como herramientas dirigidas por el autor y Obsidian. | Plantilla, BarGAIN cap. 4 y volcánico parte II. |
| III | Estado del arte y fundamentos científicos | Catalogación, recomendación, señales, explicabilidad, evaluación offline y sesgos. | Necesidad específica de SavePoint. |
| IV | Análisis de requisitos | Actores, modelo de información, requisitos, reglas, casos de uso y matriz de trazabilidad. | Plantilla, BarGAIN cap. 5 y volcánico §2.3. |
| V | Diseño de la solución | Arquitectura, API, seguridad, snapshots, artefactos, interfaz y ADR. | Plantilla y BarGAIN cap. 6. |
| VI | Algoritmos y representación | Familias reales, señales, fórmulas, normalización, exclusiones, cold start, explicabilidad y complejidad. | Necesidad específica de SavePoint. |
| VII | Metodología experimental | Corpus, procedencia, población sintética, split, candidatas, métricas, cohortes, hashes, semillas y amenazas a la validez. | TFG volcánico parte III, adaptado al protocolo real. |
| VIII | Resultados y discusión | Tablas y gráficas derivadas de artefactos, interpretación prudente y limitaciones de una ejecución. | TFG volcánico parte III y BarGAIN cap. 8. |
| IX | Implementación, pruebas y despliegue | Backend, frontend, seguridad, backup, restauración y suites de prueba. | Plantilla, BarGAIN caps. 6-8. |
| X | Conclusiones y trabajo futuro | Respuesta acotada a preguntas de investigación, límites y líneas futuras. | Plantilla y ambos TFG. |
| Anexos | Trazas extensas, tablas completas, comandos y material suplementario | Consulta reproducible sin interrumpir el argumento central. | TFG volcánico parte V. |

## Cobertura y límites pendientes

- La plantilla, ambos índices textuales, ambos PDF por páginas declaradas, el ZIP y el
  árbol histórico constan como fuentes con cobertura completa en el manifiesto.
- La validación visual pormenorizada de las páginas de índices, tablas, figuras y
  fórmulas de los PDF sigue pendiente de registrarse como evidencia específica.
- El gate `Sources` no puede pasar aún: requiere además
  `thesis/EVIDENCE-MATRIX.md`. Esta limitación es deliberada; no se sustituye con
  texto inventado ni se modifica aquí esa matriz.
