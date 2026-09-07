/**
 * Server-side fetch helpers (RESEARCH.md pattern: browser -> Next.js SSR ->
 * server-only fetch -> Django/DRF). Next.js rewrites only apply to incoming
 * requests, not outgoing fetches from within a Server Component, so these
 * call the Django backend directly via the same internal URL the rewrite
 * proxy targets. Never imported from a Client Component.
 */

const API_BASE = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export interface CoverAttribution {
  creator: string;
  licence: string;
  licence_url: string;
  source_url: string;
}

export interface Cover {
  url: string | null;
  is_placeholder: boolean;
  alt: string;
  attribution?: CoverAttribution;
}

export interface GenreRef {
  slug: string;
  name: string;
}

export interface GameCard {
  id: string;
  slug: string;
  title: string;
  year: number | null;
  platform_summary: string;
  cover: Cover;
  /** IGDB total_rating (0-100). Absent -> no ScorePill. */
  total_rating?: number | null;
  /** Number of IGDB user/critic ratings used by the relevance threshold. */
  total_rating_count?: number | null;
  /** IGDB genres for this work (CAT-02). */
  genres?: GenreRef[];
}

export interface FacetOption {
  slug: string;
  name: string;
  count: number;
}

export interface CatalogueFacets {
  platforms: FacetOption[];
  genres: FacetOption[];
  year_range: { min: number | null; max: number | null };
}

export interface CatalogueListParams {
  q?: string;
  page?: number;
  platform?: string;
  genre?: string;
  year_from?: string;
  year_to?: string;
  min_rating?: string;
  sort?: string;
}

export interface CatalogueListResult {
  results: GameCard[];
  count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  /** The sort key the server actually applied (relevance may fall back). */
  sort: string;
  /** Filter facet options + counts for the current text-scoped result set. */
  facets: CatalogueFacets;
}

export interface EditionOption {
  id: string;
  name: string;
}

export interface Release {
  id: string;
  release_name: string;
  release_date: string | null;
  platform: string | null;
  editions: EditionOption[];
}

export interface RelatedContentItem {
  id: string;
  slug: string;
  title: string;
  relation: "dlc" | "expansion";
  year: number | null;
  platform_summary: string;
  cover: Cover;
}

export interface Provenance {
  source: string;
  source_id: string;
  source_url: string;
  licence: string;
  retrieved_at: string;
  snapshot_sha256: string;
}

export interface GameDetail {
  id: string;
  slug: string;
  title: string;
  title_en: string;
  title_es: string;
  original_title: string;
  is_dlc: boolean;
  year: number | null;
  summary: string;
  rating: number | null;
  rating_count: number | null;
  total_rating_count: number | null;
  rating_breakdown: { igdb_count: number; savepoint_count: number };
  cover: Cover;
  releases: Release[];
  related_content: RelatedContentItem[];
  provenance: Provenance | null;
  /** Wired by Plan 03; absent -> the genres row is omitted. */
  genres?: GenreRef[];
  /** IGDB total_rating (0-100). Wired by Plan 03; absent -> no ScorePill. */
  total_rating?: number | null;
}

export async function fetchCatalogueList(params: CatalogueListParams = {}): Promise<CatalogueListResult> {
  const url = new URL("/api/catalogue/games/", API_BASE);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.page) url.searchParams.set("page", String(params.page));
  if (params.platform) url.searchParams.set("platform", params.platform);
  if (params.genre) url.searchParams.set("genre", params.genre);
  if (params.year_from) url.searchParams.set("year_from", params.year_from);
  if (params.year_to) url.searchParams.set("year_to", params.year_to);
  if (params.min_rating) url.searchParams.set("min_rating", params.min_rating);
  if (params.sort) url.searchParams.set("sort", params.sort);

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load catalogue (status ${response.status})`);
  }
  return (await response.json()) as CatalogueListResult;
}

export async function fetchGameDetail(slug: string, locale: "es" | "en" = "en"): Promise<GameDetail | null> {
  const url = new URL(`/api/catalogue/games/${encodeURIComponent(slug)}/`, API_BASE);
  url.searchParams.set("locale", locale);
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load game detail (status ${response.status})`);
  }
  return (await response.json()) as GameDetail;
}

export interface PublicProfileActivityItem {
  work_slug: string;
  work_title: string;
  status: string;
}

export interface PublicProfile {
  alias: string;
  activity: PublicProfileActivityItem[];
  summary: Record<string, number>;
}

export async function fetchPublicProfile(alias: string): Promise<PublicProfile | null> {
  const url = new URL(`/api/accounts/profiles/${encodeURIComponent(alias)}/`, API_BASE);
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load public profile (status ${response.status})`);
  }
  return (await response.json()) as PublicProfile;
}

export interface PopularityResultItem {
  work_id: string;
  slug: string;
  title: string;
  score: number;
}

export interface PopularityResult {
  algorithm_id: string;
  generated_at: string;
  input_snapshot_sha256: string;
  results: PopularityResultItem[];
  limitation: string;
}

export async function fetchPopularity(): Promise<PopularityResult> {
  const url = new URL("/api/library/popularity/", API_BASE);
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load popularity baseline (status ${response.status})`);
  }
  return (await response.json()) as PopularityResult;
}

export interface MyLibraryItem {
  work_id: string;
  work_slug: string;
  work_title: string;
  status: string;
  rating_half_steps: number | null;
  owned_copy_count: number;
  year: number | null;
  platform_summary: string;
  cover: Cover;
  updated_at?: string;
}

export interface MyLibraryResult {
  items: MyLibraryItem[];
  summary: Record<string, number>;
}

/**
 * Authenticated fetch -- the browser never talks to Django directly, but a
 * Server Component's own fetch() doesn't automatically carry the visitor's
 * cookies (it's a fresh server-to-server request), so the session cookie
 * must be forwarded explicitly. Call this only with a cookie header read
 * from the incoming request (via next/headers `cookies()` in the caller).
 */
export async function fetchMyLibrary(cookieHeader: string): Promise<MyLibraryResult> {
  const url = new URL("/api/library/entries/", API_BASE);
  const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
  if (!response.ok) {
    throw new Error(`Failed to load collection (status ${response.status})`);
  }
  return (await response.json()) as MyLibraryResult;
}

/** Per-item genre-overlap evidence from the genre-taste-v1 heuristic: a
 * genre the recommended work shares with the signed-in user's own rated /
 * status-tracked library, plus that genre's accumulated taste weight. */
export interface RecommendationMatchedGenre {
  slug: string;
  name: string;
  weight: number;
}

/** One ranked catalogue work from `GET /api/recommendations/genre-taste/`.
 * The endpoint returns a flat, score-ordered list; the page groups it into
 * per-genre shelves for display (D-UI-4). */
export interface PersonalRecommendationItem {
  work_id: string;
  slug: string;
  title: string;
  score: number;
  /** IGDB catalogue rating used to order candidates; null means unrated. */
  catalogue_rating: number | null;
  catalogue_rating_count: number;
  year: number | null;
  platform_summary: string;
  cover: Cover;
  matched_genres: RecommendationMatchedGenre[];
}

/** The allowlisted DTO of the authenticated genre-taste recommender
 * (REC-10, Plan 01.1-05). `algorithm_id` + `limitation` are surfaced
 * verbatim on the page so this personal heuristic can never be confused
 * with the public popularity baseline (REC-02) or the Phase 6 research
 * recommender (REC-03). `insufficient_history: true` is a distinct shape
 * with `results: []` and its own `limitation` string -- it never falls
 * back to popularity (D-09). */
export interface PersonalRecommendationsResult {
  algorithm_id: string;
  generated_at: string;
  input_snapshot_sha256: string;
  insufficient_history: boolean;
  limitation: string;
  results: PersonalRecommendationItem[];
}

export type PersonalRecommendationsResponse =
  | { kind: "ok"; data: PersonalRecommendationsResult }
  | { kind: "unauthorized" }
  | { kind: "error" };

/** A genre-grouped shelf built from the flat DTO for display. */
export interface PersonalRecommendationShelf {
  /** Display name of the taste genre this shelf is built around. */
  genre: string;
  genreSlug: string;
  /** The user's accumulated taste weight for this genre (shelf ordering). */
  tasteWeight: number;
  items: PersonalRecommendationItem[];
}

/**
 * Personalized genre-taste recommendations (REC-10). Server-side only: a
 * Server Component's own `fetch()` does not carry the visitor's cookies,
 * so the session cookie read from the incoming request must be forwarded
 * explicitly (same pattern as `fetchMyLibrary`). The endpoint is
 * `IsAuthenticated`; a `401`/`403` is surfaced as `"unauthorized"` so the
 * caller can redirect to login without leaking that the resource exists.
 */
export async function getPersonalRecommendations(
  cookieHeader: string,
  limit?: number,
): Promise<PersonalRecommendationsResponse> {
  const url = new URL("/api/recommendations/genre-taste/", API_BASE);
  if (limit != null) url.searchParams.set("limit", String(limit));
  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
  } catch {
    return { kind: "error" };
  }
  if (response.status === 401 || response.status === 403) return { kind: "unauthorized" };
  if (!response.ok) return { kind: "error" };
  try {
    return { kind: "ok", data: (await response.json()) as PersonalRecommendationsResult };
  } catch {
    return { kind: "error" };
  }
}

/**
 * Reshape the flat, score-ordered DTO into genre-grouped shelves (D-UI-4):
 * one shelf per top taste genre, ordered by the user's own genre-taste
 * weight (descending, `slug` ascending tie-break for determinism), capped
 * at `maxShelves`. A work that overlaps several taste genres appears on
 * each of those shelves. Within a shelf the DTO's score order is
 * preserved. Returns `[]` for the insufficient-history shape.
 */
export function groupRecommendationsByGenre(
  result: PersonalRecommendationsResult,
  { maxShelves = 4, maxItemsPerShelf = 12 }: { maxShelves?: number; maxItemsPerShelf?: number } = {},
): PersonalRecommendationShelf[] {
  if (result.insufficient_history || result.results.length === 0) return [];

  const genres = new Map<string, { name: string; weight: number }>();
  for (const item of result.results) {
    for (const genre of item.matched_genres) {
      const existing = genres.get(genre.slug);
      if (!existing || genre.weight > existing.weight) {
        genres.set(genre.slug, { name: genre.name, weight: genre.weight });
      }
    }
  }

  return [...genres.entries()]
    .sort(([slugA, a], [slugB, b]) => b.weight - a.weight || slugA.localeCompare(slugB))
    .slice(0, maxShelves)
    .map(([slug, { name, weight }]) => ({
      genre: name,
      genreSlug: slug,
      tasteWeight: weight,
      items: result.results
        .filter((item) => item.matched_genres.some((genre) => genre.slug === slug))
        .slice(0, maxItemsPerShelf),
    }))
    .filter((shelf) => shelf.items.length > 0);
}

export interface AccountMe {
  username: string;
}

/**
 * The signed-in simulated account's own identity. The endpoint is wired
 * by Plan 04/08; until then this resolves to `null` and callers degrade
 * to an alias-free greeting.
 */
export async function fetchAccountMe(cookieHeader: string): Promise<AccountMe | null> {
  const url = new URL("/api/accounts/me/", API_BASE);
  try {
    const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
    if (!response.ok) return null;
    const body = (await response.json()) as { username?: unknown };
    return typeof body.username === "string" ? { username: body.username } : null;
  } catch {
    return null;
  }
}

export interface SourcesSummary {
  source: string;
  source_url: string;
  licence: string;
  retrieved_at: string;
  snapshot_sha256: string;
  record_count: number;
  approved_asset_count: number;
  total_asset_candidate_count: number;
}

export async function fetchSources(): Promise<SourcesSummary | null> {
  const url = new URL("/api/catalogue/sources/", API_BASE);
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 503) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load sources summary (status ${response.status})`);
  }
  return (await response.json()) as SourcesSummary;
}
