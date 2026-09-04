# Phase 1: Three-Day Public Demo Slice - Research

**Researched:** 2026-09-04
**Domain:** walking skeleton web, catálogo legal offline, autenticación controlada, despliegue reproducible
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Demo Journey
- **D-01:** The public URL opens a realistic product homepage with SavePoint branding, value proposition, representative content, and a visible login entry.
- **D-02:** Controlled access uses a conventional username/password form with demo credentials displayed separately; demo passwords are never infrastructure secrets.
- **D-03:** Successful login opens the catalogue rather than a dashboard or collection page.
- **D-04:** The product contains no guided tour. Actions and empty states must be self-explanatory; a separate presentation script will support the tribunal demo.

### Initial Catalogue
- **D-05:** Phase 1 uses a curated, reviewed sample of 100-300 games, while identifiers, schemas, and import boundaries must support thousands later.
- **D-06:** The sample represents multiple eras, genres, PC, current consoles, and historical platforms rather than favouring one ecosystem.
- **D-07:** Maximise cover availability only where source terms permit display/caching. Retain attribution and use a coherent first-party placeholder when rights or data are unavailable.
- **D-08:** Each game page shows concise provenance and links to a detailed global sources/methodology page.
- **D-09:** Catalogue identity is hierarchical: work → releases/platforms/editions → user-owned copies. Distinct remakes are separate linked works. — **Reversibility:** costly — flattening or changing this hierarchy later would require catalogue and ownership-data migration.
- **D-10:** Interface and catalogue presentation support Spanish and English per user preference, with explicit fallback to English or the original value and alternative titles searchable in both languages.
- **D-11:** DLC and expansions are related child content inside the base-game page, not independent catalogue results or backlog entries.
- **D-12:** Initial search tolerates case, accents, bilingual alternative titles, and small typographical errors. Advanced faceted filters and autocomplete remain Phase 4.

### Backlog and Inventory
- **D-13:** Ratings use five stars with half-star increments. Store them in an exact normalized representation suitable for later recommendation/evaluation calculations.
- **D-14:** A game exposes one current state—pending, playing, completed, or abandoned—while retaining a dated transition history. — **Reversibility:** costly — removing history after launch would discard chronological evidence used by later statistics and experiments.
- **D-15:** Phase 1 copy creation requires only physical/digital format, platform, and edition. Purchase, conservation, location, and private-note fields arrive in Phase 3.
- **D-16:** Status and rating belong to the game/work; multiple platform copies remain separate ownership records. Preserve a clean model boundary for optional version-level ratings in a later release.

### Visual Direction
- **D-17:** Use a modern hybrid visual style: dark, cover-led catalogue presentation with clean, highly legible inventory and data panels.
- **D-18:** The initial dark palette is provisional, accessible, and implemented through replaceable design tokens. Future screenshots, links, sketches, and palettes can become canonical visual references through `$gsd-ui-phase 1`.
- **D-19:** Catalogue uses an adaptive cover grid. Essential information is visible; richer information may appear on large screens or keyboard focus, but no action may depend only on hover.
- **D-20:** Navigation uses a top bar on desktop and a compact menu on mobile, covering home, catalogue, collection, profile, and session actions.

### the agent's Discretion
- Exact demo-game selection within the agreed representative 100-300 boundary, subject to documented lawful provenance.
- Exact provisional colour values, typography, spacing, placeholder artwork, and responsive breakpoints, subject to accessible contrast and replaceable tokens.
- Exact copy and micro-interaction wording in Spanish and English, provided both locales remain complete and consistent.

### Deferred Ideas (OUT OF SCOPE)
- Advanced catalogue filters, autocomplete, and resilient live enrichment — Phase 4.
- Purchase details, conservation state, storage location, private notes, lists, comments, and import/export — Phase 3.
- Content, collaborative, and hybrid recommenders plus academic comparison — Phases 5-7.
- Research comparison panel and full security/operations hardening — Phase 8.
- Optional rating per release/platform — future release; Phase 1 stores only game-level ratings.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|---|---|---|
| AUTH-01 | User can sign in to and sign out of a controlled account. | Django session auth, CSRF and controlled seeded account. |
| PROF-02 | An authorised visitor can view a public profile. | Server-side allowlisted projection and indistinguishable unavailable response. |
| CAT-01 | User can search video games by title. | PostgreSQL normalized search document plus trigram ranking. |
| CAT-03 | Each game has a detail page showing available data and its provenance. | Work hierarchy and `SourceRecord`/`AssetAttribution`. |
| CAT-04 | Canonical identifiers do not depend on enrichment API. | Internal immutable UUID plus retained Wikidata QID as source identifier. |
| CAT-06 | Catalogue remains usable with local data when API unavailable. | Versioned JSON/CSV snapshot imported into PostgreSQL; zero runtime provider calls. |
| LIB-01 | User can set four backlog states. | `LibraryEntry.current_status` plus append-only `StatusTransition`. |
| LIB-02 | User can rate consistently. | Integer half-star units (`1..10`, nullable), never binary float. |
| INV-01 | User can register multiple copies. | Independent `OwnedCopy` rows under user and release/edition. |
| INV-02 | Copy records format, platform and edition. | Database constraints and server validation. |
| INV-05 | Private notes and purchase details never appear publicly. | Phase 1 omits those fields; public serializer is explicit allowlist. |
| DATA-01 | Stable, citable, legally suitable dataset. | Curated Wikidata CC0 snapshot; media handled per-file separately. |
| DATA-02 | Dataset records version, licence, URL, retrieval date, checksum. | Checked-in manifest and SHA-256 over immutable raw snapshot. |
| REC-02 | Popularity baseline. | Deterministic aggregate interaction score, precomputed/tie-broken by canonical ID. |
| SEC-02 | No secret/API key in public artifacts. | Runtime-only env secrets, build-context exclusions, bundle and repository scans. |
| OPS-01 | Internet deployment documented. | Render Blueprint with web/API/PostgreSQL, health checks and secret placeholders. |
| OPS-02 | Reproducible local run. | Pinned Docker Compose services, deterministic seed command and README runbook. |
| OPS-03 | Lawful offline demo works. | Bundled snapshot/assets and no dependency on provider availability. |
| QUAL-03 | Responsive and WCAG 2.2 AA verifiable. | UI-SPEC checks, Playwright journey, axe scan and manual keyboard/reflow evidence. |
| DOC-01 | Architecture decisions record alternatives/rationale. | ADRs for stack, data source, auth boundary and deployment. |
| AGENT-01 | Record agent roles/responsibilities. | Append-only agent activity/evidence manifest. |
| AGENT-02 | Retain protocols, configuration, models, tools and artifacts. | Versioned methodology records with hashes and links, excluding secrets. |
| AGENT-03 | Distinguish proposals, verification and author decisions. | Typed evidence ledger (`proposal`, `automated-check`, `author-decision`). |
</phase_requirements>

## Summary

La Fase 1 debe planificarse como un único recorrido vertical demostrable, no como la primera entrega parcial de todas las capas futuras: homepage → login controlado → catálogo → ficha → estado/nota/dos copias → colección → perfil público → cierre de sesión. La ruta crítica necesita datos locales, PostgreSQL y autenticación real desde el primer día; las recomendaciones avanzadas, la API de enriquecimiento y los campos ricos se difieren explícitamente. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`]

Para el corpus, la opción de menor riesgo es producir una instantánea curada de 100–300 obras desde datos estructurados de Wikidata, cuyos espacios estructurados se publican bajo CC0, conservando QID, consulta, fecha, revisión/fecha de corte y SHA-256. [CITED: https://www.wikidata.org/wiki/Wikidata:Licensing] Las imágenes no heredan CC0: cada archivo de Wikimedia Commons tiene licencia y obligaciones propias, y Commons recomienda verificar cada caso; por eso sólo se admite una lista explícita revisada con autor/licencia/URL o el placeholder propio. [CITED: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en]

La arquitectura mínima sigue el stack ya investigado del proyecto: Next.js/TypeScript para la UI, Django/DRF para identidad y reglas, y PostgreSQL como única ruta persistente. [VERIFIED: `AGENTS.md`] El despliegue recomendado para esta fase es Render mediante `render.yaml`, dos servicios web Docker y PostgreSQL administrado; los secretos quedan como valores no sincronizados/generados en la plataforma. Render documenta Blueprints, `preDeployCommand`, `healthCheckPath`, referencias a la cadena de conexión y variables `sync: false`/`generateValue`. [CITED: https://render.com/docs/blueprint-spec]

**Primary recommendation:** planificar cuatro olas: (0) contratos, esqueleto y pruebas; (1) PostgreSQL + import/seed + auth; (2) UI bilingüe y recorrido completo; (3) seguridad, accesibilidad, despliegue y paquete de evidencia.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Localización ES/EN y estados UI | Browser / Frontend Server | API / Backend | UI resuelve copy y rutas; API devuelve códigos/valores estables, no frases localizadas. [ASSUMED] |
| Autenticación y sesión | API / Backend | Frontend Server | Django valida credenciales, emite sesión y aplica CSRF; Next sólo presenta el flujo. [CITED: https://docs.djangoproject.com/en/5.2/topics/auth/default/] |
| Catálogo, jerarquía y procedencia | Database / Storage | API / Backend | PostgreSQL conserva identidad/relaciones; DRF expone DTOs validados. [VERIFIED: `AGENTS.md`] |
| Búsqueda tolerante | Database / Storage | API / Backend | Normalización y trigramas se ejecutan donde residen los datos; el cliente conserva `q` en URL. [CITED: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/search/] |
| Mutaciones backlog/nota/copias | API / Backend | Database / Storage | Reglas, propiedad, constraints y transacciones deben ser autoritativas en servidor. [ASSUMED] |
| Perfil público | API / Backend | Frontend Server | Serializer/proyección allowlist; SSR sólo recibe datos ya reducidos. [CITED: https://nextjs.org/docs/app/guides/data-security] |
| Baseline de popularidad | API / Backend | Database / Storage | Agregado determinista y cacheable; nunca entrenamiento en request. [VERIFIED: `AGENTS.md`] |
| Dataset y media offline | CDN / Static | Database / Storage | Raw/manifest son artefactos versionados; datos normalizados se importan a PostgreSQL. [ASSUMED] |
| Secretos y proveedor | API / Backend | Deployment platform | Sólo runtime server; nada `NEXT_PUBLIC_*` ni argumentos Docker. [CITED: https://nextjs.org/docs/app/guides/environment-variables] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---|---:|---|---|
| Python | 3.13.x exacta | Backend y scripts de datos | Versión decidida por la investigación global; el host sólo tiene 3.14.2, así que Docker debe fijar 3.13. [VERIFIED: `AGENTS.md`; VERIFIED: environment probe] |
| Django | 5.2.17 LTS | Auth, ORM, migraciones y dominio | Evita implementar identidad, hash de contraseñas, sesión y migraciones. [VERIFIED: `AGENTS.md`; CITED: https://www.djangoproject.com/download/] |
| Django REST Framework | 3.18.0 | API JSON y permisos | Encaja con Django y permite serializers públicos distintos de los privados. [VERIFIED: `AGENTS.md`; CITED: https://www.django-rest-framework.org/community/release-notes/] |
| PostgreSQL | 18.x, misma patch local/remota | Persistencia única | Relaciones y constraints para obra/releases/copias/historial; trigramas para D-12. [VERIFIED: `AGENTS.md`; CITED: https://www.postgresql.org/docs/current/pgtrgm.html] |
| Next.js | 16.2.x | App Router, SSR y UI | Dirección aprobada del proyecto y soporte de ejecución como servidor Node. [VERIFIED: `AGENTS.md`; CITED: https://nextjs.org/blog/next-16-2] |
| React / React DOM | 19.2.7 | Componentes accesibles | Generación fijada en la investigación global. [VERIFIED: `AGENTS.md`; CITED: https://react.dev/versions] |
| TypeScript | 6.0.x strict | Contratos frontend | Reduce deriva entre estados/DTOs; el esquema OpenAPI queda diferido si amenaza el plazo. [VERIFIED: `AGENTS.md`] |
| Tailwind CSS | 4.3.x | Tokens y layout adaptativo | Implementa UI-SPEC sin introducir kit de componentes/registro. [VERIFIED: `AGENTS.md`; VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---|---:|---|---|
| psycopg | 3.x locked | Driver PostgreSQL | Backend local/CI/Render. [VERIFIED: `AGENTS.md`] |
| pytest + pytest-django | 9.1.1 + compatible locked | Tests del dominio/API | Desde Wave 0; ejecutar contra PostgreSQL. [VERIFIED: `AGENTS.md`] |
| Vitest | 5.0.x, validar compatibilidad | Tests de utilidades/componentes | Copy contract, normalización y estados puros. [VERIFIED: `AGENTS.md`] |
| Playwright | 1.62.x | Recorrido E2E | Una prueba Chromium de la demo; matriz completa puede ejecutarse al gate. [VERIFIED: `AGENTS.md`] |
| axe-core | locked | Barrido a11y automatizado | Integrado en Playwright para las 7 páginas y 2 viewports/idiomas. [VERIFIED: `AGENTS.md`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| Next.js + DRF | Django templates + HTMX | Menos servicios y más rápido, pero contradice la dirección de frontend ya registrada y dificulta el dashboard posterior. [VERIFIED: `AGENTS.md`] |
| Dos servicios públicos | Next.js como BFF + API privada | Reduce CORS/CSRF visible, pero añade proxying y configuración; para tres días se recomienda mismo dominio lógico mediante rewrite/proxy de Next hacia Django. [ASSUMED] |
| Wikidata snapshot | RAWG/IGDB en runtime | Más carátulas/metadata, pero introduce credenciales, términos, cuota y deriva; no es necesario para Phase 1 y DATA-04 está en Phase 4. [VERIFIED: `.planning/REQUIREMENTS.md`] |

**Installation (después del checkpoint de legitimidad):**

```bash
# backend
python -m pip install "Django==5.2.17" "djangorestframework==3.18.0" "psycopg[binary]~=3.3" "pytest==9.1.1" pytest-django
# frontend
pnpm add next@16.2 react@19.2.7 react-dom@19.2.7 tailwindcss@4.3
pnpm add -D typescript@6 vitest @testing-library/react @playwright/test axe-core
```

Los números anteriores proceden del stack global, no de una resolución de lock exitosa en esta sesión; el ejecutor debe resolverlos dentro de las imágenes y conservar lockfiles. [VERIFIED: `AGENTS.md`; ASSUMED]

## Package Legitimacy Audit

El seam obligatorio se ejecutó el 2026-09-04. No pudo consultar metadatos de registro (todos los campos quedaron `null`) y clasificó todos los paquetes `SUS` por `unknown-age`, `unknown-downloads` y `no-repository`; además, PyPI quedó inaccesible por restricción de socket y PowerShell bloqueó `npm.ps1`. Esto es ausencia de observación, no evidencia de ilegitimidad. [VERIFIED: command output from this session]

| Package group | Registry | Age / Downloads / Source | Verdict | Disposition |
|---|---|---|---|---|
| `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@tailwindcss/postcss` | npm | no observado | SUS | Checkpoint humano + resolver por `npm.cmd view`; origen oficial citado. |
| `vitest`, `@testing-library/react`, `@playwright/test`, `axe-core` | npm | no observado | SUS | Checkpoint humano + resolver por `npm.cmd view`; origen oficial/proyecto debe confirmarse. |
| `Django`, `djangorestframework`, `psycopg`, `pytest`, `pytest-django` | PyPI | no observado | SUS | Checkpoint humano + resolver dentro de red aprobada; origen oficial citado donde existe. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** todos los anteriores por fallo de metadatos; el plan debe insertar un `checkpoint:human-verify` único antes de instalar.

## Architecture Patterns

### System Architecture Diagram

```text
Browser (ES/EN)
  ├─ GET pages/search ───────────────► Next.js SSR/UI
  │                                      │ server-only fetch
  └─ POST login/status/rating/copy ──────┼──────────────► Django/DRF
                                         │                  ├─ auth/session + CSRF
                                         │                  ├─ permissions/projections
                                         │                  └─ domain services
                                         │                           │ ORM transactions
                                         ▼                           ▼
                                bundled public assets          PostgreSQL 18
                                                                   ▲
Versioned Wikidata snapshot ─► validate/hash/import/seed CLI ───────┤
Reviewed Commons assets ─────► attribution manifest + static assets ┘

Deployment: Render web(next) + web(api) + managed PostgreSQL
Offline: Docker Compose runs the same images + local PostgreSQL; no provider call
```

### Recommended Project Structure

```text
apps/
├── api/
│   ├── config/                 # settings, urls, ASGI/WSGI
│   ├── accounts/               # controlled auth and public projection
│   ├── catalogue/              # work/release/edition/platform/provenance
│   ├── library/                # status, rating, copies, popularity service
│   └── tests/
└── web/
    ├── app/[locale]/           # home/login/catalogue/detail/collection/profile/sources
    ├── components/             # UI-SPEC primitives and domain components
    ├── i18n/                   # en/es dictionaries and parity test
    └── tests/
data/
├── raw/                        # immutable curated export
├── manifests/                  # source URL, revision, date, licence, SHA-256
└── assets/                     # only reviewed media + attribution metadata
docs/
├── adr/                        # architecture choices and alternatives
└── methodology/                # agents/evidence/provenance
infra/
├── compose.yaml
└── render.yaml
e2e/
```

### Pattern 1: Immutable source snapshot → validated import → relational domain

El importer debe fallar de forma atómica si cambia el esquema, falta un identificador, aparece un DLC como obra raíz, una edición no apunta a release/plataforma, la licencia/fecha/URL/checksum no existen o el hash difiere. Después usa `update_or_create`/upsert por `(source, source_id)` pero genera un UUID interno estable para CAT-04. [ASSUMED]

No descargar Wikidata durante el arranque ni el despliegue. El servicio público tiene límites, devuelve 429 y exige un User-Agent adecuado; la consulta de extracción es una tarea explícita y el resultado queda congelado. [CITED: https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual]

### Pattern 2: Modelo de dominio mínimo con invariantes en base de datos

```text
GameWork(id UUID, canonical_slug, original_title, title_en, title_es, description_*, is_dlc=false)
GameAlias(work_id, locale, normalized_value)
Platform(id, name)
GameRelease(id, work_id, platform_id, release_date)
Edition(id, release_id, name)
RelatedContent(parent_work_id, child_source_id, relation='dlc'|'expansion')
SourceRecord(work_id, source, source_id, source_url, retrieved_at, licence, snapshot_sha256)
AssetAttribution(work_id, local_path, creator, licence, licence_url, source_url, reviewed_at)
LibraryEntry(user_id, work_id, current_status, rating_half_steps NULL|1..10)
StatusTransition(entry_id, from_status, to_status, changed_at)
OwnedCopy(user_id, work_id, release_id, edition_id, format='physical'|'digital')
```

Estos nombres y enums son diseño recomendado todavía no implementado, por tanto `[ASSUMED]`; el plan debe convertirlos en migraciones y tests de constraints antes de UI.

### Pattern 3: Mutación transaccional y autorización por propiedad

Estado actual y transición se actualizan en una transacción; una transición idéntica no crea historial duplicado. Rating se recibe como entero `rating_half_steps`, se valida `1..10`, y se presenta dividiendo entre dos. Copias se crean sólo para el usuario autenticado y para release/edition pertenecientes a la obra solicitada. [ASSUMED]

### Pattern 4: Proyección pública separada

Nunca reutilizar el serializer de colección. Crear `PublicProfileSerializer`/query específica con campos permitidos únicamente; su contrato no contiene `OwnedCopy`, email, IDs internos ni futuros campos privados. Responder el mismo 404 seguro para alias inexistente/no autorizado y comprobar también HTML, RSC/preload y JSON. Next recomienda filtrar datos en una DAL antes de pasarlos al contexto de React. [CITED: https://nextjs.org/docs/app/guides/data-security]

### Pattern 5: Búsqueda determinista y gradual

Persistir una clave normalizada (minúsculas + Unicode NFKD + eliminación de marcas) de títulos/aliases y activar `pg_trgm`; primero coincidencia exacta/prefijo, luego similitud por trigramas con umbral fijado y desempate por título normalizado + UUID. El módulo `pg_trgm` ofrece funciones/operadores de similitud e índices GiST/GIN. [CITED: https://www.postgresql.org/docs/current/pgtrgm.html] La consulta, página y locale permanecen en URL; no se incluye autocomplete/facetas. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`]

### Pattern 6: Popularidad explícita, simple y reproducible

Definir antes de sembrar una fórmula versionada, por ejemplo `score = 3*completed + 2*playing + pending + sum(rating_half_steps)/10`, calculada sólo con cuentas demo, con desempate por UUID y fecha de corte registrada. [ASSUMED] Para evitar venderla como personalizada, el DTO incluye `algorithm_id='popularity-v1'`, `generated_at`, `input_snapshot_sha256` y la UI usa el copy canónico de UI-SPEC. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`]

### Anti-Patterns to Avoid

- **Consumir proveedor en request:** rompe CAT-06/OPS-03, introduce deriva/cuota y puede filtrar tokens. Usar snapshot local. [VERIFIED: `AGENTS.md`]
- **Guardar rating como `float`:** representa mal pasos exactos y complica evaluación; usar entero de medios pasos. [ASSUMED]
- **Aplanar plataforma/edición en strings de copia:** contradice D-09 y dificulta migrar a miles de juegos. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`]
- **Compartir serializer privado/público:** una futura adición puede exfiltrar datos por defecto; proyección allowlist dedicada. [ASSUMED]
- **Introducir CORS con cookies sin necesidad:** eleva riesgo CSRF/configuración; exponer una misma origin al navegador mediante proxy/rewrite. [ASSUMED]
- **Sembrar en cada arranque:** duplica o altera demo; comando idempotente explícito con versión/seed. [ASSUMED]
- **Carátulas “fair use” de Wikipedia o scraping:** no cumplen la política acordada; sólo Commons revisado por archivo o placeholder. [CITED: https://commons.wikimedia.org/wiki/Commons:Simple_media_reuse_guide]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Password hashing/session | Crypto/tokens propios | Django auth + session middleware | Django incluye primitivas y controles mantenidos. [CITED: https://docs.djangoproject.com/en/5.2/topics/auth/default/] |
| CSRF | Token casero | Django CSRF middleware/cookie | Debe vincular mutaciones a sesión/origin. [CITED: https://docs.djangoproject.com/en/5.2/ref/csrf/] |
| SQL search | Concatenación SQL/Levenshtein casero | ORM + PostgreSQL `unaccent`/`pg_trgm` | Evita inyección y soporta índices. [CITED: https://www.postgresql.org/docs/current/pgtrgm.html] |
| i18n | Condicionales dispersos | Diccionarios tipados + segmento `[locale]` | Permite paridad y fallback probado. [ASSUMED] |
| Asset legal status | Inferir licencia por dominio | Manifest por archivo + placeholder | Commons advierte que cada archivo debe verificarse. [CITED: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en] |
| Secrets | `.env` comprometido o `NEXT_PUBLIC_*` | Platform env/secret + `.env.example` | Next inlinea `NEXT_PUBLIC_*` en el bundle. [CITED: https://nextjs.org/docs/app/guides/environment-variables] |
| Readiness | Esperas/sleeps | Health checks Compose/Render | Compose documenta `service_healthy`; Render soporta endpoint HTTP. [CITED: https://docs.docker.com/compose/gettingstarted/] |

**Key insight:** en tres días, el ahorro principal proviene de reducir variantes y reutilizar primitivas maduras, no de omitir los límites de datos, auth y despliegue que después obligarían a reescribir la demo.

## Data and Cover Strategy

### Fixed corpus

1. Mantener una consulta SPARQL versionada que obtiene candidatos `instance of video game`, labels/aliases ES/EN, fecha, plataforma, género, desarrollador/editor y relaciones disponibles. La cobertura real de propiedades no está garantizada; registrar ausencias, no inventarlas. [CITED: https://query.wikidata.org/; ASSUMED]
2. Curar manualmente 100–300 QIDs en una allowlist equilibrada por era/plataforma/género; guardar criterios y recuentos. La muestra es demostrativa, no estadísticamente representativa del universo de videojuegos. [ASSUMED]
3. Exportar JSON/CSV, registrar consulta, endpoint, `retrieved_at`, licencia CC0, URL, recuento, revisión/fecha de corte y SHA-256; nunca modificar el raw: una corrección crea una versión nueva. [CITED: https://www.wikidata.org/wiki/Wikidata:Licensing]
4. Generar fixture/import idempotente y reporte de filas aceptadas/rechazadas. DATA-03 completo se difiere a Phase 2; en Phase 1 basta validación release-blocking y resumen de importación. [VERIFIED: `.planning/REQUIREMENTS.md`]

### Covers

- Sólo incorporar un archivo si existe registro explícito de `source_url`, `creator`, `licence`, `licence_url`, `attribution_text`, `retrieved_at`, hash y revisión humana. [ASSUMED]
- No asumir que la imagen de una página Wikipedia está en Commons ni que es reutilizable; si no enlaza a Commons/licencia verificable, usar placeholder. [CITED: https://commons.wikimedia.org/wiki/Commons:Simple_media_reuse_guide]
- Evitar hotlinking; Commons lo permite técnicamente pero no lo recomienda, y la licencia debe cumplirse igualmente. Servir una copia optimizada sólo cuando su licencia lo permita y conservar original/derivación documentados. [CITED: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en]
- El objetivo “máximo número” queda subordinado a revisión legal. Para el plazo, es mejor 20–60 assets aprobados y placeholder coherente en el resto que cobertura visual no defendible. [ASSUMED]

## Security Domain

### Applicable ASVS Categories (Level 1)

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | yes | Django auth, contraseña demo rotatable, sin registro público. [CITED: https://docs.djangoproject.com/en/5.2/topics/auth/default/] |
| V3 Session Management | yes | Cookie `HttpOnly`, `Secure` en producción, `SameSite=Lax`, logout POST y expiración configurada. [ASSUMED] |
| V4 Access Control | yes | Permisos por endpoint/objeto; perfil usa proyección allowlist. [ASSUMED] |
| V5 Input Validation | yes | DRF serializers + ORM constraints; React no es autoridad. [ASSUMED] |
| V6 Cryptography | yes | Django password hashers y TLS de plataforma; no criptografía propia. [CITED: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/] |
| V7 Error/Logging | yes | 4xx genéricos, sin stack/secrets, logs con request ID. [ASSUMED] |
| V8 Data Protection | yes | No copiar campos privados al DTO/HTML/RSC. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`] |
| V9 Communications | yes | HTTPS, host/origin allowlists. [CITED: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/] |
| V12 Files/Resources | limited | Dataset/assets sólo desde manifests revisados, sin upload Phase 1. [ASSUMED] |
| V13 API | yes | Métodos, content type, auth y errores controlados. [ASSUMED] |
| V14 Configuration | yes | `DEBUG=False`, `ALLOWED_HOSTS`, `check --deploy`, secret runtime. [CITED: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/] |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| SQL injection en búsqueda | Tampering/Disclosure | ORM y parámetros; prohibir raw SQL con input. Django advierte sobre raw constructs. [CITED: https://docs.djangoproject.com/en/5.2/internals/security/] |
| CSRF en mutaciones | Tampering | Django CSRF, same-origin, cookies seguras; test de POST sin token. [CITED: https://docs.djangoproject.com/en/5.2/ref/csrf/] |
| XSS desde metadata/alias | Tampering | Renderizar texto, no `dangerouslySetInnerHTML`; fixtures maliciosos de prueba. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`] |
| Exposición de secreto en bundle/image/log | Disclosure | Prohibir secretos en `NEXT_PUBLIC_*`, `ARG`, `render.yaml`; escaneo `git grep` + bundle. [CITED: https://nextjs.org/docs/app/guides/environment-variables; CITED: https://render.com/docs/docker-secrets] |
| IDOR/perfil/copia ajena | Elevation | Querysets por usuario; public serializer distinto; tests usuario A/B. [ASSUMED] |
| Host/open redirect/URL maliciosa | Spoofing/SSRF | Sólo rutas relativas y allowlist de hosts/URLs `https`; no fetch de URL aportada por usuario. [ASSUMED] |
| Credential stuffing demo | Spoofing | Cuenta controlada, contraseña no reutilizada, límite de login razonable y posibilidad de rotación. Rate-limit completo queda Phase 8. [VERIFIED: `.planning/REQUIREMENTS.md`; ASSUMED] |

### Secret acceptance gate

- `.env`, secrets y dumps excluidos en `.gitignore` y `.dockerignore`; Docker advierte que sin `.dockerignore` el contexto puede incluir `.env`. [CITED: https://docs.docker.com/compose/gettingstarted/]
- `render.yaml` contiene `sync: false` o `generateValue: true`, nunca valores. [CITED: https://render.com/docs/blueprint-spec]
- Ningún nombre de secreto usa prefijo `NEXT_PUBLIC_`; Next lo inlinea en JavaScript cliente durante build. [CITED: https://nextjs.org/docs/app/guides/environment-variables]
- Ejecutar `python manage.py check --deploy`, buscar patrones de secretos en Git y escanear `.next/static`/source maps antes de publicar. [CITED: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/; ASSUMED]

## Common Pitfalls

### Pitfall 1: el dataset “legal” y las carátulas se confunden
**What goes wrong:** CC0 de Wikidata se atribuye erróneamente a archivos visuales. **Why:** metadata y media viven en regímenes distintos. **Avoid:** manifests separados; revisión por archivo. **Warning:** asset sin autor/licencia/URL. [CITED: https://www.wikidata.org/wiki/Wikidata:Licensing; CITED: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en]

### Pitfall 2: la demo depende de una API
**What goes wrong:** catálogo vacío por cuota/red/token. **Why:** importación o SSR consulta proveedor. **Avoid:** snapshot y assets locales, test con red externa deshabilitada. **Warning:** llamadas a dominios externos en el recorrido E2E. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`]

### Pitfall 3: autenticación funciona local pero no desplegada
**What goes wrong:** cookies/CSRF/host/origin difieren entre dos dominios. **Why:** CORS y proxy diseñados tarde. **Avoid:** misma origin visible y rewrite a API; fijar `CSRF_TRUSTED_ORIGINS`, proxy headers y secure cookies; smoke real. [ASSUMED]

### Pitfall 4: seed no determinista
**What goes wrong:** credenciales, popularidad y screenshots cambian. **Why:** timestamps/random global o re-seed destructivo. **Avoid:** seed explícita, IDs estables, reloj/fecha de corte, comando idempotente y digest. **Warning:** ejecutar seed dos veces cambia recuentos. [ASSUMED]

### Pitfall 5: UI bonita pero recorrido incompleto
**What goes wrong:** muchas pantallas sin mutaciones persistentes. **Why:** trabajo horizontal. **Avoid:** primer E2E mínimo atraviesa base real antes de estilizado. **Warning:** mocks de frontend tras Wave 1. [ASSUMED]

### Pitfall 6: alcance de accesibilidad imposible al final
**What goes wrong:** rating estrellas, menú y modal no funcionan con teclado/zoom. **Why:** semántica añadida al final. **Avoid:** controles nativos/ARIA correctos, focus y estados desde componentes base; ejecutar checks por ola. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`]

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Backend | `pytest 9.1.1` + `pytest-django`, PostgreSQL real [VERIFIED: `AGENTS.md`] |
| Frontend | `Vitest 5.0.x` + Testing Library [VERIFIED: `AGENTS.md`] |
| Browser | `Playwright 1.62.x` + axe-core [VERIFIED: `AGENTS.md`] |
| Config files | none — Wave 0 (greenfield) [VERIFIED: repository scan] |
| Quick run | `docker compose run --rm api pytest -q -x` and `pnpm --dir apps/web test --run` [ASSUMED] |
| Full suite | `docker compose up -d --build && pnpm --dir apps/web exec playwright test` [ASSUMED] |

### Phase Requirements → Test Map

| Req ID(s) | Behavior | Type | Automated Command | Exists? |
|---|---|---|---|---|
| AUTH-01 | login, redirect catalogue, logout, CSRF rejection | API/E2E | `pytest apps/api/accounts/tests -q` | ❌ Wave 0 |
| PROF-02, INV-05 | public projection works and contains no forbidden fields | API/E2E | `pytest apps/api/accounts/tests/test_public_profile.py -q` | ❌ Wave 0 |
| CAT-01, CAT-06 | exact/accent/alias/typo search offline | integration | `pytest apps/api/catalogue/tests/test_search.py -q` | ❌ Wave 0 |
| CAT-03, CAT-04 | detail hierarchy and provenance, stable IDs | integration | `pytest apps/api/catalogue/tests/test_detail.py -q` | ❌ Wave 0 |
| LIB-01, LIB-02 | status/history and half-star exactness | unit/API | `pytest apps/api/library/tests/test_entry.py -q` | ❌ Wave 0 |
| INV-01, INV-02 | two copies and edition/release constraints | API | `pytest apps/api/library/tests/test_copies.py -q` | ❌ Wave 0 |
| DATA-01, DATA-02 | manifest fields/hash/import idempotence | unit/integration | `pytest apps/api/catalogue/tests/test_import.py -q` | ❌ Wave 0 |
| REC-02 | deterministic score/order and label metadata | unit/API | `pytest apps/api/library/tests/test_popularity.py -q` | ❌ Wave 0 |
| SEC-02 | no secret patterns in repo/bundle/image config | CI/static | `scripts/check-secrets.ps1` | ❌ Wave 0 |
| OPS-01 | deployed health + smoke journey | smoke | `playwright test e2e/deployed-smoke.spec.ts` | ❌ Wave 0 |
| OPS-02, OPS-03 | clean Compose boot/seed without provider | integration | `docker compose up --build --wait` | ❌ Wave 0 |
| QUAL-03 | two locales/viewports, axe and keyboard flow | E2E/manual | `playwright test e2e/demo-journey.spec.ts e2e/a11y.spec.ts` | ❌ Wave 0 |
| DOC-01 | ADR template/required fields present | static | `scripts/check-evidence.ps1` | ❌ Wave 0 |
| AGENT-01..03 | typed, linked evidence entries and no secrets | static | `scripts/check-evidence.ps1` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** test del módulo cambiado (<30 s cuando sea posible).
- **Per wave merge:** backend + frontend unitarios y un Chromium E2E.
- **Phase gate:** suite completa, import desde cero, Compose limpio, deployed smoke, UI-SPEC manual checklist y evidencia archivada.

### Wave 0 Gaps

- [ ] Configurar `pytest.ini`/`pyproject.toml`, `conftest.py` y DB PostgreSQL de test.
- [ ] Configurar Vitest/Testing Library y tests de paridad ES/EN/copy contract.
- [ ] Configurar Playwright, proyecto local y `BASE_URL` desplegada.
- [ ] Crear fixtures maliciosos para XSS/URL, dos usuarios para IDOR y dataset hash incorrecto.
- [ ] Crear un único `demo-journey.spec.ts` tracer-first antes de dividir páginas.
- [ ] Crear checklist manual versionado para teclado, 320px/400% zoom y lector de pantalla básico.

## Deployment and Reproducibility

El plan debe usar imágenes multi-stage y Compose con `web`, `api`, `db`; healthchecks y `depends_on: condition: service_healthy` eliminan carreras de arranque. [CITED: https://docs.docker.com/compose/gettingstarted/] El mismo commit y lockfiles construye local y Render; no instalar dependencias ni bajar dataset al arrancar. [ASSUMED]

Render Blueprint soporta servicios Docker, PostgreSQL, migración predeploy, seed inicial y health checks. [CITED: https://render.com/docs/blueprint-spec] No incluir credenciales en Blueprint; usar `sync:false`, referencias `fromDatabase` y secreto generado. [CITED: https://render.com/docs/blueprint-spec] Coste, disponibilidad del plan y comportamiento de suspensión deben confirmarse inmediatamente antes de crear recursos, porque son condiciones comerciales mutables. [ASSUMED]

El runbook mínimo debe demostrar: `copy .env.example .env`, introducir sólo valores locales no públicos, `docker compose up --build --wait`, `docker compose exec api python manage.py migrate`, `... seed_demo --manifest ...`, URLs y credenciales demo; además, checksum esperado y salida de health. [ASSUMED]

## Thesis and Agent Evidence

Crear desde Wave 0 un ledger append-only legible por máquina, por ejemplo JSONL/Markdown generado, con: timestamp UTC, actor (`human` o agent role), modelo/runtime/version si está disponible, objetivo, input artifacts, output artifacts y hashes, clasificación (`proposal`, `automated-check`, `author-decision`), decisión humana, herramientas/comandos, resultado y limitaciones. No copiar conversación completa ni secretos por defecto. [ASSUMED]

ADRs mínimos de esta fase: `ADR-001 modular monolith + Next frontend`, `ADR-002 PostgreSQL canonical path`, `ADR-003 Wikidata snapshot + per-asset licensing`, `ADR-004 session auth/same-origin boundary`, `ADR-005 Render + Compose parity`. Cada ADR registra contexto, alternativas, decisión, consecuencias, evidencia y autor/aprobación. [ASSUMED]

Conservar prompts/protocolos relevantes como referencias/versiones y hashes cuando su redistribución sea permitida; distinguir claramente texto propuesto por agente, verificación automatizada y aceptación/modificación del autor. [VERIFIED: `.planning/REQUIREMENTS.md`] Para una tesis defendible, capturar también fallos (package seam sin red, decisiones descartadas y correcciones), no sólo resultados exitosos. [ASSUMED]

## Deliberate Deferrals

- No API de enriquecimiento ni comparación de proveedores (DATA-04+ en Phase 4). [VERIFIED: `.planning/REQUIREMENTS.md`]
- No usuarios sintéticos de evaluación; Phase 1 sólo incluye 2–4 cuentas/fixtures demo deterministas, mientras AUTH-02/EVAL-09 son Phase 2. [VERIFIED: `.planning/REQUIREMENTS.md`]
- No contenido/colaborativo/híbrido ni explicaciones; sólo popularidad declarada como baseline. [VERIFIED: `.planning/REQUIREMENTS.md`]
- No comentarios, listas, import/export ni inventario rico. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`]
- No pipeline completo de SAST/dependency/secret scanning ni hardening L1 exhaustivo; sí gate específico SEC-02 y controles necesarios para publicar. [VERIFIED: `.planning/REQUIREMENTS.md`]
- No admin UI, backups/restore, observabilidad avanzada o research dashboard. [VERIFIED: `.planning/REQUIREMENTS.md`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---:|---|---|
| Node.js | Next build/runtime | ✓ | 24.13.0 | Docker Node 24 pinned [VERIFIED: environment probe] |
| npm | bootstrap/Corepack | ✓, PowerShell wrapper blocked | bundled with Node; `npm.ps1` blocked | use `npm.cmd` or Docker [VERIFIED: environment probe] |
| pnpm | frontend lock/install | ✗ | — | Corepack inside Docker after package legitimacy checkpoint [VERIFIED: environment probe] |
| Python | scripts | ✓, wrong target | 3.14.2 vs target 3.13 | Docker Python 3.13 [VERIFIED: environment probe; VERIFIED: `AGENTS.md`] |
| uv | Python locking | ✗ | — | install only after verification, or pip inside Docker for skeleton then add lock before gate [VERIFIED: environment probe; ASSUMED] |
| Docker | reproducible runtime | ✓ | 29.2.1 | — [VERIFIED: environment probe] |
| PostgreSQL CLI/server | DB | ✗ host | — | container `postgres:18` [VERIFIED: environment probe; ASSUMED] |
| Git | evidence/versioning | ✓ | 2.42.0.windows.2 | — [VERIFIED: environment probe] |

**Missing dependencies with no fallback:** none observadas.

**Missing dependencies with fallback:** pnpm, uv, Python 3.13 y PostgreSQL host se encapsulan en Docker; probar que Docker Desktop esté corriendo antes de ejecutar planes. [ASSUMED]

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| Live API as dataset | Immutable snapshot + provenance manifest | Separates UI enrichment from reproducible evidence. [VERIFIED: `AGENTS.md`] |
| Secret baked in frontend/build args | runtime server env/secret file | Next public variables and Docker args can expose values. [CITED: https://nextjs.org/docs/app/guides/environment-variables; CITED: https://render.com/docs/docker-secrets] |
| Flat game-platform string | work → release/platform/edition → copy | Preserves identity and multiple ownership. [VERIFIED: `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`] |
| Mock-only demo | tracer E2E over PostgreSQL from Wave 0 | Makes the visible slice evidence-backed. [ASSUMED] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Same-origin proxy/rewrite is the fastest safe browser boundary for two services. | Architecture/Pitfalls | Auth cookies may require alternative deployment topology. |
| A2 | Proposed table/field names and constraints fit future phases. | Architecture | Migration cost; planner should treat names as provisional but preserve relations. |
| A3 | `pg_trgm` threshold/ranking can meet D-12 for 100–300 curated games. | Search | Needs fixture-based tuning; fallback is app-side ranking only for candidate set. |
| A4 | Proposed popularity formula is academically sufficient for Phase 1. | Popularity | Must be approved/versioned; weights may change before Phase 5 protocol. |
| A5 | Render remains affordable/available for the student's account/region. | Deployment | Must be checked before creating resources; swap Blueprint target if not. |
| A6 | 20–60 Commons assets can be reviewed inside deadline. | Covers | Use placeholder for every unreviewed asset; no release block on count. |
| A7 | CLI paths/commands shown match the eventual scaffold. | Validation/Runbook | Planner/executor must update commands after files exist. |

## Open Questions (RESOLVED INTO BLOCKING GATES)

Estas preguntas dejan de ser decisiones abiertas del executor: cada una tiene un gate, resultado cerrado y contingencia definidos en los planes. Ningún gate admite continuación parcial.

1. **¿Está disponible Render y su PostgreSQL en condiciones adecuadas para esta cuenta/región?**
   - What we know: la especificación soporta la topología requerida. [CITED: https://render.com/docs/blueprint-spec]
   - What's unclear: precio/cuotas/suspensión vigentes y autorización para crear recursos.
   - Recommendation: checkpoint de despliegue al principio del Día 1; si falla, elegir PaaS equivalente sin cambiar el contrato Docker/Compose.
   - **Closed outcome:** 01-12 Task 2 exige decisión humana `Render | PaaS Docker equivalente`, autorización previa a crear recursos, URL HTTPS/host/commit y smoke verde. Si coste/región/suspensión no se aceptan o el smoke falla, estado BLOCKED y rollback; 01-14 no comienza.
2. **¿Qué 100–300 QIDs y qué assets pasan revisión?**
   - What we know: datos estructurados Wikidata CC0; licencias de Commons son por archivo. [CITED: https://www.wikidata.org/wiki/Wikidata:Licensing]
   - What's unclear: cobertura final de títulos ES/EN, releases y media.
   - Recommendation: congelar allowlist y manifest en Wave 1; placeholder por defecto.
   - **Closed outcome:** 01-05 Task 1 genera el candidato sin tocar PostgreSQL y Task 2 bloquea antes de 01-06/import hasta que `catalogue-freeze.md` tenga APPROVED, 100–300 QIDs representativos, checksums y decisión resuelta por asset; cualquier media no verificada usa placeholder propio.
3. **¿Puede resolverse exactamente el lock recomendado en Linux/Python 3.13?**
   - What we know: no hubo acceso de registro desde esta sesión y el seam marcó SUS por falta de metadatos. [VERIFIED: package audit command]
   - Recommendation: checkpoint humano y resolución limpia dentro de Docker antes de implementar.
   - **Closed outcome:** 01-01 Task 1 bloquea toda instalación hasta verificar registro/mantenedor/proyecto/versiones y resolver locks en las imágenes fijadas. Cualquier paquete discrepante queda BLOCKED, no se sustituye silenciosamente.

## Project Constraints (from AGENTS.md)

- Mantener reproducibles experimentos, datos sintéticos, configuración y resultados. [VERIFIED: `AGENTS.md`]
- Respetar licencia/términos y trazar cada fuente. [VERIFIED: `AGENTS.md`]
- Entregar aplicación desplegada y entorno local documentado. [VERIFIED: `AGENTS.md`]
- Mantener audiencia inicial controlada con cuentas sintéticas/demo. [VERIFIED: `AGENTS.md`]
- Hacer recorridos responsive y accesibles. [VERIFIED: `AGENTS.md`]
- Justificar arquitectura/tecnologías con evidencia. [VERIFIED: `AGENTS.md`]
- Usar Python 3.13, Django 5.2 LTS/DRF, PostgreSQL, Next.js/React/TypeScript/Tailwind según la investigación registrada, con lockfiles e imágenes fijadas. [VERIFIED: `AGENTS.md`]
- No microservicios/Kafka/Kubernetes, MongoDB primario, vector DB, entrenamiento en request, SQLite de producción/integración, API live durante evaluación ni dependencias `latest`. [VERIFIED: `AGENTS.md`]
- Usar PostgreSQL también en integración, no SQLite. [VERIFIED: `AGENTS.md`]
- Servir secretos en servidor y documentar toda decisión/uso de agentes. [VERIFIED: `AGENTS.md`]
- No hay convenciones/código existentes que reutilizar; el repositorio es greenfield. [VERIFIED: repository scan; VERIFIED: `AGENTS.md`]

## Sources

### Primary (HIGH confidence)

- https://www.wikidata.org/wiki/Wikidata:Licensing — licencia CC0 de datos estructurados.
- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en — reutilización y obligaciones por archivo.
- https://commons.wikimedia.org/wiki/Commons:Simple_media_reuse_guide — distinguir Commons de imágenes no libres/fair use.
- https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual — formatos, límites, 429 y User-Agent.
- https://docs.djangoproject.com/en/5.2/topics/auth/default/ — autenticación/sesión.
- https://docs.djangoproject.com/en/5.2/ref/csrf/ — protección CSRF.
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ — gate de despliegue seguro.
- https://docs.djangoproject.com/en/5.2/internals/security/ — límites y riesgos de SQL raw.
- https://www.postgresql.org/docs/current/pgtrgm.html — búsqueda por similitud/indexación.
- https://nextjs.org/docs/app/guides/environment-variables — variables privadas y `NEXT_PUBLIC_`.
- https://nextjs.org/docs/app/guides/data-security — frontera server/client y filtrado DAL.
- https://docs.docker.com/compose/gettingstarted/ — healthchecks, volúmenes y exclusión de `.env`.
- https://render.com/docs/blueprint-spec — infraestructura, DB, health, predeploy y secretos.
- https://render.com/docs/docker-secrets — riesgos de secretos en build/image.

### In-repo authoritative context (HIGH confidence)

- `AGENTS.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md`
- `.planning/phases/01-three-day-public-demo-slice/01-UI-SPEC.md`
- `.planning/STATE.md`

### Tertiary (LOW confidence)

- Ninguna fuente comunitaria se usó como base normativa; todas las propuestas sin fuente primaria se marcan `[ASSUMED]`.

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM-HIGH — está registrado con fuentes oficiales, pero el lock/legitimacy probe no pudo acceder a registros.
- Architecture: MEDIUM — deriva de decisiones cerradas y patrones oficiales; nombres y topología same-origin requieren implementación.
- Data legality: HIGH para Wikidata CC0 y política Commons; MEDIUM para la selección/manifest concreto hasta revisión.
- Security: MEDIUM-HIGH — controles de framework/plataforma citados; Phase 1 no pretende completar todo el hardening de Phase 8.
- Validation: MEDIUM — arquitectura definida, pero infraestructura aún no existe.

**Research date:** 2026-09-04
**Valid until:** 2026-10-04 para stack estable; verificar términos/plans de hosting y licencias de cada asset en cada release.
