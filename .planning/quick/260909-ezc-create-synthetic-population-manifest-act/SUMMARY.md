---
quick_task: create-synthetic-population-manifest-active-isolation-and-signal-audit
status: complete
completed: 2026-09-09
---

# Resumen

Se completaron los tres controles previos a algoritmos.

- Se generó y verificó el manifiesto `synthetic-population-manifest-2026.09.2.json` con
  400 usuarios, 2.868 entradas, IDs de cuenta y hash
  `be3e43c451724c9c3add784394955397292d20438dc18f17c60b1984e1f4dd38`.
- Se verificó la población real: 400 activos, 200 históricos preservados, solapamiento 0,
  y split disjunto 240/80/80.
- Se auditó la cobertura sobre 190.479 obras: géneros/plataformas 100 %, desarrolladores
  53,03 %, franquicias 6,07 %, rating IGDB 14,19 %, volumen 16,08 %, recencia elegible
  14,19 % y PopScore completo 9.929 obras.
- Se documentaron las reglas de ausencia y renormalización en
  `docs/verification/recommendation-input-audit-2026-09-09.md`.
- No se ejecutó ningún algoritmo ni evaluación.
