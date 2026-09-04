---
phase: "01"
slug: "three-day-public-demo-slice"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-04"
---

# Phase 01 — Validation Strategy

> Contrato de validación tracer-first para mantener ciclos de feedback cortos durante la ejecución.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest + pytest-django sobre PostgreSQL; frontend: Vitest + Testing Library; navegador: Playwright + axe-core |
| **Config file** | Ninguno todavía — Wave 0 los crea |
| **Quick run command** | `docker compose run --rm api pytest -q -x` y `pnpm --dir apps/web test --run` |
| **Full suite command** | `docker compose up -d --build --wait` seguido de `pnpm --dir apps/web exec playwright test` |
| **Estimated runtime** | Por medir tras completar Wave 0; objetivo de feedback rápido < 60 s por tarea |

## Sampling Rate

- **After every task commit:** ejecutar las pruebas del módulo modificado; objetivo menor de 30 s.
- **After every plan wave:** ejecutar backend, frontend unitario y al menos un E2E Chromium.
- **Before `$gsd-verify-work`:** suite completa, importación desde cero, Compose limpio, smoke desplegado y checklist UI deben estar verdes.
- **Max feedback latency:** 60 s para la muestra rápida; la suite completa puede superar ese límite y se mide por separado.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-01/15-02/04-02 | 01-15/01-04 | 4/5 | AUTH-01 | T-15-01/T-04-01 | bootstrap/rotación sin fuga, sesión válida, logout y rechazo CSRF | API/E2E | `pytest apps/api/accounts/tests -q` | ❌ W0 | ⬜ pending |
| 07-02 | 01-07 | 6 | PROF-02, INV-05 | T-07-01 | proyección pública por allowlist sin propiedad privada | API/E2E | `pytest apps/api/accounts/tests/test_public_profile.py -q` | ❌ W0 | ⬜ pending |
| 06-02 | 01-06 | 5 | CAT-01, CAT-06 | T-06-02 | búsqueda offline exacta, por alias, acentos y typo | integration | `pytest apps/api/catalogue/tests/test_search.py -q` | ❌ W0 | ⬜ pending |
| 06-02 | 01-06 | 5 | CAT-03, CAT-04 | T-06-01 | jerarquía estable y procedencia visible | integration | `pytest apps/api/catalogue/tests/test_detail.py -q` | ❌ W0 | ⬜ pending |
| 04-01/07-01 | 01-04/01-07 | 5/6 | LIB-01, LIB-02 | T-04-02 | autorización por propietario, historial y medias estrellas exactas | unit/API | `pytest apps/api/library/tests/test_entry.py` | ❌ W0 | ⬜ pending |
| 07-01 | 01-07 | 6 | INV-01, INV-02 | T-07-02 | múltiples copias aisladas por usuario | API | `pytest apps/api/library/tests/test_copies.py -q` | ❌ W0 | ⬜ pending |
| 05/06 | 01-05/01-06 | 3/5 | DATA-01, DATA-02 | T-06-01 | hash, licencia, procedencia e importación idempotente | unit/integration | `pytest apps/api/catalogue/tests/test_import.py -q` | ❌ W0 | ⬜ pending |
| 07-03/16-01/16-02 | 01-07/01-16 | 6/7 | REC-02 | T-16-01/T-16-03 | seis resultados deterministas con metadatos antes de superficies | unit/API | `pytest apps/api/library/tests/test_popularity.py apps/api/accounts/tests/test_seed_demo.py -q` | ❌ W0 | ⬜ pending |
| 15-01/15-02/11-02 | 01-15/01-11 | 4/10 | SEC-02 | T-15-01/T-11-01 | credencial runtime y ausencia de secretos/entradas maliciosas | static/API | `scripts/check-secrets.ps1` | ❌ W0 | ⬜ pending |
| 16-02/11/12 | 01-16/01-11/01-12 | 7/10/11 | OPS-01, OPS-02, OPS-03 | T-16-01/T-12-03 | seed ordenado, despliegue saludable y arranque local sin proveedor | smoke/integration | `docker compose up --build --wait` | ❌ W0 | ⬜ pending |
| 10-01 | 01-10 | 9 | QUAL-03 | T-10-01 | ES/EN, teclado, axe y viewports objetivo | E2E/manual | `playwright test e2e/demo-journey.spec.ts e2e/a11y.spec.ts` | ❌ W0 | ⬜ pending |
| 13-01/13-02 | 01-13 | 11 | DOC-01, AGENT-01, AGENT-02, AGENT-03 | T-13-01 | evidencia tipada, enlazada y sin secretos | static | `scripts/check-evidence.ps1` | ❌ W0 | ⬜ pending |

## Wave 0 Requirements

- [ ] Configurar pytest/pytest-django, fixtures compartidos y PostgreSQL real de test.
- [ ] Configurar Vitest y Testing Library, incluida paridad ES/EN.
- [ ] Configurar Playwright para entorno local y `BASE_URL` desplegada.
- [ ] Crear fixtures de XSS/URL, dos usuarios para IDOR y manifiesto con hash incorrecto.
- [ ] Crear primero `e2e/demo-journey.spec.ts` como tracer end-to-end.
- [ ] Crear checklist manual versionado para teclado, 320 px, zoom 400 % y lector de pantalla básico.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Legibilidad y ausencia de solapamientos a 320 px y zoom 400 % | QUAL-03 | La calidad visual requiere inspección humana | Recorrer portada, login, catálogo, detalle y perfil en ES/EN con teclado |
| Lector de pantalla básico | QUAL-03 | La experiencia auditiva no queda cubierta completamente por axe | Verificar orden, nombres accesibles, avisos de error y cambios de estado |
| Procedencia/licencia de cada carátula seleccionada | DATA-01 | La licencia de Commons se decide por archivo | Comparar manifiesto, URL de archivo, autor, licencia y página de atribución |
| Smoke de la URL pública | OPS-01 | Depende del recurso externo desplegado | Ejecutar el recorrido del tribunal y registrar fecha, commit y resultado |

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency measured and acceptable
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
