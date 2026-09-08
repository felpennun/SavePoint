import { getDictionary } from "@/i18n";

/** Aggregate-only rating provenance shown below the mixed product score. */
export function RatingBreakdownLine({
  igdbCount,
  savepointCount,
  locale,
}: {
  igdbCount: number;
  savepointCount: number;
  locale: string;
}) {
  const externalCount = Math.max(0, igdbCount);
  const localCount = Math.max(0, savepointCount);
  if (externalCount === 0 && localCount === 0) return null;

  const copy = getDictionary(locale).detail;
  const template =
    externalCount > 0 && localCount > 0
      ? copy.ratingBreakdown
      : externalCount > 0
        ? copy.ratingBreakdownExternalOnly
        : copy.ratingBreakdownLocalOnly;
  const text = template.replace("{igdb}", String(externalCount)).replace("{savepoint}", String(localCount));

  return <p className="sp-meta sp-detail-rating-breakdown">{text}</p>;
}
