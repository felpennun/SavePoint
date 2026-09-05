import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { RecommendationShelf } from "@/components/RecommendationShelf";
import { getDictionary } from "@/i18n";
import { fetchRecommendations } from "@/lib/api";

/**
 * Recommendations (01.1-UI-SPEC Screen Contract 4, REC-10, NEW).
 * Auth-gated the same way as /collection. Genre-grouped horizontal
 * shelves, one per top taste genre (cap 4), each with a plain-language
 * explainer; already-owned works are excluded. Insufficient-history state
 * is visually distinct from the site-wide RecommendationStrip. The
 * heuristic endpoint is Plan 05/09 -- until it lands this page shows the
 * insufficient-history state.
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

  const result = await fetchRecommendations(cookieHeader);
  if (result === "unauthorized") {
    redirect(loginRedirect);
  }

  const shelves = result && !result.insufficient_history ? result.shelves.slice(0, 4) : [];

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{r.heading}</h1>
      <p className="sp-lead">{r.intro}</p>
      <p className="sp-muted" style={{ margin: "0 0 var(--space-xl)" }}>
        {r.excludedNote}
      </p>

      {shelves.length === 0 ? (
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
        shelves.map((shelf) => (
          <RecommendationShelf key={shelf.genre_slug} shelf={shelf} locale={locale} />
        ))
      )}
    </main>
  );
}
