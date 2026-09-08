import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { RecommendationShelf } from "@/components/RecommendationShelf";
import { ContentRecommendationShelf } from "@/components/ContentRecommendationShelf";
import { OwnedGamesDlcShelf } from "@/components/OwnedGamesDlcShelf";
import { getDictionary } from "@/i18n";
import {
  getContentRecommendations,
  getOwnedDlc,
  getPersonalRecommendations,
  groupRecommendationsByGenre,
} from "@/lib/api";

/**
 * Recommendations (01.1-UI-SPEC Screen Contract 4, REC-10, NEW).
 *
 * The independent D-04 personalized page: it wires the D-09 backend
 * contract (`GET /api/recommendations/genre-taste/`, `IsAuthenticated`)
 * into horizontal shelves for the content recommender, genre taste, and
 * owned downloadable content. Each shelf has a localized visible heading;
 * algorithm explanations remain in the thesis and are not mixed into this
 * product surface.
 *
 * Auth-gated exactly like `/collection`: no `sessionid` cookie -> redirect
 * to login; cookie present but the API denies (401/403) -> same redirect.
 * The signed-out state exposes no personal data and the nav link is only
 * added for authenticated visitors (threat T-01.1-10).
 */
export default async function RecommendationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const r = dict.recommendations;

  const cookieStore = await cookies();
  const loginRedirect = `/${locale}/login?next=${encodeURIComponent(`/${locale}/recommendations`)}`;
  if (!cookieStore.has("sessionid")) {
    redirect(loginRedirect);
  }
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const [genreResponse, contentResponse, ownedDlcResponse] = await Promise.all([
    getPersonalRecommendations(cookieHeader),
    getContentRecommendations(cookieHeader),
    getOwnedDlc(cookieHeader).catch(() => ({ groups: [] })),
  ]);
  if (genreResponse.kind === "unauthorized" || contentResponse.kind === "unauthorized") {
    redirect(loginRedirect);
  }

  const genreData = genreResponse.kind === "ok" ? genreResponse.data : null;
  const contentData = contentResponse.kind === "ok" ? contentResponse.data : null;
  const genreShelves = genreData && !genreData.insufficient_history ? groupRecommendationsByGenre(genreData) : [];
  const contentItems = contentData ? contentData.results : [];
  const hasRecommendations = contentItems.length > 0 || genreShelves.length > 0 || ownedDlcResponse.groups.length > 0;

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{r.nav}</h1>
      {!hasRecommendations && (genreResponse.kind === "error" || contentResponse.kind === "error") ? (
        <div className="sp-empty" role="alert">
          <p className="sp-lead" style={{ marginInline: "auto" }}>
            {r.error}
          </p>
          <Link href={`/${locale}/recommendations`} className="sp-btn-primary">
            {dict.common.retry}
          </Link>
        </div>
      ) : hasRecommendations ? (
        <div className="sp-recommendation-shelves">
          <ContentRecommendationShelf
            items={contentItems}
            locale={locale}
            heading={r.contentHeading}
            error={contentResponse.kind === "error" ? r.error : undefined}
            retryHref={`/${locale}/recommendations`}
            retryLabel={r.retry}
          />
          {genreShelves.map((shelf) => (
            <RecommendationShelf key={shelf.genreSlug} shelf={shelf} locale={locale} />
          ))}
          <OwnedGamesDlcShelf
            groups={ownedDlcResponse.groups}
            locale={locale}
            labels={r.dlc}
            status={ownedDlcResponse.groups.length > 0 ? "populated" : "empty"}
          />
        </div>
      ) : (
        <div className="sp-empty">
          <p className="sp-h2" style={{ margin: 0 }}>{r.emptyHeading}</p>
          <p className="sp-lead" style={{ marginInline: "auto" }}>{r.emptyBody}</p>
          <Link href={`/${locale}/catalogue`} className="sp-btn-primary">{r.emptyCta}</Link>
        </div>
      )}
    </main>
  );
}
