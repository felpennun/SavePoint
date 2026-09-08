---
tags: [concepto, tema/metodologia]
---

# Ledger de agentes

`docs/methodology/agent-ledger.jsonl`: un objeto JSON por linea, append-only.
Campos obligatorios: `timestamp` UTC, `type`, `actor`, `objective`, `inputs`,
`outputs`, `tools`, `result`, `limitations`, `responsibility`. Cada artefacto se
referencia por `path` relativo y SHA-256 de 64 caracteres. Append-only es una
convencion auditable, no un WORM criptografico: para evidencia final hay que
firmar/taggear el commit o archivar el release con checksum.

## Enlaces

- [[Metodo de trabajo asistido por agentes]] · [[check-evidence]] · [[Convenciones de idioma]]
