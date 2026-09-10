import Link from "next/link";

/**
 * LoginIconButton (01.1-UI-SPEC). The navbar right-end account slot when
 * the visitor is logged OUT: a plain <Link> to the dedicated full
 * /{locale}/login page (never a dropdown/modal), rendered as a
 * person-icon (inline SVG, no dependency) with an aria-label; on >= md
 * the label also shows as visible text. Rightmost navbar item, 44px
 * target, visible focus ring.
 */
export function LoginIconButton({ locale, label }: { locale: string; label: string }) {
  return (
    <Link href={`/${locale}/login`} className="sp-btn-secondary" aria-label={label}>
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        aria-hidden="true"
      >
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21v-1a7 7 0 0 1 14 0v1" />
      </svg>
      <span className="hidden md:inline">{label}</span>
    </Link>
  );
}
