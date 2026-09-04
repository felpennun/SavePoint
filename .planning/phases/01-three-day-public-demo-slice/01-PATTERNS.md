# Fase 1: Three-Day Public Demo Slice - Mapa de patrones

**Mapeado:** 2026-09-04  
**Archivos o familias clasificados:** 34  
**Análogos encontrados:** 0 / 34

## Resultado del análisis

SavePoint es un repositorio greenfield. El inventario de Git contiene artefactos de planificación, documentación y la infraestructura interna de GSD, pero ningún modelo Django, endpoint DRF, página Next.js, componente React, migración, importador de datos, prueba de producto o configuración de despliegue de SavePoint. Por tanto, **no existe ningún análogo de código de aplicación rastreado que deba copiarse**.

Los archivos bajo `.codex/` implementan la herramienta de planificación y no el producto SavePoint. Aunque están rastreados, no coinciden en rol ni flujo de datos con la aplicación y quedan expresamente excluidos como análogos. Los planes deben establecer los primeros patrones del producto siguiendo `01-RESEARCH.md`, `01-UI-SPEC.md`, las decisiones D-01–D-20 y los requisitos de la fase.

## Clasificación de archivos

| Archivo nuevo o modificado | Rol | Flujo de datos | Análogo más cercano | Calidad |
|---|---|---|---|---|
| `apps/api/manage.py` | config / utilidad | request-response / comandos | ninguno | sin análogo |
| `apps/api/config/settings.py` | config | request-response | ninguno | sin análogo |
| `apps/api/config/urls.py` | route | request-response | ninguno | sin análogo |
| `apps/api/accounts/models.py` | model | CRUD | ninguno | sin análogo |
| `apps/api/accounts/serializers.py` | transform / guard | request-response | ninguno | sin análogo |
| `apps/api/accounts/views.py` | controller | request-response | ninguno | sin análogo |
| `apps/api/accounts/urls.py` | route | request-response | ninguno | sin análogo |
| `apps/api/catalogue/models.py` | model | CRUD | ninguno | sin análogo |
| `apps/api/catalogue/serializers.py` | transform | request-response | ninguno | sin análogo |
| `apps/api/catalogue/views.py` | controller | request-response | ninguno | sin análogo |
| `apps/api/catalogue/search.py` | service | transform / request-response | ninguno | sin análogo |
| `apps/api/catalogue/management/commands/import_catalogue.py` | utility | file-I/O / batch / CRUD | ninguno | sin análogo |
| `apps/api/catalogue/migrations/*` | migration | CRUD | ninguno | sin análogo |
| `apps/api/library/models.py` | model | CRUD | ninguno | sin análogo |
| `apps/api/library/serializers.py` | transform / validation | request-response | ninguno | sin análogo |
| `apps/api/library/services.py` | service | CRUD / request-response | ninguno | sin análogo |
| `apps/api/library/views.py` | controller | request-response | ninguno | sin análogo |
| `apps/api/library/popularity.py` | service | batch / transform | ninguno | sin análogo |
| `apps/api/**/tests/*.py` | test | CRUD / request-response / batch | ninguno | sin análogo |
| `apps/web/app/[locale]/layout.tsx` | component / provider | request-response | ninguno | sin análogo |
| `apps/web/app/[locale]/{page,login/page,catalogue/page,games/[id]/page,collection/page,profiles/[alias]/page,sources/page}.tsx` | component / route | request-response | ninguno | sin análogo |
| `apps/web/components/{AppShell,TopNavigation,MobileMenu,Button,TextField,Notice}.tsx` | component | event-driven | ninguno | sin análogo |
| `apps/web/components/{CoverImage,GameCard,CoverGrid,SearchForm}.tsx` | component | request-response / event-driven | ninguno | sin análogo |
| `apps/web/components/{StatusControl,RatingControl,CopyForm,CopyList}.tsx` | component | CRUD / event-driven | ninguno | sin análogo |
| `apps/web/components/{ProvenanceSummary,RecommendationStrip,Skeleton,LanguageSwitch}.tsx` | component | request-response / event-driven | ninguno | sin análogo |
| `apps/web/i18n/{es,en}.ts` | config / transform | request-response | ninguno | sin análogo |
| `apps/web/lib/api.ts` | service | request-response | ninguno | sin análogo |
| `apps/web/app/globals.css` | config / presentation | transform | ninguno | sin análogo |
| `data/raw/*`, `data/manifests/*`, `data/assets/*` | data / config | file-I/O / batch | ninguno | sin análogo |
| `infra/compose.yaml`, `apps/{api,web}/Dockerfile` | config | request-response / batch | ninguno | sin análogo |
| `infra/render.yaml` | config | batch / deployment | ninguno | sin análogo |
| `e2e/{demo-journey,a11y,deployed-smoke}.spec.ts` | test | request-response / event-driven | ninguno | sin análogo |
| `scripts/{check-secrets,check-evidence}.ps1` | utility / test | file-I/O / batch | ninguno | sin análogo |
| `docs/adr/*.md`, `docs/methodology/*` | documentation / evidence | file-I/O / append-only | ninguno | sin análogo |

## Asignaciones de patrón

Al no existir análogos, estas asignaciones indican la fuente normativa que sustituye a un archivo existente.

### Backend Django/DRF

**Aplicar a:** `apps/api/config/*`, `accounts/*`, `catalogue/*`, `library/*`  
**Fuente:** `01-RESEARCH.md`, secciones “Architectural Responsibility Map”, “Architecture Patterns” y “Security Domain”.

- Mantener un monolito modular Django con cuentas, catálogo y biblioteca como módulos separados.
- Usar autenticación de sesión Django, protección CSRF y una frontera same-origin; no crear tokens o criptografía propios.
- Autorizar por usuario en el servidor. La proyección pública debe tener serializer/query allowlist independiente del DTO privado.
- Validar con serializers, ORM, constraints y transacciones. No concatenar SQL ni aceptar URLs arbitrarias.
- Actualizar estado actual e historial en una transacción; una transición idéntica no debe duplicar historial.
- Representar la nota con un entero exacto de medios pasos, nullable y limitado a `1..10`.

### Modelo relacional

**Aplicar a:** `catalogue/models.py`, `library/models.py` y migraciones  
**Fuente:** `01-RESEARCH.md`, “Pattern 2: Modelo de dominio mínimo”.

El primer patrón de dominio debe conservar:

```text
GameWork -> GameRelease -> Edition
         -> GameAlias
         -> SourceRecord / AssetAttribution
         -> RelatedContent (DLC/expansion no accionable)

User + GameWork -> LibraryEntry -> StatusTransition
User + GameWork + Release/Edition -> OwnedCopy
```

Usar UUID interno estable; conservar identificadores de fuente por separado. Status y rating pertenecen a la obra, mientras cada copia es un registro independiente asociado a una release/edición válida.

### Importación y procedencia

**Aplicar a:** `import_catalogue.py`, `data/raw/*`, `data/manifests/*`, `data/assets/*`  
**Fuente:** `01-RESEARCH.md`, “Immutable source snapshot”, “Data and Cover Strategy”.

- El raw es inmutable y la importación es explícita, atómica, idempotente y verificable por SHA-256.
- El manifest incluye fuente, URL, licencia, fecha de recuperación, revisión/fecha de corte, recuento y checksum.
- Los datos estructurados y las imágenes tienen manifests/licencias separados.
- Cada asset requiere decisión explícita de derechos; si falta, usar placeholder propio.
- Ningún arranque, request o despliegue descarga Wikidata ni llama a un proveedor.

### Búsqueda y popularidad

**Aplicar a:** `catalogue/search.py`, `library/popularity.py`  
**Fuente:** `01-RESEARCH.md`, patrones 5 y 6.

- Búsqueda: normalización Unicode, títulos y aliases ES/EN, exacto/prefijo antes de trigramas, umbral fijado y desempate determinista.
- Popularidad: fórmula versionada, fecha de corte, hash de entrada y desempate estable por identificador canónico.
- El DTO identifica `algorithm_id='popularity-v1'`; la UI lo presenta como baseline agregado, nunca como recomendación personalizada.

### Frontend y componentes

**Aplicar a:** rutas, componentes, i18n y estilos bajo `apps/web/`  
**Fuente:** `01-UI-SPEC.md` completo.

- Los componentes consumen tokens semánticos `--sp-*`; no incrustar colores crudos en componentes.
- Implementar HTML nativo accesible, foco visible, targets mínimos de 44 px y ninguna acción exclusiva de hover.
- `StatusControl` usa `fieldset`/radios y `RatingControl` rango o radios accesibles con valor numérico visible.
- Las mutaciones requieren guardado explícito, estado pendiente, mensajes localizados, preservación de valores y manejo de foco.
- La consulta vive en `?q=`; el catálogo pagina 24 elementos y conserva locale/query.
- Diccionarios ES/EN completos con prueba de paridad; no construir plurales concatenando fragmentos.
- Renderizar metadata externa como texto. No usar `dangerouslySetInnerHTML` ni destinos de enlace no allowlisted.

### API cliente y frontera de secretos

**Aplicar a:** `apps/web/lib/api.ts`, settings, Docker y Render  
**Fuente:** `01-RESEARCH.md`, “Secret acceptance gate”; `01-UI-SPEC.md`, “Privacy, Security, and Source Transparency”.

- Sólo el servidor accede a secretos y endpoints internos.
- Ningún secreto usa `NEXT_PUBLIC_*`, argumento Docker, valor literal en Blueprint o mensaje de UI.
- El navegador usa rutas relativas same-origin; los retornos tras login también son relativos y validados.
- Los errores públicos son localizados y no contienen trazas, IDs internos, credenciales ni detalles del proveedor.

### Pruebas

**Aplicar a:** pruebas backend/frontend, `e2e/*` y scripts estáticos  
**Fuente:** `01-RESEARCH.md`, “Validation Architecture”; `01-UI-SPEC.md`, “Accessibility Acceptance Checks”.

- Backend: pytest/pytest-django contra PostgreSQL real, incluyendo constraints, CSRF, IDOR, import idempotente y determinismo.
- Frontend: Vitest/Testing Library para i18n, copy contractual, tokens y componentes por rol/nombre.
- E2E tracer-first: homepage → login → catálogo → búsqueda → ficha → estado → 3.5 estrellas → dos copias → colección → perfil → logout.
- Playwright + axe en ES/EN y viewports móvil/escritorio, con comprobaciones manuales versionadas para teclado, 320 px y zoom 400%.
- Fixtures hostiles deben cubrir XSS, URL no permitida, dos usuarios para IDOR y checksum incorrecto.

### Operación y evidencia

**Aplicar a:** Compose, Dockerfiles, Render, ADRs y metodología  
**Fuente:** `01-RESEARCH.md`, “Deployment and Reproducibility” y “Thesis and Agent Evidence”.

- Las mismas imágenes fijadas se ejecutan localmente y en Render; servicios `web`, `api`, `db`, healthchecks y migración predeploy.
- Secretos mediante entorno de runtime con placeholders `sync: false`/valores generados.
- ADRs documentan contexto, alternativas, decisión, consecuencias, evidencia y aprobación del autor.
- Ledger de agentes append-only con actor, rol, runtime/modelo disponible, entradas, salidas y hashes, herramientas, resultado, limitaciones y tipo `proposal`, `automated-check` o `author-decision`.

## Patrones compartidos que deben establecerse

### Autenticación y autorización

No hay excerpt de código existente. El primer patrón debe ser Django session auth + CSRF, permisos por endpoint/objeto, querysets limitados al propietario y serializer público allowlist.

### Validación y errores

No hay excerpt de código existente. El primer patrón debe combinar validación DRF, constraints PostgreSQL y errores públicos uniformes sin información sensible. El frontend preserva datos introducidos y enfoca el resumen de errores.

### Persistencia y transacciones

No hay excerpt de código existente. PostgreSQL es la única ruta canónica local, CI y desplegada; no usar SQLite. Las mutaciones con historial usan `transaction.atomic()` y constraints en base de datos.

### Localización

No hay excerpt de código existente. La API devuelve códigos estables, no copy localizada; el frontend resuelve ES/EN, fallback a inglés/original y paridad completa.

### Accesibilidad

No hay excerpt de código existente. Los primeros componentes locales deben fijar nombres accesibles, foco, semántica nativa, estados loading/error/empty y comportamiento de teclado conforme al UI-SPEC.

### Reproducibilidad y procedencia

No hay excerpt de código existente. Dataset, seed, popularidad, lockfiles, imágenes y evidencia deben conservar versión, hashes y parámetros deterministas desde el primer commit de aplicación.

## Sin análogo encontrado

| Familia | Motivo | Fuente que debe usar el planner |
|---|---|---|
| Backend Django/DRF completo | No existe código de aplicación Python | `01-RESEARCH.md` y documentación oficial citada allí |
| Frontend Next.js/React completo | No existe código TS/TSX/CSS de producto | `01-UI-SPEC.md` y `01-RESEARCH.md` |
| Modelos/migraciones PostgreSQL | No existe esquema de producto | Modelo relacional recomendado y D-09, D-13–D-16 |
| Pipeline dataset/assets | No existe importador ni dato versionado | Estrategia Wikidata/Commons y DATA-01/02 |
| Pruebas y E2E | No existe configuración de test de producto | Validation Architecture y acceptance checks |
| Infraestructura/deploy | No existe Compose, Dockerfile ni Blueprint | Deployment and Reproducibility |
| ADRs/evidencia de agentes | No existe formato de evidencia del proyecto | Thesis and Agent Evidence y AGENT-01..03 |

## Metadatos

**Ámbito de búsqueda:** archivos rastreados por Git en la raíz; se comprobaron artefactos de planificación, documentación y `.codex/`.  
**Código de aplicación rastreado escaneado:** 0 archivos.  
**Análogos válidos:** 0.  
**Razón de exclusión principal:** `.codex/` pertenece al runtime GSD y no al producto SavePoint.  
**Fecha de extracción:** 2026-09-04.

