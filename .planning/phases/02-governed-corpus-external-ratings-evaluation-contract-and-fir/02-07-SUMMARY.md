---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 07
subsystem: ui
tags: [nextjs, tailwind, vitest, playwright, accessibility]

requires:
  - phase: 01.1-real-scale-catalogue-and-product-experience
    provides: "Design tokens, AppShell y controles de navbar accesibles"
provides:
  - "Tokens de sombra, skeleton y utilidades compartidas para las superficies de la Fase 2"
  - "Navbar autenticada solo-icono por debajo de md, con nombre accesible completo"
  - "Contratos automatizados para tokens CSS y overflow/paridad DOM de la navbar"
affects: [02-04, 02-06, 02-12, QUAL-05]

actuals:
  tokens: 1850
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Tokens CSS compartidos en globals.css para superficies flotantes, skeletons y facetas"
    - "Las etiquetas visibles responsive se ocultan con hidden md:inline sin alterar el DOM accesible"

key-files:
  created:
    - "apps/web/app/__tests__/globals-tokens.test.ts"
    - "apps/web/components/__tests__/nav-overflow.test.tsx"
  modified:
    - "apps/web/app/globals.css"
    - "apps/web/components/AppShell.tsx"
    - "apps/web/components/ThemeToggle.tsx"
    - "apps/web/components/AccountSwitcher.tsx"

key-decisions:
  - "Se reutilizan tokens de superficie existentes; no se introduce un color de acento nuevo."
  - "La comprobación DOM de navbar usa el Chrome local ya instalado cuando faltan los binarios gestionados de Playwright."

patterns-established:
  - "Los controles responsive conservan aria-label/aria-pressed y solo cambian la visibilidad de la etiqueta textual."
  - "Los tests CSS parsean globals.css y nombran explícitamente la regla ausente en el mensaje de fallo."

requirements-completed: [QUAL-05]

coverage:
  - id: D1
    description: "Tokens dark/light y utilidades de pulido compartidas para skeletons, facetas y tablas de contribución"
    requirement: QUAL-05
    verification:
      - kind: unit
        ref: "apps/web/app/__tests__/globals-tokens.test.ts (5 tests)"
        status: pass
      - kind: other
        ref: "corepack pnpm --dir apps/web run build"
        status: pass
    human_judgment: false
  - id: D2
    description: "Navbar autenticada solo-icono bajo md con nombres accesibles y DOM estable"
    requirement: QUAL-05
    verification:
      - kind: automated_ui
        ref: "apps/web/components/__tests__/nav-overflow.test.tsx (6 tests, Chrome local)"
        status: pass
      - kind: other
        ref: "corepack pnpm --dir apps/web run build"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-07
status: complete
---

# Phase 2: Gobernanza, ratings externos, contrato de evaluación y primer recomendador avanzado — Plan 07

**Tokens de interfaz reutilizables y navbar autenticada responsive con accesibilidad preservada bajo `md`**

## Performance

- **Duration:** 25 min de reanudación
- **Started:** 2026-09-07T00:00:00+02:00
- **Completed:** 2026-09-07
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Añadidos `--shadow-overlay`, tokens de skeleton y utilidades `.sp-skeleton`, `.sp-facet` y `.sp-contrib-table` respetando `prefers-reduced-motion`.
- Convertidos `ThemeToggle` y `AccountSwitcher` a solo-icono bajo `md`, conservando nombre accesible, estado y orden del DOM.
- Añadidas pruebas de contrato CSS y de navbar responsive; build y suite web completos pasan.

## Task Commits

1. **Tarea 1: Tokens y utilidades de pulido compartidas** — `51d8559`
2. **Tarea 2: Navbar autenticada solo-icono** — `bcd79dd` (fix: responsive navbar)

## Files Created/Modified

- `apps/web/app/globals.css` — tokens y utilidades compartidas.
- `apps/web/app/__tests__/globals-tokens.test.ts` — contratos parseados de CSS.
- `apps/web/components/AppShell.tsx` — geometría responsive del header.
- `apps/web/components/ThemeToggle.tsx` — etiqueta visible responsive.
- `apps/web/components/AccountSwitcher.tsx` — trigger accesible solo-icono.
- `apps/web/components/__tests__/nav-overflow.test.tsx` — pruebas de accesibilidad y paridad DOM.

## Decisions Made

- Se usó el Chrome instalado localmente mediante `PLAYWRIGHT_CHANNEL=chrome`; instalar navegadores gestionados no era necesario para validar el cambio y habría añadido una descarga externa.

## Deviations from Plan

### Correcciones necesarias

**1. Descubrimiento de tests en `__tests__`**
- **Encontrado durante:** Tarea 1.
- **Problema:** La configuración de Vitest no incluía la ruta de tests declarada por el plan.
- **Corrección:** Se amplió `apps/web/vitest.config.ts` para descubrir `app/__tests__` y `components/__tests__`.
- **Verificación:** Las cinco suites y 27 tests pasan.
- **Commit:** `51d8559`.

**Total de desviaciones:** 1 corrección necesaria.
**Impacto:** Sin cambio de alcance; evita que los contratos del plan queden fuera de CI local.

## Issues Encountered

- Los binarios gestionados de Playwright no estaban descargados. La suite se ejecutó con el Chrome local instalado, sin modificar dependencias ni lockfiles.

## User Setup Required

Ninguno.

## Next Phase Readiness

02-07 está listo para consumo por 02-04, 02-06 y 02-12. La ola 1 sigue pendiente únicamente de 02-01.

---
*Phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir*
*Plan: 07*
*Completed: 2026-09-07*
