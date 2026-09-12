---
tags: [fase/03, tema/interfaz, tema/recomendadores, qual-02, resultado]
---

# Evidencia UI/E2E de recomendaciones para el cierre de Fase 3 (QUAL-02)

Contrapartida de interfaz al cierre backend de Fase 3
([[2026-09-12 - Cierre backend Fase 3 y limitaciones metodologicas]]). Este documento
registra la evidencia entregada y los hallazgos reales encontrados al producirla; con
esta evidencia, `QUAL-02` queda cubierto para el cierre de la fase.

## Qué se entregó

**`e2e/recommendations.spec.ts`** (nuevo), ejecutado con
`corepack pnpm exec playwright test e2e/recommendations.spec.ts --project=chromium`
tal como especifica la tabla de verificación de `03-VALIDATION.md` para QUAL-02.
Tres pruebas, las tres en verde de forma reproducible:

1. **El orden del DOM coincide con el de la API, por cada estante de contenido
   con resultados.** La verdad de referencia se lee de
   `GET /api/recommendations/snapshot/` mediante `page.request` (la misma
   sesión de navegador, no un cliente aparte). Compara los `slug` extraídos de
   los `href` de cada tarjeta, en orden, contra `results[].slug` de la API para
   los 14 algoritmos de contenido publicados. También comprueba, directamente
   sobre el payload, que cada lista de resultados es `score`-descendente.
2. **Ausencia de superficie de evaluación en el producto.** Sin `<canvas>`, sin
   clases de librerías de gráficas, sin `<select>` ni combobox alguno en la
   página, y sin vocabulario metodológico (nDCG, Wilcoxon, bootstrap, Friedman,
   leave-one-out, leave-fraction-out, protocolo vN, p-valor, Holm) en el texto
   visible.
3. **Reflow a 320px, temas claro/oscuro y alcanzabilidad por teclado.** Sin
   desbordamiento horizontal de `main` a 320px; el fondo computado cambia entre
   `data-theme="dark"` y `"light"` sin errores de consola; `Tab` desde el
   principio del documento alcanza una tarjeta real dentro de
   `.sp-shelf-track`.

## Fallos reales encontrados y corregidos en el camino

Ninguno de estos tres fue una regresión de la sesión de filtros del catálogo —
son bugs genuinos del árbol `apps/web` descubiertos al construir la prueba, ya
corregidos:

1. **Desbordamiento horizontal a 320px en el estante de DLC.** `.sp-shelf-track`
   y el `<div>` sin clase que envuelve cada grupo de DLC en
   `OwnedGamesDlcShelf` son ítems de una rejilla (`display: grid` en
   `.sp-shelf`); sin `min-width: 0`, su tamaño de contenido máximo obligaba a
   `main` —y a la página— a desbordarse lateralmente. Corregido con
   `min-width: 0` en `.sp-shelf-track` y una nueva clase
   `.sp-shelf-dlc-group` para ese envoltorio.
2. **Clic imposible sobre el radio de estado en la ficha de juego.**
   `LibraryControls` oculta el `<input type="radio">` nativo con
   `pointer-events: none` (patrón de chip accesible), así que Playwright debe
   interactuar con el `<label>`/`<span>` visible, no con el rol `radio`
   directamente — no es un bug de producto, pero sí dejó obsoleta la prueba
   `e2e/demo-journey.spec.ts` existente.
3. **`e2e/demo-journey.spec.ts` desactualizado en tres frentes**, todos ajenos
   a este cierre de Fase 3 pero corregidos de paso porque bloqueaban la
   evidencia: aserciones sobre un `<h1>` "Catálogo"/"Colección" que ya no
   existe (pedido explícito del autor esta sesión: el título del navbar basta;
   sobrevive como nombre accesible de la sección de resultados, expuesto como
   landmark `region`); aserciones sobre `section.sp-disclosure` y el texto
   `genre-taste-v1`, que no existen desde que `RecommendationsClient` pasó al
   snapshot stale-while-revalidate con varios estantes; y el flujo de
   estado/valoración/copias de `LibraryControls`, que hoy guarda las tres cosas
   con un único botón "Guardar configuración" y un único
   `data-testid="configuration-feedback"`, no tres acciones separadas.

## Hallazgo operativo: la cola de trabajos del producto está saturada por la población sintética de evaluación

Al intentar obtener un snapshot "ready" para `demo-visitor` la primera vez, el
estado quedó en `stale` más de 30 s. Investigado en vivo:

- La cola `RecommendationRefreshJob` tenía **5.392 filas en `queued`**, de las
  cuales **351 usuarios distintos** son la población sintética de la Fase 3/4
  (`synthetic-*`), con 15 trabajos en cola cada uno. La población de 400
  usuarios se generó para la evaluación offline exclusivamente, pero algo
  encoló también sus refrescos de recomendación **en la cola web/producto**,
  compitiendo con cuentas reales por los mismos 16 workers de un solo hilo por
  algoritmo.
- Además, recrear el contenedor `api` (`docker compose up --build`, necesario
  varias veces hoy para publicar cambios de `apps/web`) deja a los 16
  `recommendation-worker-*` —que usan `network_mode: "service:api"`— con la
  conexión a PostgreSQL rota (`server closed the connection unexpectedly`), y
  el propio manejo de ese fallo también fallaba (`the connection is closed` al
  intentar marcar el trabajo como `FAILED`). `docker compose restart` no lo
  arregla (el namespace de red sigue apuntando al contenedor `api` viejo, ya
  inexistente); hace falta `up -d --force-recreate --no-deps` sobre los 16
  workers.

Ninguno de los dos hallazgos se corrigió estructuralmente esta sesión — el
segundo se resolvió operativamente (recrear los workers); el primero se
sorteó adelantando manualmente en el tiempo (`available_at`/`created_at`) los
15 trabajos de `demo-visitor` para poder obtener un snapshot "ready" y
verificar la evidencia. Ambos quedan anotados aquí para quien retome el tema:
la cola de producto necesita, como mínimo, excluir a los usuarios sintéticos
de evaluación de `enqueue_latest_refresh`, y los workers `network_mode:
"service:api"` necesitan sobrevivir a un rebuild de `api` sin intervención
manual.

## Alcance no tocado

Esta sesión no tocó `apps/api/evaluation/**` ni ningún artefacto/documento del
cierre backend de Fase 3 — solo `apps/web/**`, `e2e/**` y este documento.

## Fuentes canónicas

- [`e2e/recommendations.spec.ts`](../../e2e/recommendations.spec.ts).
- [`e2e/demo-journey.spec.ts`](../../e2e/demo-journey.spec.ts) (correcciones).
- [`.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-VALIDATION.md`](../../.planning/phases/03-explainable-content-recommenders-and-baseline-comparison/03-VALIDATION.md)
  — tabla de verificación QUAL-02 y "Punto 7" que este documento satisface.
- [[2026-09-12 - Cierre backend Fase 3 y limitaciones metodologicas]].
