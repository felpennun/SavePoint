/**
 * Shared catalogue filter/sort vocabulary (01.1-UI-SPEC Screen Contract 2,
 * CAT-02). All controls submit via GET so every filtered view is a
 * shareable URL.
 *
 * The `sort` and `min_rating` vocabularies are fixed client-side; the
 * catalogue API validates them again and returns a bounded 400 for anything
 * off-list (RESEARCH security V5). Platform/genre slugs are open-ended (the
 * real option lists come from the API `facets` payload at request time), so
 * `parseFilters` passes them through untouched and lets the server drop any
 * value it does not recognise.
 */

export const SORT_KEYS = [
  "popscore_desc",
] as const;
export type SortKey = (typeof SORT_KEYS)[number];

export const DEFAULT_SORT: SortKey = "popscore_desc";

export function resolveSort(raw: string | undefined): SortKey {
  if (raw && (SORT_KEYS as readonly string[]).includes(raw)) return raw as SortKey;
  return DEFAULT_SORT;
}

export const MIN_RATING_OPTIONS = ["70", "80", "90"] as const;

/** A selectable filter option, as rendered in a FacetMenu checkbox list. The
 * catalogue page derives these from the API `facets` payload. */
export interface FilterOption {
  value: string;
  label: string;
}

export const FILTER_PARAM_KEYS = ["q", "platform", "genre", "year_from", "year_to", "min_rating", "sort"] as const;

/** Stable presentation order for the governed platform allowlist. Current
 * consoles come first, followed by previous generations and other platforms.
 * Options not in this list are retained at the end in label order. */
export const PLATFORM_DISPLAY_ORDER = [
  "nintendo-switch",
  "playstation-5",
  "xbox-series-x-s",
  "playstation-4",
  "xbox-one",
  "wii-u",
  "nintendo-3ds",
  "playstation-vita",
  "wii",
  "xbox-360",
  "playstation-3",
  "nintendo-ds",
  "playstation-2",
  "gamecube",
  "playstation-portable",
  "xbox",
  "dreamcast",
  "nintendo-64",
  "game-boy-advance",
  "game-boy-color",
  "game-boy",
  "snes",
  "nes",
  "sega-saturn",
  "sega-mega-drive-genesis",
  "sega-game-gear",
  "sega-master-system",
  "atari-jaguar",
  "atari-lynx",
  "atari-7800",
  "atari-5200",
  "atari-2600",
  "pc-microsoft-windows",
  "mac",
  "linux",
  "ios",
  "android",
  "web-browser",
] as const;

export function sortPlatformOptions(options: FilterOption[]): FilterOption[] {
  const order = new Map<string, number>(PLATFORM_DISPLAY_ORDER.map((slug, index) => [slug, index]));
  return [...options].sort((a, b) => {
    const rankA = order.get(a.value) ?? Number.MAX_SAFE_INTEGER;
    const rankB = order.get(b.value) ?? Number.MAX_SAFE_INTEGER;
    return rankA - rankB || a.label.localeCompare(b.label) || a.value.localeCompare(b.value);
  });
}

export interface CatalogueFilters {
  q?: string;
  platform: string[];
  genre: string[];
  year_from?: string;
  year_to?: string;
  min_rating?: string;
  sort: SortKey;
}

/** Parse + validate raw searchParams into a safe filter object. Unknown
 * min_rating values are dropped; platform/genre slugs pass through (the API
 * validates them); years are clamped and swapped if from > to. */
export function parseFilters(
  sp: Record<string, string | string[] | undefined>,
  currentYear: number,
): CatalogueFilters {
  const firstValue = (value: string | string[] | undefined): string | undefined =>
    Array.isArray(value) ? value[0] : value;
  const normalizeFacet = (value: string | string[] | undefined): string[] => {
    const values = Array.isArray(value) ? value : value == null ? [] : [value];
    return [...new Set(values.map((item) => item.trim()).filter(Boolean))];
  };

  const q = firstValue(sp.q)?.trim() || undefined;
  const platform = normalizeFacet(sp.platform);
  const genre = normalizeFacet(sp.genre);
  const minRatingRaw = firstValue(sp.min_rating);
  const minRating = (MIN_RATING_OPTIONS as readonly string[]).includes(minRatingRaw ?? "") ? minRatingRaw : undefined;

  const clampYear = (v: string | undefined): number | undefined => {
    if (!v) return undefined;
    const n = Number(v);
    if (!Number.isInteger(n)) return undefined;
    return Math.min(Math.max(n, 1958), currentYear + 2);
  };
  let from = clampYear(firstValue(sp.year_from));
  let to = clampYear(firstValue(sp.year_to));
  if (from != null && to != null && from > to) [from, to] = [to, from];

  return {
    q,
    platform,
    genre,
    year_from: from != null ? String(from) : undefined,
    year_to: to != null ? String(to) : undefined,
    min_rating: minRating,
    sort: resolveSort(firstValue(sp.sort)),
  };
}

/** Count of user-set filters (sort at its default and empty q do not
 * count). */
export function countActiveFilters(f: CatalogueFilters): number {
  let n = 0;
  if (f.q) n += 1;
  n += f.platform.length;
  n += f.genre.length;
  if (f.year_from) n += 1;
  if (f.year_to) n += 1;
  if (f.min_rating) n += 1;
  return n;
}

/** Build a query string from a filter object (+ optional page), omitting
 * empties and the default sort. */
export function buildQuery(f: Partial<CatalogueFilters>, page?: number): string {
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  if (f.platform) {
    for (const platform of f.platform) params.append("platform", platform);
  }
  if (f.genre) {
    for (const genre of f.genre) params.append("genre", genre);
  }
  if (f.year_from) params.set("year_from", f.year_from);
  if (f.year_to) params.set("year_to", f.year_to);
  if (f.min_rating) params.set("min_rating", f.min_rating);
  if (f.sort && f.sort !== DEFAULT_SORT) params.set("sort", f.sort);
  if (page && page > 1) params.set("page", String(page));
  const s = params.toString();
  return s ? `?${s}` : "";
}

/** Remove one occurrence of a repeated query parameter while preserving all
 * other values and parameters. */
export function removeHref(current: string, key: "genre" | "platform", value: string): string {
  const params = new URLSearchParams(current.startsWith("?") ? current.slice(1) : current);
  const next = new URLSearchParams();
  let removed = false;

  for (const [param, paramValue] of params) {
    if (!removed && param === key && paramValue === value) {
      removed = true;
      continue;
    }
    next.append(param, paramValue);
  }

  const query = next.toString();
  return query ? `?${query}` : "";
}
