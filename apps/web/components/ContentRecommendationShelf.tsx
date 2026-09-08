import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import type { ContentRecommendationItem } from "@/lib/api";
import { getDictionary } from "@/i18n";

export function ContentRecommendationShelf({
  items,
  locale,
  heading,
  error,
  retryHref,
  retryLabel,
}: {
  items: ContentRecommendationItem[];
  locale: string;
  heading: string;
  error?: string;
  retryHref?: string;
  retryLabel?: string;
}) {
  if (items.length === 0 && !error) return null;
  return (
    <section className="sp-shelf" aria-labelledby="content-recommendations-heading">
      <h2 id="content-recommendations-heading" className="sp-h2">
        {heading}
      </h2>
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
        <ol className="sp-shelf-track" style={{ listStyle: "none", margin: 0, padding: 0 }}>
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
