"use client";

import { useEffect, useState } from "react";

/**
 * ThemeToggle (01.1-UI-SPEC, D-UI-1). Visible to every visitor. Reads its
 * initial state from the `data-theme` attribute the server already set on
 * <html> (from the sp-theme cookie) -- no localStorage, no flash. On
 * activate it flips `document.documentElement.dataset.theme` synchronously
 * and writes the sp-theme cookie (path=/, 1 year, SameSite=Lax, not
 * HttpOnly -- it is not a secret and the client must set it).
 * Icon-only at every width; 44px target; the state and the action are on
 * `aria-pressed` and `aria-label`.
 */
export function ThemeToggle({
  labels,
}: {
  labels: {
    switchToDark: string;
    switchToLight: string;
  };
}) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const current = document.documentElement.dataset.theme === "light" ? "light" : "dark";
    setTheme(current);
    setMounted(true);
  }, []);

  function toggle() {
    const next = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    document.cookie = `sp-theme=${next};path=/;max-age=31536000;SameSite=Lax`;
    setTheme(next);
  }

  const isLight = theme === "light";

  return (
    <button
      type="button"
      className="sp-btn-secondary sp-icon-btn min-w-11 shrink-0"
      aria-pressed={isLight}
      aria-label={isLight ? labels.switchToDark : labels.switchToLight}
      onClick={toggle}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
        {mounted && isLight ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19" />
          </>
        ) : (
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        )}
      </svg>
    </button>
  );
}
