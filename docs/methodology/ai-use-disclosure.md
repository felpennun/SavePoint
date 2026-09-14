# Disclosure de uso de IA

## Declaración

SavePoint se desarrolló con asistencia de agentes bajo el método documentado en
`docs/methodology/agent-method.md`. La asistencia se utilizó para proponer diseños,
organizar tareas, implementar código y preparar documentación. No se almacenan en el
repositorio conversaciones completas, prompts, cookies, credenciales, variables de
entorno ni logs brutos.

En esta tarea el runtime disponible fue Codex y la familia de modelo se registra como
`gpt-5`; la versión exacta no fue expuesta al repositorio. Ese nombre no se presenta como
una garantía de reconstrucción exacta de lenguaje natural. La parte reproducible del
resultado son el script, las fuentes, los hashes, los comandos y las decisiones humanas.

## Separación de funciones

| Categoría | Qué ocurrió | Evidencia o autoridad |
|---|---|---|
| Propuesta del agente | Se propuso una forma allowlisted de transformar el run v15 en tabla, JSON y SVG, además de ordenar la documentación. | `07-05-PLAN.md`, commits de implementación y este disclosure. |
| Check automático | PowerShell validó SHA-256 antes de escribir y produjo salidas deterministas; `check-evidence.ps1` y `git diff --check` comprueban gates concretos. | `scripts/generate-phase-07-evidence.ps1`, salidas hash-pinned y comandos registrados. |
| Decisión del autor | Felipe debe decidir si las licencias, limitaciones, cifras y formato son adecuados para la memoria y la entrega. | Revisión humana pendiente; el agente no firma la evidencia académica. |

## Controles aplicados

- Las métricas se copian desde snapshots publicados; no se recalculan ni se completan con
  estimaciones.
- La población, el protocolo v15, las semillas, el corpus y los snapshots se conservan con
  sus identidades; el puntero v16 solo se usa para anclajes compartidos.
- Las salidas excluyen datos individuales, dumps, secretos, rutas absolutas y logs crudos.
- El generador tiene una allowlist de rutas y hashes, y falla cerrado ante deriva de bytes o
  identidad científica.
- La diferencia entre propuestas, verificación automática y decisión humana permanece
  explícita; un agente no se presenta como evaluador independiente.

## Coste, reproducibilidad y límites

El paquete no introduce coste recurrente ni un servicio de pago. No se dispone de una
medición de tokens, precio o consumo de inferencia suficientemente estable para atribuir un
coste monetario exacto a la asistencia; por ello no se inventa una cifra. La metodología
asistida puede reproducir controles y artefactos, pero no garantiza una reconstrucción
idéntica de toda salida de lenguaje natural si cambian runtime, modelo o tooling.

El resultado de evaluación sigue siendo simulación sobre usuarios sintéticos. La asistencia
de IA no convierte esa simulación en evidencia sobre usuarios reales ni sustituye la
revisión de amenazas a la validez, licencias, interpretación o formato universitario.
