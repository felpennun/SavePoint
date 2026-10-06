# Protocolo de verificación manual de la Fase 1

Este protocolo complementa los checks automáticos de pytest, Vitest, Playwright y axe. Está versionado para que un revisor de la tesis pueda reproducir las mismas observaciones humanas. Nunca pegues contraseñas, cookies, DSNs, claves de API ni volcados de entorno en este documento ni en capturas.

## Cobertura automática (Plan 01-10, `e2e/a11y.spec.ts`)

Las siguientes secciones de esta checklist se ejercitan ahora automáticamente, en el commit `97d438e` y posteriores: 26 tests, todos en verde -- axe (critical/serious = 0) en homepage/login/catálogo/un detalle de juego/fuentes, ES e EN, a 375x812 y 1280x800; el recorrido completo solo con teclado (skip link → login → búsqueda → detalle → estado → colección → perfil → sign-out); sin overflow horizontal a 375px; `prefers-reduced-motion` renderiza sin error. Esto es evidencia automática generada por agente, no una confirmación humana -- según *Firma* más abajo, no cierra por sí sola las secciones de **Reflow al 400% de zoom** ni de **Pasada básica con lector de pantalla**, que requieren un humano real a un nivel de zoom real / con un lector de pantalla real. Las casillas de esas dos secciones siguen sin marcar a la espera de esa sesión humana; no las marques a partir de la salida automática.



## Cabecera de evidencia

Registra una fila por cada sesión de verificación.

| Fecha UTC | Commit de Git | Entorno/URL | Navegador y versión | SO | Revisor | Resultado |
|---|---|---|---|---|---|---|
| _pendiente_ | _pendiente_ | URL local o pública, sin credenciales | _pendiente_ | _pendiente_ | _pendiente_ | PASS / FAIL |

Para los fallos, registra solo la página, el comportamiento observable, el comportamiento esperado y una referencia a captura no sensible. Enlaza el commit que lo arregla y repite toda la sección afectada.

## Precondiciones

- Usa solo el catálogo local inmutable y los usuarios demo sintéticos.
- Verifica español e inglés de forma independiente; cambiar de locale debe preservar la ruta y la entrada de formulario.
- Ejercita homepage, login, catálogo, un detalle de juego, colección, perfil público y fuentes/metodología.
- Abre las herramientas de desarrollo solo para inspeccionar nombres de campo del DOM/red. Redacta las cookies y las cabeceras relacionadas con autorización de toda la evidencia.
- Confirma que el acceso a proveedores externos puede deshabilitarse sin perder el recorrido del catálogo.

## Recorrido solo con teclado

- [ ] El skip link es lo primero, es visible al enfocar y mueve el foco a `main`.
- [ ] El orden de tabulación sigue el orden de lectura; todo indicador de foco es visible y no queda recortado.
- [ ] Homepage → login → catálogo es alcanzable sin puntero.
- [ ] La búsqueda se envía con Enter, mueve el foco al encabezado de resultados y anuncia el conteo una vez.
- [ ] El menú móvil informa de su estado expandido, se cierra con Escape y devuelve el foco a su disparador.
- [ ] El estado puede guardarse usando la interacción nativa de teclado; el éxito se anuncia una vez.
- [ ] Se puede seleccionar y guardar una valoración de 3.5/5 sin depender del color ni de la forma de la estrella.
- [ ] Se pueden añadir dos copias distintas; formato, plataforma y edición siguen siendo comprensibles.
- [ ] La colección y el perfil público son alcanzables y el sign-out es una acción explícita.
- [ ] Los envíos de formulario fallidos preservan la entrada de usuario segura y enfocan un resumen de errores enlazado.
- [ ] Ninguna acción o información primaria está disponible solo al hacer hover.

## Reflow a 320 píxeles CSS

Fija el viewport a 320 píxeles CSS de ancho al 100% de zoom, luego visita cada página requerida en ES e EN.

- [ ] No hay scroll horizontal de página.
- [ ] Navegación, formularios, botones, tarjetas, procedencia y filas de copia siguen siendo totalmente alcanzables.
- [ ] Los controles conservan un objetivo usable de 44×44 píxeles CSS o una excepción inline documentada.
- [ ] Títulos, etiquetas traducidas, nombres de fuente, URLs y mensajes de error hacen wrap sin recortarse.
- [ ] Los marcos de portada conservan una proporción 3:4 sin desplazar el contenido adyacente.
- [ ] El orden del DOM y el orden visual coinciden; ninguna información solo-móvil reemplaza el contenido de escritorio.

## Reflow al 400% de zoom

Usa un viewport de escritorio de al menos 1280×800, fija el zoom del navegador al 400% y repite las páginas requeridas en ES e EN.

- [ ] El contenido hace reflow a una dimensión sin scroll horizontal de página.
- [ ] Los controles enfocados no quedan ocultos por elementos sticky, diálogos ni bordes del viewport.
- [ ] Los errores de formulario, las live regions, los menús y el contenido modal siguen siendo perceptibles y operables.
- [ ] El texto no se trunca, no se solapa ni se reemplaza con iconos.

## Pasada básica con lector de pantalla

Usa NVDA con Firefox/Chrome en Windows o VoiceOver con Safari en macOS. Registra la combinación en la cabecera de evidencia.

- [ ] El título de página, el idioma, un `h1`, los landmarks y el propósito de la navegación se anuncian.
- [ ] Enlaces y botones tienen nombres localizados específicos; los iconos y las imágenes de portada duplicadas no repiten ruido.
- [ ] Las etiquetas de formulario, el estado requerido, las descripciones, los errores, el estado seleccionado y la valoración numérica se anuncian.
- [ ] La carga, los conteos de resultados y los resultados de mutación se anuncian una vez sin leer toda la rejilla.
- [ ] El estado de perfil público no disponible no revela si existe una cuenta privada.
- [ ] Las fuentes/procedencia son comprensibles y los destinos de los enlaces externos son evidentes.

## Fixture hostil y revisión de privacidad

Usa `e2e/fixtures/hostile.json`; contiene solo identificadores sintéticos y cadenas hostiles.

- [ ] Todo valor `untrustedText` renderiza como texto inerte; no se crea ningún elemento, manejador de evento, estilo ni script.
- [ ] Todo valor `untrustedUrls` se rechaza; no se produce ninguna navegación, redirección, fetch al servidor ni enlace.
- [ ] El propietario A solo puede acceder a datos de copia propiedad de A; el visitante B no puede inferirlos ni mutarlos cambiando un identificador.
- [ ] El hash de dataset deliberadamente incorrecto bloquea la importación y no reporta contenido de registro en crudo.
- [ ] El DOM del perfil público, los payloads HTML/RSC, el árbol de accesibilidad y las respuestas de red no contienen ningún email, detalle de copia poseída, ID interno, nota, campo de compra, cookie ni credencial.
- [ ] Los bundles del navegador, los source maps, el historial del contenedor, los logs, las capturas y los reportes generados no contienen ningún secreto de infraestructura ni clave de proveedor.

## Observaciones visuales y de movimiento

- [ ] Los colores de token cumplen el contraste requerido y no transmiten estado por sí solos.
- [ ] La preferencia de movimiento reducido elimina todo movimiento de transición no esencial.
- [ ] Las portadas ausentes/sin licencia usan el placeholder de primera parte y preservan las fronteras de atribución.
- [ ] Español e inglés no tienen claves de traducción en crudo, estados en idioma mezclado ni recortes con aproximadamente un 30% de expansión de texto.

## Firma

La sesión pasa solo cuando todas las casillas aplicables están marcadas, los checks automáticos para el mismo commit están en verde y todo fallo ha sido corregido y re-testeado. El revisor firma con nombre/iniciales y fecha UTC; las observaciones generadas por agente deben etiquetarse como propuestas automáticas hasta que un humano las confirme.
