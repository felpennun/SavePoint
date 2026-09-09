/**
 * ScorePill (01.1-UI-SPEC First-Party Component Contracts + Nocturne
 * identity). IGDB `total_rating` (0-100) as a rounded integer that sits
 * INSIDE the Nocturne "save slot" shape: a JetBrains Mono numeral over the
 * shell, which is filled with a tinted tier ground and stroked in the tier
 * colour. Five tramos (identity artboard 1c):
 *   90-100 essential (primary) - 75-89 great (success) - 60-74 fair
 *   (neutral) - 40-59 poor (warning) - 0-39 bad (error).
 * `rating == null` renders nothing -- the caller shows `card.score.none`
 * visually-hidden if it needs to. Never uses the accent as a flood.
 */

/** The Nocturne isotype shell -- a memory-card notch -- on a 48 grid. */
const SLOT_PATH = "M6 12a6 6 0 0 1 6-6h20l10 10v20a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V12Z";

type Tier = "essential" | "great" | "fair" | "poor" | "bad";

function tierOf(value: number): Tier {
  if (value >= 90) return "essential";
  if (value >= 75) return "great";
  if (value >= 60) return "fair";
  if (value >= 40) return "poor";
  return "bad";
}

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
  /** Show a localized textual label next to the slot (detail page). */
  withLabel?: boolean;
  label?: string;
}) {
  if (rating == null || Number.isNaN(rating)) return null;
  const value = Math.round(rating);
  const tier = tierOf(value);
  const ariaLabel = ariaLabelTemplate.replace("{n}", String(value));

  return (
    <span
      className={`sp-score-pill sp-score-${tier}${withLabel ? " sp-score-pill--labelled" : ""}${
        className ? ` ${className}` : ""
      }`}
      role="img"
      aria-label={ariaLabel}
    >
      <span className="sp-score-slot">
        <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
          <path d={SLOT_PATH} />
        </svg>
        <span className="sp-score-slot-value">{value}</span>
      </span>
      {withLabel && label ? <span className="sp-score-pill-label">{label}</span> : null}
    </span>
  );
}
