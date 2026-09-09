import Link from "next/link";
import { cookies } from "next/headers";

import { BrandLockup } from "@/components/BrandLockup";
import { GameCard } from "@/components/GameCard";
import { NewReleasesShelf } from "@/components/NewReleasesShelf";
import { getDictionary } from "@/i18n";
import { fetchAccountMe, fetchCatalogueList, fetchMyLibrary, getNewReleases } from "@/lib/api";

/** Home (01.1-UI-SPEC Screen Contract 1). Logged-out: wordmark + value
 * proposition + CTA row + catalogue sample. Signed-in: greeting + "pick up
 * where you left off" + genre-recommendations CTA.
 * Home was not in the plan's files_modified -- redesigned here as a scope
 * addition so the whole journey reads as one product. */
export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);

  const cookieStore = await cookies();
  const signedIn = cookieStore.has("sessionid");
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

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

  let continueItems: Awaited<ReturnType<typeof fetchMyLibrary>>["items"] = [];
  let alias: string | null = null;
  if (signedIn) {
    const [me, lib] = await Promise.all([
      fetchAccountMe(cookieHeader),
      fetchMyLibrary(cookieHeader).catch(() => null),
    ]);
    alias = me?.username ?? null;
    continueItems = lib?.items.slice(0, 6) ?? [];
  }

  return (
    <main className="sp-page">
      {signedIn ? (
        <>
          <h1 className="sp-h1">
            {alias ? dict.home.signedIn.greeting.replace("{alias}", alias) : dict.home.signedIn.continueHeading}
          </h1>
          {alias ? (
            <p className="sp-meta">{dict.account.switcher.current.replace("{alias}", alias)}</p>
          ) : null}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-ctl)", alignItems: "center", margin: "var(--space-lg) 0" }}>
            <Link href={`/${locale}/recommendations`} className="sp-btn-primary">
              {dict.home.signedIn.recommendationsCta}
            </Link>
            <Link href={`/${locale}/collection`} className="sp-link">
              {dict.nav.collection}
            </Link>
          </div>

          <h2 className="sp-h2">{dict.home.signedIn.continueHeading}</h2>
          {continueItems.length === 0 ? (
            <p className="sp-lead">
              {dict.collection.emptyBody}{" "}
              <Link href={`/${locale}/catalogue`} className="sp-link">
                {dict.collection.emptyCta}
              </Link>
            </p>
          ) : (
            <ul className="sp-grid">
              {continueItems.map((item) => (
                <GameCard
                  key={item.work_id}
                  game={{
                    id: item.work_id,
                    slug: item.work_slug,
                    title: item.work_title,
                    year: item.year ?? null,
                    platform_summary: item.platform_summary ?? "",
                    cover: item.cover ?? { url: null, is_placeholder: true, alt: item.work_title },
                  }}
                  locale={locale}
                  score={item.display_rating}
                  ratingHalfSteps={item.rating_half_steps}
                />
              ))}
            </ul>
          )}
        </>
      ) : (
        <>
          <div style={{ color: "var(--color-text-primary)", marginBottom: "var(--space-sm)" }}>
            <BrandLockup />
          </div>
          <h1 className="sp-h1">SavePoint</h1>
          <p className="sp-lead">{dict.home.valueProposition}</p>
          {/* No log-in entry here on purpose: sign-in lives in the navbar
              (person icon) and on its own /login page. The home hero leads
              with browsing the catalogue and creating an account. */}
          <nav style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-ctl)", alignItems: "center", margin: "var(--space-lg) 0" }}>
            <Link href={`/${locale}/catalogue`} className="sp-btn-primary">
              {dict.home.loggedOut.secondaryCta}
            </Link>
            <Link href={`/${locale}/register`} className="sp-link">
              {dict.home.loggedOut.registerCta}
            </Link>
          </nav>

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
                  <GameCard key={game.id} game={game} locale={locale} score={game.display_rating ?? null} />
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      <div style={{ borderTop: "1px solid var(--color-surface-border)", marginTop: "var(--space-2xl)", paddingTop: "var(--space-2xl)" }}>
        <NewReleasesShelf
          items={newReleases}
          locale={locale}
          status={newReleasesFailed ? "error" : newReleases.length === 0 ? "empty" : "populated"}
          labels={dict.home.newReleases}
        />
      </div>

    </main>
  );
}
