"use client";

import { useEffect } from "react";

import { recordRecentGame, type RecentGame } from "@/lib/recent-games";

/** Records the current game as visited (localStorage) so it shows up in
 * the home "Pick up where you left off" section. Renders nothing. */
export function RecordGameVisit({ game }: { game: RecentGame }) {
  useEffect(() => {
    recordRecentGame(game);
    // Re-record whenever the game changes (client nav between detail pages
    // reuses this component instance). Keyed on slug -- the rest of the
    // payload is stable for a given game.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [game.slug]);

  return null;
}
