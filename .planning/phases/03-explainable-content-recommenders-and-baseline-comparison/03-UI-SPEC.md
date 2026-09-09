---
phase: "03"
slug: "explainable-content-recommenders-and-baseline-comparison"
status: approved
shadcn_initialized: false
preset: none
created: "2026-09-08"
reviewed_at: "2026-09-09"
---

# Fase 03 — Contrato de diseño UI

> Contrato visual y de interacción para la Fase 3. Extiende el sistema de diseño de primera
> parte ya implementado; no abre un rediseño ni un panel de investigación. Generado por
> `gsd-ui-researcher` y validado por `gsd-ui-checker` el 2026-09-08.

> **Enmienda del autor — 2026-09-09.** La página pasa a mostrar una sección independiente
> para cada variante de recomendación de producto, con una explicación breve y las señales
> consideradas. Las configuraciones de investigación, los baselines no personalizados y las
> métricas siguen fuera de esta superficie.

La superficie de producto en alcance es `/{locale}/recommendations`. Debe mostrar datos reales
del backend y conservar exactamente el orden descendente de puntuación publicado por cada
recomendador. La evaluación, las métricas, las cohortes, los intervalos, los tests estadísticos,
los tiempos y los estados de ejecución se publican como artefactos e informe reproducible, no
como dashboard web en esta fase.

Fuentes de decisión: `03-CONTEXT.md`, `ROADMAP.md`, `REQUIREMENTS.md`, las decisiones bloqueadas
del autor en esta sesión, `02-UI-SPEC.md` y la implementación actual. Las rutas solicitadas
`apps/web/app/recommendations/page.tsx`, `apps/web/components/game-card.tsx` y
`apps/web/components/site-header.tsx` ya no existen con esos nombres; sus equivalentes vigentes
inspeccionados son `apps/web/app/[locale]/recommendations/page.tsx`,
`apps/web/components/GameCard.tsx` y `apps/web/components/AppShell.tsx`.

---

## Alcance visual bloqueado

El foco visual principal es la primera sección de recomendaciones y su primera tarjeta; el
encabezado de la página establece el contexto y el primer resultado real debe atraer la mirada.

1. La página mantiene el `AppShell`, la navegación autenticada, el selector de idioma, el selector
   de tema y el comportamiento mobile existentes sin alterar orden de foco, etiquetas ni
   breakpoints.
2. El contenido normal de la página es únicamente un `<h1>` breve y secciones de recomendaciones.
   Cada sección algorítmica contiene un `<h2>` visible, una explicación de una o dos frases y
   una lista de tarjetas. La explicación identifica el enfoque y las señales usadas sin exponer
   hashes, metodología experimental, pesos internos sin calibrar ni un bloque de investigación.
3. La página muestra, en este orden, las cinco variantes publicables de contenido: suma ponderada,
   combinación multiplicativa, dos etapas, variante con señal negativa y variante de recencia.
   Después muestra la heurística por género y, al final, el estante relacional de DLC. Una sección
   sin resultados se omite por completo.
4. Cada sección conserva el orden recibido de su endpoint: no reordena por título, rating externo,
   fecha, género ni popularidad, y no agrupa el resultado de forma que altere su ranking. Nunca
   sustituye silenciosamente a otra sección si falla. El estante relacional de DLC conserva el
   orden determinista del endpoint y no se presenta como un ranking por score.
5. No se renderizan fixtures, placeholders de juegos, tarjetas de relleno ni resultados simulados
   en el estado poblado. Un placeholder de **carátula ausente** sí es válido porque representa un
   dato real incompleto y conserva la geometría.
6. Cada recomendación de contenido incluye una razón determinista, breve y fundada en señales
   reales del resultado. La razón ocupa como máximo dos líneas visuales; no se recuperan
   `<details>` de metodología, tablas de contribuciones ni la frase «según tus géneros y
   valoraciones».
7. No se añaden gráficas, tablas de métricas, filtros de runs, un selector de algoritmo, botones de
   exportación, estados de job ni comparaciones estadísticas. Las cinco variantes se muestran como
   secciones fijas y explicadas; no se convierte la página en un panel de laboratorio. Todo lo
   experimental pertenece a los artefactos de evaluación y a la Fase 7.

---

## Design System

| Propiedad | Valor |
|-----------|-------|
| Tool | **none** — sistema de tokens CSS y componentes React de primera parte ya establecido |
| Preset | not applicable |
| Component library | none — componentes manuales en `apps/web/components/` |
| Icon library | none — SVG inline ya existentes; esta fase no añade iconos |
| Font | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| Styling | Tailwind CSS 4 mediante `@import "tailwindcss"` y tokens `@theme` en `apps/web/app/globals.css` |
| Temas | Oscuro por defecto y claro mediante `ThemeToggle`; mismos nombres de token en ambos temas |

No existe `components.json` y no se adopta shadcn. El proyecto ya cuenta con un sistema manual
aprobado, la decisión del autor exige conservar los patrones actuales y añadir un kit implicaría
una dependencia y un lenguaje visual nuevos sin necesidad de fase. Al ser `Tool: none`, se omite
`Component Inventory`: no hay un paquete de componentes que enumerar.

---

## Spacing Scale

Se reutilizan literalmente los tokens existentes; no se crea ningún valor nuevo.

| Token | Valor | Uso en esta fase |
|-------|-------|------------------|
| `xs` | 4px | Separación interna mínima y gap de señales inline |
| `sm` | 8px | Título–metadatos de tarjeta y padding inferior del track |
| `ctl` | 16px | Padding de controles heredados del shell |
| `md` | 16px | Separación título–lista y gap constante entre tarjetas |
| `lg` | 24px | Padding horizontal de página y paneles de estado |
| `xl` | 32px | Padding superior de página |
| `2xl` | 48px | **Separación vertical exacta entre secciones de recomendaciones** |
| `3xl` | 64px | Padding inferior de página |

Excepciones heredadas: target interactivo mínimo de **44×44px**; carátula de estante de
**120×160px** con relación **3:4**. Estas dimensiones son geometría de componente, no nuevos
tokens de espaciado.

Reglas obligatorias:

- `.sp-recommendation-shelves` mantiene `display: grid` y `gap: var(--space-2xl)` en todos los
  anchos. No se usa margen dependiente del número de tarjetas.
- Cada `.sp-shelf` usa `display: grid; gap: var(--space-md)`; su `<h2>` tiene margen `0`.
- Una sección con un solo juego queda alineada al inicio y conserva el mismo hueco inferior que
  una sección llena. No se centra, no estira la tarjeta y no reduce el gap entre secciones.

---

## Typography

Se declaran exactamente cuatro tamaños y dos pesos para esta superficie.

| Rol | Tamaño | Peso | Line Height | Uso |
|-----|--------|------|-------------|-----|
| Body | 16px (`--text-body`) | 400 | 1.5 | Metadatos principales y copy breve de estados |
| Label | 13px (`--text-meta`) | 600 | 1.4 | Metadatos compactos y razón determinista de tarjeta |
| Heading | 20px (`--text-heading`) | 600 | 1.25 | Título visible de cada sección `<h2>` |
| Display | 28px (`--text-display`) | 600 | 1.2 | Título de página `<h1>` |

No se usa peso 700 en los elementos nuevos de esta fase. Los títulos de tarjeta usan 16px/600,
clamp visual de dos líneas y conservan el texto completo en el nombre accesible del enlace. Las
cabeceras de sección envuelven sin truncarse. Metadatos y razón usan slots de altura fija para
que su longitud o ausencia no cambie el alto de la tarjeta.

---

## Color

La distribución 60/30/10 y los pares light/dark existentes no cambian.

| Rol | Valor | Uso |
|-----|-------|-----|
| Dominante (60%) | `--color-surface-base`: `#0d0d12` dark / `#f4f4f7` light | Fondo de página y canalones |
| Secundario (30%) | `--color-surface-raised`: `#17171f` / `#ffffff`; `--color-surface-overlay`: `#1f1f2b` / `#ececf1` | Header, tarjetas, placeholders de carátula y estados |
| Accent (10%) | `--color-accent`: `#8b7cf6` / `#6d5cd6`; strong `#a394ff` / `#5a49c0` | Solo CTA primario de estados, enlaces de texto, navegación activa y selección/foco heredados |
| Destructivo | `--color-danger`: `#f87171` / `#c62828` | Token heredado; **sin uso en esta fase** porque no hay acciones destructivas |

Accent reservado para: CTA «Explorar el catálogo», control «Cargar recomendaciones», enlaces de texto,
marcador de navegación activa y estados seleccionados heredados. No se usa para colorear scores,
rangos, carátulas, títulos de sección ni razones; el orden del ranking no depende del color.
El ring global de foco sigue siendo `2px solid --color-focus-ring` con offset de 2px.

---

## Copywriting Contract

Toda cadena nueva o modificada se incorpora con paridad estricta en `es.ts`, `en.ts` y
`dictionary.ts`. Las explicaciones de sección son copy de producto breve, no documentación
experimental.

| Elemento | Español | Inglés |
|----------|---------|--------|
| Título de página | `Recomendaciones` | `Recommendations` |
| Sección suma ponderada | `Afinidad por contenido` | `Content match` |
| Explicación suma ponderada | `Combina similitud de contenido, tus valoraciones y señales de calidad y popularidad.` | `Combines content similarity, your ratings, and quality and popularity signals.` |
| Sección multiplicativa | `Afinidad equilibrada` | `Balanced content match` |
| Explicación multiplicativa | `Combina las señales para que ninguna compense por completo una afinidad muy baja en otra.` | `Combines signals so that a very low match in one dimension cannot be fully offset by another.` |
| Sección dos etapas | `Afinidad en dos etapas` | `Two-stage content match` |
| Explicación dos etapas | `Primero encuentra obras afines por contenido y después las ordena con las señales escalares.` | `First finds content-similar works, then orders them with scalar signals.` |
| Sección negativa | `Afinidad con tus preferencias en cuenta` | `Content match with your preferences in mind` |
| Explicación negativa | `Refuerza lo que valoras y reduce candidatos de géneros que has valorado negativamente varias veces.` | `Boosts what you rate positively and reduces genres you have rated negatively several times.` |
| Sección de recencia | `Novedades afines a ti` | `Recent matches for you` |
| Explicación de recencia | `Usa las mismas señales personalizadas y añade la novedad de la fecha de lanzamiento.` | `Uses the same personalised signals and adds release-date recency.` |
| Sección por género | `Porque juegas mucho a {genre}` | `Because you play a lot of {genre}` |
| Explicación por género | `Una heurística basada en los géneros de tu actividad y en la valoración del catálogo.` | `A heuristic based on the genres in your activity and the catalogue rating.` |
| Sección de juegos poseídos | `Para tus juegos` | `For games you own` |
| Grupo DLC | `DLC de {game}` | `DLC for {game}` |
| Razón breve de tarjeta | `Coincide contigo en {reasons}.` | `Matches your taste in {reasons}.` |
| Primary CTA | `Explorar el catálogo` | `Browse the catalogue` |
| Empty state heading | `Aún no hay suficiente actividad` | `Not enough activity yet` |
| Empty state body | `Valora o completa algunos juegos y aquí aparecerán recomendaciones.` | `Rate or complete a few games and recommendations will appear here.` |
| Error state | `No se pudieron cargar tus recomendaciones. Inténtalo de nuevo.` | `We couldn't load your recommendations. Try again.` |
| Reintento | `Cargar recomendaciones` | `Reload recommendations` |
| Destructive confirmation | No hay acciones destructivas; no se muestra confirmación. | No destructive actions; no confirmation is shown. |

Copy prohibida en esta fase, aunque queden claves históricas en el diccionario:

- `Recomendaciones según tus géneros y valoraciones` / `Recommended by your genres and ratings`.
- Explicaciones largas sobre cómo se genera el ranking.
- Párrafos con `algorithm_id`, limitaciones, hashes, versiones o metodología.
- La introducción del estante DLC; el título visible basta.

Las razones de tarjeta enumeran como máximo dos señales localizadas presentes en la evidencia
real, por ejemplo género, plataforma, franquicia, desarrollador o valoración externa. Nunca
atribuyen una señal ausente ni usan texto generativo.

---

## Contrato de pantalla — `/{locale}/recommendations`

### Estructura y orden

1. `AppShell` heredado.
2. `<main class="sp-page">` con `<h1 class="sp-h1">Recomendaciones</h1>`.
3. Contenedor `.sp-recommendation-shelves`.
4. Sección «Afinidad por contenido» (`content-cbf-weighted-v1`).
5. Sección «Afinidad equilibrada» (`content-cbf-multiplicative-v1`).
6. Sección «Afinidad en dos etapas» (`content-cbf-twostage-v1`).
7. Sección «Afinidad con tus preferencias en cuenta» (`content-cbf-neg-v1`).
8. Sección «Novedades afines a ti» (`recency-v1`).
9. Estantes reales por género (`genre-taste-v1`), en el orden determinista devuelto por su contrato.
10. Sección «Para tus juegos», solo cuando existe al menos un grupo real con contenido.

Cada sección algorítmica usa `<section aria-labelledby>` y una `<ol>` porque el orden comunica
ranking. La explicación se asocia al título mediante `aria-describedby` y no contiene información
distinta de la copy aprobada. El frontend itera el array recibido sin `sort()`. La clave estable es
`work_id`; un empate ya llega resuelto por el backend. La sección relacional de DLC usa `<ul>` y no
muestra posición ni score inventados.

### Geometría uniforme

- Todos los tracks reutilizan scroll horizontal nativo, `gap: 16px` y `scroll-snap-type: x
  proximity`; no se añaden flechas hover-only.
- Cada `<li>` de estante ocupa **120px de ancho y 288px de alto**. La carátula ocupa
  **120×160px**; debajo se reservan siempre los mismos slots: título de dos líneas, metadatos de
  una línea y razón de hasta dos líneas.
- Cuando un slot no aplica se conserva su altura mediante estructura/clase de layout, no mediante
  texto falso ni caracteres invisibles. La tarjeta completa sigue siendo un único enlace.
- Una portada remota ausente o fallida se reemplaza por `.sp-cover-placeholder` dentro de la misma
  caja de 120×160px, sin cambio de layout.
- Los metadatos de una línea terminan en ellipsis visual; título y razón hacen clamp a dos líneas.
  El nombre accesible del enlace conserva el título completo.
- El `ScorePill` de valoración del catálogo no representa la puntuación interna del algoritmo. No
  se introduce una segunda puntuación visual si el backend no ofrece una escala de producto
  calibrada; el orden de `<ol>` es la representación del ranking.

### Responsive e interacción

- Desktop y mobile mantienen el mismo DOM y orden semántico. Los estantes desbordan solo dentro de
  `.sp-shelf-track`; la página nunca genera scroll horizontal a 320px ni a 400% de zoom.
- Touch, rueda/trackpad y navegación por Tab permiten recorrer tarjetas. Al enfocar una tarjeta
  fuera del viewport, el navegador desplaza el track hasta hacerla visible.
- No existe interacción exclusiva de hover. Cada tarjeta abre la ficha ya existente y mantiene un
  target mínimo de 44px.
- El menú mobile conserva focus trap, cierre con Escape y devolución del foco. `LanguageToggle`,
  `ThemeToggle` y `AccountSwitcher` mantienen etiquetas accesibles y persistencia actuales.
- Se respeta `prefers-reduced-motion`; el scroll y los skeletons no añaden animación obligatoria.

### Orden y fidelidad de datos

- La respuesta principal debe identificar `algorithm_id`, versión de features, versión de modelo,
  snapshot y score, pero la UI solo usa esos campos para verificar identidad y mantener el orden;
  no los convierte en prosa de metodología.
- Cada tarjeta corresponde a una obra real elegible. No se crean DTOs de muestra en producción.
- Los juegos consumidos, fechas futuras y ediciones alternativas ya deben llegar excluidos por el
  contrato del backend; el frontend no los reintroduce ni realiza una segunda clasificación.
- Una razón se renderiza solo si sus tokens de evidencia pertenecen al mismo resultado versionado.
  Si falta la razón de un ítem, la tarjeta conserva su slot y el resultado sigue visible, pero el
  caso se registra como respuesta parcial y no se inventa copy.

---

## Contratos de componentes de primera parte

| Componente | Contrato de Fase 3 |
|------------|--------------------|
| `AppShell` | Se reutiliza sin cambios funcionales; navegación, i18n, tema, focus trap y orden de foco quedan congelados. |
| `ContentRecommendationShelf` | Renderiza una variante de contenido como `<section>` con `<h2>`, explicación breve y `<ol>`; conserva el array del endpoint sin reordenar, identifica el `algorithm_id` en el mapeo interno y pasa a `GameCard` la razón real. |
| `RecommendationShelf` | Renderiza resultados reales de `genre-taste-v1` con su explicación breve localizada; conserva el orden por score dentro de cada estante y no muestra metodología experimental. |
| `OwnedGamesDlcShelf` | Omite `intro`; oculta grupos vacíos y usa `<ul>` porque es una relación determinista, no una puntuación algorítmica. |
| `GameCard` | Mantiene enlace único, portada 3:4, título completo accesible y placeholder lawful. En variante `shelf`, fija 120×288px y añade razón breve en slot de dos líneas cuando exista. |
| Estado de carga de ruta | Skeleton geometry-matched: título de página, cabeceras de las secciones configuradas y cuatro tarjetas 120×288px por track; skeletons `aria-hidden`, un único `role="status" aria-live="polite"`. |

No se introduce un componente de dashboard, tabla de métricas, chart, selector de run ni paquete
de UI de terceros.

---

## Estados de datos e interacción

| Estado | Contrato |
|--------|----------|
| Loading | Se muestra el skeleton de ruta con la misma geometría final. Solo el mensaje localizado «Cargando…» / «Loading…» se anuncia una vez. |
| Populated | Secciones reales, título, explicación breve, listas semánticas y orden del backend intacto. La explicación no muestra pesos, hashes ni métricas de evaluación. |
| Empty parcial | Una sección opcional sin resultados se omite por completo, incluido su `<h2>`; no deja un hueco extra ni una lista vacía. |
| Empty total | Si ninguna sección tiene resultados reales, se muestra el empty state y CTA del Copywriting Contract; nunca tarjetas de relleno. |
| Error parcial | La sección afectada conserva su `<h2>` y muestra el error breve con «Cargar recomendaciones»; las demás secciones reales permanecen visibles. No se sustituye por otro ranking. |
| Error total | Se muestra un único `role="alert"`, el error y «Cargar recomendaciones». El shell continúa operativo. |
| Datos incompletos | Carátula ausente usa placeholder fijo; metadatos ausentes dejan su slot; razón ausente no se inventa. |
| Unauthorized | Redirección existente a `/{locale}/login?next=...`; no se expone contenido personal antes ni después del redirect. |

El reintento vuelve a solicitar la sección o página fallida y preserva locale, sesión y posición de
lectura razonable. No existen mutaciones optimistas ni acciones destructivas.

---

## UI Considerations

> Cobertura de estados shape-rooted conforme a `ui-consideration-probe.md`. La copy de estados
> vacío y error se referencia desde `## Copywriting Contract` y no se duplica aquí.

Applicable state considerations resolved: **6 covered, 2 backstop, 0 unresolved**.

| Categoría | Elemento(s) | Estado | Resolución / Motivo |
|-----------|-------------|--------|---------------------|
| empty | Colección de secciones y listas | ✅ covered | Una sección vacía se omite; si todas están vacías se renderiza el estado del Copywriting Contract y nunca una tarjeta placeholder. |
| loading | Página y tracks de recomendaciones | ✅ covered | Skeletons geometry-matched reservan cabeceras y tarjetas 120×288px; están ocultos al árbol accesible y un único status anuncia la carga. |
| error | Página y sección individual | ✅ covered | El error total usa `role="alert"`; el parcial queda bajo su título con retry localizado y no borra las demás listas reales. |
| populated | Listas algorítmicas | ✅ covered | `<ol>` conserva exactamente la secuencia score-desc del backend; cada tarjeta muestra datos reales y razón fundada cuando está disponible. |
| partial | Tarjeta y sección con campos/fetch incompletos | ✅ covered | Portada y metadatos ausentes preservan slots; una sección fallida no se sustituye ni oculta silenciosamente. |
| overflow | Tracks, títulos y metadatos | ✅ covered | Solo el track hace scroll horizontal; el título y la razón se acotan a dos líneas, el meta a una, y no hay overflow de página. |
| zero-one-many | Cada estante | 🧪 backstop | Zero omite la sección, one queda alineado al inicio sin estirarse y many activa scroll; un test visual debe medir altura y gap idénticos. |
| long-text | i18n, títulos, razones y cabeceras | 🧪 backstop | A 30% de expansión y 400% de zoom las cabeceras envuelven, las tarjetas mantienen altura uniforme y el texto completo sigue accesible; requiere prueba visual held-out. |

La navegación heredada no cambia: sus estados de overflow y long-text continúan cubiertos por el
contrato aprobado de la Fase 2.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Ninguno | Ninguno | No aplica — `Tool: none`, sin shadcn ni registros de terceros |

---

## Verificación exigida al planner/executor

1. Test de contrato frontend: los `work_id` renderizados en cada `<ol>` coinciden, en el mismo
   orden, con el payload score-desc; no hay `sort()` ni agrupación cliente sobre la lista principal.
2. Test de producción: ningún estado poblado usa fixtures, títulos placeholder o resultados
   inventados; el placeholder de portada solo aparece cuando `cover.is_placeholder` o falla la
   imagen real.
3. Test i18n: paridad de claves ES/EN y ausencia en el DOM de toda la copy prohibida.
4. Playwright desktop y 320px: una sección con 1 ítem y otra con muchos mantienen 48px de gap
   vertical; todas las tarjetas de estante miden 120×288px con tolerancia de 1px.
5. Playwright con títulos, plataformas y razones largas: no hay scroll horizontal de página; el
   track conserva scroll propio y el texto accesible contiene el título completo.
6. Test de estados loading, empty total, error total, error parcial y metadatos/cover/razón
   ausentes; ningún fallo parcial permite que otra sección parezca ser el ranking principal.
7. Pase axe-core en dark y light, navegación completa por teclado, foco visible y comprobación de
   reflow a 400% / 320px. Los skeletons no producen anuncios repetidos.
8. Test de alcance: se renderizan las cinco secciones de contenido con su `algorithm_id` y copy
   aprobada; no se renderizan gráficas, tablas de métricas, selectores de algoritmo/run ni
   controles de exportación en `/{locale}/recommendations`.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS (FLAG no bloqueante resuelto declarando el foco visual)
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS
- [x] Dimension 7 Inventory Provenance: PASS — no aplica con `Tool: none`

**Approval:** approved
