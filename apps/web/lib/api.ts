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

export interface Release {
  id: string;
  release_name: string;
  release_date: string | null;
  platform: string | null;
  editions: string[];
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
