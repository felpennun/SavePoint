---
phase: "2"
slug: "governed-corpus-external-ratings-evaluation-contract-and-fir"
status: approved
shadcn_initialized: false
preset: none
created: "2026-09-06"
reviewed_at: "2026-09-06"
---

# Phase 2 — UI Design Contract

> Contrato visual y de interacción para la Fase 2. **Extiende** el sistema de diseño ya
> aprobado en `01.1-UI-SPEC.md` (tokens light+dark, marca Cristal, escala tipográfica,
> componentes de primera parte en `apps/web/components/`). **No es un rediseño**: es un pase
> de producto dirigido más superficies nuevas concretas. Generado por gsd-ui-researcher,
> verificado por gsd-ui-checker.
>
> Prosa en español (convención `CONVENTIONS.md` §1). Se mantienen en inglés: nombres de token
> CSS, nombres de componente, rutas de fichero, IDs de requisito, claves de copy. Las cadenas
> de UI visibles se dan **bilingües es + en** (el i18n del proyecto exige paridad,
> `apps/web/tests/i18n.test.ts`).

Requisitos en alcance con impacto de UI: **CAT-02** (filtros multi-selección — refinamiento),
**QUAL-05** (nuevo pase de producto sobre catálogo / filtros / ficha / recomendaciones),
**REC-03 / REC-06 / REC-07 / REC-08 / REC-09** (primer recomendador de contenido: lista
ordenada, arranque en frío, exclusiones, explicación determinista, versiones visibles),
**D-24** (estante "Novedades" en la home), **D-15** (estante "Para tus juegos" / DLC),
**D-07 / D-09** de 01.1 heredado (ratings externos + rating mezclado en vivo),
**D-01.1-10-a** (overflow de la nav autenticada <430px).

Fuera de alcance de UI (sin superficie de usuario esta fase): el harness de evaluación y los
usuarios sintéticos (paneles de investigador → Fase 7), chips/filtro por tienda (diferido),
estante "Tendencia" (Fase 6), el conjunto completo de métricas más-allá-del-acierto (Fase 3).

---

## Decisiones de contrato (resueltas con el autor — 2026-09-06)

Las 6 preguntas abiertas fueron respondidas **"OK a todo"**. No queda ningún ítem de contrato
pendiente de decisión; el checker solo valida ejecución.

| # | Pregunta | Resolución |
|---|----------|-----------|
| P1 | UX de filtros multi-selección | `<details>` "menú de faceta" por campo multi (Género, Plataforma) con lista de `<input type="checkbox">`; **un chip activo por valor seleccionado**; parámetros de URL **repetidos** (`?genre=rpg&genre=strategy&platform=switch`); `parseFilters` lee **todos** los valores, no `first()`; etiqueta de semántica visible (géneros = AND "contiene todos", plataformas = OR "disponible en alguna"). Sin `<select multiple>` nativo, sin combobox de tokens con JS. |
| P2 | Rating "general" mezclado (D-09) | **Un solo número** en `ScorePill` (0–100). Texto visible del pill: `"Valoración IGDB"` → **`"Valoración"`** en tarjeta y ficha. Línea de desglose en **texto plano solo en la ficha**: "Basada en la valoración de N usuarios de IGDB y M de SavePoint". Sin tooltip. Sin dato → "sin valoración". |
| P3 | Orden de la ficha de juego | Sinopsis (`summary` de IGDB, clamp ~6 líneas + "Mostrar más") **antes** de `LibraryControls`, estilo Letterboxd. Orden completo abajo en Screen Contract 2. |
| P4 | Explicación del recomendador + composición de la página | Frase corta determinista + `<details>` "Por qué" con tabla de contribución por género + fila de término de rating + pie "Variante: {algorithm_id}"; la etiqueta de variante aparece **además** una vez en la cabecera de sección. Página de recomendaciones = **3 secciones etiquetadas coexistiendo**: "Recomendado para ti" (ranking nuevo del laboratorio de contenido), estantes por género de `rank_genre_taste_v1` (se mantienen de 01.1), "Para tus juegos" (DLC de juegos poseídos). |
| P5 | Ventana de "Novedades" (D-24) | N = **6 meses**; `first_release_date` desc, desempate `canonical_slug`; máx **20** ítems; mismo tratamiento visual que el estante de popularidad; **encima** del estante de popularidad; visible logueado y deslogueado; si 0 lanzamientos en la ventana → se **oculta el estante entero**. |
| P6 | Overflow de nav autenticada <430px (D-01.1-10-a) | En `<md`, `ThemeToggle` y `AccountSwitcher` pasan a **solo icono** (se oculta el texto visible, se mantiene `aria-label`); la etiqueta vuelve en `≥md`. Paridad de DOM preservada. |

---

## Design System

Sin cambios estructurales respecto a 01.1. Tabla de referencia:

| Property | Value |
|----------|-------|
| Tool | **none** — sistema de tokens CSS de primera parte (D-07). shadcn/Radix/Base UI **no** adoptados; el gate de aprobación de dependencias + D-07 pesan en contra de una UI kit. |
| Preset | not applicable |
| Component library | none — componentes React server/client hechos a mano en `apps/web/components/` |
| Icon library | none — inline SVG, sin dependencia de runtime (≤10 glifos: chevron, filter, star, star-half, check, account/person, sun, moon, x, arrow). |
| Font | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` — sin cambio, sin web-font. |
| Styling | Tailwind v4 (`@import "tailwindcss"` + `@theme` en `apps/web/app/globals.css`) vía `@tailwindcss/postcss`. Tokens = custom properties CSS consumidas por `var()` / valores arbitrarios de Tailwind. |
| Color scheme | **Dark + light**, dark por defecto, `ThemeToggle` persistido (cookie `sp-theme`, aplicado server-side en `app/[locale]/layout.tsx`, sin flash). |

### Token additions this phase (el executor las añade a `@theme` en `globals.css`)

Extienden el bloque existente; **no** reemplazan ningún token de 01.1.

```css
/* Elevación real para superficies que se solapan con contenido debajo
   (el popover de faceta multi-selección flota sobre la rejilla de tarjetas;
   01.1 diferenciaba superficies solo por fondo + borde de 1px, insuficiente
   cuando hay solapamiento). */
--shadow-overlay: 0 6px 20px -4px rgba(0, 0, 0, 0.45);      /* tema dark */

/* Bloque de esqueleto de carga (geometry-matched). Estático bajo
   prefers-reduced-motion (regla ya presente en globals.css). */
--color-skeleton-base: var(--color-surface-overlay);
--color-skeleton-sheen: var(--color-surface-raised);
```

```css
:root[data-theme="light"] {
  --shadow-overlay: 0 6px 20px -4px rgba(20, 20, 30, 0.18);  /* tema light */
}
```

Todo lo demás (superficies, texto, accent, status, danger/success, focus ring, radios, escala
tipográfica, escala de espaciado, `--color-rating`, `--color-score-*`) se **reutiliza literal**
de `globals.css`. No se añade ningún token de color de marca ni de acento nuevo.

### Barra de contribución del recomendador ("Por qué")

Elemento de visualización de datos monocromo, **deliberadamente no accent**: pista =
`--color-surface-overlay`; relleno = `--color-text-secondary`; valor numérico también impreso
como texto (`{pct}%`) para no depender solo del color/longitud. No requiere token nuevo.

---

## Component Inventory

**Tool: none** — el proyecto no tiene design system instalado, no hay paquete que enumerar ni
línea de procedencia que registrar (gsd-ui-checker Dimensión 7 no aplica con `Tool: none`).
Los contratos de componente de primera parte están en `## First-Party Component Contracts`.

---

## Spacing Scale

Sin cambios respecto a 01.1. Valores declarados (todos múltiplos de 4), consumidos como
`--space-*`:

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gap icono-etiqueta, padding interior de chip, gap entre estrellas, gap entre checkbox y label en el menú de faceta |
| sm | 8px | Espaciado compacto, título-a-meta de tarjeta, gap de fila de chips |
| ctl | 12px | Padding vertical de controles compactos / header |
| md | 16px | Gap por defecto — rejilla de catálogo, tarjeta-a-tarjeta, campos de formulario, filas de la tabla de contribución |
| lg | 24px | Padding de sección, agrupación interna de la barra de filtros, padding del popover de faceta |
| xl | 32px | Gaps de layout, espacio sobre/bajo la barra de filtros |
| 2xl | 48px | Cortes de sección mayores (entre estantes de recomendación, entre las 3 secciones de la página de recomendaciones) |
| 3xl | 64px | Ritmo vertical de página en viewports anchos |

Excepciones (heredadas, sin cambio): **44px** de target interactivo mínimo
(`min-height: 2.75rem` en `button, a, input, select, textarea`, WCAG 2.5.8) — es un suelo, no
un valor de escala. `aspect-ratio: 3 / 4` fijo para portadas; anchos de render 156px (rejilla),
120px (estante), 280px (héroe de ficha, 200px `<820px`).

---

## Typography

Sin cambios respecto a 01.1. Cuatro tamaños (**13 / 16 / 20 / 28**), dos pesos
(**400 regular, 600 semibold**), consumidos como `--text-*` / `--leading-*`.

| Role | Size | Weight | Line Height | Aplicado a (adiciones de esta fase en cursiva) |
|------|------|--------|-------------|-----------------------------------------------|
| Body | 16px (`--text-body`) | 400 | 1.5 | Copy de párrafo, filas de lista, valores, enlaces en prosa, *la sinopsis de IGDB en la ficha* |
| Label | 13px (`--text-meta`) | 600 | 1.4 | Meta de tarjeta, chips de género, score pill, `<label>`, texto de filter-chip, línea de conteo/estado, *cabeceras de columna de la tabla de contribución*, *`<summary>` del menú de faceta*, *etiqueta de variante del recomendador*, *línea de desglose de rating en la ficha* |
| Heading | 20px (`--text-heading`) | 600 | 1.25 | `<h2>` de sección (barra de filtros, títulos de estante, subsecciones de ficha, *cabeceras de las 3 secciones de la página de recomendaciones*) |
| Display | 28px (`--text-display`) | 600 | 1.2 | `<h1>` de página |

Reglas de texto largo (heredadas + esta fase):
- Título de tarjeta: clamp a **2 líneas**; el título completo sigue siendo el texto accesible
  del enlace y se muestra sin clamp en la ficha.
- Fila de chips de género: hasta **3**, luego `+N` como chip no interactivo.
- *Sinopsis de IGDB en la ficha: clamp a **~6 líneas** (`-webkit-line-clamp: 6`) con un
  `<details>`/botón "Mostrar más" / "Show more" que la expande sin clamp; "Mostrar menos" /
  "Show less" la vuelve a colapsar.*
- *Frase de explicación del recomendador: una sola línea, sin clamp, envuelve libremente.*
- Aceptación incluye 30% de expansión de texto y reflow a 400% de zoom (heredado).

---

## Color

Sin cambios en la división **60 / 30 / 10**, ni en la lista reservada de accent, ni en las
asignaciones semánticas. Los valores hex viven en `globals.css` (dark) y en
`:root[data-theme="light"]` (light); solo cambian los valores entre temas.

| Role | Token (dark) | Usage |
|------|--------------|-------|
| Dominante (60%) | `--color-surface-base` `#0d0d12` | Fondo de página, columna principal, canalones de rejilla |
| Secundario (30%) | `--color-surface-raised` `#17171f` (tarjetas, header/nav, barra de filtros, paneles) + `--color-surface-overlay` `#1f1f2b` (menús desplegables, *popover de faceta*, chip hover/seleccionado, panel del account switcher, *pista de la barra de contribución*, *fondo del score pill*) | Superficies elevadas y de chrome |
| Accent (10%) | `--color-accent` `#8b7cf6` / `--color-accent-strong` `#a394ff` (hover) con `--color-accent-on` `#16121f` para texto sobre relleno accent | Ver lista reservada abajo |
| Destructivo | `--color-danger` `#f87171` | "Borrar valoración"; "Quitar copia" (ambos heredados de 01.1). **Sin acciones destructivas nuevas esta fase.** |

**Accent reservado para — lista explícita (nunca "todos los elementos interactivos"):**
1. Relleno del botón de acción primaria — uno por pantalla: "Aplicar filtros" (catálogo),
   "Añadir a la colección" / "Actualizar estado" (ficha), submit de login/registro.
2. Enlaces de texto dentro de prosa / body copy (enlace de fuente en procedencia, enlaces
   "Explorar el catálogo" de estados vacíos, "Borrar todos los filtros").
3. Ítem de navegación activo — marcador `aria-current="page"` en el header.
4. Marcador de página actual en la paginación.
5. Contorno de estado enfocado/seleccionado en un `<select>` / checkbox de faceta / chip (junto
   con el `--color-focus-ring` global, que sigue siendo dorado).

**Accent NO se usa para:** bordes de tarjeta, marcos de portada, el score pill (usa
`--color-score-*`), pills de estado de backlog (usan `--color-status-*`), estrellas de
valoración personal (usan `--color-rating`), *la barra de contribución del recomendador* (usa
`--color-text-secondary` sobre `--color-surface-overlay`), *el chip de faceta seleccionada*
(usa `--color-surface-overlay` + check en `--color-text-primary`), ni fondos de hover genéricos
(usan `--color-surface-overlay`).

Contraste: cada pareja nueva debe superar WCAG 2.2 AA (4.5:1 texto body, 3:1 texto grande / UI)
contra su fondo **en ambos temas**, verificado con el pase axe-core (QUAL-03 / QUAL-05).
Conocidos-buenos (dark): `--color-text-secondary #b8b8c4` sobre `--color-surface-overlay
#1f1f2b` ≈ 8.6:1 (relleno de barra de contribución y su texto). Figuras del tema light: en
`01.1-UI-SPEC.md › Theming`.

---

## Copywriting Contract

EN/ES **paralelo** — cada cadena nueva va en `apps/web/i18n/en.ts` y `es.ts` (paridad
test-enforced). Se reutilizan claves existentes donde ya existen; las nuevas se listan con su
ruta de anidamiento.

### Filas requeridas por la plantilla

| Element | Copy (EN) | Copy (ES) |
|---------|-----------|-----------|
| Primary CTA (superficie principal cambiada: catálogo) | Apply filters | Aplicar filtros |
| Empty state heading (recomendador de contenido sin historial suficiente) | Not enough history yet | Aún no hay suficiente historial |
| Empty state body (recomendador de contenido, arranque en frío) | Rate or complete a few games. Meanwhile, here's a cold-start view based on popular genres. | Valora o completa algunos juegos. Mientras tanto, te mostramos una vista de arranque en frío basada en géneros populares. |
| Error state (recomendador de contenido) | We couldn't build your recommendations. Try again. | No se pudieron generar tus recomendaciones. Inténtalo de nuevo. |
| Destructive confirmation | **Ninguna acción destructiva nueva en esta fase.** "Borrar valoración" / "Quitar copia" siguen siendo en línea, de bajo riesgo y reversibles (contrato 01.1). La gobernanza del corpus (marcar `in_corpus=False`) es de backend/CLI, sin UI de usuario. | — |

### Conjunto completo de cadenas nuevas (EN / ES paralelo)

| Key path | EN | ES |
|----------|----|----|
| `card.score.label` (**NEW** — texto visible del pill; sustituye a "IGDB rating") | Rating | Valoración |
| `card.score.aria` (**valor revisado** — quita "IGDB"; la clave se mantiene) | Rating {n} out of 100 | Valoración {n} de 100 |
| `card.score.none` (**valor revisado** — quita "IGDB") | No rating | Sin valoración |
| `detail.ratingBreakdown` | Based on ratings from {igdb} IGDB users and {savepoint} SavePoint users. | Basada en la valoración de {igdb} usuarios de IGDB y {savepoint} de SavePoint. |
| `detail.ratingBreakdownExternalOnly` | Based on ratings from {igdb} IGDB users. | Basada en la valoración de {igdb} usuarios de IGDB. |
| `detail.ratingBreakdownLocalOnly` | Based on ratings from {savepoint} SavePoint users. | Basada en la valoración de {savepoint} usuarios de SavePoint. |
| `detail.synopsis.heading` | Summary | Sinopsis |
| `detail.synopsis.showMore` | Show more | Mostrar más |
| `detail.synopsis.showLess` | Show less | Mostrar menos |
| `catalogue.facet.genreSemantics` | Shows games that have all selected genres. | Muestra juegos que tienen todos los géneros seleccionados. |
| `catalogue.facet.platformSemantics` | Shows games available on any selected platform. | Muestra juegos disponibles en alguna de las plataformas seleccionadas. |
| `catalogue.facet.selectedCount` (count) | zero: "Any" / one: "1 selected" / many: "{n} selected" | zero: "Cualquiera" / one: "1 seleccionado" / many: "{n} seleccionados" |
| `catalogue.facet.clear` | Clear | Quitar |
| `catalogue.facet.searchInList` | Filter this list | Filtrar esta lista |
| `catalogue.filters.genrePlural` | Genres | Géneros |
| `catalogue.filters.platformPlural` | Platforms | Plataformas |
| `catalogue.chip.genre` | Genre: {value} | Género: {value} |
| `catalogue.chip.platform` | Platform: {value} | Plataforma: {value} |
| `recommendations.forYou.heading` | Recommended for you | Recomendado para ti |
| `recommendations.forYou.intro` | A ranked list from the content-based recommender. Variant: {variant}. | Una lista ordenada del recomendador basado en contenido. Variante: {variant}. |
| `recommendations.forYou.variantLabel` | Variant: {variant} | Variante: {variant} |
| `recommendations.forYou.versionsLabel` | Model {model} · features {features} · data {data} | Modelo {model} · features {features} · datos {data} |
| `recommendations.forYou.explanationSentence` | Matches your taste for {genres}, and its rating among similar games. | Coincide con tu gusto por {genres} y su valoración entre juegos similares. |
| `recommendations.forYou.coldStartBadge` | Cold-start view | Vista de arranque en frío |
| `recommendations.forYou.error` | We couldn't build your recommendations. Try again. | No se pudieron generar tus recomendaciones. Inténtalo de nuevo. |
| `recommendations.forYou.excludedNote` | Games already in your collection are not shown. | No se muestran los juegos que ya están en tu colección. |
| `recommendations.why.toggle` | Why | Por qué |
| `recommendations.why.heading` | Why this recommendation | Por qué esta recomendación |
| `recommendations.why.genreContribution` | Genre contribution | Contribución por género |
| `recommendations.why.contributionValue` | {pct}% | {pct} % |
| `recommendations.why.ratingTerm` | Rating term | Término de valoración |
| `recommendations.why.ratingTermFallback` | No rating for this game — the median of its genres was used. | Sin valoración para este juego — se usó la mediana de sus géneros. |
| `recommendations.why.variantFooter` | Variant: {variant} | Variante: {variant} |
| `recommendations.dlc.heading` | For games you own | Para tus juegos |
| `recommendations.dlc.intro` | Downloadable content for games already in your collection. | Contenido descargable de juegos que ya tienes en tu colección. |
| `recommendations.dlc.baseGameLabel` | DLC for {game} | DLC de {game} |
| `home.newReleases.heading` | New releases | Novedades |
| `home.newReleases.explainer` | Recently released games from the governed corpus. | Juegos del corpus gobernado lanzados recientemente. |
| `common.showLess` | Show less | Mostrar menos |
| `nav.themeToggleAria` (reafirma, ya existe como `theme.toggle.switchTo*`) | — reutiliza `theme.toggle.switchToDark` / `switchToLight` | — |

Claves reutilizadas sin cambio: `catalogue.filters.*` (heading, apply, clearAll, anyOption,
mobileToggle, unavailable, emptyHeading, emptyBody, activeLabel), `catalogue.sort.*`,
`catalogue.gamesCount` / `filteredCount`, `catalogue.searchLabel`, `recommendations.heading` /
`intro` / `excludedNote` / `methodHeading` / `methodAlgorithm` / `shelfHeading` / `shelfEvidence`
/ `cardEvidence` / `emptyHeading` / `emptyBody` / `emptyCta` / `error`, `common.retry` /
`common.showMore` / `common.coverMissing`, `detail.genres` / `detail.platforms` /
`detail.releaseDate` / `detail.attribution` / `detail.seeSources`, `provenance.heading`,
`nav.*`, `theme.toggle.*`, `account.*`.

`card.score.aria` y `card.score.none` **cambian de valor** (quitan "IGDB"); las claves se
mantienen, así que la paridad de `i18n.test.ts` no se altera.

---

## Screen Contracts

### Navbar (todas las páginas) — `components/AppShell.tsx` (P6, D-01.1-10-a)

Sin cambios de estructura respecto a 01.1 salvo el arreglo de overflow:

- **`< md`:** `ThemeToggle` y `AccountSwitcher` se renderizan **solo icono**. El texto visible
  ("Tema: {estado}", "Cuenta simulada: {alias}") se oculta con `.visually-hidden` /
  `hidden md:inline`; el `aria-label` y el `aria-pressed` se mantienen intactos. El glifo
  (sol/luna; avatar/inicial + chevron) queda como único contenido visible. Ambos siguen en la
  barra del header (no dentro del `MobileMenu`), como en 01.1, pero ahora la fila cabe a 320px
  sin scroll horizontal de página.
- **`≥ md`:** idéntico a 01.1 — icono + etiqueta de texto visible.
- El orden del DOM es **el mismo** a todo ancho (solo cambia la visibilidad del `<span>` de
  texto vía clase utilitaria). El `LoginIconButton` (deslogueado) ya era solo icono en 01.1 y
  no cambia.
- Objetivos de 44px, ring de foco visible, operables por teclado — sin cambio.

### 1. Home (`app/[locale]/page.tsx`) — D-24 estante "Novedades"

Añade **un estante nuevo** sobre el estante de popularidad existente, en ambos estados
(deslogueado y logueado):

- **Posición:** después del contenido principal de la home (muestra de catálogo deslogueado /
  fila "Retoma donde lo dejaste" logueado) y **encima** del `RecommendationStrip` de
  popularidad, separado por el mismo divisor (`border-top` + `--space-2xl`).
- **Cabecera:** `<h2>` `home.newReleases.heading` ("Novedades" / "New releases") +
  explicador `home.newReleases.explainer` (Label, `--color-text-muted`).
- **Contenido:** fila horizontal desplazable de `GameCard` variante `shelf` (portada 120px),
  hasta **20** ítems, ordenados por `first_release_date` desc con desempate `canonical_slug`,
  ventana = últimos **6 meses**. Mismo tratamiento visual que el estante de popularidad
  (`.sp-shelf` / `.sp-shelf-track`).
- **Vacío:** si 0 juegos del corpus gobernado en la ventana → **el estante entero no se
  renderiza** (ni cabecera ni fila). No hay estado vacío visible.
- **Fallo de carga:** el estante se omite; nunca deja la página en blanco (contrato "partial"
  heredado). El resto de la home renderiza igual.

`RecommendationStrip` de popularidad: se mantiene tal cual, debajo, sigue etiquetado como
agregado no personalizado.

Cobertura de estados: empty (estante oculto), loading (esqueleto: 1 cabecera + 6 bloques de
portada, `aria-hidden`, un `role="status"` "Cargando…"), error (estante omitido), partial
(fallo del estante no afecta al resto), overflow (la fila hace scroll dentro de su propio
contenedor, nunca scroll horizontal de página), zero-one-many (n/a — sin conteo visible).

### 2. Game detail (`app/[locale]/games/[id]/page.tsx`) — CAT-03 / QUAL-05 / P2 / P3 / D-15

Dos columnas en `≥ md`, apiladas en móvil (`.sp-detail-grid`, ya existe).

**Columna izquierda:** héroe de portada 280×373 (`aspect-ratio 3/4`, `radius-card`), hotlink
IGDB `t_cover_big`, `CoverImage` con fallback `onError` al placeholder de primera parte.
Sin cambio respecto a 01.1.

**Columna derecha — orden exacto (P3):**

1. **`<h1>` título** (Display) + año al lado (Body, `--color-text-secondary`).
2. **Score pill + desglose de rating** (P2):
   - `ScorePill` con el número **mezclado** 0–100 (externo IGDB + valoraciones de usuarios de
     SavePoint según se acumulan, D-09). Texto visible del pill = `card.score.label`
     ("Valoración" / "Rating") — **ya no "Valoración IGDB"**.
   - Directamente debajo, **una línea de texto plano** (Label, `--color-text-muted`) con el
     desglose: `detail.ratingBreakdown` "Basada en la valoración de N usuarios de IGDB y M de
     SavePoint". Variantes `…ExternalOnly` / `…LocalOnly` según qué fuente tenga conteo > 0.
   - Sin ninguna de las dos fuentes con dato → **no se renderiza el pill**; en su lugar
     `card.score.none` ("Sin valoración") visible como texto (Label, `--color-text-muted`).
     Este juego queda excluido del sort por rating y del filtro `min_rating` (D-07, backend).
   - **Sin tooltip, sin segundo pill.**
3. **Sinopsis** (`summary` de IGDB, **NUEVO**): `<h2>` `detail.synopsis.heading`
   ("Sinopsis" / "Summary") + prosa Body. Clamp a **~6 líneas**; si el texto excede, un
   `<details>` / botón "Mostrar más" (`detail.synopsis.showMore`) la expande sin clamp y
   "Mostrar menos" (`detail.synopsis.showLess`) la colapsa. Si IGDB no trae `summary` → **la
   sección entera se omite** (nunca una cabecera vacía).
4. **Géneros** — fila de chips (Label), enlaces a `/{locale}/catalogue?genre={slug}`.
5. **Plataformas** — lista de texto plano (Label), de `releases[].platform`, de-duplicada.
6. **Fecha de lanzamiento** — fecha localizada completa, o se omite la fila.
7. **`LibraryControls`** (client, existente) — botón primario accent "Añadir a la colección" /
   "Actualizar estado"; estado como grupo segmentado `StatusPill`; valoración como 5 estrellas
   `--color-rating`; "Borrar valoración" en línea `--color-danger`. Copias sin cambio.
8. **Estante "Para tus juegos"** (D-15, **NUEVO**, solo si el usuario autenticado **posee el
   juego base** de esta ficha… o, en la ficha de un juego base, si posee ese juego y tiene
   DLC): `<h2>` `recommendations.dlc.heading` + fila horizontal `GameCard` variante `shelf` de
   los DLC (`is_dlc=True` vía `RelatedContent`). Los DLC siguen **fuera** del catálogo
   gobernado normal (D-03) pero son consultables aquí. Si el usuario no posee el juego o no hay
   DLC → sección omitida.
9. **Contenido relacionado** (existente) — se mantiene.
10. **Estante de popularidad** (`RecommendationStrip`) — panel **secundario**; su fallo no deja
    la página en blanco (contrato "partial").
11. **Procedencia + atribución** (existente) — `source · source_id · licence · retrieved_at` +
    "Datos de IGDB.com" (ADR-006 §5) + enlace a `/{locale}/sources`. Estático, visible.

Cobertura de estados: partial (sin portada → placeholder; sin score → sin pill + texto "sin
valoración"; sin `summary` → sección omitida; sin géneros/plataformas → fila omitida; sin DLC
o juego no poseído → estante omitido), error (404 → `notFound()`; fallo de popularidad →
estante oculto), long-text (título sin clamp aquí; sinopsis con clamp de 6 líneas + expandir;
listas de géneros/plataformas envuelven), zero-one-many (N/M del desglose de rating vía
`formatCount` cuando aplique — o texto directo con números).

### 3. Catalogue (`app/[locale]/catalogue/page.tsx`) — CAT-02 multi-selección (P1)

Server component, dirigido por `searchParams`, **todos los controles envían por GET** — cada
vista filtrada es una URL compartible. Sin estado cliente.

**Cambio respecto a 01.1:** los campos **Género** y **Plataforma** pasan de `<select>` único a
**multi-selección** vía un `<details>` "menú de faceta". El resto de la barra de filtros
(búsqueda `q`, `year_from`/`year_to`, `min_rating`, `sort`, "Aplicar filtros", "Borrar todos
los filtros") no cambia.

**Menú de faceta (por cada campo multi — Género, Plataforma):**
- Un `<details class="sp-facet">` dentro del `<form method="get">`. `<summary>` = nombre del
  campo ("Géneros" / "Plataformas", `catalogue.filters.genrePlural` / `platformPlural`) +
  `catalogue.facet.selectedCount` ("Cualquiera" / "N seleccionados") + chevron. Objetivo 44px.
- Al abrir: un panel `--color-surface-raised` + `--shadow-overlay` + `radius-card`,
  `padding: lg`, que **flota sobre la rejilla** en `≥ md` (posición absoluta dentro de un
  contenedor `position: relative`) y fluye en el flujo en `< md`.
- Contenido del panel:
  - Una **línea de semántica** (Label, `--color-text-muted`): géneros →
    `catalogue.facet.genreSemantics` "Muestra juegos que tienen **todos** los géneros
    seleccionados." · plataformas → `catalogue.facet.platformSemantics` "Muestra juegos
    disponibles en **alguna** de las plataformas seleccionadas."
  - Lista desplazable (`max-height` ~320px, `overflow-y: auto`) de
    `<label><input type="checkbox" name="genre" value="{slug}"> {nombre}</label>` — un check por
    opción de faceta. `name` repetido → el navegador envía `?genre=a&genre=b`.
  - Un enlace `catalogue.facet.clear` ("Quitar" / "Clear") que deselecciona solo esa faceta
    (href = la URL actual sin ningún `genre`).
  - (Opcional, si la lista de plataformas es larga: un `<input>` de filtrado en-lista
    `catalogue.facet.searchInList`, puramente cosmético client-side; degrada a lista completa
    sin JS.)
- El panel **no auto-envía**: el usuario marca checks y pulsa "Aplicar filtros" (un solo submit
  del form, consistente con el resto de la barra).

**Parsing (`lib/catalogue-filters.ts`):** `parseFilters` deja de usar `first()` para `genre` y
`platform` y **lee el array completo** de `searchParams` (`sp.getAll("genre")`), normaliza,
de-duplica, descarta vacíos. `CatalogueFilters.genre` / `.platform` pasan de `string?` a
`string[]`. `buildQuery` emite un par repetido por valor. `countActiveFilters` cuenta **cada
valor seleccionado** (2 géneros + 1 plataforma = 3 filtros activos). Valor de faceta
desconocido → se ignora, no fuerza resultado vacío (patrón heredado).

**Fila de chips activos:** **un `FilterChip` por valor seleccionado** — "Género: RPG ✕",
"Género: Estrategia ✕", "Plataforma: Switch ✕". Cada chip es un enlace que quita **solo ese
valor** (mantiene los demás `genre`/`platform` y el resto de params).
`aria-label="Quitar filtro {label}"`. `--color-surface-overlay`, Label. "Borrar todos los
filtros" se muestra si hay ≥1 filtro activo.

**Resto de la pantalla** (línea de conteo completo con `Intl.NumberFormat`, línea de resultado
`role="status"`, rejilla `repeat(auto-fill, minmax(156px, 1fr))`, paginación que preserva todos
los params, `GameCard` con score pill relabelado) — sin cambio respecto a 01.1.

**Móvil (`< md`):** la barra de filtros sigue colapsando en su `<details>` disclosure exterior;
los menús de faceta interiores fluyen en el flujo (no flotan). Rejilla a `minmax(140px, 1fr)`,
suelo 2-up. Sin scroll horizontal de página a 320px / 400% zoom.

Cobertura de estados: empty (filtros sin resultados → `catalogue.filters.emptyHeading/Body` +
"Borrar todos los filtros"; búsqueda de texto vacía → `catalogue.emptyHeading/Body`), loading
(esqueleto de rejilla geometry-matched, un `role="status"` polite), error (fallo del catálogo →
`errors.retryCatalogue` + reintento; fallo de la lista de facetas → menús de faceta
`disabled` + `catalogue.filters.unavailable`, la búsqueda sigue), populated (conteo + label de
sort + chips siempre visibles), overflow (fila de chips envuelve, panel de faceta hace scroll
interno, sin scroll de página), zero-one-many (`catalogue.facet.selectedCount`,
`catalogue.filters.activeLabel`, conteos de resultado — todos localizados vía `formatCount`),
long-text (clamp de 2 líneas en título, `+N` de géneros, reflow a 400%).

### 4. Recommendations (`app/[locale]/recommendations/page.tsx`) — REC-03/06/07/08/09 + D-15 (P4)

**Auth-gated** igual que 01.1 (`/collection`): sin `sessionid` → `redirect` a
`/{locale}/login?next=…`; cookie presente pero 401 → mismo redirect. El link de nav solo
aparece autenticado.

La página pasa a **3 secciones etiquetadas que coexisten**, en este orden:

**(a) "Recomendado para ti"** — el ranking del **laboratorio de contenido** (NUEVO, REC-03):
- `<h2>` `recommendations.forYou.heading`.
- Cabecera de sección: `recommendations.forYou.intro` con la **variante visible una vez aquí**
  (`recommendations.forYou.variantLabel` "Variante: {algorithm_id}") — "bien marcado el tipo de
  recomendación" (D-16). Debajo, en Label `--color-text-muted`, la línea de versiones
  publicadas `recommendations.forYou.versionsLabel` (modelo · features · datos — REC-09).
- Línea `recommendations.forYou.excludedNote` (Label, muted) — se excluyen los juegos ya
  consumidos/en biblioteca (REC-07).
- **Una lista ordenada** (`<ol>`) de recomendaciones (no agrupada por género — el modelo de
  contenido produce un ranking cruzado). Cada ítem:
  - `GameCard` (variante `grid` o una fila compacta con portada 120px) + posición.
  - **Frase corta determinista** de explicación bajo el título
    (`recommendations.forYou.explanationSentence`, reutiliza `.sp-card-evidence`), derivada
    solo de features persistidas, **sin prosa generada** (D-16 / REC-08).
  - Debajo, un `<details>` **"Por qué"** (`recommendations.why.toggle`) que abre:
    - `<h3>`/label `recommendations.why.heading`.
    - **Tabla de contribución por género** (`KeyValueTable` / `.sp-contrib-table`): fila por
      género contribuyente — nombre a la izquierda, barra `--color-text-secondary` sobre
      `--color-surface-overlay` + valor `{pct}%` (`recommendations.why.contributionValue`) a la
      derecha. El % también como texto (no solo color/longitud).
    - **Fila de término de rating** (`recommendations.why.ratingTerm`) con su valor 0..1
      normalizado; si el candidato no tenía rating propio y se usó la mediana de género →
      `recommendations.why.ratingTermFallback` como nota (D-07 / D-13).
    - **Pie** `recommendations.why.variantFooter` "Variante: {algorithm_id}".
- **Arranque en frío (REC-06):** si el usuario no tiene historial suficiente para el modelo de
  contenido → la sección muestra `recommendations.forYou` empty heading/body + un badge
  `recommendations.forYou.coldStartBadge` ("Vista de arranque en frío") y renderiza una vista
  de fallback explícita basada en géneros populares — **nunca una lista vacía**.

**(b) Estantes por género** (`rank_genre_taste_v1`, **se mantienen** de 01.1, REC-10):
- Sin cambio funcional: un `RecommendationShelf` por género de gusto, cada uno con su
  explicador y su disclosure de algoritmo/limitación existentes.
- Separado de la sección (a) por `--space-2xl` y una cabecera `<h2>` propia
  (`recommendations.heading` "Recomendaciones según tus géneros"). Debe leerse claramente como
  **una técnica distinta** de (a).

**(c) "Para tus juegos"** (DLC, D-15, **NUEVO**):
- `<h2>` `recommendations.dlc.heading` + intro `recommendations.dlc.intro`.
- Agrupado por juego base poseído: subtítulo `recommendations.dlc.baseGameLabel` "DLC de
  {game}" + fila horizontal `GameCard` variante `shelf` de sus DLC.
- Si el usuario no posee ningún juego con DLC → **sección omitida** (sin estado vacío).

**Distinción visual obligatoria:** las 3 secciones **nunca comparten cabecera ni tratamiento**.
`RecommendationStrip` (popularidad, REC-02) sigue siendo una `<ol>` plana bajo "Populares en la
demo" y **no** aparece en esta página (vive en home y ficha).

Cobertura de estados: empty ((a) arranque en frío con fallback explícito; (b) `insufficient_history`
→ `recommendations.emptyHeading/Body` + CTA catálogo; (c) omitida), loading (esqueleto: cabecera
+ 5 filas con bloque de portada para (a); 2 cabeceras de estante + 4 bloques para (b); un
`role="status"` polite por región), error ((a)/(b) `recommendations.error` + reintento, el
chrome de la página sigue), partial (una sección falla → las otras renderizan; un estante con
solo su mínimo de ítems renderiza), populated (variante + versiones siempre visibles en (a)),
zero-one-many (contadores de contribución y de género localizados), overflow (tablas "Por qué"
y estantes hacen scroll dentro de su contenedor; sin scroll de página; `<details>` cerrado por
defecto para no alargar la página).

---

## First-Party Component Contracts

Sin design system instalado — componentes hechos a mano en `apps/web/components/`. Cada fila es
un contrato que el executor implementa/actualiza; **no es una lista cerrada**. Los estados
enumerados son de obligado cumplimiento para el checker (Dimensión 2) y para QUAL-05.

### Nuevos o modificados esta fase

| Component | File | Contract + estados |
|-----------|------|--------------------|
| `FacetMenu` (**NEW**) | `components/FacetMenu.tsx` | Server component. `<details class="sp-facet">` dentro del `<form method="get">` del catálogo. Props: `name` (`"genre"`\|`"platform"`), `label`, `options: FilterOption[]`, `selected: string[]`, `semanticsText`, `locale`. Renderiza `<summary>` (label + `catalogue.facet.selectedCount` + chevron inline SVG, 44px) y un panel con: línea de semántica (Label, muted), lista scrollable de `<label><input type="checkbox" name={name} value={slug}>`, enlace "Quitar". **No auto-envía.** Degrada a lista completa sin JS. **Estados:** `collapsed` (default; summary muestra el conteo), `expanded` (panel visible, `--shadow-overlay` en `≥md` flotando sobre la rejilla, en flujo en `<md`), `summary:focus-visible` (ring 2px `--color-focus-ring`), `option:checked` (check en `--color-text-primary`, fila con fondo `--color-surface-overlay`), `disabled` (facetas no disponibles → `disabled` en el `<details>` + todos los checkbox, `aria-disabled`), `empty` (0 opciones → summary deshabilitado + texto `catalogue.filters.unavailable`), `keyboard` (Enter/Espacio en summary alterna; Tab recorre los checkbox; Escape en `≥md` cierra y devuelve foco al summary). |
| `FilterBar` (**MOD**) | `components/FilterBar.tsx` | Sustituye los dos `<select>` de género/plataforma por dos `<FacetMenu>`. El resto (búsqueda, años, `min_rating`, `sort`, acciones) sin cambio. Sigue siendo server component, `<form method="get">`, disclosure `<details>` exterior en móvil, DOM idéntico a todo ancho. |
| `FilterChip` (**MOD**) | `components/FilterChip.tsx` | Sin cambio de API. El catálogo ahora emite **un chip por valor** de faceta seleccionada; `removeHref` quita solo ese valor. `aria-label="Quitar filtro {label}"`, glifo ✕ inline SVG, `--color-surface-overlay`, Label. **Estados:** `default`, `hover` (sin cambio de fondo — solo el ✕ pasa a `--color-text-primary`), `focus-visible` (ring). |
| `ScorePill` (**MOD**) | `components/ScorePill.tsx` | Sin cambio de props ni de rampa de color (`--color-score-weak/fair/strong`). **Cambio:** el texto visible junto al número usa `card.score.label` ("Valoración" / "Rating"), **no** "IGDB rating". `aria-label` = `card.score.aria` revisado ("Valoración {n} de 100"). `rating == null` → no renderiza nada (el llamador muestra `card.score.none` "Sin valoración"). Nunca usa `--color-accent`. **Estados:** `weak` (<40), `fair` (40–74), `strong` (≥75), `absent` (null → nada). |
| `RatingBreakdownLine` (**NEW**) | inline en la ficha (o `components/RatingBreakdownLine.tsx`) | `<p>` Label `--color-text-muted` bajo el `ScorePill` **solo en la ficha**. Props: `igdbCount`, `savepointCount`. Elige `detail.ratingBreakdown` / `…ExternalOnly` / `…LocalOnly` según qué conteo sea > 0. **Estados:** `both` (ambos conteos), `externalOnly`, `localOnly`, `none` (ambos 0 → no se renderiza esta línea; el llamador ya mostró "Sin valoración"). Sin tooltip. |
| `Synopsis` (**NEW**) | `components/Synopsis.tsx` | Client component ligero. Props: `text`, `labels` (`heading`, `showMore`, `showLess`). `<section>` + `<h2>` `detail.synopsis.heading` + prosa Body con `-webkit-line-clamp: 6`; si `scrollHeight > clientHeight`, un `<button class="sp-link">` alterna expandido/colapsado (`aria-expanded`). Sin JS: se renderiza el texto completo con el clamp CSS y el botón como `<details>`/`<summary>` de respaldo. **Estados:** `clamped` (default, texto largo), `expanded`, `short` (texto cabe en 6 líneas → sin botón), `absent` (`text` vacío → la sección entera no se renderiza). |
| `ContentRecommendationList` (**NEW**) | `components/ContentRecommendationList.tsx` | `<section>` + `<h2>` `recommendations.forYou.heading` + cabecera con `variantLabel` y `versionsLabel` + `<ol>` de ítems. Cada ítem = `GameCard` + frase `explanationSentence` + `<WhyDisclosure>`. **Estados:** `populated` (≥1 ítem), `coldStart` (badge `coldStartBadge` + empty copy + fallback de géneros populares — nunca `<ol>` vacío), `loading` (esqueleto cabecera + 5 filas), `error` (`recommendations.forYou.error` + reintento, chrome intacto). |
| `WhyDisclosure` (**NEW**) | `components/WhyDisclosure.tsx` | `<details>` cerrado por defecto. `<summary>` = `recommendations.why.toggle` ("Por qué"), 44px. Panel: `<h3>` `why.heading` + `ContributionTable` + fila de término de rating (con `why.ratingTermFallback` si aplica) + pie `why.variantFooter`. **Estados:** `collapsed` (default), `expanded`, `summary:focus-visible`, `keyboard` (Enter/Espacio alterna). |
| `ContributionTable` (**NEW**) | `components/ContributionTable.tsx` | Tabla `key → value` (patrón `KeyValueTable`, ver abajo). Fila por género: nombre (Label) + barra (`div` pista `--color-surface-overlay`, relleno `--color-text-secondary`, `width: {pct}%`) + `{pct}%` como texto (`why.contributionValue`). Última fila = término de rating. **No usa accent.** **Estados:** `populated`, `singleGenre` (una fila), `ratingFallback` (nota `ratingTermFallback` visible). Accesible: `<table>` semántica con `<th scope="row">`; la barra es decorativa (`aria-hidden`), el % es el dato accesible. |
| `OwnedGamesDlcShelf` (**NEW**) | `components/OwnedGamesDlcShelf.tsx` | `<section>` + `<h2>` `recommendations.dlc.heading` (o subtítulo `dlc.baseGameLabel` por juego base en la página de recomendaciones) + fila horizontal `GameCard` variante `shelf`. Reutiliza `.sp-shelf` / `.sp-shelf-track`. **Estados:** `populated`, `empty` (el usuario no posee juegos con DLC → sección **no** renderizada), `loading` (esqueleto 1 cabecera + 4 bloques), `error` (omitida). Usado en ficha (Screen Contract 2 §8) y en recomendaciones (§c). |
| `NewReleasesShelf` (**NEW**) | `components/NewReleasesShelf.tsx` | `<section>` + `<h2>` `home.newReleases.heading` + explicador `home.newReleases.explainer` + fila horizontal `GameCard` variante `shelf` (máx 20, `first_release_date` desc, ventana 6 meses). Mismo tratamiento que `RecommendationStrip`/`.sp-shelf`. **Estados:** `populated`, `empty` (0 en ventana → sección **no** renderizada), `loading` (esqueleto 1 cabecera + 6 bloques, `aria-hidden`, un `role="status"`), `error` (omitida, la home no se rompe). |
| `AppShell` (**MOD**) | `components/AppShell.tsx` | En `< md`, pasa `compact`/oculta el `<span>` de texto de `ThemeToggle` y `AccountSwitcher` (clase `hidden md:inline`), manteniendo `aria-label`/`aria-pressed`. DOM idéntico a todo ancho. Monta `NewReleasesShelf` **no** aquí (vive en la home). Resto sin cambio. |
| `ThemeToggle` (**MOD**) | `components/ThemeToggle.tsx` | El `<span>{labels.label}: {stateWord}</span>` se envuelve en `class="hidden md:inline"`. El `<button>` mantiene `aria-label` (`switchToDark`/`switchToLight`) y `aria-pressed`. En `< md` = solo el glifo sol/luna, 44px. **Estados:** `dark` (luna), `light` (sol), `< md` (solo icono), `≥ md` (icono + label), `focus-visible` (ring). |
| `AccountSwitcher` (**MOD**) | `components/AccountSwitcher.tsx` | El texto "Cuenta simulada: {alias}" del trigger se envuelve en `hidden md:inline`; en `< md` = avatar/inicial + chevron. `aria-label` conserva "Cuenta simulada: {alias}" (la palabra "simulada"/"simulated" sigue en el nombre accesible siempre). Panel `role="menu"` sin cambio (focus-trap, Escape, focus-return). **Estados:** `< md` (icono + chevron), `≥ md` (+ texto), `open`/`closed`, `focus-visible`. |

### Contratos de pulido general (formalización de utilidades ya en `globals.css`)

Codifican patrones existentes para que el checker y el executor tengan una fuente única. Todos
respetan `prefers-reduced-motion` (regla global ya presente).

| Patrón | Clase(s) / token | Contrato + estados |
|--------|------------------|--------------------|
| **Panel / superficie** | `.sp-surface` | `--color-surface-raised` + borde 1px `--color-surface-border` + `radius-card` + `padding: lg`. Superficie flotante (popover de faceta) añade `--shadow-overlay`. **Estados:** `resting` (borde, sin sombra), `floating` (+ `--shadow-overlay`, solo cuando se solapa con contenido). Sin sombra en superficies en-flujo. |
| **Familia de botones** | `.sp-btn-primary` / `.sp-btn-secondary` / `.sp-btn-danger` | Primary = relleno `--color-accent`, texto `--color-accent-on`, 600, uno por pantalla. Secondary = `--color-surface-overlay`, borde, texto `--color-text-secondary`, Label. Danger = transparente, borde + texto `--color-danger`. Todos `min-height: 2.75rem`. **Estados (cada uno):** `default`, `hover` (primary → `--color-accent-strong`; secondary → sin cambio de fondo; danger → sin cambio), `focus-visible` (ring 2px `--color-focus-ring`, `outline-offset: 2px`), `disabled` (`opacity` reducida + `cursor: not-allowed` + `aria-disabled`; nunca solo color), `loading` (texto sustituido por label de progreso + `disabled`, p. ej. `register.pending`). |
| **Patrón de disclosure único** | `<details>/<summary>` nativo + (variante con focus-trap) `role="menu"` | **Un solo patrón** reutilizado en: menús de faceta multi-selección, `<details>` exterior de la barra de filtros en móvil, "Por qué" del recomendador, "Mostrar más" de la sinopsis, disclosure de algoritmo/limitación de 01.1. `<summary>` sin marcador nativo (`::-webkit-details-marker { display: none }`), chevron inline SVG que rota, 44px, `list-style: none`. La **variante con focus-trap** (`AccountSwitcher`, `MobileMenu`) usa `role="menu"` + Escape-cierra + focus-return — reservada a menús que se solapan con navegación, no a filtros. **Estados:** `collapsed`, `expanded`, `summary:focus-visible`, `disabled`, `keyboard` (Enter/Espacio alterna; Escape cierra la variante popover/menu). |
| **Chips y pills** | `.sp-chip` / `.sp-status-pill` / `.sp-score-pill` / `.sp-copies-chip` | Radio 999px, Label 600, `--color-surface-overlay` de fondo. `sp-chip` (filtro activo / género) lleva ✕ o es enlace. `sp-status-pill` usa `--color-status-{status}` en `currentColor` (borde + texto). `sp-score-pill` usa `--color-score-{tier}`. **Estados:** `default`, `interactive:hover` (solo el glifo ✕ cambia a `--color-text-primary`), `focus-visible` (ring), `on-cover` (posición absoluta, para status/score sobre portada — nunca solapan el título), `static/inline` (`--score-pill--inline` en la ficha). Ninguno usa `--color-accent`. |
| **Tablas clave-valor** | `.sp-kv` / `.sp-summary-dl` / **`.sp-contrib-table` (NEW)** | `<table>` o `<dl>` semántica. Clave = Label `--color-text-secondary`; valor = Body/Label `--color-text-primary` 600. `.sp-contrib-table` añade una celda de barra decorativa (`aria-hidden`) entre clave y valor. **Estados:** `populated`, `singleRow`, `withFallbackNote` (fila de nota en `--color-text-muted`). Sin zebra striping; separación por `--space-md` y borde 1px `--color-surface-border` opcional entre filas. |
| **Elevación / hover / foco** | `--shadow-overlay` (NEW) · `--color-surface-overlay` (hover) · `--color-focus-ring` (foco) | Elevación: **solo** superficies que se solapan (popover de faceta, menús). Hover: fondo → `--color-surface-overlay`; nunca cambia de tinte de color. Foco: **siempre** `outline: 2px solid var(--color-focus-ring); outline-offset: 2px` (regla `:focus-visible` global, nunca `outline: none` sin equivalente). **Estados por control interactivo:** `rest`, `hover`, `focus-visible`, `active`, `disabled`. |
| **Esqueleto de carga** | **`.sp-skeleton` (NEW)** | Bloque geometry-matched que reserva el layout exacto del contenido que sustituye (p. ej. 156×208 para portada de rejilla, 120×160 para portada de estante). Fondo `--color-skeleton-base`; animación de barrido opcional hacia `--color-skeleton-sheen`. `aria-hidden="true"`. Bajo `prefers-reduced-motion` → **estático** (sin barrido). Exactamente **un** `role="status"` polite ("Cargando…" / "Loading…") por región asíncrona, no uno por bloque. **Estados:** `pulsing` (default), `static` (reduced-motion), acompañado siempre de la región polite. |
| **Estado vacío** | `.sp-empty` | `--color-surface-raised` + borde + `radius-card` + `padding: 2xl lg`, centrado. Contiene: `<h2>`/`<p class="sp-h2">` de encabezado + `<p class="sp-lead">` de cuerpo (con siguiente paso) + opcional CTA (`.sp-btn-primary` o `.sp-link`). La copy vive en `## Copywriting Contract`. **Estados:** `withCta` (catálogo filtrado, recomendaciones sin historial), `informational` (sin CTA), `hidden` (estantes "Novedades" / "Para tus juegos" con 0 ítems → no se renderiza `.sp-empty`, la sección entera se omite). |

---

## UI Considerations

> Análogo visual de la sección de cobertura del edge-probe. Lo lee gsd-planner para construir
> `must_haves.truths`. Las 56 consideraciones de estado aplicables enumeradas por el
> ui-consideration-probe (55 filas distintas — se consolidó un duplicado de categoría) sobre
> 9 superficies. La **copy** de vacío/error vive en `## Copywriting Contract`; esta sección
> cubre la **forma** del estado y **referencia** esas claves en vez de repetirlas.
>
> Las matrices transversales de estado heredadas de 01.1 (`empty` / `loading` / `error` /
> `populated` / `partial` / `overflow` / `zero-one-many` / `long-text`) están todas marcadas
> "explicit" en `ROADMAP.md`; las filas abajo referencian la sección concreta de este
> 02-UI-SPEC o esa matriz heredada.

Consideraciones de estado aplicables resueltas: **45 resolved (explicit), 10 resolved
(backstop), 0 unresolved — 55 filas sobre 9 superficies**.

<!-- Vocabulario de status (probe-core projectTruths):
     ✅ covered   → cadena de verdad plana, se eleva a must_haves.truths
     🧪 backstop  → escalar plano { statement, verification: backstop }; en verify sin evidencia
                    explícita → insufficient_spec → human_needed (nunca un pase silencioso)
     ⚠ unresolved → asunción explícita del planner (se expone, nunca se descarta en silencio)
     Filas REEMPLAZADAS (no añadidas) en cada re-run del probe — idempotente. -->

### E1 — `FacetMenu` (form + list-collection + interactive-control)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E1 FacetMenu — 0 opciones de faceta | ✅ covered | El `<details>` se renderiza `disabled` + `aria-disabled` y se muestra `catalogue.filters.unavailable`; el input `q` sigue enviando (Screen Contract 3 › cobertura error; First-Party Component Contracts › `FacetMenu` estado `empty`). |
| loading | E1 FacetMenu | ✅ covered | El catálogo es server-render; las opciones de faceta llegan con el payload de la página, así que `FacetMenu` no tiene estado async propio — la rejilla que lo rodea usa `.sp-skeleton` geometry-matched + un único `role="status"` polite (Screen Contract 3 › loading; matriz `loading` heredada de 01.1). |
| error | E1 FacetMenu | ✅ covered | El fallo del fetch de opciones degrada **cada** `FacetMenu` a `disabled` y renderiza `catalogue.filters.unavailable`; la búsqueda `q` sigue viva (Screen Contract 3 › error; `FacetMenu` estado `disabled`). |
| populated | E1 FacetMenu | ✅ covered | El menú abierto muestra la línea de semántica AND/OR (`catalogue.facet.genreSemantics` / `platformSemantics`), la lista scrollable de checkboxes y el enlace `catalogue.facet.clear`; el `<summary>` siempre muestra `catalogue.facet.selectedCount` (First-Party Component Contracts › `FacetMenu`; Screen Contract 3). |
| partial | E1 FacetMenu — slug seleccionado desconocido en la URL | ✅ covered | Un slug desconocido se ignora: no se pinta como checkbox fantasma ni fuerza resultado vacío (Screen Contract 3 "valor de faceta desconocido → se ignora"; matriz `partial` heredada de 01.1). |
| overflow | E1 FacetMenu — lista de ~220 plataformas | 🧪 backstop | La lista de checkboxes de plataforma dentro de `max-height: ~320px; overflow-y: auto` se renderiza y desplaza de forma aceptable a 320px de ancho y 400% de zoom **sin virtualización** — a confirmar con el pase visual/Playwright de la fase. |
| zero-one-many | E1 FacetMenu — recuento de selección | ✅ covered | `catalogue.facet.selectedCount` usa el mecanismo `formatCount` zero/one/many (`Cualquiera` / `1 seleccionado` / `{n} seleccionados`); `countActiveFilters` cuenta **cada** valor seleccionado (Copywriting Contract; `lib/catalogue-filters.ts`). |
| long-text | E1 FacetMenu — etiquetas de opción largas | 🧪 backstop | Las etiquetas largas de género/plataforma envuelven dentro del panel sin recortar el checkbox ni el panel a 30% de expansión de texto / 400% de zoom — verificado por el pase de viewport+zoom, no por un assert unitario. |

### E2 — Fila de chips de filtro activo (list-collection)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E2 chip row | ✅ covered | Sin filtros activos la fila no se renderiza y "Borrar todos los filtros" se oculta (Screen Contract 3 "se muestra si hay ≥1 filtro activo"). |
| loading | E2 chip row | ✅ covered | La fila se deriva síncronamente de `searchParams` durante el SSR — sin estado async (Screen Contract 3; matriz `loading` heredada de 01.1). |
| error | E2 chip row | ✅ covered | Si el mapa de etiquetas de faceta no está disponible, el chip cae al slug crudo (`{genreLabels|platformLabels}.get(value) ?? value`); la fila sigue renderizando y cada chip sigue quitando su valor (Screen Contract 3). |
| populated | E2 chip row | ✅ covered | Un `FilterChip` por valor activo ("Género: RPG ✕", "Género: Estrategia ✕", "Plataforma: Switch ✕"); cada uno es un enlace que quita **solo ese valor** y conserva el resto de params (Screen Contract 3; First-Party Component Contracts › `FilterChip` `MOD`). |
| partial | E2 chip row | ✅ covered | Un chip de un valor que la lista de facetas ya no ofrece sigue renderizando con su slug y sigue siendo individualmente removible (Screen Contract 3 › fallback de etiqueta de chip). |
| overflow | E2 chip row | ✅ covered | La fila envuelve (`flex-wrap`, `.sp-chip-row`); con multi-select contiene más chips y sigue envolviendo en vez de causar scroll horizontal de página (Screen Contract 3; matriz `overflow` heredada de 01.1). |
| zero-one-many | E2 chip row | ✅ covered | Zero → fila oculta; one → un chip; many → chips envueltos, uno por valor; sin cadena de recuento en la propia fila (Screen Contract 3). |
| long-text | E2 chip row — etiqueta de filtro larga | 🧪 backstop | Un chip con una etiqueta de filtro localizada larga envuelve/trunca dentro de la fila sin desbordar el viewport a 30% de expansión / 400% de zoom — a confirmar con el pase visual. |

### E3 — `NewReleasesShelf` (list-collection + media)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E3 NewReleasesShelf — 0 lanzamientos en la ventana de 6 meses | 🧪 backstop | Toda la sección (cabecera + fila) está **ausente del DOM** — no un contenedor vacío renderizado; la ausencia efectiva se confirma con un test held-out/visual (Screen Contract 1; First-Party Component Contracts › `NewReleasesShelf` estado `empty`; P5). |
| loading | E3 NewReleasesShelf | ✅ covered | Esqueleto = 1 cabecera + 6 bloques `.sp-skeleton` de portada (120×160), `aria-hidden`, un `role="status"` polite "Cargando…" (`NewReleasesShelf` estado `loading`; matriz `loading` heredada de 01.1). |
| error | E3 NewReleasesShelf | ✅ covered | El fallo del fetch omite la sección; el resto de la home renderiza sin cambios (`NewReleasesShelf` estado `error`; matriz `partial` heredada de 01.1). |
| populated | E3 NewReleasesShelf | ✅ covered | Hasta 20 `GameCard` variante `shelf` ordenados `first_release_date` desc con desempate `canonical_slug`, colocados **encima** del `RecommendationStrip` de popularidad, visibles logueado y deslogueado (Screen Contract 1; P5). |
| partial | E3 NewReleasesShelf | ✅ covered | Un ítem con portada muerta/ausente usa el placeholder de primera parte vía `CoverImage` onError; un estante fallido nunca deja la home en blanco (matriz `partial` heredada de 01.1). |
| overflow | E3 NewReleasesShelf | ✅ covered | La fila hace scroll horizontal dentro de su propio `.sp-shelf-track` y nunca causa scroll horizontal de página a 320px / 400% de zoom (§ UI Considerations `overflow`). |
| zero-one-many | E3 NewReleasesShelf | ✅ covered | Zero → sección oculta; one → una tarjeta; many → fila scrollable acotada a 20; sin cadena de recuento visible (Screen Contract 1). |
| long-text | E3 NewReleasesShelf — títulos largos | 🧪 backstop | Los títulos largos en el estante hacen clamp a 2 líneas (`GameCard`) sin romper la altura de la fila a 30% de expansión / 400% de zoom — a confirmar con el pase visual. |

### E4 — `RatingBreakdownLine` (static-content)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| overflow | E4 RatingBreakdownLine | ✅ covered | Es un único `<p>` (Label, `--color-text-muted`) que envuelve bajo el `ScorePill`; nunca ensancha la columna derecha (Screen Contract 2 §2; First-Party Component Contracts › `RatingBreakdownLine`). |
| long-text | E4 RatingBreakdownLine — N/M grandes + frase ES larga | 🧪 backstop | `detail.ratingBreakdown` con valores N/M grandes y la redacción ES más larga envuelve a 2+ líneas sin recorte a 30% de expansión de texto / 400% de zoom — a confirmar con el pase visual. |

### E5 — `Synopsis` (static-content)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| loading | E5 Synopsis | ✅ covered | El `summary` viene en el payload server de la ficha — sin estado async propio; la ruta de detalle está cubierta por la matriz `loading` heredada de 01.1 (Screen Contract 2). |
| error | E5 Synopsis | ✅ covered | Si IGDB no aporta `summary`, toda la `<section>` de sinopsis (cabecera incluida) se omite — nunca una cabecera vacía (First-Party Component Contracts › `Synopsis` estado `absent`; Screen Contract 2 §3). |
| overflow | E5 Synopsis | ✅ covered | La prosa hace clamp a ~6 líneas (`-webkit-line-clamp: 6`); la expansión es un toggle `aria-expanded` en el sitio (`common.showMore` / `common.showLess`) — nunca ensancha el layout de dos columnas (First-Party Component Contracts › `Synopsis`). |
| long-text | E5 Synopsis — `summary` muy largo | 🧪 backstop | Un `summary` de IGDB muy largo hace clamp a 6 líneas, se expande entero con "Mostrar más" y vuelve a colapsar con "Mostrar menos" sin layout shift a 400% de zoom — a confirmar con el pase visual. |

### E6 — `ContentRecommendationList` (list-collection)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E6 ContentRecommendationList — sin historial / deslogueado | 🧪 backstop | Un usuario sin historial suficiente **nunca** ve una `<ol>` vacía: la sección muestra la copy vacía de `recommendations.forYou` + `coldStartBadge` y renderiza un fallback explícito de arranque en frío por géneros populares (REC-06); la **forma exacta** del ítem de fallback / la ruta deslogueada se confirman con un test held-out (First-Party Component Contracts › `ContentRecommendationList` estado `coldStart`). |
| loading | E6 ContentRecommendationList | ✅ covered | Esqueleto = 1 cabecera de sección + 5 filas cada una con un bloque `.sp-skeleton` de portada; un `role="status"` polite por región (`ContentRecommendationList` estado `loading`; matriz `loading` heredada de 01.1). |
| error | E6 ContentRecommendationList | ✅ covered | `recommendations.forYou.error` + control de reintento; el chrome de la página y las otras dos secciones siguen renderizando (`ContentRecommendationList` estado `error`; Screen Contract 4 › cobertura error). |
| populated | E6 ContentRecommendationList | ✅ covered | `<ol>` ordenada; cada ítem = `GameCard` + `explanationSentence` determinista + `WhyDisclosure`; la cabecera muestra `variantLabel` + `versionsLabel` una vez (Screen Contract 4 §a; D-16 / REC-08 / REC-09). |
| partial | E6 ContentRecommendationList | ✅ covered | Los títulos ya consumidos/poseídos se excluyen (REC-07, `recommendations.forYou.excludedNote`); si esta sección falla, los estantes por género y la sección DLC siguen renderizando (Screen Contract 4 › cobertura partial). |
| overflow | E6 ContentRecommendationList | ✅ covered | La lista es vertical; cada `WhyDisclosure` está colapsado por defecto, así que la longitud de página queda acotada; los paneles `<details>` y sus tablas internas hacen scroll dentro de su contenedor (Screen Contract 4 › cobertura overflow). |
| zero-one-many | E6 ContentRecommendationList | ✅ covered | Zero → fallback de arranque en frío (nunca vacío); one → un ítem ordenado; many → lista ordenada completa; posición ordinal renderizada por ítem (Screen Contract 4 §a). |

### E7 — `WhyDisclosure` + `ContributionTable` (interactive-control + static-content + list-collection)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E7 WhyDisclosure — sin contribuciones de género | ✅ covered | Aún sin solape de género, el `WhyDisclosure` renderiza la fila de término de rating y el `variantFooter`; la tabla de género muestra su única fila aplicable (First-Party Component Contracts › `ContributionTable` estado `singleGenre`). |
| loading | E7 WhyDisclosure | ✅ covered | El `WhyDisclosure` está colapsado por defecto y su contenido ya viene en el payload de la recomendación — sin estado async al expandir (First-Party Component Contracts › `WhyDisclosure`). |
| error | E7 WhyDisclosure | ✅ covered | Si faltan datos de contribución, la disclosure abre igualmente mostrando el `variantFooter` y los términos presentes; nunca bloquea el ítem de lista padre (`ContributionTable` comportamiento `partial`). |
| populated | E7 WhyDisclosure + ContributionTable | ✅ covered | El panel expandido = `why.heading` + tabla de contribución por género (nombre + barra `aria-hidden` + `{pct}%` como texto) + fila de término de rating + `why.variantFooter` "Variante: {algorithm_id}" (Screen Contract 4 §a; D-16). |
| partial | E7 ContributionTable — sin rating propio del candidato | ✅ covered | Cuando el candidato no tenía rating propio y se usó la mediana de género, `why.ratingTermFallback` aparece como fila-nota (`ContributionTable` estado `withFallbackNote`; D-07 / D-13). |
| overflow | E7 ContributionTable — muchos géneros | ✅ covered | La tabla hace scroll dentro del panel `<details>`; el panel está cerrado por defecto, así que nunca extiende la página de forma inesperada (Screen Contract 4 › cobertura overflow). |
| zero-one-many | E7 ContributionTable | ✅ covered | Zero géneros contribuyentes → solo fila de término de rating; one → una fila; many → una fila por género, cada una con un `why.contributionValue` `{pct}%` localizado (Copywriting Contract; First-Party Component Contracts › `ContributionTable`). |

### E8 — `OwnedGamesDlcShelf` (list-collection)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| empty | E8 OwnedGamesDlcShelf — el usuario no posee juegos con DLC | 🧪 backstop | Toda la sección `OwnedGamesDlcShelf` está **ausente del DOM** (no un contenedor vacío renderizado) — la ausencia efectiva, en ficha y en la página de recomendaciones, se confirma con un test held-out/visual (Screen Contract 2 §8 / Screen Contract 4 §c; First-Party Component Contracts › `OwnedGamesDlcShelf` estado `empty`; D-15). |
| loading | E8 OwnedGamesDlcShelf | ✅ covered | Esqueleto = 1 cabecera + 4 bloques `.sp-skeleton` de portada; un `role="status"` polite (`OwnedGamesDlcShelf` estado `loading`; matriz `loading` heredada de 01.1). |
| error | E8 OwnedGamesDlcShelf | ✅ covered | El fallo del fetch omite la sección tanto en la ficha como en la página de recomendaciones; ninguna de las dos se queda en blanco (`OwnedGamesDlcShelf` estado `error`; matriz `partial` heredada de 01.1). |
| populated | E8 OwnedGamesDlcShelf | ✅ covered | Agrupado por juego base poseído (`recommendations.dlc.baseGameLabel` "DLC de {game}") con una fila horizontal `GameCard` variante `shelf` por grupo; los DLC quedan fuera del catálogo gobernado pero consultables aquí (D-15; Screen Contract 4 §c). |
| partial | E8 OwnedGamesDlcShelf | ✅ covered | Las entradas de DLC con portada ausente usan el placeholder de primera parte; un juego base con 0 DLC resolubles no se muestra como grupo vacío (matriz `partial` heredada de 01.1). |
| overflow | E8 OwnedGamesDlcShelf | ✅ covered | La fila de cada grupo hace scroll dentro de su propio `.sp-shelf-track`; sin scroll horizontal de página a 320px / 400% de zoom (§ UI Considerations `overflow`). |
| zero-one-many | E8 OwnedGamesDlcShelf | ✅ covered | Zero poseídos-con-DLC → sección oculta; one → un grupo; many → un grupo etiquetado por juego base poseído (Screen Contract 4 §c). |

### E9 — Navbar autenticada solo-icono `< md` (nav + interactive-control)

| Category | Element | Status | Resolution / Reason |
|----------|---------|--------|---------------------|
| loading | E9 navbar solo-icono | ✅ covered | La navbar es chrome server-render sin estado async; el estado de auth se lee de la cookie `sessionid` durante el SSR (Navbar Screen Contract; heredado de 01.1). |
| error | E9 navbar solo-icono | ✅ covered | Si `fetchAccountMe` falla, el `AccountSwitcher` cae a la etiqueta genérica "Cuenta simulada" pero el trigger solo-icono y el menú siguen funcionando (heredado de 01.1 + fix D-01.1-13-b). |
| overflow | E9 navbar solo-icono | ✅ covered | En `< md`, `ThemeToggle` y `AccountSwitcher` renderizan solo-icono (texto visible `hidden md:inline`), así que la fila del header autenticada cabe a 320px sin scroll horizontal de página — el fix D-01.1-10-a (Navbar Screen Contract; First-Party Component Contracts › `AppShell` / `ThemeToggle` / `AccountSwitcher` `MOD`; P6). |
| long-text | E9 navbar solo-icono — alias de cuenta largo | 🧪 backstop | A 320px y 400% de zoom con un alias de cuenta simulada largo, la navbar autenticada solo-icono sigue cabiendo sin scroll horizontal y ambos controles conservan su `aria-label` / `aria-pressed` completos — a confirmar con el pase visual/Playwright de la fase. |

**Backstop (10) — se elevan como `{ statement, verification: backstop }`:** E1 overflow, E1 long-text,
E2 long-text, E3 empty, E3 long-text, E4 long-text, E5 long-text, E6 empty, E8 empty, E9 long-text.
Sin evidencia explícita en verify → `insufficient_spec` → `human_needed` (nunca un pase silencioso).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| n/a — sin shadcn, sin registro de componentes | none | not applicable |

No hay ningún registro de UI de terceros en uso ni propuesto. Si más adelante se adopta
`lucide-react` (iconos) pasa por el gate de aprobación de dependencias del proyecto (pin exacto
+ evidencia oficial + firma humana), no por un flujo de registro shadcn.

---

## Accessibility Contract (heredado de 01.1 — QUAL-03 / QUAL-05)

No negociable, re-verificado por el pase axe / viewport / zoom del plan de evidencia de esta
fase:

- axe-core: cero violaciones en cada página nueva/rediseñada (home, catálogo, ficha,
  recomendaciones), **una vez por tema** (dark + light).
- Cada pareja de color nueva (barra de contribución, pill relabelado, línea de desglose, panel
  de faceta con `--shadow-overlay`, check seleccionado, esqueleto) supera WCAG 2.2 AA en ambos
  temas (4.5:1 texto body, 3:1 texto grande / componentes UI).
- Ring de foco `2px --color-focus-ring` visible en cada control interactivo (summary de faceta,
  checkbox, chip, "Por qué", "Mostrar más", toggles solo-icono); nunca `outline: none` sin
  equivalente.
- Objetivo interactivo mínimo 44×44px (suelo `min-height: 2.75rem` existente) — incluye los
  toggles solo-icono en `< md` y los `<summary>` de faceta.
- 400% zoom / 320px de ancho: sin scroll horizontal de página; barra de filtros → disclosure;
  rejilla → suelo 2-up; panel de faceta con scroll interno; nav autenticada cabe (fix
  D-01.1-10-a).
- 30% de expansión de texto: sin recorte de títulos, chips, botones, el banner de demo, el
  `<summary>` de faceta ni la etiqueta de variante.
- Los toggles solo-icono en `< md` conservan un **nombre accesible** completo vía `aria-label`
  (`ThemeToggle`: `switchToDark`/`switchToLight`; `AccountSwitcher`: "Cuenta simulada: {alias}",
  la palabra "simulada"/"simulated" nunca desaparece del árbol de accesibilidad).
- Menús de faceta: la variante nativa `<details>` no atrapa foco (los filtros no se solapan con
  navegación); la variante `role="menu"` (`AccountSwitcher`, `MobileMenu`) sí, con Escape-cierra
  y focus-return.
- Tabla de contribución: `<table>` semántica con `<th scope="row">`; la barra es `aria-hidden`,
  el `%` es el dato accesible — tier/peso nunca se transmite solo por color o longitud.
- `ScorePill`: no color-only — muestra el número; "Sin valoración" es texto, no ausencia
  silenciosa.
- Una sola región `role="status"` polite por superficie asíncrona; esqueletos `aria-hidden`.
- Paridad EN/ES enforced por `apps/web/tests/i18n.test.ts` para cada clave nueva.

---

## Per-Surface Coverage Matrix (QUAL-05 — fuente de verdad ejecutable)

Cada superficie con su cobertura desktop + móvil + accesibilidad. El contrato completo de cada
una vive en `## Screen Contracts`; esta matriz es el roll-up compacto que el executor y la
verificación de QUAL-05 leen.

| Surface | Desktop + Mobile + Accessibility coverage | Verdict |
|---|---|---|
| **Catalogue** (`/[locale]/catalogue`) | **Desktop:** `FilterBar` con dos `FacetMenu` multi-selección (popover flotante con `--shadow-overlay` sobre la rejilla ~156px); línea de semántica AND/OR visible; un `FilterChip` por valor seleccionado; conteo completo localizado; paginación que preserva params repetidos. **Mobile:** `FilterBar` colapsa en `<details>`; menús de faceta fluyen en flujo; rejilla 2-up; chips envuelven; sin scroll horizontal a 320px. **Accessibility:** axe limpio por tema; cada checkbox y `<summary>` operables por teclado con ring visible y 44px; `parseFilters` lee `getAll`; valor desconocido se ignora; reflow 400% / 320px sin scroll de página. | pending checker |
| **Detail** (`/[locale]/games/[id]`) | **Desktop:** orden P3 — título/año → `ScorePill` relabelado "Valoración" + `RatingBreakdownLine` en texto plano → sinopsis IGDB (clamp 6 líneas + "Mostrar más") → géneros → plataformas → fecha → `LibraryControls` → estante "Para tus juegos" (si posee el base) → relacionados → popularidad (secundario) → procedencia + atribución IGDB. **Mobile:** una columna; portada escala a 200px; controles a ancho completo. **Accessibility:** axe limpio por tema; sin `summary` / sin score / sin DLC → pieza omitida, nunca cabecera vacía; `Synopsis` con `aria-expanded`; `CoverImage` `onError` → placeholder sin CLS; sin tooltip para el desglose de rating. | pending checker |
| **Recommendations** (`/[locale]/recommendations`) | **Desktop:** auth-gated; 3 secciones etiquetadas que coexisten — (a) "Recomendado para ti" `<ol>` del laboratorio de contenido con frase determinista + `<details>` "Por qué" (tabla de contribución por género + término de rating + pie "Variante: {id}") + `variantLabel` y `versionsLabel` en cabecera; (b) estantes por género `rank_genre_taste_v1` (se mantienen de 01.1); (c) "Para tus juegos" (DLC de juegos poseídos). Arranque en frío explícito, nunca `<ol>` vacía (REC-06); excluye juegos consumidos (REC-07). **Mobile:** secciones apiladas; estantes y tablas "Por qué" hacen scroll dentro de su contenedor; `<details>` cerrado por defecto. **Accessibility:** axe limpio por tema; tabla de contribución semántica con barra `aria-hidden` y `%` textual; "Por qué" operable por teclado; secciones son regiones etiquetadas y estructuralmente distintas del `RecommendationStrip` de popularidad. | pending checker |
| **Home** (`/[locale]`) | **Desktop:** estante "Novedades" nuevo (máx 20, `first_release_date` desc, ventana 6 meses) **encima** del estante de popularidad, visible logueado y deslogueado; se oculta entero si 0 ítems. **Mobile:** estante horizontal con scroll propio; sin scroll de página. **Accessibility:** axe limpio por tema; esqueleto `aria-hidden` + un `role="status"`; fallo del estante no rompe la home. **Navbar (todas las páginas):** `ThemeToggle` + `AccountSwitcher` solo-icono en `< md` (fix D-01.1-10-a) con `aria-label` completo; etiqueta vuelve en `≥ md`; DOM idéntico a todo ancho; la fila del header cabe a 320px. | pending checker |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS
- [x] Dimension 7 Inventory Provenance: PASS (n/a — `Tool: none`)

**Approval:** approved — checker-verified 7/7 (2026-09-06); `## UI Considerations` added (55 filas: 45 explicit, 10 backstop, 0 unresolved).
