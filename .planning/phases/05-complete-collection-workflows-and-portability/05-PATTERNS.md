---
phase: "05"
slug: "complete-collection-workflows-and-portability"
status: complete
created: "2026-09-12"
---

# Fase 5: mapa de patrones reutilizables

**Mapeado:** 2026-09-12  
**Archivos de backend analizados:** 20  
**Archivos de integración/E2E documentados:** 8  
**Regla de fuentes:** todos los análogos citados pasan `git ls-files`; no se han usado espejos runtime.

Este documento orienta al planner sobre código existente que debe extenderse. La prosa está en español y los identificadores, snippets, rutas y nombres de tests conservan el inglés del repositorio. La otra sesión es propietaria de `apps/web/**` y `design/**`; las rutas web de este documento son únicamente un handoff de contrato y no deben ser editadas por esta sesión.

## Alcance que debe reflejar el plan

- Implementar registro/login/sesión Django real reutilizando el contrato ya existente; no mezclar cuentas reales con `DemoAccountIdentity`.
- Añadir biografía, avatar validado y visibilidad `public/private`; el alias sigue siendo `User.username` y no es editable.
- Mantener `LibraryEntry` como entidad de estado/rating por obra y extender `OwnedCopy` con metadatos de compra y conservación.
- Añadir comentarios únicos por usuario/obra y listas manuales de juegos que ya pertenezcan a la colección, con orden persistido y privacidad explícita.
- Derivar toda proyección pública de allowlists manuales y aplicar ownership desde `request.user` en queryset, serializer, servicio y constraint.
- Implementar solo CSV UTF-8 versionado y seguro. JSON, preview/importación y conflictos de `PORT-02`/`PORT-03` quedan fuera y requieren reconciliación documental antes de declarar esos requisitos satisfechos.

## File Classification

| Archivo nuevo/modificado previsto | Rol | Flujo de datos | Análogo más cercano | Calidad |
|---|---|---|---|---|
| `apps/api/accounts/models.py` | model | CRUD | el mismo `accounts/models.py` (clases `DemoAccount*`) | exacto de app |
| `apps/api/accounts/serializers.py` | serializer/projection | request-response | el mismo `accounts/serializers.py` | exacto |
| `apps/api/accounts/services.py` | service | CRUD/transaccional | `apps/api/library/services.py` | role-match |
| `apps/api/accounts/views.py` | controller | request-response | el mismo `accounts/views.py` | exacto |
| `apps/api/accounts/urls.py` | route | request-response | `apps/api/library/urls.py` | role-match |
| `apps/api/accounts/migrations/0003_phase5_profile.py` | migration | batch/schema | `apps/api/accounts/migrations/0002_demo_accounts.py` | exacto de app |
| `apps/api/accounts/tests/test_profile.py` | test | CRUD/seguridad | `test_public_profile.py` + `test_registration.py` | role-match |
| `apps/api/accounts/tests/test_public_profile.py` | test | projection/privacy | el mismo archivo | exacto |
| `apps/api/library/models.py` | model | CRUD | el mismo `library/models.py` (`OwnedCopy`) | exacto |
| `apps/api/library/serializers.py` | serializer | request-response | el mismo `library/serializers.py` | exacto |
| `apps/api/library/services.py` | service | CRUD/transaccional | el mismo `library/services.py` | exacto |
| `apps/api/library/export.py` | utility | file-I/O/transform | sin análogo de exportación; `library/services.py` aporta scoping | parcial |
| `apps/api/library/views.py` | controller | request-response | el mismo `library/views.py` | exacto |
| `apps/api/library/urls.py` | route | request-response | el mismo `library/urls.py` | exacto |
| `apps/api/library/migrations/0003_phase5_comments_lists.py` | migration | batch/schema | `apps/api/library/migrations/0002_rating_copies.py` | exacto de app |
| `apps/api/library/migrations/0004_phase5_copy_metadata.py` | migration | batch/schema | `apps/api/library/migrations/0003_phase5_comments_lists.py` | exacto de app |
| `apps/api/library/tests/test_copies.py` | test | CRUD/concurrencia | el mismo archivo | exacto |
| `apps/api/library/tests/test_comments.py` | test | CRUD/ownership | `test_copies.py` + `test_entry.py` | role-match |
| `apps/api/library/tests/test_lists.py` | test | CRUD/ordering | `test_copies.py` + `test_entry.py` | role/data-flow match |
| `apps/api/library/tests/test_export.py` | test | file-I/O/security | `accounts/tests/test_public_profile.py` + `library/tests/test_schema.py` | parcial |
| `apps/api/library/tests/test_schema.py` | test | schema/constraints | el mismo archivo | exacto |
| `e2e/collection-workflows.spec.ts` | test | request-response/browser | `e2e/demo-journey.spec.ts` | exacto de runner |
| `e2e/a11y.spec.ts` | test | browser/accessibility | el mismo archivo | exacto |

Las páginas y componentes web que la otra sesión puede modificar están documentados en [Handoff de integración web](#handoff-de-integración-web), pero no forman parte de los archivos que esta sesión debe editar.

## Pattern Assignments

### `apps/api/accounts/models.py` — perfil, favoritos y privacidad

**Análogo:** `apps/api/accounts/models.py:35-71`, donde las entidades auxiliares apuntan al `AUTH_USER_MODEL`, usan UUID/OneToOne, `ordering` y `CheckConstraint`.

**Patrón a copiar:** mantener `User.username` como alias canónico inmutable. Si se introduce un `AccountProfile` separado, relacionarlo con `settings.AUTH_USER_MODEL` y no duplicar alias. Los valores de privacidad deben ser un enum pequeño (`public/private`) y los favoritos deben quedar limitados por constraints de `(user, slot)` y `(user, work)`, con slots `1..5`. Las restricciones de negocio también deben comprobarse en el servicio; el modelo es la última defensa.

```python
class DemoAccountIdentity(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demo_identity"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_simulated=True),
                name="accounts_demo_identity_always_simulated",
            ),
        ]
```

No aceptar `user_id` del cliente para perfil o favoritos: el propietario se deriva de la sesión.

### `apps/api/accounts/serializers.py` — DTO owner y proyección pública

**Análogo:** `apps/api/accounts/serializers.py:1-9,22-25,28-55`.

**Allowlist pública obligatoria:** construir el diccionario a mano. La futura proyección puede añadir biografía, avatar, favoritos públicos, listas públicas y comentarios públicos solo si la política de visibilidad los autoriza; nunca usar `ModelSerializer` para el perfil público.

```python
def _escape_text(value: str) -> str:
    return str(value)

return {
    "alias": _escape_text(user.username),
    "activity": activity,
    "summary": summary,
}
```

El serializer owner debe excluir `username` de la escritura y validar límites de biografía/avatar. Los serializers de favoritos, comentarios, listas y copias deben usar `ChoiceField`, `UUIDField`, `max_length`, `allow_null` y `DecimalField`/validación equivalente; no confiar en coerciones del frontend.

### `apps/api/accounts/services.py` — actualización atómica de perfil/favoritos

**Análogo:** `apps/api/library/services.py:101-191`, especialmente `save_library_configuration()`.

No existe aún un service de cuentas; el planner debe crear uno con funciones estrechas como actualización de perfil y reemplazo del conjunto completo de favoritos. Usar `transaction.atomic()`, validar que cada obra pertenece a la colección del usuario, bloquear el conjunto afectado cuando sea necesario y guardar cambios coherentes en una sola transacción.

```python
with transaction.atomic():
    entry = LibraryEntry.objects.select_for_update().filter(user=user, work=work).first()
    # validate first, then persist the complete authoritative payload
```

El servicio no debe cambiar `User.username`, estampar `DemoAccountIdentity` ni aceptar una identidad de propietario desde el payload.

### `apps/api/accounts/views.py` — sesión, perfil owner y perfil público

**Análogos:** `apps/api/accounts/views.py:46-112` para CSRF/login y `:115-189` para registro; `:217-241` para perfil público.

Conservar estos controles:

```python
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
```

El login debe mantener tipo de payload estricto, mensaje uniforme `401`, resolución case-insensitive sin enumeración, `login(request, user)` y redirect relativo allowlisted. El registro debe mantener `validate_password`, `transaction.atomic()`, respuesta uniforme a la carrera de duplicados, `login()` que rota sesión y throttle `registration`. Logout sigue siendo `IsAuthenticated` y llama a `logout()`.

Los endpoints privados de perfil/favoritos deben ser `IsAuthenticated` y recibir el propietario solo de `request.user`. Los endpoints públicos deben resolver `public/private` antes de serializar y devolver la misma forma no enumerable para alias inexistente o proyección no visible cuando la decisión de privacidad lo requiera.

### `apps/api/accounts/urls.py` — contrato de rutas

**Análogo:** `apps/api/library/urls.py:16-24`.

Mantener imports de views explícitos, `app_name`, converters de ruta y nombres estables. Añadir las rutas de `me/profile/favorites` bajo `api/accounts/` sin mover las existentes:

```python
path("me/", MeView.as_view(), name="me"),
path("profiles/<str:alias>/", PublicProfileView.as_view(), name="public-profile"),
```

Registrar el app solo mediante el include ya existente en `apps/api/config/urls.py:16-22`; no crear un router paralelo.

### `apps/api/accounts/migrations/0003_phase5_profile.py` — schema de perfil/favoritos

**Análogo:** `apps/api/accounts/migrations/0002_demo_accounts.py:8-32`.

La migración debe depender de `accounts.0002_demo_accounts` y de `settings.AUTH_USER_MODEL`, crear solo tablas/campos nuevos y preservar las cuentas demo y reales. Copiar la forma de `CreateModel`, `OneToOneField`/`ForeignKey`, `ordering` y constraints explícitos. Preferir campos avatar/biografía/visibilidad nulables o con defaults seguros para que el despliegue sea reversible y no destruya usuarios existentes.

### `apps/api/accounts/tests/test_profile.py` — pruebas owner/privacy

**Análogos:** `apps/api/accounts/tests/test_public_profile.py:20-52,70-125` y `apps/api/accounts/tests/test_registration.py:50-74,182-269`.

Usar fixtures `User.objects.create_user`, `APIClient`, `@pytest.mark.django_db` y clientes autenticados. Cubrir persistencia tras nueva lectura, alias ausente del payload editable, biografía/avatar inválidos, cinco slots, sexto/duplicado rechazado, obra fuera de colección rechazada, aislamiento entre usuarios y privacidad pública/privada. Reutilizar la comprobación recursiva de claves prohibidas del test público.

Para auth/security conservar el patrón de cliente CSRF de `test_registration.py:41-47` y la aserción de sesión persistente de `:50-74`; no sustituirlo por credenciales hardcodeadas en E2E.

### `apps/api/accounts/tests/test_public_profile.py` — allowlist y privacidad

**Análogo exacto:** el mismo archivo, especialmente `FORBIDDEN_KEYS` y `_assert_no_forbidden_keys()` en `:20-52`, y aislamiento A/B en `:114-125`.

Ampliar la allowlist aprobada de forma positiva y mantener una lista negativa que incluya `email`, `password`, IDs internos, `copies`, `format`, `purchase`, `location`, `notes` y `rating_half_steps`. Probar que perfil/actividad/favoritos/listas/comentarios privados no aparecen desde cliente anónimo o usuario B, mientras el propietario conserva acceso.

### `apps/api/library/models.py` — copias, comentarios y listas

**Análogo exacto:** `apps/api/library/models.py:18-44` para entidad asociativa única y `:67-92` para `OwnedCopy`.

No mover estado/rating a la copia. Extender `OwnedCopy` con fecha de compra, precio decimal no negativo, moneda normalizada, tienda y campos de conservación/ubicación; rechazar conservación/ubicación para `format="digital"` tanto en servicio como en `CheckConstraint`. Mantener `user`, `work`, `release`, `edition`, UUID e idempotency key.

Los comentarios deben tener `user`, `work`, texto, visibilidad y timestamps, con `UniqueConstraint(user, work)`. Las listas deben tener propietario, nombre, visibilidad y timestamps; sus items deben referenciar `work`, guardar `position` y usar `UniqueConstraint(list, work)` y `UniqueConstraint(list, position)`. La inserción de un item exige `LibraryEntry(user=user, work=work)`.

```python
models.UniqueConstraint(
    fields=("user", "work"),
    name="library_unique_entry_per_user_work",
)
```

### `apps/api/library/serializers.py` — inputs completos y outputs allowlisted

**Análogo exacto:** `apps/api/library/serializers.py:10-49`.

Mantener serializers declarativos y pequeños. Extender `LibraryCopyConfigurationSerializer` y `OwnedCopySerializer` con los metadatos nuevos; añadir serializers separados para comentario, lista, item y reorder. El serializer de reorder debe recibir una lista de UUIDs, rechazar duplicados y no inferir posiciones del orden de llegada sin validación completa.

```python
class LibraryConfigurationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["pending", "playing", "completed", "abandoned"], allow_null=True
    )
    rating_half_steps = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)
    copies = LibraryCopyConfigurationSerializer(many=True)
```

La respuesta pública no debe reutilizar estos DTOs owner: requiere una proyección allowlisted propia.

### `apps/api/library/services.py` — ownership, transacciones e idempotencia

**Análogo exacto:** `apps/api/library/services.py:41-98` para creación idempotente y `:101-191` para reemplazo transaccional.

Todas las operaciones nuevas deben recibir `user` explícitamente desde la view, filtrar cada entidad por ese usuario y validar relaciones de obra/release/edition antes de guardar. Usar `transaction.atomic()` para CRUD compuesto, `select_for_update()` en reordenación/reemplazo, y dejar que constraints PostgreSQL resuelvan carreras de inserción; recuperar `IntegrityError` solo cuando el contrato lo permita.

```python
existing = OwnedCopy.objects.filter(user=user, idempotency_key=idempotency_key).first()
if existing is not None:
    return existing, False

with transaction.atomic():
    copy = OwnedCopy.objects.create(user=user, work=work, release=release, ...)
```

Para listas, validar el conjunto completo antes de asignar posiciones consecutivas y guardar el reorder en una transacción. El endpoint de reorder exige `expected_version`; una versión obsoleta produce HTTP 409 sin cambios, mientras la coincidencia se procesa con `select_for_update()` y commit, incrementa la versión y queda cubierta por un oráculo de orden/versión tras reload. Para comentarios, `get_or_create`/update/delete debe estar siempre acotado por `(user, work/comment_id)` y las obras fuera de `LibraryEntry` deben producir error sin mutación.

### `apps/api/library/export.py` — contrato CSV de solo lectura

**Análogo:** no existe exportador en el código actual. El scoping debe copiar `library/views.py:42-55` y `:167-170`; la serialización debe usar `csv` de la biblioteca estándar.

Crear una función pura de filas/contrato y otra de descarga si el diseño lo requiere. Fijar `schema_version=1`, cabecera y orden deterministas; construir cada fila desde campos nombrados, nunca desde `values()` amplio ni desde `__dict__`. El exportador debe recibir el usuario y consultar solo sus datos visibles, sin `password`, sesiones, IDs internos innecesarios ni datos de otro usuario.

Contrato propuesto por RESEARCH: `schema_version`, `record_type`, `work_slug`, `work_title`, `status`, `rating_half_steps`, `copy_format`, `purchase_date`, `price`, `currency`, `store`, `conservation_state`, `storage_location`, `comment`, `list_name`, `list_visibility`, `list_position`, `favorite_slot`. Los campos no aplicables quedan vacíos.

```python
def neutralize_spreadsheet_formula(value: str) -> str:
    if value[:1] in ("=", "+", "-", "@"):
        return "\t" + value
    return value
```

Aplicar la función a cada celda antes de `csv.writer`, mantenerla idempotente y devolver UTF-8 con `newline=""`, content type CSV y `Content-Disposition` controlado. No implementar JSON ni importación como código “preparatorio”.

### `apps/api/library/views.py` — endpoints owner-scoped y descarga

**Análogo exacto:** `apps/api/library/views.py:35-88` para lectura owner-scoped, `:162-191` para DTO/servicio/error y `:194-217` para reemplazo completo.

El patrón de lectura debe ser literalmente equivalente a:

```python
entries = LibraryEntry.objects.filter(user=request.user).select_related("work")
copies = OwnedCopy.objects.filter(user=request.user, work=work)
```

Cada view mutante usa `IsAuthenticated`, instancia el serializer, resuelve una `GameWork` no-DLC con `get_object_or_404`, llama al servicio y devuelve errores de validación como `400` sin filtrar excepciones internas. Los recursos ajenos deben parecer inexistentes (`404`) o seguir el contrato explícito, nunca modificar tras comprobar propiedad.

La view de exportación solo prepara la respuesta; el orden, allowlist y neutralización pertenecen a `export.py`. La descarga no debe consultar una proyección pública para obtener datos privados del propio usuario.

### `apps/api/library/urls.py` — rutas de comentario/lista/exportación

**Análogo exacto:** `apps/api/library/urls.py:16-24`.

Añadir rutas explícitas bajo el include actual, con converters UUID donde corresponda, nombres estables y separación entre colección owner y proyección pública. No cambiar las rutas de recomendaciones ni crear un segundo namespace.

### `apps/api/library/migrations/0003_phase5_comments_lists.py` — schema relacional de comentarios y listas

**Análogo exacto:** `apps/api/library/migrations/0002_rating_copies.py:9-62`.

Depender de `library.0002_rating_copies` y de la migración de catálogo que corresponda. Crear `GameComment`, `CustomList` y `CustomListItem`, incluyendo la versión entera inicial de `CustomList` que usa el reorder optimista; declarar `UniqueConstraint` y `CheckConstraint` con nombres estables. El plan debe incluir `migrate` sobre base vacía y una comprobación real de constraints PostgreSQL, no solo `makemigrations --check`.

### `apps/api/library/migrations/0004_phase5_copy_metadata.py` — schema de metadatos de copias

**Análogo exacto:** `apps/api/library/migrations/0003_phase5_comments_lists.py` y `apps/api/library/migrations/0002_rating_copies.py`.

Extender `OwnedCopy` con los campos de compra y conservación, junto con sus `CheckConstraint`, dependiendo explícitamente de `library.0003_phase5_comments_lists`. La separación deja el límite de datos de comentarios/listas en 0003 y el incremento de metadatos de inventario en 0004, de modo que cada plan puede migrar, inspeccionar y probar su propio contrato contra PostgreSQL antes de continuar con la siguiente wave.

### División intencionada frente al patrón genérico de una migración de fase

Aunque el patrón genérico de esta fase podría concentrar todo el esquema en una única `0003_phase5_collection_workflows.py`, Fase 5 conserva dos migraciones consecutivas por una razón de dependencia y verificación: `0003_phase5_comments_lists.py` acompaña al plan 05-02 y crea el agregado de comentarios/listas; `0004_phase5_copy_metadata.py` acompaña al plan 05-03 y solo extiende `OwnedCopy`. Esta división mantiene la cadena Django lineal, hace visible que el plan 05-03 depende del contrato ya migrado de listas/comentarios y permite que los gates `[BLOCKING]` de cada wave comprueben constraints distintos sin mezclar dos cortes de dominio. No cambia el alcance ni introduce una entidad alternativa: únicamente expresa en el historial de migraciones la secuencia ya fijada por los planes.

### `apps/api/library/tests/test_copies.py` — metadatos y carreras

**Análogo exacto:** `apps/api/library/tests/test_copies.py:61-113` para relaciones inválidas, `:168-218` para concurrencia y `:221-280` para reemplazo/eliminación de configuración.

Ampliar los fixtures actuales de work/release/edition/user. Probar persistencia de compra, precio, moneda y tienda; conservación/ubicación solo física; precio inválido; dos usuarios aislados; replay de idempotency key; y que la configuración completa conserva los campos al actualizar/eliminar copias. Mantener `@pytest.mark.django_db(transaction=True)` y `connections.close_all()` en pruebas concurrentes.

### `apps/api/library/tests/test_comments.py` — CRUD único por obra

**Análogos:** `test_copies.py:55-113` para fixtures/`force_authenticate` y `test_entry.py:131-142,210-229` para ownership y autenticación.

Cada test debe verificar creación, actualización y borrado del propio comentario, unicidad `(user, work)`, payloads de texto límite/hostiles, obra no perteneciente a la colección, usuario B incapaz de leer/editar/borrar A y visibilidad pública/privada. Las respuestas deben comprobar DTO positivo y claves prohibidas, no solo `status_code`.

### `apps/api/library/tests/test_lists.py` — colección y reordenación

**Análogos:** `test_copies.py:61-99` para validación de relaciones y `test_entry.py:131-142,247-282` para aislamiento/concurrencia.

Cubrir CRUD owner-scoped, rechazo de una obra no presente en `LibraryEntry`, duplicado de obra por lista, posiciones consecutivas, reorder completo, reorder con IDs ajenos/faltantes/extras, concurrencia y visibilidad. Confirmar que eliminar una obra de la colección no concede permiso para añadirla a listas nuevas y que la política para items existentes está documentada.

### `apps/api/library/tests/test_export.py` — CSV, privacidad y fórmula

**Análogos parciales:** `apps/api/accounts/tests/test_public_profile.py:20-52,104-125` para allowlist/hostile payloads y `apps/api/library/tests/test_schema.py:20-60` para inspección estructural PostgreSQL.

No hay un test de exportación previo que copiar. Crear fixtures A/B y verificar cabecera exacta/versionada, UTF-8, orden repetible, colección/rating/listas/campos de copia permitidos, ausencia de password/sesión/IDs privados de terceros y aislamiento. Inyectar `=`, `+`, `-`, `@` en títulos, tiendas, comentarios y alias; comprobar que ninguna celda empieza con una fórmula ejecutable tras neutralización.

### `apps/api/library/tests/test_schema.py` — migraciones y constraints

**Análogo exacto:** `apps/api/library/tests/test_schema.py:12-60`.

Extender las aserciones de `information_schema`, `pg_constraint` y `_meta.get_field()` para comentarios, listas, slots favoritos y los nuevos campos/constraints de `OwnedCopy`. Mantener la comprobación de dependencia de migración y `@pytest.mark.django_db`; el test debe fallar si desaparece una constraint aunque el endpoint aún parezca funcionar.

### `e2e/collection-workflows.spec.ts` — tracer de navegador

**Análogo exacto:** `e2e/demo-journey.spec.ts:19-51,122-193,236-292`.

Reutilizar `installCsrfOriginShim`, la lectura de credenciales desde entorno y las consultas Playwright por label/role. El tracer debe probar registro/login real, sesión después de reload, perfil, copia con metadatos, comentario, lista/reorder, privacidad y descarga CSV. No introducir secretos, usuarios/passwords fijos ni valores en URLs/traces.

```typescript
await page.getByLabel("Usuario").fill(username);
await page.getByLabel("Contraseña").fill(password);
await page.getByRole("button", { name: "Entrar" }).click();
await page.waitForURL(/\/es\/catalogue$/);
```

Para la descarga, parsear la respuesta/archivo y verificar contenido, cabecera y neutralización, no solo que el botón sea visible.

### `e2e/a11y.spec.ts` — accesibilidad del handoff

**Análogo exacto:** `e2e/a11y.spec.ts:18-46,48-82,91-117`.

Añadir profile, detalle con comentarios, colección/listas, formulario de copias y acción de exportación a la matriz de rutas y ejecutar desktop/mobile. Mantener viewport mínimo de `375x812`, `axe-core` local y fallo para violaciones `critical`/`serious`; complementar con teclado y estados de error accesibles.

## Shared Patterns

### Ownership y autorización

**Fuentes:** `apps/api/library/views.py:40-55,101-104,162-191,220-240`; `apps/api/library/services.py:138-166,194-208`; `apps/api/accounts/views.py:192-215`.

Aplicar siempre esta cadena: `IsAuthenticated` → queryset filtrado por `request.user` → serializer sin propietario sustituible → service transaccional → constraint PostgreSQL. Nunca aceptar `user_id`/`owner_id` desde JSON ni hacer una comprobación de propiedad después de `update/delete`.

### Validación, errores y sesión

**Fuentes:** `apps/api/accounts/views.py:32-40,66-112,141-189`; `apps/api/config/settings.py:110-149,159-166`; `apps/api/library/views.py:172-207`.

Conservar `SessionAuthentication`, CSRF para mutaciones, mensajes uniformes de credenciales, `ScopedRateThrottle`, `validate_password`, cookies `HttpOnly`/`SameSite=Lax` y respuestas `400/401/403/404/409/429` previsibles. Los detalles de `ValidationError` se traducen a respuestas de API; no se exponen stacks, credenciales o DSN.

### Allowlists y privacidad

**Fuentes:** `apps/api/accounts/serializers.py:48-55`; `apps/api/accounts/tests/test_public_profile.py:20-52,104-125`; `apps/web/app/[locale]/profiles/[alias]/page.tsx:36-55`.

Construir DTOs públicos desde campos permitidos y decidir visibilidad antes de cargar/serializar datos. El frontend renderiza únicamente las claves del DTO; no se usa como control de acceso. `friends-only` no debe aparecer como enum ni como rama simulada.

### Migraciones y base de datos

**Fuentes:** `apps/api/accounts/migrations/0002_demo_accounts.py:8-32`; `apps/api/library/migrations/0002_rating_copies.py:9-62`; `apps/api/library/tests/test_schema.py:12-60`.

Mantener cadenas de migración separadas por app, campos compatibles con datos existentes, nombres de constraints estables y verificación contra PostgreSQL real. No introducir SQLite ni una tabla paralela de inventario.

### Tests

**Fuentes:** `apps/api/accounts/tests/test_auth.py:16-34,52-73,110-218`; `apps/api/library/tests/test_copies.py:168-218`; `e2e/a11y.spec.ts:67-82`.

Los tests backend usan pytest-django/APIClient y fixtures reales de PostgreSQL; los tests de throttle limpian `cache`; los tests concurrentes cierran conexiones por hilo. Los tests E2E consultan roles/labels accesibles y no contienen secretos.

## Handoff de integración web

Esta sesión no modifica `apps/web/**` ni `design/**`. La otra sesión debe adaptar sus archivos a los contratos backend y mantener estos análogos versionados:

| Punto de integración | Análogo actual y patrón que conservar |
|---|---|
| `apps/web/lib/api.ts` | `fetchPublicProfile()` en `:191-212` y `fetchMyLibrary()` en `:239-272`: tipos DTO explícitos, `cache: "no-store"`, forward explícito de cookies en Server Components y tratamiento claro de `404/401/403/error`. |
| `apps/web/app/[locale]/collection/page.tsx` | `:62-76` redirige si falta `sessionid`, `:71-75` reenvía cookies y `:86-108` filtra/ordena datos recibidos. Añadir listas/exportación sin duplicar autorización en cliente. |
| `apps/web/app/[locale]/profiles/[alias]/page.tsx` | `:36-55` y `:88-105`: renderizar solo el DTO allowlisted y usar `notFound()` ante proyección no visible/404. |
| `apps/web/app/[locale]/games/[id]/page.tsx` | `:30-35` para sesión/cookies y `:164-170` para integrar controles owner en el aside. La sección de comentarios debe seguir el mismo detalle de juego y no tocar contratos de recomendaciones. |
| `apps/web/components/LibraryControls.tsx` | `:68-83` obtiene CSRF y hace POST same-origin; `:131-151` carga estado/copies; `:160-189` guarda configuración y refresca. Extender el formulario de copia, no crear una segunda vía de persistencia. |
| `apps/web/app/[locale]/login/page.tsx` y `register/page.tsx` | Las journeys existentes de `e2e/demo-journey.spec.ts:122-193,236-292` son el contrato observable: labels accesibles, errores de throttle y redirect a catálogo. |
| `apps/web/components/AppShell.tsx` / diccionarios | Mantener navegación autenticada, estados loading/empty/error y claves ES/EN; no hardcodear prosa nueva en componentes. |
| `design/**` | Handoff únicamente: integrar los estados público/privado, comentario vacío/error, reorder inválido, metadatos de copia y descarga. No existe un análogo backend para editar este árbol. |

El E2E de esta fase debe coordinarse con los cambios de la otra sesión para fijar rutas, labels y nombres de `data-testid` antes de cerrar el plan; el backend no debe adaptarse a selectores visuales que contradigan el contrato API.

## No Analog Found

| Archivo/capacidad | Motivo | Fuente para planificar |
|---|---|---|
| `apps/api/library/export.py` | No existe exportador CSV/JSON en el repositorio. | Contrato CSV de `05-RESEARCH.md`, módulo `csv` estándar, neutralización formula-like y pruebas nuevas. |
| `apps/api/accounts/services.py` | No existe service de cuentas separado. | `apps/api/library/services.py` como patrón de transacción/ownership; mantener funciones pequeñas. |
| Comentarios y listas | No hay entidades equivalentes actuales. | `LibraryEntry`/`OwnedCopy`, constraints PostgreSQL y reglas D-04/D-07 de `05-CONTEXT.md`. |
| `PORT-02` y `PORT-03` | La decisión D-09 los difiere explícitamente. | Reconciliación documental; no crear endpoints ni tests de feature de importación. |

## Notas de reconciliación para el planner

- `PROF-01` todavía dice “editar alias” en `REQUIREMENTS.md`, pero D-01 bloquea esa edición: planificar una reconciliación explícita y cubrir solo biografía/avatar.
- `PORT-01` todavía enumera CSV y JSON en roadmap/requisitos, pero D-08 fija CSV-only: marcarlo como parcial o actualizar la fuente canónica con autorización; no declarar JSON implementado.
- El criterio de aceptación del roadmap que exige JSON/importación entra en conflicto con el contexto de fase; el plan debe dejar la limitación visible y asignar `PORT-02/03` a una decisión/fase futura.
- La elección avatar URL HTTPS frente a upload binario sigue siendo una decisión de implementación. Si se mantiene URL, validar longitud/esquema y no hacer fetch/proxy server-side; si se exige upload, abrir checkpoint antes de añadir almacenamiento/media.

## Metadata

**Ámbito de búsqueda:** `apps/api/accounts`, `apps/api/library`, `apps/api/config`, `e2e`, páginas/componentes web indicados por `05-CONTEXT.md`, y mapas `.planning/codebase/{ARCHITECTURE,CONVENTIONS,STRUCTURE,TESTING}`.  
**Fuentes primarias leídas:** `05-CONTEXT.md`, `05-RESEARCH.md`, `ROADMAP.md`, `AGENTS.md`, `CONVENTIONS.md` y los análogos enumerados arriba.  
**Restricción respetada:** no se editaron `apps/web/**`, `design/**` ni ningún otro archivo.

## PATTERNS COMPLETE
