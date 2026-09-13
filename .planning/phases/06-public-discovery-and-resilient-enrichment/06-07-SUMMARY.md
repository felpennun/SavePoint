---
phase: 06-public-discovery-and-resilient-enrichment
plan: 07
subsystem: ui
tags: [nextjs, react, typescript, social, inbox, ssr, csrf, accessibility]

# Dependency graph
requires:
  - phase: 06-04
    provides: "API de recomendaciones privadas, inbox receptor-scoped, mark_read, contador y cooldown 429/Retry-After"
  - phase: 06-06
    provides: "Patrones SSR sociales, AccountSwitcher y navegación autenticada accesible"
provides:
  - "Bandeja privada de mensajes de amigos con DTO allowlisted y lectura receptor-scoped"
  - "Formulario de recomendación con estado conservado y cooldown gobernado por el backend"
  - "Entrada /messages y badge textual accesible en el menú de cuenta"
affects: [06-08, 06-09, SOCIAL-05]

# Actuals (#2632)
actuals:
  tokens: 7138
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Los fetchers SSR reenvían Cookie y fuerzan no-store; las mutaciones cliente usan apiFetch y CSRF"
    - "La respuesta social se normaliza mediante allowlist antes de llegar a React"
    - "El badge se sincroniza con el aggregate autenticado y no con el estado local de otra cuenta"

key-files:
  created:
    - apps/web/components/SocialInbox.tsx
    - apps/web/app/[locale]/messages/page.tsx
    - apps/web/tests/social-messages.test.ts
  modified:
    - apps/web/lib/api.ts
    - apps/web/lib/client-api.ts
    - apps/web/components/AccountSwitcher.tsx
    - apps/web/components/AppShell.tsx

key-decisions:
  - "El cliente conserva juego, amistad y texto ante cualquier fallo de envío; solo muestra el cooldown y Retry-After que devuelve el API."
  - "El contador del menú se vuelve a consultar tras mark_read y solo el aggregate receptor-scoped puede retirar el estado pendiente."
  - "Los identificadores necesarios para mutar permanecen en el contrato interno del cliente, pero no se presentan como texto ni data-* en la tarjeta del mensaje."

requirements-completed: [SOCIAL-05]

coverage:
  - id: D1
    description: "Inbox privado SSR/client con DTO allowlisted, enlace al juego, portada, texto opcional y mark_read"
    requirement: SOCIAL-05
    verification:
      - kind: unit
        ref: "apps/web/tests/social-messages.test.ts — inbox DTO, endpoint read y render seguro"
        status: pass
      - kind: other
        ref: "docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Formulario de recomendación y AccountSwitcher con ruta privada, estado textual y punto rojo de pendientes"
    requirement: SOCIAL-05
    verification:
      - kind: unit
        ref: "apps/web/tests/social-messages.test.ts — labels, ruta /messages y Retry-After"
        status: pass
    human_judgment: true
    rationale: "La comprobación browser-level de foco, Escape y responsive requiere Chromium, ausente en la imagen web; el contrato unitario y TypeScript sí pasan."

# Metrics
duration: 12min
completed: 2026-09-13
status: complete
---

# Phase 06 Plan 07: Public discovery and resilient enrichment Summary

**Bandeja privada de recomendaciones entre amistades con lectura CSRF, cooldown autoritativo y badge accesible de pendientes.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-13T19:12:00Z
- **Completed:** 2026-09-13T19:22:00Z
- **Tasks:** 2
- **Files modified:** 7 del write-set, más el ledger de verificaciones

## Accomplishments

- Se añadieron fetchers SSR con `Cookie`/`no-store`, normalización allowlisted y mutaciones cliente para enviar recomendaciones y marcar mensajes como leídos.
- `SocialInbox` muestra únicamente la proyección del receptor, conserva el formulario ante errores, presenta `429`/`Retry-After` del servidor y actualiza el aggregate después de `mark_read`.
- `/messages` queda autenticada y el menú de cuenta enlaza `Mensajes de amigos`, anuncia el estado pendiente y muestra el punto rojo sin depender solo del color.

## Task Commits

Cada tarea quedó comprometida atómicamente:

1. **Task 1: Tracer: fetch privado → bandeja → mark_read/badge** — `83e3e23` (RED), `efb705f` (GREEN)
2. **Task 2: Entrada Mensajes de amigos y punto rojo textual** — `b3c49b7` (GREEN; la prueba RED falló antes de la implementación en la misma iteración)

El commit documental final incluye `Refs #60` y `Closes #60`.

## Files Created/Modified

- `apps/web/lib/api.ts` — DTOs, normalización y fetchers SSR de inbox/contador.
- `apps/web/lib/client-api.ts` — envío, lectura, contador y tratamiento de 429/Retry-After con CSRF.
- `apps/web/components/SocialInbox.tsx` — tarjetas privadas, estados loading/error/empty, recomendación y lectura.
- `apps/web/app/[locale]/messages/page.tsx` — página autenticada de mensajes y opciones de recomendación.
- `apps/web/components/AccountSwitcher.tsx` — enlace exacto, badge y estado accesible receptor-scoped.
- `apps/web/components/AppShell.tsx` — etiquetas localizadas del nuevo acceso.
- `apps/web/tests/social-messages.test.ts` — contrato de fetch, lectura, cooldown, render seguro y badge.
- `ideas-vault/Fases/Fase 6 - Descubrimiento publico.md` — espejo conceptual enlazado al resumen canónico y a la limitación de Chromium.

## Decisions Made

El backend sigue siendo la autoridad de privacidad, cooldown y contador. El frontend solo conserva el formulario y refleja respuestas exitosas; no crea mensajes localmente ni infiere pendientes de otra cuenta. La compatibilidad con el test de navegación existente se mantiene cuando `AccountSwitcher` se renderiza sin las nuevas etiquetas, mientras `AppShell` las proporciona siempre en el producto.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Tipado explícito del catálogo de recomendaciones**

- **Encontrado durante:** Task 1, verificación TypeScript.
- **Problema:** el fallback vacío de la carga opcional del catálogo se infería como `any[]`.
- **Corrección:** se tipó como `GameCard[]` y se separó el fallback de errores del `redirect` autenticado.
- **Archivos modificados:** `apps/web/app/[locale]/messages/page.tsx`.
- **Verificación:** `tsc --noEmit` pasa.
- **Commit:** `efb705f`.

**2. [Rule 1 - Test/runtime bug] Aislamiento de navegación y CSRF en Vitest**

- **Encontrado durante:** Task 2, verificación focalizada.
- **Problema:** el render SSR del selector necesitaba el mock de `next/navigation` y el test de POST necesitaba una cookie CSRF sintética.
- **Corrección:** se añadieron mocks locales sin credenciales reales.
- **Archivos modificados:** `apps/web/tests/social-messages.test.ts`.
- **Verificación:** 4 tests focalizados pasan.
- **Commit:** `b3c49b7`.

---

**Total desviaciones:** 2 auto-fijadas (1 Rule 3, 1 Rule 1).
**Impacto:** sin dependencias nuevas, sin cambio arquitectónico y dentro del write-set del plan.

## TDD Gate Compliance

Task 1 tiene commits RED/GREEN separados. En Task 2 la prueba RED se ejecutó y falló antes de implementar, pero el ajuste del test y la implementación se incluyeron en un único commit GREEN; se deja constancia para la auditoría del gate.

## Issues Encountered

- La orden declarada con `pnpm --dir apps/web test -- --run social-messages` arrastra suites del proyecto por la forma en que el script reenvía `--`; además, `nav-overflow` no puede iniciar Chromium en la imagen web y `social-comments.test.ts` sigue siendo un artefacto no integrado de `06-08`. La verificación equivalente focalizada `vitest run tests/social-messages.test.ts` pasa con 4/4 y TypeScript pasa. El caso queda registrado en `.planning/WINDOWS.md` como `unrun-verify`; no se modificó el trabajo ajeno.
- Los handlers `state.advance-plan` y `state.update-progress` no pudieron interpretar el formato histórico de `STATE.md`; se conservaron sus actualizaciones válidas y se ajustaron manualmente `stopped_at`, `next_action` y el porcentaje calculado 58/60.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

La UI de mensajes, el contador y los contratos SSR/client están listos para la integración de comentarios y traducciones de `06-08` y para los journeys E2E de `06-09`. La validación browser-level de foco y responsive queda pendiente hasta disponer de Chromium en la imagen web.

## Self-Check: PASSED

- Los siete archivos del write-set existen; `SocialInbox` contiene `aria-live`, la página contiene `Mensajes de amigos` y `AccountSwitcher` contiene el enlace/badge.
- Los commits `83e3e23`, `efb705f` y `b3c49b7` existen en el historial.
- La suite focalizada reporta 4/4 y `tsc --noEmit` termina con código 0.

---
*Phase: 06-public-discovery-and-resilient-enrichment*
*Completed: 2026-09-13*
