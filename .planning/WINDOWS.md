---
schema_version: 1
open_count: 6
waived_count: 0
fixed_count: 0
total_count: 6
last_updated: 2026-09-13T15:11:32.391Z
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
  }
]
````
