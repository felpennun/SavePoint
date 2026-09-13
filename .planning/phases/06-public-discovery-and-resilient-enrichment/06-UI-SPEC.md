---
phase: "6"
slug: "public-discovery-and-resilient-enrichment"
status: draft
shadcn_initialized: false
preset: none
created: "2026-09-13"
---

# Fase 6 — Contrato de diseño de interfaz

> Contrato visual y de interacción para descubrimiento público, proyecciones
> protegidas y módulo social. La fuente funcional principal es
> `06-CONTEXT.md` (2026-09-13); cuando el roadmap o los requisitos todavía no
> reflejan la ampliación social, este documento sigue las decisiones ratificadas
> en ese contexto.

## Design System

| Propiedad | Valor |
|-----------|-------|
| Tool | `none`: sistema CSS first-party existente; Tailwind CSS 4.3.3 solo aporta utilidades |
| Preset | No aplicable; no existe `components.json` |
| Component library | Componentes React first-party con CSS en `apps/web/app/globals.css`; sin Radix ni base-ui |
| Icon library | SVG inline first-party; ningún paquete de iconos externo |
| Font | `Inter` para interfaz y `JetBrains Mono` para metadatos, rutas, identificadores y estados técnicos |

### Reutilización obligatoria

La fase debe extender los patrones existentes, no crear una segunda gramática
visual. Reutilizar `AppShell`, `AccountSwitcher`, `FilterBar`,
`FilterDropdown`, `FacetMenu`, `FilterChip`, `PaginationArrow`, `GameCard`,
`CoverImage`, `StatusPill`, `ScorePill`, `GameComments`, `CustomLists` y
`ProfileSettings` cuando la responsabilidad coincida. Los nuevos componentes
sociales deben consumir los mismos `sp-*` utilities y variables CSS.

No se inicializa shadcn en esta fase: el proyecto ya tiene un sistema visual
first-party con tokens, variantes clara/oscura, foco visible y componentes
accesibles. No se incorporan bloques de registries.

## Spacing Scale

Valores declarados, todos múltiplos de 4 y alineados con `globals.css`:

| Token | Valor | Uso |
|-------|-------|-----|
| `xs` | 4px | Separación de icono y texto, microajustes inline |
| `sm` | 8px | Separación compacta entre controles, chips y filas |
| `ctl` | 12px | Padding de controles y filas compactas existente |
| `md` | 16px | Separación y padding por defecto |
| `lg` | 24px | Padding de superficies y separación de bloques |
| `xl` | 32px | Gaps de layout y separación entre secciones relacionadas |
| `2xl` | 48px | Separación entre áreas principales del detalle/perfil |
| `3xl` | 64px | Espaciado de página y cabeceras destacadas |

Excepciones: controles interactivos con un mínimo de 44px de alto y ancho
cuando son icon-only; no reducir ese objetivo para ahorrar espacio. En móvil,
el padding lateral de `sp-page` puede seguir el `md` existente; el contenido
no debe producir scroll horizontal.

## Typography

La jerarquía nueva usa exactamente dos pesos: regular `400` y semibold `600`.
El token existente de 12px queda reservado a microtexto técnico/eyebrow y no
se introduce como una nueva categoría de contenido.

| Rol | Tamaño | Peso | Line height |
|-----|--------|------|-------------|
| Label/meta | 13px | 600 | 1.4 |
| Body | 16px | 400 | 1.55 |
| Heading | 22px | 600 | 1.2 |
| Display | 30px | 600 | 1.2 |

Reglas adicionales:

- Los alias, títulos de juego, nombres de listas y mensajes se envuelven; no
  se permite que un valor largo fuerce el ancho del viewport.
- `JetBrains Mono` se reserva para conteos, rutas compartibles, fechas/IDs
  técnicos y estados de límite; no usarlo para párrafos.
- No añadir tamaños ni pesos ad hoc a las nuevas pantallas. Para texto muy
  corto de estado puede usarse el token micro existente de 12px.

## Color

La proporción 60/30/10 es de presencia visual, no una razón para introducir
colores nuevos. Mantener ambos temas mediante los mismos nombres de variable.

| Rol | Valor | Uso |
|-----|-------|-----|
| Dominante (60%) | Dark `#161826`; light `#f7f7fa` (`--color-surface-base`) | Fondo de página y áreas de lectura |
| Secundario (30%) | Dark `#232532`; light `#fdfdff` (`--color-surface-raised`), con overlay `#292b31`/`#eceef4` | Cards, superficies, menú de perfil, toolbar y paneles |
| Accent (10%) | Dark `#9184d9`; light `#5d5294` (`--color-accent`) | Acciones primarias outline, enlaces, navegación activa, paginación actual y outline de filtros seleccionados |
| Destructive | Dark `#f0808a`; light `#b3262c` (`--color-danger`) | Bloquear, eliminar amistad, eliminar contenido y errores destructivos |

Accent reservado exclusivamente para:

- CTA primaria `Enviar solicitud de amistad`, `Aplicar filtros` y
  `Recomendar juego` cuando estén disponibles.
- Enlaces de alias, juegos, listas y URLs compartibles.
- Estado de ruta activa, página actual y filtro seleccionado.
- Contorno del foco visible a través de `--color-focus-ring`.

El punto rojo de mensajes pendientes usa `--color-danger` y un texto accesible
complementario; nunca se comunica solo por color. Los estados de amistad
pendiente, aceptada, rechazada y bloqueada también llevan etiqueta textual. No
usar `--color-rating` para relaciones sociales.

## Copywriting Contract

La interfaz visible se localiza en `es.ts` y `en.ts` con paridad exacta. Las
frases de esta tabla son el copy español prescriptivo; las nuevas claves deben
tener una contraparte inglesa equivalente sin interpolar datos sensibles.

| Elemento | Copy prescriptivo |
|----------|-------------------|
| CTA primaria de descubrimiento social | `Enviar solicitud de amistad` |
| CTA de recomendación | `Recomendar juego` |
| Vacío del módulo social | Heading: `Aún no tienes amistades` · Body: `Busca un alias exacto para enviar una solicitud.` |
| Vacío de búsqueda exacta | `No se encontró ese alias exacto.` · Siguiente paso: `Comprueba el alias completo e inténtalo de nuevo.` |
| Vacío de mensajes | Heading: `No tienes mensajes de amigos` · Body: `Cuando una amistad te recomiende un juego, aparecerá aquí.` |
| Vacío de colección autorizada | `Esta colección no tiene juegos visibles.` |
| Vacío de lista autorizada | `Esta lista está vacía.` |
| Perfil mínimo no amigo | `Solo puedes ver el perfil básico hasta que se acepte la amistad.` |
| Error de carga | `No se pudo cargar esta información. Inténtalo de nuevo.` · Acción: `Reintentar` |
| Error de mutación | `La acción no se pudo completar. Revisa el estado e inténtalo de nuevo.` |
| Límite de recomendación | `Ya has recomendado un juego a esta amistad durante los últimos 7 días.` |
| 404 genérico | Heading: `No se ha encontrado este recurso.` · Body: `Comprueba el enlace o vuelve al catálogo.` No mencionar autorización, amistad o existencia previa. |
| Rechazar solicitud | `¿Rechazar la solicitud de {alias}? Podrá volver a enviarte una solicitud más adelante.` |
| Eliminar amistad | `¿Eliminar a {alias} de tus amistades? Perderá el acceso a tu colección, listas y comentarios permitidos, pero podrá solicitar amistad de nuevo.` |
| Bloquear cuenta | `¿Bloquear a {alias}? Se cancelarán las solicitudes, se eliminará la amistad, se revocará el acceso y no podrá volver a enviarte solicitudes mientras esté bloqueado.` |
| Confirmación positiva | `Solicitud aceptada.` / `Amistad eliminada.` / `Cuenta bloqueada.` / `Solicitud rechazada.` |

Las confirmaciones para `rechazar`, `eliminar amistad` y `bloquear` deben
identificar el alias y describir la consecuencia. `Bloquear` se presenta como
acción destructiva con `sp-btn-danger`; `rechazar` y `eliminar amistad` no se
agrupan bajo una etiqueta genérica de “gestionar”.

## Pantallas y contratos de interacción

### 1. Catalogue y filtros completos

- Conservar la página SSR actual `/{locale}/catalogue` y el patrón de
  `FilterBar` como una franja fina sobre la cuadrícula. La búsqueda por título,
  los chips activos, el recuento, la ordenación y la paginación permanecen
  navegables sin JavaScript.
- Cada filtro que se presente visualmente vive en un `FilterDropdown`/`FacetMenu`
  accesible: trigger `summary` con estado y número de selecciones, panel
  acotado con scroll interno, checkboxes nativos para multi-selección y
  `Aplicar filtros`/`Limpiar filtros` claramente separados.
- El backend y el contrato de consulta deben poder representar juegos,
  plataformas, ediciones, géneros, franquicias, desarrolladores, editoriales,
  fechas, modos y tags. La selección, agrupación y orden visual final de esas
  facetas queda deliberadamente abierta por D-01: no interpretar las facetas
  no mostradas en la primera versión como una omisión del contrato API.
- Todos los controles visuales deben serializar su estado en parámetros GET,
  incluidos valores repetidos y la ordenación. Copiar/pegar la URL debe
  reproducir exactamente el resultado; la paginación conserva la query completa.
- En desktop los popovers se anclan al trigger y no empujan la cuadrícula. En
  móvil el toolbar puede envolver; el panel de filtros ocupa el ancho
  disponible, mantiene `Aplicar` y `Limpiar` al alcance y se cierra con Escape
  devolviendo el foco al trigger.
- Resultados: `GameCard` conserva portada, título, año, plataforma y score con
  el tratamiento de portadas existente. Los títulos largos envuelven dentro de
  la card y la cuadrícula usa columnas adaptativas sin overflow.

### 2. Perfil mínimo para una persona no amiga

- La ruta de perfil SSR puede mostrar únicamente avatar (o iniciales), alias,
  biografía y una acción contextual. No renderizar colección, listas,
  comentarios, actividad, estadísticas, copias, compras, precios, tiendas,
  ubicaciones ni notas.
- El CTA inicial es `Enviar solicitud de amistad`. Tras enviar, se reemplaza
  por un estado textual `Solicitud enviada` y queda deshabilitado mientras se
  procesa; si existe una solicitud recibida, mostrar `Aceptar solicitud` y
  `Rechazar solicitud` con sus estados independientes.
- Si la relación está bloqueada en cualquiera de los dos sentidos, no
  presentar CTA ni contenido social. Los recursos protegidos bloqueados
  responden con la misma pantalla 404 genérica que cualquier otro recurso no
  autorizado.
- El perfil mínimo debe ser distinguible de una página de recurso no
  encontrado: D-07 lo mantiene visible a no amigos. El contenido social no
  debe aparecer brevemente durante la carga SSR.

### 3. Perfil, colección y listas para amistades aceptadas

- Una amistad aceptada conserva la cabecera del perfil y muestra secciones o
  navegación local para `Perfil`, `Colección` y `Listas`. El estado activo debe
  exponerse con `aria-current` o un encabezado equivalente; no ocultar estas
  superficies tras hover.
- Usar `/{locale}/profiles/[alias]` para el perfil y
  `/{locale}/profiles/[alias]/lists/[listSlug]` para una lista compartible. La
  colección puede vivir como sección autorizada del perfil; su URL no debe
  convertirse en una vía alternativa para saltarse la comprobación.
- La colección autorizada es una lista o cuadrícula legible con exactamente
  estos campos: portada, título/enlace, año, plataforma, `StatusPill` de
  backlog y valoración personal. Nunca mostrar copias, compras, precios,
  tiendas, ubicaciones ni notas privadas.
- Cada lista autorizada tiene URL compartible propia, nombre de lista y sus
  juegos en el orden manual del propietario. Cada fila reutiliza la misma
  proyección de juego que la colección; no añadir descripción, estadísticas o
  metadatos de propiedad por comodidad visual.
- El propietario puede ver y gestionar sus propias superficies mediante los
  controles existentes. Una amistad solo obtiene lectura de la proyección
  allowlisted. Las listas/colección vacías mantienen su encabezado y muestran
  el copy vacío, no una card vacía sin explicación.
- Una URL directa de perfil o lista siempre vuelve a validar autenticación,
  relación y visibilidad en el servidor. Propietario y amistad aceptada ven el
  contenido; el resto recibe 404 genérico indistinguible de inexistencia.

### 4. Módulo de amistades

- Crear una página dedicada, enlazada desde la navegación autenticada, con
  tres bloques explícitos: `Solicitudes recibidas`, `Solicitudes enviadas` y
  `Amistades`. Exponerla en `/{locale}/friends`. Cada bloque tiene recuento
  textual singular/plural y un estado vacío propio.
- La búsqueda inicial es un formulario de alias exacto, no autocomplete ni
  directorio parcial. Un resultado muestra avatar/iniciales, alias, estado de
  relación y la acción válida; cero resultados usa el copy de búsqueda exacta.
- Una solicitud recibida ofrece `Aceptar` y `Rechazar`. Una amistad ofrece
  `Eliminar amistad` y `Bloquear`; ambas son acciones separadas, visibles y
  etiquetadas. No reutilizar `Rechazar` como sinónimo de `Eliminar`.
- `Rechazar` no crea relación y permite una nueva solicitud en el futuro.
  `Eliminar amistad` revoca el acceso pero deja abierta una futura solicitud.
  `Bloquear` cancela solicitudes, elimina la relación, revoca acceso, impide
  nuevas solicitudes y oculta mutuamente perfiles y contenido social.
- Para cada mutación: deshabilitar solo la fila afectada durante la petición,
  conservar el contexto del alias, anunciar el resultado en `aria-live` y
  mover/eliminar la fila solo después de una respuesta válida. Si falla,
  mantenerla visible y ofrecer `Reintentar` sin filtrar el motivo interno.
- Las confirmaciones de rechazo, eliminación y bloqueo son diálogos
  accionables con `Cancelar` y una acción confirmatoria específica. El diálogo
  atrapa foco, cierra con Escape y lo devuelve al trigger.

### 5. Recomendaciones entre amistades y bandeja privada

- Integrar en el menú de `AccountSwitcher` una entrada exacta `Mensajes de
  amigos` que enlace a la página propia `/{locale}/messages`. La entrada puede
  mostrar un recuento textual de no leídos.
- Cuando haya mensajes o notificaciones pendientes, colocar un punto rojo
  pequeño arriba a la derecha del icono de perfil. El trigger debe anunciar
  `Mensajes de amigos` y el estado de no leídos en `aria-label`; el punto nunca
  es la única señal.
- La bandeja privada usa una lista de tarjetas compactas: avatar/alias del
  emisor, fecha, enlace al juego del catálogo, portada si está disponible y el
  mensaje opcional. No mostrar correos ni identificadores internos. El juego
  abre su ficha; al abrir o marcar como leído se actualiza el estado y el punto
  desaparece únicamente cuando no queden pendientes.
- El formulario `Recomendar juego` solo aparece para amistades aceptadas.
  Requiere un juego del catálogo, permite texto opcional y muestra
  confirmación local después de guardar. No enviar emails.
- Aplicar el límite de una recomendación por pareja emisor-receptor en una
  ventana móvil de siete días. Si el límite está activo, mantener visible el
  historial/estado y sustituir el CTA por el copy de límite; no presentar un
  error genérico que sugiera que el juego no existe.
- El envío fallido conserva el juego y el texto escritos, anuncia el error y
  ofrece reintentar. La bandeja puede mostrar la versión anterior mientras se
  actualiza, pero nunca debe inventar un mensaje ni exponer el de otra cuenta.

### 6. Comentarios dentro de la ficha del juego

- Mantener `GameComments` dentro de la página `/{locale}/games/[id]`, en el
  contenido principal después de los metadatos del juego, no como feed dentro
  del perfil.
- Cuando el visitante tiene permiso, cada comentario de tercero muestra solo
  alias del autor, texto y fecha. El alias enlaza al perfil permitido si la
  relación lo permite. No mostrar IDs, datos de propiedad, valoración ajena,
  compras ni notas privadas.
- Una persona no amiga o no autorizada no ve comentarios de terceros, aunque
  conozca la URL del juego. El juego sigue siendo visible si el catálogo lo
  permite; la sección de comentarios se omite o muestra un mensaje de acceso
  neutro sin revelar cuántos comentarios existen.
- El autor conserva la gestión de su propio comentario según las reglas de
  Fase 5. Los comentarios privados nunca aparecen a amistades; los marcados
  como públicos solo aparecen a amistades aceptadas.
- Usar la estructura existente de carga, formulario, edición, borrado,
  `aria-live` y error localizado. Un texto largo se envuelve y conserva una
  medida de lectura razonable; no truncar el comentario completo.

## Privacidad, seguridad y 404

- La UI consume proyecciones explícitas allowlisted; nunca infiere permisos a
  partir de un `owner_id` enviado por el cliente ni muestra campos simplemente
  porque estén presentes en un DTO.
- Las rutas directas protegidas no muestran un estado “cargando recurso” que
  confirme su existencia antes de la comprobación. La respuesta no autorizada
  usa la misma forma, copy y código 404 que un recurso inexistente.
- El perfil mínimo no amigo es la única excepción intencionada: alias, avatar,
  biografía y acción de solicitud sí son visibles conforme a D-07.
- No usar `alt`, títulos, tooltips, atributos data-* o mensajes de error para
  filtrar IDs internos, estado de bloqueo, nombres de campos privados o
  diferencias entre “no existe” y “no autorizado”.
- No hay llamadas a la enrichment API desde la interfaz ni durante una
  petición web; las vistas siguen funcionando con datos locales y placeholders
  legales cuando falte una portada.

## Responsive y accesibilidad

- Mantener el mínimo global de 44px para enlaces, botones, inputs, selects,
  checkboxes y triggers. Los iconos decorativos llevan `aria-hidden="true"`;
  los icon-only tienen nombre accesible completo.
- Cada página tiene un `h1`, landmarks (`nav`, `main`, `section`/`aside`) y
  encabezados de sección. Los recuentos de solicitudes, estados de relación,
  mensajes no leídos y acciones completadas se anuncian con texto, no solo
  con color, punto o icono.
- El orden de foco sigue el orden visual: búsqueda/filtros → resultados →
  acciones. Los popovers y diálogos son utilizables solo con teclado, cierran
  con Escape y devuelven el foco. La navegación móvil reutiliza el patrón de
  `MobileMenu` con focus trap.
- En anchuras móviles, el perfil apila cabecera, CTA y secciones; colección y
  listas pasan a una columna cuando dos columnas produzcan compresión; las
  cards y tablas reflowan en vez de crear scroll horizontal de página.
- Los títulos de juegos, alias, nombres de listas, biografías, comentarios y
  mensajes admiten una expansión mínima del 30 % y zoom del 400 % sin perder
  acciones ni provocar solapamientos.
- Respetar `prefers-reduced-motion: reduce`; el punto rojo no parpadea y los
  cambios de carga no dependen de animación. Skeletons, si se usan, reservan
  geometría y llevan `aria-hidden="true"` con un único anuncio `aria-live`.
- Probar `es` y `en` con alias largos, cero/uno/muchos elementos, teclado,
  foco, lectura de punto rojo, 404 genérico y viewports desktop/mobile.

## UI Considerations

Las consideraciones cubren estados de catálogo, perfiles, relaciones, mensajes,
listas y comentarios. El copy de vacío y error se define arriba para evitar
duplicación.

Applicable state considerations resolved: 8 covered, 0 backstop, 0 unresolved

| Categoría | Elementos | Estado | Resolución / razón |
|-----------|-----------|--------|--------------------|
| empty | `catalogue`, `social-hub`, `messages`, `friend-collection`, `friend-list`, `comments` | ✅ covered | Los estados de cero resultados y cero contenido mantienen encabezado, copy localizado y siguiente paso explícito; referencian las filas de `Copywriting Contract`. |
| loading | `catalogue`, `social-hub`, `messages`, `interactive-control` | ✅ covered | La carga usa geometría reservada/skeleton oculto a AT o un anuncio `aria-live="polite"`; las mutaciones deshabilitan solo la fila afectada y conservan sus valores. |
| error | `catalogue`, `social-hub`, `messages`, `interactive-control` | ✅ covered | Cada carga y mutación tiene mensaje localizado, alcance de reintento, foco estable y preservación de datos; nunca expone el motivo de autorización. |
| populated | `catalogue`, `friend-profile`, `friend-collection`, `friend-list`, `messages` | ✅ covered | La jerarquía normal está prescrita: cards de catálogo; perfil autorizado; proyección allowlisted de juego; orden manual de listas; tarjeta privada de mensaje. |
| partial | `catalogue`, `friend-profile`, `friend-collection`, `messages` | ✅ covered | La ausencia de portada, biografía o mensaje opcional no vacía la superficie: se usa placeholder/copy neutro y permanecen los campos autorizados disponibles. |
| overflow | `catalogue`, `social-hub`, `friend-list`, `comments`, `messages`, `nav` | ✅ covered | Grid adaptativa, popovers con scroll interno, wrap de títulos/prosa, filas verticales y menú móvil evitan overflow horizontal; no se recorta contenido social. |
| zero-one-many | `catalogue`, `social-hub`, `messages`, `friend-collection`, `friend-list`, `comments` | ✅ covered | Se cubren cero, una y muchas coincidencias con recuentos localizados, singular/plural, layout estable y paginación determinista. |
| long-text | `friend-profile`, `friend-list`, `comments`, `messages`, `interactive-control` | ✅ covered | Alias, títulos, biografías, comentarios, mensajes y etiquetas envuelven con límites de lectura; los botones conservan nombre y objetivo de 44px. |

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| No aplica | Ninguno | `components.json` no existe; no se usan shadcn ni registries de terceros. |

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS
- [ ] Dimension 7 Inventory Provenance: PASS — no aplica al sistema manual; los componentes first-party se han enumerado desde el código existente.

**Approval:** pending

## UI-SPEC COMPLETE
