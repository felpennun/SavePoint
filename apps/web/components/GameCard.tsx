import Link from "next/link";

import type { GameCard as GameCardData } from "@/lib/api";

/**
 * Catalogue/collection card (UI-SPEC GameCard): cover, full accessible
 * linked title, year, concise platform summary. The whole card is a
 * single link -- no action is hover-only, and keyboard focus reaches the
 * same information a mouse hover would.
 */
export function GameCard({ game, locale }: { game: GameCardData; locale: string }) {
  return (
    <li>
      <Link href={`/${locale}/games/${game.slug}`} className="block">
        <div style={{ aspectRatio: "3 / 4" }} className="overflow-hidden rounded-lg bg-[var(--color-surface-raised)]">
          {game.cover.is_placeholder ? (
            <div
              className="flex h-full w-full items-center justify-center text-sm"
              style={{ color: "var(--color-text-muted)" }}
              data-testid="cover-placeholder"
            >
              {game.title}
            </div>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element -- lawful placeholder/cover, external allowlisted host only
            <img src={game.cover.url ?? undefined} alt={game.cover.alt} loading="lazy" className="h-full w-full object-cover" />
          )}
        </div>
        <p className="mt-2 font-medium" style={{ color: "var(--color-text-primary)" }}>
          {game.title}
        </p>
        <p className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
          {game.year ?? ""} {game.year ? "·" : ""} {game.platform_summary}
        </p>
      </Link>
    </li>
  );
}
