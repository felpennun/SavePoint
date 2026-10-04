---
tags: [seguridad, rendimiento, despliegue, informe]
estado: vigente
fecha: 2026-10-04
---

# Revisión de seguridad, rendimiento y despliegue (2026-10-04)

Alcance: CI y despliegue, dependencias, configuración de Django y de Next.js, secretos (árbol e historial), base de
datos, usuarios y sesiones, y pruebas de ataque "de caja negra" contra la API local (inyección SQL, manipulación de URL,
control de acceso entre usuarios, redirecciones, límites de ritmo, cabeceras). Después, optimización y caché. No se
ha hecho una prueba de intrusión externa ni un escáner dinámico (ZAP).

## 1. Por qué la web no se desplegaba (dos causas encadenadas)

1. **Healthchecks desactivados en los workers.** El flujo "Quality gates" fallaba en `docker compose up --wait` con
   `container savepoint-recommendation-worker-* has no healthcheck configured`, en los 40 últimos pushes (desde el
   14/09). Render solo despliega la API si ese flujo pasa (`autoDeployTrigger: checksPass`), así que la API pública
   se quedó en el commit del 05/09 (571 commits atrás) mientras Vercel desplegaba el frontal nuevo contra ella:
   `/es` no respondía y `/es/catalogue` daba 500. Arreglado en `3943eb8` (healthcheck real por worker).
2. **Permisos de `.next` en Linux.** Con el healthcheck arreglado, el siguiente fallo fue `container savepoint-web-1
   exited (1)`. Reproducido en local simulando los permisos del ejecutor de CI: Docker crea el volumen anónimo
   `apps/web/.next` con dueño root y `next build` (usuario `node`) muere con `EACCES: .next/trace`. En Windows no se
   notaba. Arreglo: el `Dockerfile` crea `.next` con dueño `node`. Comprobado con la misma simulación (con y sin
   el arreglo).
3. El flujo ahora imprime los registros de `web` y `api` cuando falla un paso, para no depender de adivinar.

Efecto de seguridad: las puertas de seguridad de CI (escáner de secretos, `check --deploy`, migraciones, pruebas de
seguridad) llevaban sin ejecutarse desde el 14/09.

## 2. Hallazgos de seguridad y estado

| # | Gravedad | Hallazgo | Estado |
|---|---|---|---|
| 1 | Alta | Puertas de seguridad de CI inoperantes (§1). | Corregido, pendiente de ver el CI en verde |
| 2 | Alta | `next` 16.3.4: GHSA-vcvr-r3jv-pc5j (ejecución remota en `next/og` `ImageResponse`, versiones 16.2.0 a 16.3.5). El proyecto no usa `next/og`, así que no es explotable hoy. | **Pendiente**: subir a 16.3.6 con su registro de legitimidad |
| 3 | Media | `urllib3` 2.7.0, tres avisos (corregidos en 2.8.0). Solo lo usa la importación de IGDB fuera de línea. | **Pendiente**: fijar 2.8.0 en el lock |
| 4 | Media | Una `\x00` (byte nulo) en la ruta o en un parámetro provocaba un **500** (PostgreSQL no admite NUL). No es inyección, pero es un fallo provocable por cualquiera. | Corregido: middleware que responde 400 |
| 5 | Media | El navegable de DRF (consola HTML con token CSRF) se servía a quien enviara `Accept: text/html`. | Corregido: solo JSON |
| 6 | Media | La conexión a la base de datos **ignoraba `?sslmode=`** de `DATABASE_URL` y en producción podía caer a texto plano (libpq `prefer`). | Corregido: se respeta `sslmode` y en producción el valor por defecto es `require` |
| 7 | Media-baja | La subida de foto y portada leía todo el cuerpo antes de comprobar el tope de 512 KiB y no tenía límite de ritmo. | Corregido: se comprueba `upload.size` antes de leer y se limitan las escrituras a 20 por minuto |
| 8 | Media-baja | Solo algunas rutas tenían límite de ritmo: un usuario autenticado podía crear cientos de listas por minuto (160 en la prueba). | Corregido: límite por usuario de 300 por minuto en todas las rutas que no tienen otro propio |
| 9 | Media-baja | La respuesta pública de facetas completas pesa unos 2,8 MB (40.000 desarrolladoras) y se recalculaba en cada petición: amplificación para un ataque de denegación. | Corregido: se calcula una vez cada 6 h |
| 10 | Baja | `infra/compose.yaml` lleva contraseñas de demostración en claro (`DEMO_PASSWORD`, `DEMO_ACCOUNTS`) y la base local `local_test_only`. Solo locales; repositorio privado. | **Pendiente**: si son las del Render público, cambiarlas |
| 11 | Baja | CSP con `script-src 'unsafe-inline'` (seguimiento documentado). | Pendiente |
| 12 | Baja | Fotos de amistades con `Cache-Control: private, max-age=3600`: tras bloquear o eliminar a alguien pueden quedar una hora en el navegador del otro. | Pendiente |
| 13 | Info | En local la aplicación usa un rol de PostgreSQL superusuario y sin TLS (normal en el contenedor de desarrollo). En producción hay que usar un rol sin privilegios de superusuario (Neon: rol de la aplicación) y `sslmode` activo. | Recomendación |
| 14 | Info | El servidor de desarrollo anuncia `WSGIServer/0.2 CPython`. En producción corre gunicorn. | Nada |

## 3. Pruebas de ataque realizadas (47 comprobaciones, 3 hallazgos reales corregidos)

- **Inyección SQL:** 11 cargas útiles (comillas, `UNION SELECT`, `pg_sleep`, `DROP TABLE`, plantillas, bytes nulos,
  5.000 caracteres) contra 12 parámetros del catálogo, la búsqueda de personas y los filtros de biblioteca. Sin errores de
  base de datos y sin efecto de retardo. Revisión del código: no hay consultas construidas con texto; los únicos
  `cursor.execute` son bloqueos consultivos con parámetros.
- **Manipulación de URL:** `..%2f`, `%2e%2e`, `%00`, `' OR 1=1--` en rutas de alias y de slug: todo 400/404 (el `%00` era
  500, corregido).
- **Control de acceso (IDOR):** con dos usuarios, el segundo no puede ver, modificar, borrar ni añadir a una lista del
  primero (404 en todos los métodos), no ve su colección ni su foto sin ser amistad, y la lista privada no sale por la URL
  pública. Las 12 rutas protegidas rechazan a un anónimo, igual que las escrituras.
- **Asignación masiva:** `is_staff`, `is_superuser` y `user` se ignoran en el perfil y en el registro.
- **Redirecciones:** `next=//evil.com`, `https://evil.com`, `/\evil.com`, `javascript:` y `///evil.com/%2f..` no se
  reflejan; siempre responde la ruta interna.
- **CSRF:** una escritura sin token da 403.
- **Cabeceras y CORS:** `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`; sin CORS permisivo; `/admin/` exige sesión;
  JSON mal formado y 404 sin trazas.
- **Cuentas:** el inicio de sesión devuelve el mismo mensaje y el mismo tiempo (192 ms) para un usuario que existe y otro
  que no; la sesión cambia al iniciar (sin fijación); el cierre de sesión la invalida en el servidor; el cambio de
  contraseña invalida las demás sesiones; las contraseñas se guardan con PBKDF2-SHA256 (los usuarios sintéticos tienen
  contraseña inutilizable).
- **Límites de ritmo:** inicio de sesión (a partir del intento 6 en esa prueba), registro (5 por hora), búsqueda de catálogo
  (120 por minuto), nuevo límite por usuario (429 tras unas 220 peticiones en la prueba) y subida de imágenes.
- **Secretos:** el escáner del repositorio (código, salida de compilación, capas de imágenes y registros) da PASS; el
  historial solo tiene valores de prueba y señuelos; `.env.example` es el único fichero de entorno versionado.
- **Base de datos:** el puerto 5432 no se publica en el equipo; las consultas son ORM.
- **Configuración:** `check --deploy` en producción sin avisos; HSTS de un año, cookies seguras en producción,
  clave secreta de 50 caracteres como mínimo, autenticación solo por sesión, contenedores sin root, imágenes fijadas por
  digest, permisos de GitHub Actions `contents: read`.

## 4. Rendimiento y caché

Medido contra la API local (la web envía `facets=lite`):

| Consulta | Antes (primera vez) | Después (repetida) |
|---|---|---|
| Catálogo por defecto | 580 ms | 2 ms |
| Catálogo página 40 | 520 ms | 3 ms |
| Catálogo con plataforma | 100-220 ms | 3 ms |
| Catálogo con búsqueda | 45-67 ms | 3 ms |

Cambios:
- **API:** la respuesta de catálogo (variante ligera) se guarda 2 minutos por consulta, con `Cache-Control: public,
  max-age=60, stale-while-revalidate=300`, igual que la ficha de un juego; las facetas completas se guardan 6 h.
- **Navegador (caché de navegación):** `staleTimes` de Next.js: las páginas ya visitadas se reutilizan 30 s (dinámicas)
  y 3 min (estáticas). Volver a la colección con la caché tarda unos 86 ms. Para que no haya datos viejos, un
  componente (`RouterCacheGuard`) descarta esa caché y refresca la página tras cualquier escritura correcta a la API;
  probado: guardar un juego y volver a la colección muestra la tarjeta nueva.
- **Imágenes:** la caché de portadas optimizadas pasa de 60 s a 7 días.
- **Detectado y no cambiado:** el diseño de la capa raíz consulta la cuenta en cada carga completa; con la caché de
  navegación apenas se nota. El tiempo de la primera visita tras reiniciar sigue dependiendo del cálculo de facetas
  (unos 2 s la primera vez).

## 5. Pruebas

778 de backend (incluye 5 nuevas de endurecimiento) y 66 de frontend, todas en verde. Las pruebas se ejecutan ahora con
la caché del proceso vacía entre una y otra, porque la caché del catálogo podía colarse entre pruebas.

## 6. Pendiente

- Confirmar que el CI queda en verde con los dos arreglos y que Render redespliega (aplicará las migraciones nuevas).
- Subir `next` a 16.3.6 y `urllib3` a 2.8.0.
- Revisar las contraseñas de demostración si coinciden con el despliegue público (#10) y usar un rol de base de datos sin
  privilegios de superusuario en producción (#13).
- CSP con nonces (#11) y tiempo de caché de fotos de amistades (#12).
