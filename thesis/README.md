# Memoria del TFG SavePoint (LaTeX)

Proyecto LaTeX de la memoria del Trabajo Fin de Grado de SavePoint. Parte de la plantilla
oficial de TFG de la Escuela Técnica Superior de Ingeniería Informática de la Universidad de
Sevilla.

## Estado de esta revisión

La versión condensada toma sus afirmaciones de las matrices verificadas de `thesis/` y
distingue la publicación experimental v15 del contrato vigente v16. Felipe Peña Núñez es el
único autor y responsable del TFG; las herramientas asistidas forman parte de la metodología,
nunca de la autoría.

Para Prism, importar la carpeta `thesis/` completa y compilar `TFG.tex`. Antes de entregar
deben revisarse visualmente saltos de tabla, referencias, índices, figuras y avisos de LaTeX.
Esta sesión no dispone de navegador con Prism, por lo que esa comprobación visual sigue
pendiente y no se declara realizada.

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
`titlesec`, `tocbasic`, `csquotes`, `eurosym`, `array`, `tabularx`) o **MiKTeX**. También compila en **Overleaf**
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

No quedan marcadores `\todo[inline]` en el documento: el último (consolidación de la
evidencia de verificación en `sections/05_diseno_actualizado.tex`) se cerró el 2026-09-22
con las cifras reales del cierre de la Fase 7 (736 pruebas de backend, 70 de frontend, 56 de
navegador, todas en verde, 14/09/2026). Sigue sin haber intervención humana pendiente marcada
en el texto, pero antes de la entrega conviene:

1. **Compilar en Overleaf** (motor pdfLaTeX, compilador `latexmk`) y revisar el PDF: saltos
   de página de las figuras, desbordes de tablas anchas, y que la bibliografía resuelve
   todas las citas. Esta máquina de desarrollo no tiene `latexmk` ni `pdflatex` instalados,
   así que esta comprobación no se ha podido hacer localmente.
2. **Repaso final de cifras y fechas.** Toda cifra de la memoria procede de la evidencia del
   repositorio; conviene un último cotejo contra `docs/verification/` y `.planning/` antes de
   entregar, sobre todo tras cualquier cambio posterior a esta revisión.
3. **Informe de uso de IA.** Documento aparte, ya previsto, que no forma parte de esta
   memoria.
