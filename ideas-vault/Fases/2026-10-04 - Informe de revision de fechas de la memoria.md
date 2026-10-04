---
tags: [informe, memoria, fechas, planificacion]
estado: vigente
fecha: 2026-10-04
---

# Informe: revisión de las fechas de la memoria

Revisión solo de lectura. **No se ha cambiado nada en `thesis/`.** Se han contrastado todas las fechas de
`thesis/sections/*.tex` con la evidencia del repositorio: historial de git, `.planning/ROADMAP.md`, las firmas de
fase de `docs/verification/` y los ADR de `docs/adr/`.

## 1. Resumen

- Las fechas de la parte técnica (evaluación, corpus, verificación, demostración pública) **son correctas**.
- El **calendario de gestión** (capítulo 3: 2 de junio al 30 de septiembre, seis iteraciones, hitos H0 a H4 y H7) **no
  coincide con la evidencia del repositorio**, donde el proyecto arranca el 4 de septiembre y las Fases 1 a 4 se
  cierran entre el 5 y el 12 de septiembre.
- Dentro de la propia memoria hay una contradicción verificable: el hito H1 dice 12/06/2026 y la sección de despliegue dice
  que la demostración pública está en vivo "desde el 5 de septiembre de 2026".

## 2. Fechas verificadas como correctas

| Fecha en la memoria | Dónde | Evidencia |
|---|---|---|
| 5 sept 2026, sondeo autenticado de IGDB | 06 (fuentes) | Plan 01.1-01, ADR-006 con fecha 2026-09-05 |
| 5 sept 2026, demostración pública en vivo (dos veces) | 06 (despliegue) | Fase 1 completada el 2026-09-05 |
| 7 sept 2026, valores medidos de la Fase 2 | 06 (datos) | Planes 02-xx del 2026-09-07 |
| Versiones de corpus `2026.09.1` y `2026.09.2` | 06, 07 | ADR-008 (2026-09-07), artefactos de evaluación |
| Protocolo v12, 10 sept 2026 | 07 | `evaluation-400-test-2026-09-10` |
| Protocolo v14, 11 sept 2026 | 07 | `evaluation-400-test-2026-09-11` |
| Ejecución v15, `2026-09-12` | 05, 07 | `evaluation-400-test-2026-09-12-v15`, commit del 12/09 |
| H5, 12/09/2026, resultados v15 | 03 | Mismo artefacto |
| H6, 14/09/2026, flujos, amistades y endurecimiento | 03 | Fases 5 y 6 cerradas el 13/09 y la 7 el 14/09 |
| 14 sept 2026, cierre de la Fase 7 | 06 | `phase-07-launch-gate.md`, ROADMAP |
| 4 oct 2026, regresión repetida (773 y 66) | 06 | Ejecutada hoy |
| Convocatoria de octubre, curso 2025/2026 | portada, `TFG.tex` | Fijada en el commit del 06/09/2026 |

También cuadra la aritmética: del 2 de junio al 30 de septiembre son 17,1 semanas (la memoria dice diecisiete);
las horas suman 440; 440 h × 14 € = 6.160 €; cuatro meses de material e indirectos.

## 3. Discrepancias

### 3.1 El calendario de gestión frente al repositorio (alta)

El historial muestra un primer commit el 24/08/2026 ("Initial commit"), el inicio real del proyecto el 04/09/2026
(`docs: initialize project`) y 627 commits en septiembre. No hay actividad de desarrollo en junio, julio ni agosto.

| Hito en la memoria (cap. 3) | Fecha en la memoria | Evidencia en el repositorio | ¿Coincide? |
|---|---|---|---|
| H0, aprobación de la propuesta y arranque del repositorio | 02/06 | Primer commit 24/08; proyecto iniciado 04/09; ADR-001 a ADR-005 con fecha 2026-09-04 | No |
| H1, demostración pública (Fase 1) | 12/06 | Fase 1 completada 2026-09-05 (16/16 planes) | No, y contradice 06 |
| H2, catálogo a escala real e interfaz rediseñada (Fase 01.1) | 03/07 | Fase 01.1: planes del 05 al 06/09; firma el 2026-09-06 | No |
| H3, contrato de evaluación congelado (Fase 2) | 24/07 | Protocolo congelado el 2026-09-07; Fase 2 aceptada el 2026-09-08 | No |
| H4, recomendadores de contenido, colaborativo e híbrido | 14/08 | Fases 3 y 4 completadas el 2026-09-12 | No |
| H5, resultados v15 | 12/09 | 12/09 | Sí |
| H6, flujos, amistades y endurecimiento | 14/09 | 13/09 y 14/09 | Sí |
| H7, memoria completa, lista para defensa | 30/09 | Memoria con commits el 14/09, 23/09, 03/10 y 04/10 | Parcial |

Las iteraciones 1 a 4 (del 2 de junio al 14 de agosto) arrastran el mismo desfase. La Iteración 1 dice que cerró "con un
entorno de desarrollo reproducible en Docker Compose" y con las decisiones ADR-001 y ADR-002, pero esos ADR están
fechados el 04/09. La figura `calendario-iteraciones.pdf` repite estas fechas (meses de junio a octubre).

### 3.2 Contradicción interna (alta)

- Tabla de hitos, H1: "Demostración pública de tres días en producción (Fase 1) … 12/06/2026".
- Sección de despliegue: "La demostración pública está en vivo desde el 5 de septiembre de 2026".

Las dos no pueden ser ciertas a la vez.

### 3.3 Cierre de la memoria y la Iteración 6 (media)

- H7 fija la memoria completa el 30/09, y la Iteración 6 (14 al 30 de septiembre) "se dedicó por completo a la redacción".
- La propia memoria menciona después el 4 de octubre (regresión repetida) y el repositorio tiene trabajo de producto
  posterior al 14/09 (páginas de amistades, perfil, inicio, vista detallada de recomendaciones).

### 3.4 Estimación de esfuerzo (media, depende de 3.1)

Las 17 semanas × unas 25 h semanales = 440 h, el coste material y los indirectos de "4 meses" se calculan sobre el
calendario de 3.1. Si el calendario real se reduce, estas cifras tendrían que justificarse de otro modo, aunque la
memoria ya declara que es una estimación reconstruida y no un registro de horas.

## 4. Opciones (decisión del autor)

1. **Mantener el calendario como narrativa del trabajo real fuera del repositorio** (estudio previo de junio a agosto) y
   decirlo explícitamente: que el repositorio recoge desde el 4 de septiembre y que las fechas de H0 a H4 son las de
   la planificación previa. Hay que arreglar igualmente la contradicción de H1 (3.2).
2. **Alinear los hitos con la evidencia del repositorio.** Propuesta de fechas verificables:
   - H0, 04/09/2026: arranque del repositorio y ADR-001 a ADR-005.
   - H1, 05/09/2026: demostración pública (Fase 1).
   - H2, 06/09/2026: catálogo a escala real e interfaz rediseñada (Fase 01.1).
   - H3, 08/09/2026: contrato de evaluación congelado y aceptado (Fase 2).
   - H4, 12/09/2026: recomendadores y comparación completos (Fases 3 y 4).
   - H5 y H6 sin cambios (12/09 y 14/09).
   - H7, según la fecha real de cierre (después del 30/09).
   Con esta opción cambian también el número de iteraciones, la figura del calendario y la justificación de horas.
3. **Opción mixta:** conservar las seis iteraciones como agrupación lógica, pero con las fechas del repositorio en los hitos
   y una frase que explique que el trabajo se concentró entre el 4 y el 14 de septiembre.

Hace falta que decidas la opción antes de tocar la memoria, porque cambia el capítulo 3, la figura del calendario, la
frase de la Iteración 6, el presupuesto y, en menor medida, la sección de despliegue (H1).

## 5. Observaciones menores

- Hay tres formatos de fecha: `dd/mm/aaaa` en la tabla de hitos, "d de mes de aaaa" en el texto e ISO en los
  identificadores de ejecución. Es coherente por uso (tabla, prosa, identificador); no hace falta unificarlo.
- `00_agradecimientos.tex` y la portada no llevan fecha concreta, solo mes y curso. No hay fecha de depósito ni de
  defensa en la memoria.

## 6. Aplicado (2026-10-04)

El autor confirmó trabajo previo (investigación y pruebas de desarrollo) desde aproximadamente un mes antes del
arranque del repositorio de producto, y unas 225 horas de dedicación. Se aplicó una versión con fechas reales:

- Capítulo 3: hitos H0 a H7 (H0 04/08 aprox.; H1 05/09; H2 06/09; H3 08/09; H4 12/09; H5 12/09; H6 14/09; H7 04/10),
  seis iteraciones (principios de agosto a 4 de octubre), figura `calendario-iteraciones` regenerada.
- Esfuerzo: 225 h (unas 25 h semanales durante nueve semanas), reparto por bloques escalado proporcionalmente
  (30, 18, 62, 20, 46, 23 y 26 h), coste directo 3.150,00 €, material 37,50 €, indirectos 90,00 €, total 3.277,50 €.
- La sección de despliegue (cap. 6) no se ha tocado; depende de cuándo se cierre el despliegue final.
