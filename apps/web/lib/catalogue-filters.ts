/**
 * Shared catalogue filter/sort vocabulary. Every value is submitted through
 * GET so a copied URL is a reproducible catalogue query.
 */

export const SORT_KEYS = [
  "popscore_desc",
  "relevance",
  "title_asc",
  "title_desc",
  "release_newest",
  "release_oldest",
  "rating_desc",
] as const;
export type SortKey = (typeof SORT_KEYS)[number];

export const DEFAULT_SORT: SortKey = "popscore_desc";

export function resolveSort(raw: string | undefined): SortKey {
  if (raw && (SORT_KEYS as readonly string[]).includes(raw)) return raw as SortKey;
  return DEFAULT_SORT;
}

export const MIN_RATING_OPTIONS = ["50", "60", "70", "80", "90"] as const;

export interface FilterOption {
  value: string;
  label: string;
}

export const REPEATED_FACET_KEYS = [
  "platform",
  "tag",
  "edition",
  "genre",
  "franchise",
  "developer",
  "publisher",
  "mode",
] as const;
export type RepeatedFacetKey = (typeof REPEATED_FACET_KEYS)[number];

export const FILTER_PARAM_KEYS = [
  "q",
  ...REPEATED_FACET_KEYS,
  "year_from",
  "year_to",
  "date_from",
  "date_to",
  "min_rating",
  "sort",
] as const;

/** Stable presentation order for the governed platform allowlist. */
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
  tag: string[];
  edition?: string[];
  genre?: string[];
  franchise?: string[];
  developer?: string[];
  publisher?: string[];
  mode?: string[];
  year_from?: string;
  year_to?: string;
  date_from?: string;
  date_to?: string;
  min_rating?: string;
  sort: SortKey;
}

export type FacetOptionKey =
  | "platforms"
  | "editions"
  | "genres"
  | "franchises"
  | "developers"
  | "publishers"
  | "modes"
  | "tags";

export type CatalogueFacetOptions = Partial<Record<FacetOptionKey, FilterOption[]>>;

const FACET_OPTION_KEYS: Record<RepeatedFacetKey, FacetOptionKey> = {
  platform: "platforms",
  tag: "tags",
  edition: "editions",
  genre: "genres",
  franchise: "franchises",
  developer: "developers",
  publisher: "publishers",
  mode: "modes",
};

const FACET_DEFAULTS: Pick<CatalogueFilters, RepeatedFacetKey> = {
  platform: [],
  tag: [],
  edition: [],
  genre: [],
  franchise: [],
  developer: [],
  publisher: [],
  mode: [],
};

function validDateBound(raw: string | undefined, currentYear: number): string | undefined {
  if (!raw) return undefined;
  const value = raw.trim();
  const yearMatch = /^(\d{4})$/.exec(value);
  if (yearMatch) {
    const year = Number(yearMatch[1]);
    return year >= 1950 && year <= currentYear + 2 ? value : undefined;
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) return undefined;
  const year = Number(value.slice(0, 4));
  return year >= 1950 && year <= currentYear + 2 ? value : undefined;
}

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function normalizedFacetValues(value: string | string[] | undefined): string[] {
  const values = Array.isArray(value) ? value : value == null ? [] : [value];
  return [...new Set(values.map((item) => item.trim()).filter(Boolean))];
}

/** Parse raw Next.js searchParams into a safe, backend-shaped filter object. */
export function parseFilters(
  sp: Record<string, string | string[] | undefined>,
  currentYear: number,
): CatalogueFilters {
  const values = Object.fromEntries(
    REPEATED_FACET_KEYS.map((key) => [key, normalizedFacetValues(sp[key])]),
  ) as Pick<CatalogueFilters, RepeatedFacetKey>;

  const minRatingRaw = firstValue(sp.min_rating);
  const minRating = (MIN_RATING_OPTIONS as readonly string[]).includes(minRatingRaw ?? "")
    ? minRatingRaw
    : undefined;

  return {
    q: firstValue(sp.q)?.trim() || undefined,
    ...FACET_DEFAULTS,
    ...values,
    year_from: validDateBound(firstValue(sp.year_from), currentYear),
    year_to: validDateBound(firstValue(sp.year_to), currentYear),
    date_from: validDateBound(firstValue(sp.date_from), currentYear),
    date_to: validDateBound(firstValue(sp.date_to), currentYear),
    min_rating: minRating,
    sort: resolveSort(firstValue(sp.sort)),
  };
}

/** Count each selected value and each scalar bound as an active filter. */
export function countActiveFilters(f: CatalogueFilters): number {
  let count = f.q ? 1 : 0;
  for (const key of REPEATED_FACET_KEYS) count += f[key]?.length ?? 0;
  if (f.year_from) count += 1;
  if (f.year_to) count += 1;
  if (f.date_from) count += 1;
  if (f.date_to) count += 1;
  if (f.min_rating) count += 1;
  return count;
}

/** Restrict selected controls to options returned by the local API facets. */
export function restrictSelectedFilters(
  filters: CatalogueFilters,
  facets: CatalogueFacetOptions,
): CatalogueFilters {
  const next = { ...filters };
  for (const key of REPEATED_FACET_KEYS) {
    const options = facets[FACET_OPTION_KEYS[key]];
    if (options) {
      next[key] = (filters[key] ?? []).filter((value) => options.some((option) => option.value === value));
    }
  }
  return next;
}

/** Build a deterministic query using the backend's exact parameter names. */
export function buildQuery(f: Partial<CatalogueFilters>, page?: number): string {
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  for (const key of REPEATED_FACET_KEYS) {
    for (const value of f[key] ?? []) params.append(key, value);
  }
  if (f.year_from) params.set("year_from", f.year_from);
  if (f.year_to) params.set("year_to", f.year_to);
  if (f.date_from) params.set("date_from", f.date_from);
  if (f.date_to) params.set("date_to", f.date_to);
  if (f.min_rating) params.set("min_rating", f.min_rating);
  if (f.sort && f.sort !== DEFAULT_SORT) params.set("sort", f.sort);
  if (page && page > 1) params.set("page", String(page));
  const query = params.toString();
  return query ? `?${query}` : "";
}

/** Remove one occurrence of a repeated facet while preserving all other GET state. */
export function removeHref(current: string, key: RepeatedFacetKey, value: string): string {
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
