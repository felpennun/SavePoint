/**
 * Shared catalogue filter/sort vocabulary (01.1-UI-SPEC Screen Contract 2,
 * CAT-02). All controls submit via GET so every filtered view is a
 * shareable URL. The server-side query wiring is Plan 03; this module is
 * the client contract -- the allowlists here are what the page validates
 * incoming `searchParams` against (RESEARCH security V5: unknown values
 * are ignored / fall back to the default, never trusted).
 *
 * The platform/genre option lists are a curated placeholder set pending
 * Plan 03's option endpoint; the FilterBar degrades to search-only if a
 * list is ever passed empty.
 */

export const SORT_KEYS = [
  "relevance",
  "title_asc",
  "title_desc",
  "release_newest",
  "release_oldest",
  "rating_desc",
] as const;
export type SortKey = (typeof SORT_KEYS)[number];

export const DEFAULT_SORT: SortKey = "release_newest";

export function resolveSort(raw: string | undefined, hasQuery: boolean): SortKey {
  if (raw && (SORT_KEYS as readonly string[]).includes(raw)) return raw as SortKey;
  return hasQuery ? "relevance" : DEFAULT_SORT;
}

export const MIN_RATING_OPTIONS = ["70", "80", "90"] as const;

/** Curated placeholder platform slugs (Plan 03 replaces with the full
 * 220-row list from the option endpoint). */
export const PLATFORM_OPTIONS: { value: string; label: string }[] = [
  { value: "win", label: "PC (Microsoft Windows)" },
  { value: "ps5", label: "PlayStation 5" },
  { value: "ps4", label: "PlayStation 4" },
  { value: "series-x", label: "Xbox Series X|S" },
  { value: "xone", label: "Xbox One" },
  { value: "switch", label: "Nintendo Switch" },
  { value: "switch-2", label: "Nintendo Switch 2" },
  { value: "mac", label: "macOS" },
  { value: "linux", label: "Linux" },
  { value: "ios", label: "iOS" },
  { value: "android", label: "Android" },
];

/** Curated placeholder genre slugs (Plan 03 replaces with the 23-row
 * IGDB genre list). */
export const GENRE_OPTIONS: { value: string; label: string }[] = [
  { value: "rpg", label: "Role-playing (RPG)" },
  { value: "adventure", label: "Adventure" },
  { value: "shooter", label: "Shooter" },
  { value: "platform", label: "Platform" },
  { value: "puzzle", label: "Puzzle" },
  { value: "strategy", label: "Strategy" },
  { value: "simulator", label: "Simulator" },
  { value: "sport", label: "Sport" },
  { value: "fighting", label: "Fighting" },
  { value: "racing", label: "Racing" },
  { value: "indie", label: "Indie" },
  { value: "arcade", label: "Arcade" },
  { value: "tactical", label: "Tactical" },
  { value: "hack-and-slash", label: "Hack and slash / Beat 'em up" },
  { value: "visual-novel", label: "Visual Novel" },
  { value: "point-and-click", label: "Point-and-click" },
];

export const FILTER_PARAM_KEYS = ["q", "platform", "genre", "year_from", "year_to", "min_rating", "sort"] as const;

export interface CatalogueFilters {
  q?: string;
  platform?: string;
  genre?: string;
  year_from?: string;
  year_to?: string;
  min_rating?: string;
  sort: SortKey;
}

/** Parse + validate raw searchParams into a safe filter object. Unknown
 * platform/genre/min_rating values are dropped; years are clamped and
 * swapped if from > to. */
export function parseFilters(
  sp: Record<string, string | undefined>,
  currentYear: number,
): CatalogueFilters {
  const q = sp.q?.trim() || undefined;
  const platform = PLATFORM_OPTIONS.some((o) => o.value === sp.platform) ? sp.platform : undefined;
  const genre = GENRE_OPTIONS.some((o) => o.value === sp.genre) ? sp.genre : undefined;
  const minRating = (MIN_RATING_OPTIONS as readonly string[]).includes(sp.min_rating ?? "") ? sp.min_rating : undefined;

  const clampYear = (v: string | undefined): number | undefined => {
    if (!v) return undefined;
    const n = Number(v);
    if (!Number.isInteger(n)) return undefined;
    return Math.min(Math.max(n, 1958), currentYear + 2);
  };
  let from = clampYear(sp.year_from);
  let to = clampYear(sp.year_to);
  if (from != null && to != null && from > to) [from, to] = [to, from];

  return {
    q,
    platform,
    genre,
    year_from: from != null ? String(from) : undefined,
    year_to: to != null ? String(to) : undefined,
    min_rating: minRating,
    sort: resolveSort(sp.sort, Boolean(q)),
  };
}

/** Count of user-set filters (sort at its default and empty q do not
 * count). */
export function countActiveFilters(f: CatalogueFilters): number {
  let n = 0;
  if (f.q) n += 1;
  if (f.platform) n += 1;
  if (f.genre) n += 1;
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
  if (f.platform) params.set("platform", f.platform);
  if (f.genre) params.set("genre", f.genre);
  if (f.year_from) params.set("year_from", f.year_from);
  if (f.year_to) params.set("year_to", f.year_to);
  if (f.min_rating) params.set("min_rating", f.min_rating);
  if (f.sort && f.sort !== DEFAULT_SORT) params.set("sort", f.sort);
  if (page && page > 1) params.set("page", String(page));
  const s = params.toString();
  return s ? `?${s}` : "";
}
