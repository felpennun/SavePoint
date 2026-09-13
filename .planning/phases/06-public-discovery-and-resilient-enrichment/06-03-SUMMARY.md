---
phase: 06-public-discovery-and-resilient-enrichment
plan: 03
subsystem: api
tags: [django, privacy, social, profiles, collections, lists, authorization]

# Dependency graph
requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: "Relaciones sociales persistentes y contrato de catálogo local"
provides:
  - "Policy server-side owner/accepted_friend/basic/hidden"
  - "Perfiles básicos y proyecciones protegidas con allowlists explícitas"
  - "URLs owner+slug para listas públicas y 404 genérico ante acceso no autorizado"
affects: [06-04, 06-06, 06-09, social-visibility]

# Actuals
actuals:
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "La policy se evalúa antes del queryset y deriva el actor de request.user"
    - "Los DTOs compartidos usan allowlists manuales y no exponen IDs internos ni metadatos de inventario"
    - "El locator owner+slug y el 404 genérico evitan enumeración y bypass por URL directa"

key-files:
  created:
    - apps/api/social/policies.py
    - apps/api/library/migrations/0006_phase6_public_list_slug.py
    - apps/api/tests/test_public_profile.py
  modified:
    - apps/api/accounts/serializers.py
    - apps/api/accounts/views.py
    - apps/api/library/models.py
    - apps/api/library/serializers.py
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - apps/api/tests/test_social_visibility.py
    - ideas-vault/Fases/Fase 6 - Descubrimiento publico.md

key-decisions:
  - "El perfil básico para no-amigos contiene únicamente alias, avatar, biografía y acción contextual; colección, listas y comentarios requieren propietario o amistad aceptada."
  - "Las listas usan alias del propietario más public_slug estable y único por propietario; el acceso directo no revela si el recurso existe."
  - "La proyección compartida conserva juego, portada, año, plataforma, estado de backlog, valoración personal y orden manual, excluyendo copias, compras, precios, tiendas, ubicaciones, notas e IDs internos."

requirements-completed: [PROF-03, PROF-04, SOCIAL-04]

coverage:
  - id: D1
    description: "La matriz de visibilidad distingue owner, accepted friend, non-friend, anonymous y blocked."
    requirement: PROF-03
    verification:
      - kind: integration
        ref: "apps/api/tests/test_public_profile.py -k basic or owner or friend or anonymous or blocked — 4 passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "El slug owner+slug, el backfill y la proyección de listas son aditivos, estables y allowlisted."
    requirement: PROF-04
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_visibility.py -k slug or list_projection — 2 passed"
        status: pass
      - kind: other
        ref: "docker compose ... manage.py makemigrations --check --dry-run — No changes detected"
        status: pass
    human_judgment: false
  - id: D3
    description: "Las rutas de colección/lista aplican autorización antes del queryset y preservan el orden manual."
    requirement: SOCIAL-04
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_visibility.py -k collection or list or direct_url or idor or allowlist — 8 passed"
        status: pass
    human_judgment: false

# Metrics
duration: 1h+
completed: 2026-09-13
status: complete
---

# Phase 06 Plan 03: Protected public projections Summary

La frontera de privacidad de perfiles, colecciones y listas queda implementada en API y sincronizada con el vault. Las verificaciones declaradas pasaron tras limpiar exclusivamente la base temporal de tests que había quedado ocupada por ejecuciones concurrentes.

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `00df843`, `23e3390` | Policy y tracer de visibilidad de perfil |
| 2 | `12c4216`, `84a737c` | Slug owner+slug y contrato de proyección |
| 3 | `f4d12fc` | Rutas protegidas de colección, listas y comentarios |

## Deviations

- El primer intento de pytest no pudo crear la base `test_savepoint_test` porque estaba ocupada; `--reuse-db` encontró permisos duplicados. Se eliminó únicamente esa base temporal y la repetición limpia pasó.

## Self-Check: PASSED

- `makemigrations --check --dry-run`: pasó.
- Perfil/proyección: `4 passed`.
- Slug/list projection: `2 passed`.
- Colección/lista/URL directa/IDOR/allowlist: `8 passed`.
