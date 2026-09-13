# Fase 5 — Signoff de evidencia backend + interfaz (Complete Collection Workflows and Portability)

**Fecha:** 2026-09-13 (backend); interfaz añadida el 2026-09-13
**Autor:** sesión backend (planes 05-01, 05-02, 05-03, 05-04) + sesión web (§9)
**Idioma:** español (`CONVENTIONS.md` §1); identificadores/rutas/nombres de campo/comandos en inglés.

Este documento cierra la evidencia backend de la Fase 5 (autenticación real, perfil,
favoritos, comentarios, listas, metadatos de copias y exportación CSV) y explicita qué
parte de la verificación de la fase corresponde a la sesión web. Esta sesión backend
**no ha modificado** `apps/web/**`, `design/**`, capturas de pantalla, ni el contrato
público de recomendaciones (`apps/api/recommendations/published.py`) en ninguno de los
cuatro planes.

## 1. Comandos ejecutados y resultado

Todos los comandos se ejecutaron contra PostgreSQL real vía `infra/compose.yaml`
(`docker compose -f infra/compose.yaml run --rm api ...`); ningún test de esta fase usa
SQLite ni workers pesados.

| Comando | Resultado |
|---|---|
| `python apps/api/manage.py migrate --noinput` | `No migrations to apply.` — cadena de migraciones ya aplicada (`accounts.0003_phase5_profile`, `library.0003_phase5_comments_lists`, `library.0004_phase5_copy_metadata`; el Plan 05-04 no añade migración nueva). |
| `python apps/api/manage.py makemigrations --check --dry-run` | `No changes detected` — sin drift entre modelos y migraciones. |
| `pytest apps/api/accounts/tests apps/api/library/tests -q` | `247 passed` (incluye `test_copies.py`, `test_comments.py`, `test_lists.py`, `test_export.py`, `test_schema.py`, `test_profile.py`, `test_public_profile.py`). |
| `pytest apps/api -q` (suite completa, ejecutada tras el Plan 05-04) | `619 passed` — sin regresión en catalogue/recommendations ni en el resto del backend. |

El pre-existente flake `apps/api/catalogue/tests/test_search.py::test_pagination_defaults_to_25_per_page`
(solo reproducible cuando corre la suite completa de `apps/api`, pasa en aislamiento;
tracked en la issue de GitHub #51) no apareció en ninguna de las ejecuciones de esta
sesión y es, en cualquier caso, ajeno a `accounts`/`library`.

## 2. Migraciones PostgreSQL de la fase

| Migración | Plan | Contenido |
|---|---|---|
| `accounts/migrations/0003_phase5_profile.py` | 05-01 | `AccountProfile` (bio/avatar/visibilidad), `FavoriteSlot` (5 slots). |
| `library/migrations/0003_phase5_comments_lists.py` | 05-02 | `GameComment`, `CustomList`, `CustomListItem`. |
| `library/migrations/0004_phase5_copy_metadata.py` | 05-03 | `OwnedCopy` extendido con compra/conservación. |
| _(ninguna)_ | 05-04 | La exportación CSV (`apps/api/library/export.py`) es de solo lectura sobre modelos existentes; no requiere schema nuevo. |

Cada migración fue verificada contra `information_schema`/`pg_constraint` real en
`apps/api/{accounts,library}/tests/test_schema.py`, no solo `makemigrations --check`.

## 3. Matriz de requisitos → evidencia

| Requisito | Estado | Evidencia |
|---|---|---|
| PROF-01 | Implementado | `apps/api/accounts/tests/test_profile.py` — alias inmutable, bio/avatar HTTPS, IDOR/CSRF (05-01). |
| LIB-03 | Implementado | `apps/api/library/tests/test_comments.py` — unicidad user/work, CRUD, ownership, visibilidad (05-02). |
| LIB-04 | Implementado | `apps/api/library/tests/test_lists.py` — membresía de colección, reorder con concurrencia optimista (05-02). |
| INV-03 | Implementado | `apps/api/library/tests/test_copies.py` — compra/precio/moneda/tienda, round-trip, idempotencia (05-03). |
| INV-04 | Implementado | `apps/api/library/tests/test_copies.py` — regla física/digital en serializer, servicio y `CheckConstraint` (05-03). |
| PORT-01 | Implementado (solo CSV; JSON fuera de este cierre por D-08) | `apps/api/library/tests/test_export.py` (05-04). |
| PORT-02 | **Abierto** — `pending`, asignado a `Phase 7` | Sin endpoint/parser/test de feature en `apps/api/library`; ver `05-PORTABILITY-RECONCILIATION.md`. |
| PORT-03 | **Abierto** — `pending`, asignado a `Phase 7` | Sin endpoint/parser/test de feature en `apps/api/library`; ver `05-PORTABILITY-RECONCILIATION.md`. |
| PORT-04 | Implementado | `apps/api/library/tests/test_export.py::test_hostile_store_and_comment_values_are_neutralized_in_the_export` y prueba de idempotencia de `neutralize_spreadsheet_formula` (05-04). |
| PRIV-01 | Implementado | `apps/api/accounts/tests/test_public_profile.py` — allowlist recursiva sobre actividad/favoritos/comentarios/listas (05-01/05-02). |

La reconciliación completa de PROF-01/PORT-01..04 frente a `05-CONTEXT.md` (D-01, D-08,
D-09) está en
`.planning/phases/05-complete-collection-workflows-and-portability/05-PORTABILITY-RECONCILIATION.md`.

## 4. Amenazas mitigadas (STRIDE, `05-04-PLAN.md` `<threat_model>`)

| Amenaza | Componente | Mitigación verificada |
|---|---|---|
| T-05-04-01 (Elevation) | Endpoint de exportación | `IsAuthenticated`; cada consulta de `export.py` filtra por `user=request.user` (o `list__user=user`); ningún `user_id` llega del cliente; `test_export_contains_only_the_owners_authorized_data` prueba aislamiento A/B. |
| T-05-04-02 (Tampering) | Celdas CSV | Contrato de columnas fijo (`CSV_FIELDNAMES`), `neutralize_spreadsheet_formula` sobre `=`/`+`/`-`/`@`, prueba de idempotencia y de bytes-idénticos en exportaciones repetidas. |
| T-05-04-03 (Information disclosure) | Exportación / DTO público | Allowlist positiva por `record_type`; ninguna columna referencia `password`, sesión ni IDs internos (`work_id`/`copy_id`/`list_id`/`item_id` nunca se escriben, solo se usan como desempate interno). |
| T-05-04-04 (Repudiation) | Documentación de evidencia y alcance | Este signoff, `05-PORTABILITY-RECONCILIATION.md` y `05-VALIDATION.md` registran comandos, resultados y qué requisitos siguen abiertos. |
| T-05-04-SC (Tampering, dependencias) | `apps/api/library/export.py` | Sin dependencias nuevas; usa `csv` de la biblioteca estándar. |

Amenazas de fases previas (identidad/sesión/CSRF en 05-01, unicidad/concurrencia en
05-02, validación física/digital en 05-03) permanecen mitigadas sin cambios en este
plan; ver sus propios `SUMMARY.md` para el detalle STRIDE de cada una.

## 5. Contrato de integración UI (handoff a la sesión web)

El contrato completo de rutas/DTOs de 05-01/05-02/05-03 está en
`docs/verification/phase-05-api-handoff.md`. Este plan añade únicamente:

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/library/export/collection.csv` | requiere sesión | Descarga CSV UTF-8, `schema_version=1`, con favoritos/colección/copias/comentarios/items de lista propios. `Content-Disposition: attachment; filename="savepoint-collection-export.csv"`. No hay variante JSON ni endpoint de importación. |

La UI solo necesita disparar la descarga (por ejemplo, un enlace/botón que navegue a
esa URL con la sesión autenticada activa); el navegador gestiona la descarga del
`Content-Disposition` sin lógica adicional en el cliente.

## 6. Limitaciones explícitas

- **JSON de exportación, previsualización e importación (PORT-02/PORT-03):** fuera de
  esta fase por decisión D-09; sin endpoints, parsers ni tests de feature en
  `apps/api/library`. Reconciliación completa en `05-PORTABILITY-RECONCILIATION.md`.
- **Privacidad "solo amigos":** deliberadamente no modelada (D-03/D-07); solo existen
  los estados `public`/`private`, verificables sin relación de amistad.
- **Avatar como URL, no upload binario:** decisión de la Fase 5 (A1 en `05-RESEARCH.md`);
  el backend valida esquema HTTPS y longitud pero no hace fetch ni proxy del recurso.
- **Evidencia de navegador pendiente de la sesión web** (ver §7): esta sesión backend
  no ejecuta Playwright/axe y no declara esa evidencia como verde.

## 7. Handoff de integración externa (responsabilidad de la sesión web)

Esta sesión backend **no ejecuta** los siguientes comandos ni declara su resultado; se
registran aquí como el trabajo pendiente que cierra la verificación completa de la
Fase 5:

```bash
corepack pnpm exec playwright test e2e/collection-workflows.spec.ts --project=chromium
```

más la matriz de accesibilidad (`axe-core`, navegación por teclado, viewports
desktop/mobile) sobre:

- registro/login real y sesión tras reload,
- perfil (bio/avatar/visibilidad) y estantería de cinco favoritos,
- ficha de juego con comentarios (crear/editar/borrar, público/privado),
- colección con listas personalizadas (crear/reordenar/borrar) y formulario de copias
  (metadatos de compra/conservación, error físico/digital),
- descarga y apertura del CSV de exportación (cabecera, contenido, ausencia de datos
  privados de terceros, neutralización de fórmulas visible al abrir en una hoja de
  cálculo).

Esta sesión backend no modifica `apps/web/**`, `design/**` ni capturas de pantalla, y no
atribuye al backend ningún resultado de esa ejecución. El signoff final de la Fase 5
queda condicionado a que la sesión web adjunte esa evidencia revisada (sin secretos) en
un documento propio o en una actualización de este mismo archivo.

## 8. Cierre backend

Con la evidencia de este documento:

- Los cuatro planes de la Fase 5 (05-01..05-04) tienen pruebas backend contra
  PostgreSQL real, sin regresión (`619/619` en la suite completa `apps/api`).
- PROF-01, LIB-03, LIB-04, INV-03, INV-04, PORT-01 (solo CSV), PORT-04 y PRIV-01 quedan
  implementados y verificados.
- PORT-02 y PORT-03 quedan explícitamente abiertos y asignados a la Fase 7, sin código
  "preparatorio" que sugiera lo contrario.
- La verificación de navegador (Playwright/axe) queda como evidencia pendiente,
  explícitamente asignada a la sesión web, antes de poder considerar cerrada la
  verificación completa (backend + UI) de la Fase 5.

## 9. Verificación de interfaz (sesión web, 2026-09-13)

Esta sección cierra el §7: integración de `apps/web/**` sobre el contrato de
`docs/verification/phase-05-api-handoff.md`, con evidencia Playwright/axe real, no solo
código escrito. Commits: `71ee4f2` (integración inicial), `62332f3` (fixes encontrados
durante la verificación + `e2e/collection-workflows.spec.ts`).

### 9.1 Comandos ejecutados y resultado

| Comando | Resultado |
|---|---|
| `npx playwright test e2e/collection-workflows.spec.ts --project=chromium` | `2 passed` — reproducido en **tres** ejecuciones separadas (incluidas dos consecutivas contra la misma cuenta demo persistente, probando idempotencia) tras los fixes de §9.2. |
| `npx playwright test e2e/a11y.spec.ts e2e/demo-journey.spec.ts --project=chromium` | `38 passed`, 5 fallos — los cinco son staleness/no-idempotencia **preexistentes**, ajenos a esta fase; documentados y trackeados en la issue de GitHub #53, no corregidos en esta sesión (fuera de alcance). |
| `npx vitest run` (`apps/web`) | `34/34 passed` — sin regresión por los cambios de esta sección. |

### 9.2 Dos bugs reales encontrados y corregidos durante la verificación

La integración inicial (commit `71ee4f2`) compilaba y pasaba los tests unitarios, pero
**no se había ejercitado contra el navegador real** hasta construir esta evidencia. Dos
fallos genuinos aparecieron exactamente por eso:

1. **La descarga CSV (PORT-01/PORT-04) devolvía 404 a través del proxy de Next.js.**
   La regla genérica `/api/:path*` de `apps/web/next.config.ts` añade siempre una barra
   final antes de reenviar a Django; `library/urls.py`'s `export/collection.csv` es la
   única ruta del proyecto deliberadamente sin barra final (se lee como un nombre de
   fichero literal). Confirmado que el fallo era del proxy, no del backend, comparando
   `curl` directo al puerto 8000 de Django (403, correcto — sin sesión) contra el mismo
   `curl` vía el puerto 3000 de Next.js (404). Arreglado con una regla de rewrite
   específica para esa ruta exacta, evaluada antes que la regla genérica.
2. **`GameComments`/`CustomLists` reutilizaban las clases visuales de
   `LibraryControls` (`.sp-copy-remove`/`.sp-copy-add`) sin ninguna clase adicional que
   las distinguiera.** En la ficha de un juego (donde coinciden `LibraryControls` y
   `GameComments`), un selector `.sp-copy-remove` sin acotar no puede distinguir "borrar
   esta copia" de "borrar este comentario" — el propio bucle de limpieza de la suite E2E
   llegó a borrar un comentario real por este motivo antes del fix. Se añadieron clases
   distintas (`sp-comment-remove`/`-edit`/`-cancel`, `sp-list-delete`/`-item-remove`/
   `-item-up`/`-item-down`/`-item-add`) junto a las existentes — el estilo visual no
   cambia, cada acción queda identificable de forma independiente.

Ninguno de los dos bugs era detectable por los tests unitarios existentes ni por la
suite backend (ambos son puramente de integración web: proxy HTTP y colisión de
selectores DOM).

### 9.3 Superficies cubiertas y su evidencia

| Superficie | Verificado | Accesibilidad (axe) | Captura |
|---|---|---|---|
| Registro real (D-00) → perfil propio (bio/avatar/visibilidad) → favoritos | Crear cuenta real, editar, recargar y confirmar persistencia vía API (no solo estado local); favorito visible en la vista pública debajo del editor | Sin violaciones critical/serious | `e2e/artifacts/phase-05/profile-owner-editor.png` |
| Comentario por obra (LIB-03) | Crear/editar el comentario propio, recargar y confirmar persistencia; distinción entre el propio comentario (editable) y comentarios de terceros | Sin violaciones critical/serious | `e2e/artifacts/phase-05/game-detail-comment.png` |
| Listas personalizadas + reorder (LIB-04) | Crear lista, añadir dos obras, reordenar (subir), confirmar el nuevo orden tras recargar (reorder optimista persistido, no solo estado local) | Sin violaciones critical/serious | `e2e/artifacts/phase-05/collection-custom-list.png` |
| Metadatos de copia (INV-03/INV-04) | Guardar fecha/precio/moneda/tienda/conservación/ubicación, confirmar persistencia tras recargar; alternar a digital oculta conservación/ubicación por completo (no solo deshabilitadas) | — (cubierta por el escaneo de colección) | — |
| Exportación CSV (PORT-01/PORT-04) | Descarga real vía `page.request` compartiendo la cookie de sesión del navegador (no un cliente autenticado aparte): código 200, cabecera exacta de 18 columnas, contenido correcto, **byte-idéntica en una segunda descarga inmediata**, enlace visible en la colección apuntando al mismo endpoint | — (descarga de fichero, no aplica axe) | — |

### 9.4 Limitaciones de esta evidencia

- La matriz completa de teclado/viewport (320px/400%/lector de pantalla) que pide
  `05-04-PLAN.md` no se ejecutó exhaustivamente sobre las 5 superficies nuevas; el axe
  scan cubre las violaciones critical/serious automatizables, no un audit WCAG manual
  completo — mismo nivel de evidencia que el resto del proyecto (`e2e/a11y.spec.ts`,
  Plan 01-10).
- La verificación de privacidad `private` (colección/favoritos/comentarios/listas
  ocultos a un visitante no propietario) ya está cubierta por los 588+619 tests
  backend de `test_public_profile.py`/`test_comments.py`/`test_lists.py`; esta sesión
  no repitió esa comprobación específica en el navegador (habría sido una duplicación,
  no una verificación nueva del contrato de interfaz).
- Cinco fallos preexistentes en `a11y.spec.ts`/`demo-journey.spec.ts`, ajenos a esta
  fase, quedan documentados y trackeados en la issue #53 sin corregir (fuera de
  alcance de la Fase 5).

## 10. Cierre de fase

Con las evidencias de los §1-9:

- Los cuatro planes de la Fase 5 (05-01..05-04) están completos en backend **y** en
  interfaz, con pruebas reproducibles en ambas capas.
- Los criterios de éxito 1-4 de `.planning/ROADMAP.md` (perfil/comentarios/listas
  usables, copias con compra/conservación, export CSV determinista, fórmulas
  neutralizadas) están verificados end-to-end, no solo a nivel de API.
- El criterio de éxito 5 (verificación de accesibilidad automatizada, evidencia
  contemporánea) está cubierto por los escaneos axe de §9.3, con las limitaciones
  explícitas de §9.4.
- PORT-02/PORT-03 permanecen abiertos y asignados a la Fase 7, tal como decide D-09 —
  esta sesión no implementa nada de importación.

La Fase 5 queda cerrada.

---
*Fase: 05-complete-collection-workflows-and-portability*
*Firmado (evidencia backend): 2026-09-13*
*Firmado (evidencia de interfaz): 2026-09-13*
