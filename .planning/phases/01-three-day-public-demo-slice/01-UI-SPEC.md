---
phase: "1"
slug: "three-day-public-demo-slice"
status: draft
shadcn_initialized: false
preset: none
created: "2026-09-04"
---

# Phase 1 — UI Design Contract

> Visual and interaction contract for the three-day public demonstration. It is intentionally narrow, bilingual, accessible, and token-driven. The palette and typeface are provisional implementation choices, not final SavePoint branding.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — greenfield repository; use local semantic components and CSS/Tailwind tokens |
| Preset | not applicable |
| Component library | none; prefer native HTML controls and accessible local compositions |
| Icon library | Lucide React, pinned when the frontend lockfile is created; icons never replace visible labels for primary actions |
| Font | Inter Variable when locally bundled; fallback `Inter, ui-sans-serif, system-ui, sans-serif`; no runtime font CDN dependency |
| Direction | LTR for Spanish and English |
| Theme | dark only in Phase 1; values below are replaceable semantic tokens |

No component inventory is declared because no design-system package is installed. This is confirmed by the 2026-09-04 repository scan: no application `package.json`, `components.json`, Tailwind configuration, UI source, or stylesheet exists. Do not initialize or add a third-party component registry merely to satisfy this contract.

### Semantic Token Contract

Components consume semantic variables, never raw palette values. Every visual value in this phase may be rebranded by changing tokens without changing component markup.

```css
:root {
  color-scheme: dark;
  --sp-color-canvas: #0b0f14;
  --sp-color-surface: #121923;
  --sp-color-surface-raised: #1b2634;
  --sp-color-border: #344256;
  --sp-color-text: #f4f7fb;
  --sp-color-text-muted: #aab6c5;
  --sp-color-accent: #5ee1a2;
  --sp-color-on-accent: #062116;
  --sp-color-focus: #8bbcff;
  --sp-color-danger: #ff6b7a;
  --sp-color-on-danger: #2b060b;
  --sp-color-warning: #f5c451;
  --sp-color-scrim: rgb(0 0 0 / 72%);
  --sp-radius-sm: 4px;
  --sp-radius-md: 8px;
  --sp-radius-lg: 12px;
  --sp-shadow-raised: 0 12px 32px rgb(0 0 0 / 28%);
  --sp-content-max: 1280px;
  --sp-control-min: 44px;
}
```

Use the accent only for the primary CTA, selected control, active navigation underline, rating fill, and small recommendation rank marker. Use focus blue exclusively for focus indication. Do not communicate status, rating, errors, or selection by colour alone.

## Spacing Scale

Declared values (multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Icon-to-label or metadata gap |
| `space-2` | 8px | Compact control internals |
| `space-4` | 16px | Default component gap and mobile gutter |
| `space-6` | 24px | Card padding and tablet gutter |
| `space-8` | 32px | Section gap and desktop gutter |
| `space-12` | 48px | Major section separation |
| `space-16` | 64px | Hero/page separation on large screens |

Exceptions: interactive targets are at least 44×44px; 2px focus rings and 1px borders are non-spacing strokes. Cover aspect ratio is fixed at 3:4 and is not a spacing token.

## Typography

Only four sizes and two weights are allowed in Phase 1.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px | 400 | 1.5 |
| Label / metadata | 14px | 600 | 1.4 |
| Section heading | 20px | 600 | 1.25 |
| Page/display heading | 32px | 600 | 1.2 |

- Body and form copy use 16px; never shrink inputs below 16px on mobile.
- Metadata may use 14px but must retain the muted-text contrast target.
- At widths below 640px, display headings remain 32px and wrap; do not scale below the declared set.
- Game titles wrap to two lines in grid cards and fully render on detail pages. Use locale-aware line breaking; never bake translated copy into fixed-width images.
- Use tabular numerals for rating values, years, copy counts, and result counts.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--sp-color-canvas` `#0B0F14` | Page background and image-placeholder base |
| Secondary (30%) | `--sp-color-surface` `#121923`; raised `#1B2634` | Navigation, cards, forms, data panels, menu |
| Accent (10%) | `--sp-color-accent` `#5EE1A2` | Primary CTA, selected control, active-nav underline, filled rating stars, rank marker |
| Destructive | `--sp-color-danger` `#FF6B7A` | Destructive/error states only; Phase 1 has no destructive user action |

Accent reserved for: “Explore catalogue” / “Ver catálogo”, login submit, save/update submit, current segmented option, active navigation indicator, filled star value, and recommendation rank marker. Links inside prose use underlined primary text, not accent alone. All normal text must meet WCAG AA 4.5:1; large text and meaningful graphical boundaries meet 3:1. Verify actual token pairs automatically and in-browser before release.

## Copywriting Contract

Spanish (`es`) and English (`en`) ship together. Spanish is the initial locale unless a saved user preference or `Accept-Language` selects English. A visible language control uses `ES` and `EN`, has accessible name “Idioma / Language,” persists the choice, and never discards form input when changed.

| Element | Spanish | English |
|---------|---------|---------|
| Homepage primary CTA | Ver catálogo | Explore catalogue |
| Homepage login entry | Acceder a la demo | Sign in to demo |
| Homepage value proposition | Tu colección de videojuegos, ordenada y lista para descubrir | Your game collection, organised and ready to discover |
| Navigation: Catalogue | Catálogo | Catalogue |
| Navigation: Collection | Colección | Collection |
| Navigation: Profile | Perfil | Profile |
| Skip link | Saltar al contenido | Skip to content |
| Login submit | Iniciar sesión | Sign in |
| Login pending | Accediendo… | Signing in… |
| Username label | Nombre de usuario | Username |
| Password label | Contraseña | Password |
| Demo credentials heading | Credenciales de demostración | Demo credentials |
| Copy username | Copiar nombre de usuario | Copy username |
| Copy password | Copiar contraseña | Copy password |
| Copy confirmation | Copiado al portapapeles. | Copied to clipboard. |
| Controlled-demo notice | Esta es una demo académica controlada. | This is a controlled academic demo. |
| Search label | Buscar juegos | Search games |
| Search placeholder | Título o título alternativo | Title or alternative title |
| Catalogue scope label | Catálogo de demostración seleccionado | Curated demo catalogue |
| Search empty heading | No encontramos juegos | No games found |
| Search empty body | Prueba con otro título o revisa la ortografía. | Try another title or check the spelling. |
| Clear search query | Borrar búsqueda | Clear search |
| Collection empty heading | Tu colección está vacía | Your collection is empty |
| Collection empty body | Añade un estado o una copia desde la ficha de un juego. | Add a status or copy from a game page. |
| Public collection empty | Aún no hay juegos públicos | No public games yet |
| Popularity empty | Aún no hay suficiente actividad en la demo | Not enough demo activity yet |
| Generic loading | Cargando… | Loading… |
| Generic error | No se pudo cargar esta información. Inténtalo de nuevo. | We couldn’t load this information. Try again. |
| Invalid login credentials | El nombre de usuario o la contraseña no son correctos. Comprueba los datos e inténtalo de nuevo. | The username or password is incorrect. Check the details and try again. |
| Homepage sample failure | No se pudo cargar la muestra del catálogo. Puedes abrir el catálogo completo. | We couldn’t load the catalogue sample. You can open the full catalogue. |
| Open full catalogue | Abrir catálogo completo | Open full catalogue |
| Collection failure | No se pudo cargar tu colección. | We couldn’t load your collection. |
| Retry collection | Reintentar colección | Retry collection |
| Public profile unavailable | Este perfil no está disponible o no existe. | This profile is unavailable or does not exist. |
| Return to catalogue | Volver al catálogo | Return to catalogue |
| Sources unavailable | No se pudieron cargar las fuentes y la metodología. | We couldn’t load the sources and methodology. |
| Reload sources | Volver a cargar las fuentes | Reload sources |
| Not available | No disponible | Not available |
| Unrated | Sin valorar | Unrated |
| Status: Pending | Pendiente | Pending |
| Status: Playing | Jugando | Playing |
| Status: Completed | Completado | Completed |
| Status: Abandoned | Abandonado | Abandoned |
| Cover unavailable | Portada no disponible | Cover unavailable |
| Offline/local-data notice | Modo sin conexión: se muestran los datos locales disponibles. | Offline mode: available local data is shown. |
| Retry catalogue | Reintentar catálogo | Retry catalogue |
| Retry game details | Reintentar detalles del juego | Retry game details |
| Retry recommendations | Reintentar recomendaciones | Retry recommendations |
| Retry sign-in | Reintentar inicio de sesión | Retry sign-in |
| Retry search | Reintentar búsqueda | Retry search |
| Retry status save | Reintentar guardado del estado | Retry status save |
| Retry rating save | Reintentar guardado de la valoración | Retry rating save |
| Retry copy save | Reintentar guardado de la copia | Retry copy save |
| Status save success | Estado guardado. | Status saved. |
| Rating save success | Valoración guardada: {rating} de 5. | Rating saved: {rating} out of 5. |
| Copy save success | Copia añadida. | Copy added. |
| Save status | Guardar estado | Save status |
| Save rating | Guardar valoración | Save rating |
| Add copy | Añadir copia | Add copy |
| Save copy | Guardar copia | Save copy |
| Recommendation label | Popular en la demo | Popular in the demo |
| Provenance link | Ver fuentes y metodología | View sources and methodology |
| Sign out | Cerrar sesión | Sign out |
| Catalogue result count: zero | 0 juegos | 0 games |
| Catalogue result count: one | 1 juego | 1 game |
| Catalogue result count: many | {count} juegos | {count} games |
| Owned copy count: zero | 0 copias | 0 copies |
| Owned copy count: one | 1 copia | 1 copy |
| Owned copy count: many | {count} copias | {count} copies |
| Status summary count: zero | 0 juegos | 0 games |
| Status summary count: one | 1 juego | 1 game |
| Status summary count: many | {count} juegos | {count} games |
| Recommendation count: zero | 0 recomendaciones | 0 recommendations |
| Recommendation count: one | 1 recomendación | 1 recommendation |
| Recommendation count: many | {count} recomendaciones | {count} recommendations |
| Destructive confirmation | No destructive action exists in Phase 1. | No destructive action exists in Phase 1. |

Error copy must name the failed object where useful (“No se pudo guardar la copia / We couldn’t save the copy”), preserve user-entered values, place the matching object-specific retry action from this table beside the message, and never disclose stack traces, identifiers, credentials, or provider details. Do not render a generic “Retry / Reintentar” action.

All visible and announced counts use the canonical zero/one/many rows above; `{count}` is replaced with a locale-formatted integer. These explicit forms are required even when the number is also visually apparent. Do not construct counts by concatenating a number with an untranslated noun.

## Responsive Layout Contract

| Range | Contract |
|-------|----------|
| 0–639px | 16px page gutters; compact top bar; menu button opens a modal navigation sheet; one-column forms and panels; adaptive two-column cover grid when at least 320px wide, otherwise one column; sticky actions prohibited if they obscure content/keyboard |
| 640–1023px | 24px gutters; compact menu remains; 3–4 grid columns using `repeat(auto-fill, minmax(144px, 1fr))`; game detail uses cover plus stacked content |
| 1024–1439px | 32px gutters; full top navigation; 5–6 grid columns; game detail uses 280px cover column plus fluid information/action column; public profile uses main content plus 280px summary rail |
| ≥1440px | Content remains centered at 1280px; no uncontrolled line-length or card stretching; grid may reach 7 columns while covers retain 3:4 ratio |

- Reflow must work at a 320px CSS viewport and at 400% browser zoom without two-dimensional page scrolling. Data local to a copy may wrap vertically rather than become a wide table.
- Use container width, not device detection. No information or action exists only in the large-screen layout.
- Cards reserve the cover aspect-ratio box before images load to prevent layout shift.
- Navigation order and DOM order remain identical across breakpoints.

## Component and Surface Inventory

These are local semantic components to implement, not claims about an installed library.

| Component / surface | Contract |
|---------------------|----------|
| `AppShell` | Skip link, banner/top navigation, `main`, optional footer; max-width token and responsive gutters |
| `TopNavigation` | Logo/home, canonical navigation labels for Catalogue, Collection, and Profile, locale control, session action; current page exposed with `aria-current="page"` |
| `MobileMenu` | Native button with name and expanded state; modal sheet with focus trap, Escape close, close-on-route, focus return, and background scroll lock |
| `Button` | Primary, secondary, quiet variants; 44px minimum; loading keeps label context and disables repeat submit |
| `TextField` | Persistent visible label, optional hint, inline error associated with `aria-describedby`; no placeholder-only labels |
| `Notice` | Informational/offline/error variants with icon, heading where needed, and text; error uses `role="alert"` only after an action fails |
| `CoverImage` | 3:4 frame, useful localized alt on detail/hero; empty alt when adjacent card title duplicates it; lawful placeholder with no fake artwork |
| `GameCard` | Cover, full accessible linked title, year, platform summary, optional status; action never appears only on hover |
| `CoverGrid` | Semantic list, stable result count, adaptive columns; DOM and visual order match |
| `SearchForm` | Labelled search input plus submit; URL-backed query; Enter submits; tolerant matching is server behavior; no autocomplete/filter UI |
| `StatusControl` | `fieldset`/`legend` with the four canonical `Status:` rows; native radios or equivalent roving radio group; current value announced |
| `RatingControl` | 0.5–5.0 in half-star steps, implemented as labelled native range or radio group; arrow keys adjust; visible numeric value; clear/unrated option |
| `CopyForm` | Format, platform, edition only; required fields marked in text; field errors and summary; no Phase 3 private/purchase fields |
| `CopyList` | Semantic list of owned copies with format, platform, edition; private by authenticated ownership boundary |
| `ProvenanceSummary` | Source name, dataset/version, licence label, retrieval date where present, canonical ID, link to methodology; missing values use the canonical `Not available` row |
| `RecommendationStrip` | Ordered popularity results; explicitly labelled baseline; no personalized or explanatory-model claim |
| `Skeleton` | Mirrors final geometry, `aria-hidden="true"`; a single adjacent polite status announces loading |
| `LanguageSwitch` | Two-option labelled control; persists choice; route and form state survive switch |

## Global Interaction and Keyboard Contract

- The first focusable element uses the canonical `Skip link`; activation moves focus to `main`.
- Native links navigate and native buttons act. Do not put click handlers on generic `div`/`span` elements.
- Visible focus is a 2px `--sp-color-focus` outline with 2px offset on every interactive element; it must not be clipped by cards or dialogs.
- Tab order follows DOM/reading order. No positive `tabindex`. Enter activates links/buttons and submits forms; Space activates buttons/radios; Escape closes the mobile menu or non-destructive modal and returns focus to its trigger.
- Search submission updates the URL (`?q=`), places focus on the result heading, and announces the result count through a polite live region. It does not announce on each keystroke.
- Mutations expose pending state without removing the control label, prevent duplicate submission, announce success politely, and focus the error summary on failure while preserving values.
- Status changes and ratings require an explicit save in Phase 1; do not use optimistic success. On success, update the visible value and dated history without full-page focus loss.
- Card hover may reveal supplementary metadata only if the same metadata appears on keyboard focus and remains available on the detail page. No required action is hover-only.
- Star glyphs are decorative. The accessible name is numeric, for example “3.5 de 5 estrellas / 3.5 out of 5 stars.”
- Authentication expiration redirects to login with a localized, non-sensitive notice and an encoded same-origin return path. Never show passwords in URLs or logs.
- Respect `prefers-reduced-motion`; transitions are opacity/colour only, 150ms maximum, and entirely removable. No autoplay, parallax, cover zoom, or essential animation.

## Screen-by-Screen Contract

### 1. Public Homepage (`/`)

- Header: SavePoint wordmark, Catalogue link, locale switch, and visible “Acceder a la demo / Sign in to demo.” Unauthenticated Collection/Profile links route to login with context rather than appearing disabled.
- Hero: one 32px canonical `Homepage value proposition`, short supporting sentence, canonical homepage primary CTA, and canonical homepage login entry.
- Representative catalogue: 6–8 lawful game cards spanning eras/platforms. Never imply these are personalized. Missing covers use the canonical placeholder.
- Value blocks: catalogue, collection, and explainable recommendations described without claiming Phase 1 already implements later algorithms.
- Footer: Sources & methodology, demo limitation, language, and repository/project information if public.
- No product tour, carousel, testimonial fabrication, research dashboard, waitlist, or open-registration CTA.

### 2. Login (`/login`)

- Centered single-column form, maximum width 448px. Username and password use their canonical label rows; password supports browser managers and a labelled reveal control.
- A separate panel uses the canonical `Demo credentials heading` row and displays the approved demo username/password as ordinary selectable text with the canonical `Copy username` and `Copy password` actions. Successful copying announces canonical `Copy confirmation`; credentials never enter query parameters.
- The panel uses the canonical `Controlled-demo notice` row. No registration, password reset, social login, or product tour.
- Invalid credentials render canonical `Invalid login credentials` without revealing whether an account exists. Successful authentication routes to `/catalogue` and focuses its `h1`.

### 3. Catalogue (`/catalogue`)

- `h1`, the canonical `Catalogue scope label`, search form, stable result count using `Catalogue result count: zero`, `Catalogue result count: one`, or `Catalogue result count: many`, then cover grid.
- Initial view shows the full 100–300 item lawful sample in paginated pages or progressive server pagination; Phase 1 page size is 24. Pagination uses real links, retains query/locale, and exposes current page.
- Search covers canonical and bilingual alternative titles, tolerating case, accents, and small typos. No autocomplete, advanced filters, sort controls, infinite-scroll-only behavior, or DLC/expansion result cards.
- Each card shows title, year, concise platform summary, and signed-in status where present. Status badges include text.
- Covers load lazily below the fold, retain dimensions, and fall back to the lawful placeholder on missing/error.

### 4. Game Detail (`/games/{canonical-id}`)

- Breadcrumbs, cover/placeholder, localized title with original/English fallback explicitly marked, year, concise description and available metadata.
- Related releases/platforms/editions are grouped beneath the work. Remakes link as separate related works. DLC/expansions appear as non-actionable child content and cannot be added to backlog.
- Signed-in action panel contains current status, five-star half-step rating, and explicit save actions. Dated status history is a simple newest-first list.
- Ownership panel lists multiple copies and opens an inline or modal Add Copy form with only format, platform, and edition. Platform/edition choices must correspond to the work hierarchy.
- Popularity section uses the canonical `Recommendation label`, shows ordered results, and explains in one sentence that order comes from aggregate demo interactions; do not call it personalized.
- Provenance summary is always visible, not hidden in a tooltip: source, version, licence/rights label, canonical identifier, and detailed methodology link.

### 5. Collection (`/collection`)

- Authenticated-only. `h1`, summary counts by the four statuses using canonical `Status summary count: zero`, `Status summary count: one`, or `Status summary count: many`, and a single text search over the user’s collected works. Do not add advanced filtering or bulk edit.
- Items use compact cover-led cards/list rows showing title, current status, rating, and owned-copy count using canonical `Owned copy count: zero`, `Owned copy count: one`, or `Owned copy count: many`. Private purchase/notes/location fields do not exist in Phase 1 UI or payloads.
- Empty state points back to Catalogue. Zero values render as `0`, never as missing skeletons.
- Selecting an item goes to game detail for edits; Phase 1 does not introduce a second editing model.

### 6. Public Profile (`/profiles/{alias}`)

- Publicly readable only for an authorised demo visitor as defined by the backend access policy; never infer access from hidden UI alone.
- Header: alias, avatar or initials placeholder, demo/public label, and allowed aggregate counts.
- Public collection excerpt shows only title, public status, and rating when permitted by the Phase 1 projection. It never renders owned-copy records, format, platform ownership, edition ownership, notes, purchase data, internal IDs, or email/account data.
- Popularity recommendation strip uses aggregate demo data and is labelled as a baseline, not as the profile owner’s private behavioral explanation.
- Unknown or unavailable profile renders canonical `Public profile unavailable` with canonical `Return to catalogue`; retry is inappropriate because the state intentionally does not distinguish absence from inaccessibility or confirm private account existence.

### 7. Sources and Methodology (`/sources`)

- Plain, readable content page: dataset name/version, source URL, licence/usage summary, retrieval date, checksum, cover-art policy, placeholder policy, offline behavior, and known limitations.
- External links identify the destination and open in the same tab by default. User-visible URLs are validated server-side; no arbitrary redirects.
- The page distinguishes catalogue provenance from a claim of endorsement and labels Phase 1 recommendation logic as a simple popularity baseline.
- If required source content cannot load, render canonical `Sources unavailable` with canonical `Reload sources`; never invent or omit attribution silently.

## State Matrices

### Page and Data Surfaces

| Surface | Loading | Empty / zero | Populated | Error / partial | Offline |
|---------|---------|--------------|-----------|-----------------|---------|
| Homepage sample | 6 geometry-matched skeleton cards | Hide sample grid; keep value proposition and catalogue CTA | 6–8 cards | Canonical `Homepage sample failure` with canonical `Open full catalogue`; render lawful placeholders only for individual cover failures | Same local sample; offline notice only when detected |
| Catalogue | Heading/search remain; 12–24 skeleton cards and canonical `Generic loading` status | Canonical search-empty heading/body and `Clear search query` action | Result count, 24-card page, pagination | Keep any returned cards; inline error plus canonical `Retry catalogue` action. Never blank entire page for cover failures | Full local catalogue remains usable; persistent informational notice |
| Game detail | Breadcrumb/title shell plus cover/panel skeletons | Missing optional field uses canonical `Not available`; zero copies uses canonical `Add copy` prompt | Full hierarchy, actions, provenance | Core local record remains; failed panel uses canonical `Retry game details`; cover gets placeholder | Local record and mutations work if local stack is available; no external request required |
| Collection | Heading and summary skeletons | Contracted empty state with Catalogue link | Counts use canonical `Status summary count: zero/one/many`; rows use canonical `Owned copy count: zero/one/many` | Preserve last rendered data; canonical `Collection failure` with canonical `Retry collection` | Local deployment works; browser network loss shows notice and disables mutations with reason |
| Public profile | Header/content skeletons | Allowed collection uses canonical `Public collection empty` | Allowlisted projection | Canonical `Public profile unavailable` with canonical `Return to catalogue`; never expose private fields in errors | Previously/local server-provided projection remains usable |
| Popularity results | Ordered-card skeletons | Canonical `Popularity empty` and `Recommendation count: zero`; no invented results | Count uses canonical `Recommendation count: one/many`; 6 ordered items in the demo fixture | Label unavailable with canonical `Retry recommendations`; game page remains usable | Precomputed local results render; no provider dependency |
| Sources | Text skeleton only if fetched separately | Not applicable: required release content | Complete source record | Release-blocking canonical `Sources unavailable` with canonical `Reload sources`; no invented attribution | Bundled/local source record renders |

### Forms and Mutations

| Form | Pristine | Invalid | Submitting | Success | Server/network failure |
|------|----------|---------|------------|---------|------------------------|
| Login | Empty fields; demo credentials separate | Inline field errors + linked summary; invalid credential response uses canonical `Invalid login credentials`; focus first invalid field | Button retains canonical `Login submit` context with localized pending state and disables repeat | Route to catalogue | Preserve username, clear password, canonical `Invalid login credentials`, canonical `Retry sign-in` |
| Search | Current query reflected from URL | Whitespace-only becomes unfiltered catalogue | Search button retains canonical `Search label` context; previous results may remain with busy state | Focus result heading; announce count | Preserve query and previous results; error plus canonical `Retry search` |
| Status | Current value selected | Missing selection explained | Button retains canonical `Save status` context | Announce canonical `Status save success` and append dated history | Revert to confirmed state; scoped alert; retain attempted selection; canonical `Retry status save` |
| Rating | Current value or canonical `Unrated` visible | Values outside 0.5–5 blocked | Button retains canonical `Save rating` context | Announce canonical `Rating save success` with exact `{rating}` | Revert confirmed value; scoped alert; retain attempted value; canonical `Retry rating save` |
| Add copy | Format/platform/edition fields | Field errors + summary | Button retains canonical `Save copy` context | Close/reset form, announce canonical `Copy save success`, and focus new copy | Keep entered values, focus error summary, canonical `Retry copy save` |

## Privacy, Security, and Source Transparency Contract

- Hiding a field is not authorization. Public profile responses use a server-generated allowlisted projection and must never include copy-level ownership details or future private inventory fields in HTML, JSON, preload data, logs, or error objects.
- Demo credentials are public test credentials, not infrastructure secrets. No API/provider token, database credential, secret key, or private endpoint may appear in browser bundles, HTML, source maps, cover URLs, screenshots, or UI messages.
- All provider/dataset access occurs server-side. Phase 1 catalogue UI must remain useful with provider access disabled.
- Treat catalogue titles, descriptions, source names, aliases, and external metadata as untrusted text: render as text, never unsanitized HTML; do not allow metadata to inject links, styles, scripts, or UI instructions.
- Only allowlisted `https` source URLs may become external links. Never render user/provider text as a navigation target without validation.
- Every cover needs an asset-rights decision. When display/caching is not permitted or data is absent, use the first-party placeholder rather than a hotlinked or scraped image.
- The placeholder is a token-driven 3:4 surface with controller/bookmark line motif, SavePoint name, and the canonical `Cover unavailable` copy. It must not mimic copyrighted cover art.

## Accessibility Acceptance Checks

The Phase 1 release is not acceptable until all checks below pass on homepage, login, catalogue, one game detail, collection, public profile, and sources page in both locales.

- [ ] Automated axe scan has no critical or serious violations at 375×812 and 1280×800.
- [ ] Keyboard-only path completes: homepage → login → catalogue search → game detail → status → 3.5-star rating → add two copies → collection → public profile → sign out.
- [ ] Every interactive control has a visible name, role, state, focus indicator, and 44×44px target (or equivalent inline spacing exception documented by WCAG).
- [ ] Heading hierarchy has one `h1`; landmarks include banner/navigation/main/contentinfo where present; skip link works.
- [ ] Focus is never lost after navigation, menu/modal close, validation failure, loading completion, or mutation success.
- [ ] At 320px width and 400% zoom, content reflows without horizontal page scrolling or clipped controls.
- [ ] Text contrast is at least 4.5:1; focus, component boundaries, and meaningful graphics are at least 3:1; automated token tests cover every declared pair.
- [ ] Rating and status are operable and understandable without colour, star shape, pointer, or hover.
- [ ] Spanish and English have parity: no raw translation keys, missing labels, mixed-language loading/error text, or layout clipping under 30% text expansion.
- [ ] Reduced-motion mode removes non-essential transition motion; no animation flashes or autoplays.
- [ ] Cover alternatives avoid duplicate announcements; placeholder and failure behavior are announced meaningfully where the image carries information.
- [ ] Live regions announce result count and mutation outcomes once, without repeating entire grids or interrupting initial page load.
- [ ] Public profile DOM, network payload, page source, and accessible tree contain no private copy or account fields.

## UI Considerations

Applicable state considerations resolved: 8 covered, 0 backstop, 0 unresolved.

| Category | Element(s) | Status | Resolution / Reason |
|----------|------------|--------|---------------------|
| empty | Catalogue results, collection, recommendations, public profile collection | ✓ covered | Every collection surface has explicit zero/empty behavior and references localized Copywriting Contract rows where applicable. |
| loading | Catalogue, detail, collection, profile, recommendations | ✓ covered | Geometry-matched skeletons reserve layout; one polite status announces loading and skeletons are hidden from accessibility APIs. |
| error | Pages, scoped panels, all mutations | ✓ covered | Scoped retry, value preservation, safe localized messages, and focus behavior are defined in the state matrices. |
| populated | All collection and detail surfaces | ✓ covered | Required information hierarchy, result counts, ordering, provenance, and action placement are specified screen by screen. |
| partial | Catalogue covers, game metadata, profile/recommendation panels | ✓ covered | Core local data remains visible; missing assets use lawful placeholders and failed secondary panels cannot blank the page. |
| overflow | Cover grid, navigation, metadata, copy list | ✓ covered | Adaptive grid, wrapping, bounded content width, mobile menu, and vertical copy rows prevent page-level horizontal overflow. |
| zero-one-many | Copies, results, status counts, recommendation items | ✓ covered | Zero copy/results language, singular/plural localized count handling, multiple owned copies, and paginated catalogue behavior are explicit. |
| long-text | Bilingual copy, titles, descriptions, aliases, source/licence labels | ✓ covered | Titles wrap, prose reflows, cards clamp only redundant title previews, and acceptance includes 30% expansion plus 400% zoom. |

## Registry Safety

Not applicable. No shadcn installation or third-party registry block is part of Phase 1. Any later registry adoption requires a new inventory enumeration and source-vetting pass before it becomes contractual.

## Explicit Phase 1 Exclusions

Do not render placeholders, disabled navigation, teaser cards, or “coming soon” controls for: advanced filters, autocomplete, live enrichment controls, comments, custom lists, import/export, purchase/conservation/storage/private-note fields, delete flows, per-release ratings, content/collaborative/hybrid recommendations, recommendation explanations, experiments, research charts/dashboard, unrestricted registration, or admin operations. Their absence is intentional scope control, not an empty state.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS
- [ ] Dimension 7 Inventory Provenance: PASS (not applicable because Tool is none)

**Approval:** pending

## Decision Provenance

| Source | Decisions used |
|--------|----------------|
| `01-CONTEXT.md` | D-01 through D-20, including flow, catalogue scope, bilingual behavior, domain hierarchy, rating/status/copy model, visual direction, navigation, and deferred boundaries |
| `REQUIREMENTS.md` | 23 Phase 1 requirements, especially AUTH-01, CAT-01/03/04/06, LIB-01/02, INV-01/02/05, DATA-01/02, REC-02, SEC-02, OPS-01/02/03, and QUAL-03 |
| `ROADMAP.md` | Three-day demo-grade boundary and five Phase 1 success criteria |
| `research/SUMMARY.md` | Next.js/React/Tailwind direction, immutable/local data boundary, public allowlist, server-side provider access, accessibility and reproducibility risks |
| Repository scan | Greenfield status; no existing design system, components, or tokens |
