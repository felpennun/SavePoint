import type { ReactNode } from "react";
import { HoverPrefetchLink } from "@/components/HoverPrefetchLink";

import { CoverImage } from "@/components/CoverImage";
import { PlatinumBadge } from "@/components/PlatinumBadge";
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
  bare = false,
  isPlatinum = false,
  itemClassName,
  overlay,
}: {
  game: GameCardData;
  locale: string;
  score?: number | null;
  status?: BacklogStatus;
  ratingHalfSteps?: number | null;
  ownedCopyCount?: number;
  coverVariant?: "grid" | "shelf";
  /** Plain-language reason this card is here (e.g. the tag-overlap
   * evidence on the recommendations shelf). Rendered under the meta line. */
  evidence?: string;
  /** Nocturne home artboard (2b): drop the whole card panel -- render just
   * the cover poster with the title and year underneath it, no surface,
   * no score pill, no foot. Used for the logged-out home sample and the
   * "Novedades" shelf, where the browse journey leads with the artwork. */
  bare?: boolean;
  /** Personal "platinum" mark -- Collection page only. GameCard never
   * fetches this itself; the caller decides whether the current context
   * (owner's own collection) is allowed to show it at all. */
  isPlatinum?: boolean;
  /** Extra class for the list item that wraps the card. */
  itemClassName?: string;
  /** Extra control laid over the card (e.g. the collection list's "remove" toggle). */
  overlay?: ReactNode;
}) {
  const dict = getDictionary(locale);
  const { width, height } = coverVariant === "shelf" ? { width: 164, height: 246 } : { width: 200, height: 300 };
  const metaParts = [game.year != null ? String(game.year) : null, game.platform_summary].filter(Boolean);
  const showStars = ratingHalfSteps != null && ratingHalfSteps > 0;
  const showCopies = ownedCopyCount != null && ownedCopyCount > 0;
  const hasFoot = status != null || showStars || showCopies;

  const cover = game.cover.is_placeholder ? (
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
  );

  if (bare) {
    return (
      <li>
        <HoverPrefetchLink href={`/${locale}/games/${game.slug}`} className="sp-tile">
          <div className="sp-cover">{cover}</div>
          <p className="sp-tile-title">{game.title}</p>
          {game.year != null ? <p className="sp-tile-meta">{game.year}</p> : null}
        </HoverPrefetchLink>
      </li>
    );
  }

  return (
    <li className={itemClassName}>
      <HoverPrefetchLink href={`/${locale}/games/${game.slug}`} className="sp-card">
        <div className="sp-cover">
          {cover}
          {isPlatinum ? <PlatinumBadge label={dict.card.platinum.label} /> : null}
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
              {showStars || showCopies ? (
                <div className="sp-card-rating-copies">
                  {showStars ? (
                    <StarRating value={ratingHalfSteps as number} ariaLabelTemplate={dict.card.rating.aria} />
                  ) : null}
                  {showStars && showCopies ? (
                    <span aria-hidden="true" className="sp-card-dot">·</span>
                  ) : null}
                  {showCopies ? (
                    <span className="sp-card-copies">
                      {formatCount(dict.collection.ownedCopyCount, ownedCopyCount as number)}
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </HoverPrefetchLink>
      {overlay}
    </li>
  );
}
