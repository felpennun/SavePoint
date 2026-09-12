# Firma de la Fase 3: Recomendadores explicables y comparación de baselines

**Estado: ACEPTADA CON LIMITACIÓN METODOLÓGICA** por Felipe (autor), 2026-09-12.

La Fase 3 queda aceptada con todos sus entregables de backend, evaluación offline,
documentación, vault y evidencia UI/E2E. La limitación multi-semilla se acepta
explícitamente y no se presenta como robustez estadística: el protocolo v15 consumió
el test una sola vez (`test_runs: 1`). Una futura sensibilidad entre semillas deberá
usar un protocolo, población, split y artefacto versionados de forma independiente.

## Evidencia de cierre

| Área | Evidencia | Resultado |
|---|---|---|
| Backend y harness | `docker compose -f infra/compose.yaml exec -T api pytest /workspace/apps/api/evaluation -q` | 112 pasados |
| Evaluación final | `apps/api/evaluation-400-test-2026-09-12-v15.artifact.json` | 16/16 algoritmos, 79 usuarios evaluables |
| Cohortes | `docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.md` | 79 evaluables; `no_history` descrita como cold start |
| UI/E2E | `e2e/recommendations.spec.ts` | 3 pruebas Playwright pasadas |
| Evidencia UI/E2E | `ideas-vault/Fases/2026-09-12 - Evidencia UI-E2E de recomendaciones para el cierre de Fase 3 (QUAL-02).md` | API/DOM, ausencia de superficie metodológica, 320 px/temas/teclado |
| Integridad documental | `git diff --check` | PASS |

## Limitaciones aceptadas

- El test final v15 no se repite con varias semillas; la incertidumbre bootstrap es
  interna a la muestra pareada y no sustituye una sensibilidad entre semillas.
- El artefacto v15 conserva cobertura de catálogo, HHI y cobertura de predicción a
  nivel global, pero no listas completas por usuario; por ello esas tres métricas no
  se atribuyen artificialmente a cohortes.
- La evidencia Playwright depende de credenciales demo y de que el snapshot de
  recomendaciones alcance un estado estable; la propia prueba lo verifica mediante
  polling y deja constancia de esa precondición operativa.

## Documentos canónicos

- [`03-VALIDATION.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-VALIDATION.md)
- [`evaluation-results-400-test-2026-09-12-v15.md`](evaluation-results-400-test-2026-09-12-v15.md)
- [`evaluation-checkpoint-400-users-2026-09-12-v15.md`](evaluation-checkpoint-400-users-2026-09-12-v15.md)
- [`recommendations.spec.ts`](../../e2e/recommendations.spec.ts)
- [`03-03-SUMMARY.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-03-SUMMARY.md)
- [`03-04-SUMMARY.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-04-SUMMARY.md)

**Firma del autor:** Felipe
**Fecha:** 2026-09-12
**Commit de integración:** pendiente de integrar los cambios documentales y la
evidencia de esta sesión.
