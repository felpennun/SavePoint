---
fase: 07-research-panel-hardening-and-evidence-freeze
plan: 05
estado: PASS
fecha_utc: 2026-09-14T08:54:18Z
---

# Gate de lanzamiento de la Fase 07

La gate final se ejecutÃ³ como un Ãºnico orquestador fail-closed. No invoca el runner de evaluaciÃ³n, no recalcula mÃ©tricas y protege por hash el artefacto v15, el snapshot de cohortes, el puntero de protocolo y el marker consumido.

## Resultado

**Estado:** PASS
**Fallo:** Ninguno.

| ComprobaciÃ³n | Estado | Comando | Evidencia resumida |
|---|---|---|---|
| Git diff check | PASS | `git diff --check` | exit 0 |
| Compose configuration | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml config` | exit 0 |
| Local stack setup | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml up --build --wait db api web` | exit 0 |
| Provision local demo roles | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml exec -T -e RESEARCH_VIEWER_USERNAME=phase7-research-viewer -e RESEARCH_VIEWER_PASSWORD=[redacted] -e PLATFORM_ADMIN_USERNAME=phase7-platform-admin -e PLATFORM_ADMIN_PASSWORD=[redacted] api python manage.py shell -c import os;from django.contrib.auth import get_user_model;from accounts.models import AccountProfile;from django.core.management import call_command;U=get_user_model();specs=[('RESEARCH_VIEWER_USERNAME','RESEARCH_VIEWER_PASSWORD','Research Viewer'),('PLATFORM_ADMIN_USERNAME','PLATFORM_ADMIN_PASSWORD','Platform Admin')];users=[(U.objects.get_or_create(username=os.environ[un])[0],pw,g) for un,pw,g in specs];[(u.set_password(os.environ[pw]),setattr(u,'is_active',True),u.save(update_fields=['password','is_active'])) for u,pw,g in users];[call_command('bootstrap_phase7_roles',user_id=str(AccountProfile.objects.get_or_create(user=u)[0].admin_uuid),group=g) for u,pw,g in users]` | exit 0 |
| Migration drift check | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml run --rm api python manage.py migrate --check` | exit 0 |
| Django deploy checks | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml run --rm -e DJANGO_DEPLOY_ENV=production api python manage.py check --deploy` | exit 0 |
| Backend phase 7 contract API admin portability operations | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml run --rm api pytest apps/api/evaluation/tests/test_phase7_contract.py apps/api/evaluation/tests/test_phase7_api.py apps/api/tests/test_phase7_admin_security.py apps/api/library/tests/test_portability.py apps/api/tests/test_phase7_operations.py -q` | exit 0 |
| Vitest | PASS | `corepack pnpm --dir apps/web exec vitest run` | exit 0 |
| TypeScript | PASS | `corepack pnpm --dir apps/web exec tsc --noEmit` | exit 0 |
| Playwright and axe Chromium | PASS | `corepack pnpm exec playwright test e2e/research-panel.spec.ts e2e/admin-security.spec.ts e2e/a11y.spec.ts e2e/deployed-smoke.spec.ts --project=chromium` | exit 0 |
| Post-browser idle connection cleanup | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml exec -T db psql -U savepoint_test -d postgres -v ON_ERROR_STOP=1 -c SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND state = 'idle';` | exit 0 |
| API connection reset before recovery gates | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml restart api` | exit 0 |
| API ready after connection reset | PASS | `docker compose -f C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml up -d --wait api` | exit 0 |
| Secrets scan | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-secrets.ps1` | exit 0 |
| Dependency scan | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1` | exit 0 |
| Security scan | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-security.ps1 -IncludeDeployment` | exit 0 |
| Evidence scan | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1` | exit 0 |
| Backup manifest help contract | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-backup-manifest.ps1 -Help` | exit 0 |
| Weekly backup | PASS | `powershell -ExecutionPolicy Bypass -File scripts/backup-postgres.ps1 -BackupRoot C:\Users\Felipe\AppData\Local\Temp\savepoint-phase-07-launch-2097849a4a2d48a6a8f4db17eff2d0c2 -BackupKind weekly -ArtifactPath docs/verification/phase-07-evidence-manifest.json` | exit 0 |
| Backup manifest validation | PASS | `powershell -ExecutionPolicy Bypass -File scripts/check-backup-manifest.ps1 -ManifestPath C:\Users\Felipe\AppData\Local\Temp\savepoint-phase-07-launch-2097849a4a2d48a6a8f4db17eff2d0c2\weekly-20260914-105045-20192.manifest.json -BackupRoot C:\Users\Felipe\AppData\Local\Temp\savepoint-phase-07-launch-2097849a4a2d48a6a8f4db17eff2d0c2` | exit 0 |
| Disposable monthly restore | PASS | `powershell -ExecutionPolicy Bypass -File scripts/restore-disposable-db.ps1 -BackupRoot C:\Users\Felipe\AppData\Local\Temp\savepoint-phase-07-launch-2097849a4a2d48a6a8f4db17eff2d0c2 -ManifestPath C:\Users\Felipe\AppData\Local\Temp\savepoint-phase-07-launch-2097849a4a2d48a6a8f4db17eff2d0c2\weekly-20260914-105045-20192.manifest.json -ComposeFile C:\Users\Felipe\Documents\Importantes\TFG\SavePoint\infra\compose.yaml -ApiUrl http://127.0.0.1:8000/health/` | exit 0 |
| Same-origin health | PASS | `GET http://127.0.0.1:3000/health/` | HTTP 200; sensitive markers absent |
| Secure headers | PASS | `GET http://127.0.0.1:3000/es` | HTTP 200; sensitive markers absent |

## Alcance protegido

- Artefacto publicado: evaluation-400-test-2026-09-12-v15, protocolo 15, corpus 2026.09.2, 400 usuarios solicitados, 79 evaluables y 16 algoritmos.
- El marker pps/api/.evaluation-test-run.json y las fuentes v15 se comparan antes/despuÃ©s; no se ejecuta ningÃºn comando de evaluaciÃ³n.
- Las credenciales locales son variables de proceso efÃ­meras; sus valores no se escriben en esta evidencia, trazas ni logs.
- El restore usa una base de datos desechable fuera de la base canÃ³nica y elimina Ãºnicamente ese destino.

## Limitaciones y revisiÃ³n humana

El resultado automÃ¡tico no sustituye la revisiÃ³n del autor sobre el recorrido visual en espaÃ±ol/inglÃ©s, el reflow a 320 px y 400 %, ni la adecuaciÃ³n legal de la redistribuciÃ³n. El paquete v15 sigue siendo evidencia de simulaciÃ³n con una sola ejecuciÃ³n publicada, no evidencia de usuarios reales.
