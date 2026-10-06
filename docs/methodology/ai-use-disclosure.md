# Declaración de uso de IA

## Declaración

SavePoint se ha desarrollado con asistencia de agentes de IA, bajo el método descrito en [`agent-method.md`](agent-method.md). La asistencia se utilizó a lo largo de todo el proyecto para investigar alternativas, proponer diseños, organizar y planificar tareas, implementar y probar código, y preparar documentación. No se guardan en el repositorio conversaciones completas, prompts, cookies, credenciales, variables de entorno ni registros sin revisar.

Se usaron Codex (familia `gpt-5`) y Claude Code (familia Claude), según la tarea. La versión exacta de un modelo no siempre la expone el entorno y, cuando falta, se anota como desconocida. Un nombre de modelo no garantiza reconstruir exactamente una salida en lenguaje natural: la parte reproducible del resultado son el código, las fuentes, las sumas de verificación, los comandos y las decisiones humanas.

## Separación de funciones

| Categoría | Qué ocurre en el proyecto | Evidencia o autoridad |
|---|---|---|
| Propuesta del agente | Diseños, hipótesis, planes y cambios candidatos de código y documentación. | Los planes, los commits y los documentos de decisión que los recogen. |
| Verificación automática | Pruebas, validadores de contrato, comprobaciones de dependencias y de secretos, y sumas de verificación que impiden cerrar una tarea si fallan. | Comandos reproducibles y su resultado para un commit concreto. |
| Decisión del autor | Alcance, aceptación o rechazo de alternativas, licencias, límites de los resultados y formato final de la memoria. | Los puntos de control, las decisiones de arquitectura (ADR) y la revisión humana; el agente no firma la evidencia académica. |

## Controles aplicados

- Las métricas se copian de artefactos publicados y congelados; no se recalculan ni se completan con estimaciones.
- La población, el protocolo, las semillas, el corpus y los snapshots se conservan con sus identidades, y las ejecuciones se comprueban contra ellas.
- Los resultados que se publican excluyen datos individuales, volcados, secretos, rutas absolutas y registros sin revisar.
- Una propuesta de un agente no es evidencia mientras no se enlace con código, una prueba, un dato inmutable o una fuente primaria.
- La diferencia entre propuesta, verificación automática y decisión humana permanece explícita; un agente no se presenta como evaluador independiente.

## Coste, reproducibilidad y límites

El uso de IA no ha introducido un coste recurrente ni un servicio de pago propio del proyecto. No se dispone de una medición estable de tokens, precio o consumo de inferencia que permita atribuir un coste monetario exacto a la asistencia, y por eso no se inventa una cifra. La metodología asistida puede reproducir controles y artefactos, pero no garantiza una reconstrucción idéntica de toda salida de lenguaje natural si cambian el entorno, el modelo o las herramientas.

La evaluación de los recomendadores es una simulación sobre usuarios sintéticos. La asistencia de la IA no convierte esa simulación en evidencia sobre usuarios reales ni sustituye la revisión de las amenazas a la validez, las licencias, la interpretación de los resultados ni el formato universitario.
