# Phase 6: Public Discovery and Resilient Enrichment - Pattern Map

**Mapped:** 2026-09-13  
**Files analyzed:** 58  
**Analogs found:** 50 / 58

El alcance combina la ampliación de descubrimiento del catálogo, la visibilidad social
controlada por amistad y una capa de mensajería/recomendaciones privadas. Los nombres de
migración y de las rutas nuevas marcados como `[ASSUMED]` son propuestas derivadas de
`06-RESEARCH.md`; el plan puede ajustar el número de migración sin cambiar el patrón.

## File Classification

| Fichero nuevo/modificado | Rol | Flujo de datos | Análogo más cercano | Calidad |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | config/rebaseline | transform/batch | — | sin análogo |
| `.planning/REQUIREMENTS.md` | config/rebaseline | transform/batch | — | sin análogo |
| `apps/api/social/__init__.py` | config/módulo | request-response | — | sin análogo |
| `apps/api/social/apps.py` | config | request-response | `apps/api/accounts/apps.py` | role-match |
| `apps/api/social/models.py` | model | CRUD | `apps/api/accounts/models.py`, `apps/api/library/models.py` | role-match |
| `apps/api/social/permissions.py` | middleware/policy | request-response | `apps/api/accounts/views.py` | role-match |
| `apps/api/social/policies.py` | utility/policy | request-response | `apps/api/accounts/serializers.py` | role-match |
| `apps/api/social/serializers.py` | serializer | transform/request-response | `apps/api/accounts/serializers.py`, `apps/api/library/serializers.py` | role-match |
| `apps/api/social/services.py` | service | CRUD/event-driven | `apps/api/accounts/services.py`, `apps/api/library/services.py` | role-match |
| `apps/api/social/urls.py` | route | request-response | `apps/api/accounts/urls.py`, `apps/api/library/urls.py` | role-match |
| `apps/api/social/views.py` | controller/view | request-response | `apps/api/accounts/views.py`, `apps/api/library/views.py` | role-match |
| `apps/api/social/migrations/0001_initial.py` `[ASSUMED]` | migration | batch/schema | `apps/api/accounts/migrations/0003_phase5_profile.py` | role-match |
| `apps/api/social/tests/test_social.py` | test | CRUD/request-response | `apps/api/accounts/tests/test_public_profile.py`, `apps/api/library/tests/test_comments.py` | role-match |
| `apps/api/config/settings.py` | config | request-response | el mismo fichero | exacto |
| `apps/api/config/urls.py` | route/config | request-response | el mismo fichero | exacto |
| `apps/api/accounts/serializers.py` | serializer | transform/request-response | el mismo fichero | role-match |
| `apps/api/accounts/views.py` | controller/view | request-response | el mismo fichero | role-match |
| `apps/api/library/serializers.py` | serializer | transform/request-response | el mismo fichero | exacto |
| `apps/api/library/services.py` | service | CRUD/transactional | el mismo fichero | exacto |
| `apps/api/library/views.py` | controller/view | request-response | el mismo fichero | exacto |
| `apps/api/library/urls.py` | route | request-response | el mismo fichero | exacto |
| `apps/api/library/tests/test_comments.py` | test | CRUD/request-response | el mismo fichero | exacto |
| `apps/api/library/tests/test_lists.py` | test | CRUD/request-response | el mismo fichero | exacto |
| `apps/api/catalogue/models.py` | model | CRUD/import | el mismo fichero | exacto |
| `apps/api/catalogue/migrations/0019_phase6_discovery.py` `[ASSUMED]` | migration | batch/schema | `apps/api/accounts/migrations/0003_phase5_profile.py` | role-match |
| `apps/api/catalogue/search.py` | service/utility | request-response/transform | el mismo fichero | exacto |
| `apps/api/catalogue/serializers.py` | serializer | transform/request-response | el mismo fichero | exacto |
| `apps/api/catalogue/views.py` | controller/view | request-response | el mismo fichero | exacto |
| `apps/api/catalogue/urls.py` | route | request-response | el mismo fichero | exacto |
| `apps/api/catalogue/management/commands/import_catalogue.py` | service/job | batch/file-I/O | el mismo fichero | exacto |
| `apps/api/catalogue/tests/test_search.py` | test | request-response/transform | el mismo fichero | exacto |
| `apps/api/catalogue/tests/test_import.py` | test | batch/file-I/O | el mismo fichero | exacto |
| `apps/web/app/[locale]/catalogue/page.tsx` | page/App Router | request-response/SSR | el mismo fichero | exacto |
| `apps/web/components/FilterBar.tsx` | component | request-response/GET form | el mismo fichero | exacto |
| `apps/web/components/FacetMenu.tsx` | component | request-response/GET form | el mismo fichero | exacto |
| `apps/web/app/[locale]/profiles/[alias]/page.tsx` | page/App Router | request-response/SSR | el mismo fichero | role-match |
| `apps/web/app/[locale]/profiles/[alias]/lists/[listSlug]/page.tsx` `[ASSUMED]` | page/App Router | request-response/SSR | `apps/web/app/[locale]/profiles/[alias]/page.tsx` | sin análogo |
| `apps/web/app/[locale]/friends/page.tsx` `[ASSUMED]` | page/App Router | request-response/SSR | `apps/web/app/[locale]/recommendations/page.tsx` | sin análogo |
| `apps/web/app/[locale]/messages/page.tsx` | page/App Router | request-response/SSR | `apps/web/app/[locale]/recommendations/page.tsx` | role-match |
| `apps/web/app/[locale]/games/[id]/page.tsx` | page/App Router | request-response/SSR | el mismo fichero | exacto |
| `apps/web/components/SocialActions.tsx` | component | event-driven/request-response | — | sin análogo |
| `apps/web/components/SocialInbox.tsx` | component | request-response/event-driven | — | sin análogo |
| `apps/web/components/AppShell.tsx` | component/layout | request-response/navigation | el mismo fichero | exacto |
| `apps/web/components/AccountSwitcher.tsx` | component | request-response/event-driven | el mismo fichero | exacto |
| `apps/web/components/GameComments.tsx` | component | CRUD/request-response | el mismo fichero | exacto |
| `apps/web/lib/social.ts` `[ASSUMED]` | API adapter | request-response | `apps/web/lib/api.ts`, `apps/web/lib/client-api.ts` | sin análogo |
| `apps/web/lib/api.ts` | API adapter/types | request-response/SSR | el mismo fichero | exacto |
| `apps/web/lib/catalogue-filters.ts` | utility | transform/GET URL | el mismo fichero | exacto |
| `apps/web/middleware.ts` | middleware | request-response/auth guard | el mismo fichero | exacto |
| `apps/web/app/globals.css` | stylesheet/config | transform/UI | clases existentes del mismo fichero | role-match |
| `apps/web/i18n/dictionary.ts` | config/types | transform | el mismo fichero | exacto |
| `apps/web/i18n/es.ts` | config/translation | transform | el mismo fichero | exacto |
| `apps/web/i18n/en.ts` | config/translation | transform | el mismo fichero | exacto |
| `apps/web/tests/social.test.ts` `[ASSUMED]` | test | request-response/component | `apps/web/tests/catalogue-filters.test.ts` | role-match |
| `apps/web/tests/catalogue-filters.test.ts` | test | transform/GET URL | el mismo fichero | exacto |
| `apps/web/tests/i18n.test.ts` | test | transform | el mismo fichero | exacto |
| `e2e/social-workflows.spec.ts` `[ASSUMED]` | test E2E | event-driven/request-response | `e2e/collection-workflows.spec.ts` | role-match |
| `e2e/a11y.spec.ts` | test E2E | request-response/UI | el mismo fichero | exacto |

## Pattern Assignments

### Backend: módulo `social`

No existe todavía un dominio social en el árbol. Las siguientes asignaciones son el patrón
combinado que debe copiar el plan: comandos transaccionales de `accounts`/`library`,
proyecciones seguras de perfil y errores 404 genéricos.

#### `apps/api/social/apps.py` y `apps/api/social/__init__.py`

**Análogo:** `apps/api/accounts/apps.py` (líneas 1-6). Mantener el módulo Django mínimo y
registrarlo en `INSTALLED_APPS`; `__init__.py` no necesita lógica. No crear un registro global
de notificaciones si el badge se puede derivar de mensajes no leídos y solicitudes pendientes.

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
```

Para `social`, conservar `default_auto_field` y cambiar únicamente `name = "social"`.

#### `apps/api/social/models.py`

**Análogos:** `apps/api/accounts/models.py` (líneas 90-128) para perfiles/constraints y
`apps/api/library/models.py` (líneas 173-203, 209-267) para relaciones con usuario, visibilidad
y orden manual. Modelar por separado `Friendship`, `FriendshipRequest`, `Block` y
`SocialMessage`; usar `settings.AUTH_USER_MODEL`, timestamps y constraints explícitos.

```python
class GameComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    work = models.ForeignKey("catalogue.GameWork", on_delete=models.CASCADE)
    visibility = models.CharField(max_length=8, choices=Visibility.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "work"), name="library_comment_unique_user_work"),
        ]
```

Copiar el uso de `UniqueConstraint`/`CheckConstraint`, pero para amistad usar el par canónico
ordenado (`user_low`, `user_high`) y para solicitudes/bloqueos una relación dirigida. El
cooldown de recomendación debe ser por `sender`, `recipient` y ventana temporal, con índice
compuesto `(sender, recipient, created_at)`.

#### `apps/api/social/permissions.py` y `apps/api/social/policies.py`

**Análogos:** `apps/api/accounts/views.py` (líneas 224-305) para separar
`IsAuthenticated`/`AllowAny`, y `apps/api/accounts/serializers.py` (líneas 86-139) para
resolver viewer/owner antes de serializar.

La policy debe devolver estados explícitos —`owner`, `accepted_friend`, `basic` o `hidden`—
y centralizar:

- perfil básico para anónimo/no-amigo: alias, avatar, bio y acción permitida;
- contenido de amigo aceptado: colección/listas/comentarios proyectados;
- bloqueos en ambos sentidos: ocultar perfil, cancelar solicitudes y denegar acciones;
- recurso no autorizado: `None`/not-found para que la vista responda 404 genérico.

```python
user = get_object_or_404(User, alias=alias, is_active=True)
return Response(build_public_profile(user, viewer=request.user))
```

No confiar en IDs de propietario enviados por cliente. Las policies deben aceptar el viewer
derivado de `request.user` y el propietario resuelto por URL.

#### `apps/api/social/serializers.py`

**Análogos:** `apps/api/accounts/serializers.py` (líneas 127-139) y
`apps/api/library/serializers.py` (líneas 195-203, 252-267). No reutilizar el serializer
privado de `library` para amigos.

```python
return {
    "alias": profile.user.alias,
    "avatar_url": profile.avatar_url,
    "bio": _escape_text(profile.bio),
    "action": action,
}
```

Crear DTOs distintos para `PublicBasicProfile`, `FriendCollectionItem`, `FriendListItem`,
`ProfileComment`, `FriendRequest` y `SocialMessage`. La proyección de colección sólo puede
contener `game`, `cover`, `year`, `platform`, `backlog_status` y `personal_rating`; la de
comentario, `author_alias`, `text` y `date`. Excluir `copies`, compras, precio, tienda,
ubicación, notas privadas, `owner_id` e IDs internos no necesarios. Mantener `_escape_text`
de `library/serializers.py` (líneas 154-158) y nunca usar `dangerouslySetInnerHTML`.

#### `apps/api/social/services.py`

**Análogos:** `apps/api/accounts/services.py` (líneas 25-75, 78-106) y
`apps/api/library/services.py` (líneas 348-371, 413-515).

```python
with transaction.atomic():
    profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=owner)
    profile.bio = bio
    profile.save(update_fields=["bio", "updated_at"])
```

Implementar cada transición como comando de servicio dentro de `transaction.atomic()`:
solicitar, aceptar, rechazar, eliminar amistad, bloquear/desbloquear, enviar, marcar leído y
recomendar. Obtener siempre la identidad del usuario autenticado; validar el estado actual
antes de mutar; bloquear debe cancelar solicitudes, borrar la amistad y revocar acceso.
Para la recomendación, bloquear la fila estable del par dirigido dentro de la transacción,
consultar `timezone.now()` con zona horaria y exigir exactamente `7 * 24` horas antes de
crear otro mensaje.

#### `apps/api/social/urls.py`, `apps/api/social/views.py` y `apps/api/config/urls.py`

**Análogos:** `apps/api/accounts/urls.py` (líneas 1-25), `apps/api/library/urls.py` (líneas
1-41), y `apps/api/config/urls.py` (líneas 1-22).

```python
urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/<uuid:work_id>/", GameDetailView.as_view(), name="game-detail"),
]
```

Mantener rutas explícitas, trailing slash y `config.urls` como punto de inclusión. En las
vistas sociales, aplicar `permission_classes = [IsAuthenticated]` a bandeja/acciones privadas,
resolver alias/lista desde la URL y devolver 404 indistinguible para recurso inexistente o
no autorizado. Seguir en `GameListView` (`catalogue/views.py`, líneas 70-107) el patrón de
capturar `FilterValidationError` y responder 400 acotado.

#### `apps/api/social/migrations/0001_initial.py` y `apps/api/catalogue/migrations/0019_phase6_discovery.py`

**Análogo:** `apps/api/accounts/migrations/0003_phase5_profile.py` (líneas 8-45). Generar
migraciones declarativas con dependencias explícitas, `settings.AUTH_USER_MODEL`,
`UniqueConstraint`, `CheckConstraint` e índices. La migración de catálogo debe añadir
`Publisher` o la relación equivalente sólo si el plan confirma que no puede reutilizar
`Developer`/`CuratedLabel`; no introducir una entidad duplicada sin decisión de modelo.

### Backend: accounts, library y privacidad

#### `apps/api/accounts/serializers.py` y `apps/api/accounts/views.py`

**Análogos:** los mismos ficheros (role-match). `build_public_profile` (líneas 86-139) ya
calcula propietario y aplica visibilidad antes de construir un diccionario allowlist. La
vista pública (líneas 281-305) resuelve alias exacto, filtra `is_active`, usa
`AllowAny`/`ScopedRateThrottle` y entrega 404 genérico.

```python
user = User.objects.filter(alias=alias, is_active=True).first()
if user is None:
    raise Http404
return Response(build_public_profile(user, viewer=request.user))
```

Modificar la policy para que `public` signifique friend-visible en las secciones sociales:
anónimo/no-amigo recibe sólo el perfil básico; amigo aceptado recibe las proyecciones; un
bloqueo recibe 404. Mantener la actualización de perfil propia autenticada y el escape de
texto.

#### `apps/api/library/serializers.py`, `apps/api/library/services.py`, `apps/api/library/views.py`, `apps/api/library/urls.py`

**Análogos:** el mismo módulo. `MyLibraryView` (`views.py`, líneas 47-106) deriva el owner de
`request.user`, usa `select_related`/`prefetch_related` y construye respuesta explícita. Las
operaciones de comentario (`services.py`, líneas 348-396) validan texto, pertenencia y
duplicado dentro de transacción. Las listas (`services.py`, líneas 413-515) bloquean la lista,
validan versión y mantienen posiciones `1..N`.

```python
entries = (
    LibraryEntry.objects.filter(user=request.user)
    .select_related("work")
    .prefetch_related("work__releases__platform")
)
```

Añadir una ruta de lectura de perfil/lista que reciba viewer y pase por `social.policies` antes
de usar queryset. Ajustar `WorkCommentsView` (líneas 321-356): conservar POST autenticado,
pero para terceros sólo devolver comentarios si el viewer es amigo aceptado. `serialize_list`
(líneas 230-249) sigue siendo owner-facing; para amigos usar el DTO allowlist social y
preservar el orden manual de `CustomListItem.position`.

#### `apps/api/library/tests/test_comments.py` y `apps/api/library/tests/test_lists.py`

**Análogo:** los mismos ficheros. Reutilizar `_client_for`/`force_authenticate`, `_collect` y
las aserciones de claves. `test_comments.py` (líneas 121-207) ya prueba 404 de otro owner,
401/403 anónimo, privacidad y texto hostil; `test_lists.py` (líneas 306-340) prueba 404 para
todos los recursos de otro usuario y las claves exactas de `serialize_profile_list`.

Ampliar sin relajar las pruebas existentes: anónimo/no-amigo debe ver sólo básico, amigo
aceptado la proyección completa permitida, bloqueado 404, y las respuestas no deben contener
ninguna clave prohibida.

### Backend: catálogo, filtros y enriquecimiento offline

#### `apps/api/catalogue/models.py` y `apps/api/catalogue/migrations/0019_phase6_discovery.py`

**Análogo:** `catalogue/models.py` (líneas 16-157 para dimensiones simples; líneas 203-370
para `Developer`, `GameWork`, `Platform`, `GameRelease`, `Edition`; líneas 432-455 para
`SourceRecord`). Copiar UUID, `slug`, nombre, orden y procedencia. Las nuevas dimensiones
deben ser relaciones consultables y gobernadas por corpus, no JSON arbitrario.

#### `apps/api/catalogue/search.py`

**Análogo:** el mismo fichero, especialmente `CatalogueQuery` (líneas 94-117),
`_multi_values` (119-145), `parse_catalogue_query` (148-202), `_apply_filters` (205-239),
`_facets` (290-320) y `search_games` (366-427).

```python
def _multi_values(params: QueryDict, key: str) -> tuple[str, ...]:
    values = params.getlist(key)
    cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
    if len(cleaned) > 20:
        raise FilterValidationError(f"Too many values for {key}")
    return tuple(cleaned)
```

Extender el mismo flujo para `editions`, `genres`, `franchises`, `developers`, `publishers`,
fechas, `modes` y `tags`. Repeticiones deben conservarse en URL; filtros multi-valor de una
misma dimensión se combinan según el contrato actual (plataformas OR, tags AND), dimensiones
distintas intersectan; valores desconocidos se descartan sin vaciar resultados; sort/años/
ratings inválidos responden 400. Calcular facets sobre el corpus gobernado antes de paginar,
con conteos deterministas y sin N+1.

#### `apps/api/catalogue/serializers.py`, `apps/api/catalogue/views.py` y `apps/api/catalogue/urls.py`

**Análogos:** los mismos ficheros. `GameCardSerializer` (`serializers.py`, líneas 79-113)
usa allowlist y helpers para título, año, tags, plataforma y cover; `ReleaseSerializer`
(116-130) ya expone release/plataforma/edición. `GameListView` (`views.py`, líneas 70-107)
parsea, valida, serializa con contexto y conserva `facets`; `GameDetailView` (110-134) hace
`select_related`/prefetch y 404 genérico. Mantener el mapeo explícito de `catalogue/urls.py`
(líneas 1-19).

#### `apps/api/catalogue/management/commands/import_catalogue.py`

**Análogo:** el mismo comando, líneas 51-80 y 82-220. Mantener snapshot congelado, checksum,
estado `APPROVED`, `transaction.atomic()`, advisory lock, `SourceRecord.update_or_create`
e idempotencia. El enriquecimiento ausente debe degradar a valor nulo/placeholder gobernado,
registrar fuente, licencia, `retrieved_at` y hash; nunca llamar a un proveedor vivo desde una
vista ni inventar procedencia.

```python
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [IMPORT_LOCK_KEY])
    SourceRecord.objects.update_or_create(
        work=work, source=source, source_id=source_id,
        defaults={"snapshot_sha256": snapshot_sha256, "retrieved_at": retrieved_at},
    )
```

#### `apps/api/catalogue/tests/test_search.py` y `apps/api/catalogue/tests/test_import.py`

**Análogos:** los mismos ficheros. `test_search.py` (líneas 332-370) prueba allowlist de
sort, límites y 400 sin fuga; líneas 465-525 prueban facets, N+1 y URL reproducible; líneas
552-682 prueban parámetros repetidos, deduplicación, AND/OR, corpus gobernado y límite 20.

```python
params = {"platform": "pc", "tag": "role-playing-rpg", "sort": "rating_desc"}
first = client.get("/api/catalogue/games/", params).json()
second = client.get("/api/catalogue/games/", params).json()
assert [r["id"] for r in first["results"]] == [r["id"] for r in second["results"]]
```

`test_import.py` (líneas 26-68, 72-104, 107-129) cubre jerarquía/provenance, idempotencia,
fallo cerrado por freeze/checksum y concurrencia. Añadir casos para cada nueva dimensión,
fallback de enriquecimiento, hash y ausencia de llamadas de red.

### Frontend: App Router, perfil y catálogo

#### `apps/web/app/[locale]/catalogue/page.tsx`, `apps/web/components/FilterBar.tsx`, `apps/web/components/FacetMenu.tsx`

**Análogos:** los mismos ficheros. La página de catálogo (líneas 1-216) es Server Component:
espera `params/searchParams`, usa `parseFilters`, construye `URLSearchParams`, llama a
`fetchCatalogueList` y conserva filtros al paginar. `FilterBar` (líneas 1-151) usa un `<form>`
GET y `FacetMenu` (líneas 1-77) usa checkboxes repetidos con el mismo nombre.

```tsx
<form method="get" className="sp-filter-bar">
  <FacetMenu name="platform" options={facets.platforms} query={query} />
  <FacetMenu name="tag" options={facets.tags} query={query} />
</form>
```

Añadir sólo las dimensiones elegidas por UI-SPEC, manteniendo el contrato backend completo:
GET compartible, parámetros repetidos, `page`, orden determinista, etiquetas de filtros y
estado de error/reintento. No mover el estado de browse al cliente ni crear una llamada externa.

#### `apps/web/app/[locale]/profiles/[alias]/page.tsx` y `apps/web/app/[locale]/profiles/[alias]/lists/[listSlug]/page.tsx`

**Análogo:** la página de perfil existente (líneas 1-215). Copiar `cookies()` →
`fetchPublicProfile(..., cookieHeader)`, `notFound()` cuando API devuelve null y el patrón de
`Link`/`CoverImage`/`StatusPill`. La página nueva de lista debe resolver su URL en SSR y
reenviar la cookie; backend decide amistad y responde 404 genérico.

No conservar el supuesto antiguo de que colección/listas/comentarios “public” son públicos a
anónimos: el perfil básico sí puede ser público, pero esas secciones sólo se renderizan para
owner/amigo aceptado.

#### `apps/web/app/[locale]/friends/page.tsx` y `apps/web/app/[locale]/messages/page.tsx`

**Análogo parcial:** `apps/web/app/[locale]/recommendations/page.tsx` (líneas 1-34) para
redirigir si falta cookie; `layout.tsx` (líneas 1-71) y la página de perfil para SSR.

```tsx
const cookieHeader = (await cookies()).toString();
if (!cookieHeader) redirect(`/${locale}/login?next=/${locale}/recommendations`);
```

Las dos páginas deben ser privadas, cargar datos del servidor con el header `Cookie`, usar
DTOs sociales seguros y exponer estados vacíos/errores accesibles. `messages` debe permitir
marcar leído y enviar recomendación; `friends` debe separar solicitudes recibidas/enviadas,
amistades y acciones de rechazo/eliminación/bloqueo.

#### `apps/web/app/[locale]/games/[id]/page.tsx` y `apps/web/components/GameComments.tsx`

**Análogos:** el mismo juego (página, líneas 1-238) y el mismo componente (líneas 1-250).
La página SSR obtiene cookie y `fetchGameDetail`; el componente carga comentarios por API,
usa `aria-live`, feedback `role="status"` y distingue autor propio.

Mantener comentarios en `/{locale}/games/[id]`, pero hacer que API devuelva terceros sólo con
amistad aceptada. El render debe mostrar alias, texto y fecha; nunca ownership/internal IDs.
Conservar edición/borrado únicamente para el autor y el patrón de `apiFetch` con CSRF para
mutaciones.

### Frontend: navegación, cuenta y adaptadores

#### `apps/web/components/AppShell.tsx`

**Análogo:** el mismo fichero, líneas 21-36, 89-172 y 174-229. `buildNavItems` añade enlaces
condicionales autenticados; `MobileMenu` ya implementa focus trap, Escape, foco de retorno,
`role="dialog"` y `aria-expanded`.

Añadir el acceso a amigos/mensajes conservando el orden DOM, navegación con `aria-current`,
breakpoints existentes y el mismo comportamiento móvil. El contador no debe depender sólo de
color.

#### `apps/web/components/AccountSwitcher.tsx`, `apps/web/components/SocialActions.tsx`, `apps/web/components/SocialInbox.tsx`

**Análogo:** `AccountSwitcher.tsx` (líneas 1-150) para menú, focus trap, Escape, foco de
retorno, `role="menu"` y logout con CSRF; no hay análogo directo de las dos superficies
sociales nuevas.

```tsx
<button
  type="button"
  aria-label={labels.account}
  aria-expanded={open}
  aria-controls="account-menu"
>
```

Extender el dropdown con `Mensajes de amigos`, estado de unread/pending y punto rojo con
`aria-label`/texto accesible. `SocialActions` debe representar sólo acciones permitidas por
DTO (`add`, `pending`, `friend`, `blocked`), deshabilitar mientras muta y anunciar resultado;
`SocialInbox` debe renderizar solicitudes/mensajes, marcar leído y manejar error sin confiar
en IDs de propietario ocultos.

#### `apps/web/lib/social.ts`, `apps/web/lib/api.ts` y `apps/web/lib/client-api.ts`

**Análogos:** `api.ts` (líneas 156-239, 563-625) para tipos/fetch SSR, cookie forwarding,
`no-store`, null en 404 y errores; `client-api.ts` (líneas 20-47) para CSRF y mutaciones.

```ts
export async function fetchAccountMe(cookieHeader?: string): Promise<AccountMe | null> {
  const response = await fetch(`${API_BASE}/api/accounts/me/`, {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Account request failed");
  return response.json();
}
```

Agregar tipos explícitos para estados básicos/amigo/blocked, solicitudes, inbox, unread badge,
colección/lista de amigo y comentario. `social.ts` puede agrupar fetchers sociales para no
seguir inflando `api.ts`; todas las llamadas SSR deben aceptar cookie y todas las mutaciones
cliente deben pasar por `apiFetch`.

#### `apps/web/lib/catalogue-filters.ts` y `apps/web/middleware.ts`

**Análogos:** los mismos ficheros. `catalogue-filters.ts` (líneas 1-186) ya normaliza arrays,
construye `URLSearchParams` con `append` para platform/tag y elimina una ocurrencia sin perder
las demás. `middleware.ts` (líneas 1-72) mantiene locales, paths públicos y redirect con
`next`.

Extender `FILTER_PARAM_KEYS`, `parseFilters`, `buildQuery` y `removeHref` para las facets
seleccionadas, preservando orden y repetición. Añadir `/friends` y `/messages` a las rutas
privadas; mantener `/profiles` público sólo para el perfil básico. El middleware puede usar
presencia de sesión para UX, pero la autorización final queda en API/SSR.

#### `apps/web/app/globals.css`

**Análogo:** utilidades y tokens existentes del mismo fichero. Reutilizar variables, spacing,
focus ring, breakpoints y patrones `.sp-*`; añadir sólo estilos para badge, estados de relación,
inbox y listas sociales. Respetar controles de al menos 44px, zoom 400%, wrap largo y estados
focus/disabled sin depender únicamente de color.

### Frontend: traducciones y pruebas

#### `apps/web/i18n/dictionary.ts`, `apps/web/i18n/es.ts`, `apps/web/i18n/en.ts`

**Análogos:** los mismos ficheros. `Dictionary` declara la forma, y `es`/`en` son objetos
tipados paralelos. Añadir claves simétricas para `friends`, `messages`, acciones sociales,
badge, privacidad, perfil básico, lista de amigo y comentarios. La prosa nueva de las claves
españolas va en español; los identificadores permanecen en inglés.

#### `apps/web/tests/social.test.ts`, `apps/web/tests/catalogue-filters.test.ts`, `apps/web/tests/i18n.test.ts`

**Análogos:** `catalogue-filters.test.ts` (líneas 1-15) para Vitest de URL/normalización y
`i18n.test.ts` (líneas 1-61) para paridad recursiva de claves, valores no vacíos y
`formatCount`.

Cubrir en `social.test.ts` la presentación básica/amigo/bloqueado, labels accesibles, badge y
transiciones de botones. Mantener en filtros pruebas de repetición, orden y eliminación
individual. La paridad `es`/`en` debe seguir siendo una aserción exacta, no una lista manual
de excepciones.

#### `e2e/social-workflows.spec.ts` y `e2e/a11y.spec.ts`

**Análogos:** `e2e/collection-workflows.spec.ts` (líneas 1-120) para registro/login,
autenticación, shim CSRF y fixtures Playwright; `e2e/a11y.spec.ts` (líneas 1-120) para axe,
viewports mobile/desktop y recorrido `es`/`en`.

```ts
await expect(page.getByRole("heading", { name: /collection/i })).toBeVisible();
const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
expect(accessibilityScanResults.violations).toEqual([]);
```

El flujo social debe crear dos usuarios, solicitar/aceptar, comprobar proyección y bloqueo,
probar cooldown de recomendación y verificar que URLs directas no autorizadas dan 404. Añadir
perfil amigo, lista y messages a la matriz axe sin guardar screenshots o credenciales en el
repositorio.

## Shared Patterns

### Identidad, permisos y privacidad

**Fuentes:** `apps/api/accounts/views.py:224-305`, `apps/api/accounts/serializers.py:86-139`,
`apps/api/accounts/tests/test_public_profile.py:92-104,174-259`.

- Derivar owner/sender desde `request.user`; nunca aceptar `owner_id`, `sender_id` o
  `recipient_id` del cliente.
- Resolver alias exacto y usuario activo; ocultar la diferencia entre inexistente y no
  autorizado con 404 genérico.
- Policy antes de queryset y serializer; allowlist explícita por audiencia.
- El perfil básico es público; colección, listas, comentarios y actividad requieren owner o
  amistad aceptada; bloqueos ocultan en ambos sentidos.

### Transacciones y estado

**Fuentes:** `apps/api/accounts/services.py:25-106`, `apps/api/library/services.py:348-515`.

Usar `transaction.atomic()`, `select_for_update()` cuando dos acciones puedan competir,
validación de estado actual y `update_fields` acotado. Mantener errores de dominio claros y
convertirlos en 400/409 en la vista, igual que `StaleListVersion`/`CommentAlreadyExists`.

### DTOs y salida segura

**Fuentes:** `apps/api/accounts/serializers.py:127-139`, `apps/api/library/serializers.py:195-203,252-267`.

Separar DTO privado, básico y de amigo. Escapar texto, no serializar modelos completos y
probar recursivamente claves prohibidas. Las listas y colecciones se filtran antes de
serializar; el orden manual se conserva.

### Catálogo local, facets y procedencia

**Fuentes:** `apps/api/catalogue/search.py:119-145,205-239,290-320,366-427`,
`apps/api/catalogue/management/commands/import_catalogue.py:51-220`.

El catálogo HTTP es local y determinista. Parsear allowlists y límites antes de consultar,
usar GET como fuente de verdad, mantener facets antes de paginación y ejecutar enriquecimiento
únicamente en import/job con snapshot, checksum, licencia, hash e idempotencia.

### SSR, cookies y CSRF

**Fuentes:** `apps/web/app/[locale]/profiles/[alias]/page.tsx:66-72`,
`apps/web/app/[locale]/collection/page.tsx`, `apps/web/lib/api.ts:229-239,563-625`,
`apps/web/lib/client-api.ts:20-47`.

Las páginas privadas reenvían `Cookie` en SSR; las mutaciones pasan por `apiFetch` con cookie
CSRF y credenciales same-origin. No implementar acciones sociales sólo con estado cliente ni
hacer llamadas de proveedores externos desde App Router.

### Accesibilidad y traducción

**Fuentes:** `apps/web/components/AppShell.tsx:89-172`,
`apps/web/components/AccountSwitcher.tsx:51-146`, `apps/web/tests/i18n.test.ts:1-61`,
`e2e/a11y.spec.ts:1-120`.

Conservar focus trap/Escape/foco de retorno, nombres accesibles y `aria-live` para operaciones.
Todo texto nuevo debe existir en `es` y `en`; validar paridad con el test recursivo y axe en
ambos locales.

## No Analog Found

Estas superficies no tienen un precedente directo de dominio/flujo; el planner debe combinar
los role-match indicados con las decisiones de `06-RESEARCH.md`:

| Fichero | Motivo | Base parcial recomendada |
|---|---|---|
| `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` | Rebaseline de requisitos, no código ejecutable | convenciones GSD y Wave 0 de `06-RESEARCH.md` |
| `apps/api/social/__init__.py` | Módulo nuevo | paquete Django vacío |
| `apps/web/app/[locale]/profiles/[alias]/lists/[listSlug]/page.tsx` | Lista de amigo con policy/404 nuevo | página de perfil + listas de `library` |
| `apps/web/app/[locale]/friends/page.tsx` | Bandeja/relaciones sin UI existente | página privada de recommendations + AppShell |
| `apps/web/components/SocialActions.tsx` | Estados friend/pending/blocked nuevos | AccountSwitcher + feedback de GameComments |
| `apps/web/components/SocialInbox.tsx` | Inbox/unread/read nuevo | AccountSwitcher + CustomLists para estados busy/error |
| `apps/web/lib/social.ts` | Adapter social nuevo | `apps/web/lib/api.ts` + `apps/web/lib/client-api.ts` |

## Metadata

**Alcance de búsqueda:** `apps/api/{accounts,catalogue,library,config}`,
`apps/web/{app,components,lib,i18n,tests}`, `e2e`, `.planning` y `.agents`.  
**Ficheros escaneados como análogos:** 50 rutas fuente, todas verificadas con
`git ls-files -- <path>` y por tanto versionadas.  
**Patrón de cambios preexistentes:** el estado de trabajo contiene modificaciones ajenas en
`apps/api/library/**`, `apps/web/**` y artefactos de `e2e`; se han leído como estado actual y
no se han revertido ni editado.  
**Fecha de extracción:** 2026-09-13.
