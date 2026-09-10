/**
 * StatusPill (01.1-UI-SPEC). Backlog status as a pill using
 * --color-status-{status}; the label text comes from the caller
 * (dict.status.labels.*). Read-only presentational use on cards and in
 * the collection status summary; LibraryControls keeps its native radio
 * group for the editable control.
 *
 * Nocturne identity: a tinted tier ground plus a leading glyph (diamond /
 * filled square / check / cross) so the state reads by shape as well as
 * colour and label -- never colour alone.
 */
export type BacklogStatus = "pending" | "playing" | "completed" | "abandoned";

/** 12px marks on a 24 grid, currentColor so they take the tier colour. */
function StatusGlyph({ status }: { status: BacklogStatus }) {
  const common = {
    width: 12,
    height: 12,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    focusable: false,
    style: { flex: "none" as const },
  };
  switch (status) {
    case "pending":
      return (
        <svg {...common} fill="currentColor" stroke="none">
          <path d="M12 3l9 9-9 9-9-9 9-9Z" />
        </svg>
      );
    case "playing":
      return (
        <svg {...common} fill="currentColor" stroke="none">
          <rect x="4" y="4" width="16" height="16" rx="2" />
        </svg>
      );
    case "completed":
      return (
        <svg {...common}>
          <path d="M5 13l4 4L19 7" />
        </svg>
      );
    case "abandoned":
      return (
        <svg {...common}>
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      );
  }
}

export function StatusPill({
  status,
  label,
  onCover = false,
  bare = false,
}: {
  status: BacklogStatus;
  label: string;
  onCover?: boolean;
  /** Drop the pill chrome: a plain glyph + label line in the status
   * colour, for use inside the game card foot. */
  bare?: boolean;
}) {
  const className = bare
    ? `sp-status-line sp-status-${status}`
    : `sp-status-pill sp-status-${status}${onCover ? " sp-status-pill--on-cover" : ""}`;
  return (
    <span className={className}>
      <StatusGlyph status={status} />
      {label}
    </span>
  );
}
