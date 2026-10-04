---
tags: [despliegue, corpus, neon, render]
estado: vigente
fecha: 2026-10-05
---

# Corpus público en Neon y Render (2026-10-05)

Hasta hoy la base pública (Neon) tenía solo los 150 juegos curados de Wikidata (ADR-003), con `in_corpus` a falso, así que
el catálogo público salía vacío. Desde hoy lleva un **subconjunto del corpus gobernado 2026.09.2**.

## Criterio

Obras gobernadas (`in_corpus`, no DLC) con nota IGDB (`total_rating` o `rating`) **o** PopScore mayor que 0:
**32.550 juegos** (30.695 con nota IGDB, 9.929 con PopScore, 8.074 en ambos). El corpus gobernado completo (190.479)
ocuparía unos 1,3 GB con índices y no cabe en el plan gratuito de Neon (1 GiB); el subconjunto ocupa **275 MB**.

## Qué se cargó

- Los 32.550 juegos más los 10.714 DLC relacionados que enseñan sus fichas: 43.264 obras.
- 71.153 alias de búsqueda, 110.291 lanzamientos, 43.264 portadas con atribución, 51.817 registros de procedencia,
  215.380 filas de evidencia de etiquetas curadas, 9.929 PopScore y los diccionarios (géneros, franquicias,
  desarrolladoras, temas, perspectivas, modos, subgéneros).
- Versión de corpus 2026.09.2 activa; la 2026.09.1 queda inactiva.
- **No** se cargaron: palabras clave, vectores de características, cachés de señales, trabajos y snapshots de
  recomendación ni instantáneas de rating/popularidad (la API pública no los usa).

## Qué se conservó

Los 150 juegos de Wikidata de Neon siguen ahí (sus UUID no cambian) porque la cuenta registrada tiene entradas de
biblioteca y una copia que dependen de ellos. Las plataformas existentes se reutilizan por nombre. `import_catalogue`
(arranque de Render) sigue siendo idempotente: solo toca obras con `SourceRecord` de Wikidata.

## Cómo se hizo (reproducible)

`scripts/public-corpus/export_subset.sql` construye un esquema temporal `pubexport` en la base local y
`scripts/public-corpus/load_subset.sh` lo vuelca en Neon con `COPY` (la URL de Neon se lee de un fichero temporal que
se borra al terminar; nunca se versiona). Antes de escribir se creó la rama de respaldo
`backup-before-corpus-subset-2026-10-05` (sin compute) como vuelta atrás.

Incidencia: 1.660 lanzamientos de DLC sin plataforma (`platform_id` nulo) se perdieron en el primer volcado por un
`JOIN`; se detectó al contrastar recuentos y se cargaron aparte. Comprobación final: 0 lanzamientos huérfanos, 0 entradas
de biblioteca huérfanas, todas las obras con lanzamiento.

## Verificación pública

`/api/catalogue/stats/` devuelve 32.550 juegos y 30.695 con nota; listado, búsqueda ("zelda": 19), filtro por plataforma,
ficha (GTA V, The Witcher 3 con 7 contenidos relacionados y resumen en español), estantería de novedades (20) y las
páginas de Vercel responden 200 en 0,2-0,8 s.

## Límites

- Las recomendaciones personalizadas se calculan en el propio Render con un único worker (ver la sección final);
  son más lentas que en local, donde hay un worker por algoritmo y el corpus completo.
- Las facetas `facets=lite` se guardan 6 h en la caché de proceso de la API.
- Pendiente de ajustar: el texto de la memoria que dice que el despliegue público usa el corpus curado de 150 juegos.
- La contraseña del rol `neondb_owner` pasó por el historial de la sesión: conviene rotarla y actualizar
  `DATABASE_URL` en Render.

Relacionado: [[2026-10-04 - Revision de seguridad]].

## Despliegue completo y fluidez (2026-10-05, tarde)

- **Recomendaciones:** se cargaron también los vectores `fs-v13` (32.550) y las instantáneas de nota (30.623) y
  popularidad (169.547) de 2026.09.2: 359 MB en Neon. Render no tenía ningún proceso que ejecutara la cola de
  trabajos (los trabajos se quedaban en `queued`); `render-start.sh` activa un worker **bajo demanda**: la API lanza un proceso corto que
  vacía la cola y termina (`recommendations/ondemand.py`), sin consultar Neon en segundo plano; así el ping a Render no
  consume horas de cómputo de Neon. Gunicorn pasa a 1 proceso con 4 hilos para que quepa en 512 MB.
- **Cuentas de demostración públicas:** `demo_user` (copia de la cuenta local `felipe` con todos sus datos),
  `demo_user2`, `demo_user3` y `demo_user4` (vacías), todas con la clave de demostración acordada con el autor. Script
  de copia: `scripts/public-corpus/clone_account_to_public.sh`.
- **Login y registro:** el botón volvía a "Entrar" mientras el navegador cargaba la portada, lo que parecía que no
  había pasado nada; ahora se queda en "Entrando…" hasta que cambia la página.
- **Fluidez:** `s-maxage=120` en las respuestas públicas del catálogo (la caché del borde de Vercel las reutiliza) y
  precalentado de las facetas al arrancar la API. El arranque en frío de Render (apagado tras ~15 min sin tráfico) se
  mitiga con un ping externo gratuito cada 5-10 min a `/health/`; no se hace con GitHub Actions porque el repositorio
  es privado y se agotarían los minutos gratuitos.

## Velocidad de navegación y desplegable (2026-10-05, noche)

- **Región de Vercel:** las funciones de Next.js se ejecutaban en Washington (`iad1`) mientras que Render y Neon están
  en Frankfurt, así que cada página de servidor cruzaba el Atlántico por cada llamada a la API. `vercel.json` fija
  `"regions": ["fra1"]`.
- **Precarga:** `HoverPrefetchLink` carga la página destino completa al pasar el ratón, enfocar o tocar una tarjeta,
  las flechas de paginación, las etiquetas de filtro y las filas del selector de la colección.
- **Pantalla de carga:** se probó una pantalla de esqueleto (`app/[locale]/loading.tsx`) y se retiró a petición del
  autor: quitaba dinamismo y la velocidad ya es buena sin ella.
- **Ficha de juego:** `LibraryControls` hacía cuatro peticiones al abrir (estado, nota, copias y configuración); la
  configuración ya lo devuelve todo, así que ahora es una.
- **Desplegable del perfil:** la insignia de platino (`z-index: 1`) se pintaba por encima del menú de cuenta porque la
  cabecera no formaba su propio nivel; `.sp-navbar` tiene ahora `z-index: 60`.
- **Ficha de juego en la API:** la respuesta de `/api/catalogue/games/<slug>/` se guarda 5 minutos por slug e idioma en
  la caché de la API (una docena de consultas menos por visita repetida); los 404 no se guardan.
