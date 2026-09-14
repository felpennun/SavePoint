import { getDictionary } from "@/i18n";

export default async function ResearchLoading({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
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
