---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
plan: 12
subsystem: ui
tags: [nextjs, react, recommendations, covers, accessibility]

requires:
  - phase: 02-11
    provides: "Endpoint autenticado del recomendador de contenido versionado."
  - phase: 02-06
    provides: "GameCard shelf y estante de DLC reutilizable."
provides:
  - "Página de recomendaciones con listas de contenido, gusto por género y DLC poseído."
  - "Carátulas, metadatos y dimensiones uniformes en las tarjetas de recomendaciones."
  - "Títulos visibles para cada sección y ausencia de la explicación técnica en la superficie de usuario."
affects: [phase-03, product-ui]

actuals:
  tokens: 3400
  tasks: 3
  commits: 0

tech-stack:
  added: []
  patterns: ["SSR autenticado con fetch paralelo y estantes reutilizables."]

key-files:
  created:
    - apps/web/components/ContentRecommendationShelf.tsx
  modified:
    - apps/web/app/[locale]/recommendations/page.tsx
    - apps/web/lib/api.ts
    - apps/web/i18n/dictionary.ts
    - apps/web/i18n/en.ts
    - apps/web/i18n/es.ts
    - apps/api/recommendations/views.py
    - apps/api/recommendations/content/rank.py
    - apps/api/recommendations/content/combine.py
    - apps/api/recommendations/tests/test_content.py
    - apps/web/app/[locale]/page.tsx
    - apps/web/app/[locale]/games/[id]/page.tsx

key-decisions:
  - "El recomendador de contenido aplica un mínimo de 1.000 valoraciones en la superficie de usuario."
  - "La evaluación conserva el conjunto completo y compartido de candidatos para no cambiar el protocolo de investigación."
  - "La página muestra únicamente listas y sus títulos; las explicaciones metodológicas permanecen en la documentación."

patterns-established:
  - "Los DTO de recomendaciones incluyen carátula, año y plataformas para evitar consultas individuales desde la página."
  - "El espaciado entre secciones depende del contenedor común y no del número de tarjetas de cada lista."

requirements-completed: [QUAL-05]

coverage:
  - id: D1
    description: "Página autenticada con secciones tituladas para contenido, géneros y DLC."
    requirement: QUAL-05
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_content.py"
        status: pass
      - kind: automated_ui
        ref: "docker compose -f infra/compose.yaml exec -T web pnpm --dir apps/web run build"
        status: pass
    human_judgment: true
    rationale: "La uniformidad visual de las tarjetas y el espaciado deben comprobarse en la demo a distintos anchos."
  - id: D2
    description: "Tarjetas de recomendaciones con carátulas y metadatos procedentes del backend."
    requirement: QUAL-05
    verification:
      - kind: integration
        ref: "apps/api/recommendations/tests/test_content.py::test_content_view_validates_algorithm_and_clamps_limit"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-07
status: complete
---

# Phase 2 Plan 12: listas de recomendaciones con carátulas

La página de recomendaciones presenta tres superficies independientes: el recomendador de contenido, las listas agrupadas por género y el contenido descargable de juegos poseídos. Cada superficie tiene un título y reutiliza tarjetas con carátula y tamaño constante.

## Verificación

- Suite de recomendaciones: 61 pruebas correctas.
- TypeScript: correcto.
- Build de Next.js: correcto.
- La tira obsoleta de “Populares en la demo” se ha retirado de la home y de la ficha.

## Preparación para el siguiente plan

La página consume el endpoint versionado de contenido y está preparada para que los resultados de la evaluación se documenten por separado. La verificación visual E2E queda condicionada a disponer del proyecto Chromium en la configuración de Playwright.
