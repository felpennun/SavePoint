# Runbook de despliegue de la demo pública

Este runbook prepara la topología pública aprobada por el propietario, de coste cero y sin tarjeta. **No** afirma que las cuentas o recursos ya existan. Docker Compose (`web` + `api` + PostgreSQL) sigue siendo el entorno reproducible canónico.

## Topología aprobada y frontera de paridad

| Superficie | Host público | Contrato |
|---|---|---|
| UI de navegador | Vercel Hobby | Construye nativamente el workspace Next.js bloqueado; proxea `/api/*` y `/health/` del lado del servidor hacia Render. |
| API | Render Free | Construye `apps/api/Dockerfile`, incluyendo el catálogo local congelado, y expone `/health/`. |
| Base de datos | Neon Free | Proyecto `autumn-breeze-06234770`, rama `production`; suministra PostgreSQL a Render como secreto de runtime. |

El navegador solo ve el origen HTTPS de Vercel. `API_PROXY_TARGET` existe únicamente en el entorno de servidor de Next.js, así que las cookies de sesión y CSRF de Django siguen siendo same-origin visibles por el navegador. El runtime público es funcional y de versión equivalente a Compose, pero deliberadamente **no** ejecuta la imagen Docker del frontend. Es una diferencia de despliegue documentada, no paridad de imagen bit a bit.

No se puede introducir ninguna tarjeta de pago ni habilitar ninguna función o recurso de pago. Si algún panel pide una tarjeta o muestra un precio recurrente distinto de cero, detente y desmonta los recursos incompletos.

## Limitaciones honestas del tier gratuito

Los límites de los proveedores cambian. Vuelve a comprobar las páginas oficiales enlazadas en el momento de la creación y registra lo que muestren los paneles.

- Render documenta que un servicio web gratuito duerme tras 15 minutos sin tráfico entrante; despertar puede tardar cerca de un minuto. Las cuotas mensuales de horas, ancho de banda o pipeline pueden suspenderlo o deshabilitarlo. Los servicios gratuitos no son para producción.
- Render Free no soporta `preDeployCommand`. Su override de Docker tokenizado como argv invoca solo `sh /workspace/apps/api/render-start.sh`; el script POSIX dentro de la imagen usa `set -eu`, ejecuta `migrate -> import_catalogue -> bootstrap_demo_account -> seed_demo` y luego hace `exec` del servidor HTTP. Todo comando de datos es idempotente y protegido con advisory lock; `numInstances: 1` impide que múltiples instancias de la aplicación inicialicen concurrentemente. Un paso fallido detiene el arranque, así que health nunca se pone en verde con inicialización parcial.
- No vuelvas a poner sintaxis `&&`, `${...}` ni `sh -c` anidado en `dockerCommand`: Render no evalúa ese campo como código de shell. El escaneo de fuente del despliegue protege la frontera del Blueprint, mientras que `apps/api/tests/test_render_startup.py` comprueba el orden fail-closed del script.
- Neon Free tiene límites de horas de cómputo, almacenamiento, proyectos y transferencia dependientes de la cuenta y puede suspender el cómputo ocioso. Confirma los valores actuales y la retención en el panel/docs de Neon; este runbook no promete durabilidad ni backup.
- Compose sigue disponible offline si cualquier tier gratuito público duerme, cambia los términos o desaparece.
- Vercel Hobby sobre un repositorio **privado** solo auto-despliega commits cuyo email de autor de Git GitHub vincula a la propia cuenta del propietario del proyecto. Un commit con un email verificado bajo una cuenta de GitHub *distinta* se bloquea silenciosamente ("the commit author did not have contributing access... Hobby Plan does not support collaboration for private repositories"), incluso cuando el nombre visible del committer coincide. Solución: fija el `user.email` local a la dirección noreply emitida por GitHub de la cuenta del propietario (`<user-id>+<username>@users.noreply.github.com`, siempre verificada y única de esa cuenta, obtenida de `gh api users/<username> --jq .id`) en vez de un email personal que podría estar verificado en otro sitio.

Referencias oficiales comprobadas 2026-09-04:

- <https://render.com/docs/free>
- <https://render.com/docs/blueprint-spec>
- <https://vercel.com/docs/plans/hobby>
- <https://vercel.com/docs/rewrites>
- <https://neon.com/docs/introduction/plans>

## Contrato de secretos y frontera de confianza

- Los datos de conexión de Neon, `DEMO_USERNAME`, `DEMO_PASSWORD` y `DJANGO_CSRF_TRUSTED_ORIGINS` son `sync: false` en Render y se introducen solo en las UIs de variables de entorno del proveedor.
- El `DATABASE_URL` de Render debe recibir el valor **directo/sin pooling** `DATABASE_URL_UNPOOLED` de Neon. La ruta de arranque ejecuta migraciones de esquema y operaciones de advisory lock que requieren una sesión real; una conexión con pooling de transacciones no es un endpoint de migración seguro. Esta demo controlada y pequeña usa deliberadamente esa misma URL directa en runtime en vez de almacenar dos secretos de base de datos.
- `DJANGO_SECRET_KEY` lo genera Render. Ningún secreto entra en Git, un argumento de build, logs, capturas, chat ni artefactos de test.
- En Render, fija `DJANGO_CSRF_TRUSTED_ORIGINS` al origen de producción exacto de Vercel, como `https://example.vercel.app`, sin ruta.
- En Vercel, fija el `API_PROXY_TARGET` solo-servidor al origen HTTPS exacto de Render. Nunca lo prefijes con `NEXT_PUBLIC_`.
- Render suministra `RENDER_GIT_COMMIT`; `/health/` devuelve esa revisión no secreta a través de Vercel para que el smoke pueda rechazar un despliegue obsoleto.
- El smoke rechaza HTTP, credenciales/ruta/query en `BASE_URL`, tráfico de navegador cross-origin, peticiones fallidas y un desajuste de revisión.

## Orden de creación manual (acción humana bloqueante)

El orden evita la configuración circular de origen público sin debilitar CSRF.

1. Haz push del commit candidato exacto y asegúrate de que los checks del repositorio están en verde.
2. Neon ya está preparado: proyecto `autumn-breeze-06234770`, rama `production`. `neon deploy` reconció la política `neon.ts` commiteada con éxito sin cambios, y las variables locales se descargaron solo en `.env.local` (ignorado). Copia la cadena de conexión directa/sin pooling de la rama directamente en el `DATABASE_URL` de Render; nunca la pegues en este repositorio ni en el chat.
3. En Render, crea un Blueprint desde `infra/render.yaml`. Confirma exactamente un servicio web `free` en Frankfurt y precio cero. Introduce el `DATABASE_URL` de Neon y credenciales demo fuertes. Guarda `DJANGO_CSRF_TRUSTED_ORIGINS` después de que el paso 4 proporcione la URL de Vercel; no despliegues con configuración incompleta.
4. Importa el repositorio en Vercel Hobby sin tarjeta. Selecciona `apps/web` como Root Directory y pnpm según se detecta de los ficheros de lock/workspace commiteados. Fija `API_PROXY_TARGET` al origen HTTPS de Render solo para Production. Registra la URL de producción de Vercel asignada.
5. Vuelve a Render, fija `DJANGO_CSRF_TRUSTED_ORIGINS` a ese origen exacto de Vercel y despliega. La cadena de arranque debe terminar y `/health/` debe ponerse en verde antes de continuar.
6. Vuelve a desplegar Vercel desde el mismo commit de Git para que su destino de rewrite y la revisión del frontend queden fijados juntos.
7. Ejecuta el smoke desde un shell local de confianza, pasando los secretos solo como variables de entorno de proceso:

```powershell
$env:BASE_URL = "https://<vercel-production-host>"
$env:EXPECTED_COMMIT = "<full-render-git-commit-sha>"
$env:DEMO_USERNAME = "<runtime-secret>"
$env:DEMO_PASSWORD = "<runtime-secret>"
corepack pnpm exec playwright test e2e/deployed-smoke.spec.ts --project=chromium
```

Borra esas cuatro variables inmediatamente después. No subas una traza fallida hasta que sus metadatos de petición se hayan revisado en busca de secretos.

## Evidencia de despliegue (requerida para cerrar OPS-01)

| Campo | Valor |
|---|---|
| Decisión de producto | APROBADO: Vercel Hobby + Render Free + Neon Free; sin tarjeta/recursos de pago |
| URL HTTPS de Vercel / host en allowlist | `https://save-point-orpin.vercel.app` |
| URL HTTPS de la API en Render | `https://savepoint-api-37nz.onrender.com` |
| Proyecto/rama de Neon (sin cadena de conexión) | `autumn-breeze-06234770` / `production`; enlazado y reconciliado con éxito, 2026-09-04 |
| Commit de Git desplegado | `ff5aa2ee7ae460f780187f1fc13298bfb2e12fbe` (confirmado idéntico tanto en el `/health/` de Render como en el `/health/` de Vercel vía el proxy same-origin) |
| Hora/resultado UTC del smoke | 2026-09-05T10:00Z, PASS — `e2e/deployed-smoke.spec.ts` en verde contra las URLs de arriba |

Se encontraron y arreglaron tres bugs reales de la ruta de despliegue mientras se alcanzaba un smoke en verde, en orden: (1) a `apps/api/Dockerfile` le faltaba `docs/` (el check del doc de congelación del que depende import_catalogue), (2) `data/demo/seed-v1.json` hardcodeaba un `GameWork.id` aleatorio no portable en vez del `canonical_slug` determinista, (3) el matcher de locale de `apps/web/middleware.ts` estaba redirigiendo `/health/` en vez de dejar que el rewrite del proxy lo manejara. Un cuarto problema fue una particularidad específica de Vercel Hobby (ver "Limitaciones honestas del tier gratuito" arriba), no un bug de código. Todos están commiteados en `main` entre `c7d5d26` y `ff5aa2e`.

Cualquier campo `PENDIENTE` o smoke en rojo bloquea la finalización de OPS-01. No queda ninguno.

## Rotación, rollback y desmontaje

Rota las credenciales demo en la página de Environment de Render, vuelve a desplegar para que corra el bootstrap idempotente, verifica un login fresco y luego borra las copias del lado del operador. Rota las credenciales de Neon en Neon, reemplaza el `DATABASE_URL` de Render con el nuevo valor directo/sin pooling, vuelve a desplegar y revoca la credencial antigua solo después de que health esté en verde.

Para una regresión de la aplicación, vuelve a desplegar el mismo commit conocido-bueno en Render y Vercel, asegúrate de que las migraciones son retrocompatibles y vuelve a ejecutar el smoke con ese SHA. No revocar una migración de forma destructiva contra la única base de datos. Las funciones de restore/branch de Neon no deben asumirse disponibles en Free; verifícalas antes de confiar en ellas.

Para el desmontaje, exporta solo la evidencia de tesis que sea lícita y necesaria, borra el proyecto de Vercel, el servicio de Render y el proyecto de Neon, y verifica que cada panel no muestra ningún recurso ni cargo. Compose local más los datasets commiteados es la ruta de recuperación.
