import { GameCard } from "@/components/GameCard";
import { getDictionary } from "@/i18n";
import type { PersonalRecommendationShelf } from "@/lib/api";

/**
 * RecommendationShelf (01.1-UI-SPEC, D-UI-4). One <section> per top taste
 * genre: a labelled <h2> ("Because you play a lot of {genre}"), a
 * plain-language explainer, and a horizontally scrollable GameCard row
 * (120px cover variant). Each card carries its own genre-overlap
 * evidence line. Contains its own overflow -- never causes page-level
 * horizontal scroll. Structurally distinct from the flat popularity
 * RecommendationStrip <ol> (D-09).
 */
export function RecommendationShelf({
  shelf,
  locale,
}: {
  shelf: PersonalRecommendationShelf;
  locale: string;
}) {
  const dict = getDictionary(locale);
  const r = dict.recommendations;
  const heading = r.shelfHeading.replace("{genre}", shelf.genre);
  const explainer = r.shelfEvidence.replace("{genre}", shelf.genre);

  return (
    <section className="sp-shelf" aria-label={heading}>
      <h2 className="sp-h2" style={{ margin: "0 0 var(--space-xs)" }}>
        {heading}
      </h2>
      <p className="sp-muted" style={{ margin: "0 0 var(--space-md)" }}>
        {explainer}
      </p>
      <ul className="sp-shelf-track" style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {shelf.items.map((item) => (
          <GameCard
            key={item.work_id}
            game={{
              id: item.work_id,
              slug: item.slug,
              title: item.title,
              year: null,
              platform_summary: "",
              cover: { url: null, is_placeholder: true, alt: item.title },
            }}
            locale={locale}
            coverVariant="shelf"
            evidence={r.cardEvidence.replace(
              "{genres}",
              item.matched_genres.map((genre) => genre.name).join(", "),
            )}
          />
        ))}
      </ul>
    </section>
  );
}
