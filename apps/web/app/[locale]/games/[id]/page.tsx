import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { LibraryControls } from "@/components/LibraryControls";
import { RecommendationStrip } from "@/components/RecommendationStrip";
import { ScorePill } from "@/components/ScorePill";
import { getDictionary } from "@/i18n";
import { fetchGameDetail, fetchPopularity } from "@/lib/api";

/**
 * Game detail (01.1-UI-SPEC Screen Contract 3, redesign only). Two-column
 * on >= md: cover hero left; title / IGDB ScorePill / genres / platforms /
 * release date / LibraryControls / provenance right. Missing cover ->
 * first-party placeholder (CoverImage onError). Missing score/genres/
 * platforms -> the row is omitted, never an empty heading. Popularity is a
 * secondary panel whose failure must not blank the page.
 */
export default async function GameDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: rawLocale, id } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const game = await fetchGameDetail(id);
  if (!game) {
    notFound();
  }

  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");

  let popularityResults: Awaited<ReturnType<typeof fetchPopularity>>["results"] = [];
  try {
    const popularity = await fetchPopularity();
    popularityResults = popularity.results.filter((r) => r.work_id !== game.id).slice(0, 5);
  } catch {
    popularityResults = [];
  }

  const platforms = Array.from(
    new Set(game.releases.map((r) => r.platform).filter((p): p is string => Boolean(p))),
  );
  const releaseDates = game.releases
    .map((r) => r.release_date)
    .filter((d): d is string => Boolean(d))
    .sort();
  const firstReleaseDate = releaseDates[0];
  const genres = game.genres ?? [];

  return (
    <main className="sp-page">
      <div className="sp-detail-grid">
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

        <div>
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

          {firstReleaseDate ? (
            <>
              <h2 className="sp-h2">{dict.detail.releaseDate}</h2>
              <p className="sp-kv">
                {new Intl.DateTimeFormat(locale, { dateStyle: "long" }).format(new Date(firstReleaseDate))}
              </p>
            </>
          ) : null}

          <div className="sp-surface" style={{ marginTop: "var(--space-lg)" }}>
            <LibraryControls workId={game.id} locale={locale} isAuthenticated={isAuthenticated} releases={game.releases} />
          </div>

          {game.related_content.length > 0 ? (
            <section aria-label={locale === "es" ? "Contenido relacionado" : "Related content"}>
              <h2 className="sp-h2">{locale === "es" ? "Contenido relacionado" : "Related content"}</h2>
              <ul>
                {game.related_content.map((related) => (
                  <li key={related.id}>
                    {related.title} ({related.relation})
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <div style={{ marginTop: "var(--space-xl)", paddingTop: "var(--space-md)", borderTop: "1px solid var(--color-surface-border)" }}>
            <RecommendationStrip results={popularityResults} locale={locale} />
          </div>

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
    </main>
  );
}
