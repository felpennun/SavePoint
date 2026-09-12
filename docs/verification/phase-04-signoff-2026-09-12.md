# Firma de cierre de la Fase 4 — colaborativo e híbrido

**Fecha:** 2026-09-12
**Autor y decisión:** Felipe — **ACEPTADA CON LIMITACIÓN METODOLÓGICA**
**Fase:** 04 — Collaborative and Hybrid Comparison

## Alcance aceptado

La fase entrega y documenta:

- el ranker colaborativo `cf-user-knn-v1`;
- el híbrido `hybrid-weighted-cf-v1`, con combinación documentada de señales de
  contenido y colaborativas;
- candidatos, exclusiones, DTOs, explicaciones y fallbacks compartidos con el
  resto del sistema;
- workers web y estanterías independientes, sin eliminar las variantes de
  contenido;
- ejecución offline por procesos con límite de concurrencia, hashes comunes,
  estados explícitos y tiempos individuales y de pared;
- documentación de teoría, formulación, parámetros, decisiones, limitaciones,
  evidencia y aportación de los agentes.

## Evidencia revisada

1. `.planning/phases/04-collaborative-and-hybrid-comparison/04-VERIFICATION.md`
   registra `482 passed`, TypeScript correcto, servicios Compose, 14 trabajos
   `succeeded` de Felipe, 13 secciones personales y 20 resultados por sección
   nueva.
2. `docs/verification/evaluation-results-400-test-2026-09-12-v15.md` registra
   la ejecución final congelada: protocolo v15, corpus `2026.09.2`, 16/16
   algoritmos y 79/80 usuarios evaluables.
3. `docs/verification/evaluation-checkpoint-400-users-2026-09-12-v15.md`
   conserva el checkpoint y la trazabilidad de entradas.
4. El runner v15 registra `max_workers=2`, `serial_tail=5`, 4.297,9 segundos
   de tiempo de pared y duraciones por algoritmo.
5. `docs/methodology/recommendation-algorithms.md` y los tres `*-SUMMARY.md`
   de la fase documentan la implementación y el razonamiento del diseño.
6. Las pruebas Playwright de recomendaciones cubren el orden renderizado y la
   ausencia de elementos de depuración; no fue necesario modificar la interfaz
   desde esta sesión.

## Limitación metodológica aceptada

El artefacto v15 es una única ejecución exitosa del split `test`, con una
semilla de evaluación. El split se consume una sola vez y no se relanza para
fabricar replicaciones post hoc. El bootstrap y los contrastes pareados aportan
incertidumbre interna del run, pero no estiman la sensibilidad entre semillas.

Por tanto, las conclusiones se presentan como comparación reproducible y
acotada de esta población sintética, corpus, protocolo y semilla. No se
presentan como estabilidad general de los algoritmos frente a otras semillas o
poblaciones. Una ampliación multi-semilla queda como trabajo posterior y deberá
crear un protocolo, población, split y artefacto nuevos.

La limitación no bloquea el cierre: el objetivo de Fase 4 — incorporar,
comparar y documentar los métodos colaborativo e híbrido bajo el contrato
común— está cubierto y su evidencia es recalculable desde los artefactos
congelados.

## Requisitos y trazabilidad

- **REC-04:** completo — `cf-user-knn-v1` implementado, probado y evaluado.
- **REC-05:** completo — `hybrid-weighted-cf-v1` implementado, probado y
  evaluado.
- **DOC-03:** completo — teoría, formulación, parámetros y limitaciones de cada
  algoritmo documentadas.

Las tres issues de los planes son #44, #45 y #46 y sus elementos están
registrados en el tablero de SavePoint. Quedan cerradas tras esta verificación.

## Decisión de cierre

Con la limitación anterior registrada de forma visible, Felipe acepta la Fase 4
como **completada con limitación metodológica** y autoriza avanzar a la
planificación de la Fase 5. La evaluación multi-semilla no se considera una
evidencia ausente accidental, sino una extensión futura delimitada.
