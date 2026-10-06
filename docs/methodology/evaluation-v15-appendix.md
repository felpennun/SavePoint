# Adenda metodológica de la evaluación v15

## Cohortes y métricas desagregables

El artefacto v15 conserva observaciones por usuario para métricas de acierto,
diversidad intra-lista y novedad, por lo que esas magnitudes pueden agregarse por
cohorte sin volver a ejecutar los algoritmos. Las métricas que dependen del conjunto
de listas completo —cobertura de catálogo, HHI y cobertura de predicción— permanecen
globales en v15 porque no se persistieron las listas completas por usuario. Esta
decisión evita fabricar una desagregación no auditable.

## Test de un solo consumo y semillas

El test v15 es deliberadamente de un solo consumo (`test_runs: 1`). Las semillas fijas
permiten reproducir exactamente el artefacto; no permiten afirmar robustez frente a
otras poblaciones hasta realizar un estudio de sensibilidad versionado. Repetir el
test con otra semilla requiere cambiar protocolo, manifiesto y hash, y no debe hacerse
mutando el marcador del test ya consumido. Los intervalos bootstrap del artefacto
cuantifican incertidumbre dentro de la muestra pareada observada, no variación entre
semillas.

## Entorno y recursos

Desde el cierre de Fase 3, el runner paralelo captura en nuevas ejecuciones el entorno
no sensible (Python, plataforma, CPU y versiones de paquetes) y los recursos del
proceso (CPU de usuario/sistema y pico RSS), además de los tiempos ya existentes. La
captura no almacena secretos, rutas privadas, nombres de máquina ni valores de
variables de entorno. No se atribuye retroactivamente a v15 porque una medición
posterior no sería una observación histórica válida.

Esta adenda complementa [`evaluation-protocol.md`](./evaluation-protocol.md) y el
resultado citable `evaluation-results-400-test-2026-09-12-v15.md` (de `docs/verification/`, no incluido en el repositorio público).
