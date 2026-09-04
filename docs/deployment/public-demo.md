# Public demo deployment runbook

This runbook prepares a reversible deployment of the same Docker build context used locally. It does **not** authorize or prove that a public deployment exists. Creating paid resources is a blocking human decision.

## Proposed Render topology

`infra/render.yaml` declares two Docker web services and one managed PostgreSQL database in Frankfurt. The browser contacts only `savepoint-web`; its server-side `API_PROXY_TARGET` points to `savepoint-api`, preserving the application's same-origin cookie model. The API runs the idempotent chain `migrate -> import_catalogue -> bootstrap_demo_account -> seed_demo` as its pre-deploy command, then serves `/health/`. PostgreSQL has an empty public IP allowlist.

The Blueprint deliberately selects the smallest currently documented paid compute IDs (`0.5c-512mb` for each web service and `0.1c-256mb` for PostgreSQL), because Render documents `preDeployCommand` as a paid-service feature. Prices, taxes, quotas and regional availability are **not** encoded here and must be checked in the account's confirmation screen immediately before creation. As checked on 2026-09-04, Render documents Frankfurt as available, but regions cannot be changed in place.

Do not silently switch this Blueprint to `free`: Render currently documents that free web services suspend after 15 minutes idle and that free PostgreSQL expires after 30 days, has no backups, and can be restarted for maintenance. The local Compose environment remains the canonical reproducible fallback regardless of host behavior.

Authoritative provider references:

- <https://render.com/docs/blueprint-spec>
- <https://render.com/docs/deploys#pre-deploy-command>
- <https://render.com/docs/compute-plans>
- <https://render.com/docs/free>
- <https://render.com/docs/regions>

## Security contract

- `DJANGO_SECRET_KEY` is provider-generated; database credentials come from `fromDatabase`.
- `DEMO_USERNAME` and `DEMO_PASSWORD` are `sync: false`. Enter them only in Render's secret prompt. Never put them in Git, a build argument, logs, screenshots, chat, or test artifacts.
- `DJANGO_CSRF_TRUSTED_ORIGINS` is also prompted with `sync: false` because Render Blueprints expose private `host`/`hostport`, not another service's public URL. Enter exactly the final `https://<web-host>` origin (no path).
- Demo credentials are read server-side by Django only. The web service receives no credential variable, and no `NEXT_PUBLIC_*` secret exists.
- Render supplies TLS for its public URLs. Record and test only the exact HTTPS web hostname; the deployed smoke rejects HTTP, credentials in URLs, redirects to another host, and a revision mismatch.
- `autoDeployTrigger: checksPass` prevents unreviewed pushes from becoming the public demo automatically.

## Authorization and creation

Before creating anything, the owner must review the live Render confirmation screen and explicitly approve provider, region, monthly estimate, suspension/retention behavior and teardown responsibility.

1. Push the exact commit intended for the demo and ensure required repository checks are green.
2. In Render, create a Blueprint from this repository and choose `infra/render.yaml` as the Blueprint path.
3. Confirm all three proposed resources, their Frankfurt region and their displayed recurring cost. Abort if any differs from the reviewed contract.
4. Supply strong, unique values for `DEMO_USERNAME` and `DEMO_PASSWORD`, plus the exact public web origin for `DJANGO_CSRF_TRUSTED_ORIGINS`, in the prompt. Do not copy credential values into this document.
5. Wait for the database and API pre-deploy command, API healthcheck and web healthcheck to succeed.
6. Record the non-secret evidence below, then run the smoke locally with secrets supplied through the process environment:

```powershell
$env:BASE_URL = "https://<approved-web-host>"
$env:EXPECTED_COMMIT = "<full-deployed-commit-sha>"
$env:DEMO_USERNAME = "<runtime-secret>"
$env:DEMO_PASSWORD = "<runtime-secret>"
corepack pnpm exec playwright test e2e/deployed-smoke.spec.ts --project=chromium
```

Clear the four process variables after the run. Do not upload traces from a failed authentication run until they have been reviewed for sensitive request metadata.

## Deployment evidence (must be completed after authorization)

| Field | Value |
|---|---|
| Provider | PENDING HUMAN AUTHORIZATION |
| Public HTTPS URL | PENDING |
| Allowlisted host | PENDING |
| Deployed Git commit | PENDING |
| UTC smoke time/result | PENDING |

Any `PENDING` field or a red smoke blocks completion of OPS-01 and the following wave.

## Rotation, rollback and teardown

To rotate the demo identity, update `DEMO_USERNAME` and `DEMO_PASSWORD` in the API service's Environment page and choose a deploy option that reruns the pre-deploy chain. The bootstrap command updates the controlled demo account idempotently and never prints the values. Verify a fresh login, then invalidate any old operator-side copies.

For an application regression, use Render's deploy history to roll back both services to the same known-good commit, verify that migrations remain backward-compatible, and rerun the deployed smoke with that commit as `EXPECTED_COMMIT`. If schema rollback is unsafe, restore into a new database from an owner-approved backup/export; never guess or run a destructive reverse migration against the only copy.

For teardown, first export any evidence or data the thesis needs, then delete the web service, API service and database from the Blueprint/dashboard and verify billing has stopped. Disconnecting or deleting the Blueprint alone does not necessarily delete managed resources. Local Compose plus committed datasets remains the recovery path.

## Equivalent-PaaS fallback

Another Docker PaaS is acceptable only after an explicit owner decision and only if it supplies: managed TLS; two services built from these exact Dockerfiles and repository context; private or authenticated service-to-service routing; managed PostgreSQL; secret runtime variables; an ordered, fail-closed pre-release job; healthchecks; immutable commit identification; logs; rollback; and documented teardown/cost/retention. Record the provider-specific mapping and rerun the identical smoke. Architectural substitutions or a live external catalogue API are out of scope.
