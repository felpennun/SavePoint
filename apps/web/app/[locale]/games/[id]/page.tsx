import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { LibraryControls } from "@/components/LibraryControls";
import { ScorePill } from "@/components/ScorePill";
import { getDictionary } from "@/i18n";
import { fetchGameDetail } from "@/lib/api";

/**
 * Game detail (01.1-UI-SPEC Screen Contract 3, redesign only). Three columns
 * on wide screens: cover hero left, game information in the centre, and the
 * game configuration panel on the right. Missing cover -> first-party placeholder
 * (CoverImage onError). Missing score/genres/platforms -> the row is omitted,
 * never an empty heading.
 */
export default async function GameDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: rawLocale, id } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const game = await fetchGameDetail(id, locale);
  if (!game) {
    notFound();
  }

  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");

  const platforms = Array.from(
    new Set(game.releases.map((r) => r.platform).filter((p): p is string => Boolean(p))),
  );
  const genres = game.genres ?? [];

  return (
    <main className="sp-page sp-game-page">
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

          {game.total_rating != null ? (
            <div style={{ margin: "var(--space-sm) 0" }}>
              <ScorePill
                rating={game.total_rating}
                ariaLabelTemplate={dict.card.score.aria}
                withLabel
                className="sp-score-pill--inline"
              />
            </div>
          ) : (
            <span className="visually-hidden">{dict.card.score.none}</span>
          )}

          {game.total_rating_count != null || game.rating_count != null ? (
            <p className="sp-meta sp-detail-rating-count" aria-label={dict.detail.ratings}>
              {dict.detail.ratings}: {game.total_rating_count ?? game.rating_count}
            </p>
          ) : null}

          {genres.length > 0 ? (
            <>
              <h2 className="sp-h2">{dict.detail.genres}</h2>
              <div className="sp-chip-row">
                {genres.map((g) => (
                  <Link key={g.slug} href={`/${locale}/catalogue?genre=${encodeURIComponent(g.slug)}`} className="sp-chip">
                    {g.name}
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

          {game.summary || locale === "es" ? (
            <section>
              <h2 className="sp-h2">{dict.detail.summary}</h2>
              <p className="sp-detail-summary">{game.summary || dict.detail.summaryUnavailable}</p>
            </section>
          ) : null}

          {game.related_content.length > 0 ? (
            <section aria-label={dict.detail.relatedContent}>
              <h2 className="sp-h2">{dict.detail.relatedContent}</h2>
              <ul className="sp-related-list">
                {game.related_content.map((related) => (
                  <li key={related.id}>
                    <Link href={`/${locale}/games/${related.slug}`} className="sp-related-card">
                      <div className="sp-related-cover">
                        {related.cover.is_placeholder ? (
                          <div className="sp-cover-placeholder" data-testid="cover-placeholder">
                            <span>{related.title}</span>
                          </div>
                        ) : (
                          <CoverImage
                            src={related.cover.url}
                            alt={related.cover.alt}
                            title={related.title}
                            missingLabel={dict.common.coverMissing}
                            width={72}
                            height={96}
                          />
                        )}
                      </div>
                      <span>
                        <strong>{related.title}</strong>
                        <small>{related.relation === "dlc" ? dict.detail.dlc : dict.detail.expansion}</small>
                        <small>{[related.year, related.platform_summary].filter(Boolean).join(" · ")}</small>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {game.provenance ? (
            <section aria-label={dict.provenance.heading} className="sp-provenance">
              <h2 className="sp-h2" style={{ fontSize: "var(--text-meta)", margin: "0 0 var(--space-xs)" }}>
                {dict.provenance.heading}
              </h2>
              <p style={{ margin: 0 }}>
                {game.provenance.source} · {game.provenance.source_id} · {game.provenance.licence} ·{" "}
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
          </div>
        </div>

        <aside className="sp-game-config" aria-label={locale === "es" ? "Configuración del videojuego" : "Game configuration"}>
          <div className="sp-surface">
            <LibraryControls workId={game.id} locale={locale} isAuthenticated={isAuthenticated} releases={game.releases} />
          </div>
        </aside>
      </div>
    </main>
  );
}
