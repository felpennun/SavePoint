---
schema_version: 1
open_count: 11
waived_count: 0
fixed_count: 1
total_count: 12
last_updated: 2026-09-14T01:27:07.125Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01.1 | stub | apps/web/lib/catalogue-filters.ts |  | Curated placeholder platform/genre option lists pending Plan 03 option endpoint | open |  | 2026-09-05T21:19:35.312Z |  |
| 2 | 01.1 | stub | apps/web/app/[locale]/recommendations/page.tsx |  | Recommendations page shows insufficient-history state until Plan 05/09 heuristic endpoint | open |  | 2026-09-05T21:19:42.221Z |  |
| 3 | 01.1 | stub | apps/web/app/[locale]/register/page.tsx |  | Register submit maps errors but backend /api/accounts/register/ is Plan 04/08 | open |  | 2026-09-05T21:19:42.695Z |  |
| 4 | 02 | deviation | apps/api/catalogue/management/commands/enrich_rawg_ratings.py | 142 | RAWG SourceRecord update_or_create on (source, source_id) overwrites work FK when one RAWG game reconciles to 2 governed works (22 rows in the N=10000 run); snapshots correct, provenance row points to one work only | open |  | 2026-09-07T08:54:03.534Z |  |
| 5 | 02 | deviation | apps/api/catalogue/ratings.py |  | display_rating D-09: reparto de pesos externo/local (min(max(n,1),50)) y conjunto de cuentas implementado por must_haves; pendiente ratificacion del autor antes de que 02-13 cierre DATA-07 (coverage D6, human_judgment:true) | open |  | 2026-09-07T09:42:03.280Z |  |
| 6 | 06 | unrun-verify | .planning/phases/06-public-discovery-and-resilient-enrichment/deferred-items.md | 5 | La suite agregada de catalogue-filters no puede completar nav-overflow porque falta Chromium en el contenedor; las pruebas focalizadas y TypeScript pasan. | open |  | 2026-09-13T15:11:32.391Z |  |
| 7 | 06 | unrun-verify | apps/web/components/SocialActions.tsx |  | Verificacion browser-level de foco, Escape y responsive no ejecutada por ausencia de Chromium en la imagen web | open |  | 2026-09-13T19:04:30.104Z |  |
| 8 | 06 | unrun-verify | apps/web/tests/social-comments.test.ts |  | La orden amplia del frontend arrastra el contrato social-comments pendiente de 06-08 y Playwright no puede iniciar por ausencia de Chromium; la prueba focalizada social-messages y TypeScript pasan. | open |  | 2026-09-13T19:21:44.046Z |  |
| 9 | 06 | unrun-verify | apps/web/components/__tests__/nav-overflow.test.tsx |  | La suite completa de Vitest no puede ejecutar nav-overflow porque falta Chromium; los 53 tests no browser, los 3 social-comments, los 7 i18n y TypeScript pasan. | open |  | 2026-09-13T19:31:19.089Z |  |
| 10 | 06 | unrun-verify | e2e/catalogue-discovery.spec.ts |  | Journey browser completo y revisión axe visual diferidos por limitaciones de la imagen Compose. | open |  | 2026-09-13T19:54:05.633Z |  |
| 11 | 06 | unrun-verify | e2e/social-workflows.spec.ts |  | Journey social browser completo diferido por limitaciones de la imagen Compose y variables de ejecución no consignadas. | open |  | 2026-09-13T19:54:06.081Z |  |
| 12 | 07 | unrun-verify | docs/verification/phase-07-operations.md |  | Restore mensual desechable bloqueado por UniqueViolation de admin_uuid duplicado en accounts.0004_phase7_anonymization | fixed |  | 2026-09-14T01:12:45.312Z | 2026-09-14T01:27:07.125Z |

````json
[
  {
    "id": 1,
    "kind": "stub",
    "phase": "01.1",
    "file": "apps/web/lib/catalogue-filters.ts",
    "line": null,
    "description": "Curated placeholder platform/genre option lists pending Plan 03 option endpoint",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-05T21:19:35.312Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "stub",
    "phase": "01.1",
    "file": "apps/web/app/[locale]/recommendations/page.tsx",
    "line": null,
    "description": "Recommendations page shows insufficient-history state until Plan 05/09 heuristic endpoint",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-05T21:19:42.221Z",
    "resolved_at": null
  },
  {
    "id": 3,
    "kind": "stub",
    "phase": "01.1",
    "file": "apps/web/app/[locale]/register/page.tsx",
    "line": null,
    "description": "Register submit maps errors but backend /api/accounts/register/ is Plan 04/08",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-05T21:19:42.695Z",
    "resolved_at": null
  },
  {
    "id": 4,
    "kind": "deviation",
    "phase": "02",
    "file": "apps/api/catalogue/management/commands/enrich_rawg_ratings.py",
    "line": 142,
    "description": "RAWG SourceRecord update_or_create on (source, source_id) overwrites work FK when one RAWG game reconciles to 2 governed works (22 rows in the N=10000 run); snapshots correct, provenance row points to one work only",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-07T08:54:03.534Z",
    "resolved_at": null
  },
  {
    "id": 5,
    "kind": "deviation",
    "phase": "02",
    "file": "apps/api/catalogue/ratings.py",
    "line": null,
    "description": "display_rating D-09: reparto de pesos externo/local (min(max(n,1),50)) y conjunto de cuentas implementado por must_haves; pendiente ratificacion del autor antes de que 02-13 cierre DATA-07 (coverage D6, human_judgment:true)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-07T09:42:03.280Z",
    "resolved_at": null
  },
  {
    "id": 6,
    "kind": "unrun-verify",
    "phase": "06",
    "file": ".planning/phases/06-public-discovery-and-resilient-enrichment/deferred-items.md",
    "line": 5,
    "description": "La suite agregada de catalogue-filters no puede completar nav-overflow porque falta Chromium en el contenedor; las pruebas focalizadas y TypeScript pasan.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T15:11:32.391Z",
    "resolved_at": null
  },
  {
    "id": 7,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "apps/web/components/SocialActions.tsx",
    "line": null,
    "description": "Verificacion browser-level de foco, Escape y responsive no ejecutada por ausencia de Chromium en la imagen web",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T19:04:30.104Z",
    "resolved_at": null
  },
  {
    "id": 8,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "apps/web/tests/social-comments.test.ts",
    "line": null,
    "description": "La orden amplia del frontend arrastra el contrato social-comments pendiente de 06-08 y Playwright no puede iniciar por ausencia de Chromium; la prueba focalizada social-messages y TypeScript pasan.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T19:21:44.046Z",
    "resolved_at": null
  },
  {
    "id": 9,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "apps/web/components/__tests__/nav-overflow.test.tsx",
    "line": null,
    "description": "La suite completa de Vitest no puede ejecutar nav-overflow porque falta Chromium; los 53 tests no browser, los 3 social-comments, los 7 i18n y TypeScript pasan.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T19:31:19.089Z",
    "resolved_at": null
  },
  {
    "id": 10,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "e2e/catalogue-discovery.spec.ts",
    "line": null,
    "description": "Journey browser completo y revisión axe visual diferidos por limitaciones de la imagen Compose.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T19:54:05.633Z",
    "resolved_at": null
  },
  {
    "id": 11,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "e2e/social-workflows.spec.ts",
    "line": null,
    "description": "Journey social browser completo diferido por limitaciones de la imagen Compose y variables de ejecución no consignadas.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-13T19:54:06.081Z",
    "resolved_at": null
  },
  {
    "id": 12,
    "kind": "unrun-verify",
    "phase": "07",
    "file": "docs/verification/phase-07-operations.md",
    "line": null,
    "description": "Restore mensual desechable bloqueado por UniqueViolation de admin_uuid duplicado en accounts.0004_phase7_anonymization",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-14T01:12:45.312Z",
    "resolved_at": "2026-09-14T01:27:07.125Z"
  }
]
````
