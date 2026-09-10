import { GameCard } from "@/components/GameCard";
import type { GameCard as GameCardData } from "@/lib/api";

export type ShelfStatus = "populated" | "empty" | "loading" | "error";

function SkeletonShelf({ count }: { count: number }) {
  return (
    <section className="sp-shelf" aria-label="Loading shelf">
      <h2 className="sp-h2" aria-hidden="true">
        &nbsp;
      </h2>
      <p role="status" aria-live="polite" className="visually-hidden">
        Loading…
      </p>
      <ul className="sp-shelf-track sp-shelf-track--dense" aria-hidden="true">
        {Array.from({ length: count }, (_, index) => (
          <li key={index} className="sp-skeleton" />
        ))}
      </ul>
    </section>
  );
}

export function NewReleasesShelf({
  items,
  locale,
  status = "populated",
  labels,
}: {
  items: GameCardData[];
  locale: string;
  status?: ShelfStatus;
  labels: { heading: string };
}) {
  if (status === "loading") return <SkeletonShelf count={6} />;
  if (status === "error" || status === "empty" || items.length === 0) return null;

  return (
    <section className="sp-shelf" aria-labelledby="new-releases-heading">
      <h2 id="new-releases-heading" className="sp-h2">
        {labels.heading}
      </h2>
      <ul className="sp-shelf-track">
        {items.slice(0, 20).map((item) => (
          <GameCard
            key={item.id}
            game={item}
            locale={locale}
            score={item.display_rating ?? item.total_rating ?? null}
          />
        ))}
      </ul>
    </section>
  );
}
