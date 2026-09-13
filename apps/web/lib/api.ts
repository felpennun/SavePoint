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

export interface TagRef {
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
  /** Mixed external + SavePoint product score (D-09). */
  display_rating?: number | null;
  /** Number of IGDB user/critic ratings used by the relevance threshold. */
  total_rating_count?: number | null;
  /** Curated unified tags for this work. */
  tags?: TagRef[];
}

export interface FacetOption {
  slug: string;
  name: string;
  count: number;
}

export interface CatalogueDateFacet {
  value: string;
  label: string;
  count: number;
}

export interface CatalogueFacets {
  platforms: FacetOption[];
  editions: FacetOption[];
  genres: FacetOption[];
  franchises: FacetOption[];
  developers: FacetOption[];
  publishers: FacetOption[];
  modes: FacetOption[];
  tags: FacetOption[];
  dates: CatalogueDateFacet[];
  year_range: { min: number | null; max: number | null };
}

export interface CatalogueListParams {
  q?: string;
  page?: number;
  platform?: string[];
  tag?: string[];
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
  display_rating: number | null;
  rating_breakdown: { igdb_count: number; savepoint_count: number };
  cover: Cover;
  releases: Release[];
  related_content: RelatedContentItem[];
  provenance: Provenance | null;
  /** Curated unified tags; absent -> the tags row is omitted. */
  tags?: TagRef[];
  /** IGDB total_rating (0-100). Wired by Plan 03; absent -> no ScorePill. */
  total_rating?: number | null;
}

export interface OwnedDlcItem {
  work_id: string;
  slug: string;
  title: string;
  cover: Cover;
  relation: "dlc" | "expansion";
}

export interface OwnedDlcGroup {
  base_game: { slug: string; title: string };
  dlc: OwnedDlcItem[];
}

export interface OwnedDlcResult {
  groups: OwnedDlcGroup[];
}

export async function fetchCatalogueList(
  params: CatalogueListParams = {},
  cookieHeader?: string,
): Promise<CatalogueListResult> {
  const url = new URL("/api/catalogue/games/", API_BASE);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.page) url.searchParams.set("page", String(params.page));
  if (params.platform) {
    for (const platform of params.platform) url.searchParams.append("platform", platform);
  }
  if (params.tag) {
    for (const tag of params.tag) url.searchParams.append("tag", tag);
  }
  if (params.edition) {
    for (const edition of params.edition) url.searchParams.append("edition", edition);
  }
  if (params.genre) {
    for (const genre of params.genre) url.searchParams.append("genre", genre);
  }
  if (params.franchise) {
    for (const franchise of params.franchise) url.searchParams.append("franchise", franchise);
  }
  if (params.developer) {
    for (const developer of params.developer) url.searchParams.append("developer", developer);
  }
  if (params.publisher) {
    for (const publisher of params.publisher) url.searchParams.append("publisher", publisher);
  }
  if (params.mode) {
    for (const mode of params.mode) url.searchParams.append("mode", mode);
  }
  if (params.year_from) url.searchParams.set("year_from", params.year_from);
  if (params.year_to) url.searchParams.set("year_to", params.year_to);
  if (params.date_from) url.searchParams.set("date_from", params.date_from);
  if (params.date_to) url.searchParams.set("date_to", params.date_to);
  if (params.min_rating) url.searchParams.set("min_rating", params.min_rating);
  if (params.sort) url.searchParams.set("sort", params.sort);

  const response = await fetch(url, {
    cache: "no-store",
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
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

/** One slot of the public five-slot favorites shelf; `null` for an empty
 * slot (PROF-01/D-02, `build_public_profile`). */
export type PublicFavoriteSlot = { work_slug: string; work_title: string } | null;

export interface PublicProfileComment {
  work_slug: string;
  work_title: string;
  text: string;
}

export interface PublicProfileListItem {
  work_slug: string;
  work_title: string;
  position: number;
}

export interface PublicProfileList {
  name: string;
  items: PublicProfileListItem[];
}

export interface BasicPublicProfile {
  kind: "basic";
  alias: string;
  bio: string;
  avatar_url: string;
  action: "login" | "send_friend_request" | "request_sent" | "review_friend_request";
}

export interface ProtectedPublicProfile {
  kind: "protected";
  alias: string;
  bio: string;
  avatar_url: string;
  activity: PublicProfileActivityItem[];
  summary: Record<string, number>;
  favorites: PublicFavoriteSlot[];
  comments: PublicProfileComment[];
  lists: PublicProfileList[];
}

export type PublicProfile = BasicPublicProfile | ProtectedPublicProfile;

function normalizePublicProfile(body: unknown): PublicProfile {
  if (!body || typeof body !== "object") throw new Error("Invalid public profile response");
  const value = body as Record<string, unknown>;
  if (value.kind === "basic" || value.kind === "protected") return value as unknown as PublicProfile;
  // Django's response predates the explicit discriminator. Add it once at
  // the SSR boundary so UI callers never infer access from empty content.
  if (typeof value.action === "string") return { ...value, kind: "basic" } as BasicPublicProfile;
  return { ...value, kind: "protected" } as ProtectedPublicProfile;
}

export async function fetchPublicProfile(alias: string, cookieHeader = ""): Promise<PublicProfile | null> {
  const url = new URL(`/api/accounts/profiles/${encodeURIComponent(alias)}/`, API_BASE);
  const response = await fetch(url, {
    cache: "no-store",
    ...(cookieHeader ? { headers: { Cookie: cookieHeader } } : {}),
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load public profile (status ${response.status})`);
  }
  return normalizePublicProfile(await response.json());
}

export interface FriendCollectionItem {
  game: { slug: string; title: string };
  cover: Cover;
  year: number | null;
  platform: string;
  backlog_status: string | null;
  personal_rating: number | null;
}

export interface SharedCollection {
  items: FriendCollectionItem[];
}

export interface SharedList {
  name: string;
  items: FriendCollectionItem[];
}

async function fetchSharedProjection<T>(path: string, cookieHeader: string): Promise<T | null> {
  const url = new URL(path, API_BASE);
  const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Failed to load protected social projection (status ${response.status})`);
  return (await response.json()) as T;
}

export function fetchSharedCollection(alias: string, cookieHeader: string): Promise<SharedCollection | null> {
  return fetchSharedProjection<SharedCollection>(
    `/api/library/profiles/${encodeURIComponent(alias)}/collection/`,
    cookieHeader,
  );
}

export function fetchSharedList(alias: string, listSlug: string, cookieHeader: string): Promise<SharedList | null> {
  return fetchSharedProjection<SharedList>(
    `/api/library/profiles/${encodeURIComponent(alias)}/lists/${encodeURIComponent(listSlug)}/`,
    cookieHeader,
  );
}

export type SocialRelationship = "none" | "pending_sent" | "pending_received" | "friend" | "blocked";

export interface SocialAccount {
  alias: string;
  avatar_url: string;
  bio: string;
  relationship: SocialRelationship;
}

export interface SocialFriendshipRequest {
  id: string;
  sender_alias: string;
  receiver_alias: string;
  status: "pending";
  created_at: string;
}

export interface SocialRequests {
  received: SocialFriendshipRequest[];
  sent: SocialFriendshipRequest[];
}

export interface SocialFriend {
  alias: string;
  relationship: "friend";
}

export interface SocialFriends {
  friends: SocialFriend[];
}

export interface SocialHubData {
  requests: SocialRequests;
  friendships: SocialFriends;
}

async function fetchSocialJson<T>(path: string, cookieHeader: string): Promise<T | null> {
  const response = await fetch(new URL(path, API_BASE), {
    cache: "no-store",
    headers: { Cookie: cookieHeader },
  });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok) throw new Error(`Failed to load social data (status ${response.status})`);
  return (await response.json()) as T;
}

export async function fetchSocialHubData(cookieHeader: string): Promise<SocialHubData | null> {
  const [requests, friendships] = await Promise.all([
    fetchSocialJson<SocialRequests>("/api/social/requests/", cookieHeader),
    fetchSocialJson<SocialFriends>("/api/social/friendships/", cookieHeader),
  ]);
  if (!requests || !friendships) return null;
  return { requests, friendships };
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
  display_rating: number | null;
  owned_copy_count: number;
  year: number | null;
  platform_summary: string;
  cover: Cover;
  updated_at?: string;
  /** Owner-only "platinum" mark -- rendered exclusively on the Collection
   * page (never the catalogue, home shelves, or the public profile). */
  is_platinum?: boolean;
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

/** Per-item tag-overlap evidence from the tag-taste-v1 heuristic: a
 * tag the recommended work shares with the signed-in user's own rated /
 * status-tracked library, plus that tag's accumulated taste weight. */
export interface RecommendationMatchedTag {
  slug: string;
  name: string;
  weight: number;
}

/** One ranked catalogue work from `GET /api/recommendations/genre-taste/`. */
export interface PersonalRecommendationItem {
  work_id: string;
  slug: string;
  title: string;
  score: number;
  /** IGDB catalogue rating used to order candidates; null means unrated. */
  catalogue_rating: number | null;
  catalogue_rating_count: number;
  /** Product-facing blended rating, shared with the game detail page. */
  display_rating: number | null;
  year: number | null;
  platform_summary: string;
  cover: Cover;
  matched_tags: RecommendationMatchedTag[];
}

export interface ContentRecommendationItem {
  work_id: string;
  slug: string;
  title: string;
  score: number;
  contributions: { tag: string; contribution_pct: number }[];
  rating_term: number;
  rating_term_is_fallback: boolean;
  /** Product-facing blended rating, shared with catalogue and detail cards. */
  display_rating: number | null;
  signals: {
    external_rating: number | null;
    rating_bayesian_normalized?: number | null;
    rating_quality: number | null;
    rating_confidence: number | null;
    rating_final?: number | null;
    rating_volume: number | null;
    popscore: number | null;
    popscore_imputed: boolean;
    recency_score: number | null;
    hybrid_content_score?: number;
    hybrid_collaborative_score?: number;
    hybrid_content_weight?: number;
    hybrid_collaborative_weight?: number;
    hybrid_collaborative_fallback?: boolean;
    hybrid_relevance_score?: number;
    mmr_relevance?: number;
    mmr_redundancy?: number;
    mmr_score?: number;
  };
  reason: ContentRecommendationReason | null;
  year: number | null;
  platform_summary: string;
  cover: Cover;
}

export interface ContentRecommendationReason {
  kind: "signal_overlap";
    signals: {
      kind: "tag" | "theme" | "mode" | "feature" | "platform" | "franchise" | "developer";
      slug: string;
      name: string;
    }[];
}

export interface ContentRecommendationsResult {
  protocol_version: 10;
  algorithm_id: string;
  generated_at: string;
  input_snapshot_sha256: string;
  feature_set_version: string;
  corpus_version: string | null;
  snapshot_sha256: string;
  candidate_manifest_sha256: string;
  candidate_count: number;
  explorable_count: number;
  eligibility_cutoff_date: string;
  insufficient_history: boolean;
  limitation: string;
  parameters?: Record<string, number | string>;
  results: ContentRecommendationItem[];
}

export type ContentRecommendationsResponse =
  | { kind: "ok"; data: ContentRecommendationsResult }
  | { kind: "unauthorized" }
  | { kind: "error" };

export type RecommendationSnapshotStatus = "empty" | "building" | "stale" | "ready" | "needs_refresh";

export interface RecommendationSnapshotResult {
  status: RecommendationSnapshotStatus;
  current_revision: number;
  published_revision: number | null;
  generated_at: string | null;
  job_status: string | null;
  error: string | null;
  sections: {
    content: Record<string, ContentRecommendationsResult>;
    tags: PersonalRecommendationsResult;
  } | null;
}

export type RecommendationSnapshotResponse =
  | { kind: "ok"; data: RecommendationSnapshotResult }
  | { kind: "unauthorized" }
  | { kind: "error" };

/** Read the last published personal bundle without waiting for a refresh job. */
export async function getRecommendationSnapshot(
  cookieHeader: string,
): Promise<RecommendationSnapshotResponse> {
  const url = new URL("/api/recommendations/snapshot/", API_BASE);
  try {
    const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
    if (response.status === 401 || response.status === 403) return { kind: "unauthorized" };
    if (!response.ok) return { kind: "error" };
    return { kind: "ok", data: (await response.json()) as RecommendationSnapshotResult };
  } catch {
    return { kind: "error" };
  }
}

export async function getContentRecommendations(
  cookieHeader: string,
  limit = 20,
): Promise<ContentRecommendationsResponse> {
  const url = new URL("/api/recommendations/content/", API_BASE);
  url.searchParams.set("limit", String(limit));
  try {
    const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
    if (response.status === 401 || response.status === 403) return { kind: "unauthorized" };
    if (!response.ok) return { kind: "error" };
    return { kind: "ok", data: (await response.json()) as ContentRecommendationsResult };
  } catch {
    return { kind: "error" };
  }
}

export async function getNewReleases(): Promise<GameCard[]> {
  const url = new URL("/api/catalogue/new-releases/", API_BASE);
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load new releases (status ${response.status})`);
  }
  return (await response.json()) as GameCard[];
}

export async function getOwnedDlc(cookieHeader: string): Promise<OwnedDlcResult> {
  const url = new URL("/api/catalogue/owned-dlc/", API_BASE);
  const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
  if (!response.ok) {
    throw new Error(`Failed to load owned DLC (status ${response.status})`);
  }
  return (await response.json()) as OwnedDlcResult;
}

/** The allowlisted DTO of the authenticated tag-taste recommender
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
  primary_tag?: {
    slug: string;
    name: string;
    entry_count: number;
    weight: number;
  } | null;
  results: PersonalRecommendationItem[];
}

export type PersonalRecommendationsResponse =
  | { kind: "ok"; data: PersonalRecommendationsResult }
  | { kind: "unauthorized" }
  | { kind: "error" };

/** The single deterministic tag shelf shown in the product. */
export interface PersonalRecommendationShelf {
  /** Display name of the taste genre this shelf is built around. */
  tag: string;
  tagSlug: string;
  /** The user's accumulated taste weight for this tag (shelf ordering). */
  tasteWeight: number;
  items: PersonalRecommendationItem[];
}

/**
 * Personalized tag-taste recommendations (REC-10). Server-side only: a
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

/** Return only the dominant-library-tag shelf, capped at 20 items. */
export function primaryTagRecommendationShelf(
  result: PersonalRecommendationsResult,
  { maxItems = 20 }: { maxItems?: number } = {},
): PersonalRecommendationShelf | null {
  if (result.insufficient_history || result.results.length === 0) return null;

  const tags = new Map<string, { name: string; weight: number }>();
  for (const item of result.results) {
    for (const tag of item.matched_tags) {
      const existing = tags.get(tag.slug);
      if (!existing || tag.weight > existing.weight) {
        tags.set(tag.slug, { name: tag.name, weight: tag.weight });
      }
    }
  }

  const fallback = [...tags.entries()]
    .sort(([slugA, a], [slugB, b]) => b.weight - a.weight || slugA.localeCompare(slugB))[0];
  const primary = result.primary_tag ?? (fallback
    ? { slug: fallback[0], name: fallback[1].name, weight: fallback[1].weight }
    : null);
  if (primary === null) return null;
  const items = result.results
    .filter((item) => item.matched_tags.some((tag) => tag.slug === primary.slug))
    .slice(0, maxItems);
  return items.length > 0
    ? { tag: primary.name, tagSlug: primary.slug, tasteWeight: primary.weight, items }
    : null;
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

/** Owner-facing profile read DTO (PROF-01, `serialize_account_profile`) --
 * never includes `username`; the alias is the login username and is
 * rendered from `AccountMe`/route params, never from this response. */
export interface MyProfile {
  bio: string;
  avatar_url: string;
  collection_visibility: "public" | "private";
  favorites_visibility: "public" | "private";
}

export async function fetchMyProfile(cookieHeader: string): Promise<MyProfile | null> {
  const url = new URL("/api/accounts/me/profile/", API_BASE);
  try {
    const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
    if (!response.ok) return null;
    return (await response.json()) as MyProfile;
  } catch {
    return null;
  }
}

/** Owner-facing favorites DTO (D-02, `serialize_favorite_slots`) -- always
 * five positions; `work_id` is `null` for an empty slot. */
export interface MyFavoriteSlot {
  slot: number;
  work_id: string | null;
  work_slug: string | null;
  work_title: string | null;
}

export async function fetchMyFavorites(cookieHeader: string): Promise<MyFavoriteSlot[]> {
  const url = new URL("/api/accounts/me/favorites/", API_BASE);
  try {
    const response = await fetch(url, { cache: "no-store", headers: { Cookie: cookieHeader } });
    if (!response.ok) return [];
    const body = (await response.json()) as { slots?: unknown };
    return Array.isArray(body.slots) ? (body.slots as MyFavoriteSlot[]) : [];
  } catch {
    return [];
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
