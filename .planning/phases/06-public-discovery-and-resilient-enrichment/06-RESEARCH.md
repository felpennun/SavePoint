# Phase 6: Public Discovery and Resilient Enrichment - Research

**Researched:** 2026-09-13 [VERIFIED: environment_context]
**Domain:** Public discovery, privacy-aware social relationships, private recommendations, and local catalogue enrichment [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:1-7]
**Confidence:** MEDIUM [VERIFIED: gsd-tools classify-confidence --provider websearch --verified]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Catálogo y filtros

- **D-01:** `CAT-05` permanece dentro de la Fase 6. El backend y el contrato de
  consulta prepararán filtros para todas las dimensiones disponibles del
  catálogo, aunque el autor decidirá después cuáles se muestran en la interfaz.
  La decisión visual no debe obligar a eliminar la representación ni la
  capacidad de consulta del backend.
- **D-02:** Se conserva el comportamiento de URLs GET compartibles para las
  búsquedas y filtros del catálogo, ampliándolo a las nuevas dimensiones sin
  introducir estado de filtro exclusivo del cliente.

#### Identidad y relaciones sociales

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

#### Privacidad y URLs públicas

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

#### Mensajes y recomendaciones sociales

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

### Deferred Ideas (OUT OF SCOPE)

- Ninguna de las capacidades sociales acordadas queda diferida; el autor
  autorizó ampliar la Fase 6 para incluirlas.
- La selección visual de filtros del catálogo queda pendiente de una decisión
  de diseño posterior, sin reducir por ahora el contrato backend.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Descripción actual | Apoyo de esta investigación |
|---|---|---|
| PROF-03 | “Public profile shows only permitted games, lists, ratings, comments, and statistics.” [VERIFIED: .planning/REQUIREMENTS.md:12-17] | Proyección separada por propietario, amistad aceptada y no amistad; allowlist de campos; pruebas de autorización y no filtración. |
| PROF-04 | “Shareable URL for public profile and lists.” [VERIFIED: .planning/REQUIREMENTS.md:12-17] | Rutas SSR dinámicas con comprobación backend, cookie forwarding y `404` genérico. |
| CAT-05 | “Catalogue represents games, platforms, editions, genres, franchises, developers, publishers, dates, modes, and tags available from approved sources.” [VERIFIED: .planning/REQUIREMENTS.md:19-24] | Extensión de modelo, filtros, facets, DTOs y snapshots locales sin llamadas de proveedor en request. |
| SOCIAL-* | El contexto funcional añade solicitudes, amistades, bloqueos, proyecciones entre amigos y recomendaciones privadas. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:47-95] | Requiere rebaselining con IDs trazables antes de cerrar el plan; no debe ocultarse dentro de `PROF-03`/`PROF-04`. |
</phase_requirements>

## Summary

La Fase 6 no es únicamente una ampliación de búsqueda: es una frontera de confianza entre el catálogo local y una proyección social autorizada. El backend actual ya tiene una buena base de allowlists manuales, consultas locales, autenticación de sesión y datos relacionales, pero la proyección de perfiles existente todavía trata `public` como visibilidad para visitantes anónimos y no tiene una relación de amistad que habilite el acceso. [VERIFIED: apps/api/accounts/serializers.py:86-139; apps/api/accounts/views.py:281-305; apps/api/accounts/models.py:77-128]

La recomendación principal es crear un módulo Django `social` separado, con servicios transaccionales y querysets de visibilidad centralizados. Debe almacenar el estado actual de amistad/bloqueo y conservar el historial de solicitudes suficiente para distinguir rechazar, eliminar y bloquear. Las proyecciones sociales no deben reutilizar directamente los DTOs privados de `library`: hay que construir DTOs específicos para amigos que incluyan únicamente juego, portada, año, plataforma, estado y rating, y que preserven el orden de `CustomListItem`. [ASSUMED]

Para el catálogo, hay que ampliar el contrato backend completo de `CAT-05` ahora, aunque la selección visual quede para diseño. `GameWork` ya cubre casi todas las dimensiones mediante relaciones, pero no existe una relación de publishers en el modelo abierto durante esta sesión; `Edition` existe anidada bajo `GameRelease`, por lo que filtros y facets deben definir expresamente cómo se proyecta. [VERIFIED: apps/api/catalogue/models.py:16-157; apps/api/catalogue/models.py:218-370] La fase debe rebaselinar `.planning/ROADMAP.md` y `.planning/REQUIREMENTS.md`: el roadmap solo enumera `PROF-03`, `PROF-04` y `CAT-05`, mientras que los requisitos actuales aún describen `SOCIAL-01`/`SOCIAL-02` como v2 y declaran fuera de alcance una red social completa. [VERIFIED: .planning/ROADMAP.md:276-292; .planning/REQUIREMENTS.md:126-156,220-232]

**Recomendación primaria:** ejecutar una migración aditiva para `social`, hacer que toda lectura de contenido social pase por una política backend de visibilidad con respuesta indistinguible `404`, y ampliar `catalogue/search.py` como único punto de consulta/facets sin añadir paquetes ni proveedores externos al ciclo HTTP. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:209-229; .planning/codebase/ARCHITECTURE.md; apps/api/catalogue/search.py:1-19]

## Architectural Responsibility Map

| Capacidad | Tier primario | Tier secundario | Razonamiento |
|---|---|---|---|
| Resolver amistad, bloqueo, solicitudes y cooldown | API / Backend | Database / Storage | El servidor conoce `request.user` y las relaciones verificadas; PostgreSQL debe respaldar invariantes y concurrencia. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:47-59; apps/api/accounts/views.py:224-249] [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/] |
| Proyectar perfil, colección, listas y comentarios | API / Backend | Database / Storage | La allowlist y la decisión de visibilidad pertenecen al backend; la base de datos aporta joins filtrados. [VERIFIED: apps/api/accounts/serializers.py:1-8,86-139; apps/api/library/serializers.py:176-267] [CITED: https://www.django-rest-framework.org/api-guide/permissions/] |
| URL compartible de perfil/lista | Frontend Server (SSR) | API / Backend | Next resuelve segmentos dinámicos y reenvía la sesión; Django vuelve a autorizar la URL directa. [CITED: https://nextjs.org/docs/app/getting-started/layouts-and-pages] [VERIFIED: apps/web/app/[locale]/profiles/[alias]/page.tsx:1-50; apps/web/lib/api.ts:229-239] |
| Mensajes privados y badge pendiente | API / Backend | Browser / Client | El servidor determina recibidos/no leídos; el cliente solo presenta el resultado y ejecuta mutaciones con CSRF. [VERIFIED: apps/web/lib/client-api.ts:1-47; apps/web/components/AccountSwitcher.tsx:80-149] [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html] |
| Filtros, facets y paginación de catálogo | API / Backend | Browser / Client | El backend valida, filtra y ordena; la interfaz conserva el estado en GET y solo decide qué controles mostrar. [VERIFIED: apps/api/catalogue/search.py:94-239,290-427; apps/web/app/[locale]/catalogue/page.tsx:34-74; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45] |
| Importación/enrichment reproducible | Database / Storage | API / Backend | Los datos de descubrimiento deben proceder del corpus/snapshot local; la petición web no llama a proveedores externos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229; .planning/codebase/INTEGRATIONS.md] |

## Roadmap and Requirements Reconciliation

1. El plan debe comenzar con una tarea **Wave 0** que actualice el alcance trazable: añadir requisitos sociales nuevos con IDs propios para solicitudes/amistades/bloqueos, proyección de amigos, mensajes/recomendaciones y badge. Los nombres de esos IDs son una decisión pendiente y cualquier propuesta concreta es `[ASSUMED]`; no se deben reutilizar silenciosamente `SOCIAL-01` y `SOCIAL-02`, porque actualmente describen “follow”, activity feed y reacciones de v2. [VERIFIED: .planning/REQUIREMENTS.md:126-139]
2. Debe actualizarse la descripción y los criterios de éxito de Phase 6 en `.planning/ROADMAP.md` para incluir el módulo social, y retirar o matizar la fila “Full social network in v1” de Out of Scope para que no contradiga el alcance autorizado. [VERIFIED: .planning/ROADMAP.md:276-292; .planning/REQUIREMENTS.md:146-156; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:245-251]
3. `CAT-02` aparece trazado a Phase 01.1 en el roadmap, pero el contexto bloquea que `CAT-05` se reduzca a esa implementación y pide ampliar el backend de filtros. El plan debe aclarar si `CAT-02` se considera capacidad heredada extendida por Phase 6 o si se añade una referencia cruzada, sin cambiar las snapshots de evaluación. [VERIFIED: .planning/ROADMAP.md:13,276-292; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45,228-229]
4. `PROF-03` debe rebaselinarse para que “public” signifique visible dentro de una amistad aceptada, no anónimamente. La redacción debe separar perfil básico de contenido social autorizado y debe enumerar explícitamente la ausencia de copias, compras, precios, tiendas, ubicaciones, notas e IDs internos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-83; apps/api/accounts/serializers.py:1-8]

## Standard Stack

### Core

| Tecnología | Versión existente | Uso en esta fase | Razón |
|---|---:|---|---|
| Django | `5.2.17` | Modelos sociales, migraciones, servicios, sesiones y transacciones | Es la versión declarada por el proyecto y la fase ya usa ORM/migraciones Django. [VERIFIED: pyproject.toml:1-13; apps/api/config/settings.py:23-45] |
| Django REST framework | `3.18.0` | Endpoints, autenticación, serializers, permisos y throttling | El backend ya usa `SessionAuthentication`, vistas DRF y scopes de throttle. [VERIFIED: pyproject.toml:1-13; apps/api/config/settings.py:110-149; apps/api/accounts/views.py:64-72] |
| PostgreSQL | `18.6` | Persistencia de relaciones, constraints, índices y mensajes | Es la base de datos declarada por Compose y la integración de la aplicación. [VERIFIED: infra/compose.yaml:4-10; apps/api/config/settings.py:110-149] |
| Next.js App Router | `16.3.4` | Páginas SSR de perfil, lista y mensajes, navegación y URLs GET | El frontend existente usa Server Components, segmentos dinámicos y proxy same-origin. [VERIFIED: package.json:5-8; apps/web/app/[locale]/profiles/[alias]/page.tsx:1-50; apps/web/lib/api.ts:229-239] |
| React / React DOM | `19.2.7` | Componentes accesibles de perfil, social e inbox | Es la versión ya fijada en el root package. [VERIFIED: package.json:9-12] |
| TypeScript | `6.0.3` | DTOs, filtros, estados de relación y respuestas del inbox | El proyecto fija TypeScript y mantiene tipos de API en `apps/web/lib/api.ts`. [VERIFIED: package.json:17-22; apps/web/lib/api.ts:1-68] |

### Supporting

| Herramienta | Uso prescriptivo | Evidencia |
|---|---|---|
| `transaction.atomic()` | Agrupar aceptar/rechazar/eliminar/bloquear y crear recomendación con sus comprobaciones; mantener el bloque corto. | La documentación oficial indica atomicidad completa y recomienda transacciones cortas. [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/] |
| `UniqueConstraint` / `CheckConstraint` | Respaldar una amistad canónica por pareja, solicitudes pendientes únicas y pares no autorrelacionados. | Django documenta `UniqueConstraint` y restricciones condicionales. [CITED: https://docs.djangoproject.com/en/5.2/ref/models/constraints/] |
| `SessionAuthentication` + CSRF | Mantener la sesión existente y usar `client-api.ts` para mutaciones. | Está configurado en DRF y el cliente ya obtiene el token CSRF para métodos mutantes. [VERIFIED: apps/api/config/settings.py:110-149; apps/web/lib/client-api.ts:1-47] |
| `pytest` + `pytest-django` | Pruebas de transición, autorización, constraints, filtros y migraciones contra PostgreSQL. | Versiones y configuración existen en `pyproject.toml` y `apps/api/pytest.ini`. [VERIFIED: pyproject.toml:14-30; apps/api/pytest.ini:1-7] |
| Testing Library + Playwright | Pruebas por rol/estado para componentes y flujos sociales de navegador. | El proyecto fija ambos toolsets y Playwright usa `e2e/` con Chromium. [VERIFIED: package.json:13-22; playwright.config.ts:1-20] |

**Instalación:** no se recomienda instalar ningún paquete nuevo. La fase debe reutilizar el stack fijado y resolver el trabajo mediante código, migraciones y pruebas. [VERIFIED: pyproject.toml:1-30; package.json:1-32]

**Package Legitimacy Audit:** omitido porque esta fase no propone dependencias externas nuevas. [VERIFIED: Standard Stack de esta investigación]

## Architecture Patterns

### System Architecture Diagram

```text
Browser
  ├─ GET /[locale]/profiles/[alias] or /lists/[id]
  │     └─ Next.js Server Component ── Cookie ──> Django/DRF
  │                                               ├─ resolve viewer
  │                                               ├─ check block/friendship/owner
  │                                               ├─ filtered PostgreSQL queryset
  │                                               └─ manual allowlist DTO ──> SSR HTML
  ├─ GET /[locale]/messages
  │     └─ Next.js SSR ── Cookie ──> private inbox queryset ──> HTML
  └─ POST friendship/message/read
        └─ same-origin client-api.ts ── CSRF ──> Django service
                                              ├─ authorization
                                              ├─ transaction.atomic()
                                              └─ PostgreSQL commit

Catalogue GET filters
  └─ Next GET query string ──> local catalogue/search.py
                              ├─ allowlist + bounds
                              ├─ all CAT-05 joins/facets
                              └─ deterministic ordering/page

Offline enrichment/import
  └─ approved snapshot/API runner ──> PostgreSQL corpus + SourceRecord
                                      (never in the web request path)
```

El flujo conserva la separación existente entre frontend desacoplado, API Django y PostgreSQL, y mantiene el enrichment fuera del ciclo HTTP. [VERIFIED: .planning/codebase/ARCHITECTURE.md; .planning/codebase/INTEGRATIONS.md; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229]

### Recommended Project Structure

```text
apps/api/social/
├── __init__.py
├── apps.py
├── models.py              # estado social y mensajes
├── permissions.py         # permisos reutilizables, si son necesarios
├── policies.py            # resolución de visibilidad y 404 indistinguible
├── serializers.py         # DTOs sociales manuales
├── services.py            # transiciones y cooldown transaccionales
├── urls.py
├── views.py
└── migrations/

apps/api/tests/
└── test_social.py

apps/web/app/[locale]/
├── messages/page.tsx
├── profiles/[alias]/page.tsx
└── lists/[id]/page.tsx

apps/web/components/
├── SocialActions.tsx
├── SocialInbox.tsx
└── AccountSwitcher.tsx

apps/web/lib/
├── social.ts
└── api.ts

apps/web/tests/
└── social.test.ts

e2e/
└── social-workflows.spec.ts
```

La ubicación de app, views, urls, tests y páginas sigue la estructura detectada en el repositorio; los nombres nuevos son propuestas de implementación y por tanto `[ASSUMED]`. [VERIFIED: .planning/codebase/STRUCTURE.md; apps/api/accounts/urls.py:16-24; apps/api/library/urls.py:24-40; playwright.config.ts:1-20]

### Pattern 1: Social state as explicit domain transitions

**Qué:** tratar `accept`, `reject`, `remove`, `block`, `send_recommendation` y `mark_read` como comandos de servicio, no como cambios directos de campos recibidos del cliente. Cada comando deriva los usuarios desde `request.user`, valida la relación actual, ejecuta los cambios necesarios en una transacción y devuelve un DTO seguro. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:49-59,99-107; apps/api/accounts/views.py:224-249] [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]

**Cuándo usarlo:** siempre que una acción cambie una relación o cree acceso; no permitir `owner_id`, `sender_id` o `recipient_id` como autoridad del request. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:211-218; apps/api/accounts/views.py:224-249]

**Diseño recomendado:** una amistad actual con pareja canónica ordenada, solicitudes dirigidas que conserven el resultado histórico y bloqueos dirigidos únicos. Un `block` debe cancelar solicitudes, eliminar la amistad y hacer que todas las políticas posteriores oculten mutuamente perfil y contenido. La pareja canónica y el índice de solicitudes evitan duplicados; `transaction.atomic()` evita estados parciales. [ASSUMED] [CITED: https://docs.djangoproject.com/en/5.2/ref/models/constraints/] [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]

### Pattern 2: Policy-first querysets and manual projections

**Qué:** resolver primero una política `(viewer, owner, resource)` que produzca `owner`, `accepted_friend`, `basic`, o `hidden`; después construir el queryset ya filtrado y serializar una allowlist específica. Para colecciones y listas de amigos, no reutilizar `serialize_list` ni `serialize_comment`, porque los DTOs de propietario contienen IDs, versiones, visibilidad y campos que no son públicos. [VERIFIED: apps/api/accounts/serializers.py:1-8,86-174; apps/api/library/serializers.py:176-267]

**Cuándo usarlo:** en perfil, lista directa, comentarios de juego, colección de un amigo, inbox y cualquier endpoint que acepte un identificador compartible. DRF advierte que los permisos de objeto no se aplican automáticamente a cada elemento de una lista, por lo que el queryset debe estar restringido antes de serializar. [CITED: https://www.django-rest-framework.org/api-guide/permissions/]

**Respuesta no autorizada:** resolver “no existe”, “no autenticado”, “no amigo” y “bloqueado” como el mismo `404` genérico para rutas de contenido social. El perfil básico de un no amigo sigue la decisión D-07; el contenido social y las listas directas no deben confirmar su existencia. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-72] [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]

### Pattern 3: Separate public-basic and friend-visible DTOs

**Qué:** mantener dos contratos explícitos: perfil básico (`alias`, `avatar`, `bio` y una acción derivada para solicitar) y proyección autorizada de amigo (contenido permitido). Para una colección/lista amiga, cada item debe contener juego, cover, year, platform, backlog status y personal rating; para comentarios, alias, text y date. Excluir copies, purchases, prices, stores, locations, private notes, ownership and internal IDs. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-83]

**Cuándo usarlo:** siempre que un endpoint pueda ser invocado por más de un actor. No añadir campos “por conveniencia” al DTO de `build_public_profile`, porque el serializer actual ya usa una allowlist manual y la ampliación automática sería una regresión de privacidad. [VERIFIED: apps/api/accounts/serializers.py:1-8,86-139]

### Pattern 4: Rolling recommendation limit with a serialized critical section

**Qué:** guardar la recomendación como mensaje privado dirigido a una amistad, con referencia obligatoria al `GameWork`, mensaje opcional, fecha de creación y fecha de lectura. El límite se evalúa contra la misma pareja emisor-receptor y una ventana exacta de `7 * 24` horas usando `timezone.now()` aware; no es una semana de calendario ni un límite por juego. Para evitar carreras, bloquear una fila estable de la pareja dentro de `transaction.atomic()` antes de comprobar y crear. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:85-95] [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]

**Nota de diseño:** el autor permite representación interna distinta, pero la semántica debe ser direccional: un emisor puede recomendar a varias amistades y solo se bloquea el mismo emisor-receptor durante la ventana. Añadir un índice compuesto por emisor, receptor y fecha para el lookup. El nombre de la entidad de lock, el límite de texto y los nombres de campos son `[ASSUMED]` y deben quedar fijados en el plan. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:93-101] [ASSUMED]

### Pattern 5: GET is the source of truth for discovery state

**Qué:** ampliar `CatalogueQuery`, el parser, los filtros y facets del backend; en el frontend, propagar cada filtro permitido como parámetro GET repetible y conservarlo al paginar. Reutilizar el orden total determinista, límites y rechazo de parámetros desconocidos ya existentes. [VERIFIED: apps/api/catalogue/search.py:56-239,366-427; apps/web/lib/catalogue-filters.ts:14-185]

**Cuándo usarlo:** en toda búsqueda/facet compartible y en enlaces desde una lista social al detalle de juego. La UI puede ocultar o agrupar facets después de diseño, pero el contrato backend de D-01 no debe depender de esa decisión. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45,240-251]

### Anti-Patterns to Avoid

- **Ampliar `build_public_profile` con campos privados:** mezcla el perfil básico y el friend projection y puede reexponer `activity`, `summary`, comentarios o listas a un no amigo. Crear contratos separados. [VERIFIED: apps/api/accounts/serializers.py:86-139; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-83]
- **Confiar en que el frontend protege una lista compartida:** un usuario puede invocar directamente la URL o API; autorizar cada request y responder `404`. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]
- **Usar un `AllowAny` heredado para comentarios/listas sociales:** `WorkCommentsView` actualmente acepta GET anónimo y filtra comentarios públicos del modelo existente; Phase 6 debe sustituir ese alcance para la proyección social. [VERIFIED: apps/api/library/views.py:321-356; apps/api/library/models.py:159-203]
- **Comprobar el cooldown y crear fuera de una transacción:** dos requests concurrentes pueden pasar la comprobación y duplicar el envío. [ASSUMED] [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]
- **Llamar al proveedor externo desde perfil, búsqueda o detalle:** rompe el límite offline/local, introduce drift de datos y hace no reproducible la vista. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229]
- **Hacer que el punto rojo dependa solo del color:** el indicador necesita nombre accesible/estado textual y debe funcionar con teclado, móvil y sin JavaScript cuando sea viable. [VERIFIED: apps/web/components/AccountSwitcher.tsx:51-149; .planning/codebase/CONVENTIONS.md; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]]

## Catalogue Discovery and Resilient Enrichment

### Current coverage and gaps

`GameWork` ya contiene relaciones para `genres`, `franchises`, `developers`, `themes`, `player_perspectives`, `game_modes`, `keywords`, `subgenres` y `curated_labels`; `GameRelease` enlaza `Platform` y `Edition`. `SourceRecord` conserva source, source ID, URL, retrieval time, licence y snapshot hash. [VERIFIED: apps/api/catalogue/models.py:112-157,175-263,312-370,432-455]

El contrato actual de búsqueda solo modela `q`, `tags`, `platforms`, rango de años, rating y sort; los facets actuales son `platforms`, `tags` y `year_range`, y el parser limita cada multi-select a 20 valores. [VERIFIED: apps/api/catalogue/search.py:56-58,94-202,290-320] El plan debe ampliar de forma aditiva a `editions`, `genres`, `franchises`, `developers`, `publishers`, `dates`, `modes` y `tags`, manteniendo los límites y la ordenación determinista. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45]

`Publisher` no aparece en las definiciones de modelo abiertas en esta sesión, por lo que `CAT-05` no está completo aunque el resto de relaciones cubra gran parte del requisito. El plan debe decidir una entidad `Publisher` y una relación a `GameWork`, además de actualizar el importer, serializers, facets, filtros, fixtures y pruebas; esta es una recomendación de diseño `[ASSUMED]`, no un valor existente del repositorio. [VERIFIED: apps/api/catalogue/models.py:16-370; [ASSUMED]]

### Filter contract

Usar nombres de parámetros explícitos y repetibles, por ejemplo `platform=...&platform=...`, y una allowlist centralizada compartida por parser, facets, URL builder y tests. Mantener `platforms` como unión de seleccionados porque ya existe ese comportamiento; para cada nueva facet hay que fijar en el plan si el operador es OR dentro de la facet y AND entre facets. La recomendación conservadora es preservar los semántica actual: plataformas OR, tags/taxonomías encadenadas como AND, fechas como rango, y editions como OR sobre releases; no cambiar tags/genres sin actualizar tests existentes. [VERIFIED: apps/api/catalogue/search.py:119-239; [ASSUMED]

Las facets deben calcularse sobre el corpus gobernado y la consulta base antes de pagination, incluir `slug`, label y count determinista, y evitar consultas N+1. Los valores desconocidos deben seguir la política existente del parser —los slugs desconocidos se descartan en el filtro—, mientras que sort y límites inválidos deben continuar respondiendo `400`. [VERIFIED: apps/api/catalogue/search.py:148-239,290-320; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:209-218]

### Enrichment boundary

La expansión de metadata debe alimentar el catálogo local mediante el runner/importer aprobado y registrar la procedencia en `SourceRecord`; no debe alterar los `snapshots` ni los artefactos offline de evaluación. Si una fuente externa falla, la aplicación debe servir el último snapshot local gobernado o reportar ausencia de enrichment en una operación offline, nunca bloquear una petición de catálogo por una llamada live. [VERIFIED: apps/api/catalogue/models.py:432-455; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229; .planning/codebase/INTEGRATIONS.md]

## Social Data Model and Privacy Boundaries

### Prescriptive relational shape

Se recomienda separar `social` de `accounts` y `library` para que las relaciones, políticas y mensajes no se mezclen con el perfil de identidad ni con los DTOs de inventario. [ASSUMED]

| Entidad propuesta | Invariantes y comportamiento |
|---|---|
| `Friendship` | Pareja no ordenada canónica, sin autorrelación, una fila por amistad actual. Crear solo al aceptar; eliminar revoca acceso. [ASSUMED] |
| `FriendshipRequest` | `sender` y `receiver` dirigidos, estado/historial auditable, solicitud pendiente única por dirección. Rechazo conserva ausencia de relación y permite otra solicitud futura. [ASSUMED] |
| `Block` | `blocker` y `blocked` dirigidos, único por dirección. Bloquear cancela requests, elimina friendship, revoca acceso y oculta ambos perfiles/contenido. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:49-59] [ASSUMED] |
| `SocialMessage` | `sender`, `recipient`, `work`, cuerpo opcional, `created_at`, `read_at` y tipo recommendation; solo entre amistades aceptadas. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:85-95] [ASSUMED] |
| Badge | Derivar unread messages y pending friend requests desde querysets autenticados; no exponer un contador de otro usuario. Una entidad Notification adicional no es necesaria para el alcance actual. [ASSUMED] |

Usar `UniqueConstraint` y `CheckConstraint` donde expresen invariantes estáticos; usar servicios transaccionales para las transiciones que tocan varias tablas. Django documenta que `UniqueConstraint` se traduce en una restricción de base de datos y que `atomic()` garantiza commit/rollback del bloque. [CITED: https://docs.djangoproject.com/en/5.2/ref/models/constraints/; [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]]

### Visibility matrix

| Actor | Perfil básico | Collection/list | Comments on game | Inbox |
|---|---|---|---|---|
| Owner | Full own projection | Own data | Own permitted view | Own received/sent messages |
| Accepted friend | Alias/avatar/bio + friend projection | Only explicitly shareable content and allowed fields | Alias/text/date when permitted | Only messages addressed to viewer |
| Authenticated non-friend | Basic profile + eligible request action | `404` / no content | No social comments | No content |
| Anonymous | Basic profile only, without private action execution | `404` / no content | No social comments | Redirect/auth boundary |
| Blocked or blocker | Indistinguishable hidden profile | `404` / no content | No social comments | No content |

Esta tabla es la traducción operativa de D-06–D-14; “basic profile” no debe confundirse con acceso a la colección llamada `public`. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:61-95]

### Direct URL behavior

La ruta de perfil existente es `AllowAny` y busca alias exacto antes de llamar a `build_public_profile`; esa conducta es compatible únicamente con la proyección básica para anónimos/no amigos. La ruta futura de lista debe ser autenticada y resolver autorización de recurso en backend, sin confiar en un enlace previo desde el perfil. [VERIFIED: apps/api/accounts/views.py:281-305; apps/api/accounts/urls.py:16-24; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:69-72]

Para un `404` genérico, no incluir en cuerpo, headers diferenciadores o tiempos fácilmente distinguibles si el recurso existe pero está oculto. En listas DRF, filtrar por owner/friendship/block antes de resolver el objeto; el objeto no autorizado no debe llegar al serializer. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html; [CITED: https://www.django-rest-framework.org/api-guide/permissions/]]

## Frontend Integration and Mobile Behavior

`profiles/[alias]/page.tsx` es un Server Component que ya carga el perfil y renderiza favorites, summary, activity, comments y lists; debe pasar el `Cookie` entrante al fetch autenticado y renderizar estados básicos, friend-visible, hidden y not-found sin asumir que una respuesta anónima contiene actividad. [VERIFIED: apps/web/app/[locale]/profiles/[alias]/page.tsx:1-215; apps/web/lib/api.ts:191-239]

Añadir la bandeja a `AccountSwitcher` y al propio menú de navegación sin romper el focus trap existente. El punto rojo debe acompañar un texto/label accesible como estado (“mensajes o solicitudes pendientes”), no ser la única señal; el endpoint del badge debe devolver solo agregados del usuario autenticado. La interfaz de mensajes debe tener una ruta propia, navegación de vuelta al perfil/juego y acciones `mark_read` protegidas por CSRF. Los nombres exactos son `[ASSUMED]`. [VERIFIED: apps/web/components/AccountSwitcher.tsx:51-149; apps/web/components/AppShell.tsx:21-31,89-172; apps/web/lib/client-api.ts:1-47; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]]

El “límite móvil de recomendaciones” se interpreta aquí como una ventana móvil temporal de siete días, no como una restricción de viewport. Debe probarse en móvil la bandeja y el flujo de recomendación, pero la regla de negocio es UTC-aware, direccional y de `7 * 24` horas. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:93-95; [ASSUMED]]

La middleware actual decide coarse auth por presencia de `sessionid` y mantiene `/profiles` como ruta pública; por eso no puede ser la autoridad de privacidad. Debe añadir las rutas privadas de social/messages al guard grueso, pero el API debe seguir autorizando cada recurso y el SSR debe reenviar cookies. [VERIFIED: apps/web/middleware.ts:3-59; apps/web/lib/api.ts:229-239; [CITED: https://nextjs.org/docs/app/api-reference/functions/cookies]]

## Don't Hand-Roll

| Problema | No construir | Usar | Motivo |
|---|---|---|---|
| Transiciones multi-tabla | flags independientes en views | servicios Django + `transaction.atomic()` | Evita amistad creada sin request, bloqueo sin revocación o cooldown duplicado. [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/] |
| Autorización de colección/lista | `owner_id` del cliente o ocultación de URL | `request.user`, política de relación y queryset filtrado | OWASP exige deny-by-default y comprobación por request. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html] |
| DTO público | serializar el modelo completo | serializers/proyecciones allowlist manuales | Los modelos de `library` contienen precio, tienda, localización, notas e IDs. [VERIFIED: apps/api/library/models.py:92-203; apps/api/library/serializers.py:230-267] |
| CSRF | token propio o desactivar protección | `client-api.ts` + endpoint CSRF existente | El stack ya usa sesiones/CSRF y OWASP recomienda tokens para requests con cookies. [VERIFIED: apps/web/lib/client-api.ts:1-47; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]] |
| Cooldown concurrente | solo `latest()` seguido de `create()` | lock estable + `atomic()` + índice compuesto | La comprobación aislada no expresa por sí sola la exclusión de dos writers. [ASSUMED; [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]] |
| Filtros de catálogo | estado React paralelo a la URL | `catalogue/search.py` + query string GET | Ya existen parser, allowlists, límites y orden determinista. [VERIFIED: apps/api/catalogue/search.py:56-239; apps/web/lib/catalogue-filters.ts:35-185] |
| Notificaciones externas | email/webhooks/realtime provider | inbox local y badge derivado | El contexto prohíbe correo y el alcance exige entorno local/reproducible. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:85-95; .planning/codebase/INTEGRATIONS.md] |

## Common Pitfalls

### Pitfall 1: `public` se interpreta como anónimo

**Qué ocurre:** el perfil actual expone la proyección `PUBLIC` a cualquier viewer según visibilidad de `AccountProfile`, y `WorkCommentsView` acepta GET anónimo. [VERIFIED: apps/api/accounts/serializers.py:86-139; apps/api/library/views.py:321-356]

**Cómo evitarlo:** separar `basic` de `friend-visible`, cambiar las consultas de contenido a relación aceptada y cubrir anonymous/non-friend/blocked con tests de respuesta y campos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-83]

### Pitfall 2: autorizar la pantalla pero no la URL/API

**Qué ocurre:** un enlace compartido permite saltarse la navegación previa; la middleware solo realiza una comprobación gruesa de sesión. [VERIFIED: apps/web/middleware.ts:21-59; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:69-72]

**Cómo evitarlo:** política de recurso en cada GET directo y `404` genérico para no autorizado. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]

### Pitfall 3: filtrar secretos de inventario a través de “game data”

**Qué ocurre:** reusar `OwnedCopy` o DTO de owner puede exponer formato, fecha/price/currency, store, conservation o storage, aunque la tarjeta visual parezca solo un juego. [VERIFIED: apps/api/library/models.py:92-156; apps/api/library/serializers.py:230-249]

**Cómo evitarlo:** serializer de amigo con allowlist explícita y test que compruebe ausencia de cada campo prohibido, no solo presencia de los permitidos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:73-80]

### Pitfall 4: carrera en el límite de siete días

**Qué ocurre:** dos requests paralelos pueden comprobar el mismo vacío y crear dos recomendaciones. Esto es una consecuencia de concurrencia de una comprobación seguida de escritura y debe tratarse como riesgo de diseño `[ASSUMED]`.

**Cómo evitarlo:** lock por pareja estable, `atomic()`, índice `(sender, recipient, created_at)` y test de frontera antes, exactamente en y después de `7 * 24` horas. [ASSUMED; [CITED: https://docs.djangoproject.com/en/5.2/topics/db/transactions/]]

### Pitfall 5: re-request o block queda en estado ambiguo

**Qué ocurre:** una sola fila booleana no distingue reject, remove y block, y puede impedir una solicitud legítima posterior o dejar acceso residual. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:54-59]

**Cómo evitarlo:** modelar estado actual separado de historial dirigido; probar la matriz completa de transiciones. La forma exacta es `[ASSUMED]`.

### Pitfall 6: CAT-05 solo cambia la UI

**Qué ocurre:** el catálogo muestra algunos controles, pero `CatalogueQuery` y facets siguen teniendo solo platform/tag/year, de modo que los enlaces de otras dimensiones no son reproducibles. [VERIFIED: apps/api/catalogue/search.py:94-102,290-320; apps/web/lib/catalogue-filters.ts:35-97]

**Cómo evitarlo:** implementar primero parser, querysets, facets, DTO y tests completos; dejar la selección visual a la posterior decisión de diseño. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45,240-251]

### Pitfall 7: mensajes sin escape o badge filtrando información

**Qué ocurre:** comentarios/mensajes son input no confiable y el contador puede revelar existencia de relaciones si se calcula para el usuario equivocado. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html; [ASSUMED]]

**Cómo evitarlo:** renderizar texto como texto, no usar `dangerouslySetInnerHTML`, limitar y validar el cuerpo en servidor, y calcular badge/inbox con `request.user`. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html; VERIFIED: apps/api/accounts/views.py:224-249]

## Code Examples

### Existing same-origin mutation pattern

El patrón existente debe seguir siendo la base de `accept`, `block`, `send_recommendation` y `mark_read`; no inventar un transporte paralelo. [VERIFIED: apps/web/lib/client-api.ts:1-47]

```typescript
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    headers.set("X-CSRFToken", await getCsrfToken());
  }
  return fetch(path, { ...init, headers, credentials: "same-origin" }).then(
    async (response) => {
      if (!response.ok) throw new Error(`Request failed: ${response.status}`);
      return (await response.json()) as T;
    },
  );
}
```

La forma anterior conserva literalmente los verbos y cabeceras del helper existente, incluida la protección CSRF para métodos mutantes. [VERIFIED: apps/web/lib/client-api.ts:1-47]

### Existing deterministic GET query pattern

```typescript
const params = new URLSearchParams();
for (const value of filters.platform) params.append("platform", value);
for (const value of filters.tag) params.append("tag", value);
if (filters.yearFrom) params.set("year_from", String(filters.yearFrom));
if (filters.yearTo) params.set("year_to", String(filters.yearTo));
const href = `/catalogue?${params.toString()}`;
```

El ejemplo representa el patrón de parámetros repetibles y estado derivado de URL ya existente; las nuevas facets deben añadirse a la misma allowlist, no a un estado client-only. [VERIFIED: apps/web/lib/catalogue-filters.ts:150-185; apps/web/app/[locale]/catalogue/page.tsx:34-74]

### Existing profile allowlist boundary

```python
return {
    "alias": username,
    "bio": profile.bio,
    "avatar_url": profile.avatar_url,
    "activity": activity,
    "summary": summary,
    "favorites": favorites,
    "comments": comments,
    "lists": lists,
}
```

Este retorno debe dividirse en una proyección básica y una proyección de amigo antes de introducir campos sociales; los nombres mostrados son valores existentes y están citados desde la definición abierta durante esta sesión. [VERIFIED: apps/api/accounts/serializers.py:130-138]

## Migrations and Verification Plan

La fase necesita una migración nueva para `social` y probablemente una migración de catálogo para `Publisher` y sus relaciones. Deben ser aditivas y ejecutarse antes de seed/demo; no editar migraciones aplicadas ni cambiar el esquema de evaluación congelado. [VERIFIED: infra/compose.yaml:82-99; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:228-229; [ASSUMED]]

Orden recomendado para el plan:

1. Rebaselinar roadmap/requisitos y fijar los IDs sociales. [VERIFIED: .planning/ROADMAP.md:276-292; .planning/REQUIREMENTS.md:126-156]
2. Crear modelos/constraints/índices y migraciones, incluyendo fixture mínima sin credenciales. [ASSUMED]
3. Implementar policy/service/querysets y serializers allowlist; después views/urls. [VERIFIED: .planning/codebase/STRUCTURE.md; [ASSUMED]]
4. Extender catálogo/importer/facets/DTOs sin tocar snapshots de evaluación. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229]
5. Integrar SSR, AccountSwitcher, messages y rutas directas; finalmente completar E2E. [VERIFIED: apps/web/app/[locale]/profiles/[alias]/page.tsx:1-215; apps/web/components/AccountSwitcher.tsx:51-149; [ASSUMED]]

Comandos realistas para la fase, preferentemente dentro de los servicios Compose:

```powershell
docker compose -f infra/compose.yaml run --rm api python manage.py check
docker compose -f infra/compose.yaml run --rm api python manage.py makemigrations --check --dry-run
docker compose -f infra/compose.yaml run --rm api python manage.py migrate --plan
docker compose -f infra/compose.yaml run --rm api pytest
docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit
docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test -- --run
docker compose -f infra/compose.yaml run --rm web pnpm exec playwright test e2e/social-workflows.spec.ts --project=chromium
git diff --check
```

Los servicios `api`, `web` y `db` están definidos en `infra/compose.yaml`; el proyecto fija `pytest`, TypeScript, Vitest y Playwright, y el runner E2E usa `e2e/`/Chromium. [VERIFIED: infra/compose.yaml:4-10,82-99,233-273; pyproject.toml:14-30; package.json:13-22; playwright.config.ts:1-20] El host tiene Node `v24.13.0`, mientras que `package.json` declara `engines.node` `24.20.0`; `pnpm` no está disponible en el host, por lo que el contenedor es el camino reproducible y hay que decidir explícitamente si se actualiza Node o se flexibiliza el engine. [VERIFIED: package.json:5-8; environment probe 2026-09-13]

## Validation Architecture

### Test Framework

| Propiedad | Valor |
|---|---|
| Backend | `pytest 9.1.1` + `pytest-django 4.14.0`, configuración `apps/api/pytest.ini` [VERIFIED: pyproject.toml:14-30; apps/api/pytest.ini:1-7] |
| Frontend unit | `Vitest 5.0.0` + Testing Library `16.3.3` [VERIFIED: package.json:13-22] |
| Browser | `Playwright 1.62.1`, `e2e/`, proyecto `chromium` [VERIFIED: package.json:13-22; playwright.config.ts:1-20] |
| Quick backend | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests/test_social.py -x` [ASSUMED — confirmar ruta exacta al crear tests] |
| Full backend | `docker compose -f infra/compose.yaml run --rm api pytest` [VERIFIED: existing repository test command pattern from STATE.md; command path is operational recommendation] |
| Quick frontend | `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test -- --run social` [ASSUMED — verificar script/filtro Vitest] |
| Full browser | `docker compose -f infra/compose.yaml run --rm web pnpm exec playwright test --project=chromium` [VERIFIED: playwright.config.ts:1-20; container invocation is operational recommendation] |

### Phase Requirements → Test Map

| Req ID | Comportamiento | Tipo | Comando automatizado | Archivo |
|---|---|---|---|---|
| PROF-03 | Owner, accepted friend, non-friend, anonymous y blocked reciben exactamente la proyección autorizada. | integration/API | `pytest apps/api/tests/test_public_profile.py apps/api/tests/test_social.py -x` | Existente + Wave 0 social [VERIFIED: apps/api/accounts/serializers.py:86-139; [ASSUMED]] |
| PROF-03 | Friend collection/list nunca contiene copies, purchase data, prices, stores, locations, private notes ni internal IDs. | integration/API | `pytest apps/api/tests/test_social.py -k projection -x` | Wave 0 [ASSUMED] |
| PROF-04 | Perfil y lista directa autorizan por backend, funcionan SSR con cookie y devuelven `404` genérico en unauthorized/blocked. | E2E + API | `playwright test e2e/social-workflows.spec.ts -g "shareable"` y `pytest ... -k direct_url` | Wave 0 [ASSUMED] |
| CAT-05 | Query/facets para games, platforms, editions, genres, franchises, developers, publishers, dates, modes y tags; límites, desconocidos y orden determinista. | unit/integration | `pytest apps/api/catalogue/tests/test_search.py -x` | Extender existente [VERIFIED: apps/api/catalogue/search.py:290-427; [ASSUMED]] |
| SOCIAL-PROP-01 | Exact alias search no ofrece directorio parcial; request/accept/reject/remove/block cumplen matriz de transición. | integration/API | `pytest apps/api/tests/test_social.py -k relationship -x` | Wave 0; ID propuesto `[ASSUMED]` |
| SOCIAL-PROP-02 | Inbox privado, unread/read, badge y recommendation game+optional text; una por emisor-receptor cada ventana móvil de siete días y varias amistades permitidas. | integration/API + E2E | `pytest apps/api/tests/test_social.py -k recommendation -x`; `playwright test e2e/social-workflows.spec.ts -g "message"` | Wave 0; ID propuesto `[ASSUMED]` |
| SOCIAL-PROP-03 | Perfil/lista/comments no revelan contenido a no amigos y comentarios muestran solo alias/text/date al actor autorizado. | API + component | `pytest apps/api/tests/test_social.py -k privacy -x`; `vitest apps/web/tests/social.test.ts` | Wave 0; ID propuesto `[ASSUMED]` |

### Required backend cases

- Rechazo no crea friendship y permite nueva request; remove revoca acceso y permite re-request; block cancela requests, elimina friendship y oculta ambos sentidos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:54-59]
- Alias exacto, alias inexistente, usuario inactivo, usuario bloqueado y request parcial deben tener respuestas no enumerables. [VERIFIED: apps/api/accounts/views.py:281-305; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:49-51,69-72]
- Probar límite de recomendación justo antes, exactamente en y justo después de siete días; probar dos juegos distintos al mismo receptor y dos receptores distintos al mismo emisor. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:93-95; [ASSUMED]]
- Probar duplicate requests/blocks/friendships, self-request, reverse pending request y concurrencia de creación. [ASSUMED]
- Probar `makemigrations --check`, `migrate --plan`, `check`, constraints y que el import de catálogo no modifica snapshots de evaluación. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:228-229; [ASSUMED]]

### Required frontend and accessibility cases

- Renderizar estados owner/friend/non-friend/blocked y que un `404` no muestre contenido parcial ni controles de solicitud indebidos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-72; [ASSUMED]]
- Navegar AccountSwitcher/inbox con teclado, Escape y focus trap existente; el badge tiene nombre accesible además del color rojo. [VERIFIED: apps/web/components/AccountSwitcher.tsx:51-149; apps/web/components/AppShell.tsx:89-172; [ASSUMED]]
- Probar viewport móvil sin overflow horizontal, menú accesible y enlaces GET de catálogo conservando todos los parámetros. [VERIFIED: apps/web/app/[locale]/catalogue/page.tsx:34-74; apps/web/lib/catalogue-filters.ts:150-185; [ASSUMED]]
- Ejecutar axe sobre perfil, lista y mensajes y complementar con revisión manual de foco, contraste y lectura de mensajes. La versión actual del repositorio ya fija `axe-core` para E2E. [VERIFIED: package.json:13-22; [ASSUMED]]

### Wave 0 Gaps

- [ ] Rebaselining de `.planning/REQUIREMENTS.md` y `.planning/ROADMAP.md` para hacer trazable el social ampliado. [VERIFIED: .planning/REQUIREMENTS.md:126-156,220-232; .planning/ROADMAP.md:276-292]
- [ ] Crear `social` app, migración, constraints, índices, services y tests de aislamiento PostgreSQL. [ASSUMED]
- [ ] Decidir publisher model/import/provenance y contract de editions facets; no existe publisher en los modelos examinados. [VERIFIED: apps/api/catalogue/models.py:16-370; [ASSUMED]]
- [ ] Separar DTO básico/friend-visible y definir endpoints directos de list/comments. [VERIFIED: apps/api/accounts/serializers.py:86-139; [ASSUMED]]
- [ ] Crear fixtures sociales deterministas sin publicar credenciales y un E2E social. [VERIFIED: AGENTS.md:59-71; [ASSUMED]]
- [ ] Añadir tests frontend de badge/inbox/filtros y actualizar navegación/middleware SSR. [VERIFIED: apps/web/components/AccountSwitcher.tsx:51-149; apps/web/middleware.ts:3-59; [ASSUMED]]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Aplica | Control estándar para esta fase |
|---|---|---|
| V2 Authentication | Sí, para requests sociales y mensajes | Requerir sesión para buscar alias, mutar relaciones, leer inbox y recomendar; no aceptar identidad del body. [VERIFIED: apps/api/config/settings.py:110-149; apps/api/accounts/views.py:224-249; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html]] |
| V3 Session Management | Sí | Mantener session cookie/CSRF existing; SSR forwards cookie; no inventar token social. [VERIFIED: apps/api/config/settings.py:151-203; apps/web/lib/client-api.ts:1-47; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]] |
| V4 Access Control | Sí, crítico | Deny-by-default, policy-first querysets, every direct URL checked, blocked/nonfriend generic `404`, tests for horizontal access. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html]] |
| V5 Input Validation | Sí, crítico | Exact alias allowlist/search, bounded repeated facets, valid `GameWork`, bounded message text, enum/state validation, no client owner IDs. [VERIFIED: apps/api/catalogue/search.py:119-202; apps/api/library/serializers.py:164-174; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html]] |
| V6 Cryptography | Sí, indirecto | No hand-roll cryptography; rely on Django session/CSRF/security settings and HTTPS avatar constraint; do not place secrets or tokens in social DTOs/logs. [VERIFIED: apps/api/config/settings.py:151-203; apps/api/accounts/serializers.py:142-162; AGENTS.md:59-71; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]] |

### Known Threat Patterns for Django/DRF/Next

| Pattern | STRIDE | Mitigación |
|---|---|---|
| BOLA/IDOR en lista o colección | Elevation/Tampering | Derivar viewer del session, filtrar queryset por friendship/block y devolver `404`; no confiar en UUID/alias como autorización. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]] |
| Enumeración de usuarios/recursos | Information disclosure | Alias exacto, sin búsqueda parcial, mismo `404` para inexistente/no autorizado y no exponer contadores ajenos. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:49-51,69-72; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html]] |
| CSRF en accept/block/message/read | Tampering | `SessionAuthentication`, CSRF token existente, same-origin client, no mutación por GET. [VERIFIED: apps/api/config/settings.py:110-149; apps/web/lib/client-api.ts:1-47; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]] |
| XSS en comments/messages | Tampering/Information disclosure | Texto escapado por renderizador, no HTML arbitrario ni `dangerouslySetInnerHTML`, validación server-side. [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html] |
| Spam/cooldown bypass | Denial of service/Tampering | throttle por endpoint además de regla de negocio, lock/constraint, test concurrente y límite de texto. DRF documenta throttling como control de abuso, pero no sustituye autorización. [VERIFIED: apps/api/config/settings.py:110-149; [CITED: https://www.django-rest-framework.org/api-guide/throttling/; [CITED: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html]] |

## Assumptions Log

| # | Claim | Section | Riesgo si es incorrecto |
|---|---|---|---|
| A1 | Un app Django `social` separado es la mejor frontera de ownership. | Social Data Model | Puede requerir integrar modelos en `accounts` si el autor prioriza menos apps/migraciones. |
| A2 | La amistad actual y el historial de requests se almacenan en entidades separadas. | Social Data Model | Cambia la migración, auditoría y transición reject/remove/re-request. |
| A3 | El cooldown es direccional, exacto a `7 * 24` horas y global por sender-receiver, no por juego. | Pattern 4 | Un significado distinto cambia constraints, API errors y tests. |
| A4 | Un lock row de pareja es suficiente y aceptable para serializar el envío. | Pattern 4 | Puede necesitar estrategia PostgreSQL distinta si se exige mayor concurrencia. |
| A5 | `Publisher` se añadirá como entidad y relación de `GameWork`. | Catalogue gaps | La fuente aprobada podría modelarlo como otro tipo de credit y cambiar importer/facets. |
| A6 | El badge se deriva de unread messages y pending requests, sin entidad Notification. | Frontend Integration | Una futura taxonomía de notificaciones exigiría modelo/retención adicional. |
| A7 | Los nombres de rutas, DTOs, componentes e IDs sociales propuestos no están fijados. | All | Deben convertirse en decisiones de plan/discussion antes de implementación. |
| A8 | La semántica propuesta de operadores de facets nuevas preserva tags/plataformas actuales. | Catalogue Filter contract | Puede alterar resultados y compatibilidad de URLs si el autor quiere OR uniforme. |
| A9 | El host seguirá usando contenedores para pnpm y resolverá el mismatch Node engine. | Environment | El build puede fallar localmente o necesitar actualización del runtime. |
| A10 | El límite de longitud del mensaje será acotado en servidor, pero su valor concreto aún no está decidido. | Security / SocialMessage | Sin límite, aumenta abuso, almacenamiento y carga de UI. |

## Open Questions

1. **¿Qué IDs nuevos y qué redacción oficial cubrirán el social ampliado?** El estado actual solo traza `PROF-03`, `PROF-04` y `CAT-05` a Phase 6, mientras `SOCIAL-01`/`SOCIAL-02` siguen en v2. [VERIFIED: .planning/REQUIREMENTS.md:126-139,220-232] Recomendación: resolverlo en Wave 0 y actualizar roadmap/requirements antes de dividir planes. [ASSUMED]
2. **¿Qué fuente aprobada aporta `Publisher` y qué forma tiene `Edition` en facets?** El modelo abierto no contiene `Publisher` y editions cuelgan de releases. [VERIFIED: apps/api/catalogue/models.py:312-370] Recomendación: documentar mapping, licence y snapshot antes de modificar importer. [ASSUMED]
3. **¿Se permite mostrar el perfil básico a anonymous con botón de request deshabilitado, o solo a authenticated non-friends?** D-07 define el mínimo para no amigos, pero D-06 restringe contenido social; el contrato debe fijar el caso anonymous. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-72] Recomendación: mostrar basic profile sin acción mutante a anonymous y ocultar contenido. [ASSUMED]
4. **¿Cuál es el nombre final de la ruta de lista y qué identificador compartible se admite?** El requisito exige URL pero no fija ruta/DTO. [VERIFIED: .planning/REQUIREMENTS.md:12-17; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:106-107] Recomendación: usar ID opaco/UUID existente solo como locator y nunca devolverlo en DTO friend-visible. [ASSUMED]
5. **¿Se conservarán mensajes históricos después de remove/block?** El contexto exige revocar acceso, pero no fija retention/deletion. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:54-59,99-101] Recomendación: ocultar inmediatamente por política; fijar retención y auditoría en decisión de seguridad antes de migrar. [ASSUMED]
6. **¿Qué responde la API al cooldown?** Recomendación: error validable sin revelar mensajes de otros usuarios, con retry time solo al sender autenticado; fijar código de error y contrato antes del frontend. [ASSUMED]

## Environment Availability

| Dependencia | Necesaria para | Disponible | Versión observada | Fallback |
|---|---|---|---|---|
| Python / `.venv` | Django, migraciones, pytest | ✓ | Python `3.13.15`; Django `5.2.17`; DRF `3.18.0` | Usar container `api` si diverge. [VERIFIED: environment probe 2026-09-13; pyproject.toml:1-13] |
| Node.js | Next build/typecheck | ✓ | `v24.13.0` | Actualizar/pinear al `engines.node` `24.20.0` o usar runtime del container. [VERIFIED: environment probe 2026-09-13; package.json:5-8] |
| pnpm | frontend scripts | ✗ host | No encontrado en host | Ejecutar mediante `docker compose ... run --rm web pnpm ...`, como el servicio web ya hace en Compose. [VERIFIED: environment probe 2026-09-13; infra/compose.yaml:233-273] |
| Docker / Compose | PostgreSQL, API, web, tests reproducibles | ✓ | Docker `29.2.1`; servicios `web`, `api`, `db` healthy en la probe | — [VERIFIED: environment probe 2026-09-13; infra/compose.yaml:4-10] |
| Proveedor social externo / realtime | — | No requerido | — | No añadirlo; alcance explícitamente local y sin realtime externo. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:85-95; .planning/codebase/INTEGRATIONS.md] |

**Missing dependencies with no fallback:** ninguno para el alcance local identificado. [VERIFIED: environment probe 2026-09-13]

**Missing dependencies with fallback:** host `pnpm`; usar el servicio `web`. El mismatch de Node debe quedar como checkpoint del plan, no asumirse resuelto. [VERIFIED: environment probe 2026-09-13; package.json:5-8]

## State of the Art

| Enfoque anterior del repositorio | Enfoque requerido en Phase 6 | Impacto |
|---|---|---|
| `AccountProfile.collection_visibility` binario `PUBLIC/PRIVATE` | Política de perfil básico + accepted-friend projection + block | No mapear `PUBLIC` directamente a anonymous; conservarlo como preferencia de compartir dentro de la nueva policy. [VERIFIED: apps/api/accounts/models.py:77-128; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-83] |
| `build_public_profile` único | DTOs separados por actor | Reduce riesgo de ampliar accidentalmente el allowlist. [VERIFIED: apps/api/accounts/serializers.py:86-139; [ASSUMED]] |
| `WorkCommentsView` GET `AllowAny` | comentarios por game page condicionados por relationship | Alinea el endpoint con D-06/D-11. [VERIFIED: apps/api/library/views.py:321-356; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-80] |
| facets platform/tag/year | contrato backend completo `CAT-05` | UI posterior puede ser menor, pero API/facets no. [VERIFIED: apps/api/catalogue/search.py:290-320; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-45] |
| navegación de cuenta sin inbox | AccountSwitcher + messages page + accessible pending indicator | Añade una superficie privada sin proveedor de email/realtime. [VERIFIED: apps/web/components/AccountSwitcher.tsx:102-149; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:85-95] |

**Deprecated/outdated for this phase:** tratar cualquier contenido `public` como anónimo y considerar el social como v2 contradice el contexto actual. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:63-95; .planning/REQUIREMENTS.md:126-156]

## Project Constraints (from AGENTS.md)

- La prosa nueva de `.planning/**` debe estar en español; identifiers, comments de código, tests, logs, commits, paths, IDs, URLs, variables y comandos conservan sus formas establecidas. [VERIFIED: AGENTS.md:20-34; CONVENTIONS.md:9-18]
- Mantener reproducibilidad académica, procedencia/licencia de datos, entorno local documentado, audiencia controlada, accesibilidad/responsive y ausencia de secretos en documentos, logs, issues o commits. [VERIFIED: AGENTS.md:4-18,59-71]
- Usar PostgreSQL en integración y producción; no introducir SQLite para hacer pasar las pruebas. [VERIFIED: .planning/codebase/STACK.md; .planning/codebase/ARCHITECTURE.md]
- No realizar llamadas de proveedores externos en request; los importers/enrichment son offline y deben conservar snapshots de investigación. [VERIFIED: .planning/codebase/INTEGRATIONS.md; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-229]
- Toda proyección pública es allowlist manual y debe fallar cerrada; no confiar en IDs de propietario enviados por el cliente. [VERIFIED: AGENTS.md:4-18; .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:207-218]
- Las dependencias nuevas requieren aprobación explícita, legitimidad y verificación; esta investigación recomienda cero paquetes nuevos. [VERIFIED: CONVENTIONS.md:59-71]
- Antes de editar documentos se inició el contexto GSD mediante `init.phase-op`; el artefacto de investigación debe quedar en la ruta de fase y el workflow posterior reconciliará issues/planes. [VERIFIED: init.phase-op output; AGENTS.md:95-119]

## Sources

### Primary / repository sources (HIGH for observed code)

- `.planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md` — decisiones D-01 a D-15, alcance social, límites de privacidad y frontera local/offline. [VERIFIED: file read this session]
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` — requisitos trazados, desajustes de alcance e historial de fases. [VERIFIED: files read this session]
- `apps/api/accounts/{models.py,serializers.py,views.py,urls.py}` — perfil, allowlist, sesión y endpoint actual de perfil. [VERIFIED: files read this session]
- `apps/api/library/{models.py,serializers.py,views.py,urls.py}` — comentarios, listas, copias, DTOs privados y orden manual. [VERIFIED: files read this session]
- `apps/api/catalogue/{models.py,search.py,serializers.py,views.py,urls.py}` — dimensiones, procedencia, filtros, facets, DTOs y orden determinista. [VERIFIED: files read this session]
- `apps/web/{app/[locale]/profiles/[alias]/page.tsx,components/AccountSwitcher.tsx,lib/api.ts,lib/client-api.ts,middleware.ts}` — SSR, auth proxy, CSRF, menú, perfiles y filtros. [VERIFIED: files read this session]
- `pyproject.toml`, `package.json`, `infra/compose.yaml`, `playwright.config.ts` — versiones, contenedores y comandos de validación. [VERIFIED: files read this session]

### Official documentation (MEDIUM: fetched through web fallback; authoritative content)

- [Django database transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) — `atomic()`, autocommit, locks/short transactions y `on_commit()`. [CITED: URL]
- [Django model constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) — `UniqueConstraint`, constraints condicionales y restricciones de modelo. [CITED: URL]
- [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/) — object-level permissions, queryset filtering en listas y política explícita. [CITED: URL]
- [DRF throttling](https://www.django-rest-framework.org/api-guide/throttling/) — throttling de endpoints como control complementario contra abuso. [CITED: URL]
- [Next.js layouts and pages](https://nextjs.org/docs/app/getting-started/layouts-and-pages) — segmentos dinámicos y `searchParams` en Server Components. [CITED: URL]
- [Next.js cookies](https://nextjs.org/docs/app/api-reference/functions/cookies) — lectura de cookies en App Router para forwarding SSR. [CITED: URL]
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — deny-by-default, autorización por request, no confiar en obscurity y pruebas. [CITED: URL]
- [OWASP Django REST Framework Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html) — BOLA, auth, rate limiting y default permissions. [CITED: URL]
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) — CSRF para autenticación por cookie y SameSite como defensa adicional. [CITED: URL]
- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html) — output encoding y tratamiento de input no confiable. [CITED: URL]

### Tertiary

- No se han usado fuentes terciarias para fijar decisiones de stack o privacidad. [VERIFIED: research session]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH for versions and existing integration; no packages nuevos. [VERIFIED: pyproject.toml; package.json; infra/compose.yaml]
- Architecture: MEDIUM because current boundaries are verified but the social model, route names and DTO names are recommendations `[ASSUMED]`. [VERIFIED: codebase files read this session; [ASSUMED]]
- Pitfalls/security: MEDIUM because project-specific leak paths are verified and controls are grounded in official OWASP/Django/DRF docs fetched this session. [CITED: official URLs in Sources]
- Social acceptance criteria: HIGH for author decisions D-01–D-15; LOW/MEDIUM for implementation shape until the planner fixes the assumptions. [VERIFIED: .planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md:38-107; [ASSUMED]]

**Research date:** 2026-09-13 [VERIFIED: environment_context]
**Valid until:** 2026-10-13 for stable architecture guidance; sooner for dependency/runtime versions and platform behavior. [ASSUMED]
