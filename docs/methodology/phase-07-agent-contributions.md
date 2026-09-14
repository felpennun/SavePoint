# Contribuciones y responsabilidades de la Fase 7

## Criterio

La clasificación sigue `docs/methodology/agent-method.md`: una propuesta no es evidencia,
un check automático prueba solo su comando y una decisión académica requiere al autor
humano. Las conversaciones, prompts completos, credenciales y logs brutos no forman parte
del paquete.

| Actor o herramienta | Tipo | Contribución | Límite |
|---|---|---|---|
| Felipe | Humano | Define alcance, revisa corpus, protocolo, licencias, cifras e interpretación y decide la presentación en el TFG. | Responsabilidad académica final; debe aprobar la redistribución. |
| `gsd-phase-researcher` | Agente | Recopila restricciones y evidencia previa para el contexto de fase. | Propone; no concede derechos ni aprueba resultados. |
| `gsd-planner` | Agente | Divide el cierre en tareas, criterios de éxito y gates trazables. | No declara completado el producto. |
| `gsd-executor` | Agente | Implementa `generate-phase-07-evidence.ps1`, proyecta agregados y redacta este paquete. | No es revisor independiente ni interpreta la superioridad académica de un algoritmo. |
| SHA-256, PowerShell y `check-evidence.ps1` | Herramientas deterministas | Verifican identidad de inputs, generación estable y contrato documental. | No prueban la verdad, calidad o legalidad de las fuentes. |

## Alcance de esta contribución

La Task 2 consumió únicamente el artefacto v15, el JSON de cohortes, el puntero de
protocolo, lockfiles, Compose y documentos versionados de procedencia/metodología. El
generador no importa el runner, no ejecuta rankings, no consulta la base de datos y no
modifica el JSON fuente. La tabla y la figura son transformaciones de presentación de
agregados ya publicados.

## Revisión requerida

Antes de incorporar las salidas a la memoria, Felipe debe revisar los hashes, la diferencia
entre población nominal y usuarios evaluables, la limitación de single-run, la licencia de
IGDB/Twitch y la equivalencia semántica entre CSV, JSON y SVG. Un PASS automático no se
convierte por sí solo en aprobación humana.
