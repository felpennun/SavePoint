# Memoria del TFG SavePoint (LaTeX)

Proyecto LaTeX de la memoria del Trabajo Fin de Grado de SavePoint. Parte de la plantilla
oficial de TFG de la Escuela Técnica Superior de Ingeniería Informática de la Universidad de
Sevilla.

## Compilación

```sh
latexmk -pdf TFG.tex
```

Alternativa sin `latexmk`:

```sh
pdflatex TFG.tex
bibtex TFG
pdflatex TFG.tex
pdflatex TFG.tex
```

### Dependencias

Se necesita una distribución TeX completa: **TeX Live** (`texlive-full` o, como mínimo, los
paquetes `babel-spanish`, `mathpazo`, `natbib`, `hyperref`, `listings`, `inconsolata`,
`float`, `caption`, `geometry`, `graphicx`, `subfigure`, `tocbibind`, `todonotes`,
`titlesec`, `tocbasic`, `csquotes`, `eurosym`) o **MiKTeX**. También compila en **Overleaf**
seleccionando el motor pdfLaTeX y el compilador `latexmk`.

En esta máquina de desarrollo no hay `latexmk` ni `pdflatex` instalados, de modo que el PDF
no se ha generado localmente. Para compilar con Docker:

```sh
docker run --rm -v "$PWD":/w -w /w texlive/texlive:latest latexmk -pdf TFG.tex
```

## Estructura

- `TFG.tex`: fichero maestro con los datos de portada y el orden de capítulos.
- `etc/pkgs.tex`, `etc/style.tex`: paquetes y estilos de la plantilla, sin cambios de fondo.
- `sections/`: portada, material preliminar y los diez capítulos.
- `figures/`: figuras y capturas de la aplicación.
- `tables/`: tablas nativas incluidas con `\input`.
- `code/`: extractos de código incluidos con `\lstinputlisting` (heredados de la plantilla).
- `bibliografia.bib`: referencias en formato BibTeX.

## Artefactos que no se versionan

El PDF y los ficheros auxiliares de LaTeX (`*.aux`, `*.log`, `*.pdf`, `*.toc`, `*.bbl`,
etc.) están en `.gitignore`. Sí se versionan las fuentes `.tex`, `.bib` y las figuras.

## Pendientes del autor

Esta es la versión inicial de la memoria. Los puntos siguientes quedan marcados en el
documento con `\todo[inline]` y necesitan la intervención del autor antes de la entrega:

1. **Dedicatoria.** `\setDedication` en `TFG.tex` y el `\todo` de `sections/00_portada.tex`.
   Ahora mismo lleva el texto provisional «Por redactar.».
2. **Agradecimientos.** `sections/00_agradecimientos.tex`, con un `\todo` de marcador.
3. **Diagrama de Gantt o línea de tiempo** con las fechas reales de inicio y fin de cada
   fase, en `sections/03_planificacion_metodologia.tex` (Sección de planificación temporal).
4. **Presupuesto.** Consolidar el registro de horas por bloque y una tarifa de referencia
   citada para completar la Tabla `tab:presupuesto`, en
   `sections/03_planificacion_metodologia.tex`.
5. **Compilar en Overleaf** (motor pdfLaTeX, compilador `latexmk`) y revisar el PDF: saltos
   de página de las figuras, desbordes de tablas anchas, y que la bibliografía resuelve
   todas las citas.
6. **Repaso de cifras y fechas.** Toda cifra de la memoria procede de la evidencia del
   repositorio; conviene un último cotejo contra `docs/verification/` y `.planning/`.
7. **Informe de uso de IA.** Documento aparte, ya previsto, que no forma parte de esta
   memoria.
