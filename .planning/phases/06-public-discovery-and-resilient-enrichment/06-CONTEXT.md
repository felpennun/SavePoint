# Fase 6: Public Discovery and Resilient Enrichment - Contexto

**Recopilado:** 2026-09-13
**Estado:** Listo para planificación

<domain>
## Límite de la fase

La Fase 6 amplía su alcance original de descubrimiento público y
enriquecimiento resiliente para incluir un módulo social completo. El catálogo
debe representar y permitir filtrar todas las dimensiones de `CAT-05` que estén
disponibles en las fuentes aprobadas: juegos, plataformas, ediciones, géneros,
franquicias, desarrolladores, editoriales, fechas, modos y tags. La API debe
quedar preparada para todas esas dimensiones; la selección de filtros que se
presenta finalmente en la interfaz se decidirá durante el diseño visual.

El módulo social permite buscar usuarios por alias exacto, enviar y aceptar
solicitudes de amistad, gestionar amistades y bloquear cuentas. La colección,
las listas y los comentarios marcados como públicos son visibles únicamente
para amistades aceptadas. El perfil básico sigue siendo visible para personas
no amigas con alias, avatar, biografía y acción para añadir a esa persona,
pero sin actividad privada.

Las amistades pueden abrir URLs compartibles de perfiles y listas, pero una URL
nunca evita la comprobación de permisos: el propietario y las amistades
aceptadas pueden acceder; el resto recibe una respuesta indistinguible de
recurso inexistente. Las recomendaciones entre usuarios son mensajes sociales
privados con un juego del catálogo y un texto opcional, limitadas a una por
pareja emisor-receptor durante cada ventana móvil de siete días.

</domain>

<decisions>
## Decisiones de implementación

### Catálogo y filtros

- **D-01:** `CAT-05` permanece dentro de la Fase 6. El backend y el contrato de
  consulta prepararán filtros para todas las dimensiones disponibles del
  catálogo, aunque el autor decidirá después cuáles se muestran en la interfaz.
  La decisión visual no debe obligar a eliminar la representación ni la
  capacidad de consulta del backend.
- **D-02:** Se conserva el comportamiento de URLs GET compartibles para las
  búsquedas y filtros del catálogo, ampliándolo a las nuevas dimensiones sin
  introducir estado de filtro exclusivo del cliente.

### Identidad y relaciones sociales

- **D-03:** La amistad es bidireccional y se crea mediante solicitud y
  aceptación. La búsqueda inicial de usuarios usa el alias exacto, evitando un
  directorio parcial que facilite enumeración.
- **D-04:** El módulo social dedicado muestra solicitudes recibidas y enviadas,
  amistades y acciones de aceptar, rechazar, eliminar y bloquear.
- **D-05:** Rechazar una solicitud no crea relación y deja abierta la
  posibilidad de solicitar amistad de nuevo en el futuro. Eliminar una
  amistad termina la relación y revoca el acceso, pero no bloquea una nueva
  solicitud. Bloquear cancela solicitudes, elimina la relación, revoca el
  acceso, impide nuevas solicitudes y oculta mutuamente los perfiles y el
  contenido social mientras permanezca activo.

### Privacidad y URLs públicas

- **D-06:** Las opciones de colección, listas y comentarios que se denominen
  “públicas” son públicas únicamente dentro de la relación de amistad aceptada;
  no son visibles a visitantes anónimos ni a usuarios no amigos.
- **D-07:** Una persona no amiga ve únicamente el perfil mínimo compuesto por
  alias, avatar, biografía y acción para enviar una solicitud. No ve
  colección, listas, comentarios ni estadísticas de actividad.
- **D-08:** Las URLs directas de perfil y lista son compartibles para el
  propietario y sus amistades aceptadas. El backend comprueba autenticación y
  amistad también en la ruta directa; no se confía en haber llegado desde el
  perfil. Las solicitudes no autorizadas responden con `404` genérico.
- **D-09:** La colección de una amistad muestra juego, portada, año,
  plataforma, estado de backlog y valoración personal. Nunca muestra copias,
  compras, precios, tiendas, ubicaciones ni notas privadas.
- **D-10:** Las listas muestran los mismos datos de juego que la colección y
  conservan exactamente el orden manual definido por el propietario.
- **D-11:** Los comentarios se muestran dentro de la página del juego, cuando
  existen y el visitante tiene permiso, con alias del autor, texto y fecha.
  No se añaden datos de propiedad ni identificadores internos.
- **D-12:** La proyección pública no añade estadísticas globales independientes
  más allá de los estados y valoraciones que forman parte de la colección
  autorizada. La rebaseline de `PROF-03` debe reflejar esta decisión explícita.

### Mensajes y recomendaciones sociales

- **D-13:** Una recomendación contiene un juego del catálogo y un mensaje
  opcional, y llega a una bandeja privada de “Mensajes de amigos”. No se envían
  correos.
- **D-14:** La bandeja se integra en el desplegable del icono de perfil y tiene
  una página propia. Un punto rojo sobre el icono indica que existen mensajes
  o notificaciones pendientes.
- **D-15:** El límite es de una recomendación por pareja emisor-receptor en una
  ventana móvil de siete días. Un emisor puede recomendar a varias amistades,
  pero no repetir el envío al mismo receptor durante esa ventana.

### A criterio del agente

- La representación interna de solicitudes, amistades, bloqueos, mensajes,
  lectura y expiración del límite, siempre que respete las decisiones de
  privacidad y permita auditoría y pruebas deterministas.
- La forma visual concreta del módulo social, del indicador rojo y de los
  filtros del catálogo, manteniendo los patrones accesibles existentes. El
  autor decidirá posteriormente qué filtros se eliminan o se agrupan en la
  interfaz.
- Los nombres exactos de rutas, DTOs y componentes, siempre que las URLs
  compartibles y las respuestas `404` no filtren autorización o existencia.

</decisions>

<canonical_refs>
## Referencias canónicas

**Los agentes posteriores deben leer estas referencias antes de planificar o
implementar.**

### Alcance, requisitos y convenciones

- `.planning/ROADMAP.md` — objetivo, criterios de éxito y requisitos actuales
  de la Fase 6; debe rebaselinarse para reflejar la ampliación social.
- `.planning/REQUIREMENTS.md` — `PROF-03`, `PROF-04` y `CAT-05`; debe
  incorporar requisitos trazables del módulo social y reconciliar la privacidad.
- `.planning/PROJECT.md` — límites del producto, privacidad, reproducibilidad y
  audiencia controlada.
- `CONVENTIONS.md` — idioma, trazabilidad, privacidad, secretos y mantenimiento
  del vault vivo.
- `ideas-vault/README.md` — política de sincronización del vault.

### Decisiones y conceptos de producto

- `ideas-vault/Fases/Fase 6 - Descubrimiento publico.md` — alcance conceptual
  inicial de la Fase 6.
- `ideas-vault/Conceptos/Perfil publico.md` — perfil público y proyección
  allowlist.
- `ideas-vault/Conceptos/Allowlist de campos publicos.md` — regla de no ampliar
  DTOs públicos accidentalmente.
- `ideas-vault/Conceptos/Filtros y facetas multi-seleccion.md` — filtros GET,
  facetas y ordenación determinista.
- `.planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md`
  — privacidad `public`/`private`, perfiles, comentarios, listas y copias
  existentes que la fase debe extender sin filtrar datos privados.

### Arquitectura y patrones existentes

- `.planning/codebase/STACK.md` — versiones y herramientas aprobadas.
- `.planning/codebase/ARCHITECTURE.md` — separación Next.js/Django/PostgreSQL,
  sesiones, proyecciones y restricciones relacionales.
- `.planning/codebase/INTEGRATIONS.md` — frontera offline/local y prohibición de
  llamadas externas durante peticiones web.
- `.planning/codebase/STRUCTURE.md` — ubicación de rutas, componentes, tests y
  aplicaciones.
- `.planning/codebase/CONVENTIONS.md` — patrones de nombres, validación y
  protección de datos.

### Backend y frontend a reutilizar

- `apps/api/catalogue/models.py` — obras, releases, ediciones y dimensiones
  importadas del catálogo.
- `apps/api/catalogue/search.py` — consulta local, filtros multi-selección,
  facetas, ordenación allowlist y paginación determinista.
- `apps/api/catalogue/serializers.py` — cards, detalle, tags, releases,
  procedencia y allowlists de respuesta.
- `apps/api/catalogue/views.py` y `apps/api/catalogue/urls.py` — endpoints
  locales de catálogo y patrones de errores/throttling.
- `apps/api/accounts/models.py` — perfil, visibilidad y favoritos existentes.
- `apps/api/accounts/serializers.py` — `build_public_profile` y allowlist de
  proyección existente.
- `apps/api/accounts/views.py` y `apps/api/accounts/urls.py` — sesiones,
  perfiles y respuestas genéricas ante alias no autorizados.
- `apps/api/library/models.py`, `apps/api/library/serializers.py`,
  `apps/api/library/views.py` y `apps/api/library/urls.py` — colección,
  comentarios, listas, orden manual y datos privados que no deben filtrarse.
- `apps/web/app/[locale]/catalogue/page.tsx` — filtros GET, facetas y
  paginación compartible.
- `apps/web/app/[locale]/profiles/[alias]/page.tsx` — perfil público SSR y
  renderizado actual de colección, favoritos, comentarios y listas.
- `apps/web/components/AppShell.tsx` — navegación, selector de cuenta y punto
  de integración del módulo social.
- `apps/web/components/AccountSwitcher.tsx` — menú de cuenta existente para
  integrar “Mensajes de amigos”.
- `apps/web/lib/api.ts` y `apps/web/lib/client-api.ts` — fetch SSR, proxy
  same-origin, sesión y CSRF.

</canonical_refs>

<code_context>
## Contexto del código existente

### Activos reutilizables

- `GameWork`, `GameRelease`, `Edition` y las relaciones M2M de `catalogue` ya
  representan gran parte de `CAT-05`; `search.py` ofrece un punto único para
  ampliar filtros y facetas.
- `build_public_profile` en `accounts/serializers.py` ya construye un DTO
  manual mediante allowlist y separa privacidad de colección, favoritos,
  comentarios y listas.
- `GameCardSerializer`, `GameDetailSerializer`, `GameCard`, `GameDetail` y
  `fetchCatalogueList` permiten reutilizar tarjetas, metadatos, procedencia y
  navegación local.
- `FilterBar`, `FacetMenu`, `FilterDropdown`, `FilterDropdownScript`,
  `catalogue-filters.ts` y `PaginationArrow` ya implementan filtros GET
  accesibles y URLs reproducibles.
- `AppShell`, `AccountSwitcher`, `api.ts` y `client-api.ts` proporcionan los
  puntos de integración para navegación, menú de perfil, fetch SSR y mutaciones
  same-origin protegidas por CSRF.

### Patrones establecidos

- El catálogo y las páginas públicas usan datos locales y SSR; no se consulta
  ningún proveedor externo durante una petición.
- Los parámetros de consulta y ordenación pasan por allowlists y límites
  explícitos; la respuesta se ordena de forma total y determinista.
- La autorización se deriva del usuario autenticado y de relaciones verificadas
  en el backend, nunca de IDs de propietario enviados por el cliente.
- Las proyecciones públicas se construyen manualmente y no mediante
  introspección automática de modelos.
- El frontend mantiene degradación sin JavaScript cuando es viable, usa
  componentes accesibles y conserva sesión/CSRF a través del proxy same-origin.

### Puntos de integración

- Nuevos modelos y servicios sociales se integrarán en `accounts` o un módulo
  social claramente separado, con rutas API protegidas por relación.
- El perfil SSR y el selector de cuenta deberán consultar el estado social y la
  bandeja de mensajes sin revelar contenido a usuarios no autorizados.
- La página de cada juego es el destino de los comentarios permitidos y puede
  enlazarse desde colecciones, listas y mensajes.
- El catálogo debe ampliar su consulta y DTO sin modificar snapshots ni
  artefactos de evaluación offline.

</code_context>

<specifics>
## Detalles específicos

- El autor quiere que el punto rojo aparezca arriba a la derecha del icono de
  perfil cuando existan mensajes o notificaciones pendientes.
- Dentro del desplegable del perfil debe existir la sección “Mensajes de
  amigos”, que conduce a una página propia para consultar lo recibido.
- La clasificación visual de filtros se pospone: primero se conserva la
  capacidad completa de backend y después se decide qué se muestra al usuario.

</specifics>

<deferred>
## Ideas diferidas

- Ninguna de las capacidades sociales acordadas queda diferida; el autor
  autorizó ampliar la Fase 6 para incluirlas.
- La selección visual de filtros del catálogo queda pendiente de una decisión
  de diseño posterior, sin reducir por ahora el contrato backend.

</deferred>

---

*Fase: 6-Public Discovery and Resilient Enrichment*
*Contexto recopilado: 2026-09-13*
