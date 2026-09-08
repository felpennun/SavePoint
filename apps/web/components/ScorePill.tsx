/**
 * ScorePill (01.1-UI-SPEC First-Party Component Contracts). IGDB
 * `total_rating` (0-100) as a rounded integer in a pill whose text/border
 * use the tier color ramp; background is always --color-surface-overlay.
 * Never uses --color-accent. `rating == null` renders nothing -- the
 * caller shows `card.score.none` visually-hidden if it needs to.
 */
export function ScorePill({
  rating,
  ariaLabelTemplate,
  className,
  withLabel,
  label,
}: {
  rating: number | null | undefined;
  /** e.g. dict.card.score.aria = "Rating {n} out of 100" */
  ariaLabelTemplate: string;
  className?: string;
  /** Show a localized textual label next to the number (detail page). */
  withLabel?: boolean;
  label?: string;
}) {
  if (rating == null || Number.isNaN(rating)) return null;
  const value = Math.round(rating);
  const tier = value < 40 ? "weak" : value < 75 ? "fair" : "strong";
  const ariaLabel = ariaLabelTemplate.replace("{n}", String(value));

  return (
    <span
      className={`sp-score-pill sp-score-${tier}${className ? ` ${className}` : ""}`}
      role="img"
      aria-label={ariaLabel}
    >
      {withLabel ? `${label ?? ""} ${value}`.trim() : value}
    </span>
  );
}
