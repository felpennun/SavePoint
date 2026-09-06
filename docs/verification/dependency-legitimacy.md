# Verificación de legitimidad y decisión tecnológica

**Fecha de verificación:** 2026-09-04  
**Decisión humana:** Felipe autorizó explícitamente el conjunto delimitado con el mensaje `dependencias aprobadas`.  
**Trabajo del agente:** consulta reproducible de registros, propuesta razonada, resolución de locks y comprobaciones automáticas.  
**Límite de la aprobación:** cualquier dependencia directa nueva, cambio de versión o imagen distinta exige repetir el gate humano.

Este registro desarrolla la investigación de [01-RESEARCH.md](../../.planning/phases/01-three-day-public-demo-slice/01-RESEARCH.md). Los ADR formales y su trazabilidad completa se consolidarán en el Plan 01-13.

## Criterios de selección

Se priorizan soporte mantenido, adecuación al dominio relacional, reproducibilidad, seguridad por defecto, documentación oficial y una curva razonable para un TFG individual. Las versiones son exactas: los lockfiles fijan además todas las dependencias transitivas. No se emplean secretos para resolverlas.

## Aplicación web y frontend

| Tecnología exacta | Finalidad y razón de elección | Alternativas y consecuencias | Compatibilidad y riesgo de suministro | Evidencia oficial |
|---|---|---|---|---|
| Node.js 24.13.0 | Runtime LTS común para construir y servir Next.js. Reduce diferencias entre desarrollo, CI y despliegue. | Node 22 sería más conservador, pero 24 satisface el motor declarado por Vitest 5 y la línea acordada. | Imagen fijada por digest; ejecutar dependencias con scripts mínimos y lock congelado. | [nodejs.org](https://nodejs.org/), `node:24.13.0-slim@sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f` |
| pnpm 11.25.0 | Gestor reproducible, estricto y eficiente; un único lock para el workspace. | npm reduce herramientas, pero pnpm detecta mejor dependencias fantasma. | Paquete oficial `pnpm`, motor Node >=22.13; `packageManager` exacto. | [npm](https://www.npmjs.com/package/pnpm), [proyecto](https://github.com/pnpm/pnpm) |
| Next.js 16.3.4 | SSR, rutas y metadatos de portada/perfiles con UI React interactiva. Es la corrección estable más próxima dentro del major 16 autorizada tras detectar vulnerabilidades en 16.2.12. | Conservar 16.2.12 incumplía el umbral de seguridad; una versión canary/preview no es apropiada para producción; cambiar de major o de framework ampliaría el riesgo y el alcance. | Requiere Node >=20.9; npm confirma el repositorio oficial de Vercel, el tag estable `latest` y la integridad `sha512-/Ztf6CeRH+ejEXUrYtqI4gkS66eFIHuSwqi60RgcpWKodxFZx2/dqVCMKBwILfAHXQ+F1b1vAudgj3mnxqtoIA==`. | [npm](https://www.npmjs.com/package/next/v/16.3.4), [proyecto](https://github.com/vercel/next.js), [avisos](https://github.com/vercel/next.js/security/advisories) |
| React / React DOM 19.2.7 | Componentes accesibles compartidos y modelo declarativo estable compatible con Next 16.3. | Vue/Svelte serían válidos, pero romperían la integración y el material investigado. | Ambos paquetes proceden del repositorio oficial React y se fijan a la misma patch. | [React](https://react.dev/versions), [npm react](https://www.npmjs.com/package/react) |
| TypeScript 6.0.3 | Contratos estrictos para estados, DTO y bilingüismo; reduce fallos de integración. | JavaScript acelera el inicio, pero desplaza errores al runtime y debilita la documentación técnica. | Se evita TypeScript 7 para no introducir un cambio mayor no evaluado; origen Microsoft verificado. | [npm](https://www.npmjs.com/package/typescript), [proyecto](https://github.com/microsoft/TypeScript) |
| Tailwind CSS / PostCSS 4.3.3 | Tokens sustituibles y layout adaptativo sin incorporar un kit visual opaco. | CSS Modules reduce tooling; un component kit acelera pantallas pero dificulta justificar identidad y accesibilidad. | Paquetes oficiales de Tailwind con igual patch; superficie limitada a build. | [Tailwind](https://tailwindcss.com/), [npm](https://www.npmjs.com/package/tailwindcss) |
| @neon/config / @neon/env 1.2.0 | Configuración declarativa versionada de la rama Neon y lectura validada de sus variables; en esta fase se usa `defineConfig` y las credenciales siguen fuera de Git. | Configuración manual sólo en panel evita dependencias, pero pierde reconciliación reproducible; SDK directo ampliaría superficie innecesariamente. | Paquetes oficiales `@neon/*`, versión exacta en catálogo estricto y lock; requieren Node >=20.19. El autor autorizó su instalación durante el setup Neon. | [Neon config](https://neon.com/docs/reference/neon-cli), [npm config](https://www.npmjs.com/package/@neon/config), [npm env](https://www.npmjs.com/package/@neon/env) |

## Backend, persistencia y pruebas

| Tecnología exacta | Finalidad y razón de elección | Alternativas y consecuencias | Compatibilidad y riesgo de suministro | Evidencia oficial |
|---|---|---|---|---|
| Python 3.13.7 | Unifica backend y futuros experimentos de recomendación conservando compatibilidad de wheels. | 3.14 es el host disponible, pero no se usa para resolver el entorno; 3.13 reduce riesgo científico. | Imagen oficial fijada por digest y restricción `==3.13.*`. | [Python](https://www.python.org/), `python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689` |
| uv 0.12.9 | Resolución rápida y lock universal con versión de herramienta fijada. | pip-tools es maduro, pero separa más pasos; Poetry impone empaquetado innecesario. | PyPI declara Python >=3.8; el propio `pyproject.toml` exige esta versión exacta. | [PyPI](https://pypi.org/project/uv/), [proyecto](https://github.com/astral-sh/uv) |
| Django 5.2.17 LTS | ORM, migraciones, sesiones, CSRF, validación y admin para un dominio CRUD relacional. | FastAPI ofrece una API ligera, pero obliga a ensamblar auth/admin/ORM; Django 6 no es LTS acordada. | PyPI confirma Python >=3.10 y enlaces oficiales; se conserva la LTS investigada. | [PyPI](https://pypi.org/project/Django/), [Django](https://www.djangoproject.com/download/) |
| Django REST Framework 3.18.0 | Serialización, permisos y API coherentes con Django. | Django Ninja es más liviano, pero tiene menor continuidad con el diseño ya estudiado. | PyPI declara Python >=3.10; versión exacta compatible con Django 5.2. | [PyPI](https://pypi.org/project/djangorestframework/), [proyecto](https://www.django-rest-framework.org/) |
| psycopg[binary] 3.3.5 | Driver PostgreSQL actual con wheel reproducible para desarrollo/CI. | Compilación fuente reduce dependencia del wheel, pero exige toolchain del sistema. | Extra explícito; lock captura `psycopg-binary`; no se deserializan artefactos externos. | [PyPI](https://pypi.org/project/psycopg/), [proyecto](https://www.psycopg.org/) |
| requests 2.34.2 | Cliente HTTP síncrono para el importador offline de IGDB (Plan 01.1-01, ADR-006). El backend no tenía cliente HTTP; `requests` es el estándar de facto y la base de los wrappers IGDB de terceros. | `httpx` y `urllib3` directo se consideraron; `requests` gana por madurez, superficie mínima y ausencia de necesidad async en un job por lotes reanudable. | PyPI declara `requires-python >=3.10`; release real de `psf/requests` publicada 2026-05-14 (wheel + sdist), `yanked: false`; transitivas `certifi`, `charset-normalizer`, `idna`, `urllib3` fijadas por `uv.lock`. | [PyPI](https://pypi.org/project/requests/2.34.2/), [proyecto](https://github.com/psf/requests) |
| gunicorn 23.0.0 | Servidor WSGI de producción para la API en Render. `manage.py runserver` (servidor de desarrollo de Django) estaba siendo el proceso desplegado — sin timeouts, sin reciclado de workers, con el autoreloader activo; explícitamente no soportado por Django para producción (hallazgo H-03 de la revisión de repo 2026-09-06). Solo cambia `apps/api/render-start.sh`; Compose local sigue con `runserver`. | `uvicorn`/`waitress`/`daphne` se consideraron; `gunicorn` gana por ser el WSGI de producción de referencia para Django, sincrónico (encaja con el ORM y `pg_advisory_xact_lock`), configuración mínima y huella de memoria compatible con Render Free. | PyPI declara `requires-python >=3.7`; licencia MIT; release `23.0.0` (2024, wheel + sdist), `yanked: false`; única transitiva nueva `packaging` fijada por `uv.lock`. | [PyPI](https://pypi.org/project/gunicorn/23.0.0/), [proyecto](https://github.com/benoitc/gunicorn) |
| PostgreSQL 18.6 | Integridad relacional, constraints, transacciones y búsqueda trigram para catálogo e inventario. | SQLite difiere en concurrencia/typing; MongoDB debilita relaciones. | Imagen oficial por digest; misma major/patch en local y pruebas. | [PostgreSQL](https://www.postgresql.org/docs/release/), `postgres:18.6@sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280` |
| pytest 9.1.1 / pytest-django 4.14.0 | Tests unitarios e integración real con Django/PostgreSQL. | unittest evita dependencias, pero ofrece fixtures y parametrización menos expresivas. | Ambos nombres y requisitos Python >=3.10 verificados en PyPI; plugins limitados a la allowlist. | [pytest](https://docs.pytest.org/), [pytest-django](https://pytest-django.readthedocs.io/) |
| Vitest 5.0.0 / Testing Library 16.3.3 | Pruebas rápidas de lógica/componentes centradas en conducta observable. | Jest es más veterano; Vitest comparte ecosistema moderno y soporta Node 24 explícitamente. | Vitest declara Node ^24; repositorios oficiales comprobados en npm. | [Vitest](https://vitest.dev/), [Testing Library](https://testing-library.com/) |
| Playwright 1.62.1 / axe-core 4.13.0 | Recorrido E2E multibrowser y auditoría automática de accesibilidad. | Cypress es válido, pero Playwright aporta tres motores y contenedor oficial alineado. | Paquetes Microsoft/Deque confirmados; navegador fijado con imagen correspondiente. | [Playwright](https://playwright.dev/), `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e` |

## Método y resultado verificable

1. Se consultaron metadatos públicos de npm y PyPI (nombre, versión, repositorio y motor/intérprete) el 2026-09-04.
2. Se consultaron los índices OCI oficiales con `docker buildx imagetools inspect`; los cuatro digests anteriores son los índices multiplataforma observados en esa fecha.
3. Se ejecutó un canary negativo con un nombre inexistente/no aprobado antes de aceptar el cierre del gate.
4. `pnpm-lock.yaml` y `uv.lock` se generan con gestores normales; no se editan manualmente.
5. `scripts/check-dependencies.ps1` falla ante dependencias directas fuera de la allowlist, versiones flotantes, ausencia de locks, divergencia de runtime o digests no documentados.

La verificación de legitimidad reduce el riesgo de *dependency confusion*, typosquatting y deriva, pero no demuestra ausencia absoluta de vulnerabilidades. Los planes posteriores deben añadir auditoría de vulnerabilidades, SBOM, actualización deliberada y CI con instalación congelada. La autoría de la decisión es humana; la evidencia y el primer borrador técnico son asistidos por agente y quedan sujetos a revisión del autor del TFG.

## Revisión de seguridad posterior al gate

**Fecha:** 2026-09-04. **Autorización humana:** el autor autorizó explícitamente actualizar Next.js a la versión estable parcheada más próxima, regenerar el lock y exigir cero vulnerabilidades altas.

La primera resolución con `next@16.2.12` produjo en `pnpm audit` tres vulnerabilidades altas y dos moderadas transitivas, asociadas al árbol que incluía `sharp` y `postcss`. Por el criterio de bloqueo de riesgos altos, ese lock provisional fue rechazado y nunca se aceptó como baseline. Se eligió `next@16.3.4` porque el registro oficial de npm lo publicaba como versión estable (`latest`) dentro del mismo major 16; se descartaron las variantes canary/preview y no fue necesario un cambio arquitectónico.

La decisión sigue un proceso reproducible: metadata oficial del registro, versión directa exacta, lock transitivo regenerado por pnpm 11.25.0, `pnpm audit --audit-level high`, y checker local de allowlist con pruebas negativas. El 2026-09-04 la auditoría del lock final terminó con código 0 y **0 críticas, 0 altas, 0 moderadas, 0 bajas y 0 informativas** sobre 169 dependencias resueltas. No fue necesario aceptar ni mitigar residualmente ninguna vulnerabilidad. Las pruebas negativas rechazan un paquete canary no aprobado y los formatos flotantes `latest`, caret, tilde y `x`; los locks conservan las versiones directas aprobadas.

### Evidencia exacta de la actualización

- Consulta: `npm view next@16.3.4 version dist.tarball dist.integrity repository engines --json` contra `registry.npmjs.org`.
- Origen: `https://registry.npmjs.org/next/-/next-16.3.4.tgz`, repositorio `https://github.com/vercel/next.js.git`.
- Integridad publicada: `sha512-/Ztf6CeRH+ejEXUrYtqI4gkS66eFIHuSwqi60RgcpWKodxFZx2/dqVCMKBwILfAHXQ+F1b1vAudgj3mnxqtoIA==`.
- Resolución: `corepack pnpm install --lockfile-only --ignore-scripts` con pnpm 11.25.0; los scripts de paquetes no se ejecutaron.
- Auditoría: `corepack pnpm audit --audit-level high --json`, código 0 y todas las severidades a cero.
- Alcance de autorización: únicamente el salto exacto `16.2.12` → `16.3.4`; no se añadieron paquetes directos ni overrides.

## Alta de `requests` para el importador IGDB (Plan 01.1-01)

**Fecha:** 2026-09-05. **Autorización humana:** el autor aprobó explícitamente el pin exacto `requests==2.34.2` con el mensaje de reanudación tras revisar la evidencia oficial de PyPI (`aprobado`).

- **Motivo:** el backend no tenía cliente HTTP; el importador offline y reanudable de IGDB (ADR-006, requisito DATA-04) lo necesita para hablar con `id.twitch.tv` y `api.igdb.com/v4`.
- **Evidencia oficial:** `https://pypi.org/project/requests/2.34.2/` — licencia Apache-2.0, `requires-python >=3.10`, `requests-2.34.2-py3-none-any.whl` y `requests-2.34.2.tar.gz` subidas el 2026-05-14, `yanked: false`, repositorio de origen `github.com/psf/requests`. La versión se verificó de forma independiente contra la API JSON canónica de PyPI el 2026-09-05 (HTTP 200 para la release exacta).
- **Nota sobre RESEARCH.md:** `01.1-RESEARCH.md` marcó `requests` como `SUS` únicamente por el hueco `unknown-downloads` del seam de legitimidad (dato de descargas ausente en el entorno), no por señal real; el historial de releases de `psf/requests` (100+ desde `0.2.0`) y la verificación PyPI de esta sesión lo confirman legítimo.
- **Resolución:** `python -m uv add "requests==2.34.2"` con uv 0.12.9 (versión exacta exigida por `pyproject.toml`); `uv.lock` regenerado por la herramienta, no editado a mano. Transitivas fijadas: `certifi==2026.7.22`, `charset-normalizer==3.5.1`, `idna==3.19`, `urllib3==2.7.0`.
- **Alcance de la autorización:** únicamente el paquete directo `requests==2.34.2`. Se rechazan explícitamente `django-allauth` y `dj-rest-auth` (la app `accounts` hecha a mano se extiende en su lugar, ver ADR-006 y RESEARCH.md *Alternatives Considered*).
- **Verificación:** `scripts/check-dependencies.ps1` (allowlist Python actualizada, `uv.lock` comprobado exacto) termina con código 0.

## Alta de `gunicorn` para el servidor de producción (revisión de repo 2026-09-06, hallazgo H-03)

**Fecha:** 2026-09-06. **Autorización humana:** el autor autorizó aplicar **la totalidad** de los hallazgos de seguridad de la revisión completa del repositorio (`docs/verification/repo-review-2026-09-06.md`) con el mensaje "quiero que apruebes todos en su totalidad". El hallazgo H-03 es, literalmente, "añadir `gunicorn` y dejar de usar `manage.py runserver` como proceso desplegado", de modo que esa autorización cubre este alta. La revisión previa de la ficha oficial de PyPI la hace el autor con este registro delante.

- **Motivo:** `apps/api/render-start.sh` ejecutaba `python manage.py runserver` como proceso de larga vida en Render. La documentación de Django lo prohíbe explícitamente para producción (sin auditoría de seguridad ni de rendimiento, sin timeouts de petición, sin reciclado de workers, autoreloader activo). Solo se toca el arranque de Render; Compose local sigue con `runserver` (aceptable, es solo local).
- **Evidencia oficial:** `https://pypi.org/project/gunicorn/23.0.0/` — licencia MIT, `requires-python >=3.7`, `gunicorn-23.0.0-py3-none-any.whl` y `gunicorn-23.0.0.tar.gz`, `yanked: false`, repositorio de origen `github.com/benoitc/gunicorn`. Proyecto con historial largo (release inicial 2010, decenas de versiones) y uso masivo como WSGI de referencia para Django.
- **Alternativas consideradas:** `uvicorn` (ASGI; el proyecto es WSGI síncrono, encaja mejor con el ORM y `pg_advisory_xact_lock`), `waitress` (puro-Python, menor cuota de uso en despliegues Django), `daphne` (ASGI, mismo desajuste). `gunicorn` gana por ser el estándar y por configuración mínima.
- **Resolución:** `python -m uv add "gunicorn==23.0.0"` con uv 0.12.9; `uv.lock` regenerado por la herramienta, no editado a mano. Única transitiva nueva: `packaging==26.3` (fijada por `uv.lock`).
- **Alcance de la autorización:** únicamente el paquete directo `gunicorn==23.0.0` y su transitiva `packaging`. Sin cambios en el resto del conjunto.
- **Comando de arranque:** `exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 30 --access-logfile - --error-logfile -`. Los cuatro pasos idempotentes previos (`migrate` / `import_catalogue` / `bootstrap_demo_account` / `seed_demo`) se conservan sin cambios y siguen siendo fail-closed.
- **Verificación:** `scripts/check-dependencies.ps1` (allowlist Python actualizada con `gunicorn==23.0.0`, `uv.lock` comprobado exacto) termina con código 0; `apps/api/tests/test_render_startup.py` actualizado y en verde; `python -c "import gunicorn"` + `gunicorn --version` dentro de la imagen reconstruida.
