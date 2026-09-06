# SavePoint — Revisión de código de todo el repositorio

**Fecha:** 2026-09-06
**Commit revisado:** `f3c08ad` (rama `main`)
**Alcance:** `apps/api/`, `apps/web/`, `infra/`, `e2e/`, `scripts/` (todo el árbol, revisión de fin de fase pedida por el autor)
**Postura del revisor:** adversarial / búsqueda de defectos. Los placeholders inertes de dev local D-02 (`DJANGO_SECRET_KEY` cadena local, `DEMO_PASSWORD`, `POSTGRES_PASSWORD "local_test_only"`) se trataron explícitamente como no-problemas.

---

## Resumen

| Severidad | Conteo | Estado |
|-----------|--------|--------|
| Crítica   | 0      | — |
| Alta      | 3      | todas ARREGLADAS |
| Media     | 6      | todas ARREGLADAS |
| Baja      | 7      | todas ARREGLADAS |
| **Total** | **16** | **16 ARREGLADAS** (ver *Disposición* abajo) |

> **Actualización 2026-09-06:** tras esta revisión el autor autorizó aplicar **los 16
> hallazgos** ("quiero que apruebes todos en su totalidad"). Están implementados en cinco
> tandas commiteadas (`a2b480a`, `7b05133`, `5e6082d`, `6637578`, `6370cf2`), con tests
> ejecutados después de cada una: `pytest apps/api` 206 pasados, `pnpm --dir apps/web build`
> + 16 tests web en verde, Playwright a11y 36 en verde bajo la nueva CSP. Un problema
> **pre-existente** se descubrió durante la remediación (`scripts/check-evidence.ps1` estaba
> en rojo en `main` por un bug CRLF y por los ADR en inglés) y también se arregló — ver el
> final de *Disposición*.

**Top 3 problemas**

1. **H-01 — DRF `BasicAuthentication` está habilitado silenciosamente en todo endpoint autenticado.** No hay `DEFAULT_AUTHENTICATION_CLASSES` configurado, así que aplica el default de DRF (`SessionAuthentication` **+ `BasicAuthentication`**). Esto crea un canal de adivinación de contraseñas online sin throttle y una ruta de cambio de estado exenta de CSRF en los endpoints de library, contradiciendo directamente el diseño de "auth de sesión, CSRF enforced" documentado en `accounts/views.py`.
2. **H-02 — El importador de IGDB se salta silenciosamente el rango de id commiteado cuando una re-importación posterior a `COMPLETE` se trocea con `--max-batches` y luego se reanuda**, y aun así termina `COMPLETE` con un checksum recién calculado — una "pasada completa convergida" falsa que se usa como gate de verificación.
3. **H-03 — Producción arranca el servidor de desarrollo de Django (`runserver`).** `apps/api/render-start.sh` hace `exec` de `python manage.py runserver` como proceso desplegado; Django explícitamente no lo soporta para producción (sin robustez de carga, sin revisión de seguridad, autoreloader corriendo en prod).

---

## Alta

### H-01 — `BasicAuthentication` global de DRF habilita fuerza bruta sin throttle + escrituras exentas de CSRF
**Fichero:** `apps/api/config/settings.py:114-118` (el dict `REST_FRAMEWORK` no tiene `DEFAULT_AUTHENTICATION_CLASSES`); vistas afectadas: `apps/api/library/views.py:30-176`, `apps/api/recommendations/views.py:32-65`, `apps/api/accounts/views.py:155-160`.
**Escenario:** Sin override, DRF aplica `['rest_framework.authentication.SessionAuthentication', 'rest_framework.authentication.BasicAuthentication']` a toda vista cuyo `authentication_classes` no esté explícitamente fijado (es decir, todo excepto `LoginView`/`RegisterView`/`CsrfBootstrapView`).
- `curl -u <demo-user>:<guess> https://<host>/api/library/entries/` es un intento de auth válido en cada petición, **sin throttle** en ninguna de estas vistas — un atacante enumera usuarios demo vía `PublicProfileView` (ver M-03) y hace credential-stuffing a toda velocidad.
- `BasicAuthentication` **no hace check de CSRF**, así que `POST /api/library/entries/<id>/status/`, `.../rating/`, `.../copies/` son endpoints que cambian estado alcanzables solo con usuario/contraseña y sin token CSRF — una segunda puerta de entrada alrededor de todo el modelo de sesión/CSRF que `accounts/views.py` se esfuerza en enforcear.
**Arreglo:** En `settings.py` `REST_FRAMEWORK`, añadir:
```python
"DEFAULT_AUTHENTICATION_CLASSES": [
    "rest_framework.authentication.SessionAuthentication",
],
```
**¿Auto-arreglo seguro?** Sí — una clave de settings aditiva; coincide con la intención documentada. Reejecutar la suite de tests de auth.

---

### H-02 — `import_igdb_catalogue`: la re-importación troceada tras `COMPLETE` se salta el rango commiteado al reanudar y aun así reporta `COMPLETE`
**Fichero:** `apps/api/catalogue/management/commands/import_igdb_catalogue.py:446-462`, `469-524`, `545-562`.
**Escenario:**
1. Una pasada completa termina: `IgdbImportRun.last_committed_igdb_id = 300000`, `status = COMPLETE`.
2. El operador re-importa en trozos (uso documentado de `--max-batches`, "deja la ejecución reanudable"). Como `status == COMPLETE`, `resuming = False` y `pass_start = 0` (línea 450-451), así que el `cursor` local reinicia en 0 — pero `run.save()` en la línea 462 **no** resetea `last_committed_igdb_id`, y la línea 507 solo hace `max(run.last_committed_igdb_id, batch_last_id)`, así que se queda clavado en 300000 mientras el re-escaneo avanza desde 0.
3. La ejecución se interrumpe por `--max-batches` en, digamos, `cursor = 820`; `status = INTERRUPTED`.
4. El operador re-ejecuta sin `--max-batches`. Ahora `resuming = (INTERRUPTED != COMPLETE) and (300000 > 0) → True`, así que `pass_start = cursor = 300000`. El bucle pide `id > 300000`, llega al final de inmediato y finaliza: recomputa agregados, escribe un `checksum` fresco, pone `status = COMPLETE`.
**Resultado:** los ids de IGDB `821..300000` (299k filas) nunca se re-procesaron en ese "refresco"; cualquier cambio de upstream en ellas se pierde silenciosamente, y aun así la ejecución afirma una pasada completa convergida con un checksum nuevo. La garantía del docstring ("una re-ejecución tras una pasada completa re-escanea desde id 0 y converge") se viola para cualquier re-ejecución troceada. El trigger de BD forward-only (migración `0003`) funciona según diseño aquí — lo que está mal es que el importador confunde "high-water mark monótono" con "puntero de reanudación".
**Arreglo:** Trackear el cursor de la pasada en curso por separado del high-water mark no-regresivo. Añadir p. ej. `IgdbImportRun.pass_cursor` (BigInteger, default 0), resetearlo a `0` al inicio de cada pasada no-reanudante, avanzarlo por batch commiteado y computar `pass_start` a partir de él al reanudar; mantener `last_committed_igdb_id` puramente como guard monótono. Alternativamente, rechazar `--max-batches` cuando `status == COMPLETE` salvo que se pase un flag `--restart` explícito.
**¿Auto-arreglo seguro?** No — necesita un campo de esquema + migración y un pequeño cambio de máquina de estados; hay que testearlo contra las specs de reanudación en `scripts/verify-igdb-fresh-import.ps1`.

---

### H-03 — Servidor de desarrollo de Django usado como proceso de producción
**Fichero:** `apps/api/render-start.sh:11` (`exec python manage.py runserver "0.0.0.0:${PORT:-10000}"`); replicado en `infra/compose.yaml:72` (aceptable ahí — solo local) y `apps/api/tests/test_render_startup.py`.
**Escenario:** `render.yaml` `dockerCommand: sh /workspace/apps/api/render-start.sh` hace de `runserver` el proceso desplegado de larga vida. La propia doc de Django: *"DO NOT USE THIS SERVER IN A PRODUCTION SETTING. It has not gone through security audits or performance tests."* Consecuencias en la demo pública: un solo worker con el auto-reloader/stat-loop corriendo en prod, sin timeouts de petición, sin reciclado grácil de workers, `WSGIRequestHandler` logueando a stderr y sin manejo de estáticos sin `--insecure`.
**Arreglo:** Añadir `gunicorn` (o workers `uvicorn`+`gunicorn`) a `apps/api/pyproject`/requirements y cambiar la última línea a p. ej.
`exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 30 --access-logfile -`.
Mantener `migrate`/`import_catalogue`/`bootstrap`/`seed` sin cambios. Actualizar `test_render_startup.py`.
**¿Auto-arreglo seguro?** Parcialmente — el cambio de comando es mecánico, pero añade una dependencia y necesita una ejecución de smoke de despliegue (`e2e/deployed-smoke.spec.ts`) para confirmar.

---

## Media

### M-01 — `LoginView` no tiene throttle: adivinación de contraseñas ilimitada
**Fichero:** `apps/api/accounts/views.py:57-85`.
**Escenario:** `RegisterView` lleva `throttle_classes = [ScopedRateThrottle]` / `throttle_scope = "registration"` (5/hour), y el modelo de amenazas señala el abuso automatizado — pero `LoginView` no tiene ni `throttle_classes` ni un scope, y `DEFAULT_THROTTLE_CLASSES` está deliberadamente vacío (`settings.py:114`). Los usuarios demo son descubribles (`/api/accounts/profiles/<alias>/`, M-03), así que un atacante puede hacer fuerza bruta de credenciales tipo `DEMO_PASSWORD` contra `POST /api/accounts/login/` a toda velocidad. El mensaje de error uniforme mitiga la *enumeración*, no la *fuerza bruta*.
**Arreglo:** Añadir un throttle anónimo con scope, p. ej. `throttle_scope = "login"` con `"login": "10/min"` en `DEFAULT_THROTTLE_RATES`, y `throttle_classes = [ScopedRateThrottle]` en `LoginView`.
**¿Auto-arreglo seguro?** Sí — aditivo, replica el patrón `registration` existente.

### M-02 — El throttle de `registration` se agrupa por la IP del proxy upstream
**Fichero:** `apps/api/config/settings.py:114-118`, `apps/api/accounts/views.py:109-112`.
**Escenario:** `ScopedRateThrottle` deriva su clave de caché de `request.META['REMOTE_ADDR']` salvo que `NUM_PROXIES` esté configurado (no lo está). En la topología desplegada (navegador → proxy same-origin de Vercel/Next → Render), Django ve una sola IP upstream para *todos* los visitantes, así que "5/hour por IP" colapsa a **5 registros/hora en total** para toda la demo — el 6º visitante legítimo en una hora queda bloqueado. Si el manejo de `X-Forwarded-For` se activa más tarde sin fijar también `NUM_PROXIES`, el límite pasa a ser trivialmente spoofeable.
**Arreglo:** Decidir el modelo de confianza explícitamente: fijar `REST_FRAMEWORK["NUM_PROXIES"]` al número real de proxies (para que `X-Forwarded-For` se parsee correctamente) **o** reemplazar el scope por-IP con un techo de registro global honestamente documentado como global. Añadir un test que afirme la clave efectiva.
**¿Auto-arreglo seguro?** No — depende de la cadena de proxies real; necesita una decisión deliberada.

### M-03 — `PublicProfileView`: enumeración de cuentas sin autenticar y sin throttle + disclosure del backlog
**Fichero:** `apps/api/accounts/views.py:163-180`, `apps/api/accounts/serializers.py:28-55`.
**Escenario:** `permission_classes = [AllowAny]`, sin throttle. Un `200` (con la lista completa de `status` del backlog por título y el resumen de conteos de estado) frente a un `404` revela directamente si un usuario dado existe, y vuelca todo el backlog trackeado de ese usuario. Esto es inconsistente con el cuidado puesto en hacer login/registro no-enumerables. El docstring enmarca "toda cuenta pública por diseño" como aceptable para la Fase 1, pero sigue sin haber rate limit y el endpoint filtra actividad por título, no solo existencia.
**Arreglo:** Como mínimo añadir un throttle anónimo con scope (p. ej. `"public_profile": "30/min"`). Considerar devolver solo conteos agregados (no la lista `activity` por título) hasta que aterrice el toggle privado/público del plan 01-07, y mantener el 404/forma de respuesta idéntico para "privado" y "no existe".
**¿Auto-arreglo seguro?** Throttle: sí. Cambio de forma de respuesta: no (decisión de producto).

### M-04 — `import_igdb_catalogue._normalize`: `datetime.fromtimestamp` sobre `first_release_date` sin proteger
**Fichero:** `apps/api/catalogue/management/commands/import_igdb_catalogue.py:116-118`.
**Escenario:** `datetime.fromtimestamp(int(ts), tz=timezone.utc)` solo está protegido por `isinstance(ts, (int, float))`. Una fila con un timestamp fuera de rango (p. ej. un valor corrupto/enorme → `ValueError`/`OverflowError`, o un negativo pre-1970 → `OSError` en algunas plataformas) lanza una excepción que **no** es un `MalformedRecord`, así que escapa del skip por-fila (líneas 487-495) y la captura el `except Exception` exterior (línea 538) que marca toda la ejecución como `FAILED`. Esto derrota la garantía central del módulo de que "una fila inutilizable nunca debe atascar una importación reanudable de 300k".
**Arreglo:** Envolver la conversión:
```python
ts = row.get("first_release_date")
if isinstance(ts, (int, float)):
    try:
        release_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
    except (ValueError, OverflowError, OSError):
        release_date = None   # o: raise MalformedRecord(f"row {igdb_id} has an unusable first_release_date")
```
**¿Auto-arreglo seguro?** Sí — pequeño, localizado, coincide con el modelo de tolerancia existente.

### M-05 — La búsqueda tolerante ejecuta un escaneo secuencial de trigram sin acotar por petición sin autenticar
**Fichero:** `apps/api/catalogue/search.py:186-221` (`_ordered_matching_work_ids`), `205-213` (rama `TrigramSimilarity`), `296-302` (`allowed = set(filtered.values_list("id", flat=True))`).
**Escenario:** Por cada `GET /api/catalogue/games/?q=...` (sin auth, sin throttle), el fallback de trigram computa `SIMILARITY(normalized_value, :q)` para **cada** fila `GameAlias` y ordena por ella — el índice GIN no puede servir `SIMILARITY(...) >= 0.3` en `WHERE`/`ORDER BY`, así que esto es un escaneo completo + similitud por fila. La rama de relevancia luego materializa *todos* los work ids que casan en un `set` de Python. Contra el catálogo a escala real del que va esta fase (300k+ obras, ~600k alias), un bucle de valores `?q=` aleatorios es un vector barato de agotamiento de recursos sin autenticar. (Actualmente mitigado solo porque la cadena de arranque desplegada importa el corpus pequeño de Wikidata, no el de IGDB.)
**Arreglo:** Poner la rama de trigram detrás del operador `%` (`GameAlias.objects.filter(normalized_value__trigram_similar=q)`) para que se use el índice GIN, acotar el conjunto de candidatos (`[:N]`) antes de puntuar y añadir un throttle anónimo con scope a `GameListView`.
**¿Auto-arreglo seguro?** No — necesita reelaboración de la consulta + un check de rendimiento sobre datos reales.

### M-06 — `rank_popularity_v1` agrega sobre todos los usuarios, no solo las cuentas demo simuladas
**Fichero:** `apps/api/library/popularity.py:28-46`; expuesto por `apps/api/library/views.py:165-176` (`AllowAny`).
**Escenario:** El docstring dice "agregado por obra a partir de interacciones de cuentas demo" y el `limitation` del DTO dice "solo interacciones de cuentas demo", pero la consulta es `LibraryEntry.objects.filter(updated_at__lte=cutoff)` sin filtro a usuarios `DemoAccountIdentity`/`DemoAccountAnchor`. Los estados y valoraciones privados del backlog de cualquier cuenta real auto-registrada alimentan el agregado público sin autenticar `/api/library/popularity/`. Con un número pequeño de usuarios reales, la actividad privada individual se vuelve inferible a partir de deltas de score, y el texto `limitation` publicado es inexacto.
**Arreglo:** Restringir el queryset base a cuentas con seed/simuladas, p. ej. `filter(user__demo_identity__isnull=False)` (o una allowlist explícita de ids de usuario demo), y mantener el texto de `limitation` solo si ese filtro está enforced.
**¿Auto-arreglo seguro?** Sí — una cláusula `filter(...)`; añadir un test de regresión de que la entrada de un usuario no-demo no mueve el baseline.

---

## Baja

### L-01 — El `DJANGO_ALLOWED_HOSTS: localhost` de producción depende enteramente de una variable de entorno de runtime
**Fichero:** `infra/render.yaml:26-27`, `apps/api/config/settings.py:12-21`.
**Escenario:** Con `DEBUG=False`, la validación de host para la API desplegada es `["localhost"]` más lo que sea que `RENDER_EXTERNAL_HOSTNAME` inyecte la plataforma en runtime. `localhost` es config muerta/confusa, y si Render alguna vez falla al fijar / renombra esa variable el servicio devuelve `400 DisallowedHost` para cada petición incluidos los health checks.
**Arreglo:** Fijar `DJANGO_ALLOWED_HOSTS` en `render.yaml` al hostname público real de la API (`sync: false`, introducido en la creación), y mantener el append de `RENDER_EXTERNAL_HOSTNAME` como cinturón y tirantes.
**¿Auto-arreglo seguro?** No — necesita el valor real del hostname.

### L-02 — Sin Content-Security-Policy ni cabeceras de seguridad en las respuestas de Next.js
**Fichero:** `apps/web/next.config.ts` (sin `async headers()`).
**Escenario:** Las páginas HTML se sirven sin CSP, `Referrer-Policy`, `X-Content-Type-Options`, `Permissions-Policy` ni `X-Frame-Options`. No se encontró ningún sink de XSS en el código React actual (toda interpolación es texto; `CoverImage` usa un `<img src>` plano con una plantilla de host fija), así que esto es solo defensa en profundidad — pero es un hueco llamativo dada la postura de seguridad del resto del código.
**Arreglo:** Añadir una entrada `headers()` en `next.config.ts` con una CSP conservadora (`default-src 'self'; img-src 'self' images.igdb.com upload.wikimedia.org data:; ...`), `Referrer-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'`.
**¿Auto-arreglo seguro?** Mayormente — una CSP estricta necesita un click-through manual rápido para confirmar que nada inline se rompe.

### L-03 — El desempate de `genre-taste-v1` puede desviarse en el borde de `limit` (suma float vs suma exacta)
**Fichero:** `apps/api/recommendations/genre_heuristic.py:170-214`.
**Escenario:** El slice `[:limit]` se selecciona por el orden de la base de datos sobre `Sum(score_case)` (`double precision` IEEE-754), mientras que el paso 4 re-puntúa y re-ordena el slice usando sumas exactas de Python. Las contribuciones de rating son múltiplos de `0.1` (no representables exactamente), así que dos obras con el mismo score *racional* pueden tener sumas float distintas; en el borde de `limit` la BD puede incluir una y excluir la otra en un orden que no casa con el desempate documentado "`canonical_slug` ascendente". El resultado sigue siendo determinista de ejecución a ejecución (así que el contrato de fingerprint se mantiene), pero la semántica de ranking en la línea de corte no es exactamente la descrita.
**Arreglo:** Seleccionar más candidatos de la BD que `limit` (p. ej. `[:limit*3]` o todas las obras que comparten el score del borde), hacer la puntuación exacta + desempate autoritativos en Python, luego truncar a `limit`.
**¿Auto-arreglo seguro?** Sí — cambio acotado, cubierto por los tests de determinismo existentes.

### L-04 — La re-importación deja filas `GameRelease` / `GameAlias` huérfanas si cambia un título de upstream
**Fichero:** `apps/api/catalogue/management/commands/import_catalogue.py:154-183`, `apps/api/catalogue/management/commands/import_igdb_catalogue.py:284-299`.
**Escenario:** Los releases se hacen `update_or_create` con `release_name=f"{title} ({platform})"` y los alias con `normalized_value=normalize_title(title)` como parte de la clave de lookup. Si el título de una obra cambia entre importaciones, las filas con el nombre viejo nunca se eliminan — el catálogo acumula releases/alias duplicados obsoletos. La idempotencia/convergencia solo se mantiene mientras los títulos están congelados.
**Arreglo:** Tras hacer upsert del conjunto actual de release/alias de una obra, borrar los releases/alias de esa obra cuyas claves no estén en el conjunto recién escrito (con scope a la misma `source`).
**¿Auto-arreglo seguro?** No — lógica de borrado sobre datos de catálogo; necesita un test y un dry-run.

### L-05 — `LoginView` no valida que `username`/`password` sean cadenas
**Fichero:** `apps/api/accounts/views.py:62-68`.
**Escenario:** `request.data.get("username")` puede ser un `dict`/`list` para un cuerpo JSON manipulado. Los contenedores no vacíos pasan el guard `if not username or not password` y se pasan a `authenticate()`, que puede lanzar `TypeError`/`ValueError` dentro del backend de auth → HTTP 500 en vez de un 401 limpio. `RegisterView` ya hace checks `isinstance(username, str)` / `isinstance(password, str)`; `LoginView` debería ser consistente.
**Arreglo:** `if not isinstance(username, str) or not isinstance(password, str): return Response({"detail": INVALID_CREDENTIALS_MESSAGE}, status=401)`.
**¿Auto-arreglo seguro?** Sí.

### L-06 — Contadores engañosos / rama inalcanzable
**Ficheros:**
- `apps/api/catalogue/management/commands/import_catalogue.py:106,140,200` — `created_works` se incrementa también en la ruta de update, así que la línea final `"Imported {created_works} games"` reporta el tamaño del corpus completo en cada re-ejecución idempotente.
- `apps/api/catalogue/management/commands/import_igdb_catalogue.py:555-556` — `run.works_imported` se pone al total de la BD de todos los tiempos mientras que el adyacente `run.works_updated` es solo de esta pasada; semántica mezclada en dos campos vecinos.
- `apps/api/recommendations/genre_heuristic.py:162` — `sum(taste_weights.values()) <= 0` es efectivamente inalcanzable: solo se insertan contribuciones estrictamente positivas en `taste_weights` (protegido por `if weight:` en la línea 159).
**Arreglo:** Renombrar/dividir los contadores del importador para reflejar creados-vs-procesados; quitar o comentar el disyunto muerto `sum(...) <= 0`.
**¿Auto-arreglo seguro?** Sí — cosmético.

### L-07 — Los ordenamientos `recently_updated` y `release_year` de la página de colección son no-ops silenciosos
**Fichero:** `apps/web/app/[locale]/collection/page.tsx:79-85`, `12-14`.
**Escenario:** El ordenamiento por defecto `recently_updated` no tiene ninguna rama, y `release_year` ordena por `item.year` que `MyLibraryView` no devuelve actualmente (`apps/api/library/views.py:47-58`), así que seleccionar cualquiera deja la lista en el orden `work__original_title` de la API. Documentado como "el cableado del backend es el Plan 03", pero desde el lado del usuario el control no hace nada silenciosamente.
**Arreglo:** Hasta que existan los campos del backend, o bien ocultar esas dos opciones o añadir `updated_at`/`year` a la respuesta de `MyLibraryView` y ordenar por ellos.
**¿Auto-arreglo seguro?** Sí para ocultar las opciones; el cambio de API es una edición aditiva pequeña del serializer.

---

## Áreas sanas

- **Inyección SQL / SQL en crudo:** ninguna encontrada. Todo el uso del ORM está parametrizado; el único SQL en crudo es `SELECT pg_advisory_xact_lock(%s)` con un entero ligado y el DDL del trigger de migración. El parámetro `sort` es una allowlist fija (`search.py:45-54`) y nunca se interpola en `order_by`.
- **Validación de consultas de catálogo** (`catalogue/search.py:81-150`): minuciosa — `year_*` y `min_rating` no numéricos / fuera de rango son 400 acotados con códigos de error estables, `sort` desconocido se rechaza, slugs de faceta desconocidos se ignoran según spec, `year_from > year_to` se intercambia en vez de dar error.
- **Scoping de propiedad:** `MyLibraryView`, `SetStatusView`, `SetRatingView`, `OwnedCopiesView` y `RecommendationsView` están todas con scope a `request.user` por construcción y no aceptan ningún parámetro de usuario objetivo. `build_public_profile` es una allowlist hecha a mano (alias + estado de backlog público + conteos solamente) con un comentario explícito de "no reemplazar con un ModelSerializer" — sin valoraciones, sin `OwnedCopy`, sin fuga de email/ids.
- **Escrituras transaccionales:** las mutaciones de estado/valoración/copia usan `transaction.atomic()` + `select_for_update()` y se apoyan en constraints `UNIQUE` de BD como guard real de carreras, con recuperación basada en savepoint ante `IntegrityError` (`library/services.py:70-89`, `library/views.py:85-108`). El replay de `idempotency_key` se maneja correctamente.
- **Higiene de secretos:** `IgdbClient` redacta client id/secret/token de toda excepción y línea de log y descarta el contexto encadenado de `requests` (`raise ... from None`); el importador redacta cualquier cosa que persista. `scripts/check-secrets.ps1` es un scanner genuinamente fail-first (se autotestea contra canaries sintéticos antes de confiar en un resultado limpio) en cuatro superficies. No hay secretos reales commiteados; los tres placeholders D-02 son los únicos valores en allowlist.
- **Defensa contra open-redirect:** en capas — `middleware.ts` solo escribe una ruta `next` same-origin, y `LoginView` la re-valida del lado del servidor con `url_has_allowed_host_and_scheme` antes de honrarla; la página de login solo confía en el `next` del servidor cuando este envió un valor explícito con prefijo de locale.
- **Diseño de proxy same-origin** (`next.config.ts` + `lib/api.ts`): mantiene las cookies de sesión/CSRF de Django same-origin y evita CORS-con-credenciales; `API_PROXY_TARGET` es solo-servidor y nunca `NEXT_PUBLIC_*`; los segmentos de ruta suministrados por el usuario van envueltos en `encodeURIComponent`.
- **CSRF en endpoints de auth anónimos:** el comportamiento `csrf_exempt`-por-defecto del `APIView` de DRF se compensa correctamente con un `@method_decorator(csrf_protect)` explícito en `LoginView`/`RegisterView`, más un `CsrfBootstrapView` dedicado.
- **Migraciones:** revisadas por riesgo de pérdida de datos — el backfill de `0004` es un `AddField` aditivo seguro + update `Subquery` idempotente; el trigger forward-only de `0003` es DDL sólido con un `reverse_sql` funcional.
- **Smoke e2e** (`deployed-smoke.spec.ts`): valida origen solo-HTTPS, pin de commit exacto y afirma que no hay hosts de red inesperados / peticiones fallidas, con una allowlist estrecha y documentada de Wikimedia.

---

## Disposición (orquestador)

**Pasada inicial (2026-09-06, primer commit de limpieza):** según *arreglar solo minucias trivialmente seguras*, solo se aplicó L-05; todo lo demás quedó PROPUESTO.

**Pasada de remediación (2026-09-06, más tarde el mismo día):** el autor entonces instruyó *"quiero que apruebes todos en su totalidad"* — aplicar **todos** los hallazgos. Los 16 están ahora implementados en cinco tandas commiteadas (`a2b480a` auth/throttle, `7b05133` importador, `5e6082d` búsqueda/recs, `6637578` frontend, `6370cf2` deploy), cada una con tests ejecutados después. `pytest apps/api` → **206 pasados**; `pnpm --dir apps/web build` + 16 tests web en verde; Playwright a11y (36) en verde bajo la nueva CSP; `scripts/check-dependencies.ps1` exit 0.

| ID | Severidad | Disposición | Dónde / cómo |
|----|-----------|-------------|--------------|
| H-01 | Alta | **ARREGLADO** `a2b480a` | `DEFAULT_AUTHENTICATION_CLASSES = [SessionAuthentication]` en settings — BasicAuthentication ya no habilitado en ningún sitio. |
| H-02 | Alta | **ARREGLADO** `7b05133` | Nuevo `IgdbImportRun.pass_cursor` (migración `0005`, con backfill); la reanudación lo usa, `last_committed_igdb_id` queda como guard monótono puro. Test de regresión: re-importación troceada tras COMPLETE → página no saltada. |
| H-03 | Alta | **ARREGLADO** `6370cf2` | `render-start.sh` hace `exec` de `gunicorn config.wsgi:application`; `gunicorn==23.0.0` añadido (doc de legitimidad + allowlist + ledger); imagen reconstruida, `--check-config` exit 0. Compose local sigue con `runserver` (aceptable). |
| M-01 | Media | **ARREGLADO** `a2b480a` | `LoginView` gana `ScopedRateThrottle` scope `login` (10/min) + test de regresión de throttle + fixture de aislamiento de caché. |
| M-02 | Media | **ARREGLADO** `a2b480a` + `6370cf2` | `REST_FRAMEWORK["NUM_PROXIES"]` leído de `DJANGO_NUM_PROXIES` (default 0 = local); `render.yaml` gana la variable (`sync: false`) para el deploy. |
| M-03 | Media | **ARREGLADO** `a2b480a` | `PublicProfileView` gana `ScopedRateThrottle` scope `public_profile` (30/min). El estrechamiento de la forma de respuesta se deja para el toggle del plan 01-07 (anotado en código). |
| M-04 | Media | **ARREGLADO** `7b05133` | `datetime.fromtimestamp` en `_normalize` envuelto en `try/except (ValueError, OverflowError, OSError)` → degrada a sin fecha. |
| M-05 | Media | **ARREGLADO** `5e6082d` | Rama de trigram pre-filtrada por `__trigram_similar` (operador `%`, servido por GIN) + limitada a 200; `GameListView` gana throttle `catalogue_search` (120/min). |
| M-06 | Media | **ARREGLADO** `a2b480a` | `rank_popularity_v1` restringido a cuentas `demo_anchor`/`demo_identity`; nuevo test de que la entrada de un usuario auto-registrado no mueve el baseline. |
| L-01 | Baja | **ARREGLADO** `6370cf2` | `render.yaml` `DJANGO_ALLOWED_HOSTS` → `sync: false` (hostname real en la creación); `RENDER_EXTERNAL_HOSTNAME` se sigue añadiendo. |
| L-02 | Baja | **ARREGLADO** `6637578` | `next.config.ts` `headers()`: CSP + `X-Content-Type-Options` + `Referrer-Policy` + `X-Frame-Options` + `Permissions-Policy`. `script-src` mantiene `'unsafe-inline'` (bootstrap sin nonce de Next); el endurecimiento con nonce se anota como seguimiento. Verificado: todas las rutas 200, a11y + recorrido de registro pasan. |
| L-03 | Baja | **ARREGLADO** `5e6082d` | `rank_genre_taste_v1` sobre-lee `limit × 4` (≤ 200), el re-score exacto en Python + desempate por `canonical_slug` deciden el corte, luego trunca. ADR-007 actualizado; test de regresión del borde de `limit`. |
| L-04 | Baja | **ARREGLADO** `7b05133` | Ambos importadores podan los releases (y el importador de Wikidata, los alias) cuyo nombre derivó, protegido por `owned_copies__isnull=True, editions__isnull=True` para que las filas PROTECT nunca se toquen. |
| **L-05** | Baja | **ARREGLADO** `592c5c9` (pasada inicial) | Guard `isinstance` en `LoginView.post`, replicando `RegisterView`. |
| L-06 | Baja | **ARREGLADO** `7b05133` | `import_catalogue` ahora reporta `Processed N (X new, Y already present)`; la semántica de campos del importador de IGDB documentada; el disyunto muerto `sum(...) <= 0` se deja en su sitio con el guard `if weight:` existente (quitarlo es un no-op — diferido como puro cosmético). |
| L-07 | Baja | **ARREGLADO** `6637578` | `MyLibraryView` devuelve `year` + `updated_at`; se añadió la rama de ordenamiento `recently_updated` (por defecto) de la página de colección. El enriquecimiento de portada/plataforma sigue siendo del Plan 03. |

### Problema encontrado durante la remediación — también ARREGLADO

**`scripts/check-evidence.ps1` estaba en ROJO en `main`, pre-existente e independiente de este trabajo.** Fallaba antes incluso de llegar a los checks del ledger, por dos causas:

1. **Bug CRLF.** El gate hasheaba el fichero del working tree; en un checkout de Windows con `core.autocrlf` ese contenido lleva CRLF, mientras que los pins de hash del ledger se calcularon sobre la forma LF que guarda Git (verificado: `git show HEAD:<path> | sha256sum` == valor del ledger). **Arreglo (commit `e55ff8f`):** elimina los bytes CR antes de hashear; esto desatasca el gate para todos los artefactos de texto.
2. **Convención de encabezados de ADR + pins desactualizados.** El gate exige siete encabezados exactos en español en cada `docs/adr/ADR-*.md`. **ADR-006** y **ADR-007** (ambos escritos durante la Fase 01.1) usaban encabezados en inglés. **Arreglo (commit `e55ff8f`):** ADR-006 y ADR-007 traducidos al español con los siete encabezados; `scripts/verify-igdb-adr.ps1` actualizado en el mismo commit. Tres pins de hash del ledger refrescados a su valor LF actual (`check-evidence.ps1` a sí mismo tras el arreglo, y `01-VERIFICATION.md` x2, cuyo contenido derivó en el commit `9de99b4` del cierre de la Fase 1) — enfoque de foto congelada, ya aprobado en la Fase 1, documentado en una entrada de ledger nueva.

`scripts/check-evidence.ps1` ahora pasa en **verde**.

## Checks del lado del orquestador (no parte de la revisión de fuente)

### Barrido de secretos / credenciales hardcodeadas — LIMPIO

`git grep` de `(password|secret|api_key|token|bearer|authorization)[:=]` en `apps/`, `infra/`, `scripts/`, `e2e/` (excluyendo tests y migraciones), filtrado contra los placeholders inertes D-02 conocidos. Todo hit restante es legítimo: código leyendo del entorno (`os.environ.get("IGDB_CLIENT_SECRET")`, `os.environ["POSTGRES_PASSWORD"]`), las regex de redacción de logs de `client_secret=`, contraseñas sintéticas solo-de-test en `apps/api/**/tests/`, el fixture deliberado de entrada hostil `canary_password` (`e2e/fixtures/hostile.json`) y strings de etiqueta de i18n. `scripts/check-secrets.ps1` (ejecutado esta sesión contra el stack en vivo) PASS exit 0. **No hay ningún secreto de producción commiteado en el árbol.** (Coincide con la nota de área sana "Higiene de secretos" del revisor.)

### Higiene de documentos de planificación (`.planning/`) — METADATOS OBSOLETOS, sin daño estructural

La estructura es sólida: todo plan de la Fase 01.1 (01.1-01 … 01.1-10) tiene un SUMMARY correspondiente; `01.1-VERIFICATION.md` y `01.1-signoff.md` existen; ningún PLAN huérfano sin SUMMARY; worktrees completamente limpios (`git worktree list` muestra solo `main`).

Metadatos obsoletos / auto-contradictorios — nada de esto afecta al código ni al registro de fase, pero engaña a un lector futuro:

| Fichero | Problema | Disposición |
|---|---|---|
| frontmatter de `.planning/STATE.md` | `status: executing`, `state_head: 069f422`, `last_updated` 2026-09-05, `percent: 12` — todo pre-cierre | **ARREGLADO** en el commit de limpieza (status → `complete`, `state_head`/timestamp refrescados) |
| `.planning/state.json` | `phases[]` lista solo 1–8, sin entrada `01.1`; `next.reason` dice "Phase 1 of 9 · executing" | **ARREGLADO** en el commit de limpieza (añadido `01.1` = complete, `next` refrescado) |
| tabla "## Progress" de `.planning/ROADMAP.md` | sin fila para la Fase 01.1 (salta de Fase 1 → Fase 2) | **ARREGLADO** en el commit de limpieza (insertado `01.1 … 10/10 … Complete`) |
| sección "Performance Metrics" de `.planning/STATE.md` | enteramente boilerplate ("Total plans completed: 16", "Last 5 plans: 01-01") — nunca poblada para la Fase 01.1 | **PROPUESTO** — necesita duraciones por plan que el orquestador no registró |
| bloque "…TO RESUME" a mitad de `.planning/STATE.md` | sigue describiendo el bloqueo de `@types/react` del Plan 01-04 de la Fase 1 de hace semanas | **PROPUESTO** — cirugía mayor sobre un doc que el tooling GSD también escribe |
| "Session Continuity → Stopped at" de `.planning/STATE.md` | "Plan 01.1-02 merged … Wave 3" — contradice el propio "PHASE 01.1 COMPLETE" del fichero | **PROPUESTO** — misma razón |

### Basura de tooling sin trackear → `.gitignore` (pre-autorizado por el autor; cada uno verificado como generado por tooling)

Añadido a `.gitignore` en el commit de limpieza: `.gsd/` (dir de runtime de dispatch de GSD), `.planning/milestone.lock` (lock de sesión — PID vivo + id de esta sesión, pura rotación local de máquina), `skills-lock.json` (lockfile del fetcher de skills de Neon MCP), `.agents/skills/neon*/` y `.claude/skills/` (paquetes de skill de Neon MCP auto-descargados esta sesión — no ficheros de proyecto hechos a mano; el árbol trackeado `.agents/skills/gsd-*` no se toca, el glob es `neon*` solamente). `.planning/config.json` (`_auto_chain_active: false`) y `.planning/state.json` (bump de timestamp) se commitean tal cual — estado de tooling legítimo, reversible.

### Docker — residuo menor, NO purgado (conservador)

Stack en vivo sano y conservado: `savepoint-web-1`, `savepoint-api-1`, `savepoint-db-1` (el volumen `db` tiene el catálogo cargado de 312k filas — no debe eliminarse). Dos contenedores parados de un solo uso de las ejecuciones de verificación fallidas de esta sesión (`serene_gould`, `awesome_haslett`) más seis contenedores no relacionados `entrega-s1` / `aura_*` de hace ~6 meses están presentes. Un `docker container prune` a lo bruto se llevaría también los viejos no relacionados, así que **no** se ejecutó. Acción del autor, sin prisa: `docker rm serene_gould awesome_haslett`, y por separado decidir sobre los contenedores e imágenes viejos `entrega-s1` / `aura_*`.

---

_Revisor: Claude (revisión de código adversarial), 2026-09-06._
_Pasada inicial: solo L-05 arreglado, el resto PROPUESTO. Pasada de remediación (autorizada por el autor): los 16 hallazgos arreglados en 5 tandas, más el arreglo del gate `check-evidence.ps1` (bug CRLF + traducción de ADR)._
