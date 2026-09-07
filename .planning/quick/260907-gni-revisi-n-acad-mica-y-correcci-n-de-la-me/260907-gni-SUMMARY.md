---
status: complete
---

# Resumen

Se ha revisado la memoria LaTeX de SavePoint con un alcance centrado en presentación,
redacción y referencias.

## Cambios realizados

- Las 22 tablas activas se han convertido a `tabularx` con columnas adaptables al ancho de
  texto. Se ha añadido un ajuste común de espaciado y tamaño para conservar legibilidad.
- Se han eliminado dos construcciones de estilo detectadas por las convenciones del proyecto.
- Se han precisado las condiciones de uso de IGDB y RAWG a partir de sus páginas oficiales.
- Se han añadido referencias oficiales para Goodreads, Letterboxd y Backloggd, se han citado
  las tecnologías que ya aparecían en el texto y se ha corregido la URL de GSD.
- El presupuesto muestra ahora la ausencia de registro como dato explícito, sin presentar
  marcadores técnicos como si fueran cifras.

## Validación

La validación estática pasa para entornos, tablas, etiquetas, citas y reglas de estilo. No se
ha podido generar el PDF porque el entorno no contiene una distribución TeX. La compilación y
la inspección visual final quedan pendientes de ejecutarse en Overleaf o TeX Live.

## Estado de Git

Los cambios están guardados en el árbol de trabajo. No se ha creado commit porque el entorno
no permite escribir `.git/index`; el intento de `git add` devolvió `Permission denied` al crear
`.git/index.lock`.
