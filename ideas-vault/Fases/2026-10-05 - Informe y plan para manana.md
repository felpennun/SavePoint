---
tags: [informe, plan, despliegue, tfg, repositorio, movil]
estado: vigente
fecha: 2026-10-05
---

# Informe del día y plan para mañana (2026-10-05)

Documento de trabajo para revisar con el autor. Recoge lo que quedó hecho, lo que se descubrió por el camino, y la
lista de tareas de mañana con una propuesta de enfoque para cada una. No contiene credenciales. Detalles técnicos del
despliegue: [[2026-10-05 - Corpus publico en Neon]]. Revisión de seguridad previa: [[2026-10-04 - Revision de seguridad]].

## 0. Lo primero que hay que decidir mañana (bloqueante)

**El worker de recomendaciones de Render mantiene despierta la base de datos de Neon.** `render-start.sh` lanza
`process_recommendation_jobs --loop --poll-seconds 3`: consulta la base cada 3 s. Mientras Render esté despierto, Neon
no se duerme nunca. Hoy no es grave porque Render se apaga solo tras ~15 min sin tráfico, pero **en cuanto activemos el
ping a Render (sección 4) la base quedaría encendida 24 h**. Según recuerdo, el plan gratuito de Neon da unas 100
horas-CU al mes, que a 0,25 CU son ~400 h de cómputo, menos que las ~730 h de un mes (a verificar en la consola de Neon
antes de decidir). Agotado el cupo, Neon suspende el proyecto y **la web pública deja de funcionar**.

Esto contradice el objetivo del autor: "pingear solo a Render para no gastar las llamadas de Neon".

Propuesta (la recomendada es A):

| Opción | Cómo | Pros | Contras |
|---|---|---|---|
| **A. Worker bajo demanda** | Quitar el bucle. Cuando la API encola un trabajo, lanza un subproceso `process_recommendation_jobs` (sin `--loop`, con un candado para que haya uno solo) que procesa la cola y termina. | La base solo se consulta cuando alguien actúa. Las recomendaciones tardan lo mismo. | Hay que escribir y probar el lanzador (unas 30 líneas más test). |
| B. Bucle con espera larga | `--poll-seconds` de varios minutos. | Cambio de una línea. | Una recomendación podría tardar minutos en empezar; la base sigue despertándose con cada consulta. |
| C. Sin worker en la nube | Recomendaciones solo en local. | Sin coste. | La web pública pierde recomendaciones personalizadas. |

Hasta resolverlo: **no activar el ping** (sección 4).

## 1. Estado actual del despliegue

URLs: web `https://save-point-orpin.vercel.app`, API `https://savepoint-api-37nz.onrender.com`. Base de datos: proyecto
Neon `autumn-breeze-06234770`, rama `production`.

Hecho hoy (commits en `main`, CI en verde): `ae946bd` (Render ya no aborta sin cuentas demo), `d68bebf` (worker de
recomendaciones + scripts del corpus), `13ad406` (botón de login/registro y precalentado de facetas), `f42a798`
(región de Vercel, precarga, pantalla de carga, desplegable sobre las insignias de platino), `3600992` (caché de la
ficha de juego en la API).

Qué hay publicado:

- **Corpus:** 32.550 juegos (con nota IGDB o PopScore > 0) + 10.714 DLC relacionados; 359 MB de 1 GiB en Neon.
- **Recomendaciones:** vectores `fs-v13` (32.550) y las instantáneas de nota y popularidad de 2026.09.2; un único worker
  en Render (en local hay uno por algoritmo). Primera recomendación de una cuenta nueva: unos 4 minutos.
- **Cuentas:** `SavePoint_demo` (antigua), `tizon` (la del autor), `demo_user` (copia de `felipe` con sus 82 juegos,
  listas, comentarios y favoritos) y `demo_user2/3/4` (vacías). Clave de demostración acordada con el autor (no se
  guarda aquí).
- **Rama de respaldo en Neon:** `backup-before-corpus-subset-2026-10-05` (sin cómputo): estado anterior a la carga.
  Restaurarla perdería las cuentas creadas después.
- **Scripts reproducibles:** `scripts/public-corpus/` (`export_subset.sql`, `load_subset.sh`,
  `export_recommender_data.sql`, `load_recommender_data.sh`, `clone_account_to_public.sh`). Se ejecutan dentro del
  contenedor de la base local; la URL de Neon se lee de un fichero temporal que se borra al terminar.

Rendimiento medido en la web pública (Frankfurt, sesión iniciada): colección 0,26-0,46 s, catálogo 0,26-0,70 s, ficha
de juego 0,58-0,78 s antes de cachear la ficha; con la caché de la API la ficha responde en ~0,17 s (medido contra
Render, antes ~0,5 s). La causa principal que se corrigió:
las funciones de Vercel corrían en Washington mientras que API y base están en Frankfurt.

## 2. TFG: sección de despliegue y diferencia catálogo local / desplegado

Objetivo: completar la sección de despliegue y dejar escrita, sin maquillar, la limitación de que el catálogo de la
web desplegada **no es el mismo** que el de la web local.

Dónde está hoy (todo está desactualizado respecto a lo de hoy):

- `thesis/sections/06_implementacion.tex` líneas ~63-79 (corpus curado de 150 juegos) y ~637-692 (despliegue público:
  dice que sirve la interfaz anterior al rediseño contra 150 juegos y que el catálogo a escala real no está desplegado).
- `thesis/sections/05_diseno_arquitectura.tex` líneas ~68-98 (topología y ADR-005).
- `thesis/sections/03_gestion_planificacion.tex` líneas ~414 y ~476-479 (infraestructura gratuita, diferencia
  público/local como elección deliberada).
- `thesis/sections/08_conclusiones.tex` líneas ~37-49 (trabajo futuro: "conectar el despliegue público al catálogo a
  escala real", que ahora está **parcialmente** hecho).
- Figura `thesis/figures/despliegue-flujo.pdf` (topología y cadena de arranque; habrá que añadir el worker y el
  precalentado).

Contenido propuesto para la sección (tabla comparativa + párrafo de limitaciones):

| Aspecto | Web local (Docker) | Web desplegada |
|---|---|---|
| Obras importadas | 331.000 (330.850 de IGDB + 150 de Wikidata) | 43.414 (+150 de Wikidata) |
| Corpus gobernado (visible en el catálogo) | 190.479 | 32.550 (el 17 %): con nota IGDB o PopScore > 0 |
| Vectores de características | 190.479 por versión, 8 versiones | 32.550, solo la versión vigente `fs-v13` |
| Workers de recomendación | 4 (señales, ponderado, recencia, MMR-pop) en paralelo | 1, que procesa todos los trabajos |
| Evaluación offline | Sí (artefactos de la memoria) | No: se ejecuta solo en local |
| Tamaño de la base de datos | 3,77 GB | 359 MB (límite de Neon gratuito: 1 GiB) |
| Disponibilidad | Mientras corra Docker | Render duerme tras ~15 min sin tráfico (arranque en frío de 30-60 s) |
| Ficha / catálogo | Mismo código | Mismo código; menos resultados |

Limitaciones a dejar por escrito:
1. El corpus completo gobernado (~1,3 GB con índices solo para las tablas que usa la API) no cabe en Neon gratuito. Se
   eligió un subconjunto con criterio explícito y reproducible (nota IGDB o PopScore > 0).
2. Los resultados de la evaluación offline de la memoria se calcularon sobre el corpus completo local; la web
   desplegada es una demostración funcional, no el entorno donde se midió.
3. Las recomendaciones en la web desplegada son más lentas (un worker, CPU compartida con la API, 512 MB).
4. Los datos de la web desplegada son los de una demostración: cuentas sin verificación de correo, claves de demo.

Cosas que **no** hay que olvidar al reescribir: cambiar "150 juegos" por las cifras nuevas, la afirmación de que el
rediseño no está desplegado (ya lo está), el recuento de pruebas (779 de backend y 66 de web) y el commit desplegado.
Regenerar la vista previa PDF (está desactualizada desde el último reemplazo de figuras).

## 3. Trabajo futuro (a discutir mañana, sin decidir todavía)

Lista de candidatos para abrir la discusión de cómo y cuánto añadir (el autor no quiere secciones muy grandes):

- Desplegar el corpus gobernado completo: Neon de pago (Launch) o PostgreSQL propio; coste frente a beneficio.
- Workers de recomendación independientes por algoritmo y bajo demanda (ver sección 0).
- Caché compartida (Redis) si hubiera más de una instancia; hoy no hace falta (una sola instancia, caché en memoria).
- Caché en el borde de Vercel moviendo las lecturas públicas a rutas de Next.js con `revalidate` (el `s-maxage` por
  `rewrite` no se cachea en Vercel: probado, `MISS` repetido).
- Mantener la API despierta (ping) y precalentado de la caché en el arranque.
- Verificación de correo, recuperación de contraseña y política de contraseñas común en registro y cambio.
- Seguridad pendiente: rol de base de datos sin superusuario, CSP con nonces, caché de fotos de amistades, rotación de
  contraseñas (ver sección 8).
- Evaluación con usuarios reales (los tres profesores/compañeros que abrirán la app) frente a la población sintética.
- Aplicación móvil o PWA, internacionalización a más idiomas, exportación de datos.

## 4. Mantener Render despierto sin tocar Neon (proceso documentado)

Objetivo: que Render no se duerma (evita el arranque en frío de 30-60 s) **sin** despertar la base de datos de Neon,
para no gastar horas de cómputo.

Hecho comprobado: la ruta `/health/` **no toca la base de datos** (`config/urls.py`: responde `{"status": "ok",
"commit": ...}` leyendo solo una variable de entorno). Es la única ruta que debe usar el ping.

**No** usar `/api/catalogue/...` para el ping: esas rutas consultan Neon (su caché dura 120 s, un ping cada 5 min la
recalcularía cada vez y mantendría la base despierta).

Pasos (opción 1, UptimeRobot, gratuito, no gasta minutos de GitHub):
1. Crear cuenta en uptimerobot.com.
2. Añadir monitor de tipo HTTP(s), URL `https://savepoint-api-37nz.onrender.com/health/`, intervalo de 5 minutos
   (Render duerme a los ~15 minutos).
3. Comprobar que el monitor aparece "Up" y que `commit` en la respuesta es el desplegado.

Opción 2 (si el repositorio pasa a **público**, los minutos de GitHub Actions son gratuitos e ilimitados): flujo
programado `*/10 * * * *` con un único paso `curl -fsS --max-time 60 https://savepoint-api-37nz.onrender.com/health/`.
Con el repositorio privado no sirve: 10 min de intervalo son ~4.300 min/mes frente a los 2.000 gratuitos.

Qué ocurre cuando alguien entra: con Render despierto, la primera petición que toque la base despierta Neon (1-2 s). El
precalentado de facetas solo se ejecuta cuando Render **arranca**; las facetas viven 6 h en memoria, así que el primer
visitante después de ese plazo paga unos 2 s. Aceptable; si molestara, se puede añadir una renovación al primer acceso.

Condición previa: **resolver la sección 0** antes de activar el ping.

## 5. Revisión completa del repositorio antes de hacerlo público

Objetivo: dejar solo lo esencial para ejecutar la aplicación (en local y en web), con un README correcto. Inventario de
partida (archivos versionados, 7,5 MB de datos fuera de dependencias):

| Qué | Dónde | Observación |
|---|---|---|
| Herramienta GSD duplicada 4 veces | `.github/`, `.claude/`, `.codex/`, `.agents/` (≈ 750 ficheros cada una, de ellas ~250 `bin`, 156 `workflows`, 125 `references`) | ≈ 2.900 ficheros de tooling de agentes. Fuera de `.github/workflows/` y `.claude` mínimo, no son esenciales. |
| Planificación | `.planning/` (308 ficheros) | Memoria de trabajo interna. |
| Vault de ideas | `ideas-vault/` (≈ 160 ficheros) | Decisión del autor: ¿se publica o no? |
| Zips y binarios | `TFG/SavePoint TFG (1).zip` (11,8 MB), `TFG/TFG-vista-previa.pdf` (4,8 MB), `design/brand/SavePoint visual identity system-handoff (4).zip` | Quitar. |
| Artefactos de evaluación en la API | 28 JSON en `apps/api/` (`evaluation-400-test-*.json`, `feature-vector-cache-*.json`, manifiestos...; varios de 2-5 MB) | Mover a `docs/` o fuera del repositorio si no los usa la app. |
| Capturas de pruebas | `e2e/artifacts/` (64 ficheros, hasta 6,9 MB cada uno) | Quitar o ignorar. |
| Documentos | `docs/` (99 ficheros, 5 MB), `data/` (100 MB en disco; versionado: semillas, manifiestos, localización) | Revisar qué necesita la app para arrancar (`data/raw/wikidata-games.json`, `data/manifests/*` los usa `import_catalogue`). |
| Tesis | `thesis/` | ¿Se publica con el repositorio? Decisión del autor. |
| Otros | `tmp/`, `skills-lock.json`, `.design-import/`, carpeta rara `"ideas-vault` (9 entradas con comillas en el nombre) | Revisar. |

Esenciales para correr la app: `apps/api`, `apps/web`, `infra/`, `data/` (lo mínimo que usa `import_catalogue`,
`load_localized_summaries` y la semilla), `scripts/` (lo que use el CI y el despliegue), `.github/workflows/`,
`pyproject.toml`, `uv.lock`, `pnpm-*.yaml`, `.env.example`, README.

Antes de hacerlo público:
1. **Secretos:** el escáner del repositorio pasa (ver revisión de seguridad), pero el historial contiene valores de
   prueba y señuelos; revisar una vez más con el repositorio ya limpio. Contraseñas de demostración en
   `infra/compose.yaml`: decidir si se mantienen (son locales).
2. **Alertas de dependencias de GitHub (5 abiertas):** `next` 16.3.4 (crítica, ejecución remota en `next/og`; no usamos
   `next/og`, pero hay que subir a 16.3.6) y `urllib3` 2.7.0 (media y dos altas; fijar 2.8.0 en `uv.lock`).
3. **Historial de git:** si se quieren eliminar los ficheros grandes del historial (no solo del árbol) habría que
   reescribirlo; no recomendable salvo que el peso importe. Alternativa: publicar con el historial tal cual y quitar
   solo del árbol.
4. **README:** reescribir (64 líneas hoy) con: qué es SavePoint, capturas, arquitectura en un párrafo, cómo arrancar en
   local (Docker), cómo ejecutar tests, enlaces a la web desplegada y a sus limitaciones, licencia y créditos de datos
   (IGDB/Twitch, Wikidata). Mantener CONVENTIONS/AGENTS/CLAUDE si el autor quiere seguir trabajando con asistentes.
5. **Ramas protegidas / issues / PR templates:** revisar antes de abrir.
6. Con el repositorio público el ping desde GitHub Actions sale gratis (ver sección 4).

Método propuesto: lista de candidatos a borrar en dos columnas (esencial / no esencial) para que el autor la apruebe
antes de borrar nada, y un commit por categoría para poder revertir.

## 6. Visual solo en móvil

Pregunta del autor: ¿se pueden hacer cambios visuales solo en móvil sin afectar a la web en PC? **Sí.**

Cómo garantizarlo:
- Todos los cambios van dentro de `@media (max-width: 767px)` (el punto de corte `md:` de Tailwind es 768 px, el mismo
  que ya usa la barra de navegación) y, si hace falta, clases `md:hidden` / `max-md:` en el marcado de forma aditiva.
- Nada de tocar reglas globales existentes: bloque nuevo de CSS móvil al final de `globals.css`, bien comentado.
- **Prueba de que escritorio no cambia:** capturas de todas las rutas a 1440 px antes y después, y diferencia de píxeles
  (Playwright) que debe ser nula salvo ruido.
- Cuidado con los diseños de alto fijo (`.sp-fixed-page`, `.sp-coll-page`, `.sp-pf.is-fixed`): en móvil conviene que la
  página tenga scroll normal; esas reglas ya se activan por ancho (comprobar en cada pantalla).

Alcance propuesto (acotado, sin rediseñar todo): barra de navegación y menú, catálogo y filtros, ficha de juego,
colección (selector de estado y listas), recomendaciones, amistades y perfil, formularios de login y registro.

## 7. Revisión visual autónoma y correcciones principales

Pregunta del autor: ¿puedo hacer yo la visita y aplicar las correcciones principales? **Sí**, con este método:

1. Recorrido automático con Playwright (web desplegada o local): cada ruta con sesión de `demo_user` y sin sesión, en
   móvil (360, 390 y 430 px) y escritorio (1440 px), claro y oscuro.
2. Detección automática de problemas objetivos: desbordamiento horizontal, elementos que se salen del ancho, textos
   cortados, objetivos táctiles menores de 44 px, solapes entre elementos (como el del desplegable de hoy), errores en
   consola.
3. Informe con capturas y lista priorizada (crítico / molesto / estético).
4. Aplicar solo las correcciones principales en móvil (sección 6) y las de escritorio que sean errores claros
   (solapes, cortes), sin cambios de estilo no pedidos.
5. Volver a pasar el recorrido y adjuntar antes/después; el autor revisa y decide qué más tocar.

## 8. Pendientes heredados (no perder)

- **Correcciones del profesor:** aplicar todas (el autor las traerá/indicará). Sin trabajo previo posible hasta
  conocerlas.
- **Cambio de contraseña:** no aplica las mismas restricciones/mensajes que el registro (mostrar la misma pista y los
  motivos concretos; rechazar nueva == actual). Detectado, sin corregir.
- **Seguridad:** subir `next` a 16.3.6 y `urllib3` a 2.8.0 (con su registro de legitimidad); rol de base de datos sin
  superusuario en producción; CSP con nonces; reducir la caché de fotos de amistades; **rotar la contraseña de
  `neondb_owner` y actualizar `DATABASE_URL` en Render** (pasó por el historial de la conversación de hoy).
- **Pruebas e2e de Playwright** (colección, social, recomendaciones, humo desplegado): adaptadas pero no ejecutadas
  contra el diseño nuevo; necesitan cuenta de demostración.
- **Memoria:** recompilar la vista previa PDF; actualizar cifras de pruebas y del despliegue (sección 2).
- **Issue #77** sigue abierta (`Refs #77`); cerrar con `Closes #N` solo al cerrar un plan verificado con su SUMMARY.
- **Neon:** decidir si se borra la rama de respaldo cuando todo esté estable (no gasta cómputo, sí algo de espacio).
- **Cuentas públicas:** `demo_user2/3/4` están vacías; el autor las rellenará.
- **Registro:** el primer intento del autor falló y no se pudo reproducir (curl y navegador real dan 201). Si vuelve a
  pasar, anotar el mensaje exacto que muestra la página.

## 9. Orden sugerido para mañana

1. Decidir la opción de la sección 0 (worker bajo demanda) e implementarla; después activar el ping de la sección 4.
2. Correcciones del profesor (primero, porque condicionan la memoria).
3. Sección de despliegue y diferencias local/desplegado (sección 2) y trabajo futuro (sección 3, tras la discusión).
4. Revisión visual autónoma y correcciones, empezando por móvil (secciones 6-7).
5. Limpieza del repositorio y README (sección 5), con las dependencias actualizadas, y hacerlo público.

Nota: se retiró la pantalla de carga de esqueleto (`loading.tsx`) a petición del autor; la precarga al pasar el ratón
se mantiene.
