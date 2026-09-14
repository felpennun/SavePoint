# Estado de la memoria condensada

## Contenido redactado

- Material preliminar actualizado: resumen, abstract, acrónimos e índices de la plantilla ETSII.
- Nueve capítulos activos, organizados en partes mediante `thesis/TFG.tex`.
- Capítulo central de algoritmos con representación, IDF, perfil, similitud por facetas,
  calidad bayesiana, PopScore, CF, híbrido, MMR, exclusiones y límites.
- Metodología experimental v15 con población sintética, `leave-one-out`, candidatas comunes,
  métricas y amenazas de validez.
- Tablas de resultados reales v15: los 16 algoritmos y nDCG para K=5, K=10 y K=20.
- Requisitos, diseño, implementación, verificación, despliegue y metodología GSD/Obsidian
  incluidos de forma condensada.

## Contenido demostrado e interpretado

- Las cifras experimentales remiten a `thesis/ALGORITHM-MATRIX.md` y a la publicación v15.
- La implementación vigente v16 se describe separada de los resultados v15.
- Las interpretaciones no declaran superioridad general ni representan usuarios sintéticos como
  usuarios reales.

## Pendientes de confirmación del autor

- `% PENDIENTE: confirmar con el autor` para presupuesto, esfuerzo, consolidación de ejecuciones
  de pruebas, diagramas, capturas no existentes y datos personales de agradecimientos.
- Compilación visual en Prism: saltos de página, referencias, imágenes, índices y avisos.
- Conteo final de páginas, que no puede certificarse sin compilar el PDF.

## Verificaciones realizadas en el repositorio

- `git diff --check` sin errores.
- Todas las entradas `\input{sections/...}` activas resuelven a ficheros existentes.
- No hay referencias internas rotas entre los capítulos activos.
- Las tablas añadidas usan `tabularx` con `\textwidth`; no hay columnas fijas mayores que el
  ancho de texto detectadas en la auditoría estática.

## Autoría y metodología

Felipe Peña Núñez es el único autor y responsable académico. El uso de agentes se presenta
como asistencia gobernada por el autor, con revisión humana, evidencias versionadas y decisión
final humana. El vault de Obsidian organiza enlaces y contexto, pero no reemplaza fuentes
canónicas, código, pruebas ni artefactos.
