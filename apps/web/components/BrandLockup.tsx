/**
 * BrandLockup (Nocturne visual-identity import, identity artboard 1b). The
 * isotype -- the "save slot", a memory-card notch holding a solid
 * checkpoint marker -- sits beside the "SavePoint" wordmark set in Inter
 * 600 (hierarchy from size, never weight past 600). The slot outline uses
 * `currentColor` so it theme-swaps with the surrounding text; the marker
 * is the one reserved-accent use (10% rule), and "Point" takes the accent
 * so the wordmark carries a single mark of colour.
 *
 * The wordmark scales down with the viewport so the enlarged lockup never
 * crowds the compact mobile header.
 */
export function BrandLockup({ title = "SavePoint" }: { title?: string }) {
  return (
    <span
      role="img"
      aria-label={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        color: "inherit",
        fontWeight: 600,
        fontSize: "clamp(1.25rem, 1.05rem + 1.3vw, 1.5rem)",
        lineHeight: 1,
        letterSpacing: "-0.02em",
        whiteSpace: "nowrap",
      }}
    >
      <svg
        width="34"
        height="34"
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        focusable="false"
        style={{ display: "block", flex: "none" }}
      >
        <path
          d="M6 12a6 6 0 0 1 6-6h20l10 10v20a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V12Z"
          stroke="currentColor"
          strokeWidth="2.5"
        />
        <path d="M24 15l8 9-8 9-8-9 8-9Z" fill="var(--color-accent)" />
      </svg>
      <span aria-hidden="true">
        Save<span style={{ color: "var(--color-accent-strong)" }}>Point</span>
      </span>
    </span>
  );
}
