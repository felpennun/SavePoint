/**
 * "Pick up where you left off" is backed by the five most recently opened
 * game detail pages, kept per-browser in localStorage (no server round
 * trip, no history table). Every read/write is guarded -- a private
 * window, blocked site data or a thumbnail context can throw or return
 * nothing, and the home section must still render.
 */
export interface RecentGame {
  slug: string;
  title: string;
  year: number | null;
  platform_summary: string;
  display_rating: number | null;
  cover: { url: string | null; is_placeholder: boolean; alt: string };
}

const STORAGE_KEY = "sp-recent-games";
const MAX_ENTRIES = 5;

export function readRecentGames(): RecentGame[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (entry): entry is RecentGame =>
          entry != null &&
          typeof entry.slug === "string" &&
          typeof entry.title === "string" &&
          typeof entry.cover === "object",
      )
      .slice(0, MAX_ENTRIES);
  } catch {
    return [];
  }
}

/** Move `game` to the front of the recent list (dedup by slug, cap 5). */
export function recordRecentGame(game: RecentGame): void {
  try {
    const next = [game, ...readRecentGames().filter((entry) => entry.slug !== game.slug)].slice(
      0,
      MAX_ENTRIES,
    );
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable -- the feature degrades to empty, nothing else breaks */
  }
}
