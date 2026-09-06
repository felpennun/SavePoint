# Phase 01.1 — Deferred Items

Out-of-scope discoveries logged during execution. Not fixed here; routed to
a follow-up plan / phase.

## From Plan 01.1-10 (automated product evidence)

### D-01.1-10-a — Authenticated top-nav overflows horizontally below ~430px

- **Found during:** Plan 01.1-10, mobile reflow evidence for the
  recommendations surface (demo session).
- **What:** When a visitor is signed in, the shared header packs brand +
  `ThemeToggle` (icon + "Tema: {estado}" text) + `AccountSwitcher` (icon +
  "Cuenta simulada: {alias}" + chevron) + the mobile-menu button into one
  non-wrapping flex row. At 375px this row is ~483px wide → page-level
  horizontal scroll on every authenticated page.
- **Scope call:** This is chrome shared by all authenticated pages, not a
  property of any single Plan 01.1-10 surface. Each surface's own `<main>`
  content region reflows cleanly at 375px (verified). Fixing the header
  needs a design decision (icon-only toggles on mobile, abbreviated
  labels, or moving one control into the disclosure) that touches the
  approved 01.1-UI-SPEC Navbar contract.
- **Not done because:** Plan 01.1-10's files are the two e2e suites + the
  review doc; a navbar redesign is a UI-SPEC change, not an evidence-capture
  change. The unauthenticated header overflow (logged-out chrome) WAS fixed
  in this plan (header gap/padding made responsive) because it blocked the
  pre-existing `e2e/a11y.spec.ts` 320–375px overflow gate.
- **Suggested owner:** a small follow-up UI plan, or fold into Plan 01.1-07
  review follow-ups. Affected: `apps/web/components/AppShell.tsx`,
  `apps/web/components/ThemeToggle.tsx`, `apps/web/components/AccountSwitcher.tsx`.

## AUTH-02 / SC3 — cuentas simuladas plurales construidas pero no cableadas a ningún runtime

**Estado: RESUELTO el 2026-09-06** (plan de seguimiento "reconciliar-y-cablear", opción A
autorizada por el autor). Ya no es un ítem diferido.

### Cómo estaba (el hueco original)

`DemoAccountIdentity` + `bootstrap_demo_accounts` (contrato JSON `DEMO_ACCOUNTS` solo por
entorno) estaban implementados y testeados (Plan 01.1-04), pero nada activaba el camino
plural en un entorno en ejecución: `infra/compose.yaml` y `apps/api/render-start.sh`
llamaban al singular `bootstrap_demo_account`, así que el producto en vivo exponía una sola
cuenta precargada. La verificación de la Fase 01.1 registraba SC3 como PARCIAL por eso.

El arreglo "de una línea" (cambiar el comando de arranque + fijar un `DEMO_ACCOUNTS` local)
**no** funcionaba contra una base de datos que ya tenía el usuario `demo-visitor` de la
Fase 1 — `bootstrap_demo_accounts` abortaba con `SeedContractError: A seed username collides
with an existing, unrelated account` porque ese usuario preexistente no tenía un
`DemoAccountIdentity` para la clave de anchor legacy. Se probó y se revirtió en el cierre
de fase.

### Qué se hizo (2026-09-06)

1. **Reconciliación:** `bootstrap_demo_accounts` ahora, cuando el contrato incluye una
   entrada con `key == LEGACY_ANCHOR_KEY` y no existe aún su `DemoAccountIdentity`, **adopta**
   el usuario que está detrás del `DemoAccountAnchor` fijo (`DEMO_ACCOUNT_ANCHOR_ID`) — le
   adjunta el `DemoAccountIdentity` y rota usuario/contraseña — en vez de tratarlo como una
   colisión ajena. Mismo patrón de "convivir con estado existente" que el
   `fix(01.1-02)` de reconciliación de `slug` de `Platform`. Una colisión genuinamente ajena
   (un usuario no-demo con el mismo nombre) sigue siendo `SeedContractError` fail-closed.
2. **Cableado:** `infra/compose.yaml` y `apps/api/render-start.sh` llaman al comando
   **plural**. `DEMO_ACCOUNTS` lleva 3 cuentas — `demo-visitor` (primaria, `key`
   `demo-anchor-primary`), `demo-critico`, `demo-coleccionista` (etiquetas en español) —
   como placeholder inerte D-02 en compose y `sync: false` en `render.yaml` (el autor pone
   el valor real en el entorno de Render en el despliegue). `check-secrets.ps1` allowlista
   las dos contraseñas placeholder nuevas.
3. **Verificación en vivo:** al recrear el contenedor api, el arranque loguea
   `Demo accounts ready (total=3, created=2, rotated=1)`; cada cuenta hace
   `POST /api/accounts/login/` → 200 y `POST /api/accounts/logout/` → 200 de forma
   independiente, y tras el logout `GET /api/library/entries/` → 403 (sesión invalidada).
   3 tests de reconciliación nuevos en `test_bootstrap_demo_account.py` (31 en total) +
   209 de la suite api pasan; `check-secrets.ps1` PASS.

SC3 pasa a **VERIFICADO** en `01.1-VERIFICATION.md` (score 5/5).

## De la revisión remota del autor por capturas (2026-09-06) — pulido diferido para la pasada de diseño

El autor aprobó la Fase 01.1 (QUAL-05 cerrado sin condiciones) tras revisar 18 capturas del
stack local. Cuatro ítems cosméticos observados, aceptados explícitamente como pulido
diferido (el autor espera cambios de UI de todas formas); ninguno bloquea el cierre de fase.

### D-01.1-13-a — Mezcla ES/EN en la disclosure de la página de recomendaciones

- **Qué:** la caja "Cómo se generan" muestra el primer párrafo en español y el segundo en
  **inglés**. Ese segundo texto es el campo `limitation` del DTO de
  `GET /api/recommendations/genre-taste/`, un string definido en
  `apps/api/recommendations/genre_heuristic.py` (`_INSUFFICIENT_HISTORY_LIMITATION` /
  `_LIMITATION`). El frontend (`apps/web/app/[locale]/recommendations/page.tsx`) lo vuelca
  crudo.
- **Fix:** el frontend debe renderizar una versión localizada (ES/EN) del mensaje según el
  `algorithm_id` / el estado `insufficient_history`, en vez de mostrar el `limitation` de la
  API. El `limitation` de la API se mantiene en inglés (es una cadena de código / contrato
  del DTO, documentada en ADR-007) pero deja de ser texto de producto visible.
- **Coste:** pequeño (una tabla de mensajes en `i18n/` + un branch en la página). ~5–10 min.
- **Afecta:** `apps/web/app/[locale]/recommendations/page.tsx`, `apps/web/i18n/es.ts` +
  `en.ts`. Sin cambios de backend.

### D-01.1-13-b — El menú de cuenta no identifica la cuenta activa

- **Qué:** `AccountSwitcher` intenta `GET /api/accounts/me/` para mostrar el alias en el
  trigger y en el panel, pero ese endpoint **no existe** (404), así que degrada al literal
  "Cuenta simulada" en las tres cuentas. Los tres logins funcionan de forma independiente
  (verificado), pero el nav no distingue visualmente qué cuenta tienes activa, lo que resta
  legibilidad a la demo de SC3.
- **Fix:** añadir una vista DRF mínima `MeView` (`IsAuthenticated`) en
  `apps/api/accounts/` que devuelva `{"username": request.user.username}` (y opcionalmente
  `display_label` del `DemoAccountIdentity` si existe), registrarla en
  `accounts/urls.py` como `me/`. `AccountSwitcher` ya la consume. Añadir un test.
- **Coste:** pequeño (~15 líneas + test + una fila en `config/urls.py` ya cubierta).
- **Afecta:** `apps/api/accounts/views.py`, `apps/api/accounts/urls.py`,
  `apps/api/accounts/tests/`. `apps/web/components/AccountSwitcher.tsx` ya está preparado.

### (ya registrados antes, confirmados en la revisión)

- **D-01.1-10-a** — nav superior autenticada con overflow horizontal a <430px.
- **Detalle de juego escaso** — sin `summary` (IGDB no se importa), panel de estado/copias
  comprimido, algún juego con título vacío por dato IGDB pobre. Ver "Pulido diferido" en
  `docs/verification/phase-01.1-product-review.md`.
