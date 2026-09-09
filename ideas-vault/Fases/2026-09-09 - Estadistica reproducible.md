# Estadística reproducible de la evaluación

Se implementó `apps/api/evaluation/statistics.py` para comparar resultados ya
calculados por usuario sin usar la estadística para seleccionar parámetros.
NumPy y SciPy ya estaban aprobados, fijados y documentados en el entorno.

El módulo ofrece configuración serializable, bootstrap pareado de la diferencia
media con semilla y fallback explícito ante intervalos degenerados, Friedman
omnibus, Wilcoxon bilateral con diferencias redondeadas y registro de ceros y
empates, y corrección step-down de Holm con desempate estable por etiqueta.
Los resultados incluyen `n`, métodos, estimaciones, intervalos, p-valores,
advertencias, configuración y hash de entrada.

La primera verificación pasa con 6 pruebas específicas y 92 pruebas de toda la
suite de evaluación. La evaluación de los 400 usuarios y sus algoritmos aún no
se ha ejecutado.

Fuentes canónicas: [[../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-03-PLAN|Plan 03-03]],
[[../../docs/methodology/evaluation-protocol|protocolo de evaluación]] y
[[../../docs/verification/dependency-legitimacy|legitimidad de dependencias]].
