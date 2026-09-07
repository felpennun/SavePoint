---
type: quick-verification
status: human_needed
---

# Verificación

## Comprobaciones automáticas realizadas

- 22 entornos tabularx con 22 cierres correspondientes.
- Cero entornos tabular activos y cero declaraciones de columnas fijas.
- Cero citas sin entrada bibliográfica y cero entradas bibliográficas sin uso.
- git diff --check sin errores de contenido.

## Pendiente

No se ha compilado localmente porque TeX Live/MiKTeX no quedó instalado en Windows. La
compilación final debe ejecutarse en Overleaf con thesis/TFG.tex como documento principal,
compilador pdfLaTeX y BibTeX. Conviene revisar especialmente el log por Overfull hbox,
referencias sin resolver y páginas de tablas.
