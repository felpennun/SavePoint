---
phase: 06-public-discovery-and-resilient-enrichment
plan: 06
subsystem: ui
tags: [nextjs, react, typescript, social, profiles, ssr, accessibility]

requires:
  - phase: 06-03
    provides: Backend social relationships, privacy policy and allowlisted protected projections
  - phase: 06-05
    provides: Public discovery UI patterns and authenticated AppShell conventions
provides:
  - Protected SSR profile and list projections with basic non-friend fallback
  - Accessible SocialActions and three-section SocialHub backed by the existing social API
  - Authenticated friends route, explicit middleware protection and profile navigation
affects: [06-07, 06-08, 06-09, public profiles, social UX]

actuals:
  tokens: 15199
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns: [SSR cookie forwarding, backend-authoritative privacy projection, row-scoped mutation state, focus-managed confirmation dialogs]

key-files:
  created:
    - apps/web/components/SocialActions.tsx
    - apps/web/components/SocialHub.tsx
    - apps/web/app/[locale]/friends/page.tsx
    - apps/web/app/[locale]/profiles/[alias]/lists/[listSlug]/page.tsx
    - apps/web/tests/social-friends.test.ts
  modified:
    - apps/web/lib/api.ts
    - apps/web/app/[locale]/profiles/[alias]/page.tsx
    - apps/web/components/AppShell.tsx
    - apps/web/middleware.ts
    - apps/web/tests/social-profile.test.ts

key-decisions:
  - "El adaptador SSR normaliza la respuesta del backend con kind basic/protected; la UI no infiere permisos a partir de campos vacíos."
  - "Las colecciones y listas siguen siendo rutas protegidas por el backend y convierten un 404 en notFound(), sin filtrar diferencias de autorización."
  - "Las mutaciones sociales conservan rutas distintas para aceptar, rechazar, eliminar, bloquear y desbloquear, con CSRF, estado busy por fila y diálogos accesibles."
  - "El hub usa búsqueda de alias exacta, sin autocomplete ni sugerencias, y mantiene la respuesta del servidor como autoridad tras cada acción."

patterns-established:
  - "Las páginas SSR construyen el Cookie header desde cookies() antes de consultar proyecciones protegidas."
  - "Las acciones destructivas usan confirmación con role=dialog, Escape, retorno de foco y aria-live para el resultado."

requirements-completed: [PROF-03, PROF-04, SOCIAL-03, SOCIAL-04]

coverage:
  - id: D1
    description: "Perfil SSR basic/protected y lista compartida con allowlist y 404 genérico"
    requirement: PROF-03
    verification:
      - kind: unit
        ref: "apps/web/tests/social-profile.test.ts (4 tests)"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Hub de amistades con solicitudes recibidas/enviadas, amistades y búsqueda exacta"
    requirement: SOCIAL-03
    verification:
      - kind: unit
        ref: "apps/web/tests/social-friends.test.ts (6 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Acciones sociales separadas para aceptar, rechazar, eliminar, bloquear y desbloquear"
    requirement: SOCIAL-04
    verification:
      - kind: unit
        ref: "apps/web/tests/social-friends.test.ts (relationship and endpoint contract)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Navegación autenticada de amistades y navegación de perfil con estados accesibles"
    requirement: PROF-04
    verification:
      - kind: unit
        ref: "apps/web/tests/social-profile.test.ts (navigation/landmark contract)"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit"
        status: pass
    human_judgment: true
    rationale: "La comprobación browser-level de foco, Escape y responsive requiere Chromium, ausente en la imagen web actual."

duration: 45min
completed: 2026-09-13
status: complete
---

# Phase 6 Plan 6: Public discovery and resilient enrichment Summary

**Perfiles SSR protegidos y hub de amistades accesible conectado al backend social existente.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-13T20:20:00+02:00
- **Completed:** 2026-09-13T21:04:46+02:00
- **Tasks:** 2
- **Files modified:** 12 del write-set, más documentación de ejecución y vault

## Accomplishments

- Se implementaron perfiles y listas SSR con proyección básica para no-amigos, proyección protegida para propietario/amistad aceptada y `notFound()` para rutas no autorizadas.
- Se añadió `SocialActions` con acciones separadas, CSRF, errores reintentables, busy por fila, confirmación y gestión de foco accesible.
- Se conectó `SocialHub` desde `/friends`, con búsqueda exacta, tres secciones y actualización local solo después de respuestas API satisfactorias; middleware protege la ruta.

## Task Commits

Cada tarea se comprometió atómicamente:

1. **Task 1: Protected profile and list SSR tracer** - `a8a8278` (RED), `a35e884` (GREEN)
2. **Task 2: Social actions and friends hub** - `a487a0f` (RED), `40563dc` (GREEN)

**Plan metadata:** commit documental final con `Refs #56` y `Closes #56`.

## Files Created/Modified

- `apps/web/lib/api.ts` - DTOs, normalización y fetchers SSR de perfiles, listas, colección y datos sociales.
- `apps/web/app/[locale]/profiles/[alias]/page.tsx` - Perfil público SSR con ramas basic/protected y navegación accesible.
- `apps/web/app/[locale]/profiles/[alias]/lists/[listSlug]/page.tsx` - Lista protegida SSR allowlisted.
- `apps/web/components/SocialActions.tsx` - Acciones por relación y diálogos de confirmación accesibles.
- `apps/web/components/SocialHub.tsx` - Búsqueda exacta y solicitudes/amistades.
- `apps/web/app/[locale]/friends/page.tsx` - Entrada autenticada al hub social.
- `apps/web/components/AppShell.tsx`, `apps/web/middleware.ts` - Navegación y protección de `/friends`.
- `apps/web/tests/social-profile.test.ts`, `apps/web/tests/social-friends.test.ts` - Contratos focalizados.

## Decisions Made

Se mantuvo el backend como autoridad de privacidad y relaciones. El frontend solo presenta la proyección recibida, usa un adaptador explícito `kind` para distinguir basic/protected y evita endpoints alternativos o inferencias por ausencia de datos. No se añadieron dependencias nuevas.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Adapted verification to the project container**

- **Found during:** verificación de Task 1/2
- **Issue:** `pnpm` no está disponible en el host de ejecución.
- **Fix:** Se ejecutaron los comandos declarados mediante `docker compose ... run --rm web`, que contiene las dependencias bloqueadas del frontend.
- **Verification:** 10 tests focalizados y TypeScript pasan.
- **Committed in:** `40563dc` (implementación de Task 2)

**2. [Rule 1 - Bug] Corrected the TDD test/runtime contract**

- **Found during:** Task 2 GREEN
- **Issue:** El test de acciones necesitaba un archivo `.ts` compatible con el parser configurado y las acciones debían conservar el alias exacto tras editar la búsqueda.
- **Fix:** Se usó `createElement` en el test, se cubrieron las cinco rutas de mutación y la edición del alias reinicia el resultado previo.
- **Verification:** `social-friends.test.ts` pasa con 6 tests.
- **Committed in:** `40563dc`

---

**Total deviations:** 2 auto-fixed (1 Rule 3, 1 Rule 1).
**Impact on plan:** Sin cambio arquitectónico ni dependencias nuevas; todas las verificaciones automatizadas declaradas pasan.

## Issues Encountered

La validación interactiva de Chromium no pudo ejecutarse porque el binario no está instalado en la imagen web. La limitación está documentada en `deferred-items.md` y en `.planning/WINDOWS.md`; no bloqueó las pruebas focalizadas ni TypeScript.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

El write-set Next.js está listo para integración con las siguientes mejoras de contenido social. La comprobación browser-level de foco, Escape y responsive debe repetirse cuando la imagen web incluya Chromium.

## Self-Check: PASSED

- Los archivos del write-set y este SUMMARY existen.
- Los commits `a8a8278`, `a35e884`, `a487a0f` y `40563dc` existen en el historial.
- Las pruebas focalizadas reportan 10/10 y TypeScript termina con código 0.

---
*Phase: 06-public-discovery-and-resilient-enrichment*
*Completed: 2026-09-13*
