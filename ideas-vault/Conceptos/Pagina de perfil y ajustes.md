---
tags: [producto, perfil, privacidad, ui]
estado: vigente
fecha: 2026-10-04
---

# Pagina de perfil y ajustes

Pagina propia de cada usuario (`/{locale}/profile`), a la que se llega desde la opcion
**Editar perfil** del desplegable del icono de cuenta. Implementa el artboard 2c de
`design/SavePoint visual identity system-handoff.zip` (`SavePoint Ideas v2.dc.html`).

## Pestanas y alcance real

- **Cuenta**: nombre completo, nombre de usuario (editable una sola vez, solo a un nombre libre),
  biografia (160), cinco favoritos, foto y portada
  (subida con recorte en el navegador, URL https o uno de cinco avatares).
- **Privacidad**: Favoritos, Colección y visibilidad por defecto de las listas nuevas.
- **Preferencias**: tema e idioma (los demas interruptores del diseno no tienen funcion en el producto).
- **Conexiones**: importacion de CSV (filas de coleccion y copias).
- **Seguridad**: cambio de contrasena, exportacion (CSV y Excel) y eliminacion de la cuenta.

## Decisiones y desviaciones del diseno

- El nombre de usuario se puede cambiar una vez (3 a 30 caracteres: letras, numeros, `.`, `-`, `_`;
  sin distinguir mayusculas al comprobar duplicados). Se avisa antes de confirmar.
- La exportacion de la coleccion vive solo en Seguridad; se retiro el boton de la pagina de coleccion.

- Dos niveles de visibilidad, **Privada** y **Amistades**. El nivel "Publica" del diseno no existe
  porque las cuentas no son publicas: solo las amistades aceptadas ven la coleccion.
- No se incluyen Actividad (no hay feed), Steam, Discord, spoilers, notificaciones, resumen por
  correo ni cambio de correo (la cuenta no guarda correo).
- La eliminacion de cuenta es definitiva y exige la contrasena; el evento de auditoria no lleva actor
  porque la auditoria es de solo anadir.
- La importacion rechaza las filas de favoritos, comentarios y listas que incluye la exportacion
  completa: solo admite `collection` y `copy`.

## Fuentes

Codigo: `apps/web/components/ProfileEditor.tsx`, `apps/api/accounts/views.py`,
`apps/api/accounts/services.py`. Relacionado: [[Allowlist de campos publicos]],
[[Convenciones de idioma]].

- **Filtros desplegables (2026-10-04):** en catalogo, coleccion y la coleccion de una amistad, un filtro abierto se cierra al abrir otro, al pulsar en cualquier parte de la pantalla o con Escape. `FilterDropdownScript` pasa a ser un efecto de cliente (el `<script>` inline no se ejecutaba tras una navegacion del lado cliente) y tambien se monta en `FriendProfile`.

- **Colección: selector izquierdo (2026-10-04):** sigue el artboard "Colección con listas" de `design/brand/SavePoint visual identity system-handoff (4).zip` (`SavePoint Ideas v2.dc.html`). ESTADO (Todos, Jugando, Pendientes, Completados, Abandonados, con su cuadradito de color y el total) y MIS LISTAS (nombre, visibilidad y número de juegos). Cada fila es un enlace (`?status=` o `?list=`, excluyentes) y la activa lleva `aria-current`. En ventanas de 1500 px o más el selector ocupa el margen izquierdo hasta el logo: su fondo se extiende desde el borde izquierdo de la ventana hasta justo antes del logo y desde la cabecera hasta el final de la página (el contenido del selector no se mueve y se queda fijo al desplazar); la misma banda de color se repite a la derecha, desde justo después de la foto de perfil hasta el borde de la ventana, y la barra de filtros con el buscador y las tarjetas ocupan el ancho de la cabecera (del logo a la foto de perfil); por debajo de 1500 px queda dentro de la página, a la izquierda de las tarjetas, y en móvil se apila encima. Se retiran el desplegable "Estado", los bloques de resumen y la sección "Tus listas" de debajo: "+ NUEVA" abre un formulario en el propio selector y crea la lista; al elegir una lista, "Editar lista" (plegado) permite añadir juegos, reordenar, quitar y eliminarla. No se incluyen del diseño el encabezado de lista, el conmutador Portadas/Filas ni "Compartir lista".

- **Colección y catálogo sin scroll de página (2026-10-04):** en escritorio (más de 900 px) la página no se desplaza; la barra de filtros queda arriba y solo las tarjetas hacen scroll vertical con la barra oculta, como en amistades (clase `sp-fixed-page` y `.sp-coll-main > section`). En móvil se mantiene el scroll normal de la página.

- **Colección: lista seleccionada (2026-10-04):** la rejilla termina con el recuadro discontinuo "Añadir juego a esta lista" del diseño, que abre el buscador de la colección (el mismo de favoritos y de recomendar un juego). El panel plegado "Editar lista" tiene tres acciones: cambiar nombre, eliminar la lista (con confirmación) y "Eliminar juegos", que pone un botón de menos en cada juego; los marcados se ponen grises, se pueden marcar varios y "Confirmar borrado" pide confirmación antes de quitarlos. Ya no hay reordenar en la interfaz (la API de reordenado sigue existiendo). Componentes: `SelectedListView`, `AddGameToListTile`, `GamePicker`.
