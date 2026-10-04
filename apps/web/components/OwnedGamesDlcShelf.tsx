import { GameCard } from "@/components/GameCard";
import type { OwnedDlcGroup } from "@/lib/api";
import type { ShelfStatus } from "@/components/NewReleasesShelf";

function SkeletonShelf() {
  return (
    <section className="sp-shelf" aria-label="Loading owned game content">
      <h2 className="sp-h2" aria-hidden="true">
        &nbsp;
      </h2>
      <p role="status" aria-live="polite" className="visually-hidden">
        Loading…
      </p>
      <ul className="sp-shelf-track sp-shelf-track--dense" aria-hidden="true">
        {Array.from({ length: 4 }, (_, index) => (
          <li key={index} className="sp-skeleton" />
        ))}
      </ul>
    </section>
  );
}

export function OwnedGamesDlcShelf({
  groups,
  locale,
  status = "populated",
  labels,
}: {
  groups: OwnedDlcGroup[];
  locale: string;
  status?: ShelfStatus;
  labels: { heading: string; intro: string; baseGameLabel: string };
}) {
  if (status === "loading") return <SkeletonShelf />;
  if (status === "error" || status === "empty" || groups.every((group) => group.dlc.length === 0)) return null;

  return (
    <section className="sp-shelf" aria-label={labels.heading}>
      {groups.map((group) => {
        if (group.dlc.length === 0) return null;
        return (
          <div key={group.base_game.slug} className="sp-shelf-dlc-group">
            <h2 className="sp-h2">{labels.baseGameLabel.replace("{game}", group.base_game.title)}</h2>
            <ul className="sp-shelf-track sp-shelf-track--dense">
              {group.dlc.map((item) => (
                <GameCard
                  key={`${group.base_game.slug}-${item.work_id}`}
                  game={{
                    id: item.work_id,
                    slug: item.slug,
                    title: item.title,
                    year: null,
                    platform_summary: "",
                    cover: item.cover,
                  }}
                  locale={locale}
                  coverVariant="shelf"
                />
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
