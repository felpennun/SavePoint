---
tags: [concepto, tema/metodologia, tema/seguridad]
---

# Control contra exposicion de informacion

Los artefactos de evaluacion no publican informacion personal innecesaria: la
narrativa presenta agregados, no actividad individual. Las recomendaciones
requieren autenticacion y se calculan sobre `request.user`; `ContentRecsView` y
`OwnedGamesDlcView` no aceptan un usuario objetivo y aplican allowlists de
respuesta. Los clientes de importacion aplican `redact()` y solo referencian
credenciales por nombre de variable de entorno.

## Enlaces

- [[Allowlist de campos publicos]] · [[Baseline de popularidad]] (aislamiento)
- [[Controles metodologicos AGENT-04]] · [[check-evidence]]
