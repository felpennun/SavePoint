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

/** A selectable filter option, as rendered in the FilterBar `<select>`. The
 * catalogue page derives these from the API `facets` payload. */
export interface FilterOption {
  value: string;
  label: string;
}

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
 * min_rating values are dropped; platform/genre slugs pass through (the API
 * validates them); years are clamped and swapped if from > to. */
export function parseFilters(
  sp: Record<string, string | undefined>,
  currentYear: number,
): CatalogueFilters {
  const q = sp.q?.trim() || undefined;
  const platform = sp.platform?.trim() || undefined;
  const genre = sp.genre?.trim() || undefined;
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
