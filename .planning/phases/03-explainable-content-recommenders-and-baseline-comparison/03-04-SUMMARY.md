---
phase: 03-explainable-content-recommenders-and-baseline-comparison
plan: 04
status: completed
completed: 2026-09-12
github_issue: 40
---

# Resumen 03-04 — Runner, evidencia y cierre de alcance

## Resultado

El runner paralelo y la evidencia offline quedan cerrados para el alcance
backend/investigación de la Fase 3. La ejecución final v15 ya existente se conserva
como fuente inmutable: 16 algoritmos, 79 usuarios evaluables, comparaciones
estadísticas y tiempos por worker. La evaluación no se repitió durante este cierre.

El runner queda preparado para registrar en futuras ejecuciones:

- versión de Python, plataforma, arquitectura, CPU disponible y versiones de
  Django, NumPy, SciPy, scikit-learn y pandas cuando estén instaladas;
- CPU de usuario/sistema y pico de memoria RSS por worker y por proceso padre;
- tiempos de pared, duración agregada y estado explícito de cada worker.

La captura evita secretos, rutas privadas, nombres de máquina y valores de variables
de entorno. Es evidencia de ejecución futura; no se retroproyecta sobre v15 porque
medir el entorno después de terminar no sería una observación histórica válida.

## Análisis y documentación incorporados

- Informe JSON/Markdown por cohortes derivado sin reejecución.
- Explicación de la cohorte `no_history` como cold-start descriptivo, no como
  algoritmo con puntuación cero.
- Explicación de por qué cobertura, HHI y cobertura de predicción siguen globales en
  v15: el artefacto conserva sus valores globales, pero no las listas completas
  necesarias para una atribución exacta por cohorte.
- Limitación multi-semilla documentada en los resultados, el checkpoint, la
  metodología y el vault.

## Evidencia UI/E2E del punto 7

El punto 7 queda cubierto por la evidencia producida por la otra sesión en
`e2e/recommendations.spec.ts` y registrada en el vault. Las tres pruebas Playwright
verifican el orden API/DOM y score-descendente, la ausencia de gráficos/selectores y
copy metodológico, y el comportamiento a 320 px, temas claro/oscuro y teclado.
Esta sesión no modificó `apps/web/**` ni `design/**`; solo incorpora la evidencia al
contrato documental de la fase.

## Verificación

Los tests dirigidos del código nuevo y del merge paralelo pasan (`3 passed`) y la
evidencia UI/E2E registra tres pruebas Playwright pasadas. El artefacto histórico
mantiene su hash y el marcador de test continúa consumido; no se lanzan workers
pesados ni se modifica el contrato público de recomendaciones.
