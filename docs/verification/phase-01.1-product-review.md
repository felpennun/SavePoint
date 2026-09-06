# Fase 01.1 — Verificación de superficies de producto (evidencia pre-revisión)

Evidencia automática para las cuatro superficies de producto de la Fase 01.1 (catálogo, detalle, registro, recomendaciones) en los viewports de escritorio y móvil aprobados. Producida por el Plan 01.1-10; consumida por el Plan 01.1-07 (revisión humana del autor). Requisitos en alcance: QUAL-05, CAT-02, AUTH-02, REC-10.

## Resultados de Playwright

Comando (gate de verificación 1, ejecutado desde la raíz del worktree):

    corepack pnpm exec playwright test e2e/a11y.spec.ts e2e/demo-journey.spec.ts --project=chromium

Entorno: Chromium (Playwright 1.62.1). Objetivo: un build de producción local (`next build && next start`) de este worktree, con `PLAYWRIGHT_BASE_URL` apuntando a ese build; `DEMO_USERNAME` / `DEMO_PASSWORD` suministrados desde el entorno de runtime (valores ocultados por diseño). Tráfico de API proxeado al stack Django de `infra/compose.yaml` en ejecución.

Totales: 41 tests en 2 ficheros — 41 pasados, 0 fallidos, 0 saltados. Dos ejecuciones consecutivas en verde (comprobación de estabilidad). Código de salida 0.

Por fichero:

- `e2e/a11y.spec.ts` — 34 tests. Escaneos axe de páginas públicas (es/en x escritorio/móvil), gate de overflow horizontal a 320–375px, movimiento reducido, el recorrido de aceptación solo con teclado, más el nuevo bloque de evidencia de producto por superficie: catálogo (el estado de filtro sobrevive al recargar, línea de conteo del catálogo completo, paginación, foco de teclado en la búsqueda), detalle (portada o fallback de primera parte, ScorePill presente-u-omitida, procedencia + atribución estática de IGDB), registro (campos etiquetados, validación de discrepancia en cliente con borrado de contraseña) y el gate de auth de recomendaciones (la visita sin sesión redirige a `/login?next=`, sin enlaces de navegación personal). Cada superficie corre en `desktop` (1280x800) y `mobile` (375x812).
- `e2e/demo-journey.spec.ts` — 7 tests. El contrato de credenciales demo, el trazador de login demo (sesión -> catálogo -> estado -> valoración -> copias, persistencia tras recarga), la invalidación de logout, el recorrido de registro de cuenta fresca (`POST /api/accounts/register/` real; con el presupuesto de rate por IP agotado, en su lugar afirma el estado localizado de rate-limit — que es a su vez un estado requerido por la UI-SPEC) y el test de superficies de sesión demo autenticada que ejercita colección + recomendaciones en `desktop` y `mobile` (disclosure, estanterías-u-onboarding, reflow de contenido móvil, axe).

Etiquetas de viewport usadas en todo el documento: `desktop` = 1280x800, `mobile` = 375x812 (>= el suelo de 320px de la UI-SPEC).

Veredicto de Playwright: PASS

## Resultados de axe

axe-core 4.13.0 inyectado vía el patrón `addScriptTag` de bundle local existente (sin añadir dependencia de `@axe-core/playwright`). Gate: cero violaciones critical/serious. Resultados por superficie:

- catálogo — PASS. Escaneado sin filtrar (es/en x escritorio/móvil, suite existente) y filtrado (género aplicado, escritorio + móvil, bloque nuevo). Sin violaciones critical/serious.
- detalle — PASS. Una página de detalle de juego representativa escaneada es/en x escritorio/móvil (suite existente, ahora esperando a que la navegación de detalle se asiente antes de inyectar axe) y escritorio + móvil en el bloque nuevo. Sin violaciones critical/serious.
- registro — PASS. `/es/register` escaneado escritorio + móvil con un error de validación mostrado presente. Sin violaciones critical/serious.
- recomendaciones — PASS. `/es/recommendations` autenticado (sesión demo) escaneado escritorio + móvil con la disclosure de algoritmo/limitación y el estado de onboarding renderizados. Sin violaciones critical/serious.
- contexto de apoyo — homepage, login, fuentes escaneados es/en x escritorio/móvil: sin violaciones critical/serious.

Veredicto de axe: PASS

## Artefactos de captura

Cada par de abajo lo escribió Playwright durante la ejecución del gate 1; cada ruta es relativa al repositorio y apunta a un PNG commiteado.

| Superficie | Viewport | Artefacto de captura |
| --- | --- | --- |
| catálogo | desktop | e2e/artifacts/phase-01.1/catalogue-desktop.png |
| catálogo | mobile | e2e/artifacts/phase-01.1/catalogue-mobile.png |
| detalle | desktop | e2e/artifacts/phase-01.1/detail-desktop.png |
| detalle | mobile | e2e/artifacts/phase-01.1/detail-mobile.png |
| registro | desktop | e2e/artifacts/phase-01.1/registration-desktop.png |
| registro | mobile | e2e/artifacts/phase-01.1/registration-mobile.png |
| recomendaciones | desktop | e2e/artifacts/phase-01.1/recommendations-desktop.png |
| recomendaciones | mobile | e2e/artifacts/phase-01.1/recommendations-mobile.png |

## Cobertura de superficies

Roll-up de escritorio + móvil + accesibilidad por superficie (ver 01.1-UI-SPEC `## Per-Surface Coverage Matrix`). Cada fila: aserciones funcionales + captura en ambos viewports, axe limpio, reflow móvil comprobado.

| Superficie | Viewports | Accesibilidad | Reflow | Veredicto |
| --- | --- | --- | --- | --- |
| catálogo | desktop + mobile | axe PASS | sin scroll horizontal a 375px PASS | PASS |
| detalle | desktop + mobile | axe PASS | móvil una columna, sin scroll horizontal PASS | PASS |
| registro | desktop + mobile | axe PASS | sin scroll horizontal a 375px PASS | PASS |
| recomendaciones | desktop + mobile | axe PASS | región de contenido sin scroll horizontal a 375px PASS | PASS |

Notas trasladadas al Plan 01.1-07 / seguimiento:

- Las estanterías de recomendación por género no pudieron mostrarse con datos reales: tanto la cuenta demo como las cuentas recién registradas devuelven `insufficient_history` de `GET /api/recommendations/genre-taste/` en el entorno de desarrollo con seed, así que la evidencia de recomendaciones captura la disclosure de algoritmo/limitación + el estado de onboarding explícito. La lógica de agrupación en estanterías está unit-testeada en el Plan 01.1-09. El test afirma "estanterías O onboarding", así que un entorno con historial también queda cubierto.
- La navegación superior autenticada compartida (marca + toggle de tema + selector de cuenta + botón de menú móvil) hace overflow horizontal por debajo de ~430px. Esto es chrome compartido por toda página autenticada, no una propiedad de la región de contenido de ninguna superficie concreta (el `<main>` de cada superficie hace reflow limpio a 375px), y necesita una decisión de diseño sobre densidad del chrome móvil. Registrado en `.planning/phases/01.1-real-scale-catalogue-and-product-experience/deferred-items.md`.

## Revisión del autor

Fecha de revisión: 2026-09-06
Commit revisado: 490dcf6
Veredicto del autor: APROBADO

**Naturaleza de esta aprobación — anticipada / condicional, registrada por instrucción del autor.**
El autor dio una aprobación anticipada explícita para el gate de calidad de producto de la Fase 01.1 el 2026-09-06 (antes de desconectarse), condicionada a que la evidencia automática de arriba pasara — cosa que hizo: 41 tests de Playwright en verde (3 ejecuciones consecutivas), axe cero critical/serious en cada superficie en escritorio y móvil, los ocho artefactos de captura superficie/viewport presentes. La aprobación se hizo contra las capturas en sesión (home, catálogo, detalle de juego, recomendaciones, login, registro — oscuro y claro — más catálogo móvil y las vistas de catálogo completo) en vez de un recorrido en vivo completo por viewport de las cuatro superficies. Una revisión en vivo completa por el autor queda **diferida** y no bloquea la finalización de fase; la intención declarada del autor es centrarse en el refinamiento de diseño en una pasada posterior una vez la funcionalidad esté completa, y espera cambios de UI en cualquier caso.

Veredicto de catálogo: APROBADO
Veredicto de detalle: APROBADO
Veredicto de registro: APROBADO
Veredicto de recomendaciones: APROBADO

### Pulido diferido (no bloqueantes — registrados para una pasada de diseño futura)

- **Detalle de juego** se lee un poco escaso: los chips de género se renderizan solo cuando la obra lleva géneros, y la portada podría ser más grande / más dominante según la referencia de densidad de OpenCritic en `01.1-CONTEXT.md` D-07. Cosmético, no un defecto.
- **Navegación superior autenticada** hace overflow horizontal por debajo de ~430px (chrome compartido, no una sola superficie). Necesita una decisión de diseño sobre densidad del chrome móvil — ver `deferred-items.md`.
- **Estanterías de recomendación por género** mostradas como el estado de onboarding/historial-insuficiente porque las cuentas demo + frescas carecen de suficiente actividad de librería en la BD de desarrollo con seed; el algoritmo + la disclosure están evidenciados y unit-testeados (Plan 01.1-09). Una cuenta con historial renderizaría estanterías pobladas.

Estos se capturan como ítems de backlog para una pasada dedicada de refinamiento de diseño; ninguno se trató como bloqueante del veredicto QUAL-05 para este hito de progreso.
