import { getDictionary } from "@/i18n";

/**
 * Shown the instant a link is followed, while the next page is rendered on the
 * server. Next prefetches this boundary for links in view, so the click gives
 * immediate feedback instead of a frozen page.
 */
export default async function LocaleLoading({ params }: { params?: Promise<{ locale: string }> } = {}) {
  // A loading boundary may render without route params; stay renderable then.
  const rawLocale = params ? (await params).locale : "es";
  const dict = getDictionary(rawLocale);
  return (
    <main className="sp-page sp-route-loading" aria-busy="true">
      <div role="status" aria-live="polite" className="visually-hidden">{dict.loading.generic}</div>
      <div className="sp-skeleton sp-route-loading-heading" aria-hidden="true" />
      <div className="sp-route-loading-grid" aria-hidden="true">
        {Array.from({ length: 8 }, (_, index) => (
          <div key={index} className="sp-skeleton sp-route-loading-card" />
        ))}
      </div>
    </main>
  );
}
