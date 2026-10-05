---
tags: [tfg, revision, memoria, correcciones]
estado: aplicado-pendiente-de-revision-del-autor
fecha: 2026-10-05
---

# Revisión completa de la memoria (2026-10-05)

Revisión de solo lectura de `thesis/` (104 páginas, compilación sin referencias sin resolver). **No se ha modificado
nada**: este documento es la lista para que el autor decida qué se toca. Solo recoge incongruencias, errores y huecos
**dentro de la propia memoria** (nada que dependa del estado del repositorio). Las líneas son de los `.tex` actuales. Relacionado: [[2026-10-05 - Correcciones del profesor]].

## A. Contradicciones y errores de contenido (arreglar sí o sí)

| # | Dónde | Problema |
|---|---|---|
| A1 | 06:817-819 | Dice que la equivalencia con el despliegue público es "de datos", y justo después la Tabla 6.12 dice que el corpus es otro (subconjunto). |
| A2 | 03:467 (tabla de riesgos) | "Despliegue no conectado a datos reales... posponer esa conexión... la vía de demostración es el entorno local". Ya no es cierto desde el 5 de octubre. |
| A3 | 03:310-311, 339, 368-370 y figura del calendario | La iteración 6 y el hito H7 terminan el 4 de octubre, pero la memoria documenta hechos del 5 de octubre (06:477, 856, 871; tests "5-10-2026"). |
| A4 | 06:266 frente a 07 (tabla de versiones, v10) | "Rechaza una rejilla con más de 24 configuraciones" en el cap. 6 y rejilla de 31 en el cap. 7. |
| A6 | 07:62 frente a 05:290-291 | El cap. 7 llama "protocolo vigente" a v15 y el cap. 5 dice que el código vigente funciona bajo el protocolo 16. |
| A7 | 07:60 | Describe arquetipos con tamaños de biblioteca variados (incluido "veterano de biblioteca grande") y en la misma frase dice que los 390 usuarios tienen entre 10 y 20 entradas (desde v13). |
| A8 | 01:130-131 | Dice que el cap. 2 revisa "los sistemas de recomendación y su evaluación"; el cap. 2 no trata la evaluación (métricas, usuarios sintéticos). |
| A9 | 07:466-468 | La sección se titula "Diversidad, cobertura y amenazas" y no da ningún dato de diversidad, cobertura ni concentración de v15 (solo texto general). |
| A10 | 04:387 y Tabla de trazabilidad por familia | QUAL-03 consta completo (QUAL 5 de 5) y en la misma tabla se dice que 400 % de zoom y lector de pantalla están pendientes (también 06:684 y 774). |
| A11 | 04:364, 06:545 | "Enlaza cada requisito entregado con su evidencia" y "cada caso de uso, y por tanto cada requisito funcional": las tablas cubren una parte (faltan PORT, PRIV, REC-03 a REC-09, la mayoría de SEC y EVAL). |
| A12 | 06:476-477 | Frontend pasa de 70 pruebas (14 sep) a 66 (5 oct) sin explicar la bajada. |
| A13 | 05:61-62 frente a 06:12 y Tabla 6.12 | "Un worker por cada variante publicada" (3) frente a "cuatro workers en local" (señales + 3). |
| A14 | 04:204 (CU-13), 06:579 | CU-13 cita LIB-03, que no está en la tabla de requisitos funcionales. El diagrama y la tabla de casos de uso no incluyen listas, favoritos, importar/exportar ni las tres recomendaciones publicadas (solo la heurística de géneros). |
| A15 | 05:171-208 | La tabla de la API solo tiene la heurística `genre-taste`; faltan las rutas de las tres variantes publicadas, listas, comentarios y amistades. |
| A17 | 03:301-302 | Frase rota: "El corpus y los valoraciones, en la Sección..." (concordancia y frase incompleta). |
| A18 | 05:576, 06:314, 06:708-709 | "la valoración explícito"; "exactamente el misma clasificación"; "mientras se estaba desconectado" (no se entiende). |
| A20 | 00_agradecimientos | "Escuela Técnica Superior de Ingeniería" (falta "Informática"; la portada sí la lleva). |
| A21 | 05:520-544 | La tabla dice "las diez variantes de contenido" pero lista 11 entradas distintas (con `recency-v1` y las dos MMR). |

## B. Reglas de estilo del profesor y de la memoria

1. **Menciones a IA (regla: ninguna en toda la memoria):** 03:412 y 429 ("Suscripción a agentes de IA"); 03:225
   (`CLAUDE.md`, `.github/copilot-instructions.md`); 05:631 ("modelos de lenguaje"); 03:275-278 ("modelos distintos",
   "salida probabilística"); bibliografía `anthropic-context` ("Effective context engineering for AI agents", con URL
   genérica `anthropic.com/engineering`); `gsd` ("agentes de código", URL `get-shit-done` frente a "Get Stuff Done" en el
   texto); resumen y abstract ("asistida por agentes"); 02:5 ("agentes de código"); jerga de modelo ("ventana limpia",
   "límite de sesión").
2. **Coma antes de "y":** 59 casos (01: 5, 03: 7, 04: 5, 05: 21, 06: 6, resto en 07). Algunos son legítimos; el profesor
   lo marcó como tic.
3. **Raya larga "—"** en la tabla de hitos (03:325-339, 8 veces). La "--" de la Tabla 5.x de pesos es un marcador, no
   puntuación (decidir si se cambia por "n/d").
4. **Siglas:** la sección de acrónimos promete definirlas en el primer uso y no se cumple en el cuerpo para API, IGDB,
   HTTP, JSON, REST, RAWG, DTO, TFG, IDF, CSV y MMR (la forma larga está, la sigla no). ADR se usa en 03:151 antes de
   definirse en 05:78. nDCG y MAP se usan en 05:672 y se definen en 07:40-42. Sin listar: HHI, CSS, URL, UI, SHA, PC, CPU.
5. **Flotante sin citar:** `tab:req-estudio` (Tabla de requisitos de evaluación, cap. 4).
6. **Lenguaje de "fases"** (la norma era describir el sistema, no un cronograma de fases): 03:284, 327-331; 04:152, 154;
   06:156, 197, 474 y etiqueta `sec:pru-fase2`; 07:153. En el cap. 3 se explica qué es una fase; decidir si se mantiene.
7. **Anglicismos** sin cursiva ni explicación: split, snapshot, baseline, runner, test, gate, commit, worktree.
8. **Pies largos en la lista de figuras** (3.2, 4.1, 6.10): usar `\caption[corto]{largo}`.
9. Primera persona solo en "Valoración personal" y agradecimientos (intencionado).

## C. Repeticiones (el profesor ya avisó de contenido duplicado)

- "La web publica solo tres de las dieciséis variantes": 01:115, 05:62, 05:106, 05:602, 06:12, 06:308 y 06:323 (y los
  tres nombres dos veces: 05:602 y 06:323).
- Las dos numeraciones (protocolo frente a conjunto de características): 05:282-295, 07:133-135 y 08:38.
- GSD y aislamiento del contexto: resumen, 01:64, 02:42-62, 03:28-33 y 03:168-172.
- Docker, PostgreSQL y paridad de entornos: 05:50-66, 06:10 y 06:817.
- 04:217-232 repite casi literalmente la Tabla de requisitos de evaluación que viene detrás.
- "Usuarios sintéticos, no personas reales": resumen, abstract, 01 (dos veces), 07 (tres), 08. Esperable, pero se puede
  reducir.
- La evolución v12 a v15 y la defensa de v15 (07:172-280) ocupa más de 100 líneas; candidata a recortar.

## D. Huecos de cobertura

- **Cap. 2 de dos páginas**, sin trabajos relacionados sobre recomendación en videojuegos ni evaluación offline.
- **Funciones que existen y no se describen en el cuerpo:** listas, comentarios, favoritos, importación y exportación
  (PORT-01 a 04), panel de investigación (EVAL-13 y 14), notificaciones, adaptación a móvil y caché de rendimiento. La
  "Valoración personal" habla de la adaptación a móvil y el cuerpo no.
- **Resumen y abstract desequilibrados:** casi todo es recomendación y metodología; el producto web ocupa una frase y no
  aparecen el despliegue, las pruebas ni el resultado principal.
- Resumen: "400 usuarios sintéticos activos" cuando 10 son de arranque en frío; "dieciséis algoritmos de referencia"
  confunde con los baselines.

## E. Menores

- Dos desbordes de 2 a 4 pt (07:310, 06:797). La ecuación de F-beta termina en coma y empieza párrafo nuevo (05:437).
- "Fuente: captura del proyecto" repetido en ocho pies de figura.
- 03:279-280 deja un espacio final en blanco.

## F. Comprobado y correcto

Suma de pruebas por área (788), horas (310) y presupuesto (4.501,67 €), 86 de 88 requisitos, 16 hallazgos por
severidad, 54 de 120 comparaciones significativas, porcentajes de la tabla de éxitos, 35 entradas de bibliografía todas
citadas, sin etiquetas duplicadas ni referencias rotas.

## Propuesta de orden

1. A1 a A4, A6, A7, A17 y A18 (rápidos y sin discusión).
2. B1 (IA) y B4 (siglas), por ser reglas explícitas del profesor.
3. A8, A9, A10, A11 (requieren decidir qué afirmar).
4. C y D, solo lo que el autor quiera.

## Aplicado el 2026-10-06 (sin commit, a revisión del autor)

Compilaciones y diferencias en `TFG/revision-2026-10-06/`: `TFG-previa.pdf`, `TFG-posterior.pdf` (ambas de 104
páginas), `cambios.diff` y `cambios-por-palabras.diff`. Decisiones del autor: se descartan A10, A12, A20, B1 y B7 y
todo lo de D salvo resumen, abstract y "400 usuarios de prueba". Criterios que fijó: no crear secciones nuevas, añadir
a párrafos existentes, A13 y A15 con tres algoritmos, y que el cap. 2 no trate la evaluación.

- **A1 a A4, A6, A8, A9, A11, A13 a A15, A17, A18, A21:** corregidos. A3: cierre de la memoria a 6 de octubre (texto,
  tabla de hitos y figura del calendario regenerada). A9: párrafo con diversidad, cobertura y HHI de v15 tomados del
  artefacto. A13: la Tabla 6.12 pasa a tres procesos en local. A14: fila LIB-03 y nota sobre funciones posteriores a los
  casos de uso. A15: tres filas nuevas en la tabla de la API.
- **A7:** además de las bibliotecas de 10 a 20 entradas, la lista de arquetipos del cap. 7 era la de la primera población;
  se sustituye por los nueve de la población de 400 (2 sin historial, 3 iniciales, 3 normales, 1 intensivo veterano).
- **B2:** quitada la coma delante de "y" en todo el cuerpo (61 casos), con algunos punto y coma a mano.
- **B3, B5, B6, B8:** rayas largas fuera; la tabla de requisitos de evaluación ya se cita; sin lenguaje de "fases" (los
  incrementos se numeran sin cita por número); pies cortos para la lista de figuras y tablas.
- **B4:** siglas definidas en su primer uso (API, IGDB, RAWG, TFG, HTTP, JSON, REST, IDF, CSV, MMR, DTO, ADR, URL, CSS, SHA,
  SQL, HHI, nDCG, MAP); en la lista de acrónimos se añaden CSS, HHI, SHA, SQL y URL; PC, CPU, ALS, BPR y KNN se
  sustituyen por palabras.
- **C:** "tres de las dieciséis" ya solo en 1.2, ADR-009, 5.5.4 y 6.3; numeraciones protocolo/fs explicadas en 5.5 (cap. 7
  solo remite); párrafos de requisitos de evaluación del cap. 4 reducidos a una introducción de la tabla; GSD y
  aislamiento del contexto condensados en 3.3; Docker y paridad de entornos remitidos a 5.1; evolución v12 a v15
  condensada en el cap. 7.
- **D:** resumen y abstract reescritos para incluir el producto web, el despliegue, las pruebas y el resultado
  principal, y reducidos a una página; "400 usuarios activos" pasa a "usuarios de prueba".
- **E:** sin desbordes ni flotantes demasiado grandes; ecuación de F-beta cerrada con punto; "Fuente: captura del
  proyecto" quitada de ocho pies y sustituida por una frase en 6.4.
