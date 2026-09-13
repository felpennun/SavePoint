---
phase: 06-public-discovery-and-resilient-enrichment
plan: 04
subsystem: api
tags: [django, postgresql, social, recommendations, inbox, privacy, cooldown]
github_issue: 57

# Dependency graph
requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: "Amistades aceptadas, policy social y proyecciones protegidas de 06-03"
provides:
  - "Recomendaciones privadas con receptor único, inbox y estado de lectura"
  - "Cooldown direccional exacto de siete días con 429 y Retry-After fail-closed"
  - "Comentarios de ficha filtrados por amistad aceptada y DTO allowlisted"
affects: [06-06, 06-07, 06-08, 06-09, social-privacy]

# Actuals
actuals:
  tokens: 9059
  tasks: 3
  commits: 6

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "La pareja canónica se bloquea antes de comprobar amistad y cooldown"
    - "El inbox y mark-read filtran siempre por receiver=request.user"
    - "Remove/block convierten el contenido en tombstone mínimo y no restauran mensajes"
    - "Los comentarios autorizados se consultan antes de serializar y usan DTO manual"

key-files:
  created:
    - apps/api/social/migrations/0002_socialmessage.py
    - apps/api/tests/test_social_messages.py
    - .planning/phases/06-public-discovery-and-resilient-enrichment/06-04-SUMMARY.md
  modified:
    - apps/api/social/models.py
    - apps/api/social/serializers.py
    - apps/api/social/services.py
    - apps/api/social/views.py
    - apps/api/social/urls.py
    - apps/api/library/services.py
    - apps/api/library/views.py
    - apps/api/tests/test_social_visibility.py
    - apps/api/tests/test_public_profile.py

key-decisions:
  - "Una recomendación solo se crea entre amistades aceptadas y deriva el emisor de request.user; el alias del receptor es único y no se aceptan IDs de identidad alternativos."
  - "El límite es direccional y usa created_at > now - 7 días: exactamente al cumplir la ventana se permite el siguiente envío."
  - "Los errores de reloj, lock o lectura inciertos se tratan como cooldown conservador y no pueden crear mensajes."
  - "Eliminar o bloquear oculta inmediatamente trabajo y texto, conserva sender/receiver/fecha/razón para auditoría y no restaura contenido al desbloquear."

requirements-completed: [PROF-03, SOCIAL-04, SOCIAL-05]

coverage:
  - id: D1
    description: "Las recomendaciones privadas llegan solo al receptor de una amistad aceptada y el inbox no cruza cuentas."
    requirement: SOCIAL-05
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_messages.py — 6 passed"
        status: pass
  - id: D2
    description: "mark_read/mark_unread y unread-count son receptor-scoped; el cooldown direccional responde 429 con Retry-After y respeta la frontera exacta de siete días."
    requirement: SOCIAL-05
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_messages.py — cooldown, read/unread, badge, tombstone y reloj ingenuo"
        status: pass
  - id: D3
    description: "Los comentarios requieren owner o amistad aceptada, omiten terceros privados/bloqueados y cruzan solo alias, texto y fecha."
    requirement: PROF-03
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_visibility.py -k comment or privacy or hostile or author — 3 passed"
        status: pass
      - kind: integration
        ref: "apps/api/tests/test_public_profile.py — incluido en regresión conjunta"
        status: pass
  - id: D4
    description: "La regresión conjunta de perfil, comentarios y mensajes pasa con PostgreSQL y sin drift de esquema."
    requirement: SOCIAL-04
    verification:
      - kind: other
        ref: "check; migrate --plan; makemigrations --check --dry-run — sin errores, No changes detected"
        status: pass
      - kind: integration
        ref: "apps/api/tests/test_public_profile.py apps/api/tests/test_social_visibility.py apps/api/tests/test_social_messages.py — 23 passed"
        status: pass

# Metrics
duration: 1h+
completed: 2026-09-13
status: complete
---

# Phase 06 Plan 04: Private recommendations and authorized comments Summary

La API implementa el camino amistad aceptada → recomendación privada → inbox del receptor, con lectura/badge, cooldown direccional exacto de siete días, `429` + `Retry-After` fail-closed y ocultación por remove/block. La ficha de juego entrega comentarios de terceros únicamente a owner o amistad aceptada mediante la proyección `author_alias`, `text`, `date`.

## Task Commits

1. **Tracer: amistad → recomendación → inbox privado** — `7accc5c` (RED), `0be4d62` (GREEN).
2. **Comentarios de ficha filtrados por policy** — `22b7867` (RED), `03c28c7` (GREEN).
3. **Regresión conjunta de privacidad, mensajes y esquema** — `f75a754`.
4. **Endurecimiento fail-closed del envío** — `09a0a83`.

Todos los commits parciales incluyen `Refs #57`; el commit documental de cierre incluirá `Closes #57`.

## Accomplishments

- Se añadió `SocialMessage` persistente con juego opcional para tombstone, texto opcional, fecha, lectura y razón de ocultación, además de índices de inbox y cooldown.
- `send_recommendation` bloquea la pareja canónica antes de verificar amistad y ventana temporal; solo acepta un alias de receptor y un `work_id` de catálogo no DLC.
- El inbox, el contador unread y mark-read/mark-unread quedan filtrados por el receptor autenticado; los mensajes ocultos nunca se serializan.
- Remove y block ocultan trabajo/texto inmediatamente, conservan metadatos mínimos y no restauran la relación ni los mensajes al hacer unblock.
- `list_visible_comments` aplica owner/accepted-friend antes del queryset, excluye bloqueados y anónimos y mantiene el CRUD privado del autor.
- La suite conjunta verifica PostgreSQL, `migrate --plan`, ausencia de drift de migraciones, aislamiento, allowlists, XSS como texto plano y regresiones de perfil.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Añadir persistencia de mensajes omitida del write-set.**

- **Encontrado durante:** Task 1, al preparar el tracer RED.
- **Problema:** el plan referenciaba `SocialMessage`, pero el write-set no incluía el modelo/migración y el repositorio no podía persistir `read_at`, cooldown ni tombstones.
- **Corrección:** se completó el modelo/migración estrictamente necesarios en `apps/api/social/models.py` y `apps/api/social/migrations/0002_socialmessage.py`, sin tocar frontend ni dependencias.
- **Verificación:** `migrate --plan`, `makemigrations --check --dry-run` y suite conjunta PostgreSQL pasan.
- **Commit:** `0be4d62`.

**2. [Rule 1 - Bug] Restaurar el import de policy usado por colecciones/listas.**

- **Encontrado durante:** Task 3, regresión conjunta.
- **Problema:** al mover la autorización de comentarios al servicio se eliminó accidentalmente el import de `resolve_profile_access`, provocando `NameError` en rutas protegidas existentes.
- **Corrección:** se restauró el import sin cambiar la semántica de esas rutas.
- **Verificación:** regresión conjunta `23 passed`.
- **Commit:** `f75a754`.

**3. [Rule 2 - Security/correctness] Ampliar el cierre conservador ante incertidumbre.**

- **Encontrado durante:** revisión del tracer.
- **Problema:** una excepción del reloj o de la resolución/lectura del destinatario podía escapar como error no gobernado.
- **Corrección:** esas condiciones se convierten en `RecommendationCooldown` conservador antes de cualquier creación.
- **Verificación:** prueba de reloj ingenuo y gate focalizado `6 passed`.
- **Commit:** `09a0a83`.

## Verification

- `docker compose -f infra/compose.yaml run --rm api pytest --create-db apps/api/tests/test_social_messages.py -q` — 6 passed.
- `docker compose -f infra/compose.yaml run --rm api pytest --reuse-db apps/api/tests/test_social_visibility.py -k "comment or privacy or hostile or author" -q` — 3 passed.
- `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check` — sin problemas.
- `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run` — No changes detected.
- Regresión conjunta de los tres módulos — 23 passed.

## Deferred Issues

No se dejan pruebas omitidas, stubs ni verificaciones sin ejecutar en este plan.

## Self-Check: PASSED

- `06-04-SUMMARY.md` existe en la ruta canónica.
- Existen los commits `7accc5c`, `0be4d62`, `22b7867`, `03c28c7`, `f75a754` y `09a0a83`.
- `verify-summary` confirmó los artefactos creados y la validez del resumen.
