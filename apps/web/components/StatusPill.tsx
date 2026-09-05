/**
 * StatusPill (01.1-UI-SPEC). Backlog status as a pill using
 * --color-status-{status}; the label text comes from the caller
 * (dict.status.labels.*). Read-only presentational use on cards and in
 * the collection status summary; LibraryControls keeps its native radio
 * group for the editable control.
 */
export type BacklogStatus = "pending" | "playing" | "completed" | "abandoned";

export function StatusPill({
  status,
  label,
  onCover = false,
}: {
  status: BacklogStatus;
  label: string;
  onCover?: boolean;
}) {
  return (
    <span
      className={`sp-status-pill sp-status-${status}${onCover ? " sp-status-pill--on-cover" : ""}`}
    >
      {label}
    </span>
  );
}
