---
tags: [informe, plan, despliegue, tfg, repositorio, movil]
estado: vigente
fecha: 2026-10-05
---

# Informe del día y plan para mañana (2026-10-05)

Documento de trabajo para revisar con el autor. Recoge lo que quedó hecho, lo que se descubrió por el camino, y la
lista de tareas de mañana con una propuesta de enfoque para cada una. No contiene credenciales. Detalles técnicos del
despliegue: [[2026-10-05 - Corpus publico en Neon]]. Revisión de seguridad previa: [[2026-10-04 - Revision de seguridad]].

## 0. Worker bajo demanda: RESUELTO esta noche (antes era el bloqueante)

**Problema detectado:** el worker de recomendaciones de Render consultaba Neon cada 3 s (`--loop --poll-seconds 3`),
lo que mantiene despierta la base de datos mientras Render lo esté. Con el ping activado, Neon quedaría encendido 24 h
y agotaría las horas de cómputo del plan gratuito (según recuerdo ~100 horas-CU/mes, unas 400 h a 0,25 CU, frente a
~730 h de un mes; a verificar en la consola), tras lo cual la web dejaría de funcionar.

**Solución aplicada (opción A):** `apps/api/recommendations/ondemand.py`. Ya no hay ningún proceso que pregunte.
Cuando la API encola un refresco de recomendaciones, lanza un proceso corto (`process_recommendation_jobs
--ondemand`) que vacía la cola y termina; la base solo se consulta cuando alguien actúa.

- **Candado de fichero:** el lanzador toma el candado y se lo pasa al proceso hijo por un descriptor heredado
  (`RECOMMENDATION_WORKER_LOCK_FD`); así nunca hay dos workers a la vez y no hay hueco entre decidir y tomar el candado
  (se detectó y cerró esa carrera durante las pruebas). Si el candado está tomado, el lanzador no hace nada y el worker
  en marcha vuelve a mirar la cola antes de terminar.
- **Autorreparación:** si la página de recomendaciones consulta mientras hay un refresco pendiente y no corre ningún
  worker (por ejemplo, reinicio a mitad de un trabajo), pide uno (como mucho cada 30 s). Al arrancar Render se vacía
  una vez lo que hubiera quedado en la cola.
- **Interruptor:** solo funciona con `RECOMMENDATION_ONDEMAND_WORKER=1` (lo fija `render-start.sh`). En local y en
  los tests no se lanza nada; la pila local sigue con sus workers por algoritmo.
- **Pruebas:** 9 pruebas nuevas (`tests/test_ondemand_worker.py`) y 788 de backend en verde; comprobado además con
  procesos reales: un segundo intento inmediato no lanza otro worker y, al terminar el primero, se lanza uno nuevo.

**Efecto para el ping (sección 4):** ya se puede activar sin consumir horas de Neon, siempre que apunte a `/health/`.
**Comprobado en producción (commit `b6dd90c`, 2026-10-05 01:49-01:56):** cuenta desechable nueva, 4 juegos valorados:
el worker arrancó solo, calculó las señales en 2 min 46 s (la primera carga de vectores desde Neon) y las 3 secciones en
~1 min cada una; recomendación lista a los ~6 min; cuenta borrada después. Nota: durante las señales la API muestra
"en cola" porque ese trabajo previo no cuenta como sección. Comprobación de que Neon se suspende sin tráfico: **confirmada**
(2026-10-05, 02:13-02:22 local). Un primer intento quedó invalidado porque mis propias capturas consultaban la API
durante la espera; en el segundo, con 9 minutos sin ninguna petición, Neon registró `suspend_compute` a las 00:22:16Z.
Con el ping solo a `/health/` (sin base de datos) y el worker bajo demanda, la base se duerme sola entre visitas.

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
- Workers de recomendación independientes por algoritmo (hoy, en la nube, un único proceso bajo demanda; ver sección 0).
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

Condición previa (resuelta, sección 0): el worker bajo demanda ya no consulta la base de datos en segundo plano.

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

## 7 bis. Recorrido móvil: hallazgos y correcciones APLICADAS (2026-10-05, noche)

**Estado: aplicado el mismo día**, a petición del autor ("solo en móvil, en PC es perfecto"). Todo el CSS nuevo está
dentro de un único bloque `@media (max-width: 767px)` al final de `apps/web/app/globals.css` (mismo punto de corte
`md:` que usa la barra), y el marcado nuevo solo está en el menú móvil (`MobileMenu`, que ya era `md:hidden`).

Aplicado: (1) cabecera sin solapes: botón de menú con icono, idioma y tema dentro del menú, fondo atenuado al abrirlo;
(2) selector de la colección en dos filas de chips desplazables (la página baja de 10.570 a ~10.260 px y los juegos
empiezan en la primera pantalla); (3) paneles de filtros a ancho del bloque, dentro de la pantalla, con casillas de
tamaño normal; (4) portada con título de 28 px y tarjeta destacada con más espacio para el texto; (5) pestañas del
perfil en una fila desplazable, botón de guardar y campo de usuario a ancho completo; (6) zonas táctiles de 44 px en
idioma, enlaces sueltos, cámara del perfil, "+ NUEVA" y "+" de copias; (7) etiquetas de 11 px a 12 px;
(8) recomendaciones: selector de algoritmo en chips y sin códigos técnicos; (10) portada de la ficha centrada;
(11) menú móvil con fondo atenuado.

Medición (390 px, antes → después, mismo script): títulos de 3 o más líneas 4 → 0, texto de 11 px 8 → 1, solapes
94 → 72 y zonas táctiles pequeñas 71 → 66 (los que quedan son sobre todo falsos positivos: casillas de paneles
cerrados, los medios puntos de las estrellas y el carrusel desplazable a propósito). Cabecera: 0 solapes en todas las
páginas (antes el logo se pisaba con ES/EN en todas).

**Prueba de que escritorio y tableta no cambian:** 33 capturas completas (1440, 1024 y 768 px; con y sin sesión; 11
pantallas) antes y después. Mismas dimensiones en todas; 25 idénticas píxel a píxel y 8 con diferencias confinadas al
recuadro del juego destacado de la portada, que cambia en cada carga (repitiendo la misma página con la misma versión
salen entre 71 y 150 píxeles distintos), más un punto de 24×7 px. Los 66 tests de la web pasan (se actualizó el de la
barra: el botón de menú ahora es solo icono con `aria-label`).

No hecho / pendiente: (9) amistades (rellenos), medios puntos de las estrellas de la ficha (19 px de ancho: es la
propia naturaleza del control de media estrella), indicador del carrusel de relacionados, tema claro e inglés (el CSS
es el mismo, pero no se capturó), dispositivos reales y horizontal. Repetir con
`scripts/mobile-audit/mobile_audit.cjs` (`AUDIT_SESSION` permite usar una cookie de sesión si el origen no es de
confianza para la API, p. ej. localhost).

### Hallazgos originales (antes de aplicar)

(Descripción conservada tal como se redactó antes de aplicar los cambios.)

Qué se hizo: auditoría automática con Playwright (Chromium emulando un iPhone) sobre la web **desplegada**, con y sin
sesión de `demo_user`, a 360, 390 y 430 px de ancho, tema oscuro y español: 44 mediciones (19 sin sesión, 25 con
sesión), más capturas a 390 px de todas las pantallas, del menú, del menú de cuenta y de un filtro abierto. Script
reutilizable: `scripts/mobile-audit/mobile_audit.cjs` (variables `AUDIT_BASE`, `AUDIT_OUT`, `AUDIT_USER`,
`AUDIT_PASSWORD`; se repite igual después de los cambios). Las capturas están en una carpeta temporal y se regeneran
con el script.

Lo que está bien: **ninguna pantalla tiene scroll horizontal** (0 de 44), no hay errores de JavaScript, el catálogo en
dos columnas, la ficha de juego, el login y el registro se leen bien.

Problemas, por prioridad (todos confirmados con captura):

**P0, se ven mal a simple vista**
1. **Cabecera rota en todas las páginas.** El logo "SavePoint" se pisa con el selector ES/EN (ancho 360-430 px):
   caben mal el logo, ES/EN, el icono de tema, el de cuenta y el botón "Abrir menú". Propuesta: botón de menú solo
   con icono de hamburguesa; mover ES/EN y el tema dentro del menú (o del menú de cuenta); a menos de 380 px, logo solo
   con el icono.
2. **Colección: el selector de estado y listas ocupa ~1.200 px** antes de que se vea un solo juego (la página mide
   10.570 px de alto). Propuesta: barra horizontal desplazable de píldoras (Todos 82 · Jugando 11 · Pendientes 18 ...)
   y las listas en un desplegable o una segunda fila; los juegos empiezan en la primera pantalla.
3. **Filtros desplegables (catálogo y colección):** el panel de "Año" se sale por la derecha (llega a 487 px en una
   pantalla de 390), las casillas de las listas se dibujan como cuadrados grandes vacíos desalineados con su texto, y el
   panel tapa el botón "Aplicar filtros". Propuesta: panel a ancho completo anclado a la pantalla (hoja inferior),
   casillas de tamaño normal.

**P1, tamaños mal ajustados**
4. **Portada:** el título pasa de 36 px y ocupa 3 líneas; la tarjeta destacada pone la portada y el texto en dos
   columnas muy estrechas (el título en 2 líneas y la nota en 5). Propuesta: título ~28 px y tarjeta en una columna
   (portada arriba, texto debajo).
5. **Perfil (editar):** las pestañas (Cuenta, Privacidad, Preferencias, Conexiones, Seguridad) se parten en 3 líneas;
   "Guardar cambios" queda suelto bajo el avatar; el campo de nombre de usuario se corta ("demo_us"). Propuesta:
   pestañas en una sola fila con scroll horizontal, botón de guardar a ancho completo, campo con ancho completo.
6. **Zonas táctiles menores de 44 px** (recomendación táctil): ES/EN (24×40), "Fuentes" del pie, "Ver todas las
   fuentes" y "¿No tienes cuenta?" (16 px de alto), filas del selector de estado (40 px), icono de cámara del perfil
   (34×44). Propuesta: mínimo 44×44 solo en móvil con `padding`.

**P2, pulido**
7. **Texto de 11 px** en etiquetas pequeñas (`sp-coll-side-caption`, `sp-pf-eyebrow`, `sp-fr-eyebrow`,
   `sp-reco-rail-code`): subir a 12 px.
8. **Recomendaciones:** el selector de algoritmo ocupa media pantalla y enseña códigos técnicos (`WEIGHTED ·
   0.70/0.30`, `MMR-POP · 0.35/0.20/0.25/0.20`). En móvil: chips compactos y sin códigos.
9. **Amistades:** tres paneles apilados con mucho espacio vacío; reducir rellenos.
10. **Ficha de juego:** la portada queda alineada a la izquierda con un hueco a la derecha; centrarla o darle el
    ancho completo. El carrusel de contenido relacionado se sale del ancho a propósito (scroll horizontal), conviene
    que se note con un borde recortado.
11. **Menú móvil** abierto: cubre el contenido sin atenuar el fondo; conviene un fondo semitransparente.

Qué no se probó (hay que decirlo en el informe final): tema claro, inglés, dispositivos reales (solo emulación),
horizontal, tabletas (768-1024 px; hay reglas a 820/900/1100 px sin unificar), detalle de un perfil de amistad, listas,
las demás pestañas de editar perfil y los diálogos.

Cómo aplicarlo sin tocar escritorio: todo dentro de `@media (max-width: 767px)` (mismo punto de corte `md:` que ya
usa la barra), más clases `md:hidden` de forma aditiva; después, repetir las capturas a 1440 px y comparar píxeles con
las de antes (debe dar cero diferencias) y repetir el script móvil para demostrar que bajan los hallazgos.
Esfuerzo estimado: 3-4 horas para P0+P1, 1 hora más para P2.

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

1. Activar el ping de la sección 4 (el worker bajo demanda ya está hecho) y comprobar que Neon se suspende.
2. Correcciones del profesor (primero, porque condicionan la memoria).
3. Sección de despliegue y diferencias local/desplegado (sección 2) y trabajo futuro (sección 3, tras la discusión).
4. Móvil: ya aplicado (sección 7 bis); queda revisar en un móvil real y decidir los pendientes de esa sección.
5. Limpieza del repositorio y README (sección 5), con las dependencias actualizadas, y hacerlo público.

Nota: se retiró la pantalla de carga de esqueleto (`loading.tsx`) a petición del autor; la precarga al pasar el ratón
se mantiene.
