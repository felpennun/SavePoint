---
tags: [producto, privacidad, experiencia]
fecha: 2026-10-06
estado: vigente
fuente: "[[../../apps/api/library/views.py]]"
---

# Invariantes de colección y sesión

## Qué ha cambiado

- El número de copias mostrado en la colección cuenta solo las copias de la persona autenticada.
- La API expone si el juego pertenece a la colección de esa persona; la interfaz usa ese dato para ofrecer el formulario de comentario.
- La lectura de comentarios visibles no depende de pertenecer a la colección. La API sigue exigiendo pertenencia para crear comentarios.
- El login, el cierre de sesión y el registro recargan el inicio localizado. Las páginas dinámicas no se conservan en la caché de navegación del cliente, para refrescar la sesión y el juego aleatorio del inicio.
- Next.js se actualizó de 16.3.4 a 16.3.8 tras detectar una vulnerabilidad crítica en `next/og`; el escaneo completo de pnpm quedó sin vulnerabilidades conocidas.

## Impacto

Estas reglas mantienen los datos de inventario separados por propietario, hacen explícita la elegibilidad para comentar y evitan que una página dinámica reutilizada muestre el estado de sesión o el contenido aleatorio anterior.

## Resultado de seguridad — 2026-10-06

`pnpm audit` encontró inicialmente el aviso crítico GHSA-vcvr-r3jv-pc5j, que afectaba a Next.js `>=16.2.0 <16.3.6`. La aplicación no contiene importaciones de `next/og` ni `ImageResponse`, pero se actualizó igualmente a 16.3.8. El análisis OSV del lockfile Python encontró tres avisos de urllib3 duplicados como GHSA/PYSEC y afectados hasta la versión 2.8.0; `uv.lock` se actualizó de 2.7.0 a 2.8.0. Tras ambas actualizaciones, `pnpm audit` y el análisis de los 23 paquetes Python no reportan vulnerabilidades conocidas. La revisión del frontend tampoco encontró usos de `dangerouslySetInnerHTML` ni inserciones directas de HTML. La CSP actual conserva `'unsafe-inline'` para los scripts de arranque de Next; endurecerla con nonces queda como mejora separada.

## Validación manual — 2026-10-06

- Las 22 rutas directas en español e inglés devolvieron contenido válido; las rutas protegidas llevaron al login cuando no había sesión.
- En local, login y logout volvieron al inicio, el logout dejó `/api/accounts/me/` sin sesión, la validación del registro rechazó contraseñas distintas y el usuario no miembro siguió viendo la sección de comentarios sin el formulario.
- En local, la estantería de recomendaciones desplazó `scrollLeft` al recibir rueda vertical; el cambio de algoritmo y la vista detallada funcionaron. En 390 px, nueve rutas autenticadas no presentaron desbordamiento horizontal de página.
- Cinco solicitudes al inicio desplegado devolvieron `no-store` y variaron el juego destacado. El login desplegado no pudo auditarse con la cuenta demo probada (HTTP 401), así que la estantería autenticada de producción queda pendiente de una cuenta válida.
- La respuesta desplegada incluyó HSTS, CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` y `Referrer-Policy: same-origin`.

## Navegación horizontal de recomendaciones — 2026-10-06

El carril de recomendaciones ocultaba la barra nativa y dependía de convertir la rueda vertical en desplazamiento horizontal. Se añadieron botones accesibles para avanzar y retroceder por la fila, manteniendo rueda, trackpad, teclado y gestos táctiles. Para que el gesto funcione como el scroll vertical de la vista detallada, la estantería normal tiene ahora un listener nativo propio que captura la rueda sobre sus tarjetas y cambia `scrollLeft`; la vista detallada no usa ese listener y mantiene su scroll vertical. El listener delegado general excluye expresamente estas estanterías. La compilación de Next.js y el chequeo de tipos pasan. Falta confirmar el gesto interactivo en producción con una sesión válida: las credenciales demo conocidas solo sirven para local y el acceso de producción respondió 401.

El listener propio de la fila de recomendaciones no era la solución: el fallo real era el `scroll-snap-type: x proximity` de `.sp-shelf-track`. Una muesca de rueda (~100 px) es menos de media tarjeta (~107 px) y el snap devolvía la fila al inicio, incluso con `scrollLeft += 100` por código (reproducido con Playwright; sin snap avanza 100 px). Corrección: un único listener delegado en `ShelfWheelScroll` para todas las estanterías (incluida la de recomendaciones, se elimina el listener duplicado), que normaliza `deltaMode` (Firefox) y marca la fila con `data-wheel`, lo que desactiva el snap en CSS; un `touchstart` lo restablece. Los botones accesibles no cambian y se comprobó que avanzan/retroceden y que la rueda mueve la fila en ambos sentidos.

Fuente: `apps/web/components/RecommendationShelfTrack.tsx`, `apps/web/components/RecommendationDetailView.tsx` y `apps/web/app/globals.css`.

## Fuentes canónicas

- `apps/api/library/views.py`
- `apps/web/components/GameComments.tsx`
- `apps/web/app/[locale]/login/page.tsx`
- `apps/web/app/[locale]/register/page.tsx`
- `apps/web/components/AccountSwitcher.tsx`
- `apps/web/next.config.ts`

## Enlaces relacionados

- [[Requisitos - Backlog listas e inventario]]
- [[Requisitos - Cuentas y perfiles]]
- [[Frontera de sesión same-origin]]
