---
phase: 06-public-discovery-and-resilient-enrichment
plan: 01
subsystem: api
tags: [django, drf, postgresql, social, friendships, csrf, pytest]

# Dependency graph
requires:
  - phase: 06-public-discovery-and-resilient-enrichment
    provides: Requisitos sociales reconciliados y decisiones D-03, D-04, D-05.
provides:
  - Núcleo persistente de solicitudes, amistades bidireccionales y bloqueos reversibles.
  - API autenticada de búsqueda exacta por alias y transiciones sociales owner-scoped.
  - Constraints, índices y locks PostgreSQL inspeccionados con pruebas de concurrencia.
affects: [06-02, 06-03, 06-04, 06-06, 06-09, social-projections]

# Actuals (#2632)
actuals:
  tokens: 11422
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pareja canónica estable bloqueada mediante filas de usuario y RelationshipPair.
    - Transiciones sociales explícitas dentro de transaction.atomic() con identidad de sesión.
    - DTOs manuales y respuestas 404 genéricas para recursos sociales ocultos.

key-files:
  created:
    - apps/api/social/__init__.py
    - apps/api/social/apps.py
    - apps/api/social/models.py
    - apps/api/social/migrations/0001_initial.py
    - apps/api/social/migrations/__init__.py
    - apps/api/social/serializers.py
    - apps/api/social/services.py
    - apps/api/social/views.py
    - apps/api/social/urls.py
    - apps/api/tests/test_social.py
    - apps/api/tests/test_social_schema.py
  modified:
    - apps/api/config/settings.py
    - apps/api/config/urls.py

key-decisions:
  - "Se separa el dominio social en una app Django propia y se serializa cada pareja mediante una fila canónica estable."
  - "Las solicitudes rechazadas y bloqueadas se conservan como historial mínimo; solo existe una solicitud pendiente por dirección."
  - "Un bloqueo es un tombstone dirigido y reversible: cancela solicitudes, elimina la amistad y oculta ambos sentidos; desbloquear no restaura la amistad."

patterns-established:
  - "La vista deriva siempre el actor desde request.user; el cliente solo aporta un alias exacto o un locator de solicitud."
  - "Las operaciones que compiten bloquean usuarios en orden estable y después la pareja, evitando estados sociales parciales."

requirements-completed: [SOCIAL-03]

coverage:
  - id: D1
    description: "Búsqueda exacta por alias y flujo solicitud → aceptación → amistad bidireccional."
    requirement: SOCIAL-03
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social.py#test_exact_alias_search_does_not_return_partial_matches"
        status: pass
      - kind: integration
        ref: "apps/api/tests/test_social.py#test_request_and_accept_create_bidirectional_friendship"
        status: pass
    human_judgment: false
  - id: D2
    description: "Rechazo, eliminación, bloqueo, desbloqueo, re-solicitud y carreras concurrentes como transiciones distintas."
    requirement: SOCIAL-03
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Migración PostgreSQL con constraints, índices y registro de migración inspeccionados."
    requirement: SOCIAL-03
    verification:
      - kind: integration
        ref: "apps/api/tests/test_social_schema.py"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run"
        status: pass
    human_judgment: false
---

# Phase 6 Plan 1: Social relationship core summary

**Núcleo social Django con alias exacto, amistad bidireccional, bloqueo reversible y transiciones PostgreSQL atómicas.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-13T13:39:02Z
- **Completed:** 2026-09-13T13:52:45Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Se creó y registró la app `social`, con `RelationshipPair`, `FriendshipRequest`, `Friendship` y `Block`, además de la migración PostgreSQL `0001_initial`.
- Se expusieron búsqueda exacta, solicitudes, aceptación/rechazo, eliminación, bloqueo/desbloqueo y consulta de relación con actor derivado de sesión, CSRF compatible y throttling.
- Se probó el ciclo completo de relaciones, la privacidad bilateral durante el bloqueo, la reapertura tras desbloquear, la protección contra IDOR y la serialización determinista bajo concurrencia.

## Task Commits

Cada tarea quedó cubierta por commits atómicos; las tareas TDD tienen commit RED y commit de implementación o endurecimiento:

1. **Task 1: Tracer alias exacto → solicitud → aceptación → amistad persistida** — `5252281` (test), `4eeb316` (feat)
2. **Task 2: Transiciones separadas de rechazo, eliminación, bloqueo y desbloqueo** — `f86ba2a` (test), `58b115b` (fix)
3. **Task 3: Verificar constraints, índices y regresión del núcleo social** — `3d72424` (test)

## Files Created/Modified

- `apps/api/social/models.py` — estado social, historial mínimo, pareja canónica y constraints.
- `apps/api/social/services.py` — comandos owner-scoped y transacciones con locks deterministas.
- `apps/api/social/views.py` / `apps/api/social/urls.py` — API protegida y rutas de transición.
- `apps/api/social/serializers.py` — allowlists de entrada/salida sin identidades sustituibles.
- `apps/api/social/migrations/0001_initial.py` — esquema aditivo para PostgreSQL.
- `apps/api/tests/test_social.py` — alias, relaciones, privacidad, transiciones e interacción concurrente.
- `apps/api/tests/test_social_schema.py` — inspección de tablas, migración, constraints e índices.
- `apps/api/config/settings.py` / `apps/api/config/urls.py` — registro de app, throttles y prefijo API.

## Decisions Made

- Se usó `RelationshipPair` con `low_user`/`high_user` ordenados para ofrecer una fila estable de lock por pareja y una única amistad actual.
- `unblock` solo desactiva el tombstone creado por el blocker; no reconstituye amistad ni crea solicitudes automáticamente.
- La búsqueda social solo acepta un parámetro `alias` exacto; repeticiones, parámetros extra e identidades en el body se rechazan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Evitada la aceptación de parámetros de búsqueda repetidos**
- **Encontrado durante:** Task 2 (transiciones y validación)
- **Problema:** `QueryDict` podía reducir dos valores `alias` al último y aceptar una consulta no determinista.
- **Corrección:** la vista exige exactamente un parámetro `alias` y ningún parámetro adicional.
- **Ficheros:** `apps/api/social/views.py`
- **Verificación:** test de alias exacto y matriz social completa.
- **Commit:** `58b115b`

**2. [Rule 1 - Bug] Corregida la respuesta de error de payload social inválido**
- **Encontrado durante:** Task 2 (transiciones y validación)
- **Problema:** un `ValidationError` no indexado en el serializer podía producir un 500 al construir `serializer.errors`.
- **Corrección:** el serializer devuelve `non_field_errors` estructurado y la API responde 400.
- **Ficheros:** `apps/api/social/serializers.py`
- **Verificación:** test de rechazo de `sender_id`/`receiver_id` y matriz social completa.
- **Commit:** `58b115b`

**3. [Rule 1 - Blocking test] Cerradas las conexiones de los workers concurrentes**
- **Encontrado durante:** Task 2 (verificación concurrente)
- **Problema:** la prueba dejaba sesiones PostgreSQL abiertas y producía un warning durante teardown.
- **Corrección:** cierre explícito de conexiones por hilo y al finalizar el executor.
- **Ficheros:** `apps/api/tests/test_social.py`
- **Verificación:** prueba concurrente aislada y suite completa sin warnings.
- **Commit:** `58b115b`

### Secuenciación TDD

La implementación de los comandos de Task 2 comparte la misma frontera de servicios y vistas del tracer y quedó incluida en `4eeb316`; Task 2 añadió la cobertura completa y las correcciones de validación en `58b115b`. No se amplió el write-set ni se añadieron dependencias.

**Total desviaciones:** 3 auto-arreglos de corrección/robustez; 0 cambios arquitectónicos.

## Issues Encountered

- PostgreSQL materializa la `UniqueConstraint` condicional de solicitudes pendientes como índice único parcial; la prueba de esquema inspecciona ese índice en `pg_indexes` y las demás constraints en `pg_constraint`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

La app `social` y sus rutas están listas para que los planes posteriores reutilicen `relationship_status`, los querysets de amistad y los tombstones de bloqueo al construir proyecciones de perfil, listas, comentarios y mensajería. No quedan migraciones pendientes ni cambios sin commitear.

## Self-Check: PASSED

El resumen existe y los cinco commits de ejecución (`5252281`, `4eeb316`, `f86ba2a`, `58b115b`, `3d72424`) están presentes en el historial.

---
*Phase: 06-public-discovery-and-resilient-enrichment*
*Completed: 2026-09-13*
