# Fase 5: Complete Collection Workflows and Portability - Investigación

**Investigado:** 2026-09-12  
**Dominio:** perfiles, autenticación de sesión, colección relacional, inventario, privacidad y exportación CSV segura  
**Confianza global:** HIGH para los límites y patrones internos; MEDIUM para las recomendaciones de seguridad apoyadas en documentación oficial externa.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-00:** La Fase 5 debe ofrecer registro e inicio de sesión reales, no solo
  cuentas demo. Se reutiliza el sistema de sesión de Django y la persistencia
  PostgreSQL existente, con contraseñas hasheadas, validación de contraseña,
  protección CSRF, respuestas que no enumeren usuarios, rate limiting,
  autorización owner-scoped y pruebas de seguridad, persistencia y flujo de
  navegador.
- **D-00b:** El registro crea una cuenta persistente y autenticada; las cuentas
  sintéticas siguen existiendo como fixtures de demo separadas de las cuentas
  reales. El nombre de usuario es el alias público inmutable.
- **D-01:** El alias público coincide con el nombre de usuario de login y no es
  editable. Añadir biografía y avatar como datos editables del perfil.
- **D-02:** La colección y la estantería de cinco juegos favoritos tienen una
  opción de privacidad `pública` o `privada`. La estantería de favoritos es
  editable y está limitada a cinco juegos.
- **D-03:** La opción `solo amigos` se difiere junto con el sistema de
  amistades; no se implementa una visibilidad que el backend no pueda resolver
  de forma verificable.
- **D-04:** Cada usuario puede mantener un único comentario por juego. El
  comentario se crea, edita y elimina desde una sección de comentarios del
  juego.
- **D-05:** El autor siempre puede consultar y gestionar su propio comentario.
  La visibilidad de comentarios de terceros queda restringida por privacidad;
  la variante para amigos se habilitará únicamente cuando exista el modelo de
  amistades correspondiente.
- **D-06:** Las listas son colecciones manuales de juegos que el usuario ha
  añadido a su colección. El usuario puede crearlas, editarlas, eliminarlas y
  ordenar manualmente sus juegos.
- **D-07:** Cada lista tiene privacidad `pública` o `privada`. No se añade una
  privacidad de amigos en esta fase.
- **D-08:** La portabilidad de esta fase se limita a exportación CSV. El
  contenido exportado corresponde a los datos visibles en la aplicación y no
  expone campos privados no presentes en esa proyección.
- **D-09:** JSON e importación con vista previa, errores por fila y conflictos
  deterministas quedan fuera de la implementación actual. La planificación
  debe señalar que PORT-02 y PORT-03 siguen pendientes y proponer la
  reconciliación explícita de esos requisitos con el roadmap, sin ocultar la
  reducción de alcance.

### the agent's Discretion

- La representación técnica del avatar, siempre que respete validación,
  límites de tamaño, atribución y ausencia de secretos.
- La taxonomía concreta de estados de conservación y la representación de
  precio/moneda, siempre que los campos sean auditables, opcionales cuando
  proceda y no se filtren en proyecciones privadas.
- Si una lista puede contener un juego varias veces; se recomienda impedir
  duplicados y mantener un orden explícito estable.
- La forma visual exacta de la sección de comentarios, respetando los patrones
  accesibles existentes y sin cambiar el contrato público de recomendaciones.

### Deferred Ideas (OUT OF SCOPE)

- Sistema de amistades y privacidad `solo amigos` para colecciones, favoritos,
  listas y comentarios; pertenece a una ampliación social posterior.
- Exportación JSON e importación con previsualización, validación por fila y
  resolución determinista de conflictos; PORT-02 y PORT-03 requieren una
  decisión de roadmap antes de implementarse.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Descripción vigente en REQUIREMENTS.md | Soporte de esta investigación |
|---|---|---|
| PROF-01 | `User can edit their alias, avatar, and biography.` | El alias contradice D-01; implementar solo biografía/avatar y reconciliar el texto del requisito antes del cierre. |
| LIB-03 | `User can create, edit, and delete their own comments.` | Entidad única por usuario/obra, servicio transaccional, endpoint owner-scoped y proyección pública condicionada por privacidad. |
| LIB-04 | `User can create and order custom game lists.` | Lista manual de obras ya presentes en `LibraryEntry`, posiciones únicas y reordenación atómica. |
| INV-03 | `Each copy can record purchase date, price, currency, and store.` | Extensión de `OwnedCopy`, validación de precio/moneda y pruebas de persistencia/privacidad. |
| INV-04 | `A physical copy can record conservation state and storage location.` | Campos opcionales con constraint que impide conservar datos físicos en copias digitales. |
| PORT-01 | `User can export their collection, ratings, and lists as versioned CSV and JSON.` | Implementar únicamente CSV versionado según D-08; JSON queda pendiente y el requisito no debe marcarse completo sin ajuste documental. |
| PORT-02 | `User can preview and validate an import before applying it.` | Fuera de la implementación actual por D-09; conservar como pendiente explícito. |
| PORT-03 | `Import reports row-level errors and applies deterministic duplicate and conflict rules.` | Fuera de la implementación actual por D-09; conservar como pendiente explícito. |
| PORT-04 | `CSV exports neutralise potentially malicious spreadsheet formulas.` | Exportador con neutralización de celdas formula-like y prueba de bytes/celdas. |
| PRIV-01 | `Public projections use an explicit allowlist of fields.` | Extender el patrón manual de `build_public_profile`; no usar serialización automática de modelos con campos privados. |

</phase_requirements>

## Project Constraints (from AGENTS.md)

- La prosa nueva de `.planning/**` debe estar en español; identificadores, comentarios de código, nombres de tests, logs y comandos permanecen en inglés. `[VERIFIED: AGENTS.md:32-38; CONVENTIONS.md:13-16]`
- La fuente canónica del vault vivo debe consultarse y sus decisiones deben enlazar a la fuente canónica; el vault no sustituye a `.planning/**` ni a `docs/**`. `[VERIFIED: AGENTS.md:54-70; ideas-vault/README.md:18-29]`
- No se deben publicar secretos, cookies, tokens, credenciales, cadenas de conexión ni logs sin revisar en artefactos o issues. `[VERIFIED: AGENTS.md:72-77; CONVENTIONS.md:105-117]`
- Esta investigación no modifica `apps/web/**`, `design/**` ni el vault: la restricción explícita del autor limita el único cambio permitido a este `05-RESEARCH.md`. La coordinación de UI se debe resolver en la otra sesión y mediante contratos API revisables. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:117-143; ASSUMED]`
- No se levantan workers ni se ejecutan cálculos pesados durante la investigación. La verificación propuesta queda descrita para el ejecutor y se ejecutará contra PostgreSQL/Playwright en el momento adecuado. `[VERIFIED: .planning/config.json:11-31; ASSUMED]`

## Summary

La fase debe tratarse como una ampliación del modular monolith Django/DRF existente, no como una sustitución de autenticación ni como un segundo almacén. La base ya tiene usuarios Django, sesiones persistentes, CSRF explícito en login/registro, validadores de contraseña, errores uniformes y throttling por scope; el trabajo de fase debe conservar esos contratos y añadir perfil, privacidad, comentarios, listas y exportación sin abrir una vía de escritura que acepte un `user_id` arbitrario. `[VERIFIED: apps/api/accounts/views.py:46-112,115-197; apps/api/config/settings.py:38-49,103-149; .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:32-40]`

La entidad de inventario correcta sigue siendo `OwnedCopy`: estado y rating permanecen en `LibraryEntry`, mientras compra, moneda, tienda y conservación se añaden a la copia y se guardan con la transacción de configuración existente. Comentarios y listas deben vivir en el dominio de biblioteca o en un app de colección estrechamente relacionado, con `user` y `work` como límites de ownership, constraints de unicidad y proyecciones públicas construidas por allowlist. `[VERIFIED: apps/api/library/models.py:18-31,67-92; apps/api/library/services.py:101-191; .planning/codebase/ARCHITECTURE.md]`

La portabilidad se reduce deliberadamente a un único CSV UTF-8 versionado con orden determinista, filas explícitas y neutralización de fórmulas. JSON, importación, previsualización y conflictos no se deben implementar como "preparación" porque D-09 los difiere; PORT-02 y PORT-03 deben quedar pendientes y PORT-01 debe reconciliarse con la decisión CSV-only antes de declarar la fase completa. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-80; .planning/ROADMAP.md:252-259; .planning/REQUIREMENTS.md:37-40]`

**Recomendación principal:** construir primero un tracer backend de registro/login real → perfil owner-scoped → una copia con metadatos → comentario/lista → exportación CSV, y después completar las variantes de privacidad, concurrencia, proyecciones públicas y pruebas de navegador.

## Architectural Responsibility Map

| Capacidad | Tier primario | Tier secundario | Motivo |
|---|---|---|---|
| Registro, login, logout, sesiones, CSRF y rate limiting | API / Backend | Frontend Server | Django ya posee sesiones, middleware CSRF, `AuthenticationMiddleware` y permisos; el navegador solo transporta cookies y el header CSRF. `[VERIFIED: apps/api/config/settings.py:23-46; apps/api/accounts/views.py:46-197; CITED: https://docs.djangoproject.com/en/5.2/howto/csrf/]` |
| Perfil, avatar, biografía y visibilidad | API / Backend | Browser / Client | La autorización, validación y proyección pública deben ser server-side; el cliente no puede decidir qué campos privados salen. `[VERIFIED: apps/api/accounts/serializers.py:1-9,48-55; .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:44-50]` |
| Favoritos de cinco posiciones | Database / Storage | API / Backend | Las posiciones y la unicidad usuario/obra necesitan constraints; el endpoint debe devolver una forma fija de cinco slots, incluidos huecos nulos. `[ASSUMED]` |
| Comentarios por obra | API / Backend | Database / Storage | La regla un comentario por usuario/obra es una restricción relacional y la edición debe comprobar el propietario. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:55-60; ASSUMED para el nombre de entidad]` |
| Listas y orden manual | API / Backend | Database / Storage | La pertenencia a colección se comprueba en servicio y el orden se guarda como posición; reordenar debe ser una operación atómica. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:65-69; ASSUMED para el diseño de tablas]` |
| Metadatos de copias | Database / Storage | API / Backend | `OwnedCopy` ya relaciona usuario, obra, release y edición; la nueva información pertenece a la copia, no a la obra ni al rating. `[VERIFIED: apps/api/library/models.py:67-92; apps/api/library/services.py:101-191]` |
| Proyección pública | API / Backend | Frontend Server | La allowlist debe construirse explícitamente y el frontend solo renderiza ese DTO. `[VERIFIED: apps/api/accounts/serializers.py:48-55; apps/web/app/[locale]/profiles/[alias]/page.tsx:36-55]` |
| Exportación CSV | API / Backend | Browser / Client | El backend crea la vista autorizada, ordena filas y neutraliza fórmulas; el navegador solo descarga la respuesta. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-75; CITED: https://owasp.org/www-community/attacks/CSV_Injection]` |

## Standard Stack

### Core

| Tecnología | Versión | Uso en la fase | Por qué se mantiene |
|---|---:|---|---|
| Python | `==3.13.*` | Backend, servicios, exportador y tests | Es la restricción declarada del proyecto. `[VERIFIED: pyproject.toml:5-12]` |
| Django | `5.2.17` | ORM, migraciones, auth, sesiones, CSRF y validación | Ya es la base de cuentas y PostgreSQL; Django documenta sesiones cookie-based, hashing y validación de contraseñas. `[VERIFIED: pyproject.toml:6-8; apps/api/accounts/views.py:15-25; CITED: https://docs.djangoproject.com/en/5.2/topics/auth/]` |
| Django REST Framework | `3.18.0` | Serializers, APIViews, permisos y throttling | Las vistas actuales usan `APIView`, `IsAuthenticated` y `ScopedRateThrottle`. `[VERIFIED: pyproject.toml:7-9; apps/api/accounts/views.py:22-25; apps/api/library/views.py:13-17]` |
| PostgreSQL | `18.6` | Persistencia canónica, constraints, sesiones y migraciones | SQLite está prohibido por la configuración fail-closed y los tests de integración esperan PostgreSQL. `[VERIFIED: .planning/codebase/ARCHITECTURE.md; apps/api/config/settings.py:67-101; .planning/codebase/TESTING.md]` |
| `psycopg[binary]` | `3.3.5` | Driver PostgreSQL | Ya está fijado en el proyecto. `[VERIFIED: pyproject.toml:9-12]` |

### Supporting

| Herramienta | Versión | Uso | Cuándo usar |
|---|---:|---|---|
| pytest | `9.1.1` | Tests backend | Unitarios de servicios, integración ORM/migraciones y seguridad. `[VERIFIED: pyproject.toml:16-25]` |
| pytest-django | `4.14.0` | Base de datos de tests y cliente Django | Todas las pruebas de entidades nuevas deben correr contra PostgreSQL, no SQLite. `[VERIFIED: pyproject.toml:17-26; .planning/codebase/TESTING.md]` |
| Playwright | `1.62.1` | Flujos reales de navegador y CSRF/sesión | Registro, login, perfil, CRUD de comentario/lista, metadatos de copia, privacidad y descarga CSV. `[VERIFIED: package.json:20-30; e2e/demo-journey.spec.ts:119-213]` |
| `axe-core` | `4.13.0` | Auditoría automatizada de accesibilidad | Reutilizar la inyección de `axe-core` que ya usa E2E y añadir páginas de la fase. `[VERIFIED: package.json:21-29; e2e/demo-journey.spec.ts:38-46]` |
| `csv` de la biblioteca estándar | — | Serialización CSV | Evita una dependencia nueva y permite controlar delimitador, quoting, codificación y orden. `[ASSUMED; no se propone instalar una dependencia]` |

### Alternatives Considered

| En lugar de | No usar | Motivo |
|---|---|---|
| `OwnedCopy` extendido | Nuevo modelo paralelo de inventario | Duplicaría release/edición/formato e introduciría dos fuentes para la misma copia. `[VERIFIED: apps/api/library/models.py:67-92; ASSUMED]` |
| Django session auth | JWT o proveedor social | D-00 exige reutilizar sesiones Django y no hay una decisión para un proveedor externo. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:32-40]` |
| Avatar URL validada, sin descarga server-side | Upload local o almacenamiento externo nuevo | El stack actual no declara media/object storage para perfiles; una URL no obliga a añadir infraestructura ni a que el servidor haga fetch. La UI debe aplicar `next/image`/allowlist según su contrato y nunca el backend debe seguir URLs arbitrarias. `[VERIFIED: .planning/codebase/INTEGRATIONS.md; ASSUMED]` |
| Una tabla CSV versionada | JSON paralelo o archivo ZIP multiformato | D-08 fija CSV-only y D-09 difiere JSON/importación. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-80]` |

**Instalación:** no se recomienda instalar paquetes externos para esta fase. Si el ejecutor descubre una necesidad real, deberá detenerse en el gate de dependencia del proyecto y obtener aprobación humana antes de cambiar manifests/lockfiles. `[VERIFIED: CONVENTIONS.md:61-70; .planning/codebase/CONCERNS.md]`

## Package Legitimacy Audit

No aplica: el enfoque recomendado reutiliza las dependencias ya fijadas y no añade paquetes. `[ASSUMED: recomendación de implementación]`

## Architecture Patterns

### System Architecture Diagram

```text
Browser / Playwright
  ├─ GET /api/accounts/csrf/ ───────────────► Django CSRF cookie
  ├─ POST login/register + X-CSRFToken ─────► Session auth + PostgreSQL
  └─ owner-scoped writes ───────────────────► APIView → serializer → service
                                                │
                                                ├─ AccountProfile / Favorites
                                                ├─ LibraryEntry / OwnedCopy
                                                ├─ GameComment / GameList / ListItem
                                                └─ transaction.atomic() + constraints
                                                │
Public profile/game projections ◄─────────────┘
  └─ explicit allowlist + public/private gate

Authenticated CSV request
  └─ permission + owner query → deterministic export rows
       → formula neutralization → UTF-8 CSV download
```

El flujo mantiene la separación actual: navegador/Next.js consume API JSON, Django valida y autoriza, y PostgreSQL es el estado canónico. `[VERIFIED: .planning/codebase/ARCHITECTURE.md; apps/api/config/urls.py:16-22; apps/web/lib/api.ts:258-271]`

### Recommended Project Structure

```text
apps/api/accounts/
├── models.py              # perfil, visibilidad y favoritos
├── serializers.py         # DTOs owner/public allowlisted
├── services.py            # actualizaciones atómicas del perfil/favoritos
├── views.py               # profile/me/favorites endpoints
└── tests/test_profile.py

apps/api/library/
├── models.py              # OwnedCopy extendido, comentarios y listas
├── serializers.py         # copy/comment/list/export input/output DTOs
├── services.py            # ownership, reordenación y transacciones
├── export.py              # contrato CSV versionado y neutralización
├── views.py               # endpoints owner-scoped y descarga
├── migrations/00xx_phase5.py
└── tests/test_comments.py, test_lists.py, test_export.py

e2e/
└── collection-workflows.spec.ts
```

La estructura se alinea con la convención existente de añadir modelos, serializers, views, URLs y tests dentro del app de dominio; los nombres nuevos son una propuesta y deben conservarse en inglés en código. `[VERIFIED: .planning/codebase/STRUCTURE.md; .planning/codebase/CONVENTIONS.md; ASSUMED para los módulos nuevos]`

### Patrón 1: owner-scoped y autorización por construcción

**Qué:** todas las lecturas/escrituras privadas parten de `request.user` y la consulta filtra simultáneamente la entidad y el usuario; el payload nunca recibe un propietario sustituible. `[VERIFIED: apps/api/library/views.py:35-55,101-104,162-191,194-217,220-240]`

**Ejemplo existente:** el endpoint de copias ya expone la consulta exacta:

> `copies = OwnedCopy.objects.filter(user=request.user, work=work)` `[VERIFIED: apps/api/library/views.py:167-170]`

```python
copies = OwnedCopy.objects.filter(user=request.user, work=work)
```

La misma forma debe usarse para comentarios, listas, favoritos y exportación. Un `user_id` recibido del cliente, un queryset sin filtro de usuario o una comprobación de propiedad después de modificar la fila son anti-patrones. `[ASSUMED: prescripción derivada del patrón existente]`

### Patrón 2: serializer estricto + servicio transaccional

**Qué:** el serializer valida tipos, límites y enum; el servicio comprueba relaciones de obra/release, aplica reglas de negocio y agrupa cambios que no deben quedar parciales dentro de `transaction.atomic()`. `[VERIFIED: apps/api/library/serializers.py:25-50; apps/api/library/services.py:101-191]`

El contrato actual ya usa `LibraryConfigurationSerializer` con `status`, `rating_half_steps` y `copies`, y `save_library_configuration` trata la lista de copias como autoritativa: actualiza, inserta y elimina filas omitidas dentro de una transacción. `[VERIFIED: apps/api/library/serializers.py:42-50; apps/api/library/services.py:104-107,117-191]` Las nuevas propiedades de copia deben atravesar exactamente las mismas tres capas: DTO, servicio y persistencia.

### Patrón 3: proyección pública allowlisted

**Qué:** construir cada respuesta pública como diccionario/DTO explícito, no mediante `ModelSerializer` automático ni serialización del objeto entero. `[VERIFIED: apps/api/accounts/serializers.py:1-9,48-55]`

El contrato actual devuelve literalmente las claves `"alias"`, `"activity"` y `"summary"`; esa allowlist debe ampliarse solo con campos aprobados como biografía, avatar, favoritos públicos, listas públicas y comentarios públicos. `[VERIFIED: apps/api/accounts/serializers.py:48-55; apps/api/accounts/tests/test_public_profile.py:20-42,70-111]` No deben aparecer `email`, IDs internos, ratings personales, copias, formato, compra, ubicación, notas ni precio privado. `[VERIFIED: apps/api/accounts/serializers.py:1-9; apps/api/accounts/tests/test_public_profile.py:20-42]`

### Patrón 4: reordenación con posiciones estables

**Qué:** cada elemento de lista tiene una posición entera y la operación de reorder recibe una lista completa de IDs pertenecientes a la lista; el servicio valida que no falte ni sobre ningún elemento, reasigna posiciones consecutivas y hace commit atómicamente. `[ASSUMED]`

**Reglas prescriptivas:** impedir duplicados de obra por lista mediante `UniqueConstraint(list, work)`, usar `UniqueConstraint(list, position)` y comprobar `LibraryEntry.objects.filter(user=request.user, work_id=...)` antes de insertar. Si una obra deja la colección, no debe seguir pudiendo añadirse a una lista nueva; la política sobre listas ya existentes debe ser explícita, preferiblemente conservarla hasta que el propietario la edite y bloquear nuevas adiciones. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:65-69; ASSUMED para constraints concretas]`

### Patrón 5: exportación como contrato de lectura

**Qué:** el exportador no reutiliza ciegamente el DTO público ni el modelo; define un esquema CSV versionado, hace una consulta owner-scoped y transforma a filas allowlisted. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-75; ASSUMED para el esquema propuesto]`

Contrato recomendado para `csv_schema_version=1`: cabecera fija con `schema_version`, `record_type`, `work_slug`, `work_title`, `status`, `rating_half_steps`, `copy_format`, `purchase_date`, `price`, `currency`, `store`, `conservation_state`, `storage_location`, `comment`, `list_name`, `list_visibility`, `list_position`, `favorite_slot`. Los campos que no apliquen se exportan vacíos; el exportador no añade columnas privadas no declaradas. `[ASSUMED]`

Orden recomendado, estable y documentado: perfil/visibilidad; favoritos por `favorite_slot`; colección por `work_slug` y clave interna solo como desempate; comentarios por `work_slug`; listas por nombre/clave estable y sus elementos por `list_position`. No usar `created_at` como único orden porque dos filas pueden compartir resolución temporal. `[ASSUMED]`

### Patrón 6: cinco slots de favoritos, no cinco escrituras ambiguas

**Qué:** almacenar favoritos con `user`, `work` y `slot` entero restringido a `1..5`, con unicidad por `(user, slot)` y `(user, work)`. El DTO siempre devuelve cinco posiciones, con `null` en huecos, y el servicio reemplaza el conjunto completo de favoritos dentro de una transacción. `[ASSUMED]`

Este modelo cumple la decisión de una estantería editable limitada a cinco juegos sin rellenar automáticamente juegos que el usuario no eligió; la API puede aceptar exactamente cinco entradas normalizadas y rechazar duplicados, slots fuera de rango o una obra que no pertenezca a la colección. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:46-48; ASSUMED para la forma de almacenamiento]`

### Anti-Patterns to Avoid

- **Editar `User.username` desde el formulario de perfil:** contradice D-01 y rompe el alias de login/URL; el DTO de edición debe excluirlo. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:44-48; apps/api/accounts/urls.py:14-21]`
- **Confiar en el frontend para privacy/ownership:** un cliente puede cambiar JSON, IDs y campos ocultos; la decisión debe repetirse en serializer, servicio, queryset y proyección. `[VERIFIED: apps/api/library/views.py:35-55,162-191; apps/api/accounts/serializers.py:48-55]`
- **Usar `ModelSerializer` para la proyección pública:** un campo privado futuro se filtraría por accidente. `[VERIFIED: apps/api/accounts/serializers.py:1-9,48-55]`
- **Mover estado/rating a `OwnedCopy`:** rompe el contrato de varias copias independientes por una obra. `[VERIFIED: apps/api/library/models.py:67-70]`
- **Implementar JSON/importación “solo para completar el roadmap”:** contradice D-08/D-09 y convierte una decisión diferida en alcance no autorizado. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-80]`
- **Tratar DRF throttling como defensa completa contra fuerza bruta:** la documentación oficial advierte que el throttling de aplicación no es una medida completa de seguridad y que sus operaciones pueden tener carreras. `[CITED: https://www.django-rest-framework.org/api-guide/throttling/]`

## Don't Hand-Roll

| Problema | No construir | Usar |
|---|---|---|
| Hashing/verificación de contraseñas | Hash propio, salt manual o almacenamiento reversible | `django.contrib.auth`, `create_user`, `authenticate` y `AUTH_PASSWORD_VALIDATORS`. Django documenta hashing configurable y PBKDF2 por defecto. `[CITED: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/; VERIFIED: apps/api/accounts/views.py:159-185]` |
| CSRF de JSON/fetch | Token inventado en localStorage o endpoint sin protección | `CsrfViewMiddleware`/`csrf_protect`, `ensure_csrf_cookie` y header `X-CSRFToken`. `[CITED: https://docs.djangoproject.com/en/5.2/howto/csrf/; VERIFIED: apps/api/accounts/views.py:46-58,115-139; apps/api/config/settings.py:38-46]` |
| Autorización de objetos | Permisos duplicados en cada componente web | Querysets filtrados por `request.user`, `IsAuthenticated`, constraints y servicios transaccionales. `[VERIFIED: apps/api/library/views.py:35-55; apps/api/library/services.py:194-208]` |
| Exportación CSV | Concatenación manual de comas/quotes o `str()` sin quoting | Módulo `csv` estándar, cabecera fija, `newline=""`, UTF-8 y neutralización formula-like. `[ASSUMED; CITED: https://owasp.org/www-community/attacks/CSV_Injection]` |
| Rate limiting | Contador global en memoria dentro de la vista | `ScopedRateThrottle` como capa básica más configuración de proxy/cache y mensajes uniformes. No asumir garantías absolutas bajo concurrencia. `[VERIFIED: apps/api/accounts/views.py:61-64,136-139; CITED: https://www.django-rest-framework.org/api-guide/throttling/]` |
| Orden de listas | Orden implícito por `created_at` o índice del array del frontend | Columna de posición, constraints y reorder completo atómico. `[ASSUMED]` |

**Clave:** los problemas difíciles de esta fase no son dibujar formularios sino preservar invariantes entre sesión, propiedad, privacidad, concurrencia, exportación y migraciones. Cada invariante debe existir en más de una capa: validación para feedback, servicio para reglas y PostgreSQL para la última defensa. `[VERIFIED: apps/api/library/services.py:79-98,117-191; apps/api/library/models.py:33-44,85-92; ASSUMED para la extensión]`

## Common Pitfalls

### Pitfall 1: dejar que el requisito antiguo mande sobre el contexto

**Qué ocurre:** el plan implementa alias editable, JSON o importación porque aparecen en `REQUIREMENTS.md`/`ROADMAP.md`, aunque D-01 y D-09 los contradicen. `[VERIFIED: .planning/REQUIREMENTS.md:12,37-40; .planning/ROADMAP.md:252-259; .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:44-48,73-80]`  
**Cómo evitarlo:** planificar una tarea de reconciliación explícita: `PROF-01` pasa a biografía/avatar con alias inmutable; `PORT-01` se divide o se redefine como CSV; `PORT-02/03` permanecen pendientes para una fase posterior. No marcar esos IDs como completos mientras la fuente canónica no se actualice. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:76-80; ASSUMED para el procedimiento documental]`

### Pitfall 2: privacidad añadida solo en el frontend

**Qué ocurre:** un perfil privado sigue respondiendo actividad, favoritos, listas o comentarios porque el endpoint siempre serializa la misma consulta. `[ASSUMED]`  
**Cómo evitarlo:** resolver visibilidad en la API antes de construir la allowlist; owner ve sus datos, visitante ve solo proyección pública, y `solo amigos` no aparece ni como enum ni como rama falsa. Probar 200/404/empty según la política sin filtrar existencia de datos privados. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:49-60; apps/api/accounts/views.py:217-241; ASSUMED para el código nuevo]`

### Pitfall 3: permitir listas con obras fuera de la colección

**Qué ocurre:** una lista se convierte en una búsqueda guardada o en una recomendación y deja de representar la colección personal. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:65-67]`  
**Cómo evitarlo:** comprobar la existencia de `LibraryEntry(user=request.user, work=...)` dentro de la misma transacción que inserta el item y añadir tests de rechazo owner-scoped. `[VERIFIED: apps/api/library/models.py:18-26; ASSUMED para las nuevas consultas]`

### Pitfall 4: romper el contrato de `save_library_configuration`

**Qué ocurre:** se añaden metadatos a un endpoint paralelo o se actualiza solo la copia del primer formulario; los campos se pierden al guardar la configuración completa. `[VERIFIED: apps/api/library/services.py:101-191; apps/api/library/tests/test_copies.py:221-256]`  
**Cómo evitarlo:** extender el serializer completo, el servicio y la respuesta de configuración juntos; probar crear, editar, eliminar, replay de idempotency key, dos usuarios y rollback ante release/edition inválidos. `[VERIFIED: apps/api/library/serializers.py:32-50; apps/api/library/tests/test_copies.py:61-113,221-280]`

### Pitfall 5: copiar campos privados en la exportación

**Qué ocurre:** el exportador reutiliza un `values()` amplio y termina exponiendo IDs internos, notas, sesiones o campos destinados solo al propietario/administración. `[VERIFIED: apps/api/accounts/serializers.py:1-9; apps/api/accounts/tests/test_public_profile.py:20-42]`  
**Cómo evitarlo:** contrato de columnas versionado, querysets owner-scoped y pruebas que inspeccionen cabecera y todas las celdas en busca de campos prohibidos. `[ASSUMED]`

### Pitfall 6: CSV ejecutable al abrirlo en una hoja de cálculo

**Qué ocurre:** un título, alias, tienda o comentario que empieza con `=`, `+`, `-` o `@` se interpreta como fórmula. `[CITED: https://owasp.org/www-community/attacks/CSV_Injection]`  
**Cómo evitarlo:** aplicar una función única de neutralización antes de pasar cada valor al writer; el control debe ser idempotente para no añadir tabs repetidos. OWASP recomienda prefijar con tab en el campo quoted para el caso Excel y advierte que la mitigación altera el valor subyacente. `[CITED: https://owasp.org/www-community/attacks/CSV_Injection]`

### Pitfall 7: asumir que throttling resuelve la seguridad de login

**Qué ocurre:** el endpoint devuelve errores distintos, revela si existe el usuario o depende de un contador no atómico como única barrera. `[VERIFIED: apps/api/accounts/views.py:32-35,61-64,72-97; CITED: https://www.django-rest-framework.org/api-guide/throttling/]`  
**Cómo evitarlo:** conservar mensaje uniforme, validación de tipo, CSRF, rotación de sesión, rate scope, cookies seguras y pruebas de 401/403/429; documentar que el límite depende de cache y proxy. `[VERIFIED: apps/api/accounts/tests/test_auth.py:52-73,110-118,198-218; apps/api/accounts/tests/test_registration.py:210-269; CITED: https://www.django-rest-framework.org/api-guide/throttling/]`

### Pitfall 8: asumir que los mapas históricos describen el checkout actual

**Qué ocurre:** el mapa de código fechado 2026-09-04 no refleja todos los cambios actuales; por ejemplo, el código leído ya tiene migraciones `accounts` y `library` y los endpoints de auth/library. `[VERIFIED: .planning/codebase/ARCHITECTURE.md; apps/api/accounts/migrations/0001_initial.py:9-25; apps/api/library/migrations/0001_initial.py:9-45; apps/api/accounts/urls.py:14-21; apps/api/library/urls.py:16-24]`  
**Cómo evitarlo:** usar mapas para orientación y abrir siempre los archivos fuente actuales antes de fijar nombres de modelos, enums, rutas o dependencias en un plan. `[VERIFIED: .planning/codebase/ARCHITECTURE.md; .planning/codebase/STRUCTURE.md; ASSUMED como regla de planificación]`

## Code Examples

### Consulta owner-scoped existente

Los valores y nombres usados en el ejemplo aparecen literalmente en la implementación actual: `OwnedCopy`, `request.user` y `work`. `[VERIFIED: apps/api/library/views.py:162-170]`

```python
work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
copies = OwnedCopy.objects.filter(user=request.user, work=work)
return Response({"copies": [serialize_copy(copy) for copy in copies]})
```

### Allowlist pública existente

La implementación actual construye literalmente las claves `"alias"`, `"activity"` y `"summary"`; el ejemplo se limita a ese contrato leído. `[VERIFIED: apps/api/accounts/serializers.py:48-55]`

```python
return {
    "alias": _escape_text(user.username),
    "activity": activity,
    "summary": summary,
}
```

### Contrato propuesto para una exportación segura

La siguiente forma es una prescripción de fase, no código existente. Los prefijos se basan en la lista formula-like de OWASP (`=`, `+`, `-`, `@`); debe convertirse en código inglés y cubrirse con tests. `[ASSUMED; CITED: https://owasp.org/www-community/attacks/CSV_Injection]`

```python
def neutralize_spreadsheet_formula(value: str) -> str:
    if value[:1] in ("=", "+", "-", "@"):
        return "\t" + value
    return value
```

### Actualización propuesta de favoritos/listas

La siguiente skeleton expresa invariantes de diseño, no nombres ya existentes en el repositorio: `[ASSUMED]`

```python
with transaction.atomic():
    validate_five_favorite_slots(user=request.user, slots=payload["favorites"])
    replace_favorites(user=request.user, slots=payload["favorites"])
    validate_collection_membership(user=request.user, work_ids=payload["work_ids"])
    reorder_list_items(list_obj=list_obj, work_ids=payload["work_ids"])
```

## Portability and Scope Reconciliation

### Divergencia entre roadmap, requisitos y contexto

La hoja de ruta asigna a la fase `PROF-01, LIB-03, LIB-04, INV-03, INV-04, PORT-01, PORT-02, PORT-03, PORT-04, PRIV-01` y todavía describe exportación CSV y JSON, previsualización y resultados de importación. `[VERIFIED: .planning/ROADMAP.md:247-258; .planning/REQUIREMENTS.md:219-229]` El contexto posterior fija alias inmutable, CSV-only y exclusión de JSON/importación. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:44-48,73-80]`

La reconciliación recomendada es:

1. **Durante la planificación:** incluir una nota de alcance y una matriz que marque `PORT-02`/`PORT-03` como diferidos, `PORT-01` como parcialmente satisfacible solo con CSV y `PROF-01` como contradictorio en la palabra “alias”. No crear tareas de JSON/importación para hacer pasar artificialmente el roadmap. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:76-80; ASSUMED para la forma de la nota]`
2. **Durante la ejecución o el cierre documental autorizado:** actualizar la fuente canónica de requisitos/roadmap para separar `PORT-01-CSV` de una futura capacidad JSON/importación, o mantener `PORT-01` pendiente por no cubrir JSON. Registrar explícitamente que `PORT-02` y `PORT-03` siguen abiertos y asignarlos a una futura fase/decisión. `[ASSUMED: decisión de mantenimiento documental que requiere autorización del autor]`
3. **Criterio de aceptación de esta fase:** CSV versionado, seguro, owner-scoped y limitado a datos visibles; no aceptar JSON, importación ni alias editable como condición oculta. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:44-48,73-80]`

### Frontera de datos exportables

El usuario autenticado puede exportar su proyección propia, incluidos los datos privados que la aplicación le permite ver; eso no autoriza incluir secretos, sesiones, hashes, IDs internos innecesarios ni datos de otro usuario. Los perfiles/listas públicos solo exponen su proyección allowlisted y el exportador no debe usarla como atajo para saltarse privacy. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-75; apps/api/accounts/serializers.py:1-9; ASSUMED para la separación owner/public]`

### Avatar

Recomendación para v1: avatar opcional como URL HTTPS validada y acotada por longitud, sin que Django haga fetch, redirección ni proxy del recurso; conservar atribución si la URL procede de una fuente externa y rechazar esquemas no HTTPS. Esto evita introducir media storage, procesamiento de imágenes o SSRF en una fase centrada en workflows. `[VERIFIED: .planning/codebase/INTEGRATIONS.md; .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:82-90; ASSUMED]`

Si el autor exige upload binario, debe abrirse una decisión adicional sobre almacenamiento persistente, límites MIME/bytes, decodificación segura, nombres aleatorios, antivirus, limpieza de archivos y deployment; no sustituirlo silenciosamente por filesystem local efímero. `[ASSUMED]`

### Copias e inventario

Extender `OwnedCopy` con `purchase_date`, `price`, `currency`, `store`, `conservation_state` y `storage_location`, todos opcionales salvo la relación semántica que el payload necesite. Recomiendo `DecimalField` no float, precio no negativo, moneda textual de tres letras en mayúsculas y un enum pequeño y documentado para conservación; estos tamaños/taxonomías son propuestas del agente y requieren confirmación si afectan UI o datos históricos. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:86-90; ASSUMED]`

Para digital, `conservation_state` y `storage_location` deben ser nulos y rechazarse si llegan con `format="digital"`; para físico pueden ser nulos porque son datos opcionales. La validación debe repetirse en serializer/servicio y en un `CheckConstraint` PostgreSQL para impedir bypass del API. `[VERIFIED: apps/api/library/models.py:62-80; apps/api/library/tests/test_rating.py:62-71; ASSUMED para el constraint nuevo]`

## Runtime State Inventory

No es una fase de rename/refactor. No se requiere inventario de cadenas antiguas en estado runtime; sí se requiere una migración PostgreSQL normal para nuevas tablas/campos y un smoke de migración en una base vacía. `[ASSUMED: clasificación de la fase]`

## Environment Availability

| Dependencia | Necesaria para | Disponible en la auditoría | Versión observada | Fallback |
|---|---|---|---|---|
| Docker Engine | PostgreSQL/API y tests backend reproducibles | ✓ | `29.2.1` | No usar el Python host para tests de base de datos si no coincide el entorno. `[VERIFIED: auditoría de entorno 2026-09-12; .planning/codebase/TESTING.md]` |
| Docker Compose | Stack local | ✓ | `v5.0.2` | Ninguno preferido; el proyecto documenta Compose. `[VERIFIED: auditoría de entorno 2026-09-12; infra/compose.yaml]` |
| Python | Herramientas/test local | ✓ | `3.13.15` | Ejecutar dentro de Docker si el host deja de satisfacer `==3.13.*`. `[VERIFIED: auditoría de entorno 2026-09-12; pyproject.toml:5]` |
| Node.js | Playwright/build web | ✓ | `v24.13.0` | Usar imagen/CI fijada si el host diverge. `[VERIFIED: auditoría de entorno 2026-09-12; package.json:6-8]` |
| Corepack | Activar pnpm fijado | ✓ | `0.34.5` | `corepack` según `packageManager`; no asumir `pnpm` global. `[VERIFIED: auditoría de entorno 2026-09-12; package.json:5]` |
| pnpm | Tests/build web | ✗ como comando global | — | Usar Corepack con la versión declarada; no instalar globalmente sin aprobación. `[VERIFIED: auditoría de entorno 2026-09-12; package.json:5]` |
| uv | Resolver entorno Python | ✗ como comando global | — | Docker usa el entorno del proyecto; instalar uv solo con autorización si el ejecutor lo necesita. `[VERIFIED: auditoría de entorno 2026-09-12; pyproject.toml]` |

No se relanzaron workers ni cálculos de recomendación. La auditoría observó procesos de workers ya existentes, pero no los modificó ni los usa como dependencia de esta fase. `[VERIFIED: auditoría de entorno 2026-09-12; ASSUMED sobre no dependencia]`

## Validation Architecture

La validación Nyquist está habilitada porque `.planning/config.json` no la desactiva y `workflow.nyquist_validation` está en `true`. `[VERIFIED: .planning/config.json:11-31]` No se ejecutaron tests durante la investigación para respetar la restricción operativa; el ejecutor debe correrlos por ola.

### Test Framework

| Propiedad | Valor |
|---|---|
| Backend | `pytest==9.1.1` + `pytest-django==4.14.0`, PostgreSQL real |
| Config backend | `apps/api/pytest.ini` y `pyproject.toml` |
| Comando rápido backend | `docker compose -f infra/compose.yaml run --rm api pytest apps/api/accounts/tests apps/api/library/tests -q` |
| Suite backend completa | `docker compose -f infra/compose.yaml run --rm api pytest -q` |
| Browser | `@playwright/test==1.62.1` + `axe-core==4.13.0` |
| Comando browser | `corepack pnpm exec playwright test e2e/collection-workflows.spec.ts` |
| Suite browser completa | `corepack pnpm exec playwright test` |
| Frontend unit/component | `corepack pnpm --dir apps/web test --run` |

Los runners y archivos de configuración están fijados en el repositorio; el backend está configurado para descubrir `test_*.py` y exige configuración Django. `[VERIFIED: pyproject.toml:17-26; apps/api/pytest.ini:1-7; package.json:5-11; .planning/codebase/TESTING.md]`

### Phase Requirements → Test Map

| Req ID | Comportamiento verificable | Tipo | Comando/ubicación | Estado de infraestructura |
|---|---|---|---|---|
| PROF-01 | Registro real persiste usuario; alias no aparece en payload editable; biografía/avatar se guardan y se vuelven a leer. | backend + browser | `apps/api/accounts/tests/test_profile.py`; `e2e/collection-workflows.spec.ts` | Wave 0: crear ambos |
| LIB-03 | Un comentario por usuario/obra; CRUD propietario; otro usuario no edita; detalle muestra solo comentario permitido. | integración + browser | `apps/api/library/tests/test_comments.py`; E2E game detail | Wave 0 |
| LIB-04 | Lista CRUD; solo juegos de colección; reorder estable; duplicados rechazados. | integración + browser | `apps/api/library/tests/test_lists.py`; E2E collection | Wave 0 |
| INV-03 | Compra/fecha/precio/moneda/tienda sobreviven reload y no cruzan usuarios. | integración + browser | ampliar `test_copies.py`; E2E copy form | Wave 0: casos nuevos |
| INV-04 | Campos de conservación solo para físico; digital rechaza estado/ubicación; proyección pública no filtra. | integración + seguridad | `test_copies.py`, `test_public_profile.py` | Wave 0 |
| PORT-01 | Descarga CSV versionado con colección/rating/listas y sin JSON/importación; orden reproducible. | integración + browser | `test_export.py`; E2E download | Wave 0 |
| PORT-02 | Debe permanecer explícitamente pendiente; ningún endpoint de importación se implementa. | revisión documental | matriz de alcance y plan | No convertir en test de feature |
| PORT-03 | Debe permanecer explícitamente pendiente; no hay conflictos/import rows en esta fase. | revisión documental | matriz de alcance y plan | No convertir en test de feature |
| PORT-04 | Celdas con `=`, `+`, `-`, `@` no quedan ejecutables al abrir exportación. | unit + integration | `test_export.py` con contenido hostil | Wave 0 |
| PRIV-01 | Respuestas públicas contienen solo campos allowlisted; privado no expone actividad/favs/listas/comentarios. | integración + browser | ampliar `test_public_profile.py`; E2E privacy | Wave 0 |

### Casos backend imprescindibles

- Auth: payloads con objetos/listas en username/password, contraseña débil, alias duplicado por casefold, CSRF ausente, credenciales inválidas indistinguibles, sesión persistente, logout, 429 y no enumeración. `[VERIFIED: apps/api/accounts/tests/test_auth.py:52-73,110-218; apps/api/accounts/tests/test_registration.py:50-269]`
- Ownership: usuario A nunca lee/edita/borrar comentarios, listas, copias o exportación de B; un UUID válido de B debe dar 404/403 según contrato, no mutar nada. `[VERIFIED: apps/api/library/tests/test_entry.py:131-142,177-229; ASSUMED para entidades nuevas]`
- Concurrencia: dos inserts del mismo comentario/list item/favorite slot no duplican; reorder concurrente deja posiciones únicas; extensión de `OwnedCopy` mantiene idempotencia. `[VERIFIED: apps/api/library/tests/test_copies.py:168-218; ASSUMED para nuevos modelos]`
- Migración: base vacía aplica todas las migraciones; constraints de unicidad y check se inspeccionan en PostgreSQL. `[VERIFIED: apps/api/library/tests/test_schema.py:12-60; ASSUMED para migración nueva]`

### Browser journeys imprescindibles

1. Registro real → sesión → perfil editable → logout → visita protegida redirigida; comprobar que ninguna credencial aparece en URL, texto visible, descarga o trace. `[VERIFIED: e2e/demo-journey.spec.ts:119-213,220-292; ASSUMED extensión]`
2. Login real de dos usuarios → cada uno modifica su colección/copia/comentario/lista → comprobar aislamiento después de reload. `[VERIFIED: e2e/demo-journey.spec.ts:122-193; ASSUMED extensión]`
3. Crear cinco favoritos, intentar sexto y duplicado, alternar pública/privada y comprobar perfil público desde una sesión ajena/anónima. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:46-50; ASSUMED]`
4. Crear lista, añadir solo juegos propios, reordenar, eliminar; verificar orden y error accesible. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:65-69; ASSUMED]`
5. Guardar compra/conservación y descargar CSV; parsear contenido en test, comprobar cabecera/version, orden, privacidad y neutralización formula-like. `[VERIFIED: .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:73-75; ASSUMED]`
6. Ejecutar axe y navegación por teclado en profile, detail comments, collection lists, copy form y export action a desktop/mobile. `[VERIFIED: AGENTS.md:19; e2e/a11y.spec.ts:346-445; ASSUMED nuevas superficies]`

### Sampling Rate

- Por tarea backend: `docker compose -f infra/compose.yaml run --rm api pytest <test-file> -q`.
- Por ola: `docker compose -f infra/compose.yaml run --rm api pytest apps/api/accounts/tests apps/api/library/tests -q` y el E2E de la capacidad.
- Gate de fase: suite backend completa, Vitest, Playwright y chequeos de dependencias verdes antes de verificación manual. `[VERIFIED: .planning/codebase/TESTING.md; .planning/config.json:11-31; ASSUMED para el gate de fase]`

### Wave 0 Gaps

- [ ] `apps/api/accounts/tests/test_profile.py` — perfil, alias inmutable, avatar, biografía, privacidad y cinco slots.
- [ ] `apps/api/library/tests/test_comments.py` — unicidad, CRUD, visibilidad y ownership.
- [ ] `apps/api/library/tests/test_lists.py` — pertenencia a colección, posiciones, duplicados, privacidad y concurrencia.
- [ ] `apps/api/library/tests/test_export.py` — contrato CSV, ordering, UTF-8, privacidad y fórmula.
- [ ] `e2e/collection-workflows.spec.ts` — tracer browser de auth, perfil, colección, comentario, lista, copia y descarga.
- [ ] Migración nueva y tests de schema para constraints de `OwnedCopy`, favoritos, comentarios y listas.
- [ ] Contrato compartido frontend/API revisado con la otra LLM; esta investigación no modifica `apps/web/**`.

## Security Domain

La configuración del proyecto tiene `security_enforcement: true` y ASVS level 1. `[VERIFIED: .planning/config.json:11-31]` La taxonomía OWASP aplicable incluye autenticación, gestión de sesión, control de acceso, validación/sanitización/codificación y criptografía almacenada. `[CITED: https://devguide.owasp.org/en/03-requirements/05-asvs/]`

### Applicable ASVS Categories

| Categoría | Aplica | Control para esta fase |
|---|---|---|
| V2 Authentication | Sí | Django auth, password hashing/validators, errores uniformes, registro persistente y rate scope. `[CITED: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/; VERIFIED: apps/api/config/settings.py:103-149]` |
| V3 Session Management | Sí | SessionMiddleware, AuthenticationMiddleware, cookies HttpOnly/SameSite, rotación al login y logout invalidante. `[VERIFIED: apps/api/config/settings.py:38-46,159-167; apps/api/accounts/views.py:183-197; CITED: https://docs.djangoproject.com/en/5.2/topics/auth/]` |
| V4 Access Control | Sí | `IsAuthenticated`, owner-scoped querysets, 404/403 sin IDOR y allowlists públicas. `[VERIFIED: apps/api/library/views.py:35-55,162-240; apps/api/accounts/serializers.py:48-55]` |
| V5 Input Validation | Sí | serializers estrictos, límites bio/avatar/comment/list, enums privacy/format, validación de precio y neutralización CSV. `[VERIFIED: apps/api/library/serializers.py:10-50; CITED: https://owasp.org/www-community/attacks/CSV_Injection]` |
| V6 Stored Cryptography | Sí, acotado a credenciales | No guardar contraseñas ni tokens propios; usar hasher Django y nunca exportar `User.password`. `[CITED: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/; VERIFIED: apps/api/accounts/serializers.py:1-9]` |
| V7 Error Handling and Logging | Sí | Respuestas no enumerables, mensajes sin secretos, no incluir payload sensible en excepciones/CSV/traces. `[VERIFIED: apps/api/accounts/views.py:32-40; CONVENTIONS.md:61-70,105-117]` |
| V8 Data Protection | Sí | Separar proyección pública/owner, privacidad por entidad y pruebas negativas recursivas. `[VERIFIED: apps/api/accounts/tests/test_public_profile.py:20-49,104-125; .planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md:46-60]` |
| V13 API and Web Service | Sí | CSRF para mutaciones de sesión, serializers, permisos, 429, descarga CSV con content type/disposition controlados. `[VERIFIED: apps/api/config/settings.py:38-46,133-149; CITED: https://docs.djangoproject.com/en/5.2/howto/csrf/]` |

### Known Threat Patterns for this stack

| Patrón | STRIDE | Mitigación estándar |
|---|---|---|
| IDOR por `work_id`, `copy_id`, `list_id` o `comment_id` | Elevation/Tampering | Filtrar por `request.user` en la misma consulta y devolver 404/403 sin confirmar recursos ajenos. `[VERIFIED: apps/api/library/views.py:167-191,225-240]` |
| Enumeración de usuarios | Information disclosure | Mensaje uniforme de login/registro cuando proceda, respuestas públicas coherentes y throttle; no confundir throttle con garantía absoluta. `[VERIFIED: apps/api/accounts/views.py:32-35,72-97; CITED: https://www.django-rest-framework.org/api-guide/throttling/]` |
| CSRF en login, registro, logout y mutaciones | Spoofing | `csrf_protect`, middleware y `X-CSRFToken`; test sin header debe fallar. `[VERIFIED: apps/api/accounts/views.py:46-58,115-139; apps/api/accounts/tests/test_auth.py:110-118; CITED: https://docs.djangoproject.com/en/5.2/howto/csrf/]` |
| XSS en alias, bio, comentarios y nombres de listas | Tampering | DTOs como texto, no HTML confiable; escapar/renderizar por contexto y cubrir payloads hostiles en backend/browser. `[VERIFIED: apps/api/accounts/serializers.py:22-25; apps/api/accounts/tests/test_public_profile.py:128-163; ASSUMED para campos nuevos]` |
| CSV formula injection | Tampering/Code execution in spreadsheet | Neutralizar `=`, `+`, `-`, `@` antes de `csv.writer`; probar apertura/parseo y documentar alteración del valor. `[CITED: https://owasp.org/www-community/attacks/CSV_Injection]` |
| Confusión de proxy/IP para rate limit | DoS | Configurar `NUM_PROXIES` al número real de saltos y probar local/deploy; el código ya documenta el riesgo. `[VERIFIED: apps/api/config/settings.py:118-149; CITED: https://www.django-rest-framework.org/api-guide/throttling/]` |
| URL de avatar usada como SSRF | Server-side request forgery | No fetch/proxy server-side; validar esquema/longitud y aplicar política de imágenes en el cliente. `[ASSUMED]` |

## Assumptions Log

| # | Supuesto | Sección | Riesgo si es incorrecto |
|---|---|---|---|
| A1 | Avatar se representa como URL HTTPS sin upload binario en v1. | Portability and Scope | Puede requerir media storage, migración y un plan de seguridad de archivos. |
| A2 | “Cinco favoritos” se modela como cinco slots posibles, con huecos permitidos, no como cinco juegos obligatorios. | Architecture Patterns | Si el autor exige cinco juegos siempre completos, cambia validación/UI/seed. |
| A3 | La privacidad de comentarios de terceros se resuelve con una proyección pública/privada explícita o con la política de colección, sin “solo amigos”. | Architecture Patterns/Security | Puede cambiar el DTO público y la UX del detalle. |
| A4 | Precio como decimal no negativo, moneda de tres letras y estados de conservación documentados son suficientes para v1. | Portability | Una taxonomía académica/legal más estricta requeriría decisión y migración. |
| A5 | Una fila CSV unificada con `record_type` es preferible a varios archivos CSV. | Portability | Si la UI espera archivos separados, el contrato de descarga cambia. |
| A6 | La reconciliación de `PROF-01` y `PORT-01..03` se realizará en un cambio documental autorizado posterior a esta investigación. | Portability | El plan no puede cerrar requisitos con wording contradictorio sin esa decisión. |
| A7 | El código frontend puede cambiar durante la planificación; los contratos de esta investigación se validan contra el backend actual antes de implementar. | Project Constraints | La otra LLM puede haber cambiado labels/rutas y requerir ajuste de E2E. |

## Open Questions — RESOLVED

1. **Avatar:** resuelto como `avatar_url` opcional validada como URL HTTPS, con límites de longitud y sin fetch ni proxy server-side. El backend almacena y valida el valor; no descarga, sigue ni transforma el recurso remoto.

2. **Comentarios:** resuelto con un campo de visibilidad propio `public/private`. El autor siempre puede consultar y gestionar su comentario, incluso cuando es privado; los terceros solo reciben comentarios públicos. La privacidad no se deriva de `collection_visibility` ni de `favorites_visibility`.

3. **Fuentes canónicas:** resuelto mediante la reconciliación documental de esta fase: `PROF-01` significa alias de login inmutable más biografía/avatar editables; `PORT-01` queda limitado a CSV versionado; `PORT-02` y `PORT-03` se asignan explícitamente a la Fase 7 y no generan endpoints ni tests de feature en esta fase.

4. **Contenido del export:** resuelto con un contrato CSV versionado que incluye únicamente las superficies visibles/autorizadas de colección, ratings, listas, comentarios y favoritos; la cabecera, el orden, la codificación y la neutralización de fórmulas quedan fijados por el plan de exportación.

## Sources

### Primary (HIGH confidence)

- `.planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT.md` — decisiones bloqueadas, discreción y diferidos; leído completo.
- `.planning/ROADMAP.md` — objetivo, dependencias, requisitos y criterios vigentes de Fase 5; leído completo en sus secciones relevantes.
- `.planning/REQUIREMENTS.md` — wording y matriz de trazabilidad de `PROF-01`, `LIB-03`, `LIB-04`, `INV-03`, `INV-04`, `PORT-01..04`, `PRIV-01`.
- `.planning/STATE.md`, `CONVENTIONS.md`, `AGENTS.md` e `ideas-vault/README.md` — estado, idioma, seguridad documental y límites del vault.
- `apps/api/accounts/{models.py,serializers.py,views.py,urls.py,migrations/*,tests/*}` — auth, CSRF, registro, sesión, perfiles y allowlists actuales.
- `apps/api/library/{models.py,serializers.py,services.py,views.py,urls.py,migrations/*,tests/*}` — `LibraryEntry`, `OwnedCopy`, transacciones, idempotencia, ownership y tests PostgreSQL.
- `.planning/codebase/{ARCHITECTURE,CONVENTIONS,CONCERNS,INTEGRATIONS,STACK,STRUCTURE,TESTING}.md` — mapas de arquitectura, stack, riesgos e infraestructura; tratados como orientación fechada y contrastados contra el código actual.
- `pyproject.toml`, `package.json`, `apps/api/pytest.ini`, `e2e/demo-journey.spec.ts`, `e2e/a11y.spec.ts` — versiones, runners y patrones de verificación actuales.

### Secondary (MEDIUM confidence)

- [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/) — sesiones cookie-based, auth/authorization y middleware.
- [Django password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) — hashing y validadores de contraseña.
- [Django CSRF how-to](https://docs.djangoproject.com/en/5.2/howto/csrf/) — `csrf_protect`, `ensure_csrf_cookie` y `X-CSRFToken` para fetch.
- [Django REST Framework throttling](https://www.django-rest-framework.org/api-guide/throttling/) — scopes, cache, proxy/IP y límites de la protección.
- [OWASP CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection) — fórmula injection y neutralización con tab para Excel.
- [OWASP ASVS Developer Guide](https://devguide.owasp.org/en/03-requirements/05-asvs/) — categorías ASVS aplicables.

### Tertiary (LOW confidence)

- No se usan fuentes terciarias para decisiones bloqueadas. Las propuestas marcadas `[ASSUMED]` son decisiones de diseño pendientes de confirmación, no hechos verificados.

## Metadata

**Desglose de confianza:**

- Alcance y trazabilidad: HIGH — decisiones y requisitos leídos directamente de los archivos canónicos actuales.
- Arquitectura backend: HIGH — modelos, views, serializers, migraciones y tests leídos directamente; los mapas fechados se contrastaron con el código.
- Seguridad: MEDIUM/HIGH — controles actuales verificados en código y recomendaciones contrastadas con documentación oficial Django/DRF/OWASP.
- Avatar, semántica exacta de privacidad de comentarios, esquema CSV y taxonomía de conservación: LOW/MEDIUM — son áreas de discreción y quedan registradas como supuestos.

**Fecha de investigación:** 2026-09-12  
**Válido hasta:** 2026-10-12 para el stack estable; revisar antes si cambia el contrato de frontend o se aprueba JSON/importación.
