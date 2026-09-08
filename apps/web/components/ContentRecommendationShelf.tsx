import { GameCard } from "@/components/GameCard";
import type { ContentRecommendationItem } from "@/lib/api";

export function ContentRecommendationShelf({
  items,
  locale,
  heading,
}: {
  items: ContentRecommendationItem[];
  locale: string;
  heading: string;
}) {
  if (items.length === 0) return null;

  return (
    <section className="sp-shelf" aria-labelledby="content-recommendations-heading">
      <h2 id="content-recommendations-heading" className="sp-h2">
        {heading}
      </h2>
      <ul className="sp-shelf-track" style={{ listStyle: "none", margin: 0, padding: 0 }}>
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
            coverVariant="shelf"
          />
        ))}
      </ul>
    </section>
  );
}
