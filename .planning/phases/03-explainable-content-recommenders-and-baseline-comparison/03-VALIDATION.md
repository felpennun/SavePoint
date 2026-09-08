---
phase: "03"
slug: "explainable-content-recommenders-and-baseline-comparison"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-08"
---

# Fase 03 — Estrategia de validación

Contrato de validación para ejecutar el harness de recomendación con artefactos reproducibles,
pruebas de seguridad metodológica y consumo web del ranking real.

## Infraestructura de pruebas

| Propiedad | Valor |
|---|---|
| Framework | pytest + pytest-django; Playwright para la superficie web |
| Configuración | `apps/api/pytest.ini`, `apps/web/playwright.config.ts` |
| Comando rápido | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/evaluation/tests apps/api/recommendations/tests -q` |
| Suite completa | `docker compose -f infra/compose.yaml run --rm api pytest apps/api -q` y `corepack pnpm --dir apps/web run test` |
| Tiempo objetivo | menos de 60 s para la suite rápida; la ejecución experimental se mide como artefacto |

## Frecuencia de muestreo

- Después de cada commit de tarea: ejecutar el comando rápido correspondiente.
- Después de cada ola: ejecutar la suite completa y una prueba determinista del runner.
- Antes de `gsd-verify-work`: backend, frontend y checks de evidencia deben estar verdes.
- Ningún comando de verificación puede quedar sin un `fails_when` observable en el PLAN que lo use.

## Mapa provisional de verificación

| Tarea prevista | Requisito | Tipo | Comprobación |
|---|---|---|---|
| Contrato v2 y snapshot | EVAL-04, EVAL-05 | integración | `pytest apps/api/evaluation/tests/test_protocol_v2.py -q` |
| Candidatos y leakage | EVAL-04, EVAL-06 | integración | `pytest apps/api/evaluation/tests/test_candidate_protocol_v2.py -q` |
| Señales, variantes y explicaciones | EVAL-05, EVAL-07 | unit/integración | `pytest apps/api/recommendations/tests/test_content_v2.py -q` |
| Métricas beyond-accuracy | EVAL-08 | unit | `pytest apps/api/evaluation/tests/test_beyond_accuracy.py -q` |
| Bootstrap y contrastes | EVAL-11 | unit | `pytest apps/api/evaluation/tests/test_statistical_comparison.py -q` |
| Runner y artefactos | EVAL-12 | integración | `pytest apps/api/evaluation/tests/test_runner_v2.py -q` |
| Rankings reales en web | QUAL-02 | Playwright | `corepack pnpm exec playwright test e2e/recommendations.spec.ts --project=chromium` |

Las rutas no existentes son entregables previstos y deben pasar por Wave 0 o crearse en la tarea
que las declara. El planner debe ajustar esta tabla si divide o renombra planes, conservando la
cobertura de todos los requisitos.

## Validaciones manuales

| Comportamiento | Requisito | Motivo | Instrucciones |
|---|---|---|---|
| Reflow a 400 % y viewport móvil | QUAL-02 | Requiere inspección visual y teclado real | Abrir recomendaciones en 320 px y con zoom 400 %, recorrer foco y confirmar que no hay overflow de página. |
| Interpretación de explicaciones | EVAL-07 | La corrección semántica final no es completamente automatizable | Revisar una muestra y confirmar que cada razón solo cita señales presentes y no afirma causalidad. |

## Requisitos de Wave 0

- Crear fixtures pequeños con usuarios, ratings, candidatos, empates, ceros y listas vacías.
- Crear un fixture de fuga que demuestre que el elemento retenido no entra en el perfil.
- Crear fixture de distribución degenerada para el fallback de bootstrap.
- Si se aprueban NumPy/SciPy, congelar las versiones y verificar instalación limpia antes de
  activar los tests estadísticos.

## Criterios de cierre

- Cada requisito EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08, EVAL-11, EVAL-12 y QUAL-02 tiene
  al menos una prueba automatizada y una evidencia de ejecución.
- Los comandos tienen rutas reales o están declarados como creación de Wave 0.
- Los casos de candidato común, fecha futura, sin rating, usuario nuevo y listas vacías están
  cubiertos sin resultados inventados.
- El artefacto final contiene semilla, corpus, protocolo, configuración, commit, hashes, métricas
  por usuario y estado válido/inválido.
- `nyquist_compliant: true` se marca solo después de ejecutar el gate de validación.

**Aprobación:** pendiente
