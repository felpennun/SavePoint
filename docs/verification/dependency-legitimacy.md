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
| Next.js 16.2.12 | SSR, rutas y metadatos de portada/perfiles con UI React interactiva. Se mantiene la línea 16.2 investigada, no el major más reciente. | Django+HTMX simplifica despliegue pero limita el dashboard futuro; SPA pura empeora páginas públicas y duplicaría decisiones de routing. | Requiere Node >=20.9; repositorio oficial de Vercel confirmado en npm. | [npm](https://www.npmjs.com/package/next), [proyecto](https://github.com/vercel/next.js) |
| React / React DOM 19.2.7 | Componentes accesibles compartidos y modelo declarativo estable compatible con Next 16.2. | Vue/Svelte serían válidos, pero romperían la integración y el material investigado. | Ambos paquetes proceden del repositorio oficial React y se fijan a la misma patch. | [React](https://react.dev/versions), [npm react](https://www.npmjs.com/package/react) |
| TypeScript 6.0.3 | Contratos estrictos para estados, DTO y bilingüismo; reduce fallos de integración. | JavaScript acelera el inicio, pero desplaza errores al runtime y debilita la documentación técnica. | Se evita TypeScript 7 para no introducir un cambio mayor no evaluado; origen Microsoft verificado. | [npm](https://www.npmjs.com/package/typescript), [proyecto](https://github.com/microsoft/TypeScript) |
| Tailwind CSS / PostCSS 4.3.3 | Tokens sustituibles y layout adaptativo sin incorporar un kit visual opaco. | CSS Modules reduce tooling; un component kit acelera pantallas pero dificulta justificar identidad y accesibilidad. | Paquetes oficiales de Tailwind con igual patch; superficie limitada a build. | [Tailwind](https://tailwindcss.com/), [npm](https://www.npmjs.com/package/tailwindcss) |

## Backend, persistencia y pruebas

| Tecnología exacta | Finalidad y razón de elección | Alternativas y consecuencias | Compatibilidad y riesgo de suministro | Evidencia oficial |
|---|---|---|---|---|
| Python 3.13.7 | Unifica backend y futuros experimentos de recomendación conservando compatibilidad de wheels. | 3.14 es el host disponible, pero no se usa para resolver el entorno; 3.13 reduce riesgo científico. | Imagen oficial fijada por digest y restricción `==3.13.*`. | [Python](https://www.python.org/), `python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689` |
| uv 0.12.9 | Resolución rápida y lock universal con versión de herramienta fijada. | pip-tools es maduro, pero separa más pasos; Poetry impone empaquetado innecesario. | PyPI declara Python >=3.8; el propio `pyproject.toml` exige esta versión exacta. | [PyPI](https://pypi.org/project/uv/), [proyecto](https://github.com/astral-sh/uv) |
| Django 5.2.17 LTS | ORM, migraciones, sesiones, CSRF, validación y admin para un dominio CRUD relacional. | FastAPI ofrece una API ligera, pero obliga a ensamblar auth/admin/ORM; Django 6 no es LTS acordada. | PyPI confirma Python >=3.10 y enlaces oficiales; se conserva la LTS investigada. | [PyPI](https://pypi.org/project/Django/), [Django](https://www.djangoproject.com/download/) |
| Django REST Framework 3.18.0 | Serialización, permisos y API coherentes con Django. | Django Ninja es más liviano, pero tiene menor continuidad con el diseño ya estudiado. | PyPI declara Python >=3.10; versión exacta compatible con Django 5.2. | [PyPI](https://pypi.org/project/djangorestframework/), [proyecto](https://www.django-rest-framework.org/) |
| psycopg[binary] 3.3.5 | Driver PostgreSQL actual con wheel reproducible para desarrollo/CI. | Compilación fuente reduce dependencia del wheel, pero exige toolchain del sistema. | Extra explícito; lock captura `psycopg-binary`; no se deserializan artefactos externos. | [PyPI](https://pypi.org/project/psycopg/), [proyecto](https://www.psycopg.org/) |
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
