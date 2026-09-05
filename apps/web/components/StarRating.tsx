/**
 * StarRating (01.1-UI-SPEC). Presentational: renders `value` (0-10
 * half-steps) as 5 gold stars / half-stars in --color-rating.
 * `role="img"` + aria-label from dict.card.rating.aria so the tier is
 * never conveyed by color alone. The INTERACTIVE rating control stays the
 * <input type="range"> in LibraryControls; this is the visual skin +
 * read-only display.
 */
export function StarRating({
  value,
  ariaLabelTemplate,
  className,
}: {
  /** 0-10 half-steps (2 per full star). */
  value: number;
  /** e.g. dict.card.rating.aria = "Your rating: {n} of 5" */
  ariaLabelTemplate: string;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(10, Math.round(value)));
  const full = Math.floor(clamped / 2);
  const half = clamped % 2 === 1;
  const empty = 5 - full - (half ? 1 : 0);
  const stars = "★".repeat(full) + (half ? "½" : "") + "☆".repeat(empty);
  const label = ariaLabelTemplate.replace("{n}", (clamped / 2).toString());

  return (
    <span
      className={`sp-card-stars${className ? ` ${className}` : ""}`}
      role="img"
      aria-label={label}
    >
      {stars}
    </span>
  );
}
