import Link from "next/link";
import { cookies } from "next/headers";

import { GameCard } from "@/components/GameCard";
import { NewReleasesShelf } from "@/components/NewReleasesShelf";
import { RecentGames } from "@/components/RecentGames";
import { getDictionary } from "@/i18n";
import { fetchCatalogueList, getNewReleases } from "@/lib/api";

/** Home (01.1-UI-SPEC Screen Contract 1). Logged-out: wordmark + value
 * proposition + CTA row + catalogue sample. Signed-in: the "Novedades"
 * shelf followed by "Pick up where you left off" -- the five most recently
 * opened game pages (per-browser, localStorage).
 * Home was not in the plan's files_modified -- redesigned here as a scope
 * addition so the whole journey reads as one product. */
export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const cookieStore = await cookies();
  const signedIn = cookieStore.has("sessionid");

  let sample: Awaited<ReturnType<typeof fetchCatalogueList>>["results"] = [];
  let sampleFailed = false;
  try {
    const result = await fetchCatalogueList({ page: 1 });
    sample = result.results.slice(0, 8);
  } catch {
    sampleFailed = true;
  }

  let newReleases: Awaited<ReturnType<typeof getNewReleases>> = [];
  let newReleasesFailed = false;
  try {
    newReleases = await getNewReleases();
  } catch {
    newReleasesFailed = true;
  }

  const newReleasesShelf = (
    <NewReleasesShelf
      items={newReleases}
      locale={locale}
      status={newReleasesFailed ? "error" : newReleases.length === 0 ? "empty" : "populated"}
      labels={dict.home.newReleases}
    />
  );

  return (
    <main className="sp-page">
      {signedIn ? (
        <>
          {newReleasesShelf}
          <div style={{ borderTop: "1px solid var(--color-surface-border)", marginTop: "var(--space-md)", paddingTop: "var(--space-md)" }}>
            <RecentGames
              locale={locale}
              heading={dict.home.signedIn.continueHeading}
              emptyText={dict.home.signedIn.continueEmpty}
              emptyCta={dict.collection.emptyCta}
            />
          </div>
        </>
      ) : (
        <>
          <div className="sp-hero">
            <svg className="sp-hero-mark" width="34" height="34" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <path d="M6 12a6 6 0 0 1 6-6h20l10 10v20a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V12Z" stroke="var(--color-accent-strong)" strokeWidth="2.5" />
              <path d="M24 15l8 9-8 9-8-9 8-9Z" fill="var(--color-accent-strong)" />
            </svg>
            <h1 className="sp-h1">SavePoint</h1>
            <p className="sp-lead">{dict.home.valueProposition}</p>
            {/* No log-in entry here on purpose: sign-in lives in the navbar
                (person icon) and on its own /login page. The home hero leads
                with browsing the catalogue and creating an account. */}
            <nav style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-ctl)", alignItems: "center", marginTop: "var(--space-lg)" }}>
              <Link href={`/${locale}/catalogue`} className="sp-btn-primary">
                {dict.home.loggedOut.secondaryCta}
              </Link>
              <Link href={`/${locale}/register`} className="sp-link">
                {dict.home.loggedOut.registerCta}
              </Link>
            </nav>
          </div>

          <section aria-label={dict.home.sampleHeading}>
            <h2 className="sp-h2">{dict.home.sampleHeading}</h2>
            {sampleFailed ? (
              <div>
                <p role="alert">{dict.errors.homepageSampleFailure}</p>
                <Link href={`/${locale}/catalogue`} className="sp-link">
                  {dict.errors.openFullCatalogue}
                </Link>
              </div>
            ) : (
              <ul className="sp-grid">
                {sample.map((game) => (
                  <GameCard key={game.id} game={game} locale={locale} score={game.display_rating ?? null} bare />
                ))}
              </ul>
            )}
          </section>

          <div style={{ borderTop: "1px solid var(--color-surface-border)", marginTop: "var(--space-md)", paddingTop: "var(--space-md)" }}>
            {newReleasesShelf}
          </div>
        </>
      )}
    </main>
  );
}
