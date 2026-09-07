---
status: complete
---

# Investigación breve

## Alcance

La revisión se centra en la memoria fuente de `thesis/`, en su bibliografía y en la
configuración de LaTeX. El problema visual principal está en las tablas construidas con
`tabular` y anchos fijos: con márgenes de 2,75 cm, varias especificaciones superan el ancho
de texto disponible.

## Hallazgos aplicables

- `tabularx` permite ajustar las columnas de texto al ancho real de la página. Las columnas
  de texto deben usar una columna elástica con `\raggedright` para evitar justificación
  forzada y conservar legibilidad.
- Reducir el tamaño de letra de las tablas a `\small` y ajustar `\tabcolsep` es preferible a
  `\resizebox`, que puede producir tablas demasiado pequeñas para una memoria académica.
- Las tablas largas siguen siendo flotantes. La corrección de esta tarea cubre el desborde
  horizontal; una tabla que no quepa verticalmente debe poder desplazarse mediante el
  comportamiento normal de los flotantes o dividirse en una tarea posterior si la
  compilación lo evidencia.
- La documentación primaria de IGDB confirma el límite de cuatro peticiones por segundo,
  la atribución visible, el almacenamiento local y la gratuidad para proyectos comerciales y
  no comerciales, con asociación comercial para productos monetizados.
- Los términos de RAWG permiten uso personal gratuito y determinados proyectos comerciales
  dentro de 20.000 peticiones mensuales y límites de audiencia, siempre con atribución y
  enlace; por tanto, no debe afirmarse que todo uso comercial exige un plan de pago.
- La documentación pública del método GSD se encuentra en el repositorio `gsd-build/
  get-shit-done`. La referencia anterior del `.bib` apuntaba a otro repositorio.

## Decisiones

Se conservará la estructura y el contenido honesto del borrador. Se corregirán los anchos de
las tablas, dos construcciones estilísticas señaladas por las convenciones, la precisión de
los términos de IGDB y RAWG y la URL de GSD. Los marcadores que necesitan datos personales del
autor, como dedicatoria, agradecimientos, cronograma y horas, permanecerán visibles y se
documentarán como pendientes.
