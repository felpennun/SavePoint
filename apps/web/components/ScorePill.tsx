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
  labelPrefix = "IGDB",
}: {
  rating: number | null | undefined;
  /** e.g. dict.card.score.aria = "IGDB rating {n} out of 100" */
  ariaLabelTemplate: string;
  className?: string;
  /** Show a textual "IGDB {n}" instead of the bare number (detail page). */
  withLabel?: boolean;
  labelPrefix?: string;
}) {
  if (rating == null || Number.isNaN(rating)) return null;
  const value = Math.round(rating);
  const tier = value < 40 ? "weak" : value < 75 ? "fair" : "strong";
  const label = ariaLabelTemplate.replace("{n}", String(value));

  return (
    <span
      className={`sp-score-pill sp-score-${tier}${className ? ` ${className}` : ""}`}
      role="img"
      aria-label={label}
    >
      {withLabel ? `${labelPrefix} ${value}` : value}
    </span>
  );
}
