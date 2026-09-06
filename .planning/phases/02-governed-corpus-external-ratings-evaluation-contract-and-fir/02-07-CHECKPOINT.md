---
phase: 02
plan: 07
github_issue: 23
status: complete
completed_tasks: 2
total_tasks: 2
updated: 2026-09-07
---

# Checkpoint recuperable — 02-07

## Tarea 1 terminada

Tokens dark/light de sombra, alias de superficies para esqueletos, utilidades de faceta,
tabla de contribuciones y barrido desactivado con movimiento reducido implementados.

- RED: `5052368`, cinco tests fallaron por ausencia de reglas antes de implementar.
- GREEN: commit de implementación identificado por `feat(02-07): add shared product polish utilities`.
- `corepack pnpm --dir apps/web run test --run`: **21/21 PASS**, cuatro suites.
- `corepack pnpm --dir apps/web run build`: **PASS**, compilación y TypeScript.
- Mutaciones independientes: igualar sombras, activar barrido con movimiento reducido,
  quitar marcador oculto y añadir acento. Las cuatro fueron rechazadas por los tests;
  CSS restaurado y suite verde después.
- Aviso previo de Next: convención `middleware` obsoleta. Fuera del alcance.

## Desviaciones y límites

- Se amplió `apps/web/vitest.config.ts`: las rutas `__tests__` declaradas por el plan
  estaban excluidas de la suite existente (corrección necesaria de descubrimiento).
- Se omite el test vacío `expect(true)` ordenado por el plan: no verifica comportamiento.
  El fichero de navbar se crea con pruebas reales en la tarea 2.
- La geometría, `aria-hidden` y región de estado pertenecen a los futuros consumidores
  de las utilidades (02-04/02-06/02-12). No se ha realizado el pase axe de esas superficies.

## Siguiente acción exacta

Ejecutar tarea 2 de `02-07-PLAN.md`: ocultar solo las etiquetas visibles bajo `md`,
conservar nombre accesible y estado de ambos controles, comprobar header y añadir tests
DOM de navbar. No rehacer tarea 1. Antes, verificar el commit GREEN con `git log`.

## Tarea 2 terminada

La barra autenticada conserva ambos controles en el header y oculta solo las etiquetas
visibles por debajo de `md`, sin cambiar el orden del DOM ni el nombre accesible.
`AccountSwitcher` conserva siempre la identificación de cuenta simulada en
`aria-label`; `ThemeToggle` conserva `aria-pressed` y sus etiquetas de estado.

- Verificación: `corepack pnpm --dir apps/web run test --run` con
  `PLAYWRIGHT_CHANNEL=chrome`: **27/27 PASS**, cinco suites.
- Verificación: `corepack pnpm --dir apps/web run build`: **PASS**, compilación y TypeScript.
- El test de navbar comprueba nombres accesibles, estado pulsado, paridad del DOM y
  presencia de ambos controles en el header a 320/375/768/1280 px.
- La verificación usa el Chrome instalado localmente porque no hay binarios gestionados
  de Playwright descargados; no se añadió ninguna dependencia ni se modificó el lockfile.

## Cierre del plan

Las dos tareas de 02-07 están completas y verificadas. El orquestador mantiene
`STATE.md`, `ROADMAP.md` y `REQUIREMENTS.md`; no iniciar la ola 2 hasta cerrar también
02-01.
