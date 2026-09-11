---
tags: [fase/futuro, tema/evaluacion, decision-pendiente]
---

# Siguiente estudio — 20 usuarios reales, evaluación de calidad por encuestas

Decisión del autor (2026-09-11), anotada para evaluar en una fase posterior — **todavía no
planificada ni comprometida en `.planning/ROADMAP.md`**. Este estudio cierra el ciclo de
evaluación offline sobre población sintética
([[2026-09-11 - Evaluación offline final protocolo 12 (400 usuarios, test)]],
protocolo v14) y lo sustituye por un estudio con usuarios reales.

## Qué se hará

1. **20 usuarios reales** crean cuenta y construyen su propia biblioteca en SavePoint (juegos
   que realmente poseen/han jugado, con su propio estado y rating) — no bibliotecas
   sintéticas generadas por semilla.
2. El equipo **recoge esos datos** de biblioteca una vez construidos.
3. **Evaluación final mediante encuestas**: se pregunta a los propios 20 usuarios por la
   calidad percibida de las recomendaciones que reciben — satisfacción subjetiva, no una
   métrica de ranking automática.
4. En paralelo, se **prueban los algoritmos offline** (el mismo harness de 16 algoritmos)
   sobre esas 20 bibliotecas reales, con el mismo mecanismo de leave-one-out ya congelado.

## Diferencias explícitas con el estudio actual (protocolo v14, 400 sintéticos)

- **El corpus será distinto** en ese momento (más reciente que el `2026.09.2` congelado
  hoy) — pero **la prueba debe usar los mismos datos para las 20 colecciones**: un único
  snapshot de corpus/rating/PopScore congelado para ese estudio, igual que se congeló
  `2026.09.2` para el actual. No se compara biblioteca contra biblioteca con snapshots
  distintos.
- **Es una evaluación de calidad, no comparativa** con los resultados del estudio actual.
  El estudio de 400 usuarios sintéticos (nDCG/precisión/recall/MAP) y este de 20 usuarios
  reales (encuestas de satisfacción) miden cosas distintas con metodologías distintas — no
  se presentan como el mismo experimento en dos escalas, sino como dos capítulos
  complementarios del TFG: uno mide precisión de ranking bajo un protocolo reproducible,
  el otro mide percepción de calidad con datos y opinión reales.

## Por qué importa mantenerlo separado del corpus congelado del TFG

Ya hubo un incidente esta sesión (obras contaminadas por una importación IGDB posterior al
freeze del snapshot `2026.09.2` —
[[2026-09-11 - Evaluación offline final protocolo 12 (400 usuarios, test)]]) que ilustra
exactamente el riesgo: si el corpus "vivo" de producción sigue avanzando (ver
[[2026-09-11 - Piso de rating externo en LOO y paralelizacion offline]], sección sobre
refrescar el catálogo por cron) mientras un estudio está en curso, los resultados dejan de
ser reproducibles. Este nuevo estudio necesitará su **propio** `protocol_version`/
`corpus_version`/snapshot congelados — nunca el mismo `2026.09.2`, y nunca un corpus que
siga cambiando a mitad del estudio.

## Pendiente de decidir en la fase correspondiente (no ahora)

- Cómo se reclutan los 20 usuarios y qué consentimiento/anonimización aplica a sus datos de
  biblioteca y respuestas de encuesta.
- Diseño exacto de la encuesta (preguntas, escala, quién la analiza).
- Si el corpus para este estudio se congela antes o después de que los 20 usuarios terminen
  de construir su biblioteca (para no dejar fuera juegos que posean pero aún no estén
  gobernados).
- Qué algoritmos concretos se prueban offline sobre estas 20 bibliotecas — presumiblemente
  el mismo catálogo de 16, pero es una decisión de esa fase, no de hoy.

Ver también `.planning/STATE.md` (tabla "Deferred Items") y `.planning/ROADMAP.md`
(nota de fase candidata, sin numerar todavía).
