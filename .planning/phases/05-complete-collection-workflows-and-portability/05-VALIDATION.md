---
phase: "05"
slug: "complete-collection-workflows-and-portability"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-12"
---

# Fase 05 — Estrategia de validación

> Contrato de validación para autenticación real, perfil, favoritos, comentarios,
> listas, copias, privacidad y exportación CSV versionada. PostgreSQL es
> obligatorio; la UI queda como handoff a la otra sesión.

## Infraestructura de pruebas

| Propiedad | Valor |
|---|---|
| Framework | pytest 9.1.1 + pytest-django 4.14.0; Playwright 1.62.1 para navegador |
| Configuración | `pyproject.toml`, `apps/api/pytest.ini`, `playwright.config.ts` |
| Base obligatoria | PostgreSQL mediante `infra/compose.yaml`; SQLite no es evidencia válida |
| Comando rápido | `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput &amp;&amp; docker compose -f infra/compose.yaml run --rm api pytest apps/api/accounts/tests/test_auth.py apps/api/library/tests/test_copies.py -q` |
| Comando de cierre backend | `docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput &amp;&amp; docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run &amp;&amp; docker compose -f infra/compose.yaml run --rm api pytest apps/api/accounts/tests apps/api/library/tests -q` |
| Handoff UI | `corepack pnpm exec playwright test e2e/collection-workflows.spec.ts --project=chromium` y matriz axe/teclado/responsive de la otra sesión |

## Mapa de verificación por tarea

| Task ID | Plan | Wave | Requisitos | Evidencia automatizada | Fails when |
|---|---|---:|---|---|---|
| 05-01-01 | 01 | 1 | PROF-01, PRIV-01 | `migrate --noinput &amp;&amp; makemigrations --check --dry-run &amp;&amp; pytest apps/api/accounts/tests/test_auth.py apps/api/accounts/tests/test_profile.py -q` | Cualquier comando devuelve exit code distinto de 0, hay migraciones pendientes o falta sesión PostgreSQL, hash, reload, IDOR, duplicado, CSRF o 429. |
| 05-01-02 | 01 | 1 | PROF-01, PRIV-01 | `migrate --noinput &amp;&amp; pytest apps/api/accounts/tests/test_profile.py apps/api/accounts/tests/test_public_profile.py -q` | La migración o pytest falla, o owner/anónimo/B reciben una proyección privada en alguna combinación de visibilidad. |
| 05-01-03 | 01 | 1 | PROF-01, PRIV-01 | `migrate --noinput &amp;&amp; makemigrations --check --dry-run &amp;&amp; pytest apps/api/accounts/tests -q` | Algún comando falla o `test_schema.py` no confirma tablas, límites y constraints de perfil/favoritos en PostgreSQL. |
| 05-02-01 | 02 | 2 | LIB-03, PRIV-01 | `migrate --noinput &amp;&amp; pytest apps/api/library/tests/test_comments.py -q` | `migrate` o pytest falla, o no se prueban unicidad, ownership y visibilidad propia del autor. |
| 05-02-02 | 02 | 2 | LIB-04, PRIV-01 | `[BLOCKING] migrate --noinput &amp;&amp; pytest apps/api/library/tests/test_lists.py -q` | El gate falla cerrado si `migrate --noinput` devuelve exit code distinto de 0 y entonces pytest no cuenta como ejecutado; también falla si pytest falla, o no se prueban posiciones consecutivas, colisión/concurrencia y rollback. |
| 05-02-03 | 02 | 2 | LIB-03, LIB-04, PRIV-01 | `migrate --noinput &amp;&amp; makemigrations --check --dry-run &amp;&amp; pytest apps/api/library/tests/test_schema.py apps/api/library/tests/test_comments.py apps/api/library/tests/test_lists.py apps/api/accounts/tests/test_public_profile.py -q` | La migración, el check o pytest falla; faltan constraints o la allowlist filtra una relación privada. |
| 05-03-01 | 03 | 3 | INV-03, INV-04, PRIV-01 | `migrate --noinput &amp;&amp; pytest apps/api/library/tests/test_copies.py -q` | `migrate` o pytest falla, o no se demuestra round-trip/reload e idempotencia de metadatos. |
| 05-03-02 | 03 | 3 | INV-03, INV-04, PRIV-01 | `[BLOCKING] migrate --noinput &amp;&amp; pytest apps/api/library/tests/test_copies.py apps/api/library/tests/test_schema.py -q` | Gate fail-closed: si `migrate --noinput` devuelve exit code distinto de 0, pytest —incluido `test_schema.py`— no cuenta como ejecutado; también falla si pytest falla, faltan reglas físico/digital, rollback, ownership A/B o constraints PostgreSQL, o aparecen datos privados en la proyección. |
| 05-03-03 | 03 | 3 | INV-03, INV-04, PRIV-01 | `if (-not (Test-Path -LiteralPath 'docs/verification/phase-05-api-handoff.md')) { throw 'handoff missing' }` y comprobación `Select-String` protegida por `if (-not (...)) { throw ... }` | Falta el handoff o cualquiera de sus tokens contractuales no aparece. |
| 05-04-01 | 04 | 4 | PORT-01, PORT-04 | `migrate --noinput &amp;&amp; pytest apps/api/library/tests/test_export.py apps/api/library/tests/test_schema.py -q` | La migración o pytest falla, o el export no prueba privacidad, determinismo, UTF-8 y neutralización de fórmulas. |
| 05-04-02 | 04 | 4 | PORT-01, PORT-02, PORT-03 | Comprobaciones protegidas de `Test-Path`/`Select-String` sobre `05-PORTABILITY-RECONCILIATION.md` y las notas canónicas, más comprobación determinista de `pending` + `Phase 7` y ausencia de endpoints/parsers/tests de importación en `apps/api/library` | Falta la reconciliación, PORT-02/03 no están literalmente `pending` y asignados a `Phase 7`, existe un endpoint/parser/test de importación en `apps/api/library`, faltan decisiones CSV-only/CustomList, o PORT-02/03 aparecen como implementados. |
| 05-04-03 | 04 | 4 | PORT-01, PORT-02, PORT-03, PORT-04 | `migrate --noinput &amp;&amp; pytest apps/api/accounts/tests apps/api/library/tests -q &amp;&amp; makemigrations --check --dry-run` | Migración, suite, check o cobertura de `test_copies.py` falla; el handoff browser no se atribuye al backend. |

## Archivos de prueba requeridos

- [ ] `apps/api/accounts/tests/test_profile.py` — persistencia PostgreSQL, avatar, alias, favoritos y combinaciones de privacidad.
- [ ] `apps/api/accounts/tests/test_public_profile.py` — owner/anónimo/B y allowlist pública.
- [ ] `apps/api/library/tests/test_comments.py` — unicidad, autor, visibilidad y ownership.
- [ ] `apps/api/library/tests/test_lists.py` — pertenencia a colección, duplicados, posiciones temporales, concurrencia y rollback.
- [ ] `apps/api/library/tests/test_copies.py` — metadatos de copia, reload, formato físico/digital e idempotencia.
- [ ] `apps/api/library/tests/test_schema.py` — migraciones, tablas, foreign keys, constraints y PostgreSQL.
- [ ] `apps/api/library/tests/test_export.py` — contrato CSV, orden, privacidad, UTF-8 y neutralización.
- [ ] `e2e/collection-workflows.spec.ts` — flujo de navegador; su edición y ejecución corresponden a la otra sesión.

## Decisiones de alcance y validación

- `PROF-01` se verifica como alias de login inmutable más biografía/avatar editables.
- `PORT-01` se verifica únicamente como CSV versionado; no se espera JSON en esta fase.
- `PORT-02` y `PORT-03` permanecen pendientes y asignados a la Fase 7; esta fase no crea endpoints, parsers ni tests de feature de importación.
- `CustomList` es el agregado primario de listas y su orden se prueba con posiciones consecutivas y transacciones collision-safe.
- La UI, axe, teclado y responsive son un handoff separado; esta rama no modifica `apps/web/**` ni `design/**`.

## Cierre de validación

- [ ] Las 12 tareas de los cuatro planes tienen `<automated>` y `<fails_when>` explícitos.
- [ ] Toda verificación de migración incluye `migrate --noinput` antes de tests de esquema o integración.
- [ ] No se usa SQLite, watch mode ni una cadena de comandos que ignore un exit code.
- [ ] `nyquist_compliant: true` se marcará únicamente después de ejecutar y registrar las verificaciones.

**Aprobación:** pendiente
