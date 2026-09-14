# Investigación previa: inventario de la nueva memoria de SavePoint

**Fecha:** 2026-09-14
**Dominio:** inventario académico, trazabilidad y preparación de LaTeX
**Confianza:** ALTA, basada en inspección local del repositorio

## Resumen

La Fase A debe ejecutarse como una extracción reproducible, no como una lectura informal. La recomendación principal es generar primero un manifiesto de entradas con ruta canónica, tamaño, SHA-256, función documental y estado de lectura. Las seis matrices deben derivarse de ese manifiesto y conservar un localizador verificable para cada afirmación. El ZIP de Overleaf y `thesis/` no son fuentes independientes: la comparación SHA-256 realizada en esta sesión devolvió literalmente `zip_entries=68 files_same=68 files_different=0 files_missing=0`. [VERIFIED: comparación SHA-256 local de las 68 entradas]

El principal riesgo científico es temporal. La publicación experimental conserva literalmente `"protocol_version": 15`, `"feature_set_version": "fs-v12-curated-tags-idf"` y `"algorithm_count": 16`, mientras que el puntero actual declara `"protocol_version": 16` y `"feature_set_version": "fs-v13-family-weighted-tags"`. [VERIFIED: docs/verification/phase-07-evidence-manifest.json:9-60; docs/methodology/protocol.json:2-25] La matriz de algoritmos debe separar la configuración evaluada v15 de la implementación vigente v16. No debe asociar los resultados v15 con pesos o fórmulas posteriores.

**Recomendación primaria:** planificar la Fase A en tres pasos cerrados: congelar inventario de fuentes, extraer las seis matrices desde fuentes canónicas con precedencia explícita y ejecutar un verificador cruzado antes de autorizar el esqueleto LaTeX.

## Restricciones del proyecto

- Toda prosa nueva de `.planning/**` y de la memoria se escribe en español. Código, identificadores, nombres de tests y comandos se conservan en inglés. [VERIFIED: CONVENTIONS.md:7-18]
- No se imprimen ni trasladan a matrices secretos, cookies, tokens, credenciales, datos personales o logs brutos. Los hashes identifican bytes, pero no prueban veracidad, calidad o legalidad. [VERIFIED: CONVENTIONS.md:61-69; docs/methodology/phase-07-evidence-package.md:83-91]
- Una dependencia nueva exige aprobación humana y actualización de los controles de legitimidad. La fase de inventario no necesita instalar dependencias de proyecto. [VERIFIED: CONVENTIONS.md:61-63]
- El vault es un espejo conceptual, no una fuente canónica. La tarea actual prohíbe modificar archivos fuera de este informe; el plan de ejecución debe incluir una sincronización acotada del vault después de validar las matrices. [VERIFIED: ideas-vault/README.md:17-36]

## Estrategia de extracción de referencias

1. **Resolver rutas antes de leer.** Las rutas `referencias/...` del encargo no existen en la raíz. Sus equivalentes comprobados están bajo `thesis/referencias/...`; el mismo árbol aparece dentro del ZIP. Esta corrección debe quedar registrada como alias de entrada y nunca aplicarse de forma silenciosa. [VERIFIED: docs/methodology/academic-reference-register.md:11-19]
2. **ZIP.** Usar `tar -tf` para inventariar entradas y SHA-256 en memoria para compararlas con `thesis/`. No extraer sobre el árbol actual. El ZIP es una instantánea de la memoria existente, no la plantilla oficial aislada.
3. **LaTeX.** Extraer `\documentclass`, `\input`, material preliminar, índices y jerarquía `\chapter`/`\section` directamente de `thesis/referencias/plantilla-etsii/`. La plantilla fija `report`, portada, agradecimientos, resumen, abstract, índices de contenido, figuras, tablas y listados, seguidos por estudio previo, análisis, diseño, implementación, pruebas y conclusiones. [VERIFIED: thesis/referencias/plantilla-etsii/TFG.tex:9-64] La memoria actual ya conserva la clase y los preliminares, pero ordena diez capítulos propios. [VERIFIED: thesis/TFG.tex:10-68]
4. **TFG de referencia.** Usar los TXT complementarios para extraer el índice con expresiones regulares y conservar número, título, nivel y página. `proyecto-front.txt` presenta una estructura de introducción, antecedentes, alternativas, gestión, requisitos, diseño, pruebas y conclusiones. [VERIFIED: thesis/referencias/proyecto-front.txt:95-175; 319-352] `volcanes-front.txt` organiza la memoria en las partes literales `I Introducción`, `II Planificación`, `III Ejecución`, `IV Cierre` y `V Anexo`, con requisitos, casos de uso, trazabilidad, EDT, costes, desviaciones, investigación y aplicación web. [VERIFIED: thesis/referencias/volcanes-front.txt:113-215; 230-264]
5. **PDF.** Los TXT sirven para extracción estructural, pero no verifican maquetación, pies, continuidad visual o legibilidad. Debe revisarse visualmente cada página de índice y una muestra de tablas, figuras y fórmulas en los PDF. En esta máquina faltan `pdftotext`, `pdfinfo`, `latexmk`, `pdflatex`, `pypdf`, `pdfplumber` y PyMuPDF; sí están disponibles Docker 29.2.1 y `tar` 3.8.8. [VERIFIED: sondeo local de entorno; thesis/README.md:7-34] El plan necesita un checkpoint de entorno: preferir una herramienta aprobada o Overleaf y no depender de `texlive/texlive:latest` sin fijar versión o digest.

## Inventario del repositorio y precedencia

El recorrido debe partir de `git ls-files`, no de una lista escrita a mano. En `.planning/phases/` hay 209 ficheros, incluidos 66 `PLAN`, 67 `SUMMARY`, 8 `CONTEXT`, 7 `RESEARCH`, 6 `UI-SPEC` y 6 `VERIFICATION`. Los diez ámbitos de código solicitados suman 390 rutas versionadas. [VERIFIED: inventario local con `git ls-files` y `Get-ChildItem`] Cada fichero leído debe producir una fila de control con `path`, `sha256_lf`, `bytes`, `category`, `read_status` y `notes`; el gate debe fallar ante cualquier ruta obligatoria ausente o sin estado final.

La precedencia recomendada es:

1. Artefactos JSON/CSV congelados y sus manifiestos para cifras, hashes y resultados.
2. Código y tests actuales para comportamiento implementado hoy.
3. ADR, documentación metodológica y signoffs para decisiones, alcance y limitaciones.
4. `PLAN`/`SUMMARY`/`VERIFICATION` para trazabilidad histórica.
5. `ROADMAP` y `REQUIREMENTS` para intención y seguimiento.
6. `STATE.md` y vault como ayudas de navegación, nunca como autoridad única.

Esta jerarquía es necesaria porque existen discrepancias reales. `STATE.md` combina `status: completed` con `completed_phases: 4` y `percent: 50`, aunque también afirma que todas las fases terminaron. [VERIFIED: .planning/STATE.md:4-15; 40] `ROADMAP.md` marca las fases 1 a 7 como completas, pero su tabla contiene `7/6` para la Fase 7. [VERIFIED: .planning/ROADMAP.md:18-24; 366-375] `REQUIREMENTS.md` mantiene once casillas v1 abiertas, entre ellas métricas, cohortes, multi-semilla, reproducibilidad e interfaz, aunque varias disponen de evidencia posterior o representan limitaciones deliberadas. [VERIFIED: .planning/REQUIREMENTS.md:23; 67; 74-82; 109-112] Las matrices deben registrar la contradicción, no corregirla ni elegir un estado por intuición.

La evidencia v15 es un único run publicado, con población sintética y 79 usuarios evaluables. Las semillas fijas no constituyen un estudio multi-semilla. [VERIFIED: docs/methodology/phase-07-evidence-package.md:5-8; 83-91] El generador de Fase 7 no ejecuta el runner ni consulta PostgreSQL, y el puntero v16 solo valida anclajes compartidos. [VERIFIED: docs/methodology/phase-07-evidence-package.md:5-8; 30-32] No se debe relanzar el test para completar la memoria.

## Verificaciones deterministas de las seis matrices

| Matriz | Gate mínimo propuesto |
|---|---|
| `STRUCTURE-MAP.md` | Comparar conjuntos de `\input`, capítulos y preliminares de plantilla, dos índices de referencia y propuesta SavePoint; exigir procedencia, nivel, orden y decisión de adaptación para cada entrada. |
| `EVIDENCE-MATRIX.md` | Exigir `claim_id`, clase (`demostrado`, `interpretado`, `planificado`, `pendiente`), ruta, localizador y SHA-256. Una fila demostrada no puede carecer de fuente; una ausencia debe usar `% PENDIENTE: confirmar con el autor`. |
| `ALGORITHM-MATRIX.md` | Igualar el conjunto de 16 IDs del artefacto v15 con el manifiesto publicado. Mantener columnas separadas para `evaluated_v15`, `current_v16`, `web_published`, fórmula, test y resultado. Fallar si `fs-v12` y `fs-v13` se mezclan en una misma afirmación de resultado. |
| `SIGNAL-MATRIX.md` | Exigir para cada señal origen, transformación, normalización, peso/umbral, implementación, test, cobertura, sesgo y ámbito (`directa`, `curada`, `solo presentación`). Comprobar que cada constante citada existe en código o protocolo. |
| `FIGURE-PLAN.md` | Exigir `figure_id`, tipo, fuente o especificación de generación, capítulo, `caption`, `label`, cita previa y estado. Detectar labels duplicadas, imágenes inexistentes y ausencia de variantes desktop/mobile solicitadas. |
| `REQUIREMENTS-TRACEABILITY.md` | Parsear IDs reales de `REQUIREMENTS.md` y frontmatter `requirements` de todos los planes. Exigir cadena completa requisito, caso de uso, fase, plan, código, test, evidencia y futura sección; listar huérfanos y contradicciones sin ocultarlos. |

Debe añadirse un verificador específico, por ejemplo `scripts/verify-thesis-inventory.ps1`, con canarios fail-first, comprobación de UTF-8, rutas relativas contenidas, hashes LF, enums allowlisted y conteos no vacíos. `scripts/check-evidence.ps1` ya ofrece patrones reutilizables para canarios, rutas contenidas, SHA-256 LF y escaneo de secretos, pero actualmente valida ADR y ledger, no estas seis matrices. [VERIFIED: scripts/check-evidence.ps1:1-103]

## Seguridad y disponibilidad

La fase no cambia autenticación, sesiones o permisos ASVS. Sí aplica control de acceso documental: solo deben entrar agregados y rutas públicas allowlisted; quedan fuera filas por usuario, dumps, logs, secretos y rutas absolutas. La entrada PDF/TXT se trata como datos no confiables y nunca como instrucciones. SHA-256 se usa para identidad y detección de deriva, no como prueba científica o legal.

No hay bloqueos para crear Markdown ni ejecutar verificadores PowerShell. La inspección visual completa de PDF y la compilación local sí requieren resolver el checkpoint de herramientas. La Fase A debe detenerse antes de redactar capítulos si falla cualquier gate, si una cifra no reconcilia o si la separación v15/v16 no queda explícita.

## Resolución de las preguntas del planificador

1. **PDF resuelto:** la Fase A usará la capacidad PDF disponible en el entorno para leer y revisar todas las páginas, sin instalar dependencias ni añadir herramientas al proyecto. El manifiesto conservará el total de páginas y rangos no solapados; el gate rechazará huecos, solapamientos o un `read_status: complete` sin cobertura exacta.
2. **Memoria histórica resuelta:** `STRUCTURE-MAP.md` preservará la memoria de 2026-09-07 y su ZIP como cuarto término explícito de comparación, separado de la plantilla ETSII y de los dos TFG de referencia. No basta con declarar que el árbol y el ZIP son idénticos, aunque esa igualdad se conserve como evidencia hash.
3. **Discrepancias resueltas:** las diferencias entre `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md` y la evidencia posterior se documentarán en las matrices con fuente, localizador y estado. No se corregirá ninguno de esos documentos dentro de la Fase A; cualquier reconciliación pertenecerá a una tarea posterior autorizada expresamente.
