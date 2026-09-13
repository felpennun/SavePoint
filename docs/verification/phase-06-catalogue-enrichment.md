# Evidencia de catálogo y enriquecimiento — Fase 6

**Fecha:** 2026-09-13  
**Plan:** `06-09` · **Issue:** #58  
**Alcance:** gate PostgreSQL, migraciones, regresión API, dependencias, secretos y
preservación de snapshots de investigación.

## Resultado del gate

El gate se ejecutó contra el servicio `api` de `infra/compose.yaml`, conectado al
servicio `db`. PostgreSQL respondió `18.6 (Debian 18.6-1.pgdg13+2)`, Django usa únicamente
el backend PostgreSQL y no hay operaciones de migración pendientes.

| Comprobación | Resultado reproducible |
|---|---|
| `manage.py check` | `System check identified no issues (0 silenced)` |
| `migrate --noinput` | `No migrations to apply` |
| `migrate --plan` | `No planned migration operations` |
| `makemigrations --check --dry-run` | `No changes detected` |
| `pytest apps/api/tests -q` | `43 passed` |
| `pytest apps/api/tests/test_phase6_postgres.py -q` | `5 passed` |
| `scripts/check-dependencies.ps1` | `PASS` — allowlist y referencias OCI inmutables válidas |
| `scripts/check-secrets.ps1` | `PASS` — cuatro superficies escaneadas, sin coincidencias no permitidas |

El sentinel `apps/api/tests/test_phase6_postgres.py` comprueba el servidor 18.6, la
cadena de migraciones de cuentas, catálogo, biblioteca y social, tablas de las
proyecciones protegidas, constraints e índices de autorización/cooldown, y un plan de
migración vacío. La comprobación de hashes no carga datos en la base ni ejecuta ningún
runner de evaluación.

## Integridad de investigación y procedencia

Se conservaron las siguientes entradas locales. El valor es el SHA-256 del fichero tal
como estaba antes y después del gate; no se incluyen filas, credenciales ni logs.

| Fichero | SHA-256 |
|---|---|
| `data/raw/wikidata-games.json` | `a2b5d8d1f4388b21a03a5c3c983840e38db2c5e176613913985a5e38f7408159` |
| `data/manifests/catalogue.json` | `8b1e3ea49090dd25fbff5a4a36fb284b9d7f5fd9170c85886b5979dcd7cc6f47` |
| `data/manifests/assets.json` | `7950a0125cbefdba092711ef1e6e879d97d04506492a0313a5ac6596f5eeeb5f` |
| `apps/api/corpus-governance-2026.09.2.json` | `fd762e4895571f2b11daf182a43a4ac647f7c8070c7261399ddba636441f86e8` |
| `apps/api/corpus-ratings-2026.09.2.json` | `6a8d3bdd7c2a0f2b6bec51035dfd47ed82bbebba124bfaa6ba381a66f9531b53` |
| `apps/api/corpus-popularity-2026.09.2.json` | `8bbc9ba9b87dbcb0637a1c2439a3a49cbc142bba6c2bfcf06a3d28ef4be69592` |
| `apps/api/feature-vector-cache-2026.09.2.json` | `2b7699171b3295214db117ab2f4486cfbec9a1e0d12a66e24faba33f982872d7` |

No se relanzó la evaluación offline congelada. Tampoco se realizaron llamadas a IGDB,
RAWG ni a otro proveedor externo durante una petición HTTP; el catálogo y sus facets se
sirven desde PostgreSQL y los snapshots aprobados locales.

## Comandos de reconstrucción

Desde la raíz del repositorio, con Docker Compose y el servicio `db` saludable:

```text
docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py check
docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput
docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --plan
docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run
docker compose -f infra/compose.yaml run --rm api pytest apps/api/tests -q
powershell -ExecutionPolicy Bypass -File scripts/check-dependencies.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-secrets.ps1
```

La evidencia social/browser está separada en `phase-06-signoff.md`; este documento no
pretende convertir una prueba de contrato o una limitación de navegador en una medición
del corpus.
