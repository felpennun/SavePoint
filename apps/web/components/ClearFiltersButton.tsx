/**
 * Red trash-can button placed next to "Apply filters". It is a plain link to
 * the page without a query string, so it works without JavaScript and clears
 * every filter at once. Rendered only while at least one filter is active.
 */
export function ClearFiltersButton({ href, label }: { href: string; label: string }) {
  return (
    <a href={href} className="sp-btn-clear" aria-label={label} title={label}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 6h18" />
        <path d="M8 6V4h8v2" />
        <path d="M6 6l1 14h10l1-14" />
        <path d="M10 11v5M14 11v5" />
      </svg>
    </a>
  );
}
