import { GameCard } from "@/components/GameCard";
import { getDictionary } from "@/i18n";
import type { PersonalRecommendationShelf } from "@/lib/api";

/**
 * RecommendationShelf renders one horizontally scrollable GameCard list per
 * recommendation genre. The page intentionally keeps only these lists in
 * the successful state; explanatory copy belongs in the thesis, not in the
 * demo surface.
 */
export function RecommendationShelf({
  shelf,
  locale,
}: {
  shelf: PersonalRecommendationShelf;
  locale: string;
}) {
  const heading = getDictionary(locale).recommendations.shelfHeading.replace("{genre}", shelf.genre);

  return (
    <section className="sp-shelf" aria-labelledby={`recommendation-${shelf.genreSlug}`}>
      <h2 id={`recommendation-${shelf.genreSlug}`} className="sp-h2">
        {heading}
      </h2>
      <ul className="sp-shelf-track" style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {shelf.items.map((item) => (
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
            score={item.catalogue_rating}
          />
        ))}
      </ul>
    </section>
  );
}
