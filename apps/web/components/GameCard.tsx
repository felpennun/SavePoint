import Link from "next/link";

import { CoverImage } from "@/components/CoverImage";
import { ScorePill } from "@/components/ScorePill";
import { StarRating } from "@/components/StarRating";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import type { GameCard as GameCardData } from "@/lib/api";

/**
 * GameCard -- the single game card used on every page (catalogue,
 * collection, home, and every recommendation shelf), so the surface reads
 * the same everywhere (Nocturne identity artboard 1k). Structure: a cover
 * in a fixed 2:3 box flush at the top (clipped by the card radius, no
 * CLS), then a padded body -- a title row with the ScorePill slot beside
 * the 2-line-clamped title, a mono "year · platforms" meta line, an
 * optional plain-language evidence line (recommendation shelves), and,
 * when the collection context supplies them, a divided foot with the
 * backlog status line, the personal StarRating and an owned-copies count.
 * The whole card is one <Link>; nothing is hover-only.
 */
export function GameCard({
  game,
  locale,
  score,
  status,
  ratingHalfSteps,
  ownedCopyCount,
  coverVariant = "grid",
  evidence,
}: {
  game: GameCardData;
  locale: string;
  score?: number | null;
  status?: BacklogStatus;
  ratingHalfSteps?: number | null;
  ownedCopyCount?: number;
  coverVariant?: "grid" | "shelf";
  /** Plain-language reason this card is here (e.g. the genre-overlap
   * evidence on the recommendations shelf). Rendered under the meta line. */
  evidence?: string;
}) {
  const dict = getDictionary(locale);
  const { width, height } = coverVariant === "shelf" ? { width: 164, height: 246 } : { width: 200, height: 300 };
  const metaParts = [game.year != null ? String(game.year) : null, game.platform_summary].filter(Boolean);
  const showStars = ratingHalfSteps != null && ratingHalfSteps > 0;
  const showCopies = ownedCopyCount != null && ownedCopyCount > 0;
  const hasFoot = status != null || showStars || showCopies;

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
        </div>
        <div className="sp-card-body">
          <div className="sp-card-head">
            <p className="sp-card-title">{game.title}</p>
            <ScorePill
              rating={score}
              ariaLabelTemplate={dict.card.score.aria}
              emptyLabel={dict.card.score.none}
            />
          </div>
          {metaParts.length > 0 ? <p className="sp-card-meta">{metaParts.join(" · ")}</p> : null}
          {evidence ? <p className="sp-card-evidence">{evidence}</p> : null}
          {hasFoot ? (
            <div className="sp-card-foot">
              {status ? <StatusPill status={status} label={dict.status.labels[status]} bare /> : null}
              {showStars ? (
                <StarRating value={ratingHalfSteps as number} ariaLabelTemplate={dict.card.rating.aria} />
              ) : null}
              {showCopies ? (
                <span className="sp-card-copies">
                  {formatCount(dict.collection.ownedCopyCount, ownedCopyCount as number)}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
      </Link>
    </li>
  );
}
