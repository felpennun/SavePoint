import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { RecommendationsClient } from "@/components/RecommendationsClient";

/**
 * Recommendations (01.1-UI-SPEC Screen Contract 4, REC-10, NEW).
 *
 * The independent D-04 personalized page: it wires the D-09 backend
 * contract (`GET /api/recommendations/genre-taste/`, `IsAuthenticated`)
 * into horizontal shelves for the content recommender, tag taste, and
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
  const cookieStore = await cookies();
  const loginRedirect = `/${locale}/login?next=${encodeURIComponent(`/${locale}/recommendations`)}`;
  if (!cookieStore.has("sessionid")) {
    redirect(loginRedirect);
  }
  return <RecommendationsClient locale={locale} />;
}
