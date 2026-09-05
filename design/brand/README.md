# SavePoint brand assets — "Cristal" direction (staged)

Author-supplied identity, produced in a separate design pass and staged here on
2026-09-05 for wiring during the Phase 01.1 redesign. **Nothing here is referenced
by the app yet** — integration is plan **01.1-06** (Wave 3).

## Files

| File | Use | Themes |
|---|---|---|
| `logo-mark.svg` / `logo-mark-light.svg` | Icon only, transparent background, 64×64 viewBox | dark / light |
| `logo-mono.svg` | Icon, single ink via `currentColor` (inherits text color when inlined) | either |
| `favicon.svg` / `favicon-light.svg` | Icon on a rounded tile (browser tab / PWA) | dark / light |
| `logo-lockup.svg` / `logo-lockup-light.svg` | Mark + "SavePoint" wordmark, horizontal, 408×88 | dark / light |
| `logo-lockup-mono.svg` | Lockup, single ink via `currentColor` | either |
| `banner-og.svg` / `banner-og-light.svg` | 1200×630 social / OpenGraph card | dark / light |

## Design notes

- **Mark:** a save-point crystal (diamond outline + hollow inner diamond) with a small
  solid violet inner diamond and an underline bar. Reads down to 16px (favicon).
- **Wordmark:** drawn entirely as outlined `<path>` data — no font dependency. The
  banners' tagline/label text uses `<text>` with a `system-ui` fallback stack (matches
  the UI-SPEC typography decision).
- **Palette matches `01.1-UI-SPEC.md` tokens:**
  - dark: surfaces `#0d0d12` / `#17171f`, text `#f2f2f5` / `#aaaab8`, accent `#8b7cf6`
  - light: surfaces `#ffffff` / `#f5f5f7`, text `#17171f` / `#626272`, accent `#6d5cd6`
  - The violet is used only as the small inner-diamond accent (consistent with the 10% accent rule).

## On ingest

The supplied SVGs arrived with a UTF-8→cp1252 mojibake in their `<title>`/`<desc>`/
comments and (for the banners) the visible `<text>` — repaired to correct UTF-8 when
staged (`ó á é í`, `·`, `—`). Path geometry was untouched.

## For plan 01.1-06 (integration checklist)

- [ ] Pick the final set (mark vs lockup per placement).
- [ ] Favicon: `apps/web/app/[locale]/` or `apps/web/app/` `icon.svg` (Next.js metadata) — decide whether to serve the theme-appropriate variant or a single `currentColor` mark.
- [ ] Navbar brand: `logo-lockup` (or mark + text) in `AppShell`, theme-swapped with the `sp-theme` mechanism.
- [ ] OpenGraph: wire `banner-og.svg` (or a PNG export) via Next.js `opengraph-image`. Note `next.config.ts` currently has no `images` config.
- [ ] Remove the `02 / CRISTAL` iteration label from the banner before shipping — it's a design-round marker, not final copy.
- [ ] If PNG rasters are needed (some OG consumers don't accept SVG), export at the target sizes; do not add a raster toolchain dependency without the usual approval gate.
