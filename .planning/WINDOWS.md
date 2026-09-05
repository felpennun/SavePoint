---
schema_version: 1
open_count: 3
waived_count: 0
fixed_count: 0
total_count: 3
last_updated: 2026-09-05T21:19:42.695Z
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
  }
]
````
