# Fase 6: Public Discovery and Resilient Enrichment - Registro de discusión

> **Solo registro de auditoría.** No usar como entrada de planificación,
> investigación o ejecución. Las decisiones están en `06-CONTEXT.md`.

**Fecha:** 2026-09-13
**Fase:** 6-Public Discovery and Resilient Enrichment
**Áreas discutidas:** catálogo y filtros, módulo social, proyección pública de perfiles y listas, mensajes y recomendaciones

---

## Catálogo y filtros

| Opción | Descripción | Seleccionada |
|---|---|---|
| Posponer `CAT-05` | Mover los filtros y metadatos amplios a otra fase. | |
| Mantener `CAT-05` y preparar todos los filtros | El backend conserva todas las dimensiones; el autor decide más adelante qué filtros aparecen visualmente. | ✓ |
| Reducir ahora a filtros básicos | Limitar API e interfaz a las facetas actuales. | |

**Elección del usuario:** mantener `CAT-05`; filtros para todo en backend y decisión visual posterior.
**Notas:** el autor decidirá después qué filtros se quitan de la parte visual para los usuarios.

---

## Módulo social: relaciones y acceso

| Opción | Descripción | Seleccionada |
|---|---|---|
| Solicitud y aceptación mutuas | La amistad es bidireccional y requiere aceptación. | ✓ |
| Seguimiento unilateral | Añadir a otro usuario no requiere aprobación. | |
| Amistad inmediata | La relación se crea al añadir al usuario. | |

**Elección del usuario:** solicitud y aceptación mutuas.
**Notas:** el módulo social se incorporó explícitamente a la Fase 6.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Solo amistades aceptadas | Colección, listas y comentarios “públicos” solo son visibles para amigos. | ✓ |
| Perfil completo solo para amistades | Ni siquiera el perfil básico es visible a no amigos. | |
| Visibilidad global | Cualquier visitante puede ver contenido marcado como público. | |

**Elección del usuario:** solo amistades aceptadas.

| Opción | Descripción | Seleccionada |
|---|---|---|
| URL protegida por amistad | El propietario y amigos pueden abrirla directamente; el resto recibe `404`. | ✓ |
| Solo navegación desde el perfil | La ruta depende de haber navegado desde el perfil. | |
| Sin URLs propias de listas | Las listas solo aparecen dentro del perfil. | |

**Elección del usuario:** URL protegida por amistad.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Búsqueda exacta por alias | Una coincidencia por nombre de usuario completo. | ✓ |
| Búsqueda parcial/autocompletado | Varias cuentas aparecen mientras se escribe. | |
| Enlace de invitación | La relación se inicia desde un enlace personal. | |

**Elección del usuario:** búsqueda exacta por alias.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Módulo social dedicado | Solicitudes recibidas/enviadas, aceptar, rechazar, eliminar y bloquear. | ✓ |
| Notificaciones en el menú de cuenta | Las solicitudes se gestionan como avisos del selector. | |
| Acciones desde cada perfil | Cada perfil expone la acción según el estado. | |

**Elección del usuario:** módulo social dedicado.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Bloqueo completo | Cancela solicitudes, elimina relación, oculta contenido e impide nuevas solicitudes. | ✓ |
| Solo eliminar amistad | Revoca acceso, pero permite solicitar de nuevo. | |
| Sin bloqueo | Solo aceptar, rechazar y eliminar. | |

**Elección del usuario:** bloqueo completo.
**Notas:** el usuario aclaró que rechazar, eliminar y bloquear son estados diferentes: rechazar no crea relación; eliminar termina la amistad sin bloquear; bloquear impide futuras solicitudes y oculta mutuamente el contenido.

---

## Proyección pública de perfiles y listas

| Opción | Descripción | Seleccionada |
|---|---|---|
| Perfil mínimo para no amigos | Alias, avatar, biografía y botón para añadir; sin contenido social. | ✓ |
| Perfil completamente oculto | Respuesta `404` para no amigos. | |
| Perfil visible sin contenido | Página visible con aviso de restricción. | |

**Elección del usuario:** perfil mínimo para no amigos.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Juego, metadatos, estado y valoración | Incluye portada, año, plataforma, estado y valoración personal; excluye propiedad y notas. | ✓ |
| Lo anterior sin valoración | No muestra la puntuación personal. | |
| Solo juegos | Solo título y enlace. | |

**Elección del usuario:** la opción recomendada más la valoración personal.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Lista como colección ordenada | Mismos datos que la colección y orden manual del propietario. | ✓ |
| Solo nombres y enlaces | Vista compacta sin metadatos. | |
| Vista enriquecida | Añade descripción, fechas y estadísticas. | |

**Elección del usuario:** las listas muestran lo mismo que la colección y respetan la ordenación dada por el usuario.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Comentario dentro del juego | Alias, texto y fecha en la página del juego. | ✓ |
| Comentario resumido en el perfil | Texto y juego en el perfil. | |
| Comentario con valoración | Añade la puntuación personal en cada comentario. | |

**Elección del usuario:** el comentario aparece dentro del propio juego, si existe, con alias, texto y fecha.

---

## Mensajes y recomendaciones sociales

| Opción | Descripción | Seleccionada |
|---|---|---|
| Juego + mensaje opcional en bandeja privada | Se consulta desde “Mensajes de amigos”; sin correos. | ✓ |
| Juego en notificaciones | Aviso breve sin mensaje adicional. | |
| Mensaje libre con juego opcional | Menos estructurado y menos trazable. | |

**Elección del usuario:** juego y mensaje opcional en bandeja privada.
**Notas:** el punto rojo se muestra sobre el icono de perfil; el desplegable contiene “Mensajes de amigos” y abre una página propia.

| Opción | Descripción | Seleccionada |
|---|---|---|
| Una recomendación por pareja cada 7 días | Se puede recomendar a varias amistades, sin repetir receptor durante la ventana. | ✓ |
| Una recomendación total por emisor | Un único envío semanal en total. | |
| Una recomendación total por receptor | Un usuario recibe como máximo una semanal. | |

**Elección del usuario:** una recomendación por pareja emisor-receptor cada 7 días.

## Ideas diferidas

- La decisión de qué filtros se presentan en la interfaz queda para el diseño visual posterior.

