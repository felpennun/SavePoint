---
status: human_needed
---

# Verificación de la revisión de la memoria

## Comprobaciones realizadas

- Las 22 tablas activas de `thesis/sections/` tienen un `begin` y un `end` equilibrados y
  usan `tabularx` con `\textwidth`.
- No quedan declaraciones activas con `\begin{tabular}` ni columnas `p{...cm}` en las
  tablas de los capítulos.
- Las claves empleadas por `\cite` tienen entrada en `thesis/bibliografia.bib` y no quedan
  entradas bibliográficas sin citar.
- Todas las referencias `\ref` del documento activo tienen una etiqueta definida, incluidas
  las etiquetas de los listados de código.
- No se detectan en la prosa de los capítulos usos de `, y` ni de `--` como puntuación.
- `git diff --check` no informa errores de espacios ni finales de fichero.
- El recuento de entornos principales está equilibrado: 22 tablas, 6 figuras y 3 listados.

## Resultado

La verificación estática pasa. La compilación PDF queda pendiente de comprobación humana
porque esta máquina no tiene instalados `pdflatex`, `latexmk`, `bibtex` ni `biber`, y no se ha
descargado una imagen TeX de varios gigabytes solo para esta revisión. El README conserva el
comando reproducible para Overleaf o TeX Live.

## Revisión humana pendiente

Tras compilar en Overleaf o en una instalación TeX completa, conviene comprobar visualmente
que ninguna tabla especialmente densa necesita dividirse entre páginas y que los marcadores
de `\todo` y `\missingfigure` siguen siendo aceptables para la versión de entrega. La
dedicatoria, los agradecimientos, el cronograma y el presupuesto continúan requiriendo datos
del autor.
