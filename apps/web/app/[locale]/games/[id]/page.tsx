import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { GameComments } from "@/components/GameComments";
import { LibraryControls } from "@/components/LibraryControls";
import { OwnedGamesDlcShelf } from "@/components/OwnedGamesDlcShelf";
import { localizedGenreLabel } from "@/lib/genre-labels";
import { RatingBreakdownLine } from "@/components/RatingBreakdownLine";
import { RecordGameVisit } from "@/components/RecordGameVisit";
import { ScorePill } from "@/components/ScorePill";
import { Synopsis } from "@/components/Synopsis";
import { getDictionary } from "@/i18n";
import { fetchGameDetail, type OwnedDlcGroup } from "@/lib/api";

/** Game detail follows the P3 product order while retaining the existing
 * cover/content/configure layout: metadata first, then controls and related
 * surfaces in the sticky configuration column. */
export default async function GameDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: rawLocale, id } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const game = await fetchGameDetail(id, locale);
  if (!game) notFound();

  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");

  // The game's DLC and expansions come with the game itself, so the shelf is
  // the same for everyone: signed in or not, with or without a configuration.
  const dlcGroups: OwnedDlcGroup[] =
    game.related_content.length > 0
      ? [
          {
            base_game: { slug: game.slug, title: game.title },
            dlc: game.related_content.map((related) => ({
              work_id: related.id,
              slug: related.slug,
              title: related.title,
              cover: related.cover,
              relation: related.relation,
            })),
          },
        ]
      : [];

  const platforms = Array.from(
    new Set(game.releases.map((release) => release.platform).filter((platform): platform is string => Boolean(platform))),
  );
  const tags = game.tags ?? [];
  const releaseDate = game.releases
    .map((release) => release.release_date)
    .filter((date): date is string => Boolean(date))
    .sort()[0];
  const formattedReleaseDate = releaseDate
    ? new Intl.DateTimeFormat(locale, { dateStyle: "long" }).format(new Date(`${releaseDate}T00:00:00Z`))
    : null;

  return (
    <main className="sp-page sp-game-page">
      <RecordGameVisit
        game={{
          slug: game.slug,
          title: game.title,
          year: game.year ?? null,
          platform_summary: platforms.slice(0, 3).join(", "),
          display_rating: game.display_rating ?? null,
          cover: {
            url: game.cover.url ?? null,
            is_placeholder: game.cover.is_placeholder,
            alt: game.cover.alt,
          },
        }}
      />
      <div className="sp-detail-grid">
        <div className="sp-detail-main">
          <div className="sp-cover-hero">
            <div className="sp-cover">
              {game.cover.is_placeholder ? (
                <div className="sp-cover-placeholder" data-testid="cover-placeholder">
                  <span>{game.title}</span>
                  <span className="visually-hidden">{dict.common.coverMissing}</span>
                </div>
              ) : (
                <CoverImage
                  src={game.cover.url}
                  alt={game.cover.alt}
                  title={game.title}
                  missingLabel={dict.common.coverMissing}
                  width={280}
                  height={373}
                />
              )}
            </div>
          </div>

          <div className="sp-detail-content">
            <h1 className="sp-h1">
              {game.title}{" "}
              {game.year != null ? (
                <span style={{ color: "var(--color-text-secondary)", fontWeight: 400 }}>({game.year})</span>
              ) : null}
            </h1>

            <div style={{ margin: "var(--space-sm) 0" }}>
              {game.display_rating != null ? (
                <>
                  <ScorePill
                    rating={game.display_rating}
                    ariaLabelTemplate={dict.card.score.aria}
                    withLabel
                    label={dict.card.score.label}
                    tierLabels={dict.card.score.tiers}
                    className="sp-score-pill--inline"
                  />
                  <RatingBreakdownLine
                    igdbCount={game.rating_breakdown.igdb_count}
                    savepointCount={game.rating_breakdown.savepoint_count}
                    locale={locale}
                  />
                </>
              ) : (
                <p className="sp-meta">{dict.card.score.none}</p>
              )}
            </div>

            <Synopsis text={game.summary} labels={dict.detail.synopsis} />

            {tags.length > 0 ? (
              <>
                <h2 className="sp-h2">{dict.detail.tags}</h2>
                <div className="sp-chip-row">
                  {tags.map((tag) => (
                    <Link
                      key={tag.slug}
                      href={`/${locale}/catalogue?tag=${encodeURIComponent(tag.slug)}`}
                      className="sp-chip"
                    >
                      {localizedGenreLabel(tag.slug, tag.name, locale)}
                    </Link>
                  ))}
                </div>
              </>
            ) : null}

            {platforms.length > 0 ? (
              <>
                <h2 className="sp-h2">{dict.detail.platforms}</h2>
                <p className="sp-kv">{platforms.join(", ")}</p>
              </>
            ) : null}

            {formattedReleaseDate ? (
              <>
                <h2 className="sp-h2">{dict.detail.releaseDate}</h2>
                <p className="sp-kv">{formattedReleaseDate}</p>
              </>
            ) : null}

            <div className="sp-game-comments-region" data-testid="game-comments-region">
              <GameComments workId={game.id} locale={locale} isAuthenticated={isAuthenticated} />
            </div>
          </div>
        </div>

        <aside
          className="sp-game-config"
          aria-label={locale === "es" ? "Configuración del videojuego" : "Game configuration"}
        >
          <div className="sp-surface">
            <LibraryControls workId={game.id} locale={locale} isAuthenticated={isAuthenticated} releases={game.releases} />
          </div>

          <OwnedGamesDlcShelf
            groups={dlcGroups}
            locale={locale}
            status={dlcGroups.length > 0 ? "populated" : "empty"}
            labels={dict.recommendations.dlc}
          />

            {game.provenance ? (
            <section aria-label={dict.provenance.heading} className="sp-provenance">
              <p className="sp-eyebrow" style={{ margin: "0 0 var(--space-sm)" }}>
                {dict.provenance.heading}
              </p>
              <p style={{ margin: 0 }}>
                {game.provenance.source} · {game.provenance.source_id} · {game.provenance.licence} · {" "}
                {new Date(game.provenance.retrieved_at).toISOString().slice(0, 10)}
              </p>
              <p style={{ margin: "var(--space-xs) 0 0" }}>
                {dict.detail.attribution} ·{" "}
                <Link href={`/${locale}/sources`} className="sp-link">
                  {dict.detail.seeSources}
                </Link>
              </p>
            </section>
          ) : null}
        </aside>
      </div>
    </main>
  );
}
