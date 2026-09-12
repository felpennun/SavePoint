# Fase 5 — Contrato de integración backend/UI (handoff)

**Fecha:** 2026-09-13
**Autor:** sesión backend (planes 05-01, 05-02, 05-03)
**Idioma:** español (`CONVENTIONS.md` §1); identificadores/rutas/nombres de campo en inglés.

Este documento describe, para la sesión que integra `apps/web/**` y `design/**`, el
contrato completo de la API de Django construida en la Fase 5: identidad/perfil/favoritos
(05-01), comentarios/listas personalizadas (05-02) y metadatos avanzados de copias
(05-03). Esta sesión backend **no ha modificado** `apps/web/**`, `design/**`, capturas de
pantalla, ni el contrato público de recomendaciones (`apps/api/recommendations/published.py`)
en ninguno de los tres planes. La sesión web debe ejecutar
`e2e/collection-workflows.spec.ts` (Playwright) y su matriz de accesibilidad
(`axe-core`/teclado/responsive) sobre perfil, ficha de juego (comentarios), colección
(listas, copias) y descarga; ese trabajo pertenece a la otra sesión.

## 1. Sesión, CSRF y cookies

Todas las mutaciones (POST/PATCH/PUT/DELETE) sobre estos endpoints requieren:

- Cookie de sesión Django (`sessionid`) obtenida tras `POST /api/accounts/login/` o
  `POST /api/accounts/register/`.
- Cabecera `X-CSRFToken` con el valor de la cookie `csrftoken`, obtenida primero con
  `GET /api/accounts/csrf/` (fija la cookie sin requerir sesión).
- Cookies `HttpOnly`/`SameSite=Lax`; el cliente nunca lee `sessionid` desde JavaScript.

Una petición mutante sin CSRF válido devuelve `403`. Una petición sin sesión sobre un
endpoint `IsAuthenticated` devuelve `401`. Los mensajes de error de login/registro son
uniformes y nunca confirman si un alias existe (no enumeración).

## 2. Identidad, perfil y favoritos (05-01)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/accounts/csrf/` | pública | Fija la cookie `csrftoken`. |
| POST | `/api/accounts/login/` | pública, throttle `login` | Alias + contraseña; error uniforme `401`. |
| POST | `/api/accounts/register/` | pública, throttle `registration` | Crea cuenta real (no demo); rota sesión al terminar. |
| POST | `/api/accounts/logout/` | requiere sesión | Invalida la sesión actual. |
| GET | `/api/accounts/me/` | requiere sesión | Alias, email, flags de la cuenta autenticada. |
| GET/PATCH | `/api/accounts/me/profile/` | requiere sesión | Biografía y `avatar_url` (URL HTTPS validada); el alias (`User.username`) **nunca** es editable aquí. |
| GET/PUT | `/api/accounts/me/favorites/` | requiere sesión | Reemplazo atómico y completo de los cinco slots de favoritos (`1..5`), solo con obras de la propia colección; huecos `null` permitidos. |
| GET | `/api/accounts/profiles/<alias>/` | pública, throttle `public_profile` | Proyección **allowlisted** — ver §5. |

Campos permitidos en `PATCH /me/profile/`: `bio` (texto libre acotado), `avatar_url`
(HTTPS, longitud acotada), `collection_visibility` y `favorites_visibility` (`public` |
`private`, nunca `friends`). Un intento de enviar `username` en el payload se ignora
silenciosamente (el alias de login es inmutable, D-01).

## 3. Comentarios por obra (05-02)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET/POST | `/api/library/entries/<work_id>/comments/` | GET pública, POST requiere sesión | GET: comentarios `public` más el propio del visitante autenticado. POST: crea el único comentario del autor para esa obra (409 si ya existe). |
| GET/PATCH/DELETE | `/api/library/comments/<comment_id>/` | requiere sesión, owner-only | Un comentario ajeno responde `404` (indistinguible de inexistente). |

Un comentario exige que la obra esté en la colección del autor (`LibraryEntry`
existente); el texto está acotado a 2000 caracteres y se devuelve como texto plano,
nunca HTML. `visibility` es `public` o `private`, independiente de
`collection_visibility`/`favorites_visibility`.

## 4. Listas personalizadas (05-02)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET/POST | `/api/library/lists/` | requiere sesión | Listas propias del usuario autenticado. |
| GET/PATCH/DELETE | `/api/library/lists/<list_id>/` | requiere sesión, owner-only | `404` si la lista no pertenece al usuario. |
| POST | `/api/library/lists/<list_id>/items/` | requiere sesión | Añade una obra ya presente en la colección propia (`400` si no lo está o ya está en la lista). |
| DELETE | `/api/library/lists/<list_id>/items/<item_id>/` | requiere sesión, owner-only | — |
| POST | `/api/library/lists/<list_id>/reorder/` | requiere sesión | `expected_version` **obligatorio**; `item_ids` debe ser el conjunto completo de ítems actuales. |

El reorder es optimista: `expected_version` desactualizado devuelve `409` sin tocar
ninguna fila; una versión correcta se procesa bajo `select_for_update()` y persiste
posiciones consecutivas `1..N`. `visibility` (`public`/`private`) es propia de cada lista.

## 5. Copias e inventario avanzado (05-03)

`OwnedCopy` sigue siendo la única entidad de copia; el estado (`status`) y el rating
(`rating_half_steps`) permanecen en `LibraryEntry` y nunca se mueven a la copia.

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET/POST | `/api/library/entries/<work_id>/copies/` | requiere sesión | GET: copias propias de esa obra. POST: crea una copia (idempotente por `idempotency_key`). |
| DELETE | `/api/library/entries/<work_id>/copies/<copy_id>/` | requiere sesión, owner-only | — |
| POST | `/api/library/entries/<work_id>/configuration/` | requiere sesión | Reemplazo atómico y completo de `status`/`rating_half_steps`/`copies` para esa obra. |

### 5.1 Campos de una copia (`OwnedCopy`)

| Campo | Tipo | Reglas |
|---|---|---|
| `release_id` / `edition_id` | UUID | La edición debe pertenecer al release; el release debe pertenecer a la obra. |
| `format` | `physical` \| `digital` | Determina qué metadatos de conservación se permiten (ver 5.2). |
| `idempotency_key` | texto ≤100 | Repetir la misma clave para el mismo usuario devuelve la copia existente, nunca duplica. |
| `purchase_date` | fecha ISO `YYYY-MM-DD` | Opcional. |
| `price` | decimal, no negativo | Opcional; nunca `float`; `400` si es negativo (serializer) y `CheckConstraint` en PostgreSQL como última defensa. |
| `currency` | 3 letras | Se normaliza a mayúsculas (`eur` → `EUR`); `400` si no son exactamente 3 letras. |
| `store` | texto ≤120 | Opcional. |
| `conservation_state` | `new` \| `good` \| `fair` \| `poor` \| `damaged` | Solo válido en copias físicas (ver 5.2). |
| `storage_location` | texto ≤200 | Solo válido en copias físicas (ver 5.2). |

### 5.2 Regla física/digital

Una copia `format="digital"` **nunca** puede tener `conservation_state` ni
`storage_location`: el envío de cualquiera de los dos junto con `format="digital"`
devuelve `400` antes de tocar la base de datos. Esta regla se aplica en tres capas —
serializer, servicio y un `CheckConstraint` de PostgreSQL
(`library_copy_digital_excludes_conservation`) — de modo que ni siquiera una escritura
que bypasee la API puede violarla. Una copia física puede dejar ambos campos vacíos
(son opcionales) o rellenarlos.

### 5.3 Códigos de respuesta relevantes para copias/configuración

| Código | Cuándo |
|---|---|
| `200` | Lectura o reemplazo de configuración exitoso. |
| `201` | Copia creada por primera vez (`POST /copies/`). |
| `400` | Payload inválido: formato/moneda/estado desconocidos, precio negativo, campos físicos en una copia digital, campos que exceden su longitud máxima, o un `id` de copia que no pertenece al usuario/obra actual. |
| `401` | Sin sesión. |
| `404` | Copia/lista/comentario ajenos, o inexistentes. |
| `409` | Reintento de creación de comentario duplicado, o `expected_version` obsoleto en reorder. |
| `429` | Throttle superado (login/registro/perfil público). |

## 6. Proyecciones públicas (allowlist, PRIV-01)

`GET /api/accounts/profiles/<alias>/` construye su respuesta a mano (nunca vía
`ModelSerializer`) y **nunca** incluye: `email`, `password`, IDs internos, `copies`,
`format`, `purchase_date`, `price`, `currency`, `store`, `conservation_state`,
`storage_location`, `idempotency_key`, `rating_half_steps` personal, ni `visibility`
interna de comentarios/listas. La colección de compra/conservación de `OwnedCopy` **no
forma parte del perfil público en absoluto** — ni siquiera la existencia de una copia se
expone; solo `bio`/`avatar_url` (siempre visibles), `activity`/`summary` (gateados por
`collection_visibility`), `favorites` (gateado por `favorites_visibility`, cinco slots
estables con `null` en huecos), y agregados de `comments`/`lists` filtrados por la
visibilidad propia de cada ítem. El propietario autenticado que visita su propio alias
siempre ve su propia información completa, independientemente de la privacidad
configurada; cualquier otro visitante (anónimo o de otra cuenta) recibe únicamente la
proyección resueta según la visibilidad, con una forma estable (nunca ausente) en cada
caso.

## 7. Alcance explícitamente fuera de esta fase

- `PORT-02`/`PORT-03` (previsualización/errores de importación) no se implementan en
  esta fase; ver `.planning/phases/05-complete-collection-workflows-and-portability/05-RESEARCH.md`
  (sección "Portability and Scope Reconciliation").
- La exportación CSV (`PORT-01`/`PORT-04`) es responsabilidad del plan 05-04, no de este
  documento.
- Ningún archivo de `apps/web/**`, `design/**` ni capturas de pantalla fue editado por
  los planes 05-01/05-02/05-03.

## 8. Referencias canónicas

- `.planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md`
- `.planning/phases/05-complete-collection-workflows-and-portability/05-RESEARCH.md`
- `.planning/phases/05-complete-collection-workflows-and-portability/05-PATTERNS.md`
- `apps/api/accounts/{models,serializers,services,views,urls}.py`
- `apps/api/library/{models,serializers,services,views,urls}.py`
- `ideas-vault/Conceptos/Inventario de copias.md`
