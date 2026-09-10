"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import { readRecentGames, type RecentGame } from "@/lib/recent-games";

/** Home "Pick up where you left off" section: the five most recently
 * opened game pages, read from localStorage on mount. Client-only -- the
 * server render is the empty shell so there is no hydration mismatch. */
export function RecentGames({
  locale,
  heading,
  emptyText,
  emptyCta,
}: {
  locale: string;
  heading: string;
  emptyText: string;
  emptyCta: string;
}) {
  const [games, setGames] = useState<RecentGame[] | null>(null);

  useEffect(() => {
    setGames(readRecentGames());
  }, []);

  return (
    <section aria-labelledby="recent-games-heading">
      <h2 id="recent-games-heading" className="sp-h2">
        {heading}
      </h2>
      {games && games.length > 0 ? (
        <ul className="sp-grid">
          {games.map((game) => (
            <GameCard
              key={game.slug}
              game={{
                id: game.slug,
                slug: game.slug,
                title: game.title,
                year: game.year,
                platform_summary: game.platform_summary,
                cover: game.cover,
              }}
              locale={locale}
              score={game.display_rating}
            />
          ))}
        </ul>
      ) : (
        <p className="sp-lead">
          {emptyText}{" "}
          <Link href={`/${locale}/catalogue`} className="sp-link">
            {emptyCta}
          </Link>
        </p>
      )}
    </section>
  );
}
