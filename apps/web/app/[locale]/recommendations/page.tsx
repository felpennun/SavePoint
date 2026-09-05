import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { RecommendationShelf } from "@/components/RecommendationShelf";
import { getDictionary } from "@/i18n";
import { getPersonalRecommendations, groupRecommendationsByGenre } from "@/lib/api";

/**
 * Recommendations (01.1-UI-SPEC Screen Contract 4, REC-10, NEW).
 *
 * The independent D-04 personalized page: it wires the D-09 backend
 * contract (`GET /api/recommendations/genre-taste/`, `IsAuthenticated`)
 * into genre-grouped horizontal shelves (D-UI-4), each with a
 * plain-language explainer and per-card genre-overlap evidence, plus an
 * explicit `algorithm_id` + `limitation` disclosure so it can never be
 * confused with the public popularity baseline (REC-02, still shown
 * separately as `RecommendationStrip`) or the Phase 6 research recommender
 * (REC-03).
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

  const response = await getPersonalRecommendations(cookieHeader);
  if (response.kind === "unauthorized") {
    redirect(loginRedirect);
  }

  const data = response.kind === "ok" ? response.data : null;
  const shelves = data && !data.insufficient_history ? groupRecommendationsByGenre(data) : [];
  const showEmpty = data != null && (data.insufficient_history || shelves.length === 0);

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{r.heading}</h1>
      <p className="sp-lead">{r.intro}</p>

      {response.kind === "error" ? (
        <div className="sp-empty" role="alert">
          <p className="sp-lead" style={{ marginInline: "auto" }}>
            {r.error}
          </p>
          <Link href={`/${locale}/recommendations`} className="sp-btn-primary">
            {dict.common.retry}
          </Link>
        </div>
      ) : (
        <>
          {data ? (
            <section className="sp-disclosure" aria-label={r.methodHeading}>
              <p className="sp-meta" style={{ margin: "0 0 var(--space-xs)" }}>
                {r.methodHeading}
              </p>
              <p className="sp-muted" style={{ margin: "0 0 var(--space-xs)" }}>
                {r.methodAlgorithm.replace("{id}", data.algorithm_id)}
              </p>
              <p className="sp-muted" style={{ margin: 0 }}>
                {data.limitation}
              </p>
            </section>
          ) : null}

          {showEmpty ? (
            <div className="sp-empty">
              <p className="sp-h2" style={{ margin: 0 }}>
                {r.emptyHeading}
              </p>
              <p className="sp-lead" style={{ marginInline: "auto" }}>
                {r.emptyBody}
              </p>
              <Link href={`/${locale}/catalogue`} className="sp-btn-primary">
                {r.emptyCta}
              </Link>
            </div>
          ) : (
            <>
              <p className="sp-muted" style={{ margin: "0 0 var(--space-xl)" }}>
                {r.excludedNote}
              </p>
              {shelves.map((shelf) => (
                <RecommendationShelf key={shelf.genreSlug} shelf={shelf} locale={locale} />
              ))}
            </>
          )}
        </>
      )}
    </main>
  );
}
