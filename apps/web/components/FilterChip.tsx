import Link from "next/link";

/**
 * FilterChip (01.1-UI-SPEC). A removable active-filter indicator: a
 * <Link> that drops exactly one query param, the accent-tinted `--active`
 * chip, Label type, a visible inline-SVG cross, and
 * aria-label="Remove filter {name}".
 */
export function FilterChip({
  label,
  removeHref,
  removeAriaLabel,
}: {
  label: string;
  removeHref: string;
  removeAriaLabel: string;
}) {
  return (
    <Link href={removeHref} className="sp-chip sp-chip--active" aria-label={removeAriaLabel}>
      <span>{label}</span>
      <svg className="sp-chip-x" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
        <path d="M6 6l12 12M18 6L6 18" />
      </svg>
    </Link>
  );
}
