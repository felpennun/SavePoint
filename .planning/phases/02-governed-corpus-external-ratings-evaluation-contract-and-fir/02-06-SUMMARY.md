---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 06
subsystem: ui
tags: [nextjs, react, accessibility, game-detail, recommendations]

requires:
  - phase: 02-05
    provides: "Serializer de ficha y endpoints de novedades y DLC poseído."
  - phase: 02-04
    provides: "Catálogo con filtros y navegación por géneros."
provides:
  - "Sinopsis de ficha con clamp, expansión accesible y fallback sin JavaScript."
  - "Desglose de valoraciones y ScorePill relabelado sin afirmar que es solo IGDB."
  - "Estantes de novedades y DLC poseído con carátulas uniformes."
  - "La home y la ficha ya no muestran la tira obsoleta de populares de la demo."
affects: [phase-02-12, phase-03, product-ui]

actuals:
  tokens: 5200
  tasks: 3
  commits: 0

tech-stack:
  added: []
  patterns: ["Estantes horizontales con GameCard shelf y estados empty/error sin contenedor vacío."]

key-files:
  created:
    - apps/web/components/Synopsis.tsx
    - apps/web/components/RatingBreakdownLine.tsx
    - apps/web/components/NewReleasesShelf.tsx
    - apps/web/components/OwnedGamesDlcShelf.tsx
  modified:
    - apps/web/components/ScorePill.tsx
    - apps/web/app/[locale]/games/[id]/page.tsx
    - apps/web/app/[locale]/page.tsx
    - apps/web/lib/api.ts
    - apps/web/i18n/en.ts
    - apps/web/i18n/es.ts
    - e2e/a11y.spec.ts

key-decisions:
  - "Las carátulas de novedades, DLC y recomendaciones usan siempre GameCard con coverVariant=shelf para conservar dimensiones constantes."
  - "La tira de populares de la demo se elimina de la home y de la ficha porque el autor la marcó como desactualizada."

patterns-established:
  - "Los textos de terceros se renderizan como texto plano y nunca mediante HTML no confiable."
  - "Los estados vacíos y de error omiten el estante completo cuando no hay contenido útil."

requirements-completed: [QUAL-05, DATA-05]

coverage:
  - id: D1
    description: "Ficha con sinopsis ampliable, desglose de valoraciones y ScorePill relabelado."
    requirement: QUAL-05
    verification:
      - kind: automated_ui
        ref: "docker compose -f infra/compose.yaml exec -T web pnpm --dir apps/web run build"
        status: pass
    human_judgment: true
    rationale: "La interacción de expansión y el layout a 320px/400% requieren comprobación visual; el proyecto Playwright no declara el proyecto chromium."
  - id: D2
    description: "Estantes de novedades y DLC poseído con carátulas y estados seguros."
    requirement: DATA-05
    verification:
      - kind: automated_ui
        ref: "docker compose -f infra/compose.yaml exec -T web pnpm --dir apps/web run build"
        status: pass
    human_judgment: true
    rationale: "La presencia/ausencia del contenido y la uniformidad visual deben revisarse con datos reales del demo."

duration: 30min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 06: product polish de ficha y home

La ficha de videojuego incorpora una sinopsis legible y ampliable, desglose de la valoración externa y local, y estantes de contenido con carátulas uniformes. La home conserva novedades, pero deja de presentar el ranking obsoleto de populares de la demo.

## Verificación

- TypeScript: correcto.
- Build de Next.js: correcto.
- Suite de recomendaciones backend: correcta tras integrar los datos visuales necesarios.
- El pase E2E de Chromium queda pendiente porque la configuración disponible no declara ese proyecto.

## Incidencias

No se han modificado los ficheros de localización preexistentes del directorio `data/localization/`; pertenecen a otro trabajo del autor.

## Preparación para el siguiente plan

Los componentes y fetchers necesarios para reutilizar estantes en la página de recomendaciones están disponibles. Falta integrar y verificar formalmente el plan 02-12.
