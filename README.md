# SavePoint

[![Quality gates](https://github.com/felpennun/SavePoint/actions/workflows/quality-gates.yml/badge.svg)](https://github.com/felpennun/SavePoint/actions/workflows/quality-gates.yml)

**SavePoint** es una aplicación web para llevar la colección y los pendientes de videojuegos, al estilo de Goodreads o
Letterboxd, y es también un banco de pruebas reproducible para sistemas de recomendación. Es el Trabajo Fin de Grado de
Felipe Peña Núñez (Universidad de Sevilla, ETSII).

- **Aplicación:** catálogo de más de 190.000 obras gobernadas procedentes de IGDB, biblioteca personal con copias físicas y
  digitales, listas, comentarios, perfiles con privacidad, amistades y recomendaciones, en español e inglés, con tema claro y
  oscuro, accesible y adaptada a escritorio y móvil.
- **Investigación:** dieciséis algoritmos de recomendación (de referencia, basados en contenido, filtrado colaborativo e
  híbridos con diversidad) comparados con un protocolo de evaluación offline fijo, con usuarios sintéticos, semillas y
  resultados versionados.
- **Memoria:** [`TFG/TFG.pdf`](TFG/TFG.pdf) (fuentes LaTeX en [`TFG/`](TFG/)).

## Demo en línea

**<https://save-point-orpin.vercel.app>**

Puedes registrarte con tu propia cuenta o entrar con una de las cuentas de demostración:

| Usuario | Contraseña |
|---|---|
| `demo_user` | `demo_user123` |
| `demo_user2` | `demo_user123` |
| `demo_user3` | `demo_user123` |

Notas sobre el despliegue público:

- Usa niveles gratuitos (Vercel para la web, Render para la API y Neon para PostgreSQL). Tras un rato sin visitas la API se
  duerme y **la primera carga puede tardar hasta un minuto**.
- Publica un **subconjunto del catálogo** (unos 32.500 juegos y 10.700 contenidos adicionales) porque el corpus completo no
  cabe en el nivel gratuito de la base de datos. El entorno local reproduce el flujo completo.
- Las cuentas de demostración son de uso libre y no contienen datos personales. Las sesiones se cierran tras 30 minutos sin
  actividad.

## Qué puedes hacer

- **Catálogo:** búsqueda y filtros por plataforma, género, año y valoración, con ficha detallada de cada juego.
- **Colección:** estado de cada juego (pendiente, jugando, completado, abandonado), valoración por medias estrellas,
  copias físicas y digitales con metadatos de edición, comentarios, favoritos y listas propias con orden manual.
  Importación desde un fichero y exportación a CSV y XLSX.
- **Recomendaciones:** estanterías de juegos recomendados por varios algoritmos, con vista detallada que explica por qué se
  recomienda cada uno y con qué pesos.
- **Social:** perfiles públicos con privacidad configurable, solicitudes de amistad, recomendaciones entre amigos y mensajes.

## Arranque local

### Requisitos

- [Git](https://git-scm.com/) y [Docker](https://www.docker.com/) con Compose v2 (Docker Desktop en Windows y macOS).
- Unos 6 GB de disco para las imágenes y la base de datos (unos 12 GB si restauras el paquete de datos completo) y puertos libres: `3000` (web) y `8000` (API). Probado en
  Windows 11 con Docker Desktop.

### Descargar e iniciar

```sh
git clone https://github.com/felpennun/SavePoint.git
cd SavePoint
docker compose -f infra/compose.yaml up --build --wait
```

La primera vez construye las imágenes y tarda varios minutos. Después de `up --wait`:

- Web: <http://localhost:3000/es> (o `/en`).
- API: <http://localhost:8000> (comprobación de salud en `/health/`).

En el arranque la API aplica las migraciones, importa el catálogo base congelado de `data/` y lo publica en el catálogo,
crea las cuentas de demostración y siembra sus interacciones, y solo entonces arranca la web. Las cuentas locales son:

| Usuario | Contraseña |
|---|---|
| `demo-visitor` | `SavePoint-Demo-2026-Visit!` |
| `demo-critico` | `SavePoint-Demo-2026-Critico!` |
| `demo-coleccionista` | `SavePoint-Demo-2026-Coleccion!` |

Son credenciales de demostración que solo existen en tu entorno local.

El catálogo local arranca con el **catálogo base congelado (150 juegos de Wikidata)**, suficiente para recorrer la
aplicación: catálogo, fichas, colección, listas y amistades. Las recomendaciones y las sinopsis en español necesitan el corpus
completo de IGDB, que no se incluye en el repositorio: se importa con tus propias credenciales de Twitch
(`IGDB_CLIENT_ID` e `IGDB_CLIENT_SECRET`) mediante `import_igdb_catalogue`, bajo las condiciones descritas en
[`docs/adr/ADR-006-igdb-source.md`](docs/adr/ADR-006-igdb-source.md).

### Catálogo completo y cuentas demo (paquete de datos)

La [release v1.0.0](https://github.com/felpennun/SavePoint/releases/tag/v1.0.0) incluye `savepoint-demo-data-v1.0.0.dump`
(430 MB) y su suma de verificación. Es un volcado de PostgreSQL con el **catálogo completo** (190.479 obras gobernadas y
331.000 registros contando contenidos adicionales), los datos que usan las recomendaciones y tres cuentas demo (`demo_user1`
tiene una biblioteca amplia y sus recomendaciones ya generadas).
No contiene ningún otro usuario ni dato personal.

| Usuario | Contraseña |
|---|---|
| `demo_user1` | `demo_user123` |
| `demo_user2` | `demo_user123` |
| `demo_user3` | `demo_user123` |

Con el repositorio ya clonado, descarga el paquete y su `.sha256` en la carpeta del proyecto y restáuralo (**sustituye el
contenido de la base de datos local** y tarda unos minutos):

```sh
sh scripts/restore-demo-data.sh savepoint-demo-data-v1.0.0.dump                                      # Linux, macOS y Git Bash
powershell -ExecutionPolicy Bypass -File scripts/restore-demo-data.ps1 -Dump savepoint-demo-data-v1.0.0.dump   # Windows
```

El script comprueba la suma de verificación, para la aplicación, recrea la base de datos, restaura el paquete y vuelve a
arrancarlo todo. Las cuentas `demo-visitor`, `demo-critico` y `demo-coleccionista` se siguen creando en cada arranque.

### Parar, reiniciar y empezar de cero

```sh
docker compose -f infra/compose.yaml down        # para los contenedores y conserva los datos
docker compose -f infra/compose.yaml up --wait   # los vuelve a arrancar
docker compose -f infra/compose.yaml down -v     # lo borra todo, incluida la base de datos
```

### Si algo falla

- **Windows:** si `git clone` informa de que no puede crear algún fichero por la longitud de la ruta, clona en una carpeta
  más corta o ejecuta `git config --global core.longpaths true`.
- **Puertos ocupados:** cambia los puertos publicados de `api` y `web` en `infra/compose.yaml`.
- **Comprobar que funciona:** `curl http://localhost:8000/health/` debe responder `{"status": "ok", ...}` y
  `curl -I http://localhost:3000/es` debe responder `200`.

## Pruebas

```sh
docker compose -f infra/compose.yaml run --rm api pytest apps/api -q                 # API (más de 800 pruebas)
docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test --run     # web (Vitest)
```

Los recorridos de extremo a extremo (Playwright, en [`e2e/`](e2e/)) necesitan la pila arrancada, `corepack pnpm install` y las
variables `DEMO_USERNAME` y `DEMO_PASSWORD` de una cuenta de demostración.

El flujo de integración continua ([`quality-gates.yml`](.github/workflows/quality-gates.yml)) levanta la pila y ejecuta las
comprobaciones de dependencias y de secretos, las comprobaciones de producción de Django, la verificación de migraciones y las
pruebas de seguridad de la API.

## Tecnologías

| Capa | Tecnología |
|---|---|
| API | Python 3.13, Django 5.2 LTS y Django REST Framework 3.18 |
| Base de datos | PostgreSQL 18 |
| Web | Next.js 16, React 19, TypeScript 6 y Tailwind CSS 4 (Node 24) |
| Recomendación y evaluación | NumPy y SciPy, con métricas implementadas a mano y verificadas |
| Pruebas | pytest, Vitest, Playwright y axe-core |
| Contenedores y despliegue | Docker Compose en local; Vercel (web), Render (API) y Neon (PostgreSQL) en producción |

La web habla con la API únicamente a través del proxy del mismo origen de Next.js (`apps/web/next.config.ts`), de modo que el
navegador solo ve un origen y las cookies de sesión no cruzan dominios.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| [`apps/web/`](apps/web/) | Aplicación Next.js (interfaz, componentes, internacionalización) |
| [`apps/api/`](apps/api/) | API Django: catálogo, cuentas, biblioteca, social, recomendaciones y evaluación |
| [`infra/`](infra/) | `compose.yaml` (entorno local) y `render.yaml` (despliegue de la API) |
| [`data/`](data/) | Catálogo base congelado, manifiestos, interacciones de demostración y sinopsis en español |
| [`e2e/`](e2e/) | Pruebas de extremo a extremo con Playwright |
| [`scripts/`](scripts/) | Pasarelas de seguridad y dependencias, copia de seguridad, corpus público y auditoría móvil |
| [`docs/`](docs/) | Decisiones de arquitectura, metodología, despliegue y verificación por fase |
| [`TFG/`](TFG/) | Memoria del Trabajo Fin de Grado (LaTeX y PDF) |
| [`design/`](design/) | Imágenes de los mockups de diseño |
| [`.planning/`](.planning/) y [`ideas-vault/`](ideas-vault/) | Planificación por fases y notas del proyecto, evidencia del método de trabajo |

## Documentación

- Memoria: [`TFG/TFG.pdf`](TFG/TFG.pdf).
- Decisiones de arquitectura: [`docs/adr/`](docs/adr/).
- Protocolo de evaluación: [`docs/methodology/evaluation-protocol.md`](docs/methodology/evaluation-protocol.md) y algoritmos:
  [`docs/methodology/recommendation-algorithms.md`](docs/methodology/recommendation-algorithms.md).
- Método de trabajo con agentes de IA: [`docs/methodology/agent-method.md`](docs/methodology/agent-method.md) y
  [`docs/methodology/ai-use-disclosure.md`](docs/methodology/ai-use-disclosure.md).
- Copias de seguridad y recuperación: [`docs/deployment/backup-recovery.md`](docs/deployment/backup-recovery.md).
- Convenciones y contribución: [`CONVENTIONS.md`](CONVENTIONS.md) y [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Datos y atribuciones

- **Catálogo base (`data/raw/`, `data/manifests/`):** 150 juegos de [Wikidata](https://www.wikidata.org/wiki/Wikidata:Licensing)
  (licencia CC0 1.0) y los metadatos, con su licencia, de las imágenes de Wikimedia Commons que acompañan al catálogo. El
  repositorio no redistribuye esas imágenes.
- **Catálogo completo:** los metadatos estructurados de las más de 190.000 obras proceden de
  [IGDB.com](https://www.igdb.com/) (Twitch), consultados a través de su API con las condiciones documentadas en
  [`docs/adr/ADR-006-igdb-source.md`](docs/adr/ADR-006-igdb-source.md). No se versiona en Git ningún volcado de IGDB; el
  paquete de datos de la release incluye el catálogo únicamente con fines académicos de evaluación del trabajo, con atribución
  a IGDB.com. Las portadas se enlazan desde su origen. Las capturas de la memoria y de los mockups muestran portadas solo como ilustración.
- **Sinopsis en español (`data/localization/summaries-es.json`):** 1.898 sinopsis traducidas con Claude a partir de las
  sinopsis en inglés de IGDB. El texto original pertenece a sus autores y a IGDB; la traducción es una obra derivada
  incluida para que la demostración bilingüe funcione.

## Método de desarrollo

SavePoint se ha desarrollado con asistentes de IA (Codex y Claude Code) siguiendo el método **Get Stuff Done (GSD)**:
<https://github.com/gsd-build/get-shit-done> (versión 1.12.0). El repositorio no incluye los ficheros que GSD instala en cada
equipo (comandos, agentes, hooks) ni las instrucciones locales de cada asistente; las reglas del proyecto están reunidas en
[`CONVENTIONS.md`](CONVENTIONS.md), y la memoria del TFG explica cómo se aplicó el método y qué controles se pusieron.

## Autoría

Trabajo Fin de Grado del Grado en Ingeniería Informática - Ingeniería del Software, Universidad de Sevilla (ETSII,
Departamento de Lenguajes y Sistemas Informáticos).

- **Autor:** Felipe Peña Núñez
- **Dirección:** José Enrique Sánchez López y Aitor Rodríguez Dueñas
