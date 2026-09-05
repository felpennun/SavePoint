/**
 * DemoAccountBanner (01.1-UI-SPEC, AUTH-02). Slim, non-dismissible
 * `role="note"` bar directly under the header on authenticated pages: a
 * standing truth about the deployment, not a notification.
 */
export function DemoAccountBanner({ text }: { text: string }) {
  return (
    <div
      role="note"
      style={{
        background: "var(--color-surface-overlay)",
        color: "var(--color-text-secondary)",
        borderBottom: "1px solid var(--color-surface-border)",
        fontSize: "var(--text-meta)",
        padding: "var(--space-sm) var(--space-lg)",
      }}
    >
      {text}
    </div>
  );
}
