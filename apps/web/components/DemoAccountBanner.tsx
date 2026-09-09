/**
 * DemoAccountBanner (01.1-UI-SPEC, AUTH-02). Slim, non-dismissible
 * `role="note"` bar directly under the header on authenticated pages: a
 * standing truth about the deployment, not a notification.
 *
 * Nocturne identity: carried in JetBrains Mono with the amber accent and a
 * leading diamond so it is recognisable without relying on colour.
 */
export function DemoAccountBanner({ text }: { text: string }) {
  return (
    <div
      role="note"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-sm)",
        background: "var(--color-status-pending-bg)",
        color: "var(--color-status-pending)",
        borderBottom: "1px solid var(--color-status-pending-border)",
        fontFamily: "var(--font-mono)",
        fontSize: "var(--text-meta)",
        lineHeight: 1.4,
        padding: "var(--space-sm) var(--space-lg)",
      }}
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
        focusable="false"
        style={{ flex: "none" }}
      >
        <path d="M12 3l9 9-9 9-9-9 9-9Z" />
      </svg>
      {text}
    </div>
  );
}
