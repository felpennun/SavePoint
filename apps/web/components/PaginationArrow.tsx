import { HoverPrefetchLink } from "@/components/HoverPrefetchLink";

/** Empty slot with the arrow's footprint, so the page number stays centred
 * on the first and last pages where one arrow is missing. */
export function PaginationSpacer() {
  return <span className="sp-pagination-spacer" aria-hidden="true" />;
}

/**
 * A chevron pagination control (2026-09-12 redesign, replaces the
 * "Anterior"/"Siguiente" text links shared by the catalogue and the
 * collection page). Icon-only; the direction is still announced via
 * aria-label since nothing here is visible text.
 */
export function PaginationArrow({
  href,
  direction,
  label,
}: {
  href: string;
  direction: "prev" | "next";
  label: string;
}) {
  return (
    <HoverPrefetchLink eager href={href} className="sp-pagination-arrow" aria-label={label}>
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        style={direction === "prev" ? { transform: "scaleX(-1)" } : undefined}
      >
        <path d="M9 5l7 7-7 7" />
      </svg>
    </HoverPrefetchLink>
  );
}
