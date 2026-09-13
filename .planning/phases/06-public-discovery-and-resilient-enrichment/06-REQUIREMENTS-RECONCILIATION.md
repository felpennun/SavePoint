# Reconciliación de requisitos y decisiones — Fase 6

**Fecha:** 2026-09-13  
**Fuente funcional:** [`06-CONTEXT.md`](./06-CONTEXT.md)  
**Fuente de investigación:** [`06-RESEARCH.md`](./06-RESEARCH.md)  
**Estado:** propuesta de implementación `[ASSUMED]` ratificada para la planificación; la verificación de comportamiento queda asignada a los planes indicados.

## Propósito y límites

Esta matriz convierte las decisiones D-01..D-15 en conductas verificables antes de
crear migraciones. No sustituye los requisitos existentes ni convierte en v1 los
requisitos v2 `SOCIAL-01` y `SOCIAL-02`: esos dos identificadores conservan su
significado original de seguimiento/feed y reacciones/interacción comunitaria.

La Fase 6 sí incorpora el módulo social controlado descrito por `SOCIAL-03`,
`SOCIAL-04` y `SOCIAL-05`. Se trata de relaciones explícitas entre cuentas
controladas, no de una red social abierta: alias exacto, solicitudes y amistad
aceptada, proyecciones protegidas y recomendaciones privadas.

## Matriz semántica D-01..D-15

| Decisión | Requisito | Conducta observable y límite | Plan responsable | Prueba o evidencia exigida |
|---|---|---|---|---|
| D-01 | CAT-05 | El contrato local representa y puede consultar juegos, plataformas, ediciones, géneros, franquicias, desarrolladores, editoriales, fechas, modos y tags disponibles en fuentes aprobadas. La interfaz puede mostrar una selección posterior sin reducir el backend. | 06-02, 06-05, 06-09 | Tests de modelos, parser, facets y DTO; combinaciones de filtros; evidencia de que no se modifican snapshots de evaluación. |
| D-02 | CAT-02 (extensión de la capacidad de Phase 01.1) y CAT-05 | Búsquedas y filtros usan GET compartible, parámetros repetibles, ordenación determinista y paginación que conserva toda la query. No existe estado de filtro exclusivo del cliente. | 06-02, 06-05, 06-09 | Repetición de URL produce el mismo resultado; tests de `CatalogueQuery`, constructor de URL y paginación. |
| D-03 | SOCIAL-03 `[ASSUMED]` | Solo una cuenta autenticada puede buscar un alias exacto y enviar/aceptar una solicitud. No hay autocomplete ni directorio parcial; la amistad nace al aceptar y es bidireccional. | 06-01, 06-06, 06-09 | Alias exacto existente/inexistente, usuario inactivo, self-request, solicitud inversa y transición request→accept. |
| D-04 | SOCIAL-03 `[ASSUMED]` | El módulo social separa solicitudes recibidas, solicitudes enviadas y amistades, y ofrece acciones diferenciadas de aceptar, rechazar, eliminar y bloquear. | 06-01, 06-06, 06-09 | Matriz de estados API y flujo E2E; cada acción deriva el actor de `request.user`. |
| D-05 | SOCIAL-03 `[ASSUMED]` | Rechazar conserva ausencia de relación y permite solicitar de nuevo; eliminar revoca acceso sin bloquear; bloquear cancela solicitudes, elimina amistad, revoca acceso, impide nuevas solicitudes y oculta mutuamente perfil/contenido hasta desbloquear. | 06-01, 06-03, 06-06, 06-09 | Tests transaccionales de cada transición, re-solicitud posterior a reject/remove y ocultación bilateral tras block/unblock. |
| D-06 | PROF-03, PROF-04, SOCIAL-04 `[ASSUMED]` | `public` en colección, listas y comentarios significa compartible solo con amistad aceptada o propietario; no significa visible a anónimos ni a no-amigos. | 06-03, 06-04, 06-06, 06-08, 06-09 | Matriz de visibilidad para propietario, amigo, no-amigo, anónimo y bloqueado; assertions de ausencia de contenido. |
| D-07 | PROF-03, PROF-04, SOCIAL-04 `[ASSUMED]` | La única excepción para un no-amigo es el perfil básico: exactamente `alias`, `avatar_url`, `bio` y la acción contextual de solicitud. No se muestran colección, listas, comentarios, actividad ni estadísticas. Para anónimos la acción es no mutante. | 06-03, 06-06, 06-09 | `apps/api/tests/test_public_profile.py` cubre el perfil básico; se comprueban claves exactas y ausencia de actividad. |
| D-08 | PROF-04, SOCIAL-04 `[ASSUMED]` | Las URLs directas de perfil/lista vuelven a autenticar y autorizar en servidor usando propietario o amistad aceptada. No autorizado, bloqueado, anónimo en recurso protegido e inexistente reciben el mismo `404` genérico. | 06-03, 06-06, 06-09 | Tests API/SSR de URL directa, cookie forwarding y comparación de forma/código de respuestas `404`; no se confía en navegación previa. |
| D-09 | PROF-03, SOCIAL-04 `[ASSUMED]` | La colección autorizada contiene únicamente juego, portada, año, plataforma, estado de backlog y valoración personal. Nunca contiene copias, compras, precios, tiendas, ubicaciones ni notas privadas. | 06-03, 06-04, 06-06, 06-09 | Serializer de amigo con allowlist y prueba recursiva de claves prohibidas, incluyendo datos de `OwnedCopy`. |
| D-10 | PROF-03, PROF-04, SOCIAL-04 `[ASSUMED]` | Una lista autorizada contiene los mismos datos de juego que la colección, conserva exactamente `CustomListItem.position` y se resuelve mediante alias del propietario y `public_slug`. | 06-03, 06-06, 06-09 | Tests de orden manual, slug por propietario, lista vacía y `404` para tercero no autorizado; análogo `apps/api/library/tests/test_lists.py:306-340`. |
| D-11 | PROF-03, SOCIAL-04 `[ASSUMED]` | Los comentarios permitidos aparecen en la ficha del juego con solo alias del autor, texto y fecha. No incluyen propiedad, valoración ajena ni identificadores internos; comentarios privados nunca aparecen a amistades. | 06-04, 06-08, 06-09 | Tests de autorización y claves exactas; análogo `apps/api/library/tests/test_comments.py:121-207`; flujo de ficha y XSS escapado. |
| D-12 | PROF-03 | La proyección pública no añade estadísticas globales independientes. Solo puede mostrar estados y valoraciones que formen parte de una colección autorizada. | 06-03, 06-06, 06-09 | Denylist de `summary`, contadores y actividad; comparación de proyecciones owner/friend/basic. |
| D-13 | SOCIAL-05 `[ASSUMED]` | Una recomendación privada contiene un juego válido del catálogo y texto opcional, llega a la bandeja de “Mensajes de amigos” y no envía correo. Solo mensajes dirigidos al usuario autenticado son legibles. | 06-04, 06-07, 06-09 | Tests de creación, inbox owner-scoped, juego inexistente, texto acotado y ausencia de correos/proveedores externos. |
| D-14 | SOCIAL-05 `[ASSUMED]` | La bandeja tiene página propia y entrada exacta en el desplegable de perfil. Un badge textualmente accesible y un punto rojo indican mensajes o solicitudes pendientes; el color no es la única señal. | 06-07, 06-08, 06-09 | Tests de unread/read y badge, navegación con teclado/Escape, `aria-label`, axe y viewport móvil. |
| D-15 | SOCIAL-05 `[ASSUMED]` | Existe como máximo una recomendación por pareja dirigida emisor-receptor en cada ventana móvil de `7 * 24` horas. Se permiten distintos receptores; el bloqueo de cooldown devuelve `429`, `Retry-After` y `retry_after_seconds` al emisor autenticado. | 06-04, 06-07, 06-09 | Tests justo antes, en y justo después de siete días, juegos distintos, receptores distintos y concurrencia serializada con lock transaccional. |

## Rebaseline de requisitos

### `PROF-03` — allowlist exacta

El perfil y las proyecciones públicas se separan por audiencia y no se obtienen
mediante introspección automática. La allowlist de campos permitidos queda fijada
exactamente en:

```text
alias, avatar_url, bio,
game, cover, year, platform, backlog_status, personal_rating,
author_alias, text, date
```

Los tres primeros campos forman el perfil básico de D-07. Los campos de juego de
la segunda línea forman la proyección autorizada de colección/lista de D-09/D-10.
Los tres últimos forman la proyección autorizada de comentarios de D-11. D-07 es
la única excepción explícita a la regla de que el contenido denominado `public`
requiere propietario o amistad aceptada; no autoriza actividad, estadísticas,
copias, compras, precios, tiendas, ubicaciones, notas privadas, `owner_id` ni
otros identificadores internos.

La cobertura se comprobará en dos superficies distintas: `apps/api/tests/test_public_profile.py`
verifica el perfil básico visible a no-amigos, mientras que
`apps/api/tests/test_social_visibility.py` verifica que el contenido protegido
no aparece a no-amigos, anónimos ni bloqueados.

### `PROF-04` — URLs compartibles sin bypass de autorización

El propietario y una amistad aceptada pueden abrir el perfil y las listas
compartibles. La ruta directa vuelve a resolver el alias/`public_slug`, la cuenta
activa, el viewer autenticado y el estado de amistad en el backend. Un no-amigo,
anónimo en un recurso protegido, bloqueado o locator inexistente recibe el mismo
`404` genérico, sin cuerpo, encabezado o estado visual que permita distinguir
existencia de autorización. El perfil básico de D-07 es la excepción visible y no
da acceso a las proyecciones.

### `CAT-05` — dimensiones completas del catálogo

El contrato de catálogo enumera literalmente estas dimensiones disponibles en las
fuentes aprobadas: **juegos, plataformas, ediciones, géneros, franquicias,
desarrolladores, editoriales, fechas, modos y tags**. `CAT-02` conserva su
asignación a Phase 01.1; esta fase amplía su capacidad de consulta y trazabilidad
sin transferir la titularidad del requisito ni modificar snapshots de evaluación.
La presentación visual de facets se mantiene abierta según D-01, pero no puede
eliminar ninguna dimensión del contrato backend.

## Requisitos sociales confirmados sin reinterpretar v2

| ID | Redacción v1 para esta fase | Estado |
|---|---|---|
| SOCIAL-03 | Usuario autenticado puede buscar alias exactos y gestionar solicitudes, amistades aceptadas, rechazo, eliminación, bloqueo y desbloqueo. | `[ASSUMED]` confirmado para planificación; se implementa y prueba en 06-01/06-06/06-09. |
| SOCIAL-04 | Propietario y amistades aceptadas pueden acceder a proyecciones allowlist de perfil, colección, listas y comentarios mediante URLs protegidas; el no-amigo solo recibe el perfil básico D-07. | `[ASSUMED]` confirmado para planificación; se implementa y prueba en 06-03/06-04/06-06/06-08/06-09. |
| SOCIAL-05 | Amistades pueden enviar recomendaciones privadas con texto opcional a un inbox con lectura/no lectura y cooldown direccional móvil de siete días. | `[ASSUMED]` confirmado para planificación; se implementa y prueba en 06-04/06-07/06-09. |

`SOCIAL-01` sigue siendo “User can follow other profiles and view a social
activity feed” y `SOCIAL-02` sigue siendo “User can react to or interact with
community content”, ambos en v2. La presente ampliación no los marca como
completados, no los renombra y no usa sus identificadores para esconder el
módulo social controlado.

## Analógicos obligatorios y criterio de suficiencia

La implementación posterior debe conservar los límites de estos análogos:

- `apps/api/accounts/serializers.py:86-139` y `apps/api/accounts/views.py:224-305`
  para allowlists manuales, alias exacto, sesión y respuestas genéricas.
- `apps/api/library/tests/test_comments.py:121-207` para autorización, privacidad,
  404 y texto hostil.
- `apps/api/library/tests/test_lists.py:306-340` para owner scoping, claves exactas
  y orden de listas.

La coincidencia de tokens D-01..D-15 no basta para declarar cobertura: cada fila
debe producir la conducta, el actor autorizado, el actor denegado y la prueba
indicada. Las pruebas de `test_public_profile.py` y `test_social_visibility.py`
son intencionadamente separadas para evitar que el perfil básico se convierta en
una vía de acceso a contenido protegido.

## Verificación de la reconciliación

- La matriz cubre todas las decisiones D-01..D-15 una vez y las enlaza a
  requisitos, planes y pruebas.
- `SOCIAL-01`/`SOCIAL-02` conservan su semántica v2 y no aparecen como sustituidos.
- `PROF-03` contiene la allowlist exacta y solo la excepción D-07.
- `PROF-04` distingue perfil básico, proyecciones protegidas y URL directa con
  autorización server-side/404 genérico.
- `CAT-05` enumera juegos, plataformas, ediciones, géneros, franquicias,
  desarrolladores, editoriales, fechas, modos y tags.

