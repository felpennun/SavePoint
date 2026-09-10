import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import type { ContentRecommendationItem } from "@/lib/api";
import { getDictionary } from "@/i18n";

export function ContentRecommendationShelf({
  items,
  locale,
  heading,
  description,
  sectionId = "content-recommendations-heading",
  algorithmId,
  error,
  retryHref,
  retryLabel,
}: {
  items: ContentRecommendationItem[];
  locale: string;
  heading: string;
  description?: string;
  sectionId?: string;
  /** The backend algorithm id, shown as a mono tag beside the heading
   * (Nocturne artboard 2h). */
  algorithmId?: string;
  error?: string;
  retryHref?: string;
  retryLabel?: string;
}) {
  if (items.length === 0 && !error) return null;
  return (
    <section
      className="sp-shelf"
      aria-labelledby={sectionId}
      aria-describedby={description ? `${sectionId}-description` : undefined}
    >
      <div className="sp-shelf-head">
        <h2 id={sectionId} className="sp-h2">
          {heading}
        </h2>
        {algorithmId ? <span className="sp-algo-id">{algorithmId}</span> : null}
      </div>
      {description ? <p id={`${sectionId}-description`} className="sp-muted">{description}</p> : null}
      {error ? (
        <div className="sp-section-error" role="alert">
          <p className="sp-card-evidence">{error}</p>
          {retryHref && retryLabel ? (
            <Link href={retryHref} className="sp-link">
              {retryLabel}
            </Link>
          ) : null}
        </div>
      ) : null}
      {items.length > 0 ? (
        <ol className="sp-shelf-track">
          {items.map((item) => (
            <GameCard
              key={item.work_id}
              game={{
                id: item.work_id,
                slug: item.slug,
                title: item.title,
                year: item.year,
                platform_summary: item.platform_summary,
                cover: item.cover,
              }}
              locale={locale}
              score={item.display_rating}
              evidence={item.reason ? formatReason(item.reason, locale) : undefined}
              coverVariant="shelf"
            />
          ))}
        </ol>
      ) : null}
    </section>
  );
}

function formatReason(
  reason: NonNullable<ContentRecommendationItem["reason"]>,
  locale: string,
): string | undefined {
  const names = reason.signals.slice(0, 2).map((signal) => signal.name).filter(Boolean);
  if (names.length === 0) return undefined;
  const joined = names.join(locale === "en" ? " and " : " y ");
  const template = getDictionary(locale).recommendations.contentCardEvidence;
  return template.replace("{reasons}", joined);
}
