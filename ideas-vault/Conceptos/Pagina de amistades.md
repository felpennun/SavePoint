---
tags: [producto, social, amistades, ui]
estado: vigente
fecha: 2026-10-04
---

# Pagina de amistades

Pagina `/{locale}/friends`, implementada a partir del artboard 2d de
`design/SavePoint visual identity system-handoff (1).zip` (`SavePoint Ideas v2.dc.html`). Tres
columnas: buscar y amistades, perfil de la persona elegida, notificaciones.

## Comportamiento

- Busqueda por nombre de usuario exacto, solicitud, cancelacion de la solicitud enviada y aceptacion.
- Con la amistad aceptada se ve el nombre completo, la biografia, la foto, los cinco favoritos y el
  resumen de la coleccion, siempre que su dueno no los haya puesto en privado
  (ver [[Pagina de perfil y ajustes]]). Quien no es amistad solo ve el nombre de usuario.
- Recomendar un juego de la propia coleccion, con aviso si la amistad ya lo tiene. Se mantiene el limite
  de una recomendacion por semana y amistad (HTTP 429).
- Notificaciones: solicitud recibida, recomendacion recibida, solicitud aceptada y recomendacion
  anadida a pendientes. Una recomendacion se responde una sola vez: anadir a pendientes (crea la entrada
  como pendiente si no estaba en la coleccion y avisa a quien la envio) o descartar.
- El contador del menu de cuenta suma todo lo pendiente de las notificaciones.

## Perfil detallado de una amistad

`/{locale}/profiles/<usuario>` (solo lectura) reutiliza el diseno del perfil editable: portada, foto,
nombre y cuatro pestanas (Perfil, Coleccion, Listas, Comentarios), sin Privacidad, Preferencias,
Conexiones ni Seguridad. Lo que su dueno mantiene en privado se anuncia como "no disponible":
la coleccion y los favoritos siguen sus interruptores; cada lista y cada comentario, su propia
visibilidad. La pestana Coleccion lleva la misma barra de filtros que la coleccion propia (busqueda, estado, orden, platino) y la medalla de platino. El resumen lateral solo aparece en la pestana Perfil. Quien no es amistad pasa a la pagina de amistades. Datos: `GET /api/social/friends/<usuario>/profile/`.

## Decisiones

- No se incluye el boton "Mensaje" del diseno: no existe mensajeria libre, solo recomendaciones.
- Se conservan "Eliminar amistad" y "Bloquear" (con confirmacion) bajo el perfil, aunque el diseno no
  los dibuja, para no perder esas funciones.
- `/messages` redirige a `/friends`: la bandeja de recomendaciones vive en las notificaciones.

## Fuentes

`apps/web/components/FriendsApp.tsx`, `apps/api/social/` (`profiles.py`, `services.py`, `views.py`).

## Perfil de una amistad: colección y listas (2026-10-04)

- La pestaña **Listas** tiene un selector a la izquierda (nombre y número de juegos de cada lista visible) y, a la derecha, los juegos de la lista elegida con las mismas tarjetas de la colección (año, plataformas, estado, valoración y platino cuando la colección es visible), buscador y paginación de 8 juegos (`FriendLists`). El nombre de la lista enlaza a su página compartible.
- En escritorio (más de 900 px), las pestañas **Colección** y **Listas** no desplazan la página: la tarjeta del perfil ocupa la ventana, la barra de filtros queda fija y solo los juegos hacen scroll vertical con la barra oculta, como en el catálogo (`.sp-pf.is-fixed`, `.sp-pf-scroll`; la parte superior (banner, cabecera y pestañas) mantiene el mismo tamaño que en Perfil). Perfil y Comentarios mantienen el scroll normal.
- La pestaña **Comentarios** también va en modo fijo (sin scroll de página, los comentarios hacen scroll vertical con la barra oculta). Los selectores de listas (el de la colección propia y el de la pestaña Listas) hacen scroll vertical por su cuenta cuando hay muchas listas; en la colección propia, ESTADO queda fijo y solo se desplaza MIS LISTAS.
- En la pestaña **Perfil** el resumen ya no es un bloque: es una columna a la derecha, separada por una línea vertical y rellena con el color de los laterales de la colección, a toda la altura de la tarjeta del perfil (`.sp-pf--friend`; el editor del perfil propio no cambia).
