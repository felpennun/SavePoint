# Matriz de evidencia de SavePoint

## Función, precedencia y esquema

Esta matriz no redacta la memoria. Fija qué afirmaciones puede sostener la futura
redacción, qué debe interpretarse con cautela y qué sigue pendiente. Su precedencia es:
artefactos congelados y sus manifiestos para cifras y ejecuciones; código y pruebas para
el comportamiento vigente; ADR y documentación metodológica para decisiones; planes y
firmas para trazabilidad; y `STATE.md` o el vault solo como ayudas de navegación. El
hash de cada fuente identifica la versión leída, pero no demuestra por sí mismo calidad,
legalidad, ejecución ni validez externa.

| Campo | Uso |
| --- | --- |
| `claim_id` | Identificador estable de la afirmación. |
| `clase_epistemológica` | Solo `demostrado`, `interpretado`, `planificado` o `pendiente`. |
| `fuente`, `localizador`, `sha256` | Ruta relativa, rango o sección, e identidad fijada en `SOURCE-MANIFEST.json`. |
| `implementación`, `test`, `evidencia` | Fronteras separadas: código actual, prueba o comando, y artefacto o documento de soporte. |
| `limitación` | Impide elevar una observación a conclusión no respaldada. |
| `sección_futura` | Lugar previsto para explicarla, no una sección ya redactada. |
| `authorship_owner`, `human_responsibility`, `tool_role` | Atribución de autoría, revisión y uso instrumental de herramientas. |

## Cobertura de fuentes de esta matriz

| Dominio | Fuentes cubiertas por el manifiesto | Uso |
| --- | --- | --- |
| Planificación | `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` y los ficheros versionados de `.planning/phases/` | Intención, fases, trazabilidad y contradicciones visibles. |
| Metodología | `docs/methodology/agent-method.md`, `recommendation-algorithms.md`, `evaluation-protocol.md`, `evaluation-v15-appendix.md`, `agent-ledger.jsonl`, `phase-07-agent-contributions.md`, `phase-07-evidence-package.md`, `ai-use-disclosure.md` y `academic-reference-register.md` | Protocolo, uso de herramientas, autores de referencias y límites de la evidencia. |
| Decisiones | `docs/adr/ADR-001-architecture.md` a `ADR-009-recommendation-algorithms-and-workers.md` | Alternativas, decisión, consecuencias y reversibilidad. |
| Verificación | Todos los ficheros versionados de `docs/verification/`, incluidos signoffs, congelaciones, contratos, artefactos de evaluación y auditorías | Resultados, seguridad, procedencia, pruebas y reproducibilidad. |
| Despliegue | `docs/deployment/backup-recovery.md` y `docs/deployment/public-demo.md` | Demostración controlada, copia de seguridad y recuperación. |

La cobertura de lectura, bytes, hash, rango y estado de cada fichero está en
`thesis/SOURCE-MANIFEST.json`; esta matriz no reproduce logs, datos por usuario ni
secretos.

## Contrato de autoría y uso asistido de herramientas

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUT-01 | demostrado | Autoría | Felipe Peña Núñez es el único autor responsable del TFG. | `docs/methodology/ai-use-disclosure.md:1-15`; `df9ffcc85afc992968c0d90e6f2ebab1b7c5c9186601f0de05f4d54dd41c75ec` | No aplica. | Revisión documental. | Disclosure de uso de IA. | La declaración no reemplaza la revisión académica institucional. | Preliminares y metodología. | Felipe Peña Núñez | El autor asume análisis, diseño, implementación, revisión, validación y decisiones. | No aplica. |
| AUT-02 | demostrado | Metodología asistida | Los agentes y skills se usan bajo dirección del autor para tareas de planificación, investigación, ejecución, revisión o verificación; sus propuestas requieren revisión humana. | `docs/methodology/agent-method.md:5-60`; `893e06d711612cf7009fdd304d410ebaae66aeefccbd5df52d9751a558b0a021` | Árbol `.planning/`, commits y artefactos versionados. | Gates y revisiones descritos en el repositorio. | `agent-ledger.jsonl` y documentación metodológica. | Una traza de proceso no prueba que toda propuesta sea correcta. | Gestión y metodología. | Felipe Peña Núñez | Decisión final, aceptación, modificación o rechazo: autor. | Herramientas auxiliares, nunca coautoras, desarrolladoras ni responsables. |
| AUT-03 | demostrado | Transparencia | El disclosure exige no presentar una herramienta de IA como autora ni como responsable académica o técnica. | `docs/methodology/ai-use-disclosure.md:18-46`; hash `df9ffcc85afc992968c0d90e6f2ebab1b7c5c9186601f0de05f4d54dd41c75ec` | No aplica. | Revisión de redacción antes de entrega. | Documento de disclosure. | Debe revisarse de nuevo al cerrar la memoria. | Metodología y anexo de transparencia. | Felipe Peña Núñez | Revisión de formulaciones y responsabilidad íntegra del autor. | Descripción limitada a asistencia. |

## Afirmaciones de proyecto, decisiones y alternativas

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARC-01 | demostrado | Arquitectura | La decisión documentada adopta un monolito modular con Django y DRF, frontend Next.js y PostgreSQL. | `docs/adr/ADR-001-architecture.md:1-92`; entrada y hash en manifiesto. | `apps/api/`, `apps/web/`, `infra/`. | Suites y signoffs aplicables. | ADR-001. | La existencia de la decisión no demuestra capacidad bajo carga real. | Diseño de la solución. | Felipe Peña Núñez | El autor compara y ratifica la arquitectura. | No aplica. |
| ARC-02 | demostrado | Alternativas descartadas | Microservicios, Kafka y Kubernetes se descartan para v1 por complejidad operativa no justificada; el entrenamiento no debe ejecutarse dentro de peticiones HTTP. | `docs/adr/ADR-009-recommendation-algorithms-and-workers.md`; `docs/methodology/academic-reference-register.md:29-43`, hash `00c5ae45ee0355dddd1bb9220d1a4f7b4113022df65e78246107bfb0c997954c`. | Jobs y comandos offline. | Evidencia de arquitectura y tests asociados. | ADR-009. | Es una decisión de alcance v1, revisable ante nueva evidencia. | Diseño y alternativas descartadas. | Felipe Peña Núñez | Justificación, aprobación y futura revisión: autor. | No aplica. |
| ARC-03 | demostrado | Datos y alternativas | No se adopta una base vectorial ni evaluación contra una API viva como mecanismo experimental; se priorizan corpus y artefactos congelados. | `docs/adr/ADR-003-data-sources.md`, `ADR-006-igdb-source.md`; `docs/verification/catalogue-freeze.md`. | Importación y snapshots de catálogo. | Gates de congelación. | Congelaciones y auditorías de IGDB. | No afirma que una base vectorial sea inadecuada fuera de v1. | Datos, procedencia y diseño. | Felipe Peña Núñez | Selección de fuentes y alcance científico: autor. | No aplica. |
| ARC-04 | demostrado | Seguridad de sesión | La frontera de sesión documentada usa el mismo origen y contempla CSRF como parte del diseño. | `docs/adr/ADR-004-session-boundary.md`; `docs/verification/phase-07-admin-security.md`. | Backend y proxy del frontend. | Evidencia de seguridad del signoff. | ADR-004 y auditoría de Fase 7. | Esta fila no sustituye una auditoría externa. | Diseño de seguridad. | Felipe Peña Núñez | Revisión de amenazas y aceptación de mitigaciones: autor. | No aplica. |
| ARC-05 | demostrado | Despliegue | La paridad entre el entorno local y la demostración se documenta como decisión de despliegue. | `docs/adr/ADR-005-deployment-parity.md`; `docs/deployment/public-demo.md`. | Compose e infraestructura versionada. | Comandos y checklist de despliegue documentados. | ADR-005. | La disponibilidad pública efectiva requiere comprobación en la fecha de defensa. | Despliegue. | Felipe Peña Núñez | Despliegue y comprobación final: autor. | No aplica. |

## Evidencia experimental y reproducibilidad

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-01 | demostrado | Protocolo | El protocolo documenta candidatos comunes, exclusiones y métricas de ranking para evitar comparaciones con universos distintos. | `docs/methodology/evaluation-protocol.md:45-126`; `13204a68daf3f198e33ec925eb3131fb858ec60dc42b220d836f838557af91da`. | `apps/api/evaluation/` y `apps/api/recommendations/`. | Tests y preflight de evaluación. | Protocolo y artefactos de preflight. | La documentación no basta para afirmar resultados sin el artefacto publicado. | Metodología experimental. | Felipe Peña Núñez | Definición y revisión del protocolo: autor. | No aplica. |
| EXP-02 | demostrado | Población | La evaluación publicada v15 usa población sintética y registra 79 usuarios evaluables. | `docs/methodology/phase-07-evidence-package.md:5-8,83-93`; `dc465fb881be01217c3b177724b335e35a69fd16c95cd00641b9474e04d2d6c1`. | Generación sintética y runner offline. | Validación de población sintética. | `phase-07-evidence-manifest.json`, resultados y cohortes v15. | No representa usuarios reales ni permite generalización automática. | Metodología experimental y resultados. | Felipe Peña Núñez | Interpretación prudente de resultados: autor. | No aplica. |
| EXP-03 | demostrado | Repetición | Existe una única ejecución publicada para la evidencia v15; las semillas fijas no equivalen a un estudio multi-semilla. | `docs/methodology/evaluation-v15-appendix.md:1-32`; `f3e8e12e04c46693575ab12f09eccbf53db2b403893505300cc387133210764c`. | Runner y artefactos versionados. | No relanzar el split de prueba. | Paquete de evidencia de Fase 7. | No permite inferencia de estabilidad entre semillas. | Resultados y limitaciones. | Felipe Peña Núñez | No elevar diferencias numéricas a superioridad científica sin evidencia adicional. | No aplica. |
| EXP-04 | demostrado | Separación temporal | La publicación evaluada conserva protocolo v15; el contrato vigente puede evolucionar por separado. | `docs/methodology/evaluation-v15-appendix.md:1-32`; `docs/methodology/protocol.json:1-25`. | Protocolos y consumidores actuales. | Validaciones de anclajes compartidos. | Manifiesto de evidencia de Fase 7. | No atribuir resultados v15 a fórmulas o pesos posteriores. | Algoritmos, metodología y resultados. | Felipe Peña Núñez | Mantener separación temporal en tablas y texto: autor. | No aplica. |
| EXP-05 | interpretado | Reproducibilidad | Hashes, corpus congelado, artefactos y comandos aumentan la capacidad de repetir y auditar la ejecución publicada. | `docs/verification/catalogue-freeze.md`; `docs/methodology/phase-07-evidence-package.md:61-120`. | Snapshots, scripts y manifiestos. | Gates de evidencia. | Paquete de Fase 7. | La repetición independiente aún depende de entorno, datos permitidos y disponibilidad de dependencias. | Reproducibilidad. | Felipe Peña Núñez | Validar una repetición futura: autor. | No aplica. |

## Pruebas, seguridad y operación

Los registros de pruebas distinguen la presencia de una suite de la demostración de una
ejecución documentada. Si la fuente no fija todos los campos solicitados, se usa el
placeholder canónico y no se inventan una fecha, un conteo ni un resultado.

| test_suite_id | alcance | comando | entorno | fecha | número de pruebas | resultado | limitaciones | evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TST-BE-01 | Backend, API e integración | `% PENDIENTE: confirmar con el autor` | PostgreSQL y contenedores cuando corresponda | `% PENDIENTE: confirmar con el autor` | `% PENDIENTE: confirmar con el autor` | No inferido por mera existencia de tests. | Debe enlazar ejecución concreta, no solo código. | `docs/verification/phase-07-signoff.md`; localizador y hash en manifiesto. |
| TST-FE-01 | Frontend con Vitest | `% PENDIENTE: confirmar con el autor` | Node y frontend versionados | `% PENDIENTE: confirmar con el autor` | `% PENDIENTE: confirmar con el autor` | No inferido. | Falta consolidar artefacto de ejecución en esta matriz. | Signoffs y fuentes de `apps/web/` inventariadas. |
| TST-E2E-01 | Navegador, flujos críticos y accesibilidad | `% PENDIENTE: confirmar con el autor` | Playwright y navegador correspondiente | `% PENDIENTE: confirmar con el autor` | `% PENDIENTE: confirmar con el autor` | No inferido. | La evidencia debe identificar navegador y resultado. | `docs/verification/phase-07-launch-gate.md`; entrada del manifiesto. |
| TST-SEC-01 | Seguridad administrativa y permisos | `% PENDIENTE: confirmar con el autor` | Entorno controlado de Fase 7 | `% PENDIENTE: confirmar con el autor` | `% PENDIENTE: confirmar con el autor` | Evidencia documental disponible, conteo pendiente. | No equivale a pentest independiente. | `docs/verification/phase-07-admin-security.md`. |
| TST-OPS-01 | Backup y recuperación | `% PENDIENTE: confirmar con el autor` | Docker Compose y almacenamiento definido en el documento | `% PENDIENTE: confirmar con el autor` | `% PENDIENTE: confirmar con el autor` | No inferido. | Debe registrar una restauración ejecutada y su alcance. | `docs/deployment/backup-recovery.md`. |

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPS-01 | demostrado | Copia y recuperación | Existen instrucciones versionadas para copia de seguridad y recuperación. | `docs/deployment/backup-recovery.md`; entrada y hash en manifiesto. | `infra/` y scripts operativos aplicables. | `TST-OPS-01`. | Documento de despliegue. | No se declara aquí una restauración completada sin su artefacto. | Operación y despliegue. | Felipe Peña Núñez | Ejecución y validación de restauración: autor. | No aplica. |
| SEC-01 | interpretado | Seguridad | Las ADR y la evidencia de Fase 7 documentan controles de sesión, permisos y administración. | `docs/adr/ADR-004-session-boundary.md`; `docs/verification/phase-07-admin-security.md`. | Backend y fronteras de sesión. | `TST-SEC-01`. | ADR y signoff de seguridad. | El alcance y la profundidad de la auditoría se deben describir antes de extraer conclusiones. | Seguridad. | Felipe Peña Núñez | Evaluar cobertura y riesgos residuales: autor. | No aplica. |
| DEP-01 | demostrado | Demostración controlada | El proyecto documenta una demostración pública controlada y paridad de despliegue. | `docs/deployment/public-demo.md`; `docs/adr/ADR-005-deployment-parity.md`. | Compose, backend y frontend. | `% PENDIENTE: confirmar con el autor`. | Documentación de despliegue. | La continuidad del servicio depende del proveedor y fecha de consulta. | Despliegue. | Felipe Peña Núñez | Configuración y comprobación de la demostración: autor. | No aplica. |

## Bibliografía y fuentes académicas

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BIB-01 | demostrado | Registro bibliográfico | El repositorio mantiene un registro de referencias académicas para fundamentar la futura bibliografía. | `docs/methodology/academic-reference-register.md:1-43`; `00c5ae45ee0355dddd1bb9220d1a4f7b4113022df65e78246107bfb0c997954c`. | Futura base BibTeX. | Revisión manual de referencias. | Registro académico. | No equivale a una bibliografía ya verificada y compilada. | Estado del arte y bibliografía. | Felipe Peña Núñez | Selección, lectura y cita correcta de cada fuente: autor. | No aplica. |
| BIB-02 | pendiente | Citas definitivas | Cada referencia empleada en la memoria deberá tener entrada BibTeX verificable y relación directa con la afirmación citada. | Registro académico, `:29-43`. | `% PENDIENTE: confirmar con el autor`. | Compilación bibliográfica futura. | `% PENDIENTE: confirmar con el autor`. | La lista final no se ha cerrado en esta Fase A. | Bibliografía. | Felipe Peña Núñez | Validación de citas y estilo: autor. | No aplica. |

## GSD, agentes y Obsidian

| claim_id | clase_epistemológica | tema | afirmación acotada | fuente, localizador y sha256 | implementación | test | evidencia | limitación | sección_futura | authorship_owner | human_responsibility | tool_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MET-01 | demostrado | GSD | El método documentado organiza el trabajo mediante contexto persistente, planificación, ejecución y verificación, respaldados por artefactos versionados. | `docs/methodology/agent-method.md:10-60`; hash `893e06d711612cf7009fdd304d410ebaae66aeefccbd5df52d9751a558b0a021`. | `.planning/`, planes, resúmenes, verificaciones y commits. | Gates documentales. | Método de agentes y ledger. | El método no garantiza por sí solo corrección técnica. | Gestión y metodología. | Felipe Peña Núñez | Diseñar, dirigir y evaluar el proceso: autor. | Asistencia acotada a tareas. |
| MET-02 | demostrado | Obsidian | El vault se define como registro conceptual enlazado a fuentes canónicas, no como sustituto de documentación verificable. | `CONVENTIONS.md:43-60`; `e6967064438d7700efa054ad557eb99f71b956ca19c54a26eb58d73c237aec7c`. | `ideas-vault/`. | Revisión de enlaces y fuentes canónicas. | Política del vault. | Una nota puede quedar desactualizada respecto al repositorio. | Gestión y metodología. | Felipe Peña Núñez | Curación de notas y decisiones: autor. | Herramienta de organización del conocimiento. |
| MET-03 | interpretado | Beneficio metodológico | La trazabilidad de fases, planes, commits, pruebas y evidencias puede reducir la pérdida de contexto y facilitar la reanudación del trabajo. | `docs/methodology/agent-method.md:28-60`. | Artefactos de planificación. | Auditorías y verificaciones disponibles. | Ledger y árbol de planificación. | No se ha medido causalmente la mejora de productividad. | Gestión y metodología. | Felipe Peña Núñez | Interpretar beneficios y límites: autor. | Herramientas de apoyo bajo revisión humana. |

## Contradicciones y huecos preservados

| issue_id | clase_epistemológica | observación | fuente y localizador | tratamiento en la memoria |
| --- | --- | --- | --- | --- |
| INC-01 | demostrado | `STATE.md` declara estado completado, pero mantiene `completed_phases: 4` y `percent: 50`. | `.planning/STATE.md:4-15`; `bfd1b831cea2379fc0a7b487dd9bf7eeadcfaebed03ef8f157617dc9d155ce1f`. | No reconciliar aquí; citar la evidencia posterior concreta para cada afirmación. |
| INC-02 | demostrado | `ROADMAP.md` marca fases completadas, mientras que su resumen de Fase 7 contiene una relación `7/6`. | `.planning/ROADMAP.md:366-375`; `b369f59a53d6ba583988aa31b7d73313b63bfb5954ac11fa9737e252ab0fb9ff`. | Mantener visible hasta reconciliación autorizada. |
| INC-03 | demostrado | `REQUIREMENTS.md` conserva requisitos abiertos que pueden coexistir con evidencia posterior o con limitaciones deliberadas. | `.planning/REQUIREMENTS.md:74-112`; `45863c87424eb6baf31ffcdfb3adb8cfd20cd059cd21666a6120ce05b50ce4b4`. | No marcar cumplimiento sin cadena requisito, implementación, test y evidencia. |
| GAP-01 | pendiente | Consolidación de comandos, fechas, conteos y resultados de todas las suites de prueba. | `% PENDIENTE: confirmar con el autor`. | La siguiente matriz de pruebas deberá registrar solo ejecuciones documentadas. |
| GAP-02 | pendiente | Verificación visual pormenorizada de los PDF de referencia. | `% PENDIENTE: confirmar con el autor`. | Conservar los TXT para el índice y registrar revisión visual antes de usar ejemplos de maquetación. |
