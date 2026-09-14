# Registro académico de referencias

## Propósito

Este registro identifica las referencias de TFG disponibles en el repositorio, las reglas
de formato aplicables y el estado de incorporación. Las rutas son relativas y se mantienen
como referencias canónicas; no se copian materiales externos al paquete de evidencia v15.

## Referencias disponibles

| Ruta | Tipo | Estado | Uso previsto |
|---|---|---|---|
| `thesis/referencias/plantilla-etsii/` | Plantilla oficial ETSII US y ejemplos LaTeX | Disponible e incorporada como base de formato | Estructura de la memoria, paquetes, estilo, tablas y figuras. |
| `thesis/referencias/proyecto-front.txt` | Memoria de ejemplo, portada y resumen extraídos | Disponible; material de consulta | Comparar portada, resumen, abstract, índice y organización de una memoria de software. |
| `thesis/referencias/proyecto-toc2.txt` | Índice de memoria de ejemplo | Disponible; material de consulta | Comparar jerarquía de capítulos y tablas de contenido. |
| `thesis/referencias/volcanes-front.txt` | Portada y preliminares de TFG de ejemplo | Disponible; material de consulta | Contrastar material preliminar y presentación de resultados. |
| `thesis/referencias/TFG_Predicción_De_Erupciones_Volcánicas_Mediante_Inteligencia_Artificial.pdf` | Memoria de ejemplo en PDF | Disponible; pendiente de revisión específica | Consulta académica posterior; no se afirma que haya sido incorporada al texto. |
| `thesis/referencias/proyect-final.pdf` | Memoria de ejemplo en PDF | Disponible; pendiente de revisión específica | Consulta académica posterior; no se afirma que haya sido incorporada al texto. |
| `thesis/referencias/Plantilla_TFG___ETSII_US.zip` | Copia comprimida de plantilla | Disponible; material de referencia | Comparar con la plantilla expandida, sin usarla como fuente de resultados. |

## Reglas de formato registradas

`thesis/README.md` fija `latexmk -pdf TFG.tex` como compilación preferente, contempla
pdfLaTeX/BibTeX como alternativa, exige las fuentes `.tex`, `.bib` y figuras versionadas y
excluye PDF y auxiliares de LaTeX del control de versiones. También pide revisar saltos de
página, tablas anchas y resolución de bibliografía en la entrega.

La bibliografía de la memoria se mantiene en `thesis/bibliografia.bib`. Las tablas y figuras
del paquete v15 se generan desde artefactos inmutables, pero el autor debe decidir qué
salidas incorpora finalmente a LaTeX y qué referencias cita en cada capítulo.

## Anotaciones del tutor

No se ha identificado dentro de `thesis/referencias/` ni de `thesis/README.md` un documento
separado de anotaciones del tutor asociado a este paquete. Por tanto, no se atribuye ninguna
regla a una anotación no recibida. Este estado queda pendiente de actualización cuando el
autor aporte indicaciones específicas del tutor o de la universidad.

## Relación con la evidencia v15

La plantilla y las memorias de ejemplo orientan formato, no datos ni conclusiones. La
procedencia de cifras, licencias y limitaciones permanece en el artefacto v15, el JSON de
cohortes, el protocolo y el paquete de evidencia de la Fase 7.
