import Link from "next/link";

import { CoverImage } from "@/components/CoverImage";
import { ScorePill } from "@/components/ScorePill";
import { StarRating } from "@/components/StarRating";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import type { GameCard as GameCardData } from "@/lib/api";

/**
 * Catalogue / collection / recommendation-shelf card (01.1-UI-SPEC
 * GameCard). Cover in a fixed 3:4 box (no CLS), 2-line-clamped linked
 * title, "year · platforms" meta. Overlays: ScorePill top-right when an
 * IGDB rating is present; StatusPill top-left in the collection context.
 * Authenticated personal rating -> gold StarRating under the title.
 * Optional "{n} copies" chip (collection). The whole card is one <Link>;
 * nothing is hover-only.
 */
export function GameCard({
  game,
  locale,
  score,
  status,
  ratingHalfSteps,
  ownedCopyCount,
  coverVariant = "grid",
}: {
  game: GameCardData;
  locale: string;
  score?: number | null;
  status?: BacklogStatus;
  ratingHalfSteps?: number | null;
  ownedCopyCount?: number;
  coverVariant?: "grid" | "shelf";
}) {
  const dict = getDictionary(locale);
  const { width, height } = coverVariant === "shelf" ? { width: 120, height: 160 } : { width: 156, height: 208 };
  const metaParts = [game.year != null ? String(game.year) : null, game.platform_summary].filter(Boolean);

  return (
    <li>
      <Link href={`/${locale}/games/${game.slug}`} className="sp-card">
        <div className="sp-cover">
          {game.cover.is_placeholder ? (
            <div className="sp-cover-placeholder" data-testid="cover-placeholder">
              <span>{game.title}</span>
              <span className="visually-hidden">{dict.common.coverMissing}</span>
            </div>
          ) : (
            <CoverImage
              src={game.cover.url}
              alt={game.cover.alt}
              title={game.title}
              missingLabel={dict.common.coverMissing}
              width={width}
              height={height}
            />
          )}
          {status ? (
            <StatusPill status={status} label={dict.status.labels[status]} onCover />
          ) : null}
          <ScorePill rating={score} ariaLabelTemplate={dict.card.score.aria} />
        </div>
        <p className="sp-card-title">{game.title}</p>
        <p className="sp-card-meta">{metaParts.join(" · ")}</p>
        {ratingHalfSteps != null && ratingHalfSteps > 0 ? (
          <StarRating value={ratingHalfSteps} ariaLabelTemplate={dict.card.rating.aria} />
        ) : null}
        {ownedCopyCount != null && ownedCopyCount > 0 ? (
          <span className="sp-copies-chip">{formatCount(dict.collection.ownedCopyCount, ownedCopyCount)}</span>
        ) : null}
      </Link>
    </li>
  );
}
