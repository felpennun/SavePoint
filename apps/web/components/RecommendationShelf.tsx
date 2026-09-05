import { GameCard } from "@/components/GameCard";
import { formatCount, getDictionary } from "@/i18n";
import type { RecommendationShelfData } from "@/lib/api";

/**
 * RecommendationShelf (01.1-UI-SPEC, D-UI-4). One <section> per top taste
 * genre: labelled <h2> ("Because you play a lot of {genre}"), a
 * plain-language explainer, and a horizontally scrollable GameCard row
 * (120px cover variant). Contains its own overflow -- never causes
 * page-level horizontal scroll. Structurally distinct from the flat
 * RecommendationStrip <ol>.
 */
export function RecommendationShelf({
  shelf,
  locale,
}: {
  shelf: RecommendationShelfData;
  locale: string;
}) {
  const dict = getDictionary(locale);
  const heading = dict.recommendations.shelfHeading.replace("{genre}", shelf.genre);
  const explainer = formatCount(dict.recommendations.shelfExplainer, shelf.collection_count).replace(
    "{genre}",
    shelf.genre,
  );

  return (
    <section className="sp-shelf" aria-label={heading}>
      <h2 className="sp-h2" style={{ margin: "0 0 var(--space-xs)" }}>
        {heading}
      </h2>
      <p className="sp-muted" style={{ margin: "0 0 var(--space-md)" }}>
        {explainer}
      </p>
      <ul className="sp-shelf-track" style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {shelf.items.map((game) => (
          <GameCard key={game.id} game={game} locale={locale} score={game.total_rating} coverVariant="shelf" />
        ))}
      </ul>
    </section>
  );
}
