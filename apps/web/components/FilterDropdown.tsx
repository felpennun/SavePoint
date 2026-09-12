import type { ReactNode } from "react";

/**
 * A single popover control for a filter toolbar (redesigned 2026-09-12: the
 * filter panel moved from a sidebar to a thin bar above the results grid on
 * both the catalogue and the collection page). Every filter beyond
 * free-text search renders through this so the bar itself stays one row on
 * desktop and wraps cleanly on narrow viewports: the trigger shows the
 * filter's label plus a short summary of its current value, and the actual
 * controls only appear in the floating panel once opened.
 *
 * Plain <details>/<summary> -- no client filter state. Closing on an
 * outside click, on Escape, and when another dropdown opens is added once,
 * document-wide, by <FilterDropdownScript>; without JavaScript every panel
 * still opens and closes individually via the native disclosure toggle.
 */
export function FilterDropdown({
  label,
  summary,
  children,
  unavailable = false,
  className,
}: {
  label: string;
  summary?: string;
  children: ReactNode;
  unavailable?: boolean;
  className?: string;
}) {
  return (
    <details
      className={`sp-dropdown${className ? ` ${className}` : ""}`}
      aria-disabled={unavailable ? "true" : undefined}
      {...(unavailable ? { disabled: true } : {})}
    >
      <summary>
        <span>{label}</span>
        {summary ? <span className="sp-dropdown-summary">{summary}</span> : null}
        <svg
          className="sp-dropdown-chevron"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      <div className="sp-surface sp-dropdown-panel">{children}</div>
    </details>
  );
}
