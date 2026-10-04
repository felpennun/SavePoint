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
