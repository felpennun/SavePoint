---
status: complete
must_haves:
  truths:
    - "Las tablas de la memoria se ajustan al ancho de texto disponible sin depender de escalado ilegible."
    - "La prosa revisada respeta el español académico del proyecto y evita afirmaciones legales más amplias que sus fuentes."
    - "Las citas usadas tienen entrada bibliográfica y la comprobación final no deja claves huérfanas."
  artifacts:
    - "thesis/etc/pkgs.tex y thesis/etc/style.tex definen el soporte de tablas adaptables."
    - "Las tablas de thesis/sections/*.tex usan columnas adaptables y conservan caption/label."
    - "thesis/bibliografia.bib refleja las fuentes citadas y sus URL verificadas."
  key_links:
    - "Las citas de thesis/sections/02_estado_del_arte.tex apuntan a las entradas de thesis/bibliografia.bib."
    - "La configuración de tabularx usa el ancho de texto definido por geometry."
---

# Plan de revisión académica de la memoria

## Tarea 1: corregir el diseño de tablas

- **Ficheros:** `thesis/etc/pkgs.tex`, `thesis/etc/style.tex`, todas las tablas de
  `thesis/sections/01_introduccion.tex` a `thesis/sections/10_conclusiones.tex`.
- **Acción:** añadir `tabularx` y columnas auxiliares alineadas; sustituir las
  especificaciones fijas que exceden el ancho de página por tablas adaptables; conservar
  captions, labels y referencias del texto.
- **Verificación:** inspeccionar que cada `tabular` de la memoria se ha sustituido o queda
  justificado; comprobar que no existen anchos fijos cuya suma supere `\textwidth`.
- **Hecho cuando:** las tablas tienen una composición legible y no dependen de
  `\resizebox`.

## Tarea 2: revisión de prosa y bibliografía

- **Ficheros:** `thesis/sections/00_abstract.tex`, `thesis/sections/02_estado_del_arte.tex`,
  `thesis/sections/10_conclusiones.tex`, `thesis/bibliografia.bib`.
- **Acción:** eliminar construcciones estilísticas detectadas, precisar los términos de IGDB
  y RAWG según sus fuentes primarias, corregir la referencia de GSD y añadir citas oficiales
  solo donde la comparación de productos necesita respaldo directo.
- **Verificación:** extraer claves `\\cite` y compararlas con las claves BibTeX; revisar que
  no haya rayas dobles ni usos de `, y` en la prosa nueva.
- **Hecho cuando:** las afirmaciones verificables tienen una fuente adecuada y el texto
  mantiene una voz académica natural, sin presentar trabajo futuro como terminado.

## Tarea 3: validación de la fuente

- **Ficheros:** `.planning/quick/260907-gni-revisi-n-acad-mica-y-correcci-n-de-la-me/` y
  artefactos locales de compilación de `thesis/` si el compilador está disponible.
- **Acción:** ejecutar comprobaciones de estructura, referencias y marcadores; intentar la
  compilación recomendada sin instalar dependencias nuevas.
- **Verificación:** registrar el resultado, incluidos los bloqueos del entorno si no existe
  una distribución TeX local o una imagen disponible.
- **Hecho cuando:** existe un informe de verificación reproducible y el estado de Git muestra
  únicamente cambios de esta revisión.
