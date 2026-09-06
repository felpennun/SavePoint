# Prompt para redactar la versión inicial de la memoria del TFG (SavePoint)

> Este documento es el **encargo que el propio asistente ejecutará** para producir un primer
> borrador completo y compilable de la memoria del Trabajo Fin de Grado, en LaTeX, sobre el
> proyecto SavePoint. El autor lo revisa y lo aprueba antes de ejecutarlo. Al ejecutarlo,
> síguelo **a rajatabla**: las secciones 1 y 2 son restricciones no negociables.

---

## 0. Rol y objetivo

Actúa como el **autor único** de la memoria: Felipe Peña Núñez, estudiante del Grado en
Ingeniería Informática (Ingeniería del Software), ETSII, Universidad de Sevilla. Escribe en
primera persona del singular o en impersonal, como escribe un estudiante su propia memoria.

Objetivo del encargo: un **proyecto LaTeX que compile sin errores** con el esqueleto completo
de capítulos y **contenido redactado de verdad** para todo lo que ya existe en el repositorio
(Fases 1 y 01.1), y marcadores claros (`% PENDIENTE: ...`) para el trabajo de recomendadores
que corresponde a fases futuras. No es un stub. No es la memoria final. Es una primera
versión seria y honesta.

---

## 1. Reglas innegociables del autor

1. **Incluir el uso de agentes de IA y de skills.** Cómo se han usado, qué beneficios han
   aportado, qué añade el enfoque, y lo más interesante que se te ocurra al respecto. Es un
   contenido de primer nivel de la memoria, no una nota al pie. Ver el brief detallado en la
   sección 8. Debe leerse como una **aportación metodológica** observable por el tribunal,
   igual que hace la referencia BarGAIN en su capítulo 4.

2. **Lenguaje humano.** Prosa natural, explicativa, con criterio. Nada de listas telegráficas
   donde debería haber párrafos, nada de relleno, nada de tono de folleto ni de documento
   generado. Frases que un profesor reconozca como escritas por una persona que entiende lo
   que cuenta.

3. **Seguir las referencias.** Tienes tres en `thesis/referencias/`:
   - `plantilla-etsii/` — la plantilla oficial de TFG de la ETSII US. Es el formato de
     partida obligatorio (ver sección 3).
   - `TFG_Predicción_De_Erupciones_Volcánicas_...pdf` — TFG del mismo grado. Referencia para
     el **rigor de planificación y gestión** (objetivos, metodología, requisitos con
     trazabilidad, riesgos, presupuesto, desviaciones, seguimiento por iteraciones).
   - `proyect-final.pdf` (BarGAIN) — TFG del mismo grado y del mismo tipo (proyecto software
     de ciclo completo). Referencia principal para **estructura, registro y tono**, y sobre
     todo para el capítulo de metodología asistida por agentes (su §4.2: framework GSD, árbol
     `.planning/`, trazabilidad de tareas y evidencias, agentes con contrato de contexto
     explícito, registro de errores y reglas derivadas, valoración del enfoque). Toma de
     BarGAIN la **forma y el enfoque**, no la puntuación: BarGAIN abusa de las rayas `--`,
     que aquí están prohibidas (regla 2.1 del profesor).

4. **Incluir todo lo referente al repositorio y a la documentación**, siguiendo las pautas de
   las referencias. La memoria describe el repositorio como artefacto entregable: estructura,
   convenciones (`CONVENTIONS.md`), decisiones de arquitectura (los ADR), evidencia de
   verificación (`docs/verification/`), el ledger de agentes (`docs/methodology/agent-ledger.jsonl`),
   la planificación viva (`.planning/`), el stack, el despliegue. Fuentes exactas en la
   sección 6.

5. **Autoría.** No te pongas como coautor. No escribas que los commits los hizo una IA y que
   el autor solo aprobó. No repartas mérito entre autor y herramienta dentro de la memoria.
   El uso de IA se describe como **una metodología de trabajo que el autor diseñó, dirigió y
   evaluó** (igual que BarGAIN: "se gobernó mediante", "se aplicó fase a fase"), no como una
   coautoría. Existirá un **informe de uso de IA independiente y posterior** que cubre la
   transparencia de la herramienta; la memoria no lo suple ni lo contradice. El contenido de
   la memoria tiene que leerse como enteramente del autor.

---

## 2. Reglas de estilo (indicaciones del profesor, Aitor Menta)

Se aplican a **todo** el texto de la memoria. Son verificables; revísalas capítulo a capítulo.

2.1. **Nada de rayas `---` ni `--` como signo de puntuación.** Los LLM las usan mucho; el
   profesor las quiere fuera siempre. Reescribe la frase: usa comas, paréntesis, dos puntos,
   o dos frases separadas. (El guion corto `-` dentro de palabras compuestas o rangos
   numéricos sí es válido.)

2.2. **Evita la muletilla `", y"`** (coma seguida de "y" para cerrar enumeraciones y para
   encadenar cláusulas). Es otro rasgo típico de LLM que el profesor señala. Reestructura:
   enumera sin la coma antes de "y" cuando no aporta, o parte la frase, o usa otro conector.
   No sustituyas un tic por otro: varía la construcción.

2.3. **Acrónimos.** Defínelos en su **primer uso** con la forma larga seguida de la sigla
   entre paréntesis, por ejemplo "aprendizaje automático (ML)", y a partir de ahí usa solo la
   sigla. **Nunca** uses una sigla sin haberla definido antes en el cuerpo del texto. En el
   **resumen y el abstract normalmente no se usan acrónimos**: escribe las formas largas.
   Mantén además una sección de **Acrónimos** en el material preliminar (BarGAIN la tiene),
   generada de forma consistente con las definiciones del texto.

2.4. **Referencia siempre las figuras, tablas y extractos de código en el texto**, antes de
   que aparezcan, con su número y su `\ref`. Ejemplo: "como se puede ver en la Tabla
   \ref{tab:requisitos-cat}". Toda figura, tabla y listado lleva `\caption` y `\label`, y
   ninguno queda "suelto": si un elemento no se cita en el texto, o se cita o se quita. Deja
   que LaTeX coloque los flotantes donde quepan; el texto no debe decir "la siguiente tabla"
   ni "la tabla de abajo".

2.5. Coherentes con 2.1 y 2.2, cuida también: sin negritas decorativas a mitad de frase, sin
   emojis, sin encabezados con dos puntos y coletilla, sin "en resumen" / "en conclusión" en
   cada cierre de sección. Voz activa cuando sea natural. Términos técnicos en inglés en
   `\texttt{}` o en cursiva la primera vez, con su traducción si existe y es habitual.

---

## 3. Formato y plantilla LaTeX

### 3.1. Punto de partida

Copia la plantilla de `thesis/referencias/plantilla-etsii/` a `thesis/` (raíz del proyecto
LaTeX). Conserva **sin cambios de fondo**:

- `\documentclass[12pt]{report}` y el `\input{etc/pkgs}` + `\input{etc/style}`.
- `etc/pkgs.tex`: babel `[spanish,es-tabla]`, `mathpazo` (Palatino), `natbib [square,numbers]`,
  `hyperref` con `colorlinks`, `listings`, `inconsolata`, `float`, `caption [labelfont=bf]`,
  `geometry`, `graphicx`, `subfigure`, `tocbibind`, `todonotes`.
- `etc/style.tex`: márgenes A4 2.75 cm, `tocdepth 2`, guionado desactivado
  (`\hyphenpenalty=10000`), `\parindent .75cm`, el estilo `listingstyle` para `lstlisting`,
  `\renewcommand{\lstlistingname}{Extracto de código}`, los comandos `\setTitle`,
  `\setAuthor`, etc. para la portada.
- `sections/00_portada.tex` y su mecanismo de variables. Datos confirmados por el autor
  (2026-09); rellena en `TFG.tex` exactamente así:
  - `\setTitle{SavePoint: una plataforma de catalogación de videojuegos como banco de pruebas de algoritmos de recomendación}`
  - `\setAuthor{Felipe Peña Núñez}`
  - `\setDegree{Grado en Ingeniería Informática - Ingeniería del Software}`
  - `\setSupervisor{José Enrique Sánchez López \\ Aitor Rodríguez Dueñas}`
  - `\setDepartment{Lenguajes y Sistemas Informáticos}`
  - `\setMonth{...}` y `\setYear{...}` → `% TODO: convocatoria` (pendiente del autor: mes
    junio / julio / diciembre y curso, p. ej. 2026/27).
  - `\setDedication{...}` opcional; pendiente del autor. Si no lo da, comenta la línea.
  - Universidad: Universidad de Sevilla, ETSII.
- El orden de material preliminar de la plantilla: portada, agradecimientos, resumen
  (palabras clave), abstract (keywords), y luego `\tableofcontents`, `\listoffigures`,
  `\listoftables`, `\lstlistoflistings`.

### 3.2. Añadidos permitidos

- **Sección de Acrónimos** en el material preliminar. Usa el paquete `acro` (o
  `glossaries` con `\printacronyms`). Añade el `\usepackage` a `etc/pkgs.tex` con un
  comentario que explique por qué. Define cada acrónimo una vez y referencia con `\ac{}`.
- Puedes **reestructurar el conjunto de capítulos** (los de la plantilla son de ejemplo;
  BarGAIN también usa los suyos). Mantén el resto de la plantilla intacto.
- `bibliografia.bib` con entradas reales (ver 6.4). `\bibliographystyle{unsrtnat}`.
- Borra `sections/ejemplos_borrame.tex` y su `\input`. Borra `sections/00_abstract.tex`
  placeholder solo si lo sustituyes por el tuyo.

### 3.3. Compilación

El proyecto debe compilar limpio con `latexmk -pdf TFG.tex` (o `pdflatex` x2 + `bibtex`).
Añade un `thesis/README.md` corto con el comando de build y las dependencias
(`texlive-full` o el subconjunto). El PDF resultante no se commitea (añade `thesis/*.pdf`,
`thesis/*.aux`, etc. a `.gitignore`). Sí se commitean todas las fuentes `.tex`, `.bib`,
`figures/`, `tables/`, `code/`.

### 3.4. Figuras y datos

- Las capturas de la aplicación ya existen en `e2e/artifacts/review-2026-09-06/` y
  `e2e/artifacts/phase-01.1/`. Cópialas a `thesis/figures/` con nombres estables y
  reféncialas (regla 2.4).
- Diagramas (arquitectura, modelo de datos, flujo GSD, casos de uso): créalos como
  `figures/*.pdf` o `figures/*.png`. Si no puedes generarlos ahora, deja un
  `% PENDIENTE: figura de <X>` **y** un `\missingfigure{}` de `todonotes` con descripción,
  nunca una figura vacía sin marcar.
- Tablas de requisitos, trazabilidad, ADR, métricas de verificación: constrúyelas con datos
  **reales** del repositorio (sección 6). Formato de tabla como `tables/tabla_ejemplo.tex`.

---

## 4. Cómo usar cada referencia

| Referencia | Qué tomar | Qué NO tomar |
|---|---|---|
| Plantilla ETSII US | Formato, paquetes, estilo, portada, material preliminar, índices | — |
| TFG Volcanes | Rigor de **Planificación/Gestión**: objetivos, metodología, requisitos (información / funcionales / no funcionales / reglas de negocio / casos de uso / matriz de trazabilidad), planificación temporal e hitos, estimación de costes y presupuesto, gestión de riesgos y calidad, seguimiento por iteraciones, desviaciones | Su carga PMBOK excesiva si no aporta; adáptalo a un proyecto dirigido por fases GSD |
| TFG BarGAIN | **Estructura de capítulos** de un proyecto software de ciclo completo; el **capítulo de metodología asistida por agentes** (§4.2) como plantilla de contenido para la sección 8 de este prompt; tono de resumen/abstract (prosa humana, sin siglas); el marco de "el proceso es también objeto de estudio del TFG" | La puntuación (rayas `--`), que aquí está prohibida (regla 2.1) |

Lee las tres antes de escribir. Cita explícitamente en la memoria las fuentes bibliográficas
reales que uses (GSD, Django, IGDB, etc.), no las tesis de ejemplo.

---

## 5. Estructura de capítulos propuesta

Adáptala al proyecto SavePoint. Cada capítulo abre con un párrafo de introducción y cierra
con un párrafo de conclusiones del capítulo (como en ambas referencias). Numeración de la
plantilla.

1. **Introducción y objetivos**
   Contexto y motivación (catalogación de colecciones de videojuegos; el hueco de un banco
   de pruebas reproducible para recomendadores en un TFG). Problema abordado. Objetivo
   general. Objetivos específicos. Alcance de esta primera entrega (Fases 1 y 01.1) y de las
   fases futuras (2 a 8). Tecnologías clave. Estructura de la memoria.

2. **Antecedentes y estado del arte**
   Productos de referencia (Goodreads, Letterboxd, Backloggd, OpenCritic, Steam, IGDB.com).
   Fuentes de datos de videojuegos y sus términos (Wikidata, IGDB, RAWG). Panorama de
   sistemas de recomendación (basados en contenido, colaborativos, híbridos) y de la
   evaluación reproducible de recomendadores, a nivel de encuadre. Metodologías de desarrollo
   asistido por agentes de código. Aportación diferencial del TFG.

3. **Planificación y metodología de trabajo**
   Objetivos de gestión. Metodología: el ciclo por fases (discutir, planificar, ejecutar,
   verificar) sobre el método GSD. **Planificación viva: el árbol `.planning/`.** Trazabilidad
   de tareas, requisitos y evidencias (issues por plan, `SUMMARY`, `agent-ledger.jsonl`).
   **Agentes de IA y skills** (remite a la sección 8; es el núcleo del capítulo). Registro de
   incidencias y decisiones (memoria persistente, `deferred-items.md`, ADR). Planificación
   temporal por fases e hitos. Estimación de esfuerzo y presupuesto. Riesgos y mitigaciones.
   Desviaciones y replanificación (por ejemplo la Fase 01.1 insertada a petición del autor
   tras la Fase 1). Convención de commits y de idioma (`CONVENTIONS.md`).

4. **Análisis de requisitos**
   Actores del sistema. Requisitos de información (modelo de dominio: obra, edición, copia,
   entrada de biblioteca, valoración, cuenta simulada, procedencia). Requisitos funcionales.
   Requisitos no funcionales (reproducibilidad, legalidad y procedencia de datos,
   accesibilidad y diseño responsive, seguridad de la demo controlada). Reglas de negocio.
   Casos de uso. Matriz de trazabilidad requisito a fase a evidencia (datos reales de
   `REQUIREMENTS.md` y `01.1-VERIFICATION.md`).

5. **Diseño de la solución**
   Arquitectura (monolito modular Django/DRF + frontend Next.js + PostgreSQL; jobs de
   experimentación fuera de la petición HTTP). Decisiones de arquitectura: resume cada ADR
   (001 a 007) con su contexto, decisión y consecuencias, y refiérelos. Modelo de datos.
   Diseño de la API. Diseño de la interfaz (sistema de tokens, tema claro/oscuro, componentes,
   contrato de la UI-SPEC). Proxy same-origin y modelo de sesión/CSRF. Frontera de la demo
   controlada.

6. **Datos: adquisición, licencias y procedencia**
   El corpus congelado de la Fase 1 (Wikidata, CC0, revisión por asset de Commons). La
   importación a escala real de IGDB (ADR-006): comparación DATA-04, frontera
   `game_type = 0`, cursor de id reanudable, entrega de portadas por hotlink, términos de
   Twitch/IGDB y su reconciliación. Evidencia de congelación (checksums, cobertura agregada,
   manifiesto muestreado). Registro de legitimidad de dependencias.

7. **Implementación**
   Herramientas y entorno reproducible (Docker Compose, `uv`, `pnpm`, versiones fijadas).
   Backend: comandos de gestión (importadores, `bootstrap_demo_accounts`, `seed_demo`),
   vistas y throttling, el heurístico `rank_genre_taste_v1` y su frontera respecto al trabajo
   de recomendadores de fases futuras. Frontend: rutas, componentes, i18n español/inglés.
   Extractos de código representativos con `lstlisting` (referenciados, regla 2.4).

8. **Pruebas y verificación**
   Estrategia: pruebas unitarias e integración con PostgreSQL real, `pytest` y `vitest`,
   Playwright y `axe` para accesibilidad, smoke de despliegue. Gates de evidencia
   (`check-secrets.ps1`, `check-evidence.ps1`, `check-dependencies.ps1`, `verify-igdb-*.ps1`).
   Verificación de objetivo de fase (`01.1-VERIFICATION.md`, 5/5 criterios). Revisión de
   código completa del repositorio y su remediación (16 hallazgos). Resultados con cifras
   reales.

9. **Despliegue**
   Topología pública aprobada (Vercel + Render + Neon, coste cero). Paridad con el entorno
   local. Estado actual del despliegue y decisión del autor de posponer la conexión a datos
   reales al final del proyecto.

10. **Conclusiones y trabajo futuro**
   Grado de cumplimiento de objetivos. Aportaciones (el producto; el banco de pruebas
   reproducible en construcción; la metodología asistida por agentes como objeto de estudio).
   Limitaciones honestas (pulido de diseño diferido, `total_rating` pendiente de recarga,
   despliegue no conectado). Trabajo futuro: el contrato de evaluación congelado de la Fase 2
   y la comparación de recomendadores basados en contenido, colaborativos e híbridos de las
   Fases 5 a 8, con explicabilidad y arranque en frío.

> Los capítulos 1 a 9 se redactan con contenido real. El material de recomendadores que aún
> no existe (Fases 2 a 8) se presenta como **trabajo planificado**, con marcadores
> `% PENDIENTE`, nunca como hecho.

---

## 6. Fuentes de contenido del repositorio

Lee y usa como fuente primaria (no inventes lo que no esté aquí):

### 6.1. Planificación y requisitos
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
- `.planning/phases/01-three-day-public-demo-slice/` (planes, `SUMMARY`, `01-VERIFICATION.md`)
- `.planning/phases/01.1-real-scale-catalogue-and-product-experience/` (planes 01.1-01..10,
  `SUMMARY`, `01.1-VERIFICATION.md`, `01.1-UI-SPEC.md`, `01.1-RESEARCH.md`, `01.1-CONTEXT.md`,
  `deferred-items.md`)

### 6.2. Decisiones y evidencia
- `docs/adr/ADR-001..007-*.md` (todas)
- `docs/verification/`: `phase-01-signoff.md`, `phase-01.1-signoff.md`,
  `phase-01.1-product-review.md`, `phase-01-manual.md`, `repo-review-2026-09-06.md`,
  `igdb-api-probe.md`, `igdb-catalogue-freeze.md`, `catalogue-freeze.md`,
  `dependency-legitimacy.md`
- `docs/methodology/agent-method.md`, `docs/methodology/agent-ledger.jsonl` (el ledger es
  evidencia citable del proceso: entradas de decisión humana y de comprobación automática,
  con hashes de artefacto)
- `docs/deployment/public-demo.md`
- `CONVENTIONS.md`, `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`

### 6.3. Código (para describir y para extractos)
- `apps/api/` (Django/DRF): `catalogue/`, `accounts/`, `library/`, `recommendations/`,
  `config/settings.py`, comandos de gestión, migraciones relevantes
- `apps/web/` (Next.js): `app/[locale]/`, `components/`, `i18n/`, `next.config.ts`
- `infra/compose.yaml`, `infra/render.yaml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`
- `e2e/` (Playwright), `scripts/*.ps1`
- Historial de `git log` para hitos y trazabilidad de fases

### 6.4. Bibliografía (mínimo; añade lo que uses)
GSD / Get Stuff Done (método de desarrollo dirigido por especificación para agentes);
Django y Django REST Framework; PostgreSQL; Next.js y React; IGDB API y Twitch Developer
Services Agreement; Wikidata y Wikimedia Commons; WCAG 2.2; artículos de referencia sobre
sistemas de recomendación (contenido, colaborativos, híbridos) y sobre evaluación
reproducible de recomendadores. Todas las entradas van en `bibliografia.bib` con
`\cite`/`\citep` en el texto; nada de URLs sueltas en el cuerpo.

---

## 7. Rigor y honestidad

- Afirma solo lo que el repositorio y su evidencia respaldan. Si una cifra no está medida,
  no la inventes: escribe `% PENDIENTE: medir` o preséntala como estimación y dilo.
- El trabajo de recomendadores (comparación, métricas, resultados) **no existe todavía**. En
  la memoria es trabajo futuro planificado. No presentes resultados de experimentos que no se
  han hecho.
- Los defectos conocidos van en la memoria (limitaciones, pulido diferido, `deferred-items.md`),
  no se ocultan. Las dos referencias dedican espacio a sus limitaciones.
- Coherencia de datos: los números de la memoria (312.633 obras, 5/5 criterios, 209 tests,
  etc.) deben coincidir con los de `docs/verification/`. Si algo cambió, usa el valor actual
  del repo y no un valor de una captura antigua.

---

## 8. Brief del contenido sobre agentes de IA y skills (regla 1.1)

Este es el material que el autor quiere destacado. Cúbrelo con profundidad, con lenguaje
humano, y con el marco de "aportación metodológica observable". Modelo de referencia:
BarGAIN §4.2. Puntos a tratar (amplía con lo que consideres más interesante):

- **El problema que resuelve el enfoque.** Degradación de contexto en conversaciones largas
  con un agente. La respuesta: aislamiento de contexto, tareas atómicas, cada una en una
  instancia nueva, apoyadas en ficheros de memoria persistentes.
- **El método GSD** aplicado al proyecto: el árbol `.planning/` como fuente de verdad viva
  (PROJECT, REQUIREMENTS, ROADMAP, STATE, y los pares PLAN/SUMMARY por fase). El ciclo
  discutir a planificar a ejecutar a verificar. Un issue de GitHub por plan. Los comandos
  `/gsd-*` usados de verdad (plan-phase, execute-phase, verify-work, code-review,
  resume-work).
- **Subagentes especializados** empleados: `gsd-executor` (ejecuta un plan en una copia de
  trabajo aislada, con commits atómicos), `gsd-verifier` (verificación de objetivo de fase
  independiente), `gsd-code-reviewer` (revisión de todo el repositorio con contexto propio),
  `gsd-ui-researcher` / `gsd-ui-checker` (contrato de diseño). La separación deliberada entre
  quien planifica, quien implementa y quien verifica, y por qué reproduce la separación
  desarrollo/revisión de un equipo humano.
- **Worktrees de git aislados** por ejecutor y su ciclo (crear, ejecutar, `merge --no-ff`,
  limpiar), como mecanismo de aislamiento a nivel de sistema de ficheros.
- **Skills** invocadas durante el desarrollo, versionadas junto al código, de modo que el
  entorno de trabajo del agente forma parte del entregable.
- **El contrato de contexto del repositorio**: `AGENTS.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`, `CONVENTIONS.md`. Reglas obligatorias que toda
  herramienta (Claude, Copilot, Codex) lee al empezar. La convención de idioma como ejemplo
  de regla transversal.
- **Memoria persistente y reglas derivadas.** Ficheros de memoria del agente que sobreviven
  entre sesiones. Cómo un error o una corrección del autor se convierte en una regla que se
  relee al iniciar cada tarea. Ejemplos reales del proyecto (por ejemplo la reconciliación
  de estado preexistente en `fix(01.1-02)` y en el arreglo de SC3; el bug de shell en
  Windows en los hooks).
- **El ledger de agentes** (`docs/methodology/agent-ledger.jsonl`): registro append-only con
  entradas tipadas (decisión humana, comprobación automática), actor, herramientas, hashes de
  artefacto de entrada y salida, y limitaciones declaradas. Es el rastro de auditoría del
  proceso y sirve de evidencia para el tribunal. El gate `check-evidence.ps1` lo valida.
- **Beneficios observados**, con ejemplos del proyecto: alcance bajo control a lo largo de
  varias fases; trazabilidad de cada cambio hasta su plan, su requisito y su evidencia;
  revisiones de código con contexto independiente que encontraron 16 hallazgos reales;
  capacidad de reanudar sin pérdida de hilo tras interrupciones y límites de sesión;
  reproducibilidad del proceso, no solo del producto.
- **Limitaciones y riesgos honestos**: dependencia de la calidad de la especificación
  escrita; coste de mantener la disciplina de planificación en un TFG individual; errores del
  agente que hubo que detectar y corregir (documentados); el enfoque no sustituye el juicio
  del autor sobre arquitectura, alcance y aceptación.
- **Encuadre**: el proceso de ingeniería asistido por agentes es, en este TFG, tan
  inspeccionable, auditable y reproducible por terceros como el propio producto, y esa es una
  de las aportaciones del trabajo.

---

## 9. Idioma

- Toda la memoria en **español** (convención del proyecto: `CONVENTIONS.md`).
- **Abstract** en inglés (lo pide la plantilla). Sin acrónimos (regla 2.3).
- El código de los extractos permanece en inglés (identificadores, comentarios de código).
- Términos técnicos ingleses sin traducción asentada: en cursiva la primera vez.

---

## 10. Proceso de ejecución del encargo

1. Lee las tres referencias completas y las fuentes de la sección 6.
2. Monta el proyecto LaTeX en `thesis/` a partir de la plantilla (sección 3). Consíguelo
   **compilable vacío** primero (esqueleto de capítulos, portada rellena, índices), y
   commitea ese esqueleto.
3. Redacta capítulo a capítulo, en el orden de la sección 5. Tras cada capítulo:
   - repasa contra las reglas 2.1 a 2.5 (rayas, `", y"`, acrónimos definidos, figuras y
     tablas referenciadas con `\ref`);
   - verifica que las cifras coinciden con `docs/verification/`;
   - `latexmk` compila sin errores nuevos;
   - commit del capítulo.
4. El capítulo de metodología (sección 5.3 + brief de la sección 8) recibe el mayor esfuerzo.
5. Al terminar el borrador: pasada final de estilo sobre todo el texto (reglas 2.x), genera
   `Acrónimos` de forma consistente, comprueba `\listoffigures` / `\listoftables` /
   `\lstlistoflistings`, revisa que no queda ningún flotante sin citar ni ningún
   `% PENDIENTE` sin nota `todonotes`.
6. Entrega: resumen de qué capítulos están redactados, qué queda como trabajo futuro
   marcado, y la lista de `% TODO` que necesitan un dato del autor (tutor, departamento,
   convocatoria, título definitivo).

**No empieces a ejecutar este encargo hasta que el autor lo apruebe.**
