import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { RecommendationShelf } from "@/components/RecommendationShelf";
import { ContentRecommendationShelf } from "@/components/ContentRecommendationShelf";
import { OwnedGamesDlcShelf } from "@/components/OwnedGamesDlcShelf";
import { RecommendationRefreshNotice } from "@/components/RecommendationRefreshNotice";
import { getDictionary } from "@/i18n";
import {
  getOwnedDlc,
  getRecommendationSnapshot,
  groupRecommendationsByGenre,
} from "@/lib/api";

const CONTENT_SECTIONS = [
  ["content-cbf-weighted-v1", "weighted"],
  ["content-cbf-multiplicative-v1", "multiplicative"],
  ["content-cbf-twostage-v1", "twoStage"],
  ["content-cbf-neg-v1", "negative"],
  ["recency-v1", "recency"],
] as const;

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

  const [snapshotResponse, ownedDlcResponse] = await Promise.all([
    getRecommendationSnapshot(cookieHeader),
    getOwnedDlc(cookieHeader).catch(() => ({ groups: [] })),
  ]);
  if (snapshotResponse.kind === "unauthorized") {
    redirect(loginRedirect);
  }

  const snapshotData = snapshotResponse.kind === "ok" ? snapshotResponse.data : null;
  const genreData = snapshotData?.sections?.genre ?? null;
  const contentData = snapshotData?.sections?.content ?? {};
  const genreShelves = genreData && !genreData.insufficient_history ? groupRecommendationsByGenre(genreData) : [];
  const hasContentRecommendations = Object.values(contentData).some((result) => result.results.length > 0);
  const hasRecommendations = hasContentRecommendations || genreShelves.length > 0 || ownedDlcResponse.groups.length > 0;
  const isRefreshing = snapshotData?.status === "building" || snapshotData?.status === "stale";
  const needsCollectionChange = snapshotData?.status === "needs_refresh";
  const hasLoadError = snapshotResponse.kind === "error";

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{r.nav}</h1>
      {isRefreshing ? (
        <RecommendationRefreshNotice
          message={snapshotData?.status === "building" ? r.refreshPreparing : r.refreshUpdating}
        />
      ) : null}
      {needsCollectionChange ? (
        <p className="sp-muted" role="status" aria-live="polite">
          {r.refreshNeedsCollectionChange}
        </p>
      ) : null}
      {!hasRecommendations && hasLoadError ? (
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
          {CONTENT_SECTIONS.map(([algorithmId, copyKey]) => {
            const section = contentData[algorithmId];
            if (!section) return null;
            const copy = r.contentSections[copyKey];
            return (
              <ContentRecommendationShelf
                key={algorithmId}
                items={section.results}
                locale={locale}
                heading={copy.heading}
                description={copy.description}
                sectionId={`${algorithmId}-heading`}
              />
            );
          })}
          {genreShelves.map((shelf) => (
            <RecommendationShelf
              key={shelf.genreSlug}
              shelf={shelf}
              locale={locale}
              description={r.genreDescription}
            />
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
          <p className="sp-h2" style={{ margin: 0 }}>
            {snapshotData?.status === "building"
              ? r.refreshPreparing
              : snapshotData?.status === "needs_refresh"
                ? r.refreshNeedsCollectionChange
                : r.emptyHeading}
          </p>
          <p className="sp-lead" style={{ marginInline: "auto" }}>{r.emptyBody}</p>
          <Link href={`/${locale}/catalogue`} className="sp-btn-primary">{r.emptyCta}</Link>
        </div>
      )}
    </main>
  );
}
