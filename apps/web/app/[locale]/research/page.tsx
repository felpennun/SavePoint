import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { ResearchPanel } from "@/components/ResearchPanel";
import { getDictionary } from "@/i18n";
import {
  fetchResearchArtifacts,
  fetchResearchComparison,
  fetchResearchRuns,
  fetchAccountMe,
  type ResearchComparison,
  type ResearchQueryFilters,
} from "@/lib/api";

function singleQueryValue(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" && value ? value : undefined;
}

function readResearchFilters(searchParams: Record<string, string | string[] | undefined>): ResearchQueryFilters {
  return {
    run: singleQueryValue(searchParams.run),
    algorithm: singleQueryValue(searchParams.algorithm),
    cohort: singleQueryValue(searchParams.cohort),
    metric: singleQueryValue(searchParams.metric),
  };
}

function handleResearchResponse<T>(
  result: Awaited<ReturnType<typeof fetchResearchRuns>> | Awaited<ReturnType<typeof fetchResearchComparison>> | Awaited<ReturnType<typeof fetchResearchArtifacts>>,
  locale: string,
): T {
  if (result.kind === "unauthorized") redirect(`/${locale}/login?next=/${locale}/research`);
  if (result.kind === "forbidden") notFound();
  if (result.kind === "error") throw new Error("Research evidence request failed");
  return result.data as T;
}

export default async function ResearchPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const query = readResearchFilters(await searchParams);
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  if (!cookieStore.has("sessionid")) redirect(`/${locale}/login?next=/${locale}/research`);

  // The API remains the final authority, but the SSR route must also gate the
  // page before rendering any research data. This keeps a session cookie (or
  // an accidental staff flag) from becoming a capability grant and makes the
  // denied and unknown resource paths indistinguishable in the browser.
  const account = await fetchAccountMe(cookieHeader);
  if (account?.capabilities?.can_view_research !== true) notFound();

  handleResearchResponse(await fetchResearchRuns(cookieHeader), locale);
  const comparison = handleResearchResponse<ResearchComparison>(
    await fetchResearchComparison(cookieHeader, query),
    locale,
  );
  const artifactResult = await fetchResearchArtifacts(cookieHeader, comparison.run.run_id);
  if (artifactResult.kind === "unauthorized") redirect(`/${locale}/login?next=/${locale}/research`);
  if (artifactResult.kind === "forbidden") notFound();
  const artifacts = artifactResult.kind === "ok" ? artifactResult.data : null;
  return <ResearchPanel locale={locale} comparison={comparison} artifacts={artifacts} status={comparison.rows.length === 0 ? "empty" : artifacts ? "populated" : "partial"} labels={dict.research} />;
}
