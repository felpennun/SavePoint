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

export interface GameCard {
  id: string;
  slug: string;
  title: string;
  year: number | null;
  platform_summary: string;
  cover: Cover;
}

export interface CatalogueListResult {
  results: GameCard[];
  count: number;
  page: number;
  page_size: number;
  has_next: boolean;
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
  cover: Cover;
  releases: Release[];
  related_content: RelatedContentItem[];
  provenance: Provenance | null;
}

export async function fetchCatalogueList(params: { q?: string; page?: number } = {}): Promise<CatalogueListResult> {
  const url = new URL("/api/catalogue/games/", API_BASE);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.page) url.searchParams.set("page", String(params.page));

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load catalogue (status ${response.status})`);
  }
  return (await response.json()) as CatalogueListResult;
}

export async function fetchGameDetail(slug: string): Promise<GameDetail | null> {
  const url = new URL(`/api/catalogue/games/${encodeURIComponent(slug)}/`, API_BASE);
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
