# Elementos diferidos de la Fase 7

## Desfase histórico del ledger

- **Detectado durante:** Task 2, ejecución de `scripts/check-evidence.ps1`.
- **Problema:** el pin histórico de `docs/verification/dependency-legitimacy.md` declara
  `91144022a6dafc13fc70da84d557218c6a184cd6633140431674f3371329e408`, mientras que el
  contenido actual normalizado a LF produce `3fc98124ff3658661526f6370dbc96d719fc032360e0a123925a0709c573f2ec`.
- **Alcance:** desfase preexistente, fuera de los archivos de Task 2 y no causado por el
  generador ni por el paquete v15.
- **Acción:** no se modifica el documento histórico ni el ledger en esta tarea, porque
  corregirlo exigiría una nueva entrada append-only y una revisión independiente de la
  evidencia de dependencias.
- **Impacto:** `check-evidence.ps1` permanece en FAIL por este pin ajeno; la generación v15
  y `git diff --check` pasan. Debe resolverse antes de la gate de lanzamiento de Task 3.
