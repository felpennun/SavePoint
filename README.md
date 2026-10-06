# SavePoint

SavePoint es una aplicación web enfocada en el registro y seguimiento personal de videojuegos. Permite a los usuarios llevar un historial de sus partidas, calificar títulos, registrar el tiempo jugado y organizar su lista de juegos pendientes (backlog). Desarrollado como proyecto académico/tesis.

## Método de desarrollo

SavePoint se ha desarrollado con asistentes de IA (Claude Code, Codex y GitHub Copilot) siguiendo el método
**Get Stuff Done (GSD)**: <https://github.com/gsd-build/get-shit-done> (versión 1.12.0). El repositorio no incluye
los ficheros que GSD instala en cada equipo (comandos, agentes, hooks) ni las instrucciones locales de cada
asistente; las reglas del proyecto están reunidas en [`CONVENTIONS.md`](CONVENTIONS.md) y la memoria del TFG
(carpeta [`TFG/`](TFG/)) explica cómo se aplicó el método y qué controles se pusieron.

## Arranque local (Docker Compose)

**Entorno probado:** Windows 11 (build 26200), Docker Desktop, PostgreSQL 18.6 vía imagen oficial. `docker compose` construye `db`, `api` y `web` desde el mismo `pyproject.toml`/`uv.lock` y `package.json`/`pnpm-lock.yaml` que se usan en despliegue — ningún paso de build descarga datos de catálogo ni llama a un proveedor externo; el catálogo, las imágenes de portada referenciadas y las interacciones de la demo son artefactos locales versionados bajo `data/`.

```sh
docker compose -f infra/compose.yaml up --build --wait
```

Esto:

1. Construye las tres imágenes (`db` es oficial, `api`/`web` son multi-stage y corren como usuario no-root).
2. Levanta PostgreSQL y espera su healthcheck.
3. En `api`, ejecuta en orden fijo: `migrate` → `import_catalogue` (carga el snapshot congelado de `data/`) → `bootstrap_demo_account` (crea/rota la cuenta demo desde `DEMO_USERNAME`/`DEMO_PASSWORD`) → `seed_demo` (carga las interacciones deterministas de `data/demo/seed-v1.json`) → arranca el servidor. Los cuatro comandos son idempotentes: repetir `up` no duplica filas ni deja estado parcial.
4. Espera el healthcheck de `api` (`GET /health/`) antes de arrancar `web`.
5. En `web`, ejecuta `next build` seguido de `next start` (build de producción, no `next dev` — ver nota en `infra/compose.yaml`) y espera su propio healthcheck.

Cuando el comando termina, `web` está en <http://localhost:3000/es> (o `/en`) y `api` en <http://localhost:8000>. La UI habla con `api` únicamente a través del proxy same-origin de Next.js (`next.config.ts`); el navegador nunca hace una petición cross-origin directa.

**Apagar la red externa** (por ejemplo, desconectando el host de Internet) después de `up --wait` no afecta el journey: catálogo, login, valoraciones, copias y perfiles públicos sólo leen PostgreSQL local.

## Configuración

Todas las variables de entorno están documentadas en [.env.example](.env.example) — solo nombres y valores locales inocuos, nunca credenciales reales. `docker compose` las fija directamente en `infra/compose.yaml` para desarrollo local; para cualquier valor más allá de desarrollo local, usar `docker compose run -e VAR=valor` o el almacén de secretos de la plataforma de despliegue, nunca este repositorio.

- `DJANGO_DEPLOY_ENV` (`local` | `production`) selecciona el perfil de seguridad en `apps/api/config/settings.py`: `local` silencia únicamente las advertencias de `check --deploy` que son la guía documentada de Django para HTTP plano sin terminador TLS (HSTS, redirección SSL, cookies seguras); `production` exige esas protecciones y una `DJANGO_SECRET_KEY` de al menos 50 caracteres, sin excepción.
- `DEMO_USERNAME`/`DEMO_PASSWORD` son credenciales de demostración local, nunca una cuenta real (ver `CONVENTIONS.md`). Rotarlas: cambiar el valor y volver a ejecutar `bootstrap_demo_account`, que actualiza la cuenta ancla existente en vez de crear una nueva.

## Rotación de la cuenta demo

```sh
docker compose -f infra/compose.yaml run --rm \
  -e DEMO_USERNAME=nuevo-usuario -e DEMO_PASSWORD='nueva-contraseña-larga' \
  api python manage.py bootstrap_demo_account
```

## Verificación de salud

```sh
curl http://localhost:8000/health/   # {"status": "ok"}
curl http://localhost:3000/es        # 200, HTML de la homepage
```

## Gate de secretos

Antes de publicar cualquier artefacto (repositorio, build, imagen, log), ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-secrets.ps1
docker compose -f infra/compose.yaml run --rm api python manage.py check --deploy
```

`scripts/check-secrets.ps1` se autoverifica primero contra los canarios sintéticos de `e2e/fixtures/hostile.json` (si no los detecta, el escaneo real no es de fiar y el script falla) y después escanea, sin encontrar nada, cinco superficies: archivos rastreados por Git, el build estático de Next.js (`.next/static` y source maps), el historial/capas de las imágenes Docker construidas, logs capturados de `docker compose` y `.env.example` (que sólo debe contener nombres/valores inocuos). Ningún nombre sensible usa `NEXT_PUBLIC_*` ni un `ARG` de Docker.

## Pruebas

```sh
docker compose -f infra/compose.yaml run --rm api pytest apps/api -q
corepack pnpm exec playwright test e2e/ --project=chromium
corepack pnpm --dir apps/web test --run
```
