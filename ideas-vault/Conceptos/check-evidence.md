---
tags: [concepto, tema/metodologia]
---

# check-evidence

`scripts/check-evidence.ps1`: primero prueba canaries invalidos y luego valida el
ledger real. Exige siete encabezados en espanol en cada `docs/adr/ADR-*.md`:
`## Contexto`, `## Alternativas consideradas`, `## Decision`,
`## Evidencia y fuentes`, `## Consecuencias`, `## Reversibilidad`,
`## Aprobacion y revision`. Busca patrones de credenciales y tokens, pero no
demuestra ausencia absoluta de informacion sensible.

## Enlaces

- [[Ledger de agentes]] · [[ADR (concepto)]] · [[Convenciones de idioma]]
- [[Control contra exposicion de informacion]]
