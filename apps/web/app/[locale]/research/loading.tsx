import { getDictionary } from "@/i18n";

export default async function ResearchLoading({ params }: { params?: Promise<{ locale: string }> } = {}) {
  // Next may render a route loading boundary without route params. Keep the
  // skeleton renderable in that transient state instead of turning navigation
  // into an error page.
  const rawLocale = params ? (await params).locale : "es";
  const dict = getDictionary(rawLocale);
  return (
    <main className="sp-page sp-research-page" aria-busy="true">
      <div role="status" aria-live="polite" className="sp-research-loading-status">{dict.loading.generic}</div>
      <div className="sp-skeleton sp-research-skeleton-heading" aria-hidden="true" />
      <div className="sp-surface sp-research-skeleton-filters" aria-hidden="true" />
      <div className="sp-surface sp-research-skeleton-chart" aria-hidden="true" />
      <div className="sp-surface sp-research-skeleton-table" aria-hidden="true" />
    </main>
  );
}
