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
  description,
  algorithmId = "genre-taste-v1",
}: {
  shelf: PersonalRecommendationShelf;
  locale: string;
  description?: string;
  algorithmId?: string;
}) {
  const heading = getDictionary(locale).recommendations.shelfHeading.replace("{genre}", shelf.genre);
  const sectionId = `recommendation-${shelf.genreSlug}`;

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
        <span className="sp-algo-id">{algorithmId}</span>
      </div>
      {description ? <p id={`${sectionId}-description`} className="sp-muted">{description}</p> : null}
      <ul className="sp-shelf-track">
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
            score={item.display_rating}
          />
        ))}
      </ul>
    </section>
  );
}
